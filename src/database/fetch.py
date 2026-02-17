import streamlit as st
import pandas as pd

from utils.var import CACHE_EXPIRE_SECONDS
from database.connection import init_connection


@st.cache_data(ttl=CACHE_EXPIRE_SECONDS, show_spinner="Fetching data from DB")
def load_data(
    username: str, is_mock: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    client = init_connection()
    db_name = "mock" if is_mock else "pfn"
    db = client[db_name]

    # --- TRANSACTIONS ---
    query_t = {} if is_mock else {"user_id": username}
    # Carichiamo anche il tipo transazione per decidere il segno
    cursor_t = db["transactions"].find(query_t, {"_id": 0})
    df_t = pd.DataFrame(list(cursor_t))

    if not df_t.empty:
        # 1. Rinominiamo per compatibilità con le vecchie analisi
        df_t = df_t.rename(
            columns={
                "transaction_date": "transaction_date",  # Già corretto nel nuovo schema
                "shares": "shares",  # Già corretto
            }
        )

        # 2. TRUCCO DEL SEGNO: Se è 'Sell', moltiplichiamo shares per -1
        # Questo "ripara" istantaneamente l'aggregazione in tutte le pagine
        if "transaction_type" in df_t.columns:
            df_t.loc[df_t["transaction_type"] == "Sell", "shares"] *= -1

        # 3. Calcoli e conversioni
        df_t["transaction_date"] = pd.to_datetime(df_t["transaction_date"])
        df_t["shares"] = df_t["shares"].astype(float)
        df_t["price"] = df_t["price"].astype(float)
        df_t["fees"] = df_t.get("fees", 0.0).astype(float)
        df_t["ap_amount"] = df_t["shares"] * df_t["price"]

    # --- ASSETS --- (Logica invariata)
    cursor_a = db["assets"].find({}, {"_id": 0})
    df_a = pd.DataFrame(list(cursor_a))
    if not df_a.empty:
        df_a = df_a.rename(
            columns={
                "security_full_name": "name",
                "security_name": "name",
                "ticker_yf": "ticker_yf",
            }
        )

    return df_t, df_a


def get_user_transactions(user_id: str) -> pd.DataFrame:
    transactions = init_connection()["pfn"]["transactions"]
    user_transactions = list(transactions.find({"user_id": user_id}))
    df = pd.DataFrame(user_transactions)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "_id",
                "ticker_yf",
                "transaction_type",
                "shares",
                "price",
                "transaction_date",
                "fees",
            ]
        )

    df["_id"] = df["_id"].astype(str)

    if "transaction_type" in df.columns:
        df.loc[df["transaction_type"] == "Sell", "shares"] *= -1

    cols = [
        "_id",
        "ticker_yf",
        "transaction_type",
        "shares",
        "price",
        "transaction_date",
        "fees",
    ]
    df["transaction_date"] = pd.to_datetime(df["transaction_date"]).dt.date

    return df[cols].reset_index(drop=True)
