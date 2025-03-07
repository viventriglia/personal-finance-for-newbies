from typing import Literal

import streamlit as st
import pandas as pd
import numpy as np

from var import CACHE_EXPIRE_SECONDS, TRADING_DAYS_YEAR


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def sharpe_ratio(
    returns: pd.Series, trading_days: int, risk_free_rate: float = 3
) -> float:
    mean = returns.mean() * trading_days - risk_free_rate
    std = returns.std() * np.sqrt(trading_days)
    return mean / std


# def sortino_ratio(series, N, rf):
#     mean = series.mean() * N -rf
#     std_neg = series[series<0].std()*np.sqrt(N)
#     return mean/std_neg

# def max_drawdown(return_series):
#     comp_ret = (return_series+1).cumprod()
#     peak = comp_ret.expanding(min_periods=1).max()
#     dd = (comp_ret/peak)-1
#     return dd.min()


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_drawdown(df: pd.DataFrame) -> pd.DataFrame:
    df = df.fillna(0.0)
    cumulative_rets = (df + 1).cumprod()
    running_max = cumulative_rets.cummax()
    return (cumulative_rets - running_max).div(running_max)


def get_max_dd(df: pd.DataFrame) -> float:
    return get_drawdown(df).min()


def get_portfolio_variance(
    weights: pd.Series, returns: pd.DataFrame, trading_days=TRADING_DAYS_YEAR
) -> float:
    return trading_days * np.dot(weights.T, np.dot(returns.cov(), weights))


def get_relative_risk_contributions(
    weights: pd.Series, returns: pd.DataFrame
) -> pd.Series:
    volatility = np.sqrt(get_portfolio_variance(weights, returns))
    covariance = returns.cov()
    marginal_vols = np.dot(covariance, weights) / volatility
    risk_contrib = marginal_vols * weights
    relative_risk_contrib = risk_contrib / risk_contrib.sum()
    return relative_risk_contrib


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_portfolio_relative_risk_contribution(
    df_prices: pd.DataFrame,
    df_shares: pd.DataFrame,
    df_registry: pd.DataFrame,
    level: Literal["ticker", "asset_class", "macro_asset_class"],
) -> pd.DataFrame:
    df_log_rets = np.log(df_prices.div(df_prices.shift()))
    if level == "ticker":
        # Log-returns
        df_rets = df_log_rets
        # Weights
        df_weights = df_prices.tail(1).T.merge(
            df_shares, left_index=True, right_index=True
        )
        df_weights.columns = ["last_price", "shares"]
        df_weights["total_invested"] = df_weights["last_price"] * df_weights["shares"]
        df_weights["pf_weight"] = df_weights["total_invested"].div(
            df_weights["total_invested"].sum()
        )
    else:
        classes = df_registry[level].unique()
        df_rets = pd.DataFrame(columns=classes)
        df_weights = pd.DataFrame(columns=["total_invested"])
        # Log-returns & weights per class
        for class_ in classes:
            # Tickers belonging to class_
            cols_to_sum = df_registry[df_registry[level].eq(class_)][
                "ticker_yf"
            ].to_list()
            # Log-return of class_
            df_rets[class_] = df_log_rets[cols_to_sum].sum(axis=1)
            # Weight of class_
            df_ = (
                df_prices[cols_to_sum]
                .tail(1)
                .T.merge(df_shares.loc[cols_to_sum], left_index=True, right_index=True)
            )
            df_.columns = ["last_price", "shares"]
            df_["total_invested"] = df_["last_price"] * df_["shares"]
            df_weights.loc[class_] = df_["total_invested"].sum()
        df_weights["pf_weight"] = df_weights["total_invested"].div(
            df_weights["total_invested"].sum()
        )

    df = pd.DataFrame(
        get_relative_risk_contributions(df_weights["pf_weight"], df_rets).rename(
            "relative_risk_contribution"
        )
    ).merge(df_weights["pf_weight"], right_index=True, left_index=True)

    return df
