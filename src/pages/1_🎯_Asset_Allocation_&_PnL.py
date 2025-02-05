from datetime import datetime

import streamlit as st

from var import (
    GLOBAL_STREAMLIT_STYLE,
    PLT_CONFIG,
    PLT_CONFIG_NO_LOGO,
    FAVICON,
    DICT_GROUPBY_LEVELS,
)
from input_output import write_disclaimer, login_or_register, get_last_closing_price
from aggregation import (
    aggregate_by_ticker,
    get_pnl_by_asset_class,
    get_portfolio_pivot,
    get_wealth_history,
)
from plot import plot_sunburst, plot_wealth, plot_pnl_by_asset_class

st.set_page_config(
    page_title="PFN | Asset Allocation & PnL",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

if "user" not in st.session_state:
    login_or_register()

st.sidebar.write(
    f"Logged in as <b>{st.session_state['user']}</b>", unsafe_allow_html=True
)
if st.sidebar.button("Logout"):
    del st.session_state["user"]
    st.rerun()

if "data" in st.session_state:
    df_storico = st.session_state["data"]
    df_anagrafica = st.session_state["dimensions"]
else:
    st.error("Oops... there's nothing to display. Go through 🏠 first to load the data")
    st.stop()

df_pf = aggregate_by_ticker(df_storico, in_pf_only=True)

ticker_list = df_pf["ticker_yf"].to_list()
df_last_closing = get_last_closing_price(ticker_list=ticker_list)

df_j = df_pf[["ticker_yf", "dca", "shares"]].merge(
    df_last_closing[["ticker_yf", "price"]], how="left", on="ticker_yf"
)

expense = (df_j["shares"] * df_j["dca"]).sum()
fees = df_storico["fees"].sum().round(2)

st.markdown("## Profit & Loss")

col_l, col_m, col_r = st.columns([1, 1, 1], gap="small")

consider_fees = st.checkbox("Take fees into account")

df_j["position_value"] = df_j["shares"] * df_j["price"]
pf_actual_value = df_j["position_value"].sum()
total_expense = expense + fees if consider_fees else expense
pnl = pf_actual_value - total_expense
pnl_perc = pnl / total_expense
sign = "+" if pnl >= 0 else ""

col_l.metric(
    label="Actual portfolio value",
    value=f"{pf_actual_value: ,.1f} €",
    delta=f"{sign}{pnl: ,.1f} €",
)

col_m.metric(
    label="Return On Investment (ROI)",
    value=f"{sign}{pnl_perc: .1%}",
    help="""
    ROI shows the total gain or loss as a percentage of the original amount
    invested, regardless of how long the investment was held
    """,
)

first_transaction = df_storico["transaction_date"].sort_values()[0]
n_years = (datetime.now() - first_transaction).days / 365.25
annualised_ret = ((pf_actual_value / total_expense) ** (1 / n_years)) - 1

col_r.metric(
    label="Annualised return",
    value=f"{sign}{annualised_ret: .1%}",
    help="""
    This measures the average yearly return, helping compare investments
    held for different periods by standardising the return on an annual basis
    """,
)

df_pivot = get_portfolio_pivot(
    df=df_j,
    df_dimensions=df_anagrafica,
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
        df_dimensions=df_anagrafica,
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
    df=df_j, df_dimensions=df_anagrafica, group_by=dict_group_by[group_by]
)

fig = plot_pnl_by_asset_class(
    df_pnl=df_pnl_by_asset_class, group_by=dict_group_by[group_by]
)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG)

st.markdown("***")

st.markdown("## Wealth history")

df_wealth = get_wealth_history(df_transactions=df_storico, ticker_list=ticker_list)

fig = plot_wealth(df=df_wealth)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG)

write_disclaimer()
