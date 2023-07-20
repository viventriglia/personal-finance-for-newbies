import streamlit as st
import yfinance
from data_utils import get_collection, get_mongo_table, get_suffixes
from var import FAVICON, GLOBAL_STREAMLIT_STYLE

st.set_page_config(
    page_title="PFN | Add element to pf",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

if "demo" in st.session_state:
    st.error("Nooooo telecamera! No, no, no")
    st.stop()
elif "data" in st.session_state:
    try:
        df_storico, df_anagrafica = get_mongo_table(st.session_state["mongo_uri"])
    except:
        st.error("🚨 Errore nel download da MongoDB")
else:
    st.error("Oops... there's nothing to display. Go through 🏠 first to load the data")
    st.stop()


def add_transaction():
    ok = True
    st.header("Aggiungi Transazione al Portafoglio")

    exchange = st.selectbox(
        label="Exchange (suffix of the market - es. NYSE, NASDAQ):",
        options=get_suffixes(),
    )
    exc = exchange.split(" - ")[-1]
    st.success(exc)
    ticker = st.text_input(
        "Ticker (symbol to identify the security - es. AAPL, GOOGL):"
    )
    if len(ticker) > 1:
        try:
            ticker = ticker.upper()
            ytick = yfinance.Ticker(ticker + "." + exc)
            st.success(ytick.info["longName"].title())
        except:
            ok = False
            st.error("Il ticker sembra non esistere")
    asset = st.text_input("Asset (es. World Stocks, Gold):")
    macroasset = st.text_input("Macro-asset (es. Bonds, Stocks):")
    transaction_date = st.date_input("Transaction Date:")
    shares = st.number_input("Shares:", step=1.0, min_value=1.0)
    price = st.number_input("Price per Share:")
    fees = st.number_input("Fees (if any):")

    if st.button("Aggiungi Transazione"):
        if (
            not exchange
            or not ticker
            or not asset
            or not macroasset
            or not transaction_date
            or not shares
            or not price
            or not ok
        ):
            st.warning("Per favore, ricontrolla i campi obbligatori.")
        else:
            formatted_date = transaction_date.strftime("%Y-%m-%d")
            transaction_data = {
                "exchange": exchange,
                "ticker": ticker,
                "transaction_date": formatted_date,
                "shares": shares,
                "price": price,
                "fees": fees,
            }
            anagrafica_data = {
                "exchange": exchange,
                "ticker": ticker,
                "name": ytick.info["longName"].title(),
                "asset_class": asset,
                "macro_asset_class": macroasset,
                "ticker_yf": ticker + "." + exc,
            }

            filtro = {"$set": anagrafica_data}

            # Salva i dati e l'anagrafica nel database MongoDB
            storico_col = get_collection(st.session_state["mongo_uri"], "storico")
            storico_col.insert_one(transaction_data)

            anagrafica_col = get_collection(st.session_state["mongo_uri"], "anagrafica")
            a = anagrafica_col.update_one(
                anagrafica_data,
                filtro,
                upsert=True,
            ).upserted_id
            st.success("Transazione aggiunta con successo!")
            st.success(f"Ho aggiornato {int(a!=None)} campi anagrafica")


def main():
    st.title("App Gestione Portafoglio Finanziario")
    add_transaction()


main()
