# modules/sheets.py

import pandas as pd
import streamlit as st
import gspread

from google.oauth2.service_account import Credentials
from modules.config import extract_spreadsheet_id

from datetime import datetime




SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

REQUIRED_COLUMNS = [
    "Content ID",
    "Publishing Status",
    "Published Date",
    "Dashboard Last Updated",
    "Trello Card URL",
    "Trello Card ID",
    "Asset Link",
    "Post Link(s)",
    "Sheet Row ID",
    "Internal Approval",
    "Approval",
]


def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def open_client_sheet(spreadsheet_url, worksheet_name):
    gc = get_client()
    spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)
    return sh, ws


def ensure_required_columns(worksheet):
    headers = worksheet.row_values(1)
    changed = False

    for column in REQUIRED_COLUMNS:
        if column not in headers:
            headers.append(column)
            changed = True

    if changed:
        worksheet.update("1:1", [headers])

    return headers


def get_column_map(headers):
    return {header: idx + 1 for idx, header in enumerate(headers)}

def normalize_publish_date(value):
    if value is None or value == "":
        return pd.NaT

    if isinstance(value, (int, float)):
        try:
            return (
                pd.Timestamp("1899-12-30")
                + pd.to_timedelta(float(value), unit="D")
            )
        except Exception:
            return pd.NaT

    try:
        return pd.to_datetime(
            str(value).strip(),
            errors="coerce",
            dayfirst=True,
        )
    except Exception:
        return pd.NaT

    value = str(value).strip()

    if not value:
        return pd.NaT

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d %Y",
        "%B %d %Y",
    ]

    for fmt in formats:
        try:
            return pd.Timestamp(
                datetime.strptime(value, fmt)
            )
        except Exception:
            pass

    return pd.to_datetime(
        value,
        errors="coerce",
        dayfirst=True,
    )


def read_sheet(spreadsheet_url, worksheet_name, client_name, worksheet_gid):
    sh, ws = open_client_sheet(spreadsheet_url, worksheet_name)
    ensure_required_columns(ws)

    records = ws.get_all_records()
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["Client"] = client_name
    df["Spreadsheet URL"] = spreadsheet_url
    df["Worksheet Name"] = worksheet_name
    df["Worksheet GID"] = worksheet_gid

    if "Internal Approval" not in df.columns:
        df["Internal Approval"] = ""
    if "Approval" not in df.columns:
        df["Approval"] = ""

    return df


@st.cache_data(ttl=60)
def load_all_clients(config_df):
    frames = []

    for _, row in config_df.iterrows():
        try:
            df = read_sheet(
                row["Spreadsheet URL"],
                row["Worksheet Name"],
                row["Client"],
                row["Worksheet GID"],
            )
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"Failed loading {row['Client']}: {e}")

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def append_content_row(spreadsheet_url, worksheet_name, row_data):
    sh, ws = open_client_sheet(spreadsheet_url, worksheet_name)
    headers = ensure_required_columns(ws)

    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    row_data["Dashboard Last Updated"] = timestamp

    values = [row_data.get(header, "") for header in headers]

    publish_date = normalize_publish_date(
        row_data.get("Publishing Date")
    )

    all_rows = ws.get(
        "A:ZZ",
         value_render_option="UNFORMATTED_VALUE",
    )

    # Default = append to end
    insert_position = len(all_rows) + 1

    try:
        publishing_date_col = headers.index("Publishing Date")

        dated_rows = []

        for idx, row in enumerate(all_rows[1:], start=2):

            if len(row) <= publishing_date_col:
                continue

            existing_date = normalize_publish_date(
                row[publishing_date_col]
            )

            if pd.notna(existing_date):
                dated_rows.append(
                    (idx, existing_date)
                )

        # Sort valid dates only
        dated_rows.sort(key=lambda x: x[1])

        for row_idx, existing_date in dated_rows:
            if (
                pd.notna(publish_date)
                and publish_date <= existing_date
            ):
                insert_position = row_idx
                break

        print(
            f"Publish Date={publish_date} | Insert Position={insert_position}"
        )

    except Exception as e:
        print(
            f"Insert position calculation error: {e}"
        )

    ws.insert_row(
        values,
        insert_position,
        value_input_option="USER_ENTERED",
    )

    # Rebuild Sheet Row IDs
    row_id_col = headers.index("Sheet Row ID") + 1
    total_rows = len(ws.get_all_values())

    for row_num in range(2, total_rows + 1):
        ws.update_cell(
            row_num,
            row_id_col,
            row_num,
        )

    return {
        "row_number": insert_position,
        "worksheet_id": ws.id,
    }

def update_publish_status(spreadsheet_url, worksheet_name, row_number, urls_dict):
    sh, ws = open_client_sheet(spreadsheet_url, worksheet_name)
    headers = ensure_required_columns(ws)
    col_map = get_column_map(headers)

    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    combined_links = []

    for _, value in urls_dict.items():
        if value:
            cleaned = str(value).strip()
            if cleaned:
                combined_links.append(cleaned)

    combined_post_links = "\n".join(combined_links).strip()

    updates = {
        "Publishing Status": "Published",
        "Published Date": timestamp,
        "Dashboard Last Updated": timestamp,
        "Post Link(s)": combined_post_links,
    }

    updates.update(urls_dict)

    for column, value in updates.items():
        if column not in col_map:
            continue
        ws.update_cell(row_number, col_map[column], value)


def update_trello_info(spreadsheet_url, worksheet_name, row_number, card_id, card_url):
    sh, ws = open_client_sheet(spreadsheet_url, worksheet_name)
    headers = ensure_required_columns(ws)
    col_map = get_column_map(headers)

    if "Trello Card ID" in col_map:
        ws.update_cell(row_number, col_map["Trello Card ID"], card_id)

    if "Trello Card URL" in col_map:
        ws.update_cell(row_number, col_map["Trello Card URL"], card_url)


def update_asset_link(spreadsheet_url, worksheet_name, row_number, asset_links):
    sh, ws = open_client_sheet(spreadsheet_url, worksheet_name)
    headers = ensure_required_columns(ws)
    col_map = get_column_map(headers)

    if "Asset Link" not in col_map:
        return

    if isinstance(asset_links, list):
        asset_links = "\n".join(asset_links)

    ws.update_cell(row_number, col_map["Asset Link"], asset_links)

    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    if "Dashboard Last Updated" in col_map:
        ws.update_cell(row_number, col_map["Dashboard Last Updated"], timestamp)


def update_approval_status(
    spreadsheet_url,
    worksheet_name,
    row_number,
    internal_approval=False,
    client_approval=False,
):
    sh, ws = open_client_sheet(spreadsheet_url, worksheet_name)
    headers = ensure_required_columns(ws)
    col_map = get_column_map(headers)

    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    internal_value = "Approved" if internal_approval else "Pending"
    client_value = "Approved" if client_approval else "Pending"

    updates = {
        "Internal Approval": internal_value,
        "Approval": client_value,
        "Dashboard Last Updated": timestamp,
    }

    for column, value in updates.items():
        if column not in col_map:
            continue
        ws.update_cell(row_number, col_map[column], value)


def get_sheet_row_url(spreadsheet_url, worksheet_gid, row_number):
    return f"{spreadsheet_url}#gid={worksheet_gid}&range=A{row_number}"

def sort_sheet_by_publish_date(
    spreadsheet_url,
    worksheet_name,
):
    sh, ws = open_client_sheet(
        spreadsheet_url,
        worksheet_name,
    )

    values = ws.get_all_values()

    if len(values) <= 2:
        return

    header = values[0]
    rows = values[1:]

    try:
        publish_idx = header.index("Publishing Date")
    except ValueError:
        return

    def sort_key(row):
        try:
            return pd.to_datetime(
                row[publish_idx],
                errors="coerce",
            )
        except Exception:
            return pd.Timestamp.max

    rows.sort(key=sort_key)

    ws.update(
        "A1",
        [header] + rows,
        value_input_option="USER_ENTERED",
    )

    # Rebuild Sheet Row IDs
    if "Sheet Row ID" in header:
        row_id_col = header.index("Sheet Row ID") + 1

        for row_num in range(2, len(rows) + 2):
            ws.update_cell(
                row_num,
                row_id_col,
                row_num,
            )