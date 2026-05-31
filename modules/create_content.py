# modules/create_content.py

import streamlit as st
import pandas as pd

from datetime import timedelta, datetime, time

from modules.sheets import (
    append_content_row,
    sort_sheet_by_publish_date,
)
from modules.trello import (
    get_list_by_name,
    get_cards,
    create_card,
    sort_list_by_due_date,
)
from modules.helpers import get_next_content_id


TYPE_OPTIONS = ["Reel", "Static", "Carousel", "Video"]
RATIO_OPTIONS = ["1:1", "4:5", "9:16", "16:9"]
ASSET_MADE_BY_OPTIONS = ["Max Level", "Client", "Freelancer"]
CHANNEL_OPTIONS = ["FB", "IG", "YT", "LinkedIn", "X"]


def render_create_content(config_df):
    st.markdown(
        """
        <div class="hero-shell">
            <div class="hero-kicker">CREATE</div>
            <div class="hero-title">Create a new content piece.</div>
            <div class="hero-sub">Set the publishing date, define the creative brief, and push a clean entry into Trello and Sheets.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-head">
            <h3>New Content Entry</h3>
            <div class="section-note">Everything below is saved in one go</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_client = st.selectbox("Client", config_df["Client"].tolist())

    client_row = config_df[config_df["Client"] == selected_client].iloc[0]
    spreadsheet_url = client_row["Spreadsheet URL"]
    worksheet_name = client_row["Worksheet Name"]
    prefix = client_row["Prefix"]
    board_name = client_row["Trello Board Name"]
    list_name = client_row["Trello List Name"]

    form_shell_start = """
    <div style="
        border: 1px solid #d9e2ec;
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border-radius: 18px;
        padding: 1rem 1rem 0.5rem 1rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
        margin-bottom: 1rem;
    ">
    """

    st.markdown(form_shell_start, unsafe_allow_html=True)

    with st.form("create_content_form", clear_on_submit=False, border=False):
        st.markdown("### Scheduling")
        publish_date = st.date_input(
            "Publishing Date",
            help="This drives the publishing date in Sheets and the production due date in Trello.",
        )

        publish_ts = pd.Timestamp(publish_date)
        production_date = publish_ts - timedelta(days=4)
        due_date = datetime.combine(production_date.date(), time(18, 0))
        day_name = publish_ts.strftime("%A")

        s1, s2, s3 = st.columns(3)
        with s1:
            st.caption("Production Date")
            st.markdown(f"**{production_date.strftime('%d %b %Y')}**")
        with s2:
            st.caption("Publish Day")
            st.markdown(f"**{day_name}**")
        with s3:
            st.caption("Trello Due Time")
            st.markdown(f"**{due_date.strftime('%d %b %Y, %I:%M %p')}**")

        st.markdown("### Content Details")
        post_description = st.text_input(
            "Post Content Description",
            help="Short working title for the content piece.",
            placeholder="Example: Summer offer reel with creator cutdown",
        )

        col1, col2 = st.columns(2)
        with col1:
            content_type = st.selectbox("Type", TYPE_OPTIONS)
            ratio = st.selectbox("Ratio", RATIO_OPTIONS, index=2)
        with col2:
            asset_made_by = st.selectbox("Asset Made By", ASSET_MADE_BY_OPTIONS)
            channels = st.multiselect("Channel(s)", CHANNEL_OPTIONS, default=["IG"])

        st.markdown("### Approval Setup")
        a1, a2 = st.columns(2)
        with a1:
            internal_approval = st.checkbox("Internal Approval")
        with a2:
            client_approval = st.checkbox("Client Approval")

        st.markdown("### Creative Brief")
        info = st.text_area(
            "Info",
            height=180,
            help="Explain what needs to be created. Mention CTA, hooks, visual direction, deliverables, and objective.",
            placeholder="Write the brief, hook, CTA, angle, format notes, and any creative instructions here.",
        )
        reference = st.text_area(
            "Reference / Additional",
            height=120,
            help="Links, examples, inspiration, source notes, supporting context.",
            placeholder="Paste URLs, reference examples, creator inspiration, or notes here.",
        )
        caption = st.text_area(
            "Caption",
            height=150,
            help="Final caption or a caption brief for the team.",
            placeholder="Draft the caption or explain what the caption should communicate.",
        )

        st.markdown("### Review")
        review_channels = ", ".join(channels) if channels else "No channels selected"
        review_description = post_description.strip() if str(post_description).strip() else "Untitled content"

        r1, r2, r3 = st.columns(3)
        with r1:
            st.caption("Client")
            st.markdown(f"**{selected_client}**")
        with r2:
            st.caption("Type / Ratio")
            st.markdown(f"**{content_type} · {ratio}**")
        with r3:
            st.caption("Channels")
            st.markdown(f"**{review_channels}**")

        st.caption(f"Ready to create: {review_description}")

        submitted = st.form_submit_button("Create Content", use_container_width=True)

        if not submitted:
            st.markdown("</div>", unsafe_allow_html=True)
            return

        if not str(post_description).strip():
            st.markdown("</div>", unsafe_allow_html=True)
            st.error("Post Content Description is required.")
            return

        if not channels:
            st.markdown("</div>", unsafe_allow_html=True)
            st.error("Please select at least one channel.")
            return

        try:
            trello_list = get_list_by_name(board_name, list_name)

            if not trello_list:
                st.markdown("</div>", unsafe_allow_html=True)
                st.error("Trello list not found.")
                return

            cards = get_cards(trello_list["id"])
            content_id = get_next_content_id(prefix, cards)

            card_title = f"[{content_id}] {post_description.strip()}"
            card_description = f"""
Content ID:
{content_id}

Client:
{selected_client}

Publishing Date:
{publish_ts.strftime('%d %b %Y')}

Description:
{post_description.strip()}
"""

            card = create_card(
                trello_list["id"],
                card_title,
                card_description,
                due_date.isoformat(),
            )

            sort_list_by_due_date(
                trello_list["id"]
            )

            row_data = {
                "Production": production_date.strftime("%d %b"),
                "Publishing Date": publish_ts.strftime("%Y-%m-%d"),
                "Day": day_name,
                "Post Content Description": post_description.strip(),
                "Type": content_type,
                "Ratio": ratio,
                "Asset Made By": asset_made_by,
                "Channel(s)": ", ".join(channels),
                "Info": info.strip(),
                "Reference / Additional": reference.strip(),
                "Caption": caption.strip(),
                "Internal Approval": "Approved" if internal_approval else "Pending",
                "Approval": "Approved" if client_approval else "Pending",
                "Content ID": content_id,
                "Publishing Status": "Pending",
                "Trello Card URL": card["url"],
                "Trello Card ID": card["id"],
            }

            append_content_row(
                spreadsheet_url,
                worksheet_name,
                row_data,
            )




            st.markdown("</div>", unsafe_allow_html=True)
            st.success(f"{content_id} created successfully.")
            st.cache_data.clear()
            st.rerun()

        except Exception as e:
            st.markdown("</div>", unsafe_allow_html=True)
            st.error(f"Error: {e}")