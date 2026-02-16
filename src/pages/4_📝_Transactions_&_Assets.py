from datetime import datetime, timezone
from bson.objectid import ObjectId

import streamlit as st
import pandas as pd

from var import FAVICON, GLOBAL_STREAMLIT_STYLE
from mongo import init_connection
from user import get_user_transactions
from input_output import check_session_sidebar, ensure_data_is_loaded, load_data
from models import TransactionModel, AssetModel

st.set_page_config(
    page_title="PFN | Manage Transactions",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

check_session_sidebar()
ensure_data_is_loaded()

user_id = st.session_state["user"]
db = init_connection()["pfn"]

# Notifica persistente dopo rerun
if st.session_state.get("sync_success"):
    st.toast("Database synced!", icon="✅")
    del st.session_state["sync_success"]


def refresh_session_data():
    st.cache_data.clear()
    df_t, df_a = load_data(user_id, is_mock=False)
    st.session_state["data"] = df_t
    st.session_state["dimensions"] = df_a


st.markdown("## Manage Transactions")
st.markdown(
    f"Add new operations or edit transactions history for **{st.session_state['user']}'s portfolio**."
)


# --- FORM INSERIMENTO ---

with st.form("transaction_form", clear_on_submit=True):
    col_l, col_m, col_r = st.columns([1, 0.2, 0.6])
    ticker_yf = col_l.text_input("Ticker YF (e.g., AAPL.US)").upper().strip()
    transaction_type = col_r.radio("Type", ["Buy", "Sell"], horizontal=True)

    col1, col2, col3, col4 = st.columns(4)
    shares = col1.number_input("Shares", min_value=1, step=1)
    price = col2.number_input("Price (€)", min_value=0.0, format="%.2f")
    fees = col3.number_input("Fees (€)", min_value=0.0, format="%.2f")
    date = col4.date_input("Date", datetime.today().date())

    submitted = st.form_submit_button("Save Transaction", icon="💾")

if submitted:
    if not ticker_yf:
        st.error("Ticker is required")
    else:
        asset_doc = db["assets"].find_one({"ticker_yf": ticker_yf})

        if not asset_doc:
            st.session_state["pending_ticker"] = ticker_yf
            st.warning(f"Ticker {ticker_yf} not found. Define it below.")
        else:
            try:
                new_tx = TransactionModel(
                    user_id=user_id,
                    ticker_yf=ticker_yf,
                    transaction_type=transaction_type,
                    transaction_date=datetime.combine(date, datetime.min.time()),
                    shares=shares,
                    price=price,
                    fees=fees,
                )
                db["transactions"].insert_one(new_tx.model_dump())
                st.session_state["sync_success"] = True
                refresh_session_data()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- FORM NUOVO ASSET ---
if "pending_ticker" in st.session_state:
    with st.expander(f"New Asset: {st.session_state['pending_ticker']}", expanded=True):
        with st.form("asset_form"):
            name = st.text_input("Full Name (e.g. Apple Inc.)")
            m_class = st.text_input("Macro Class (e.g. Equities)")
            a_class = st.text_input("Class (e.g. Tech)")

            if st.form_submit_button("Create & Save"):
                try:
                    new_asset = AssetModel(
                        ticker_yf=st.session_state["pending_ticker"],
                        security_full_name=name,
                        asset_class=a_class,
                        macro_asset_class=m_class,
                    )
                    db["assets"].insert_one(new_asset.model_dump())

                    # Salva anche la transazione
                    new_tx = TransactionModel(
                        user_id=user_id,
                        ticker_yf=st.session_state["pending_ticker"],
                        transaction_type=transaction_type,
                        transaction_date=datetime.combine(date, datetime.min.time()),
                        shares=shares,
                        price=price,
                        fees=fees,
                    )
                    db["transactions"].insert_one(new_tx.model_dump())

                    del st.session_state["pending_ticker"]
                    st.session_state["sync_success"] = True
                    refresh_session_data()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

st.markdown("---")

# --- DATA EDITOR ---
st.markdown(f"### {st.session_state['user']}'s Transactions History")
st.markdown(
    "Double-click cells to edit. To delete a row, select it and press the trash icon. Remember to push changes to the cloud!"
)
user_df = get_user_transactions(user_id)

if not user_df.empty:
    edited_df = st.data_editor(
        user_df,
        column_config={
            "_id": None,
            "ticker_yf": st.column_config.TextColumn("Ticker", width="medium"),
            "transaction_type": st.column_config.SelectboxColumn(
                "Type", options=["Buy", "Sell"]
            ),
            "shares": st.column_config.NumberColumn(
                "Shares", help="Negative for Sales"
            ),
            "price": st.column_config.NumberColumn("Price", format="%.2f €"),
            "transaction_date": st.column_config.DateColumn("Date"),
            "fees": st.column_config.NumberColumn("Fees", format="%.2f €"),
        },
        use_container_width=True,
        num_rows="dynamic",
        key="tx_editor",
    )

    if st.button("Push Changes to Cloud", icon="☁️", use_container_width=True):
        changes = st.session_state["tx_editor"]
        has_changes = False

        if changes["deleted_rows"]:
            for row_idx in changes["deleted_rows"]:
                db["transactions"].delete_one(
                    {"_id": ObjectId(user_df.iloc[row_idx]["_id"])}
                )
            has_changes = True

        if changes["edited_rows"]:
            for row_idx, updated_fields in changes["edited_rows"].items():
                # Se l'utente modifica 'shares' nella tabella, lo riconvertiamo in positivo per il DB
                if "shares" in updated_fields:
                    updated_fields["shares"] = abs(updated_fields["shares"])

                if "transaction_date" in updated_fields:
                    updated_fields["transaction_date"] = datetime.combine(
                        pd.to_datetime(updated_fields["transaction_date"]),
                        datetime.min.time(),
                    )

                db["transactions"].update_one(
                    {"_id": ObjectId(user_df.iloc[row_idx]["_id"])},
                    {"$set": {**updated_fields, "updated": datetime.now(timezone.utc)}},
                )
            has_changes = True

        if has_changes:
            st.session_state["sync_success"] = True
            refresh_session_data()
            st.rerun()
