from datetime import datetime, timedelta, timezone

import streamlit as st
import yfinance as yf
import pandas as pd

from utils.var import CACHE_EXPIRE_SECONDS


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_last_closing_price(ticker_list: list[str]) -> pd.DataFrame:
    df_last_closing = pd.DataFrame(
        columns=["ticker_yf", "last_closing_date", "price"],
        index=range(len(ticker_list)),
    )
    for i, ticker_ in zip(range(len(ticker_list)), ticker_list):
        closing_date_ = None
        try:
            ticker_data = yf.Ticker(ticker_)
            closing_date_ = (
                ticker_data.history(
                    period="1d",
                    interval="1d",
                )["Close"]
                .reset_index()
                .values.tolist()
            )
            if not closing_date_:
                raise ValueError(f"Empty history for {ticker_}")
            df_last_closing.iloc[i] = [ticker_] + closing_date_[0]
        except Exception:
            try:
                closing_date_ = get_last_closing_price_from_api(ticker=ticker_)
                df_last_closing.iloc[i] = [ticker_] + closing_date_[0]
            except Exception:
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
    today = datetime.now(timezone.utc)
    delayed = today - timedelta(days=days_of_delay)

    period1 = int(delayed.timestamp())
    period2 = int(today.timestamp())

    link = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={period1}&period2={period2}&interval=1d&events=history&includeAdjustedClose=true"

    try:
        closing_date = pd.read_csv(link, usecols=["Date", "Adj Close"]).rename(
            {"Adj Close": "Close"}
        )
        closing_date["Date"] = pd.to_datetime(closing_date["Date"])
        closing_date = closing_date.head(1).values.tolist()
    except Exception:
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
    except Exception:
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
    except Exception:
        df_ecb = pd.DataFrame()
    if decimal:
        df_ecb["euro_str"] = df_ecb["euro_str"].div(100)
    return df_ecb
