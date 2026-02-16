import os

import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi


@st.cache_resource
def init_connection() -> MongoClient:
    uri = os.getenv("STREAMLIT_MONGO__URI")
    if not uri:
        try:
            uri = st.secrets["mongo"]["uri"]
        except Exception:
            st.error(
                "Error: Connection URI not found. Please set the STREAMLIT_MONGO__URI environment variable or add it to Streamlit secrets."
            )
            st.stop()

    return MongoClient(uri, server_api=ServerApi("1"))
