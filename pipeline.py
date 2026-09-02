import argparse
import time

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

def load_to_duckdb(cases):
    df = pd.DataFrame(cases)

    con = duckdb.connect("cases.duckdb")
    con.register("cases_df", df)

    con.execute("""
        CREATE OR REPLACE TABLE cases AS
        SELECT * FROM cases_df
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