import argparse

import duckdb
import pandas as pd
import requests 

API_URL = "http://127.0.0.1:8080"
CLIENT_ID = "trainee-task"
CLIENT_SECRET = "s3cret-do-not-tell"

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

def fetch_cases(token, date):
    response = requests.get(
        f"{API_URL}/api/cases?",
        params={
            "closed_on": date,
            "offset": 0,
            "limit": 100
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    response.raise_for_status()
    return response.json()["items"]


def main():
    token = get_token()
    print(fetch_cases(token, "2026-07-28"))

if __name__ == "__main__":
    main()