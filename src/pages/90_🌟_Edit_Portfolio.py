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
if "mongo_uri" not in st.session_state:
    st.error("🚨 Sezione disponibile solo con un MongoURI")
    st.stop()
if "data" in st.session_state:
    try:
        df_storico, df_anagrafica = (
            st.session_state["data"],
            st.session_state["dimensions"],
        )
    except:
        st.error("🚨 Errore nel download da MongoDB")
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
    shares = st.number_input("Shares:", step=1, min_value=1)
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
            # Aggiorno i dati in memoria
            st.session_state["data"], st.session_state["dimensions"] = get_mongo_table(
                st.session_state["mongo_uri"]
            )


def id_in_coda(lista):
    # Qua si può rendere più bellina la lista che esce, l'importante è che si conservi il campo _id in fondo
    res = []
    for item in lista:
        value = item.pop("_id")
        item["_id"] = value

        res.append(item)
    return res


def remove_item(expander_title, collection, tipo):
    # with st.expander(expander_title, expanded=True):
    # items = collection.find()
    # item_names = list(items)
    item_names = collection.to_dict(orient="records")
    item_names = id_in_coda(item_names)
    if collection.empty:
        st.warning("La collezione è vuota.")
        return

    selected_item = st.multiselect(
        "Seleziona l'elemento da rimuovere:",
        item_names,
        key=f"{expander_title}_box",
    )

    if st.button("Rimuovi", key=f"{expander_title}_button"):
        coll = get_collection(st.session_state["mongo_uri"], tipo)
        for item in selected_item:
            coll.delete_one({"_id": item["_id"]})
        st.success("Elementi rimossi con successo.")
        # Aggiorno i dati in memoria
        st.session_state["data"], st.session_state["dimensions"] = get_mongo_table(
            st.session_state["mongo_uri"]
        )


def main():
    st.title("App Gestione Portafoglio Finanziario")
    with st.expander("Aggiunta", expanded=True):
        add_transaction()
    # Rimozione
    with st.expander("Rimozione", expanded=False):
        st.header("Rimuovi Elemento dalla Collezione Storico")
        remove_item("Rimuovi Transazione", df_storico, "storico")

        st.header("Rimuovi Elemento dalla Collezione Anagrafica")
        remove_item("Rimuovi Anagrafica", df_anagrafica, "anagrafica")


main()
