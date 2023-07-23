import streamlit as st
from data_utils import get_collection, get_mongo_table
from var import FAVICON, GLOBAL_STREAMLIT_STYLE

st.set_page_config(
    page_title="PFN | Remove element from pf",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

if "demo" in st.session_state:
    st.error("Nooooo telecamera! No, no, no")
    st.stop()

if "data" in st.session_state:
    try:
        df_storico, df_anagrafica = (
            st.session_state["data"],
            st.session_state["dimensions"],
        )
    except:
        st.error("🚨 Errore nel download da MongoDB")
else:
    st.error("Oops... there's nothing to display. Go through 🏠 first to load the data")
    st.stop()


def id_in_coda(lista):
    # Qua si può rendere più bellina la lista che esce, l'importante è che si conservi il campo _id in fondo
    res = []
    for item in lista:
        value = item.pop("_id")
        item["_id"] = value

        res.append(item)
    return res


def remove_item(expander_title, collection):
    with st.expander(expander_title, expanded=True):
        items = collection.find()
        item_names = list(items)
        item_names = id_in_coda(item_names)
        if len(item_names) == 0:
            st.warning("La collezione è vuota.")
            return

        selected_item = st.multiselect(
            "Seleziona l'elemento da rimuovere:",
            item_names,
            key=f"{expander_title}_box",
        )

        if st.button("Rimuovi", key=f"{expander_title}_button"):
            for item in selected_item:
                collection.delete_one({"_id": item["_id"]})
            st.success("Elementi rimossi con successo.")
            # Aggiorno i dati in memoria
            st.session_state["data"], st.session_state["dimensions"] = get_mongo_table(
                st.session_state["mongo_uri"]
            )


def main():
    st.title("Gestione Portafoglio Finanziario")

    storico_col = get_collection(st.session_state["mongo_uri"], "storico")
    anagrafica_col = get_collection(st.session_state["mongo_uri"], "anagrafica")

    st.header("Rimuovi Elemento dalla Collezione Storico")
    remove_item("Rimuovi Transazione", storico_col)

    st.header("Rimuovi Elemento dalla Collezione Anagrafica")
    remove_item("Rimuovi Anagrafica", anagrafica_col)


main()
