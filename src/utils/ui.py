import streamlit as st
import pandas as pd
import numpy as np

from database.auth import login_user, register_user
from database.fetch import load_data


def write_disclaimer() -> None:
    st.markdown("***")
    st.markdown(
        '<center> <span style="font-size:0.7em; font-style:italic">\
        This content is for educational purposes only and is under no circumstances intended\
        to be used or considered as financial or investment advice\
        </span> </center>',
        unsafe_allow_html=True,
    )


def write_load_message(df_data: pd.DataFrame, df_dimensions: pd.DataFrame) -> None:
    n_transactions = df_data.shape[0]
    n_tickers = df_data["ticker"].nunique()
    min_date, max_date = (
        str(df_data["transaction_date"].min())[:10],
        str(df_data["transaction_date"].max())[:10],
    )
    set_data_tickers = sorted(df_data["ticker"].unique())
    set_dimensions_tickers = sorted(df_dimensions["ticker"].unique())
    n_data_na = df_data.isnull().sum().sum()
    n_dimensions_na = df_dimensions.isnull().sum().sum()

    if n_data_na > 0 or n_dimensions_na > 0:
        st.error(
            f"There are null values: {n_data_na} among transactions, {n_dimensions_na} among tickers' descriptions"
        )
        st.stop()

    if set_data_tickers != set_dimensions_tickers:
        st.warning(
            "There is some inconsistency between the tickers traded and the tickers' descriptions"
        )

    st.success(
        f"Successfully loaded **{n_transactions} transactions** relating to **{n_tickers} tickers** and spanning from {min_date} to {max_date}"
    )


def login_or_register() -> None:
    st.markdown("## Who wants to access PFN?")
    st.sidebar.write("Login or register:")
    login_sidebar = st.sidebar.selectbox(
        " ", ["Login", "Register"], label_visibility="collapsed"
    )

    if login_sidebar == "Register":
        with st.form("register_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Register")
        if submit:
            if register_user(username, password):
                st.success("Registration successful: you can now log in!", icon="✅")
            else:
                st.error("Sorry, username already taken")

    elif login_sidebar == "Login":
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
        if submit:
            if login_user(username, password):
                st.session_state["user"] = username
                st.rerun()
            else:
                st.error("Sorry, invalid credentials")
    st.stop()


def check_session_sidebar():
    if "user" in st.session_state:
        st.sidebar.write(
            f"Logged in as: **{st.session_state['user']}**", unsafe_allow_html=True
        )
        if st.sidebar.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        login_or_register()
        st.stop()


def ensure_data_is_loaded():
    if "data" not in st.session_state:
        user = st.session_state.get("user")
        if user:
            df_t, df_a = load_data(user, is_mock=False)
            st.session_state["data"] = df_t
            st.session_state["dimensions"] = df_a
            st.session_state["is_mock"] = False


def display_rebalance_simulation(
    df_res: pd.DataFrame,
    out_df: pd.DataFrame,
    level_col: str,
    level_ui: str,
    broker_fee: float,
    max_cash: float = None,
    key: str = "",
):
    st.markdown(
        "💡 *Tip: Uncheck the **Execute** box to ignore a trade you don't want to make, or manually override the **Amount to Trade (€)**.*"
    )

    col_config = {
        "Execute": st.column_config.CheckboxColumn("Execute?", default=True),
        level_ui: st.column_config.TextColumn(level_ui, disabled=True),
        "Asset Class": st.column_config.TextColumn("Asset Class", disabled=True),
        "Action": st.column_config.TextColumn("Action", disabled=True),
        "Current Value (€)": st.column_config.NumberColumn(
            "Current Value", format="%.1f €", disabled=True
        ),
        "Target Value (€)": st.column_config.NumberColumn(
            "Target Value", format="%.1f €", disabled=True
        ),
        "Amount to Trade (€)": st.column_config.NumberColumn(
            "Amount to Trade", format="%.1f €", disabled=False
        ),
        "Difference in Weight (%)": st.column_config.NumberColumn(
            "Difference in Weight",
            format="%+.1f %%",
            disabled=True,
            help="Difference between target and current weight (%)",
        ),
    }
    if "Shares to Trade (Approx.)" in out_df.columns:
        col_config["Shares to Trade (Approx.)"] = st.column_config.NumberColumn(
            "Shares to Trade (Approx.)", format="%.1f", disabled=True
        )

    edited_actions = st.data_editor(
        out_df,
        column_config=col_config,
        hide_index=True,
        use_container_width=True,
        key=key,
    )

    executed_trades = edited_actions[edited_actions["Execute"]]
    cash_needed = executed_trades["Amount to Trade (€)"].sum()
    trades_count = len(
        executed_trades[executed_trades["Amount to Trade (€)"].abs() > 0]
    )

    col1, col2 = st.columns(2)
    col1.metric(
        "Net Cash Required",
        f"€ {cash_needed:,.1f}",
        help="Positive means you need to deposit cash. Negative means you are freeing up cash.",
    )
    col2.metric("Estimated Fees", f"€ {trades_count * broker_fee:,.1f}")

    if max_cash is not None and cash_needed > max_cash + 0.5:
        st.warning(
            f"⚠️ Warning: the trades you selected require **€ {cash_needed:,.1f}**, which is more than the **€ {max_cash:,.1f}** you declared to inject."
        )

    st.markdown("### Simulation after rebalancing")
    df_sim = df_res.copy()

    df_sim = df_sim.merge(
        edited_actions[[level_ui, "Execute", "Amount to Trade (€)"]],
        left_on=level_col,
        right_on=level_ui,
        how="left",
    )

    df_sim["sim_delta"] = np.where(
        df_sim["Execute"].eq(True), df_sim["Amount to Trade (€)"], 0
    )
    df_sim["sim_final_value"] = df_sim["current_value"] + df_sim["sim_delta"]

    sim_total_value = df_sim["sim_final_value"].sum()
    df_sim["sim_weight"] = (df_sim["sim_final_value"] / sim_total_value) * 100
    df_sim["target_weight_perc"] = df_sim["target_weight"] * 100
    df_sim["deviation"] = df_sim["sim_weight"] - df_sim["target_weight_perc"]

    cols_to_display = [level_col, "target_weight_perc", "sim_weight", "deviation"]
    rename_cols = {
        level_col: level_ui,
        "target_weight_perc": "Target Weight (%)",
        "sim_weight": "Simulated Weight (%)",
        "deviation": "Deviation (%)",
    }

    if level_ui == "Tickers":
        cols_to_display.insert(1, "asset_class")
        rename_cols["asset_class"] = "Asset Class"

    st.dataframe(
        df_sim[cols_to_display]
        .rename(columns=rename_cols)
        .style.format(
            {
                "Target Weight (%)": "{:.1f}%",
                "Simulated Weight (%)": "{:.1f}%",
                "Deviation (%)": "{:+.1f}%",
            }
        )
        .map(
            lambda x: "color: #ff4b4b" if abs(x) > 1 else "color: #09ab3b",
            subset=["Deviation (%)"],
        ),
        hide_index=True,
        use_container_width=True,
    )
