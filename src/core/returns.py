from datetime import datetime
from typing import Literal

import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import brentq

from utils.var import CACHE_EXPIRE_SECONDS


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def xirr(
    df_transactions: pd.DataFrame, pf_current_value: float, consider_fees: bool
) -> float | None:
    """Extended Internal Rate of Return (XIRR).

    Solves for the annualised rate `r` such that:
        Σ [ CF_i / (1 + r)^(t_i / 365) ] = 0

    Parameters
    ----------
    cashflows : pd.Series
        Series indexed by datetime with cash-flow values.
        Negative values = investments (money out).
        The *last* entry should be the current portfolio value (money in).

    Returns
    -------
    float | None
        Annualised XIRR as a decimal (e.g. 0.12 = 12%), or None if
        the solver fails to converge.
    """
    # Build cashflows for XIRR
    cf_groupby = df_transactions.groupby("transaction_date")
    cf_amounts = cf_groupby["ap_amount"].sum().apply(lambda x: -abs(x))
    if consider_fees:
        cf_fees = cf_groupby["fees"].sum()
        cf_amounts = cf_amounts.sub(cf_fees, fill_value=0)
    cf_amounts.index = pd.to_datetime(cf_amounts.index)
    final_cf = pd.Series(
        [pf_current_value], index=[pd.Timestamp(datetime.now().date())]
    )
    cashflows = pd.concat([cf_amounts, final_cf]).sort_index()

    if cashflows.empty or cashflows.shape[0] < 2:
        return None

    # Normalise dates to days from the first cash flow
    dates = cashflows.index
    t0 = dates[0]
    days = pd.Series([(d - t0).days for d in dates], index=dates, dtype=float)

    def npv(r: float) -> float:
        return (cashflows / (1 + r) ** (days / 365)).sum()

    try:
        return brentq(npv, a=-0.999, b=100.0, xtol=1e-8, maxiter=1000)
    except Exception:
        return None


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def twr(df_wealth: pd.DataFrame) -> float | None:
    """Annualised Time-Weighted Return (TWR).

    Links holding-period returns (HPR) between each cash-flow event so
    that the result is insensitive to the timing or size of deposits.
    This makes it directly comparable to benchmark indices.

    Parameters
    ----------
    df_wealth : pd.DataFrame
        Output of `get_wealth_history()` — must contain columns
        ``ap_daily_value`` and ``ap_cum_spent``.

    Returns
    -------
    float | None
        Annualised TWR as a decimal, or None if not enough data.
    """
    if df_wealth.empty or df_wealth.shape[0] < 2:
        return None

    # Cash flows: daily change in cumulative invested capital
    df = df_wealth[["ap_daily_value", "ap_cum_spent"]].copy().dropna()
    df["cf"] = df["ap_cum_spent"].diff().fillna(0.0)

    # Sub-period boundaries: days on which new money was added
    cf_days = df.index[df["cf"] > 0].tolist()

    if not cf_days:
        # No contributions detected — plain cumulative return
        v_start = df["ap_daily_value"].iloc[0]
        v_end = df["ap_daily_value"].iloc[-1]
        if v_start == 0:
            return None
        return (v_end / v_start) - 1

    # Build sub-period boundaries: [start, cf1, cf2, ..., today]
    boundaries = [df.index[0]] + cf_days + [df.index[-1]]
    boundaries = sorted(set(boundaries))

    product = 1.0
    for i in range(len(boundaries) - 1):
        start, end = boundaries[i], boundaries[i + 1]
        sub = df.loc[start:end]
        if sub.shape[0] < 2:
            continue
        v_start = sub["ap_daily_value"].iloc[0]
        v_end = sub["ap_daily_value"].iloc[-1]
        cf = sub["cf"].iloc[1:].sum()
        denominator = v_start + cf
        if denominator == 0:
            continue
        hpr = (v_end - v_start - cf) / denominator
        product *= 1 + hpr

    twr_cum = product - 1
    total_days = (df.index[-1] - df.index[0]).days

    if total_days > 0:
        return (1 + twr_cum) ** (365 / total_days) - 1
    else:
        return None


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_period_returns(
    df: pd.DataFrame,
    df_registry: pd.DataFrame,
    tickers_to_evaluate: list[str],
    period: Literal["YE", "QE", "ME", "W", None],
    level: Literal["ticker", "asset_class", "macro_asset_class"],
):
    # Filtra solo i ticker effettivamente in portafoglio
    df_registry = df_registry[df_registry["ticker_yf"].isin(tickers_to_evaluate)]
    df_rets = df.ffill().pct_change()[1:]
    # Se il periodo è None, la frequenza è giornaliera
    if period is None:
        if level == "ticker":
            return df_rets
        else:
            classes = df_registry[level].unique()
            df_rets_classes = pd.DataFrame(columns=classes)
            for class_ in classes:
                cols_to_sum = df_registry[df_registry[level].eq(class_)][
                    "ticker_yf"
                ].to_list()
                df_rets_classes[class_] = df_rets[cols_to_sum].sum(axis=1)
            return df_rets_classes
    # Se il periodo non è None, faccio resampling al periodo desiderato
    else:
        df_rets_resampled = df_rets.resample(period).agg(lambda x: (x + 1).prod() - 1)
        if level == "ticker":
            return df_rets_resampled
        else:
            classes = df_registry[level].unique()
            df_rets_classes = pd.DataFrame(columns=classes)
            for class_ in classes:
                cols_to_sum = df_registry[df_registry[level].eq(class_)][
                    "ticker_yf"
                ].to_list()

                df_rets_classes[class_] = df_rets_resampled[cols_to_sum].sum(axis=1)
            return df_rets_classes


def get_rolling_returns(
    df_prices: pd.DataFrame,
    df_registry: pd.DataFrame,
    tickers_to_evaluate: list[str],
    window: int,
    level: Literal["ticker", "asset_class", "macro_asset_class"],
) -> pd.DataFrame:
    # Filtra solo i ticker effettivamente in portafoglio
    df_registry = df_registry[df_registry["ticker_yf"].isin(tickers_to_evaluate)]

    df_log_ret = np.log(df_prices.div(df_prices.shift(1)))
    df_roll_log_ret = df_log_ret.rolling(window=window).sum()
    df_roll_ret = np.exp(df_roll_log_ret) - 1

    # Se il livello è quello del ticker, non devo fare altro
    if level == "ticker":
        return df_roll_ret
    # Altrimenti aggrego al livello richiesto
    else:
        classes = df_registry[level].unique()
        df_roll_ret_classes = pd.DataFrame(columns=classes)
        for class_ in classes:
            cols_to_sum = df_registry[df_registry[level].eq(class_)][
                "ticker_yf"
            ].to_list()

            df_roll_ret_classes[class_] = df_roll_ret[cols_to_sum].sum(axis=1)
        return df_roll_ret_classes


@st.cache_data(ttl=10 * CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_portfolio_return_series(
    df_wealth: pd.DataFrame, period: Literal["YE", "QE", "ME", "W", None] = None
) -> pd.Series:
    """Restituisce la serie storica dei rendimenti del portafoglio aggregato."""
    df = df_wealth[["ap_daily_value", "ap_cum_spent"]].copy().dropna()
    df["cf"] = df["ap_cum_spent"].diff().fillna(0.0)

    if "is_pricing_day" in df_wealth.columns:
        pricing_days = df_wealth["is_pricing_day"].reindex(df.index).fillna(False)
        df = df[pricing_days | df["cf"].ne(0)]

    v_start = df["ap_daily_value"].shift(1)
    denominator = v_start + df["cf"]

    # Holding Period Return between observed pricing dates and cash flows.
    hpr = (df["ap_daily_value"] - v_start - df["cf"]) / denominator.replace(0, np.nan)
    hpr = hpr.fillna(0.0)

    if period is None:
        return hpr
    else:
        return hpr.resample(period).agg(lambda x: (x + 1).prod() - 1)
