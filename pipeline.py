import argparse
import time
from datetime import datetime

import duckdb
import pandas as pd
import requests

API_URL = "http://127.0.0.1:8080"
CLIENT_ID = "trainee-task"
CLIENT_SECRET = "s3cret-do-not-tell"

MAX_RETRIES = 10
BACKOFF_START_SECONDS = 1
BACKOFF_MAX_SECONDS = 30

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--date",
        required=True
    )

    return parser.parse_args()

def get_token():
    response = requests.post(
        f"{API_URL}/oauth/token",
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )

    response.raise_for_status()
    return response.json()["access_token"]

def fetch_page(token, params):
    backoff = BACKOFF_START_SECONDS

    for _ in range(MAX_RETRIES):
        response = requests.get(
            f"{API_URL}/api/cases",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", "2"))
            print(f"Rate limited (429), waiting {wait}s.")
            time.sleep(wait)
            continue

        if response.status_code == 503:
            print(f"Backend unavailable (503), backing off {backoff}s.")
            time.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX_SECONDS)
            continue

        if response.status_code == 401:
            print("Token expired, re-authenticating.")
            token = get_token()
            continue

        response.raise_for_status()
        return response.json(), token

    raise RuntimeError(f"Giving up after {MAX_RETRIES} retries.")

def fetch_cases(token, date):
    all_cases = []
    offset = 0
    limit = 100

    while True:
        data, token = fetch_page(
            token,
            {"closed_on": date, "offset": offset, "limit": limit},
        )
        items = data["items"]
        print(f"Fetched {len(items)} items.")

        if not items:
            break

        all_cases.extend(items)
        offset += limit
    return all_cases

def parse_created_at(value):
    for date_format in ("%Y-%m-%dT%H:%M:%SZ", "%d.%m.%Y %H:%M"):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    raise ValueError(f"Unbekanntes created_at-Format: {value!r}")

def clean_cases(cases):
    df = pd.DataFrame(cases)
    df["created_at"] = df["created_at"].apply(parse_created_at)
    df["last_modified"] = pd.to_datetime(df["last_modified"], format="%Y-%m-%dT%H:%M:%SZ")
    df["closed_at"] = pd.to_datetime(df["closed_at"], format="%Y-%m-%dT%H:%M:%SZ")

    df["priority"] = df["priority"].replace("", None)
    df["priority"] = pd.to_numeric(df["priority"]).astype("Int64")

    df["handling_minutes"] = pd.to_numeric(df["handling_minutes"]).astype("Int64")

    df["category"] = df["category"].str.strip().str.title()

    return df

def load_to_duckdb(cases):
    new_df = clean_cases(cases)
    new_df = new_df.sort_values("last_modified").drop_duplicates("case_id", keep="last")

    con = duckdb.connect("cases.duckdb")
    con.register("new_cases", new_df)

    table_exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = 'cases'"
    ).fetchone()[0] > 0

    if not table_exists:
        con.execute("CREATE TABLE cases AS SELECT * FROM new_cases")
    else:
        con.execute("""
            DELETE FROM cases
            WHERE EXISTS (
                SELECT * FROM new_cases
                WHERE new_cases.case_id = cases.case_id
                    AND new_cases.last_modified >= cases.last_modified
            )
        """)
        con.execute("""
            INSERT INTO cases BY NAME
            SELECT new_cases.* FROM new_cases
            LEFT JOIN cases USING (case_id)
            WHERE cases.case_id IS NULL
        """)

    con.close()

def main():
    args = parse_args()
    token = get_token()
    cases = fetch_cases(token, args.date)
    load_to_duckdb(cases)

    print(f"Loaded {len(cases)} cases.")

if __name__ == "__main__":
    main()