import streamlit as st

from input_output import write_disclaimer, login_or_register, get_max_common_history
from returns import get_period_returns, get_rolling_returns
from plot import plot_correlation_map, plot_returns, plot_rolling_returns
from var import (
    GLOBAL_STREAMLIT_STYLE,
    PLT_CONFIG_NO_LOGO,
    FAVICON,
    DICT_GROUPBY_LEVELS,
    DICT_FREQ_RESAMPLE,
    PLT_CONFIG,
)

st.set_page_config(
    page_title="PFN | Return Analysis",
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
    df_transactions = st.session_state["data"]
    df_registry = st.session_state["dimensions"]
else:
    st.error("Oops... there's nothing to display. Go through 🏠 first to load the data")
    st.stop()

df_n_shares = (
    df_transactions.groupby("ticker_yf")
    .agg(n_shares=("shares", "sum"))
    .sort_values("n_shares", ascending=False)
)
ticker_list = df_n_shares.loc[~(df_n_shares == 0).all(axis=1)].index.unique().to_list()
df_common_history = get_max_common_history(ticker_list=ticker_list)

st.markdown("## Global settings")

col_l_up, col_r_up = st.columns([1, 1], gap="small")

level = col_l_up.radio(
    label="Aggregate by:",
    options=["Macro Asset Classes", "Asset Classes", "Tickers"],
    horizontal=True,
    index=2,
    key="level",
    help="Choose how to aggregate data for analysis: Tickers provides the most granular view, while Macro Asset Classes aggregates at the highest level",
)
freq = col_r_up.radio(
    label="Frequency of returns:",
    options=["Month", "Week", "Day"],
    horizontal=True,
    index=2,
    key="freq",
)

st.markdown("<br>", unsafe_allow_html=True)
col_l_mid, col_c_mid, col_r_mid = st.columns([0.3, 1, 0.3], gap="small")
first_transaction = df_transactions["transaction_date"].sort_values().values[0]

first_day, last_day = col_c_mid.select_slider(
    "Select a time slice:",
    options=df_common_history.index,
    value=[
        max(df_common_history.index[0], first_transaction),
        df_common_history.index[-1],
    ],
    format_func=lambda value: str(value)[:10],
    label_visibility="collapsed",
)

st.markdown("***")

st.markdown(f"## Correlation of {freq.lower().replace('day','dai')}ly returns")

enhance_corr = st.radio(
    "Kind of correlation to highlight:",
    options=["Positive", "Null", "Negative"],
    index=1,
    horizontal=True,
)

df_rets = get_period_returns(
    df=df_common_history.loc[first_day:last_day, :],
    df_registry=df_registry,
    tickers_to_evaluate=ticker_list,
    period=DICT_FREQ_RESAMPLE[freq],
    level=DICT_GROUPBY_LEVELS[level],
)

fig = plot_correlation_map(
    df=df_rets.corr(),
    enhance_correlation=enhance_corr.lower(),
)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG_NO_LOGO)

st.markdown("***")

st.markdown(f"## Distribution of {freq.lower().replace('day','dai')}ly returns")

default_objs = df_rets.columns.to_list()
cols = st.multiselect(
    f"Choose the {level.lower()} to display:",
    options=default_objs,
    default=default_objs[0],
    key="sel_lev_1",
)

annotation_list = [
    f"<b>{col_}</b> ⟶ excess kurtosis: {df_rets[col_].kurtosis().round(1)}, skewness: {df_rets[col_].skew().round(1)}"
    for col_ in cols
]

fig = plot_returns(df=df_rets[cols], annotation_text="<br>".join(annotation_list))
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG)

st.markdown("***")

st.markdown("## Rolling returns")

col_l_lw, col_r_lw = st.columns([1.3, 1], gap="large")

cols = col_l_lw.multiselect(
    f"Choose the {level.lower()} to display:",
    options=default_objs,
    default=default_objs[0],
    key="sel_lev_2",
)

window = col_r_lw.slider(
    "Choose a rolling window:",
    min_value=1,
    max_value=df_common_history.loc[first_day:last_day, :].shape[0] - 2,
    value=30,
)

df_roll_ret = get_rolling_returns(
    df_prices=df_common_history.loc[first_day:last_day, :].ffill(),
    df_registry=df_registry,
    tickers_to_evaluate=ticker_list,
    level=DICT_GROUPBY_LEVELS[level],
    window=window,
)[cols]

fig = plot_rolling_returns(df_roll_ret, window)
st.plotly_chart(fig, use_container_width=True, config=PLT_CONFIG)
# TODO add start and end period in hover

write_disclaimer()
