import streamlit as st

from utils.ui import write_disclaimer, check_session_sidebar
from database.fetch import load_data
from utils.var import (
    GLOBAL_STREAMLIT_STYLE,
    FAVICON,
    APP_VERSION,
    COVER,
)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="PFN | Home",
    page_icon=str(FAVICON),
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(GLOBAL_STREAMLIT_STYLE, unsafe_allow_html=True)

# --- GESTIONE SESSIONE & AUTH ---
check_session_sidebar()

if "sync_msg" in st.session_state:
    m_type, m_text = st.session_state["sync_msg"]
    if m_type == "success":
        st.toast(m_text, icon="✅")
    elif m_type == "warning":
        st.toast(m_text, icon="⚠️")
    del st.session_state["sync_msg"]

# --- HEADER ---
st.title("Welcome to Personal Finance for Newbies!")
st.text(f"v{APP_VERSION}")

col_l, col_r = st.columns([0.8, 1], gap="large")

with col_r:
    st.markdown(
        f"""
        Welcome back **{st.session_state['user']}**!
        <br><br>
        Personal Finance for Newbies (PFN) is a web app designed to provide easy-to-use, 
        near-real-time statistics on your investment portfolio based on your transaction history.
        <br><br>
        PFN allows you to analyze your portfolio from multiple perspectives: 
        from high-level metrics like P&L and asset allocation to in-depth risk and 
        return analysis over time.
        <br><br>
        Your data is securely stored in a <b>MongoDB database</b>. PFN automatically fetches 
        historical prices from <a href="https://finance.yahoo.com/">Yahoo Finance</a> 
        to keep your valuation updated to the latest market close.
        <br><br>
        <i>"Someone's sitting in the shade today because someone planted a tree
        a long time ago"</i> (W. Buffet)
        """,
        unsafe_allow_html=True,
    )

col_l.image(str(COVER))

st.markdown("***")

# --- SEZIONE SORGENTE DATI (REAL VS MOCK) ---
st.markdown("## 🔄 Select Portfolio")

is_mock = st.session_state.get("is_mock", False)
status_color = "orange" if is_mock else "green"
status_text = "DEMO MODE (Mock Data)" if is_mock else "REAL MODE (Your Portfolio)"

st.markdown(f"Current Status: :{status_color}[**{status_text}**]")

col_info, col_mock, col_real = st.columns([1.5, 0.9, 0.9])

with col_info:
    st.write(
        """
        Select between your real portfolio or a demo portfolio to explore the app.
        """
    )

if col_mock.button(
    "Load Demo Data",
    icon="📊",
    use_container_width=True,
    help="Explore PFN with a sample portfolio",
):
    st.cache_data.clear()
    df_t, df_a = load_data(st.session_state["user"], is_mock=True)
    st.session_state["data"] = df_t
    st.session_state["dimensions"] = df_a
    st.session_state["is_mock"] = True
    st.session_state["sync_msg"] = ("success", "Demo data loaded!")
    st.rerun()

if col_real.button(
    "Sync My Portfolio",
    icon="🚀",
    use_container_width=True,
    help="Load your personal transactions from DB",
):
    st.cache_data.clear()
    df_t, df_a = load_data(st.session_state["user"], is_mock=False)
    st.session_state["data"] = df_t
    st.session_state["dimensions"] = df_a
    st.session_state["is_mock"] = False
    if not df_t.empty:
        st.session_state["sync_msg"] = ("success", "Portfolio synced successfully!")
    else:
        st.session_state["sync_msg"] = (
            "warning",
            "Your database is empty: add transactions.",
        )
    st.rerun()

if "data" not in st.session_state:
    with st.spinner("Initializing portfolio..."):
        df_t, df_a = load_data(st.session_state["user"], is_mock=False)
        st.session_state["data"] = df_t
        st.session_state["dimensions"] = df_a
        st.session_state["is_mock"] = False

st.markdown("***")

# --- NAVIGAZIONE ANALISI ---
st.markdown("## 📊 Explore your Portfolio")
st.markdown("Analyse your investments through these specialised sections:")

col_l_l, col_l_m0, col_l_m1, col_l_r = st.columns([1, 1, 1, 1], gap="large")

col_l_l.page_link(
    "pages/1_🎯_Asset_Allocation_&_PnL.py",
    label="Asset Allocation & PnL",
    icon="🎯",
    help="Portfolio composition, PnL by asset class, and wealth evolution over time.",
)
col_l_m0.page_link(
    "pages/2_📈_Return_Analysis.py",
    label="Return Analysis",
    icon="📈",
    help="Correlation maps, return distributions, and rolling performance.",
)
col_l_m1.page_link(
    "pages/3_⚠️_Risk_Analysis.py",
    label="Risk Analysis",
    icon="⚠️",
    help="Analysis of drawdowns and relative risk contributions of your assets.",
)
col_l_r.page_link(
    "pages/4_📝_Transactions_&_Assets.py",
    label="Transactions & Assets",
    icon="📝",
    help="Add, edit or delete your financial transactions and asset descriptions.",
)

st.markdown("<br>", unsafe_allow_html=True)

write_disclaimer()
