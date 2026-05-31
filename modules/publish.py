# modules/publish.py

import streamlit as st

from modules.sheets import (
    update_publish_status,
    update_approval_status,
)


def is_approved(value):
    return str(value or "").strip().lower() in ["approved", "yes", "true", "done", "1"]


def render_publish_form(content_row):
    content_id = str(content_row.get("Content ID", "")).strip()
    row_number = int(content_row["Sheet Row ID"])

    current_internal = is_approved(content_row.get("Internal Approval", ""))
    current_client = is_approved(content_row.get("Approval", ""))

    display_id = content_id if content_id else f"Row {row_number}"

    st.markdown(
        """
        <div class="glass-card">
            <div class="hero-kicker">PUBLISH</div>
            <div class="hero-title" style="font-size:1.15rem; margin-bottom:0.35rem;">Final publishing actions</div>
            <div class="hero-sub">Update approvals, add live URLs, and mark this content as published.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="section-head" style="margin-top:0.85rem;">
            <h3>Approval Controls</h3>
            <div class="section-note">{display_id}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        internal_approval = st.checkbox(
            "Internal Approval",
            value=current_internal,
            key=f"internal_approval_{content_id}_{row_number}",
        )

    with c2:
        client_approval = st.checkbox(
            "Client Approval",
            value=current_client,
            key=f"client_approval_{content_id}_{row_number}",
        )

    if st.button(
        "Save Approval Status",
        key=f"save_approvals_{content_id}_{row_number}",
        use_container_width=True,
    ):
        try:
            update_approval_status(
                spreadsheet_url=content_row["Spreadsheet URL"],
                worksheet_name=content_row["Worksheet Name"],
                row_number=row_number,
                internal_approval=internal_approval,
                client_approval=client_approval,
            )
            st.success("Approval status updated.")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {e}")

    st.markdown(
        """
        <div class="section-head" style="margin-top:1rem;">
            <h3>Post Link(s)</h3>
            <div class="section-note">One or more live URLs</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    post_links = st.text_area(
        "Post Link(s)",
        label_visibility="collapsed",
        value=str(content_row.get("Post Link(s)", "")).strip(),
        height=120,
        key=f"links_{content_id}_{row_number}",
        placeholder="Paste one or more published URLs, one per line.",
    )

    cleaned_links = "\n".join(
        [line.strip() for line in str(post_links).splitlines() if line.strip()]
    )

    st.caption("Tip: add each published link on a separate line for easier tracking.")

    if st.button(
        "Mark Published",
        type="primary",
        key=f"publish_{content_id}_{row_number}",
        use_container_width=True,
    ):
        if not cleaned_links:
            st.error("Please add at least one published URL before marking this content as published.")
            return

        try:
            update_publish_status(
                spreadsheet_url=content_row["Spreadsheet URL"],
                worksheet_name=content_row["Worksheet Name"],
                row_number=row_number,
                urls_dict={"Post Link(s)": cleaned_links},
            )
            st.success(f"{display_id} marked as published.")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {e}")