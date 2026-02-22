import streamlit as st
import os
import json
import uuid
import pandas as pd
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Trading Control Center", layout="wide")

ADMIN_PASSWORD = "admin123"

TRADE_FILE = "trades.json"
PLAN_FILE = "planned_stocks.json"

# ======================================================
# FILE HANDLING
# ======================================================
def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

trades = load_data(TRADE_FILE)
planned = load_data(PLAN_FILE)

# ======================================================
# SIDEBAR MENU
# ======================================================
menu = st.sidebar.radio(
    "Navigation",
    ["📓 Trade Log", "📅 Tomorrow Plan", "🔐 Admin Panel"]
)

# ======================================================
# TRADE LOG VIEW
# ======================================================
if menu == "📓 Trade Log":

    st.title("📓 Trade Log Book")

    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No trades recorded yet.")

# ======================================================
# TOMORROW PLAN VIEW
# ======================================================
if menu == "📅 Tomorrow Plan":

    st.title("📅 Tomorrow Planned Stocks")

    if planned:
        df = pd.DataFrame(planned)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No planned stocks saved.")

# ======================================================
# ADMIN PANEL
# ======================================================
if menu == "🔐 Admin Panel":

    password = st.text_input("Enter Admin Password", type="password")

    if password == ADMIN_PASSWORD:

        st.success("Admin Access Granted ✅")

        tab1, tab2 = st.tabs(["➕ Add Trade Log", "📅 Add Tomorrow Plan"])

        # ==================================================
        # ADD TRADE LOG
        # ==================================================
        with tab1:

            st.subheader("Add Trade Entry")

            symbol = st.text_input("Stock Symbol")
            direction = st.selectbox("Direction", ["BUY", "SELL"])
            entry = st.number_input("Entry Price")
            exit_price = st.number_input("Exit Price")
            qty = st.number_input("Quantity", step=1)
            setup = st.text_input("Setup Type (Breakout / Pullback etc)")
            emotion = st.text_input("Trader Emotion")
            notes = st.text_area("Notes")

            if st.button("Save Trade"):

                pnl = (exit_price - entry) * qty if direction == "BUY" else (entry - exit_price) * qty

                new_trade = {
                    "id": str(uuid.uuid4()),
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Symbol": symbol,
                    "Direction": direction,
                    "Entry": entry,
                    "Exit": exit_price,
                    "Qty": qty,
                    "PnL": pnl,
                    "Setup": setup,
                    "Emotion": emotion,
                    "Notes": notes
                }

                trades.append(new_trade)
                save_data(TRADE_FILE, trades)

                st.success("Trade Saved Successfully 🎯")

        # ==================================================
        # ADD TOMORROW PLAN
        # ==================================================
        with tab2:

            st.subheader("Add Tomorrow Planned Stock")

            psymbol = st.text_input("Stock Symbol", key="psymbol")
            timeframe = st.selectbox("Timeframe", ["15m", "1H", "Daily"])
            plan_type = st.selectbox("Plan Type", ["Breakout", "Pullback", "Reversal"])
            entry_zone = st.text_input("Entry Zone")
            target = st.text_input("Target")
            stoploss = st.text_input("Stoploss")
            confluence = st.text_area("Confluence Factors")

            if st.button("Save Plan"):

                new_plan = {
                    "id": str(uuid.uuid4()),
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Symbol": psymbol,
                    "Timeframe": timeframe,
                    "PlanType": plan_type,
                    "EntryZone": entry_zone,
                    "Target": target,
                    "Stoploss": stoploss,
                    "Confluence": confluence
                }

                planned.append(new_plan)
                save_data(PLAN_FILE, planned)

                st.success("Tomorrow Plan Saved 🚀")

    else:
        st.warning("Enter correct password")
