import re
import pandas as pd


def extract_numeric_suffix(content_id):

    match = re.search(
        r"(\d+)$",
        str(content_id)
    )

    if not match:
        return 0

    return int(
        match.group(1)
    )


def get_next_content_id(
    prefix,
    cards
):

    highest = 0

    for card in cards:

        title = card["name"]

        match = re.search(
            rf"\[{re.escape(prefix)}(\d+)\]",
            title,
            re.IGNORECASE
        )

        if match:

            highest = max(
                highest,
                int(match.group(1))
            )

    return f"{prefix}{highest + 1}"


def normalize_status(value):

    if not value:
        return "Pending"

    value = str(
        value
    ).strip()

    if value.lower() == "published":
        return "Published"

    return "Pending"


def parse_publish_date(value):

    if pd.isna(value):
        return pd.NaT

    value = str(
        value
    ).strip()

    try:

        return pd.to_datetime(
            value,
            errors="raise"
        )

    except:
        pass

    try:

        cleaned = (
            value
            .replace("st", "")
            .replace("nd", "")
            .replace("rd", "")
            .replace("th", "")
        )

        dt = pd.to_datetime(
            cleaned,
            format="%d %b",
            errors="raise"
        )

        return dt.replace(
            year=pd.Timestamp.now().year
        )

    except:

        return pd.NaT