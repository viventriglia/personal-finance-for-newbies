from datetime import datetime

import streamlit as st

from utils.var import (
    GLOBAL_STREAMLIT_STYLE,
    PLT_CONFIG,
    PLT_CONFIG_NO_LOGO,
    FAVICON,
    DICT_GROUPBY_LEVELS,
)
from utils.ui import write_disclaimer, check_session_sidebar
from core.aggregation import (
    aggregate_by_ticker,
    get_pnl_by_asset_class,
    get_portfolio_pivot,
    get_wealth_history,
)
from core.returns import xirr, twr
from utils.plot import plot_sunburst, plot_wealth, plot_pnl_by_asset_class
from utils.ui import ensure_data_is_loaded
from utils.market import get_last_closing_price


st.set_page_config(
    page_title="PFN | Asset Allocation & PnL",
    page_icon=str(FAVICON),
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

check_session_sidebar()
ensure_data_is_loaded()

df_transactions = st.session_state["data"]
df_registry = st.session_state["dimensions"]

if df_transactions.empty:
    st.warning(
        "⚠️ Your portfolio is empty! To see these analytics, you first need to add some investments."
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

df_j = df_pf[["ticker_yf", "dca", "shares"]].merge(
    df_last_closing[["ticker_yf", "price"]], how="left", on="ticker_yf"
)

expense = (df_j["shares"] * df_j["dca"]).sum()
fees = df_transactions["fees"].sum().round(2)

st.markdown("## Profit & Loss")

col_1, col_2, col_3, col_4, col_5 = st.columns([1.2, 1, 1, 1, 1], gap="small")

consider_fees = st.checkbox("Take fees into account")

df_j["position_value"] = df_j["shares"] * df_j["price"]
pf_actual_value = df_j["position_value"].sum()
total_expense = expense + fees if consider_fees else expense
pnl = pf_actual_value - total_expense
pnl_perc = pnl / total_expense
sign = "+" if pnl >= 0 else ""

col_1.metric(
    label="Portfolio Value",
    value=f"{pf_actual_value: ,.1f} €",
    delta=f"{sign}{pnl: ,.1f} €",
)

col_2.metric(
    label="ROI",
    value=f"{sign}{pnl_perc: .1%}",
    help="""
    **Return on Investment**: total gain or loss as a percentage of the
    invested capital, regardless of the time elapsed.
    Suitable for both lump-sum and regular-contribution investors,
    but gives no information about *when* returns were generated.
    """,
)

first_transaction = df_transactions["transaction_date"].sort_values()[0]
n_years = (datetime.now() - first_transaction).days / 365.25
annualised_ret = ((pf_actual_value / total_expense) ** (1 / n_years)) - 1

col_3.metric(
    label="CAGR",
    value=f"{sign}{annualised_ret: .1%}",
    help="""
    **Compound Annual Growth Rate**: the rate at which the portfolio would
    have grown each year if it had grown at a steady pace.
    Best suited for lump-sum investments, where a single initial
    amount is invested. For regular contributions, CAGR can be
    misleading because it assumes all capital was deployed on day one —
    prefer XIRR in that case.
    """,
)

df_wealth_early = get_wealth_history(
    df_transactions=df_transactions, ticker_list=ticker_list
)

xirr_value = xirr(
    df_transactions=df_transactions,
    pf_current_value=pf_actual_value,
    consider_fees=consider_fees,
)
twr_value = twr(df_wealth_early)


sign_x = "+" if xirr_value >= 0 else ""
col_4.metric(
    label="XIRR",
    value=f"{sign_x}{xirr_value:.1%}",
    help="""
    **Extended Internal Rate of Return**: the annualised rate that makes the
    net present value of all cash flows (investments in, portfolio value out)
    equal to zero.
    Best suited for regular-contribution portfolios, where capital
    is added at different points in time — XIRR accounts for the exact timing
    of each investment, unlike CAGR.
    """,
)

sign_t = "+" if twr_value >= 0 else ""
col_5.metric(
    label="TWR",
    value=f"{sign_t}{twr_value:.1%}",
    help="""
    **Time-Weighted Return**: links the (annualised) holding-period returns between each
    cash-flow event, eliminating the effect of the size and timing of deposits.
    This makes it directly comparable to benchmark indices, regardless of how you invest.
    """,
)

df_pivot = get_portfolio_pivot(
    df=df_j,
    df_dimensions=df_registry,
    pf_actual_value=pf_actual_value,
    aggregation_level="ticker",
)

st.markdown("***")

st.markdown("## Current portfolio asset allocation")
fig = plot_sunburst(df=df_pivot)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG_NO_LOGO)

with st.expander("Show me a table"):
    group_by = st.radio(
        label="Aggregate by:",
        options=["Macro Asset Classes", "Asset Classes", "Tickers"],
        index=1,
        horizontal=True,
    )
    df_pivot_ = get_portfolio_pivot(
        df=df_j,
        df_dimensions=df_registry,
        pf_actual_value=pf_actual_value,
        aggregation_level=DICT_GROUPBY_LEVELS[group_by],
    )
    st.dataframe(
        df_pivot_.rename(
            columns={
                "macro_asset_class": "Macro Asset Class",
                "asset_class": "Asset Class",
                "ticker_yf": "Ticker",
                "name": "Name",
                "position_value": "Position Value",
                "weight_pf": "Weight",
            }
        ).style.format(
            {
                "Position Value": "{:,.1f} €",
                "Weight": "{:,.1f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("***")

st.markdown("## Profit & Loss by asset class")

group_by = st.radio(
    label="Evaluate PnL with respect to:",
    options=["Macro Asset Classes", "Asset Classes"],
    horizontal=True,
)

dict_group_by = {
    "Macro Asset Classes": "macro_asset_class",
    "Asset Classes": "asset_class",
}

df_pnl_by_asset_class = get_pnl_by_asset_class(
    df=df_j, df_dimensions=df_registry, group_by=dict_group_by[group_by]
)

fig = plot_pnl_by_asset_class(
    df_pnl=df_pnl_by_asset_class, group_by=dict_group_by[group_by]
)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG)

st.markdown("***")

st.markdown("## Wealth history")

df_wealth = get_wealth_history(df_transactions=df_transactions, ticker_list=ticker_list)

fig = plot_wealth(df=df_wealth)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG)

write_disclaimer()
