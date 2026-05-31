# modules/calendar_view.py

import hashlib
import colorsys
import pandas as pd
from streamlit_calendar import calendar


APPROVED_FILL = "#eaf8ef"
APPROVED_BORDER = "#22c55e"
APPROVED_TEXT = "#166534"

PUBLISHED_FILL = "#e6f9f3"
PUBLISHED_BORDER = "#10b981"
PUBLISHED_TEXT = "#065f46"

OVERDUE_FILL = "#feecee"
OVERDUE_BORDER = "#ef4444"
OVERDUE_TEXT = "#991b1b"

DEFAULT_FILL = "#ffffff"
DEFAULT_TEXT = "#132238"
DEFAULT_MUTED = "#5f728c"
DEFAULT_BORDER = "#d9e2ec"
TODAY_BG = "#f2f7ff"


def is_approved(value):
    return str(value or "").strip().lower() in ["approved", "yes", "true", "done", "1"]


def hsl_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return "#{:02x}{:02x}{:02x}".format(
        int(r * 255),
        int(g * 255),
        int(b * 255),
    )


def get_client_color(client_name):
    client_name = str(client_name or "").strip()

    if not client_name:
        return "#64748b"

    digest = hashlib.sha256(client_name.lower().encode("utf-8")).hexdigest()

    hue = int(digest[:8], 16) % 360
    saturation = 68 + (int(digest[8:10], 16) % 12)
    lightness = 52 + (int(digest[10:12], 16) % 10)

    return hsl_to_hex(hue, saturation, lightness)


def build_events(df):
    events = []

    if df.empty or "Publishing Date" not in df.columns:
        return events

    today = pd.Timestamp.now().date()

    for _, row in df.iterrows():
        publish_date = row.get("Publishing Date")
        if pd.isna(publish_date):
            continue

        content_id = str(row.get("Content ID", "")).strip()
        sheet_row_id = str(row.get("Sheet Row ID", "")).strip()
        description = str(row.get("Post Content Description", "")).strip()
        client_name = str(row.get("Client", "")).strip()
        status = str(row.get("Publishing Status", "Pending")).strip().lower()

        internal_ok = is_approved(row.get("Internal Approval", ""))
        client_ok = is_approved(row.get("Approval", ""))

        client_color = get_client_color(client_name)

        if status == "published":
            background_color = PUBLISHED_FILL
            border_color = PUBLISHED_BORDER
            text_color = PUBLISHED_TEXT
            status_label = "Published"
        elif internal_ok and client_ok:
            background_color = APPROVED_FILL
            border_color = APPROVED_BORDER
            text_color = APPROVED_TEXT
            status_label = "Approved"
        elif pd.Timestamp(publish_date).date() < today:
            background_color = OVERDUE_FILL
            border_color = OVERDUE_BORDER
            text_color = OVERDUE_TEXT
            status_label = "Overdue"
        else:
            background_color = DEFAULT_FILL
            border_color = client_color
            text_color = DEFAULT_TEXT
            status_label = "Pending"

        if content_id and description:
            event_title = f"[{content_id}] {description}"
        elif description:
            event_title = description
        elif content_id:
            event_title = content_id
        elif sheet_row_id:
            event_title = f"Row {sheet_row_id}"
        else:
            event_title = "Untitled Content"

        events.append(
            {
                "title": event_title,
                "start": pd.Timestamp(publish_date).strftime("%Y-%m-%d"),
                "allDay": True,
                "backgroundColor": background_color,
                "borderColor": border_color,
                "textColor": text_color,
                "extendedProps": {
                    "content_id": content_id,
                    "sheet_row_id": sheet_row_id,
                    "client": client_name,
                    "client_color": client_color,
                    "client_approval": "Approved" if client_ok else "Pending",
                    "internal_approval": "Approved" if internal_ok else "Pending",
                    "publishing_status": row.get("Publishing Status", "Pending"),
                    "status_label": status_label,
                    "description": description,
                },
            }
        )

    return events


def render_calendar(events):
    calendar_options = {
        "editable": False,
        "selectable": False,
        "initialView": "dayGridMonth",
        "height": "auto",
        "fixedWeekCount": False,
        "displayEventTime": False,
        "eventDisplay": "block",
        "dayMaxEvents": False,
        "dayMaxEventRows": False,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek",
        },
    }

    custom_css = f"""
    html, body {{
        background: transparent !important;
    }}

    .fc {{
        color: {DEFAULT_TEXT} !important;
        background: transparent !important;
    }}

    .fc .fc-toolbar,
    .fc-header-toolbar {{
        background: #ffffff !important;
        border: 1px solid {DEFAULT_BORDER} !important;
        border-radius: 16px !important;
        padding: 12px 14px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06) !important;
    }}

    .fc .fc-toolbar-title {{
        color: {DEFAULT_TEXT} !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em !important;
    }}

    .fc .fc-col-header-cell-cushion,
    .fc .fc-daygrid-day-number,
    .fc .fc-list-day-text,
    .fc .fc-list-day-side-text {{
        color: {DEFAULT_TEXT} !important;
    }}

    .fc-theme-standard .fc-scrollgrid,
    .fc-theme-standard td,
    .fc-theme-standard th,
    .fc .fc-scrollgrid-section > * {{
        border-color: {DEFAULT_BORDER} !important;
        background: #ffffff !important;
    }}

    .fc .fc-button {{
        background: #ffffff !important;
        border: 1px solid {DEFAULT_BORDER} !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        color: {DEFAULT_TEXT} !important;
        font-weight: 600 !important;
    }}

    .fc .fc-button:hover {{
        background: #f8fbff !important;
        border-color: #c7d2e3 !important;
        color: {DEFAULT_TEXT} !important;
    }}

    .fc .fc-button-primary:not(:disabled).fc-button-active,
    .fc .fc-button-primary:not(:disabled):active {{
        background: #eef0ff !important;
        border-color: #cdd6ff !important;
        color: #4451d1 !important;
    }}

    .fc .fc-day-today {{
        background: {TODAY_BG} !important;
    }}

    .fc .fc-daygrid-day-frame {{
        min-height: 160px !important;
        padding: 6px 6px 10px 6px !important;
    }}

    .fc .fc-daygrid-day-top {{
        margin-bottom: 6px !important;
    }}

    .fc .fc-daygrid-day-number {{
        font-weight: 700 !important;
        color: {DEFAULT_MUTED} !important;
    }}

    .fc .fc-col-header-cell-cushion {{
        padding: 10px 0 !important;
        font-weight: 700 !important;
        color: {DEFAULT_MUTED} !important;
    }}

    .fc .fc-daygrid-body-natural .fc-daygrid-day-events {{
        margin-bottom: 4px !important;
    }}

    .fc .fc-daygrid-event-harness {{
        margin-bottom: 6px !important;
    }}

    .fc .fc-daygrid-event,
    .fc .fc-h-event {{
        border-radius: 12px !important;
        padding: 7px 9px !important;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06) !important;
        min-height: 36px !important;
        border-width: 1px !important;
        border-style: solid !important;
        cursor: pointer !important;
        overflow: hidden !important;
    }}

    .fc .fc-daygrid-event {{
        border-left-width: 4px !important;
    }}

    .fc .fc-daygrid-event:hover {{
        transform: translateY(-1px);
        transition: transform 140ms ease, box-shadow 140ms ease;
        box-shadow: 0 10px 18px rgba(15, 23, 42, 0.10) !important;
    }}

    .fc .fc-event-main {{
        display: block !important;
    }}

    .fc .fc-event-title {{
        font-weight: 700 !important;
        font-size: 0.79rem !important;
        line-height: 1.3 !important;
        white-space: normal !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}

    .fc .fc-event-time {{
        color: {DEFAULT_MUTED} !important;
        font-weight: 500 !important;
    }}

    .fc .fc-more-link {{
        display: none !important;
    }}

    .fc .fc-popover {{
        background: #ffffff !important;
        border: 1px solid {DEFAULT_BORDER} !important;
        color: {DEFAULT_TEXT} !important;
        border-radius: 14px !important;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12) !important;
    }}

    .fc .fc-popover-header {{
        background: #f8fbff !important;
        color: {DEFAULT_TEXT} !important;
        border-bottom: 1px solid {DEFAULT_BORDER} !important;
    }}

    .fc .fc-list,
    .fc .fc-list-table,
    .fc .fc-list-event td {{
        background: #ffffff !important;
        color: {DEFAULT_TEXT} !important;
        border-color: {DEFAULT_BORDER} !important;
    }}

    .fc .fc-list-day-cushion {{
        background: #f8fbff !important;
    }}

    .fc .fc-list-event:hover td {{
        background: #f8fbff !important;
    }}
    """

    return calendar(
        events=events,
        options=calendar_options,
        custom_css=custom_css,
        key="content_calendar",
    )