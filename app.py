import streamlit as st
import pandas as pd

from modules.auth import login
from modules.config import load_client_config
from modules.sheets import (
    load_all_clients,
    get_sheet_row_url,
    update_asset_link,
    update_approval_status,
)
from modules.calendar_view import build_events, render_calendar
from modules.create_content import render_create_content
from modules.publish import render_publish_form
from modules.helpers import parse_publish_date
from modules.trello import get_approved_links


st.set_page_config(
    page_title="Max CMS",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


def is_approved(value):
    return str(value or "").strip().lower() in ["approved", "yes", "true", "done", "1"]


def format_display_date(value):
    try:
        if value is None or pd.isna(value):
            return "-"
        return pd.Timestamp(value).strftime("%d %b %Y")
    except Exception:
        return str(value) if value else "-"


def inject_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #f6f8fc;
            --bg-accent: #eef4ff;
            --panel: #ffffff;
            --panel-soft: #f8faff;
            --panel-muted: #f1f5f9;
            --border: #d9e2ec;
            --border-strong: #c7d2e3;
            --text: #132238;
            --muted: #5f728c;
            --soft-muted: #8a9ab0;
            --primary: #5b6df6;
            --primary-2: #2bb3d6;
            --primary-soft: #eef0ff;
            --success-bg: #eaf8ef;
            --success-text: #1f7a42;
            --warning-bg: #fff5e7;
            --warning-text: #a66300;
            --danger-bg: #feecee;
            --danger-text: #bf3f4c;
            --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
            --shadow-soft: 0 6px 18px rgba(15, 23, 42, 0.06);
            --radius-lg: 20px;
            --radius-md: 16px;
            --radius-sm: 12px;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: var(--text);
        }

        html, body, .stApp, .block-container, p, span, label, small, li, div {
            color: var(--text);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(91, 109, 246, 0.10), transparent 25%),
                radial-gradient(circle at top left, rgba(43, 179, 214, 0.08), transparent 22%),
                linear-gradient(180deg, #f8fbff 0%, #f3f7fc 100%);
            color: var(--text);
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
            min-height: 0 !important;
        }

        [data-testid="stToolbar"],
        .stAppDeployButton,
        #MainMenu,
        footer {
            visibility: hidden !important;
            display: none !important;
        }

        .block-container {
            padding-top: 0.8rem;
            padding-bottom: 2rem;
            max-width: 1450px;
        }

        h1, h2, h3, h4, h5, h6,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6 {
            color: var(--text) !important;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fbff 0%, #f2f7fd 100%) !important;
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        section[data-testid="stSidebar"] .stTextInput input,
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] .stDateInput input {
            color: var(--text) !important;
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            box-shadow: none !important;
        }

        [data-testid="stDialog"] > div,
        [data-testid="stDialog"] [role="dialog"] {
            background: #ffffff !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 20px !important;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.16) !important;
        }

        [data-testid="stDialog"] * {
            color: var(--text) !important;
        }

        [data-testid="stDialog"] .stTextArea textarea,
        [data-testid="stDialog"] .stTextInput input,
        [data-testid="stDialog"] .stDateInput input {
            color: var(--text) !important;
            background: #ffffff !important;
        }

        .hero-shell {
            border: 1px solid #dbe5f0;
            background:
                linear-gradient(135deg, rgba(91, 109, 246, 0.10), rgba(43, 179, 214, 0.08)),
                #ffffff;
            border-radius: 24px;
            padding: 1.25rem 1.4rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .hero-kicker {
            font-size: 0.8rem;
            color: #667eea !important;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.05;
            margin-bottom: 0.2rem;
            color: var(--text) !important;
        }

        .hero-sub {
            color: var(--muted) !important;
            font-size: 0.98rem;
            line-height: 1.6;
        }

        .glass-card {
            border: 1px solid var(--border);
            background: #ffffff;
            border-radius: 18px;
            padding: 1rem;
            box-shadow: var(--shadow);
        }

        .mini-card {
            border: 1px solid var(--border);
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border-radius: 16px;
            padding: 0.95rem 1rem;
            min-height: 112px;
            box-shadow: var(--shadow-soft);
        }

        .mini-label {
            color: var(--muted) !important;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            margin-bottom: 0.35rem;
        }

        .mini-value {
            font-size: 2rem;
            line-height: 1;
            font-weight: 800;
            color: var(--text) !important;
            margin-bottom: 0.35rem;
        }

        .mini-sub {
            color: var(--muted) !important;
            font-size: 0.88rem;
        }

        .section-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 1rem 0 0.7rem 0;
        }

        .section-head h3 {
            margin: 0;
            font-size: 1.1rem;
            color: var(--text) !important;
        }

        .section-note {
            color: var(--muted) !important;
            font-size: 0.85rem;
        }

        .status-pill {
            display: inline-block;
            padding: 0.30rem 0.68rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            border: 1px solid transparent;
            background: #edf2f7;
            color: #4a5d75 !important;
        }

        .status-published {
            background: var(--success-bg);
            color: var(--success-text) !important;
            border-color: rgba(31, 122, 66, 0.10);
        }

        .status-approved {
            background: #ecfdf3;
            color: #15803d !important;
            border-color: rgba(21, 128, 61, 0.10);
        }

        .status-pending {
            background: var(--warning-bg);
            color: var(--warning-text) !important;
            border-color: rgba(166, 99, 0, 0.10);
        }

        .status-overdue {
            background: var(--danger-bg);
            color: var(--danger-text) !important;
            border-color: rgba(191, 63, 76, 0.10);
        }

        .pill-row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
            margin-bottom: 0.1rem;
        }

        .click-card {
            border: 1px solid var(--border);
            background: #ffffff;
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: 0.45rem;
            box-shadow: var(--shadow-soft);
        }

        .click-card-title {
            font-weight: 800;
            color: var(--text) !important;
            font-size: 1rem;
            margin-bottom: 0.35rem;
        }

        .click-card-sub {
            color: var(--muted) !important;
            font-size: 0.9rem;
            margin-bottom: 0.7rem;
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--border) !important;
            background: #ffffff !important;
            border-radius: 16px !important;
            overflow: hidden;
            margin-bottom: 0.75rem;
            box-shadow: var(--shadow-soft);
        }

        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {
            background: #ffffff !important;
            color: var(--text) !important;
        }

        .queue-simple {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .queue-topline {
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            color: var(--muted) !important;
            font-size: 0.92rem;
        }

        .queue-topline strong {
            color: var(--text) !important;
        }

        .stMarkdown,
        .stText,
        .stCaption,
        [data-testid="stMarkdownContainer"],
        [data-testid="stCaptionContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] *,
        [data-testid="stForm"] label,
        [data-testid="stForm"] p,
        [data-testid="stForm"] div,
        [data-testid="stForm"] span,
        label, small {
            color: var(--text) !important;
        }

        .row-widget.stSelectbox label,
        .row-widget.stTextInput label,
        .row-widget.stTextArea label,
        .row-widget.stDateInput label,
        .row-widget.stMultiSelect label,
        .row-widget.stCheckbox label,
        .row-widget.stRadio label,
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span {
            color: var(--muted) !important;
            opacity: 1 !important;
        }

        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stDateInput input,
        .stNumberInput input,
        .stTimeInput input,
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
            border-radius: 14px !important;
            box-shadow: none !important;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus,
        .stNumberInput input:focus,
        .stTimeInput input:focus {
            border-color: rgba(91, 109, 246, 0.45) !important;
            box-shadow: 0 0 0 3px rgba(91, 109, 246, 0.12) !important;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder,
        input::placeholder,
        textarea::placeholder {
            color: var(--soft-muted) !important;
            -webkit-text-fill-color: var(--soft-muted) !important;
            opacity: 1 !important;
        }

        [data-baseweb="select"] *,
        [data-baseweb="tag"] *,
        [data-baseweb="popover"] *,
        [data-baseweb="menu"] *,
        [data-baseweb="input"] * {
            color: var(--text) !important;
        }

        [data-baseweb="tag"] {
            background: #eef2ff !important;
            color: #4451d1 !important;
            border: 1px solid #d8defc !important;
        }

        .stCheckbox label, .stCheckbox span,
        .stRadio label, .stRadio span,
        [data-testid="stCheckbox"] label,
        [data-testid="stCheckbox"] div,
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] div {
            color: var(--text) !important;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button,
        button[kind="primary"],
        button[kind="secondary"] {
            background: linear-gradient(135deg, #5b6df6 0%, #2bb3d6 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            padding: 0.64rem 1rem !important;
            transition: 0.2s ease !important;
            box-shadow: 0 10px 24px rgba(91, 109, 246, 0.18) !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 28px rgba(91, 109, 246, 0.22) !important;
        }

        .stButton > button *,
        .stDownloadButton > button *,
        .stFormSubmitButton > button *,
        button[kind="primary"] *,
        button[kind="secondary"] * {
            color: #ffffff !important;
            fill: #ffffff !important;
        }

        .stFormSubmitButton > button {
            min-height: 46px !important;
        }

        .stLinkButton a {
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
            background: #ffffff !important;
            color: var(--text) !important;
            box-shadow: none !important;
        }

        .stLinkButton a:hover {
            background: #f8fbff !important;
            border-color: var(--border-strong) !important;
        }

        .stLinkButton a * {
            color: var(--text) !important;
        }

        .stTabs [data-baseweb="tab"] {
            background: #f6f8fc;
            border: 1px solid var(--border);
            color: var(--muted) !important;
            border-radius: 12px 12px 0 0;
        }

        .stTabs [aria-selected="true"] {
            color: var(--text) !important;
            background: #ffffff !important;
            border-bottom-color: #ffffff !important;
        }

        .calendar-shell {
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.5rem;
            background: #ffffff;
            box-shadow: var(--shadow);
        }

        [data-baseweb="popover"] {
            z-index: 999999 !important;
            background: #ffffff !important;
            border-radius: 16px !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.12) !important;
        }

        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div,
        div[data-baseweb="popover"] > div > div,
        div[data-baseweb="layer"],
        div[data-baseweb="layer"] > div,
        div[role="presentation"],
        div[role="dialog"] {
            background: #ffffff !important;
        }

        [data-baseweb="calendar"],
        [data-baseweb="datepicker"],
        [role="dialog"] [data-baseweb="calendar"],
        [role="dialog"] [data-baseweb="datepicker"] {
            background: #ffffff !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 16px !important;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.12) !important;
            opacity: 1 !important;
        }

        [data-baseweb="calendar"] div,
        [data-baseweb="datepicker"] div,
        [data-baseweb="calendar"] section,
        [data-baseweb="datepicker"] section,
        [data-baseweb="calendar"] article,
        [data-baseweb="datepicker"] article {
            background-color: #ffffff !important;
            color: var(--text) !important;
        }

        [data-baseweb="calendar"] header,
        [data-baseweb="datepicker"] header,
        [data-baseweb="calendar"] nav,
        [data-baseweb="datepicker"] nav {
            background: #ffffff !important;
            color: var(--text) !important;
        }

        [data-baseweb="calendar"] button,
        [data-baseweb="datepicker"] button {
            background: transparent !important;
            color: var(--text) !important;
            box-shadow: none !important;
        }

        [data-baseweb="calendar"] abbr,
        [data-baseweb="datepicker"] abbr {
            color: var(--muted) !important;
            text-decoration: none !important;
            background: transparent !important;
        }

        [data-baseweb="calendar"] [role="grid"],
        [data-baseweb="datepicker"] [role="grid"],
        [data-baseweb="calendar"] [role="row"],
        [data-baseweb="datepicker"] [role="row"],
        [data-baseweb="calendar"] [role="gridcell"],
        [data-baseweb="datepicker"] [role="gridcell"] {
            background: #ffffff !important;
            color: var(--text) !important;
        }

        [data-baseweb="calendar"] [role="gridcell"] > *,
        [data-baseweb="datepicker"] [role="gridcell"] > *,
        [data-baseweb="calendar"] [role="gridcell"] > * > *,
        [data-baseweb="datepicker"] [role="gridcell"] > * > * {
            background: #ffffff !important;
            color: var(--text) !important;
            border-color: transparent !important;
        }

        [data-baseweb="calendar"] [aria-selected="false"],
        [data-baseweb="datepicker"] [aria-selected="false"],
        [data-baseweb="calendar"] [aria-selected="false"] > *,
        [data-baseweb="datepicker"] [aria-selected="false"] > *,
        [data-baseweb="calendar"] [aria-selected="false"] > * > *,
        [data-baseweb="datepicker"] [aria-selected="false"] > * > * {
            background: #ffffff !important;
            color: var(--text) !important;
        }

        [data-baseweb="calendar"] [role="gridcell"]:hover,
        [data-baseweb="datepicker"] [role="gridcell"]:hover,
        [data-baseweb="calendar"] [role="gridcell"]:hover > *,
        [data-baseweb="datepicker"] [role="gridcell"]:hover > *,
        [data-baseweb="calendar"] [role="gridcell"]:hover button,
        [data-baseweb="datepicker"] [role="gridcell"]:hover button {
            background: rgba(91, 109, 246, 0.08) !important;
            color: var(--text) !important;
            border-radius: 10px !important;
        }

        [data-baseweb="calendar"] [aria-selected="true"],
        [data-baseweb="datepicker"] [aria-selected="true"] {
            background: transparent !important;
        }

        [data-baseweb="calendar"] [aria-selected="true"] button,
        [data-baseweb="datepicker"] [aria-selected="true"] button {
            background: linear-gradient(135deg, #5b6df6 0%, #2bb3d6 100%) !important;
            color: #ffffff !important;
            border-radius: 999px !important;
        }

        [data-baseweb="calendar"] [tabindex="0"],
        [data-baseweb="datepicker"] [tabindex="0"] {
            box-shadow: inset 0 0 0 1px rgba(91, 109, 246, 0.35) !important;
            border-radius: 999px !important;
        }

        [data-baseweb="calendar"] [aria-disabled="true"],
        [data-baseweb="datepicker"] [aria-disabled="true"],
        [data-baseweb="calendar"] [aria-disabled="true"] *,
        [data-baseweb="datepicker"] [aria-disabled="true"] * {
            background: #ffffff !important;
            color: rgba(95, 114, 140, 0.40) !important;
        }

        [data-baseweb="calendar"] table,
        [data-baseweb="calendar"] thead,
        [data-baseweb="calendar"] tbody,
        [data-baseweb="calendar"] tr,
        [data-baseweb="calendar"] td,
        [data-baseweb="calendar"] th,
        [data-baseweb="datepicker"] table,
        [data-baseweb="datepicker"] thead,
        [data-baseweb="datepicker"] tbody,
        [data-baseweb="datepicker"] tr,
        [data-baseweb="datepicker"] td,
        [data-baseweb="datepicker"] th {
            background: #ffffff !important;
            color: var(--text) !important;
        }

        ul[role="listbox"],
        ul[role="listbox"] *,
        li[role="option"],
        li[role="option"] * {
            background: #ffffff !important;
            color: var(--text) !important;
        }

        li[role="option"] {
            border-bottom: 1px solid rgba(217, 226, 236, 0.7) !important;
        }

        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background: rgba(91, 109, 246, 0.08) !important;
            color: var(--text) !important;
        }

        iframe {
            border-radius: 16px !important;
        }

        .stAlert {
            border-radius: 14px !important;
            border: 1px solid var(--border) !important;
            background: #ffffff !important;
            color: var(--text) !important;
        }

        hr {
            border-color: var(--border) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def approval_badge(row):
    internal_ok = is_approved(row.get("Internal Approval", ""))
    client_ok = is_approved(row.get("Approval", ""))

    if internal_ok and client_ok:
        return '<span class="status-pill status-approved">Fully Approved</span>'
    if internal_ok or client_ok:
        return '<span class="status-pill status-pending">Partially Approved</span>'
    return '<span class="status-pill status-overdue">Awaiting Approval</span>'


def format_status_badge(status, publish_date=None, row=None):
    status = str(status or "Pending").strip()
    today = pd.Timestamp.now().date()
    css_class = "status-pending"

    if status.lower() == "published":
        css_class = "status-published"
    elif row is not None:
        internal_ok = is_approved(row.get("Internal Approval", ""))
        client_ok = is_approved(row.get("Approval", ""))

        if internal_ok and client_ok:
            css_class = "status-approved"
        else:
            try:
                if publish_date is not None and pd.notna(publish_date):
                    if pd.Timestamp(publish_date).date() < today:
                        css_class = "status-overdue"
            except Exception:
                pass

    return f'<span class="status-pill {css_class}">{status}</span>'


def open_modal(content_id=None, sheet_row_id=None):
    st.session_state["selected_content_id"] = str(content_id or "").strip()
    st.session_state["selected_sheet_row_id"] = str(sheet_row_id or "").strip()
    st.session_state["show_detail_modal"] = True


def render_click_card(row, button_key):
    content_id = str(row.get("Content ID", "")).strip()
    sheet_row_id = str(row.get("Sheet Row ID", "")).strip()
    description = str(row.get("Post Content Description", "")).strip()
    client_name = str(row.get("Client", "")).strip()
    publish_date = format_display_date(row.get("Publishing Date"))
    status_badge = format_status_badge(
        row.get("Publishing Status", "Pending"),
        row.get("Publishing Date"),
        row=row,
    )

    title_prefix = f"[{content_id}] " if content_id else ""
    button_label = f"Open [{content_id}]" if content_id else "Open Details"

    st.markdown(
        f"""
        <div class="click-card">
            <div class="click-card-title">{title_prefix}{description}</div>
            <div class="click-card-sub">{client_name} · {publish_date}</div>
            <div class="pill-row">
                {status_badge}
                {approval_badge(row)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        button_label,
        key=button_key,
        use_container_width=True,
    ):
        open_modal(content_id=content_id, sheet_row_id=sheet_row_id)


def render_hero(master_df, selected_client):
    total_items = len(master_df)
    published = int(
        master_df["Publishing Status"].fillna("").astype(str).str.lower().eq("published").sum()
    ) if "Publishing Status" in master_df.columns else 0

    client_text = selected_client if selected_client != "All Clients" else "All clients"

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">MAX LEVEL</div>
            <div class="hero-title">Max Level Content Dashboard</div>
            <div class="hero-sub">
                Viewing <b>{client_text}</b> · {total_items} total content items · {published} already published.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quick_list(df, title, empty_text, key_prefix, max_items=8):
    st.markdown(
        f"""
        <div class="section-head">
            <h3>{title}</h3>
            <div class="section-note">{len(df)} items</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info(empty_text)
        return

    preview = df.head(max_items)

    for idx, (_, row) in enumerate(preview.iterrows()):
        render_click_card(
            row,
            f"{key_prefix}_{idx}_{row.get('Content ID','')}_{row.get('Sheet Row ID','')}",
        )


def render_queue_approval_controls(row, idx):
    row_number = int(row["Sheet Row ID"])
    content_id = str(row.get("Content ID", "")).strip()

    current_internal = is_approved(row.get("Internal Approval", ""))
    current_client = is_approved(row.get("Approval", ""))

    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        internal_val = st.checkbox(
            "Internal Approval",
            value=current_internal,
            key=f"queue_internal_{content_id}_{row_number}_{idx}",
        )

    with c2:
        client_val = st.checkbox(
            "Client Approval",
            value=current_client,
            key=f"queue_client_{content_id}_{row_number}_{idx}",
        )

    with c3:
        st.write("")
        if st.button(
            "Save Approvals",
            key=f"queue_save_approvals_{content_id}_{row_number}_{idx}",
            use_container_width=True,
        ):
            try:
                update_approval_status(
                    spreadsheet_url=row["Spreadsheet URL"],
                    worksheet_name=row["Worksheet Name"],
                    row_number=row_number,
                    internal_approval=internal_val,
                    client_approval=client_val,
                )
                st.success("Approval status updated.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(str(e))


@st.dialog("Content Details", width="large")
def detail_modal():
    content_id = str(st.session_state.get("selected_content_id", "")).strip()
    sheet_row_id = str(st.session_state.get("selected_sheet_row_id", "")).strip()

    filtered_source = st.session_state.get("modal_source_df")
    if filtered_source is None or filtered_source.empty:
        st.write("No content found.")
        return

    selected = pd.DataFrame()

    if content_id:
        selected = filtered_source[
            filtered_source["Content ID"].fillna("").astype(str).str.strip() == content_id
        ]

    if selected.empty and sheet_row_id:
        selected = filtered_source[
            filtered_source["Sheet Row ID"].fillna("").astype(str).str.strip() == sheet_row_id
        ]

    if selected.empty:
        st.write("No content found.")
        return

    row = selected.iloc[0]
    row_content_id = str(row.get("Content ID", "")).strip()
    title = str(row.get("Post Content Description", "")).strip()
    display_id = f"[{row_content_id}] " if row_content_id else ""

    st.markdown(
        f"""
        <div class="glass-card">
            <div class="hero-kicker">CONTENT DETAIL</div>
            <div class="hero-title" style="font-size:1.45rem;">{display_id}{title}</div>
            <div class="hero-sub">Review details, fetch assets, update approvals, and publish from one place.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([3, 1])

    with left:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Type**  \n{row.get('Type', '-')}")
            st.markdown(f"**Publish Date**  \n{format_display_date(row.get('Publishing Date'))}")
            st.markdown(f"**Platforms**  \n{row.get('Channel(s)', '-')}")
        with c2:
            st.markdown(f"**Status**  \n{row.get('Publishing Status', 'Pending')}")
            st.markdown(f"**Client Approval**  \n{row.get('Approval', 'Pending')}")
            st.markdown(f"**Internal Approval**  \n{row.get('Internal Approval', 'Pending')}")
        with c3:
            st.markdown(f"**Ratio**  \n{row.get('Ratio', '-')}")
            st.markdown(f"**Day**  \n{row.get('Day', '-')}")
            st.markdown(f"**Client**  \n{row.get('Client', '-')}")

    with right:
        trello_url = str(row.get("Trello Card URL", "")).strip()
        actual_sheet_row_id = str(row.get("Sheet Row ID", "")).strip()

        if trello_url:
            st.link_button("Open Trello Card", trello_url, width="stretch")

        if actual_sheet_row_id:
            try:
                row_url = get_sheet_row_url(
                    row["Spreadsheet URL"],
                    row["Worksheet GID"],
                    int(actual_sheet_row_id),
                )
                st.link_button("Open Sheet Row", row_url, width="stretch")
            except Exception:
                pass

    st.divider()

    asset_link = row.get("Asset Link", "")
    a1, a2 = st.columns([2, 1])

    with a1:
        st.markdown("### Assets")

        asset_text = "" if pd.isna(asset_link) else str(asset_link)

        asset_links = []
        for part in asset_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            clean_link = str(part).strip()
            if clean_link and clean_link.lower().startswith(("http://", "https://")):
                asset_links.append(clean_link)

        if asset_links:
            for idx, link in enumerate(asset_links, start=1):
                st.link_button(
                    f"Open Asset {idx}",
                    url=link,
                    key=f"modal_asset_{row_content_id or actual_sheet_row_id}_{idx}",
                    width="stretch",
                )
        else:
            st.markdown(":red[No Asset Attached Yet]")

    with a2:
        st.markdown("### Actions")
        if st.button(
            "Fetch Assets From Trello",
            key=f"fetch_asset_{row_content_id or actual_sheet_row_id}",
            use_container_width=True,
        ):
            try:
                card_reference = (
                    str(row.get("Trello Card ID", "")).strip()
                    or str(row.get("Trello Card URL", "")).strip()
                )

                if not card_reference:
                    st.error("No Trello Card found.")
                else:
                    links = get_approved_links(card_reference)

                    if not links:
                        st.warning("No approved links found.")
                    else:
                        update_asset_link(
                            spreadsheet_url=row["Spreadsheet URL"],
                            worksheet_name=row["Worksheet Name"],
                            row_number=int(actual_sheet_row_id),
                            asset_links=links,
                        )
                        st.success(f"Fetched {len(links)} asset link(s).")
                        st.cache_data.clear()
                        st.rerun()
            except Exception as e:
                st.error(str(e))

    info_text = str(row.get("Info", "")).strip()
    reference_text = str(row.get("Reference / Additional", "")).strip()
    caption_text = str(row.get("Caption", "")).strip()

    tab1, tab2, tab3 = st.tabs(["Brief", "Reference", "Caption"])

    with tab1:
        st.write(info_text if info_text else "No brief added.")

    with tab2:
        st.write(reference_text if reference_text else "No references added.")

    with tab3:
        st.write(caption_text if caption_text else "No caption added.")

    st.divider()
    render_publish_form(row)


inject_theme()

if not login():
    st.stop()

CONFIG_SHEET_URL = st.secrets["CONFIG_SHEET_URL"]
config_df = load_client_config(CONFIG_SHEET_URL)

master_df = load_all_clients(config_df)

if master_df.empty:
    st.warning("No content found.")
    st.stop()

if "Publishing Date" in master_df.columns:
    master_df["Publishing Date"] = master_df["Publishing Date"].apply(parse_publish_date)

today = pd.Timestamp.now().date()
calendar_df = master_df.dropna(subset=["Publishing Date"]).copy()

with st.sidebar:
    st.markdown("## Max CMS")

    selected_client = st.selectbox(
        "Client",
        ["All Clients"] + sorted(master_df["Client"].dropna().unique().tolist()),
    )

    page = st.radio(
        "Workspace",
        ["Dashboard", "Create Content"],
        horizontal=False,
    )

    st.divider()

    search_query = st.text_input(
        "Quick Search",
        placeholder="Search content ID / description",
    )

    show_only_pending = st.toggle("Only Pending", value=False)
    show_only_with_assets = st.toggle("Only With Assets", value=False)

if page == "Create Content":
    render_create_content(config_df)
    st.stop()

filtered_df = calendar_df.copy()
base_df = master_df.copy()

if selected_client != "All Clients":
    filtered_df = filtered_df[filtered_df["Client"] == selected_client]
    base_df = base_df[base_df["Client"] == selected_client]

if search_query:
    base_mask = (
        base_df["Content ID"].fillna("").astype(str).str.contains(search_query, case=False, na=False)
        | base_df["Post Content Description"].fillna("").astype(str).str.contains(search_query, case=False, na=False)
    )
    cal_mask = (
        filtered_df["Content ID"].fillna("").astype(str).str.contains(search_query, case=False, na=False)
        | filtered_df["Post Content Description"].fillna("").astype(str).str.contains(search_query, case=False, na=False)
    )
    base_df = base_df[base_mask]
    filtered_df = filtered_df[cal_mask]

if show_only_pending:
    base_df = base_df[
        base_df["Publishing Status"].fillna("").astype(str).str.lower() != "published"
    ]
    filtered_df = filtered_df[
        filtered_df["Publishing Status"].fillna("").astype(str).str.lower() != "published"
    ]

if show_only_with_assets:
    base_df = base_df[base_df["Asset Link"].fillna("").astype(str).str.strip() != ""]
    filtered_df = filtered_df[filtered_df["Asset Link"].fillna("").astype(str).str.strip() != ""]

st.session_state["modal_source_df"] = filtered_df.copy()

undated_df = base_df[base_df["Publishing Date"].isna()].copy()

status_series = filtered_df["Publishing Status"].fillna("").astype(str)

today_posts = filtered_df[filtered_df["Publishing Date"].dt.date == today]
today_pending = today_posts[status_series.loc[today_posts.index] != "Published"]
today_published = today_posts[status_series.loc[today_posts.index] == "Published"]

upcoming = filtered_df[
    (filtered_df["Publishing Date"].dt.date > today)
    & (filtered_df["Publishing Date"].dt.date <= (pd.Timestamp.now() + pd.Timedelta(days=7)).date())
]

overdue = filtered_df[
    (filtered_df["Publishing Date"].dt.date < today)
    & (status_series != "Published")
]

render_hero(base_df, selected_client)

k1, k2, k3, k4, k5 = st.columns(5)

cards = [
    ("Today Pending", len(today_pending), "Items waiting to be published today"),
    ("Today Published", len(today_published), "Already pushed live today"),
    ("Upcoming 7 Days", len(upcoming), "Scheduled and approaching quickly"),
    ("Overdue", len(overdue), "Past due and not yet published"),
    ("Unscheduled", len(undated_df), "Need publishing date assignment"),
]

for col, (label, value, sub) in zip([k1, k2, k3, k4, k5], cards):
    with col:
        st.markdown(
            f"""
            <div class="mini-card">
                <div class="mini-label">{label}</div>
                <div class="mini-value">{value}</div>
                <div class="mini-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

left_col, right_col = st.columns(2)

with left_col:
    render_quick_list(
        today_pending.sort_values("Publishing Date"),
        "Today's Pending Posts",
        "No pending posts today.",
        "today_pending",
    )

with right_col:
    render_quick_list(
        upcoming.sort_values("Publishing Date"),
        "Upcoming Posts",
        "No upcoming posts in the next 7 days.",
        "upcoming",
    )

st.markdown(
    """
    <div class="section-head">
        <h3>Publishing Calendar</h3>
        <div class="section-note">Click any event for full details</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="calendar-shell">', unsafe_allow_html=True)
events = build_events(filtered_df)
calendar_state = render_calendar(events)
st.markdown("</div>", unsafe_allow_html=True)

if calendar_state:
    clicked = calendar_state.get("eventClick")
    if clicked:
        try:
            extended = clicked["event"].get("extendedProps", {})
            content_id = str(extended.get("content_id", "")).strip()
            sheet_row_id = str(extended.get("sheet_row_id", "")).strip()
            open_modal(content_id=content_id, sheet_row_id=sheet_row_id)
        except Exception:
            pass

st.markdown(
    """
    <div class="section-head">
        <h3>Content Queue</h3>
        <div class="section-note">Latest items from the current filtered view</div>
    </div>
    """,
    unsafe_allow_html=True,
)

queue_df = base_df.copy()
if "Publishing Date" in queue_df.columns:
    queue_df = queue_df.sort_values("Publishing Date", ascending=True, na_position="last")

for idx, row in queue_df.head(15).iterrows():
    row_content_id = str(row.get("Content ID", "")).strip()
    row_title = str(row.get("Post Content Description", "")).strip()
    title_prefix = f"[{row_content_id}] " if row_content_id else ""
    title = f"{title_prefix}{row_title}"

    with st.expander(title):
        st.markdown('<div class="queue-simple">', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="queue-topline">
                <div><strong>Client:</strong> {row.get('Client', '-')}</div>
                <div><strong>Publishing Date:</strong> {format_display_date(row.get('Publishing Date'))}</div>
                <div><strong>Type:</strong> {row.get('Type', '-')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="pill-row">
                {format_status_badge(row.get("Publishing Status", "Pending"), row.get("Publishing Date"), row=row)}
                {approval_badge(row)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_queue_approval_controls(row, idx)

        action1, action2 = st.columns(2)

        with action1:
            if pd.notna(row.get("Sheet Row ID")):
                try:
                    sheet_url = get_sheet_row_url(
                        row["Spreadsheet URL"],
                        row["Worksheet GID"],
                        int(row["Sheet Row ID"]),
                    )
                    st.link_button(
                        "Open Sheet Row",
                        sheet_url,
                        key=f"sheet_link_{row.get('Content ID','')}_{row.get('Sheet Row ID','')}_{idx}",
                        width="stretch",
                    )
                except Exception:
                    pass

        with action2:
            if st.button(
                "Open Detail View",
                key=f"open_detail_{row.get('Content ID','')}_{row.get('Sheet Row ID','')}_{idx}",
                use_container_width=True,
            ):
                open_modal(
                    content_id=str(row.get("Content ID", "")).strip(),
                    sheet_row_id=str(row.get("Sheet Row ID", "")).strip(),
                )

        st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get("show_detail_modal"):
    detail_modal()
    st.session_state["show_detail_modal"] = False