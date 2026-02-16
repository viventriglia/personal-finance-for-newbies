from datetime import datetime, timedelta

import streamlit as st
import yfinance as yf
import pandas as pd

from var import CACHE_EXPIRE_SECONDS
from user import login_user, register_user
from mongo import init_connection


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


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner="Fetching data from DB")
def load_data(
    username: str, is_mock: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    client = init_connection()
    db_name = "mock" if is_mock else "pfn"
    db = client[db_name]

    # --- TRANSACTIONS ---
    query_t = {} if is_mock else {"user_id": username}
    # Carichiamo anche il tipo transazione per decidere il segno
    cursor_t = db["transactions"].find(query_t, {"_id": 0})
    df_t = pd.DataFrame(list(cursor_t))

    if not df_t.empty:
        # 1. Rinominiamo per compatibilità con le vecchie analisi
        df_t = df_t.rename(
            columns={
                "transaction_date": "transaction_date",  # Già corretto nel nuovo schema
                "shares": "shares",  # Già corretto
            }
        )

        # 2. TRUCCO DEL SEGNO: Se è 'Sell', moltiplichiamo shares per -1
        # Questo "ripara" istantaneamente l'aggregazione in tutte le pagine
        if "transaction_type" in df_t.columns:
            df_t.loc[df_t["transaction_type"] == "Sell", "shares"] *= -1

        # 3. Calcoli e conversioni
        df_t["transaction_date"] = pd.to_datetime(df_t["transaction_date"])
        df_t["shares"] = df_t["shares"].astype(float)
        df_t["price"] = df_t["price"].astype(float)
        df_t["fees"] = df_t.get("fees", 0.0).astype(float)
        df_t["ap_amount"] = df_t["shares"] * df_t["price"]

    # --- ASSETS --- (Logica invariata)
    cursor_a = db["assets"].find({}, {"_id": 0})
    df_a = pd.DataFrame(list(cursor_a))
    if not df_a.empty:
        df_a = df_a.rename(
            columns={
                "security_full_name": "name",
                "security_name": "name",
                "ticker_yf": "ticker_yf",
            }
        )

    return df_t, df_a


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_last_closing_price(ticker_list: list[str]) -> pd.DataFrame:
    df_last_closing = pd.DataFrame(
        columns=["ticker_yf", "last_closing_date", "price"],
        index=range(len(ticker_list)),
    )
    for i, ticker_ in zip(range(len(ticker_list)), ticker_list):
        ticker_data = yf.Ticker(ticker_)
        try:
            closing_date_ = (
                ticker_data.history(
                    period="1d",
                    interval="1d",
                )["Close"]
                .reset_index()
                .values.tolist()
            )
            df_last_closing.iloc[i] = [ticker_] + closing_date_[0]
        except:
            try:
                closing_date_ = get_last_closing_price_from_api(ticker=ticker_)
                df_last_closing.iloc[i] = [ticker_] + closing_date_[0]
            except:
                st.error(
                    f"{ticker_}: latest data not available. Please check your internet connection or try again later",
                    icon="😔",
                )

    df_last_closing["last_closing_date"] = (
        df_last_closing["last_closing_date"].astype(str).str.slice(0, 10)
    )

    return df_last_closing


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_last_closing_price_from_api(ticker: str, days_of_delay: int = 5) -> list:
    today = datetime.utcnow()
    delayed = today - timedelta(days=days_of_delay)

    period1 = int(delayed.timestamp())
    period2 = int(datetime.utcnow().timestamp())

    link = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={period1}&period2={period2}&interval=1d&events=history&includeAdjustedClose=true"

    try:
        closing_date = pd.read_csv(link, usecols=["Date", "Adj Close"]).rename(
            {"Adj Close": "Close"}
        )
        closing_date["Date"] = pd.to_datetime(closing_date["Date"])
        closing_date = closing_date.head(1).values.tolist()
    except:
        closing_date = None

    return closing_date


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_full_price_history(ticker_list: list[str]) -> dict:
    df_history = dict()

    for ticker_ in ticker_list:
        ticker_data = yf.Ticker(ticker_)
        df_history[ticker_] = ticker_data.history(
            period="max",
            interval="1d",
        )[
            "Close"
        ].rename(ticker_)

        df_history[ticker_].index = pd.to_datetime(df_history[ticker_].index.date)

    return df_history


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_max_common_history(ticker_list: list[str]) -> pd.DataFrame:
    full_history = get_full_price_history(ticker_list)
    df_full_history = pd.concat(
        [full_history[t_] for t_ in ticker_list],
        axis=1,
    )
    first_idx = df_full_history.apply(pd.Series.first_valid_index).max()
    return df_full_history.loc[first_idx:]


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_risk_free_rate_last_value(decimal: bool = False) -> float:
    try:
        df_ecb = pd.read_html(
            io="http://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_short-term_rate/html/index.en.html"
        )[0]
        risk_free_rate = df_ecb.iloc[0, 1].astype(float)
    except:
        risk_free_rate = 3
    if decimal:
        risk_free_rate = risk_free_rate / 100
    return risk_free_rate


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_risk_free_rate_history(decimal: bool = False) -> pd.DataFrame:
    euro_str_link = "https://sdw.ecb.europa.eu/quickviewexport.do?SERIES_KEY=438.EST.B.EU000A2X2A25.WT&type=csv"
    try:
        df_ecb = (
            pd.read_csv(
                euro_str_link,
                sep=",",
                skiprows=5,
                index_col=0,
            )
            .drop(columns="obs. status")
            .rename(columns={"Unnamed: 1": "euro_str"})
        ).sort_index()
    except:
        df_ecb = pd.DataFrame()
    if decimal:
        df_ecb["euro_str"] = df_ecb["euro_str"].div(100)
    return df_ecb


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
