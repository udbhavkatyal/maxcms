import re
import pandas as pd
import gspread
import streamlit as st

from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


REQUIRED_CONFIG_COLUMNS = [

    "Client",
    "Prefix",

    "Spreadsheet URL",
    "Worksheet Name",
    "Worksheet GID",

    "Trello Board Name",
    "Trello List Name"
]


def get_gspread_client():

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    return gspread.authorize(
        creds
    )


def extract_spreadsheet_id(url):

    match = re.search(
        r"/d/([a-zA-Z0-9-_]+)",
        url
    )

    if not match:
        return None

    return match.group(1)


@st.cache_data(ttl=60)
def load_client_config(
    config_sheet_url
):

    gc = get_gspread_client()

    spreadsheet_id = extract_spreadsheet_id(
        config_sheet_url
    )

    sh = gc.open_by_key(
        spreadsheet_id
    )

    ws = sh.worksheet(
        "Clients"
    )

    rows = ws.get_all_records()

    df = pd.DataFrame(
        rows
    )

    missing = [

        c
        for c in REQUIRED_CONFIG_COLUMNS
        if c not in df.columns
    ]

    if missing:

        raise Exception(
            f"Missing config columns: {missing}"
        )

    return df