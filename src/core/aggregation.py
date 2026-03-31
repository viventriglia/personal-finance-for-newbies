from datetime import datetime
from typing import Literal

import streamlit as st
import pandas as pd
import numpy as np

from utils.var import CACHE_EXPIRE_SECONDS
from utils.market import get_full_price_history


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def aggregate_by_ticker(df: pd.DataFrame, in_pf_only: bool = False) -> pd.DataFrame:
    df_portfolio = (
        df.groupby("ticker_yf")
        .agg(
            shares=("shares", "sum"),
            ap_amount=("ap_amount", "sum"),
            fees=("fees", "sum"),
        )
        .reset_index()
        .sort_values(
            "shares",
            ascending=False,
        )
    )

    df_portfolio["is_in_pf"] = df_portfolio["shares"].ne(0)

    df_portfolio["dca"] = np.where(
        df_portfolio["is_in_pf"].eq(True),
        df_portfolio["ap_amount"].div(df_portfolio["shares"]),
        0,
    )

    if in_pf_only:
        df_portfolio = df_portfolio[df_portfolio["is_in_pf"].eq(True)]

    return df_portfolio.drop(columns="is_in_pf").reset_index(drop=True)


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_wealth_history(
    df_transactions: pd.DataFrame, ticker_list: list[str]
) -> pd.DataFrame:
    begin_date = df_transactions["transaction_date"].min()
    today = datetime.now().date()
    date_range = pd.date_range(start=begin_date, end=today, freq="D")

    # There may be missing data, for instance due to an ETF changing its name after
    # one or more purchases (as happened to MWRD on 17/01/2024); since in these cases
    # the history of the ‘old’ ETF is not retrieved, we assume that the first non-null
    # price found can be propagated (as a constant) backwards
    df_prices = (
        pd.concat(
            [get_full_price_history(ticker_list)[t_] for t_ in ticker_list],
            axis=1,
        )
        .loc[begin_date:]
    )
    df_prices = df_prices.reindex(date_range)
    has_price_observation = df_prices.notna().any(axis=1)
    df_prices = df_prices.bfill()

    df_transactions = df_transactions[df_transactions["ticker_yf"].isin(ticker_list)]

    df_asset_allocation = pd.DataFrame(index=date_range, columns=ticker_list, data=0.0)
    df_cumulative_spent = pd.Series(index=date_range, data=0.0)

    for (data, ticker), group in df_transactions.groupby(
        ["transaction_date", "ticker_yf"]
    ):
        total_shares = group["shares"].sum()
        total_spent = group["ap_amount"].sum()
        df_asset_allocation.loc[data, ticker] += total_shares
        df_cumulative_spent.loc[data] += total_spent

    df_asset_allocation = df_asset_allocation.cumsum()
    df_cumulative_spent = df_cumulative_spent.cumsum()

    df_wealth = pd.DataFrame(
        df_asset_allocation.multiply(df_prices.loc[begin_date:])
        .ffill()
        .sum(axis=1)
        .rename("ap_daily_value")
    )
    df_wealth["diff_previous_day"] = df_wealth["ap_daily_value"].diff()
    df_wealth["ap_cum_spent"] = df_cumulative_spent
    df_wealth["ap_cum_pnl"] = df_wealth["ap_daily_value"] - df_wealth["ap_cum_spent"]
    df_wealth["is_pricing_day"] = has_price_observation

    return df_wealth


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_portfolio_pivot(
    df: pd.DataFrame,
    df_dimensions: pd.DataFrame,
    pf_actual_value: float,
    aggregation_level: Literal["ticker", "asset_class", "macro_asset_class"],
) -> pd.DataFrame:
    if aggregation_level == "ticker":
        groupby_keys = [
            "macro_asset_class",
            "asset_class",
            "ticker_yf",
            "name",
        ]
    elif aggregation_level == "asset_class":
        groupby_keys = [
            "macro_asset_class",
            "asset_class",
        ]
    elif aggregation_level == "macro_asset_class":
        groupby_keys = "macro_asset_class"
    df_pivot = (
        df.copy()
        .merge(df_dimensions, how="left", on="ticker_yf")
        .groupby(groupby_keys)["position_value"]
        .sum()
        .reset_index()
    )
    df_pivot["weight_pf"] = 100 * df_pivot["position_value"].div(pf_actual_value)
    df_pivot["position_value"] = df_pivot["position_value"]
    return df_pivot


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_pnl_by_asset_class(
    df: pd.DataFrame,
    df_dimensions: pd.DataFrame,
    group_by: Literal["asset_class", "macro_asset_class"],
) -> pd.DataFrame:
    df_pnl = df.merge(df_dimensions, how="left", on="ticker_yf")
    df_pnl["pnl"] = ((df_pnl["price"] - df_pnl["dca"]) * df_pnl["shares"]).astype(float)
    df_pnl = df_pnl.groupby(group_by)["pnl"].sum().reset_index().sort_values([group_by])
    return df_pnl


def format_actions(
    df: pd.DataFrame, is_ticker: bool, level_col: str, level_ui: str
) -> pd.DataFrame:
    df["Action"] = np.where(
        df["delta_value"] > 0,
        "BUY 🟢",
        np.where(df["delta_value"] < 0, "SELL 🔴", "HOLD ⚪"),
    )

    df["weight_diff"] = (df["target_weight"] * 100) - df["current_weight"]

    cols_to_show = [
        level_col,
        "Action",
        "delta_value",
        "weight_diff",
    ]

    if is_ticker:
        cols_to_show.insert(1, "asset_class")
        df["delta_shares"] = df["delta_value"] / df["price"]
        cols_to_show.append("delta_shares")

    res_df = df[cols_to_show].copy()
    res_df.insert(0, "Execute", True)

    rename_dict = {
        level_col: level_ui,
        "delta_value": "Amount to Trade (€)",
        "weight_diff": "Difference in Weight (%)",
        "delta_shares": "Shares to Trade (Approx.)",
    }
    if is_ticker:
        rename_dict["asset_class"] = "Asset Class"
    return res_df.rename(columns=rename_dict).sort_values(
        "Amount to Trade (€)", ascending=False
    )
