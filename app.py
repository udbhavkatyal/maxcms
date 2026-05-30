import streamlit as st
import pandas as pd

from modules.auth import login
from modules.config import load_client_config
from modules.sheets import (
    load_all_clients,
    get_sheet_row_url
)
from modules.calendar_view import (
    build_events,
    render_calendar
)
from modules.create_content import (
    render_create_content
)
from modules.publish import (
    render_publish_form
)
from modules.helpers import (
    parse_publish_date
)

from modules.sheets import (
    load_all_clients,
    get_sheet_row_url,
    update_asset_link
)

from modules.trello import (
    get_approved_links
)


@st.dialog("Content Details", width="large")
def show_content_modal(row):

    content_id = str(
        row.get(
            "Content ID",
            ""
        )
    )

    st.markdown(
        f"## {content_id}"
    )

    st.markdown(
        f"### {row.get('Post Content Description','')}"
    )

    top_left, top_right = st.columns(
        [3, 1]
    )

    with top_left:

        info_col1, info_col2 = st.columns(2)

        with info_col1:

            st.markdown(
                f"**Type:** {row.get('Type','')}"
            )

            st.markdown(
                f"**Publish Date:** {row.get('Publishing Date','')}"
            )

            st.markdown(
                f"**Platforms:** {row.get('Channel(s)','')}"
            )

        with info_col2:

            st.markdown(
                f"**Status:** {row.get('Publishing Status','Pending')}"
            )

            st.markdown(
                f"**Approval:** {row.get('Approval','')}"
            )

            st.markdown(
                f"**Asset By:** {row.get('Asset Made By','')}"
            )

    with top_right:

        trello_url = str(
            row.get(
                "Trello Card URL",
                ""
            )
        ).strip()

        if trello_url:

            st.link_button(
                "Open Trello Card",
                trello_url
            )

        sheet_row_id = str(
            row.get(
                "Sheet Row ID",
                ""
            )
        ).strip()

        if sheet_row_id:

            try:

                row_url = get_sheet_row_url(

                    row[
                        "Spreadsheet URL"
                    ],

                    row[
                        "Worksheet GID"
                    ],

                    int(
                        sheet_row_id
                    )
                )

                st.link_button(
                    "Open Sheet Row",
                    row_url
                )

            except Exception:
                pass

        st.divider()

        asset_link = str(
            row.get(
                "Asset Link",
                ""
            )
        ).strip()

        if asset_link:

            st.success(
                "Asset Linked"
            )

            for link in asset_link.split("\n"):

                link = link.strip()

                if link:

                    st.link_button(
                        "Open Asset",
                        link
                    )

        if st.button(
            "Fetch Asset From Trello",
            key=f"fetch_asset_{content_id}"
        ):

            try:

                card_reference = (
                    str(
                        row.get(
                            "Trello Card ID",
                            ""
                        )
                    ).strip()
                    or
                    str(
                        row.get(
                            "Trello Card URL",
                            ""
                        )
                    ).strip()
                )

                if not card_reference:

                    st.error(
                        "No Trello Card found."
                    )

                else:

                    links = get_approved_links(
                        card_reference
                    )

                    if not links:

                        st.warning(
                            "No approved links found."
                        )

                    else:

                        update_asset_link(

                            spreadsheet_url=
                                row[
                                    "Spreadsheet URL"
                                ],

                            worksheet_name=
                                row[
                                    "Worksheet Name"
                                ],

                            row_number=int(
                                sheet_row_id
                            ),

                            asset_links=links
                        )

                        st.success(
                            f"Fetched {len(links)} asset link(s)."
                        )

                        st.cache_data.clear()

                        st.rerun()

            except Exception as e:

                st.error(
                    str(e)
                )

    st.divider()

    info_text = str(
        row.get(
            "Info",
            ""
        )
    ).strip()

    if info_text:

        st.markdown(
            "### Content Brief"
        )

        st.write(
            info_text
        )

    reference_text = str(
        row.get(
            "Reference / Additional",
            ""
        )
    ).strip()

    if reference_text:

        st.markdown(
            "### Reference / Additional"
        )

        st.write(
            reference_text
        )

    caption_text = str(
        row.get(
            "Caption",
            ""
        )
    ).strip()

    if caption_text:

        st.markdown(
            "### Caption"
        )

        st.write(
            caption_text
        )

    st.divider()

    render_publish_form(
        row
    )

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Content Dashboard",
    layout="wide"
)



# =====================================================
# LOGIN
# =====================================================

if not login():
    st.stop()

# =====================================================
# CONFIG
# =====================================================

CONFIG_SHEET_URL = st.secrets[
    "CONFIG_SHEET_URL"
]

config_df = load_client_config(
    CONFIG_SHEET_URL
)

# =====================================================
# LOAD DATA
# =====================================================

master_df = load_all_clients(
    config_df
)

if master_df.empty:

    st.warning(
        "No content found."
    )

    st.stop()

# =====================================================
# DATE CLEANUP
# =====================================================

if "Publishing Date" in master_df.columns:

    master_df["Publishing Date"] = (
        master_df[
            "Publishing Date"
        ]
        .apply(
            parse_publish_date
        )
    )

today = pd.Timestamp.now().date()

calendar_df = master_df.dropna(
    subset=["Publishing Date"]
).copy()
# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title(
        "Content Dashboard"
    )

    selected_client = st.selectbox(
        "Client",
        ["All Clients"]
        +
        sorted(
            master_df["Client"]
            .dropna()
            .unique()
            .tolist()
        )
    )

    st.divider()

    page = st.radio(
        "Page",
        [
            "Dashboard",
            "Create Content"
        ]
    )

# =====================================================
# CREATE CONTENT PAGE
# =====================================================

if page == "Create Content":

    render_create_content(
        config_df
    )

    st.stop()

# =====================================================
# FILTERS
# =====================================================

filtered_df = calendar_df.copy()

if selected_client != "All Clients":

    filtered_df = filtered_df[
        filtered_df["Client"]
        ==
        selected_client
    ]

undated_df = master_df[
    master_df["Publishing Date"]
    .isna()
]

if selected_client != "All Clients":

    undated_df = undated_df[
        undated_df["Client"]
        ==
        selected_client
    ]

# =====================================================
# KPI DATA
# =====================================================

status_series = (
    filtered_df[
        "Publishing Status"
    ]
    .fillna("")
    .astype(str)
)

today_posts = filtered_df[
    filtered_df[
        "Publishing Date"
    ].dt.date
    ==
    today
]

today_pending = today_posts[
    status_series.loc[
        today_posts.index
    ]
    !=
    "Published"
]

today_published = today_posts[
    status_series.loc[
        today_posts.index
    ]
    ==
    "Published"
]

upcoming = filtered_df[
    (
        filtered_df[
            "Publishing Date"
        ].dt.date
        >
        today
    )
    &
    (
        filtered_df[
            "Publishing Date"
        ].dt.date
        <=
        (
            pd.Timestamp.now()
            +
            pd.Timedelta(days=7)
        ).date()
    )
]

overdue = filtered_df[
    (
        filtered_df[
            "Publishing Date"
        ].dt.date
        <
        today
    )
    &
    (
        status_series
        !=
        "Published"
    )
]

# =====================================================
# HEADER
# =====================================================

st.title(
    "Content Operations Dashboard"
)

# =====================================================
# KPI CARDS
# =====================================================

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Posts Today Pending",
    len(today_pending)
)

k2.metric(
    "Posts Today Published",
    len(today_published)
)

k3.metric(
    "Upcoming (7 Days)",
    len(upcoming)
)

k4.metric(
    "Overdue",
    len(overdue)
)

k5.metric(
    "Unscheduled",
    len(undated_df)
)

# =====================================================
# TODAY SECTION
# =====================================================

left_col, right_col = st.columns(2)

with left_col:

    st.subheader(
        "Today's Pending Posts"
    )

    if today_pending.empty:

        st.info(
            "No pending posts today."
        )

    else:

        for _, row in today_pending.iterrows():

            title = (
                f"[{row.get('Content ID','')}] "
                f"{row.get('Post Content Description','')}"
            )

            with st.expander(title):

                st.write(
                    row.to_dict()
                )

                if pd.notna(
                    row.get(
                        "Sheet Row ID"
                    )
                ):

                    sheet_url = (
                        get_sheet_row_url(
                            row[
                                "Spreadsheet URL"
                            ],
                            row[
                                "Worksheet GID"
                            ],
                            int(
                                row[
                                    "Sheet Row ID"
                                ]
                            )
                        )
                    )

                    st.link_button(
                        "Open Sheet Row",
                        sheet_url
                    )

with right_col:

    st.subheader(
        "Today's Published Posts"
    )

    if today_published.empty:

        st.info(
            "No published posts today."
        )

    else:

        for _, row in today_published.iterrows():

            title = (
                f"[{row.get('Content ID','')}] "
                f"{row.get('Post Content Description','')}"
            )

            with st.expander(title):

                st.write(
                    row.to_dict()
                )

# =====================================================
# CALENDAR
# =====================================================

st.divider()

st.subheader(
    "Publishing Calendar"
)

events = build_events(
    filtered_df
)

calendar_state = render_calendar(
    events
)

# =====================================================
# EVENT CLICK
# =====================================================

if calendar_state:

    clicked = calendar_state.get(
        "eventClick"
    )

    if clicked:

        try:

            content_id = (
                clicked["event"]
                ["extendedProps"]
                ["content_id"]
            )

        except Exception:

            content_id = None

        if content_id:

            selected = filtered_df[
                filtered_df[
                    "Content ID"
                ]
                ==
                content_id
            ]

            if not selected.empty:

                show_content_modal(
                    selected.iloc[0]
                )