import streamlit as st

from modules.sheets import (
    update_publish_status
)


def render_publish_form(
    content_row
):

    content_id = str(
        content_row.get(
            "Content ID",
            ""
        )
    )

    st.subheader(
        "Publish Content"
    )

    st.caption(
        f"Content ID: {content_id}"
    )

    post_links = st.text_area(

        "Post Link(s)",

        value=str(
            content_row.get(
                "Post Link(s)",
                ""
            )
        ),

        height=120,

        help=(
            "Paste one or more published post URLs.\n\n"
            "Example:\n"
            "https://instagram.com/...\n"
            "https://facebook.com/...\n"
            "https://linkedin.com/..."
        ),

        key=f"links_{content_id}"
    )

    if st.button(

        "Mark Published",

        type="primary",

        key=f"publish_{content_id}"
    ):

        try:

            update_publish_status(

                spreadsheet_url=
                    content_row[
                        "Spreadsheet URL"
                    ],

                worksheet_name=
                    content_row[
                        "Worksheet Name"
                    ],

                row_number=int(
                    content_row[
                        "Sheet Row ID"
                    ]
                ),

                urls_dict={

                    "Post Link(s)":
                        post_links
                }
            )

            st.success(
                f"{content_id} marked as published."
            )

            st.cache_data.clear()

            st.rerun()

        except Exception as e:

            st.error(
                f"Failed: {e}"
            )