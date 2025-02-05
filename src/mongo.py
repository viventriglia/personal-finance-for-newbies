import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi


@st.cache_resource
def init_connection() -> MongoClient:
    return MongoClient(st.secrets["mongo"]["uri"], server_api=ServerApi("1"))
