import streamlit as st
from data_utils import get_collection, get_mongo_table

from var import (
    GLOBAL_STREAMLIT_STYLE,
    PLT_CONFIG,
    PLT_CONFIG_NO_LOGO,
    FAVICON,
)
from utils import (
    aggregate_by_ticker,
    get_last_closing_price,
    get_max_common_history,
    get_wealth_history,
    get_portfolio_pivot,
    get_pnl_by_asset_class,
    write_disclaimer,
)
from plot import plot_sunburst, plot_wealth, plot_pnl_by_asset_class

st.set_page_config(
    page_title="PFN | Basic Stats",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

if "demo" in st.session_state:
    df_storico = st.session_state["data"]
    df_anagrafica = st.session_state["dimensions"]
elif "data" in st.session_state:
    try:
        # df_storico, df_anagrafica = get_mongo_table(st.session_state["mongo_uri"])
        df_storico = st.session_state["data"]
        df_anagrafica = st.session_state["dimensions"]
    except:
        st.error("🚨 Errore nel download da MongoDB")
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

st.markdown("## Profit and Loss")

col_l, col_r = st.columns([1, 1], gap="small")

consider_fees = st.checkbox("Take fees into account")

pf_actual_value = (df_j["shares"] * df_j["price"]).sum()
if consider_fees:
    pnl = pf_actual_value - expense - fees
    pnl_perc = 100 * (pf_actual_value - expense - fees) / expense
else:
    pnl = pf_actual_value - expense
    pnl_perc = 100 * (pf_actual_value - expense) / expense
sign = "+" if pnl >= 0 else ""

col_l.metric(
    label="Actual Portfolio Value",
    value=f"{pf_actual_value: .1f} €",
    delta=f"{pnl: .1f} € ({sign}{pnl_perc: .1f}%)",
)

df_j["position_value"] = df_j["shares"] * df_j["price"]
df_pivot = get_portfolio_pivot(
    df=df_j,
    df_dimensions=df_anagrafica,
    pf_actual_value=pf_actual_value,
    aggregation_level="ticker",
)

st.markdown("***")

st.markdown("## Current Portfolio Asset Allocation")
fig = plot_sunburst(df=df_pivot)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG_NO_LOGO)

with st.expander("Show pivot table"):
    group_by = st.radio(
        label="Aggregate by:",
        options=["Macro Asset Classes", "Asset Classes", "Ticker"],
        horizontal=True,
    )
    dict_group_by = {
        "Macro Asset Classes": "macro_asset_class",
        "Asset Classes": "asset_class",
        "Ticker": "ticker",
    }
    df_pivot_ = get_portfolio_pivot(
        df=df_j,
        df_dimensions=df_anagrafica,
        pf_actual_value=pf_actual_value,
        aggregation_level=dict_group_by[group_by],
    )
    df_pivot_.index += 1
    st.table(
        df_pivot_.rename(
            columns={
                "macro_asset_class": "Macro Asset Class",
                "asset_class": "Asset Class",
                "ticker_yf": "Ticker",
                "name": "Name",
                "position_value": "Position Value (€)",
                "weight_pf": "Weight (%)",
            }
        ).style.format(precision=1)
    )

st.markdown("***")

st.markdown("## Profit and Loss by asset class")

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

st.markdown("## Daily value of the Accumulation Plan")

df_wealth = get_wealth_history(
    df_transactions=df_storico,
    df_prices=get_max_common_history(ticker_list=ticker_list),
)

fig = plot_wealth(df=df_wealth)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG)

write_disclaimer()
