import pandas as pd
from pymongo import MongoClient
import streamlit as st

from var import CACHE_EXPIRE_SECONDS

# Mongo utils


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS)
def get_suffixes():
    yahurl = "https://help.yahoo.com/kb/SLN2310.html"

    r = pd.read_html(yahurl, keep_default_na=False)[0]
    dizi = []
    for i, row in r.iterrows():
        dizi.append(
            row["Country"]
            + " - "
            + row["Market, or Index"]
            + " - "
            + row["Suffix"].replace(".", ""),
        )
    return dizi


def get_collection(mongo_uri, table):
    mongo_db = "pfn_db"
    mongo_collection = f"pfn_portfolio_{table}"

    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    collection = db[mongo_collection]

    return collection


def get_mongo_table(mongo_uri):
    storico_col = get_collection(mongo_uri, "storico")
    anagrafica_col = get_collection(mongo_uri, "anagrafica")
    df_storico = pd.DataFrame(list(storico_col.find()))
    df_anagrafica = pd.DataFrame(list(anagrafica_col.find()))
    return df_storico, df_anagrafica


def df_to_mongo(df, mongo_uri, tipo):
    col = get_collection(mongo_uri, tipo)
    data_json = df.to_dict(orient="records")
    col.insert_many(data_json)
    return True
