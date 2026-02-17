from typing import Literal

import streamlit as st
import pandas as pd
import numpy as np

from utils.var import CACHE_EXPIRE_SECONDS


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner=False)
def get_period_returns(
    df: pd.DataFrame,
    df_registry: pd.DataFrame,
    tickers_to_evaluate: list[str],
    period: Literal["Y", "Q", "M", "W", None],
    level: Literal["ticker", "asset_class", "macro_asset_class"],
):
    # Filtra solo i ticker effettivamente in portafoglio
    df_registry = df_registry[df_registry["ticker_yf"].isin(tickers_to_evaluate)]
    # Calcolo il ritorno
    df_rets = df.ffill().pct_change()[1:]
    # Se il periodo è None, la frequenza è giornaliera
    if period is None:
        # Se il livello è quello del ticker, non devo fare altro
        if level == "ticker":
            return df_rets
        # Altrimenti sommo al livello delle asset class
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
