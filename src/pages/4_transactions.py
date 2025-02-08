from datetime import datetime

import streamlit as st

from mongo import init_connection
from user import get_user_transactions
from input_output import login_or_register

if "user" not in st.session_state:
    login_or_register()

user_id = st.session_state["user"]
st.sidebar.write(f"Logged in as <b>{user_id}</b>", unsafe_allow_html=True)
if st.sidebar.button("Logout"):
    del st.session_state["user"]
    st.rerun()

client = init_connection()
transactions = client["pfn"]["transactions"]
assets = client["pfn"]["assets"]

with st.form("transaction_form"):
    col_l, col_m, col_r = st.columns([1, 0.2, 0.6])
    ticker = col_l.text_input(
        "Ticker",
        placeholder="e.g., MWRD.MI or FLXI.DE",
        help="""
        Some tickers are ambigous and require you to specify the exchange.

        For example, to get data for VWCE you should write VWCE.MI for Borsa Italiana,
        VWCE.DE for XETRA, and so on. More on Yahoo Finance Market Coverage: https://help.yahoo.com/kb/SLN2310.html
        """,
    ).upper()
    transaction_type = col_r.radio("Transaction type", ["Buy", "Sell"], horizontal=True)
    col_l, col_m, col_r = st.columns([1, 1, 1])
    quantity = col_l.number_input("Shares", min_value=1, step=1)
    price = col_m.number_input(
        "Price per share (€)", min_value=0.00, step=0.01, format="%.2f"
    )
    date = col_r.date_input(
        "Transaction date",
        datetime.today().date(),
        format="DD/MM/YYYY",
    )

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

        # Once the asset has been created, save the transaction as well
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


with st.expander("Your transactions"):
    user_df = get_user_transactions(user_id)

    if not user_df.empty:
        st.write("Tip: you can edit your transactions by double-clicking on a field!")
        column_config = {
            "transaction_type": st.column_config.SelectboxColumn(
                "Transaction type", options=["Buy", "Sell"], required=True
            ),
            "quantity": st.column_config.NumberColumn(
                "Shares", min_value=1, step=1, required=True
            ),
            "ticker": st.column_config.TextColumn("Ticker", required=True),
            "price": st.column_config.NumberColumn(
                "Price per share",
                min_value=0.0,
                step=0.01,
                format="€ %.2f",
                required=True,
            ),
            # "date": st.column_config.DateColumn(
            #     "Transaction date", format="DD-MM-YYYY", required=True
            # ),
        }
        st.data_editor(
            user_df,
            column_config=column_config,
            use_container_width=True,
            num_rows="fixed",
        )
    else:
        st.write("You have not yet registered any transaction")
