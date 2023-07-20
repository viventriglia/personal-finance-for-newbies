import json
from pathlib import Path

import streamlit as st
from data_utils import df_to_mongo, get_mongo_table

from utils import load_data, write_disclaimer
from var import (
    GLOBAL_STREAMLIT_STYLE,
    DATA_PATH,
    FAVICON,
    APP_VERSION,
)

st.set_page_config(
    page_title="PFN",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

st.title(f"Welcome to Personal Finance for Newbies!")
st.text(f"v{APP_VERSION}")

st.markdown(
    "PFN is a web app that – from buy/sell financial asset transactions – provides easy-to-use, \
    near-real-time statistics (*i.e.*, updated to the last closing) on your investment portfolio."
)
st.markdown("***")
st.markdown("## Let's get started")

st.markdown("If you have a MongoURI,, you can put it here to download your portfolio.")

cred = ""
if Path.exists(Path("..", "creds", "creds.json")):
    with open("../creds/creds.json", "r") as f:
        cred = json.load(f)["uri"]

mongo_uri = st.text_input("Inserisci il tuo Mongo URI e premi invio", value=cred)
if len(mongo_uri) > 1:
    if not mongo_uri.endswith("/?retryWrites=true&w=majority"):
        mongo_uri = mongo_uri + "/?retryWrites=true&w=majority"
    st.session_state["mongo_uri"] = mongo_uri
if st.button("Carica i dati da Mongo", disabled=len(mongo_uri) == 0):
    st.session_state["data"], st.session_state["dimensions"] = get_mongo_table(
        mongo_uri
    )
    st.success("Dati caricati con successo")
    st.balloons

st.markdown("---")

st.markdown(
    "To load your data, fill in the template with your accumulation plan's buy/sell transactions and upload it here:",
    unsafe_allow_html=True,
)

with st.expander("**Restore** your portfolio from file."):
    col_l, col_r = st.columns([1, 0.8], gap="small")
    uploaded_file = col_l.file_uploader(
        label="Upload your Data",
        label_visibility="collapsed",
        accept_multiple_files=False,
        type="xlsx",
    )
    if uploaded_file is not None:
        try:
            df_storico, df_anagrafica = load_data(uploaded_file)
            df_to_mongo(df_storico, st.session_state["mongo_uri"], "storico")
            df_to_mongo(df_anagrafica, st.session_state["mongo_uri"], "anagrafica")
            st.session_state["data"] = df_storico
            st.session_state["dimensions"] = df_anagrafica

        except:
            st.error(
                "Please check your file format and make sure it matches the template"
            )
            st.stop()

    with open(DATA_PATH / Path("template.xlsx"), "rb") as f:
        col_l.download_button(
            "Download Template",
            data=f,
            file_name="template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# DEMO
with st.expander(
    "If you wish to **explore** the app first, load some **demo data** instead:"
):
    # st.markdown("##")
    # st.markdown(
    #     "If you wish to **explore** the app first, load some **demo data** instead:",
    #     unsafe_allow_html=True,
    # )

    if st.button(label="Load Mock Data", key="load_mock_df"):
        df_storico, df_anagrafica = load_data(DATA_PATH / Path("demo.xlsx"))
        st.session_state["data"] = df_storico
        st.session_state["dimensions"] = df_anagrafica
        st.session_state["mongo_uri"] = "demo"
        st.session_state["demo"] = "1"


write_disclaimer()
