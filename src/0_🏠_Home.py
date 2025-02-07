from pathlib import Path

import streamlit as st

from input_output import load_data, write_disclaimer
from var import (
    GLOBAL_STREAMLIT_STYLE,
    DATA_PATH,
    FILE_UPLOADER_CSS,
    FAVICON,
    APP_VERSION,
    COVER,
)

st.set_page_config(
    page_title="PFN",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

if "user" in st.session_state:
    st.sidebar.write(
        f"Logged in as <b>{st.session_state['user']}</b>", unsafe_allow_html=True
    )
    if st.sidebar.button("Logout"):
        del st.session_state["user"]
        st.rerun()

st.title(f"Welcome to Personal Finance for Newbies!")
st.text(f"v{APP_VERSION}")

col_l, col_r = st.columns([0.8, 1], gap="large")

col_r.markdown(
    """
    Personal Finance for Newbies (or PFN) is a web app that – from buy/sell
    financial asset transactions – provides easy-to-use, near-real-time statistics
    (*i.e.*, updated to the last closing) on your investment portfolio.
    <br><br>
    PFN allows you to analyse your portfolio from multiple perspectives:
    from higher-level metrics (profit & loss, asset class weights) to those
    allowing you to study risk and returns in depth, especially over time.
    To use the app, you don't need to create an account! You just need to set up a file
    (see the template below) containing your buy/sell transactions. PFN takes care of
    downloading historical prices from [Yahoo Finance](https://finance.yahoo.com/)
    and analysing them for you.
    <br><br>
    We do not collect or store any data. Nor do we provide any guarantee of the accuracy
    of the results displayed, which are intended for educational and informational
    purposes only. The project is open source and we always look for pull requests,
    if you know better!
    <br><br>
    <i>Someone's sitting in the shade today because someone planted a tree
    a long time ago</i> (W. Buffet)
    """,
    unsafe_allow_html=True,
)
col_l.image(COVER)

st.markdown("***")

st.markdown("## What assets do you have in your portfolio?")
st.markdown(
    """
    To get started, upload your data, filling in the template with the buy/sell
    transactions of your accumulation plan. Instructions can be found within
    the template itself.
    """,
    unsafe_allow_html=True,
)
col_l, col_r = st.columns([0.25, 0.95], gap="small")

uploaded_file = col_r.file_uploader(
    label="Upload your Data",
    type=["xls", "xlsx", "xlsm", "xlsb", "odf", "ods"],
    label_visibility="collapsed",
    accept_multiple_files=False,
)
st.markdown(FILE_UPLOADER_CSS, unsafe_allow_html=True)
if uploaded_file is not None:
    try:
        df_storico, df_anagrafica = load_data(uploaded_file)
        st.session_state["data"] = df_storico
        st.session_state["dimensions"] = df_anagrafica
    except ValueError:
        st.error("Please check your file format and make sure it matches the template")

with open(DATA_PATH / Path("template.xlsx"), "rb") as f:
    col_l.download_button(
        "Download Template",
        icon="📑",
        data=f,
        file_name="template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Fill in this template and upload it using the adjacent button",
    )

st.markdown(
    "<br>If you wish to explore the app first, load some **demo** data instead.",
    unsafe_allow_html=True,
)

if st.button(
    label="Load Mock Data",
    icon="📊",
    key="load_mock_df",
    help="Load data to start a demo",
):
    df_storico, df_anagrafica = load_data(DATA_PATH / Path("demo.xlsx"))
    st.session_state["data"] = df_storico
    st.session_state["dimensions"] = df_anagrafica

st.markdown("***")

st.markdown("## How do I analyse my portfolio?")

st.markdown(
    """
    Once you have the data in place, you can explore the different sections
    of the app. On the first page you can study the current portfolio composition,
    the PnL by asset class, and the evolution (since inception of the accumulation
    plan) of your wealth. On the second page you can investigate the correlations
    of returns, their distributions, as well as rolling returns. Finally, the last
    page allows you to visualise portfolio risk in terms of drawdowns and relative
    risk contributions.
    """,
    unsafe_allow_html=True,
)
col_l_l, col_l_m, col_l_r = st.columns([1, 1, 1], gap="large")
col_l_l.page_link(
    "pages/1_🎯_Asset_Allocation_&_PnL.py",
    label="Asset Allocation & PnL",
    icon="🎯",
    help="Portfolio composition, PnL, wealth evolution",
)
col_l_m.page_link(
    "pages/2_📈_Return_Analysis.py",
    label="Return Analysis",
    icon="📈",
    help="Distribution and correlation of returns, rolling returns",
)
col_l_r.page_link(
    "pages/3_⚠️_Risk_Analysis.py",
    label="Risk Analysis",
    icon="⚠️",
    help="Portfolio drawdowns, relative risk contributions",
)

st.markdown(
    """
    👉🏻 Keep in mind that this app is constantly evolving, which means that new
    features and/or new sections may pop up!
    """,
    unsafe_allow_html=True,
)

write_disclaimer()
