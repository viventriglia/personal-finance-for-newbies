import streamlit as st
import pandas as pd

from database.auth import login_user, register_user
from database.fetch import load_data


def write_disclaimer() -> None:
    st.markdown("***")
    st.markdown(
        '<center> <span style="font-size:0.7em; font-style:italic">\
        This content is for educational purposes only and is under no circumstances intended\
        to be used or considered as financial or investment advice\
        </span> </center>',
        unsafe_allow_html=True,
    )


def write_load_message(df_data: pd.DataFrame, df_dimensions: pd.DataFrame) -> None:
    n_transactions = df_data.shape[0]
    n_tickers = df_data["ticker"].nunique()
    min_date, max_date = (
        str(df_data["transaction_date"].min())[:10],
        str(df_data["transaction_date"].max())[:10],
    )
    set_data_tickers = sorted(df_data["ticker"].unique())
    set_dimensions_tickers = sorted(df_dimensions["ticker"].unique())
    n_data_na = df_data.isnull().sum().sum()
    n_dimensions_na = df_dimensions.isnull().sum().sum()

    if n_data_na > 0 or n_dimensions_na > 0:
        st.error(
            f"There are null values: {n_data_na} among transactions, {n_dimensions_na} among tickers' descriptions"
        )
        st.stop()

    if set_data_tickers != set_dimensions_tickers:
        st.warning(
            "There is some inconsistency between the tickers traded and the tickers' descriptions"
        )

    st.success(
        f"Successfully loaded **{n_transactions} transactions** relating to **{n_tickers} tickers** and spanning from {min_date} to {max_date}"
    )


def login_or_register() -> None:
    st.markdown("## Who wants to access PFN?")
    st.sidebar.write("Login or register:")
    login_sidebar = st.sidebar.selectbox(
        " ", ["Login", "Register"], label_visibility="collapsed"
    )

    if login_sidebar == "Register":
        with st.form("register_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Register")
        if submit:
            if register_user(username, password):
                st.success("Registration successful: you can now log in!", icon="✅")
            else:
                st.error("Sorry, username already taken")

    elif login_sidebar == "Login":
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
        if submit:
            if login_user(username, password):
                st.session_state["user"] = username
                st.rerun()
            else:
                st.error("Sorry, invalid credentials")
    st.stop()


def check_session_sidebar():
    if "user" in st.session_state:
        st.sidebar.write(
            f"Logged in as: **{st.session_state['user']}**", unsafe_allow_html=True
        )
        if st.sidebar.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        login_or_register()
        st.stop()


def ensure_data_is_loaded():
    if "data" not in st.session_state:
        user = st.session_state.get("user")
        if user:
            df_t, df_a = load_data(user, is_mock=False)
            st.session_state["data"] = df_t
            st.session_state["dimensions"] = df_a
            st.session_state["is_mock"] = False
