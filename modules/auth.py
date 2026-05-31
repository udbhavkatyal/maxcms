import streamlit as st


def login():
    if st.session_state.get("authenticated", False):
        return True

    st.markdown(
        """
        <style>
        .login-minimal-wrap {
            margin-top: 22vh;
        }

        .login-minimal-wrap .stForm {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        .login-minimal-wrap div[data-testid="stTextInput"] {
            margin-top: 0 !important;
            margin-bottom: 0.75rem !important;
        }

        .login-minimal-wrap div[data-testid="stTextInput"] label {
            display: none !important;
        }

        .login-minimal-wrap [data-testid="stForm"] {
            border: none !important;
            background: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1.2, 1, 1.2])

    with center:
        st.markdown('<div class="login-minimal-wrap">', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Password",
                label_visibility="collapsed",
            )

            submitted = st.form_submit_button(
                "Submit",
                use_container_width=True,
            )

            if submitted:
                if password == st.secrets["APP_PASSWORD"]:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")

        st.markdown("</div>", unsafe_allow_html=True)

    return False