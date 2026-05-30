import pandas as pd

from streamlit_calendar import calendar

from modules.helpers import (
    normalize_status
)


def build_events(df):

    events = []

    for _, row in df.iterrows():

        publish_date = row.get(
            "Publishing Date"
        )

        if pd.isna(
            publish_date
        ):
            continue

        try:

            publish_date = pd.to_datetime(
                publish_date
            )

        except:
            continue

        status = normalize_status(
            row.get(
                "Publishing Status"
            )
        )

        today = pd.Timestamp.now().date()

        if status == "Published":

            color = "#22c55e"

        elif publish_date.date() < today:

            color = "#ef4444"

        else:

            color = "#3b82f6"

        content_id = str(
            row.get(
                "Content ID",
                ""
            )
        )

        title = (
            f"[{content_id}] "
            f"{row.get('Post Content Description', '')}"
        )

        events.append(
            {
                "title": title,

                "start":
                    publish_date.strftime(
                        "%Y-%m-%d"
                    ),

                "backgroundColor":
                    color,

                "borderColor":
                    color,

                "extendedProps": {

                    "content_id":
                        content_id,

                    "sheet_row":
                        row.get(
                            "Sheet Row ID"
                        ),

                    "client":
                        row.get(
                            "Client"
                        ),

                    "spreadsheet_url":
                        row.get(
                            "Spreadsheet URL"
                        ),

                    "worksheet_name":
                        row.get(
                            "Worksheet Name"
                        ),

                    "worksheet_gid":
                        row.get(
                            "Worksheet GID"
                        ),

                    "status":
                        status
                }
            }
        )

    return events


def render_calendar(
    events
):

    options = {

        "initialView":
            "dayGridMonth",

        "height":
            850,

        "editable":
            False,

        "selectable":
            True,

        "dayMaxEvents":
            True,

        "headerToolbar": {

            "left":
                "prev,next today",

            "center":
                "title",

            "right":
                "dayGridMonth"
        }
    }

    return calendar(

        events=events,

        options=options,

        key="content_calendar"
    )