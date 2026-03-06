import streamlit as st
import pandas as pd
import numpy as np

from utils.var import (
    GLOBAL_STREAMLIT_STYLE,
    FAVICON,
    DICT_GROUPBY_LEVELS,
)
from utils.ui import (
    write_disclaimer,
    check_session_sidebar,
    ensure_data_is_loaded,
    display_rebalance_simulation,
)
from core.aggregation import aggregate_by_ticker, format_actions
from utils.market import get_last_closing_price
from database.fetch import get_user_target_weights, save_user_target_weights

st.set_page_config(
    page_title="PFN | Rebalancing",
    page_icon=str(FAVICON),
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

check_session_sidebar()
ensure_data_is_loaded()

df_transactions = st.session_state.get("data", pd.DataFrame())
df_registry = st.session_state.get("dimensions", pd.DataFrame())

if df_transactions.empty:
    st.warning(
        "⚠️ Your portfolio is empty! To use the rebalancing tool, you first need to add some investments."
    )
    st.page_link(
        "pages/4_📝_Transactions_&_Assets.py",
        label="Add your first transaction",
        icon="✍🏻",
    )
    st.stop()

df_pf = aggregate_by_ticker(df_transactions, in_pf_only=True)
ticker_list = df_pf["ticker_yf"].to_list()
df_last_closing = get_last_closing_price(ticker_list=ticker_list)

df_j = df_pf.merge(df_last_closing[["ticker_yf", "price"]], on="ticker_yf", how="left")
df_j["current_value"] = df_j["shares"] * df_j["price"]
total_pf_value = df_j["current_value"].sum()

df_merged = df_j.merge(df_registry, on="ticker_yf", how="left").rename(
    columns={"ticker_yf": "ticker"}
)

st.markdown("## Portfolio Rebalancing")
st.markdown(
    "Set your target weights to calculate the exact amounts needed to rebalance your portfolio."
)

level_ui = st.radio(
    label="Rebalance at which level?",
    options=["Macro Asset Classes", "Asset Classes", "Tickers"],
    horizontal=True,
    index=2,
)

level_col = DICT_GROUPBY_LEVELS[level_ui]

if level_ui == "Tickers":
    df_grouped = (
        df_merged.groupby([level_col, "asset_class", "price"])
        .agg(current_value=("current_value", "sum"), current_shares=("shares", "sum"))
        .reset_index()
    )
else:
    df_grouped = (
        df_merged.groupby(level_col)
        .agg(current_value=("current_value", "sum"))
        .reset_index()
    )

df_grouped["current_weight"] = (df_grouped["current_value"] / total_pf_value) * 100

st.markdown("## Target Weights")
st.markdown(
    "Check and adjust the `Target Weight (%)` column. When you're done, you can save your target portfolio weights below."
)

user_id = st.session_state["user"]
saved_targets = get_user_target_weights(user_id, level_ui)

df_editor = df_grouped[[level_col, "current_weight"]].copy()

if level_ui == "Tickers":
    df_editor = df_grouped[[level_col, "asset_class", "current_weight"]].copy()
else:
    df_editor = df_grouped[[level_col, "current_weight"]].copy()

if saved_targets:
    df_editor["target_weight"] = df_editor[level_col].map(saved_targets).fillna(0.0)
else:
    df_editor["target_weight"] = df_editor["current_weight"].round(1)

edited_df = st.data_editor(
    df_editor,
    column_config={
        level_col: st.column_config.TextColumn(level_ui, disabled=True),
        "asset_class": st.column_config.TextColumn("Asset Class", disabled=True),
        "current_weight": st.column_config.NumberColumn(
            "Current Weight (%)", format="%.1f %%", disabled=True
        ),
        "target_weight": st.column_config.NumberColumn(
            "Target Weight (%)", format="%.1f %%", min_value=0.0, max_value=100.0
        ),
    },
    hide_index=True,
    use_container_width=True,
)

if st.button("💾 Save these targets as default for " + level_ui):
    targets_dict = dict(zip(edited_df[level_col], edited_df["target_weight"]))
    save_user_target_weights(user_id, level_ui, targets_dict)
    st.toast("Target weights saved to database!", icon="✅")

total_target = edited_df["target_weight"].sum()

if not np.isclose(total_target, 100.0, atol=0.1):
    st.error(f"Target weights must sum to 100%. Current sum: **{total_target:.1f}%**")
    st.stop()
else:
    st.success(f"Weights are perfectly balanced (Sum: {total_target:.1f}%)")


st.markdown("---")
st.markdown("## Rebalancing")

df_res = df_grouped.copy()
df_res["target_weight"] = edited_df["target_weight"] / 100.0

broker_fee = st.sidebar.number_input(
    "Broker fee per trade (€)",
    min_value=0.0,
    value=0.0,
    step=0.5,
    help="Used to estimate total transaction costs",
)

tab1, tab2 = st.tabs(["🔄 Standard Rebalance", "💰 Inject New Cash"])

with tab1:
    st.info(
        "Realign your existing portfolio to the target weights without adding new capital."
    )

    df_standard = df_res.copy()
    df_standard["target_value"] = total_pf_value * df_standard["target_weight"]
    df_standard["delta_value"] = (
        df_standard["target_value"] - df_standard["current_value"]
    )
    df_standard["delta_value"] = np.where(
        df_standard["delta_value"].abs() < 1, 0, df_standard["delta_value"]
    )

    out_standard = format_actions(
        df_standard,
        is_ticker=(level_ui == "Tickers"),
        level_col=level_col,
        level_ui=level_ui,
    )

    display_rebalance_simulation(
        df_res=df_res,
        out_df=out_standard,
        level_col=level_col,
        level_ui=level_ui,
        broker_fee=broker_fee,
        key="standard_editor",
    )


with tab2:
    st.info(
        "Allocate new liquidity. The targets are calculated on the new total value. Use checkboxes to ignore some of the suggestions."
    )

    cash_to_invest = st.number_input(
        "New Cash to Invest (€)", min_value=1.0, value=1000.0, step=100.0
    )

    new_total_value = total_pf_value + cash_to_invest

    df_cash = df_res.copy()
    df_cash["target_value"] = new_total_value * df_cash["target_weight"]
    df_cash["delta_value"] = df_cash["target_value"] - df_cash["current_value"]
    df_cash["delta_value"] = np.where(
        df_cash["delta_value"].abs() < 1, 0, df_cash["delta_value"]
    )

    out_cash = format_actions(
        df_cash,
        is_ticker=(level_ui == "Tickers"),
        level_col=level_col,
        level_ui=level_ui,
    )

    display_rebalance_simulation(
        df_res=df_res,
        out_df=out_cash,
        level_col=level_col,
        level_ui=level_ui,
        broker_fee=broker_fee,
        max_cash=cash_to_invest,
        key="cash_editor",
    )

write_disclaimer()
