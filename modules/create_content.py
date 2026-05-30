import streamlit as st
import pandas as pd

from datetime import (
    timedelta,
    datetime,
    time
)

from modules.sheets import (
    open_client_sheet,
    append_content_row
)

from modules.trello import (
    get_list_by_name,
    get_cards,
    create_card
)

from modules.helpers import (
    get_next_content_id
)

TYPE_OPTIONS = [
    "Reel",
    "Static",
    "Carousel",
    "Video"
]

RATIO_OPTIONS = [
    "1:1",
    "4:5",
    "9:16",
    "16:9"
]

ASSET_MADE_BY_OPTIONS = [
    "Max Level",
    "Client",
    "Freelancer"
]

CHANNEL_OPTIONS = [
    "FB",
    "IG",
    "YT",
    "LinkedIn",
    "X"
]


def render_create_content(
    config_df
):

    st.header(
        "Create Content Piece"
    )

    selected_client = st.selectbox(
        "Client",
        config_df["Client"].tolist()
    )

    client_row = config_df[
        config_df["Client"]
        ==
        selected_client
    ].iloc[0]

    spreadsheet_url = client_row[
        "Spreadsheet URL"
    ]

    worksheet_name = client_row[
        "Worksheet Name"
    ]

    prefix = client_row[
        "Prefix"
    ]

    board_name = client_row[
        "Trello Board Name"
    ]

    list_name = client_row[
        "Trello List Name"
    ]

    st.divider()

    with st.form(
        "create_content_form"
    ):

        st.subheader(
            "Scheduling"
        )

        publish_date = st.date_input(
            "Publishing Date"
        )

        st.divider()

        st.subheader(
            "Content Details"
        )

        post_description = st.text_input(
            "Post Content Description",
            help="Short title for the content piece."
        )

        content_type = st.selectbox(
            "Type",
            TYPE_OPTIONS
        )

        ratio = st.selectbox(
            "Ratio",
            RATIO_OPTIONS,
            index=2
        )

        asset_made_by = st.selectbox(
            "Asset Made By",
            ASSET_MADE_BY_OPTIONS
        )

        channels = st.multiselect(
            "Channel(s)",
            CHANNEL_OPTIONS,
            default=["IG"]
        )

        st.divider()

        st.subheader(
            "Creative Brief"
        )

        info = st.text_area(
            "Info",
            height=180,
            help=(
                "Explain what should be created. "
                "Mention CTA, references, style, hooks."
            )
        )

        reference = st.text_area(
            "Reference / Additional",
            height=120,
            help=(
                "Links, examples, inspiration, notes."
            )
        )

        caption = st.text_area(
            "Caption",
            height=150,
            help=(
                "Draft caption or caption brief."
            )
        )

        submitted = st.form_submit_button(
            "Create Content"
        )

    if not submitted:
        return

    try:

        trello_list = get_list_by_name(
            board_name,
            list_name
        )

        if not trello_list:

            st.error(
                "Trello list not found."
            )

            return

        cards = get_cards(
            trello_list["id"]
        )

        content_id = get_next_content_id(
            prefix,
            cards
        )

        publish_date = pd.Timestamp(
            publish_date
        )

        production_date = (
            publish_date
            -
            timedelta(days=4)
        )

        day_name = (
            publish_date
            .strftime("%A")
        )

        due_date = datetime.combine(

            production_date.date(),

            time(
                18,
                0
            )
        )

        card_title = (
            f"[{content_id}] "
            f"{post_description}"
        )

        card_description = f"""
Content ID:
{content_id}

Client:
{selected_client}

Publishing Date:
{publish_date.strftime('%d %b %Y')}

Description:
{post_description}
"""

        card = create_card(

            trello_list["id"],

            card_title,

            card_description,

            due_date.isoformat()
        )

        row_data = {

            "Production":
                production_date.strftime(
                    "%d %b"
                ),

            "Publishing Date":
                publish_date.strftime(
                    "%Y-%m-%d"
                ),

            "Day":
                day_name,

            "Post Content Description":
                post_description,

            "Type":
                content_type,

            "Ratio":
                ratio,

            "Asset Made By":
                asset_made_by,

            "Channel(s)":
                ", ".join(
                    channels
                ),

            "Info":
                info,

            "Reference / Additional":
                reference,

            "Caption":
                caption,

            "Approval":
                "Pending",

            "Content ID":
                content_id,

            "Publishing Status":
                "Pending",

            "Trello Card URL":
                card["url"],

            "Trello Card ID":
                card["id"]
        }

        append_content_row(

            spreadsheet_url,

            worksheet_name,

            row_data
        )

        st.success(
            f"{content_id} created successfully."
        )

        st.cache_data.clear()

        st.rerun()

    except Exception as e:

        st.error(
            f"Error: {e}"
        )