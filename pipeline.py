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

def main():
    print(get_token())

if __name__ == "__main__":
    main()