import re
import requests
import streamlit as st

BASE_URL = "https://api.trello.com/1"


def get_auth():

    return {
        "key": st.secrets["TRELLO_API_KEY"],
        "token": st.secrets["TRELLO_TOKEN"]
    }


def get_boards():

    url = (
        f"{BASE_URL}/members/me/boards"
    )

    r = requests.get(
        url,
        params=get_auth()
    )

    r.raise_for_status()

    return r.json()

import re


def extract_card_id(card_value):

    if not card_value:
        return None

    card_value = str(
        card_value
    ).strip()

    if "trello.com" not in card_value:
        return card_value

    match = re.search(

        r"trello\.com/c/([^/]+)",

        card_value
    )

    if match:
        return match.group(1)

    return None

def get_board_by_name(name):

    boards = get_boards()

    for board in boards:

        if board["name"] == name:
            return board

    return None


def get_list_by_name(
    board_name,
    list_name
):

    board = get_board_by_name(
        board_name
    )

    if not board:
        return None

    url = (
        f"{BASE_URL}/boards/"
        f"{board['id']}/lists"
    )

    r = requests.get(
        url,
        params=get_auth()
    )

    r.raise_for_status()

    lists = r.json()

    for lst in lists:

        if lst["name"] == list_name:
            return lst

    return None


def create_card(
    list_id,
    title,
    description,
    due_date
):

    payload = {
        **get_auth(),
        "idList": list_id,
        "name": title,
        "desc": description,
        "due": due_date
    }

    r = requests.post(
        f"{BASE_URL}/cards",
        params=payload
    )

    r.raise_for_status()

    return r.json()


def get_cards(list_id):

    r = requests.get(
        f"{BASE_URL}/lists/{list_id}/cards",
        params=get_auth()
    )

    r.raise_for_status()

    return r.json()


def get_approved_links(card_value):

    card_id = extract_card_id(
        card_value
    )

    if not card_id:
        return []

    """
    Looks through all comments on a Trello card.

    Any comment containing the word:
        approved

    (case-insensitive)

    will be scanned for URLs.

    Example:

    Approved:
    https://drive.google.com/file1
    https://drive.google.com/file2
    """

    r = requests.get(

        f"{BASE_URL}/cards/{card_id}/actions",

        params={
            **get_auth(),
            "filter": "commentCard"
        }
    )

    r.raise_for_status()

    actions = r.json()

    links = []

    for action in actions:

        text = (
            action
            .get("data", {})
            .get("text", "")
        )

        if not text:
            continue

        if "approved" not in text.lower():
            continue

        found_links = re.findall(

            r"https?://[^\s]+",

            text
        )

        links.extend(
            found_links
        )

    # remove duplicates while preserving order

    unique_links = []

    seen = set()

    for link in links:

        if link not in seen:

            seen.add(link)

            unique_links.append(link)

    return unique_links