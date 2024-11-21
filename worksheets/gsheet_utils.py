from __future__ import print_function

import os
from typing import List

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def retrieve_gsheet(id, range):
    """Retrieve values from a Google Sheet.

    Args:
        id (str): The ID of the Google Sheet.
        range (str): The range of cells to retrieve.

    Returns:
        List: A list of values from the specified range in the Google Sheet."""
    creds = using_service_account()

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=id, range=range).execute()
        values: List = result.get("values", [])

        return values

    except HttpError as err:
        print(err)


def fill_all_empty(rows, desired_columns):
    for row in rows:
        for i in range(desired_columns - len(row)):
            row.append("")
    return rows


def using_service_account():
    # Path to your service account key file
    SERVICE_ACCOUNT_FILE = os.path.join(CURR_DIR, "service_account.json")

    # Scopes required by the Sheets API
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # Create credentials using the service account key file
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    return credentials
