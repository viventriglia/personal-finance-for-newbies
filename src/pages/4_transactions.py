from datetime import datetime

import streamlit as st
import pandas as pd

from mongo import init_connection

client = init_connection()
transactions = client["pfn"]["transactions"]
assets = client["pfn"]["assets"]

# Form per registrare una transazione
with st.form("transaction_form"):
    col_l, col_m, col_r = st.columns([1, 0.2, 0.6])
    ticker = col_l.text_input("Ticker", placeholder="e.g., MWRD.MI or FLXI.DE").upper()
    transaction_type = col_r.radio("Transaction type", ["Buy", "Sell"], horizontal=True)
    col_l, col_m, col_r = st.columns([1, 1, 1])
    quantity = col_l.number_input("Shares", min_value=1, step=1)
    price = col_m.number_input(
        "Price per share (€)", min_value=0.00, step=0.01, format="%.2f"
    )
    date = col_r.date_input("Transaction date", datetime.today().date())

    submitted = st.form_submit_button("Save transaction", icon="💾")

if submitted:
    if not ticker:
        st.error("Please enter a valid ticker!", icon="⚠️")
    else:
        asset_exists = assets.find_one({"ticker": ticker})

        if not asset_exists:
            st.warning(
                f"{ticker} is not yet in your database; before inserting it, please supply some information 👇",
                icon="✋",
            )
            st.session_state["new_asset_ticker"] = ticker
        else:
            # Save transaction if the asset already exists
            transaction_data = {
                "user_id": st.session_state["user"],
                "asset": {"ticker": ticker},
                "transaction_type": transaction_type,
                "quantity": quantity,
                "price": price,
                "date": datetime.combine(date, datetime.min.time()),
                "created_at": datetime.utcnow(),
            }
            transactions.insert_one(transaction_data)
            st.success("Transaction successfully saved!", icon="✅")

if "new_asset_ticker" in st.session_state:
    st.write(f"### About {st.session_state['new_asset_ticker']}")
    with st.form("new_asset_form"):
        security_name = st.text_input(
            "Security Name", placeholder="Full name of the asset"
        )
        macro_asset_class = st.selectbox(
            "Macro Asset Class",
            ["Equities", "Bonds", "Commodities", "Real estate", "Other"],
        )
        asset_class = st.text_input(
            "Asset Class", placeholder="E.g., EU Inflation-linked Bonds or World Stocks"
        )

        asset_submitted = st.form_submit_button("Save asset", icon="💾")

    if asset_submitted:
        new_asset = {
            "ticker": st.session_state["new_asset_ticker"],
            "security_name": security_name,
            "asset_class": asset_class,
            "macro_asset_class": macro_asset_class,
            "updated_at": datetime.utcnow(),
        }
        assets.insert_one(new_asset)
        st.success(
            f"{st.session_state['new_asset_ticker']} successfully saved!", icon="✅"
        )

        # Una volta che l'asset è stato aggiunto, salva anche la transazione
        transaction_data = {
            "user_id": st.session_state["user"],
            "asset": {"ticker": st.session_state["new_asset_ticker"]},
            "transaction_type": transaction_type,
            "quantity": quantity,
            "price": price,
            "date": datetime.combine(date, datetime.min.time()),
            "created_at": datetime.utcnow(),
        }
        transactions.insert_one(transaction_data)
        st.success("Transaction successfully saved!", icon="✅")

        del st.session_state["new_asset_ticker"]


def get_user_transactions(user_id: str) -> pd.DataFrame:
    user_transactions = transactions.find({"user_id": user_id})
    df = pd.DataFrame(list(user_transactions))

    if not df.empty:
        df["ticker"] = df["asset"].apply(lambda x: x["ticker"])
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d-%m-%Y")
        df.index += 1
    return df[["ticker", "transaction_type", "quantity", "price", "date"]]


if "user" in st.session_state:
    user_id = st.session_state["user"]

    with st.expander("Visualizza le tue transazioni"):
        user_df = get_user_transactions(user_id)

        if not user_df.empty:
            st.dataframe(user_df)
        else:
            st.warning("Non hai ancora registrato alcuna transazione.")
else:
    st.warning("Per visualizzare le transazioni, effettua il login.")
