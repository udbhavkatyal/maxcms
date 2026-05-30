# modules/auth.py

import streamlit as st


def login():

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title(
        "Max Level Content Dashboard"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        if password == st.secrets["APP_PASSWORD"]:

            st.session_state.authenticated = True

            st.rerun()

        else:

            st.error(
                "Invalid password"
            )

    return False