#!/usr/bin/env python3
"""One-time OAuth2 setup for Gmail and Google Calendar API access.

Run this script once to authorize the application:
    python3 setup_auth.py

It will open a browser window for Google sign-in. After authorization,
a token.json file is saved locally for subsequent API calls.

Prerequisites:
    - credentials.json in the same directory (download from Google Cloud Console)
    - pip3 install google-auth google-auth-oauthlib google-api-python-client
"""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def main():
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: {CREDENTIALS_FILE} not found.")
        print()
        print("To set up Google API credentials:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create an OAuth 2.0 Client ID (Desktop application)")
        print("3. Download the JSON and save it as credentials.json in this directory")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: Required packages not installed.")
        print("Run: pip3 install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json())
    print(f"Authorization successful! Token saved to {TOKEN_FILE}")
    print("You can now run the email summary skill.")


if __name__ == "__main__":
    main()
