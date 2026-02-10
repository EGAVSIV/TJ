import os
import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# ------------- CONFIG -------------
st.set_page_config(page_title="Trading Journal", layout="wide")
st.title("📒 Trading Journal – Discipline Dashboard")

JOURNAL_FILE = "trading_journal.csv"


# ------------- HELPERS -------------

def load_journal() -> pd.DataFrame:
    if not os.path.exists(JOURNAL_FILE):
        cols = [
            "date", "time", "symbol", "side",
            "qty", "entry", "exit",
            "sl", "tp",
            "fees",
            "rr_planned", "rr_realized",
            "pnl", "pnl_pct",
            "setup", "tag_1", "tag_2",
            "emotion_before", "emotion_after",
            "screenshot", "notes",
        ]
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(JOURNAL_FILE)
    # type fixes
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def save_journal(df: pd.DataFrame):
    df.to_csv(JOURNAL_FILE, index=False)


def calc_stats(df: pd.DataFrame):
    if df.empty:
        return {}
    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] < 0]
    total = len(df)
    eq = df["pnl"].cumsum()
    max_dd = 0.0
    peak = 0.0
    for v in eq:
        peak = max(peak, v)
        dd = (v - peak)
        max_dd = min(max_dd, dd)
    stats = {
        "total_trades": total,
        "win_rate": round(len(wins) / total * 100, 1) if total else 0,
        "avg_rr": round(df["rr_realized"].replace([np.inf, -np.inf], np.nan).mean(), 2)
        if "rr_realized" in df.columns and not df["rr_realized"].empty
        else 0,
        "avg_pnl": round(df["pnl"].mean(), 2),
        "total_pnl": round(df["pnl"].sum(), 2),
        "max_drawdown": round(max_dd, 2),
    }
    return stats


# ------------- LOAD DATA -------------
df = load_journal()

# ------------- LAYOUT -------------
tab_journal, tab_dashboard = st.tabs(["✍️ New Trade", "📊 Dashboard"])

# ------------- NEW TRADE TAB -------------
with tab_journal:
    st.subheader("Log New Trade")

    col1, col2, col3 = st.columns(3)
    with col1:
        date = st.date_input("Date", dt.date.today())
        time = st.time_input("Time", dt.datetime.now().time())
        symbol = st.text_input("Symbol", "NSE:RELIANCE")
    with col2:
        side = st.selectbox("Side", ["LONG", "SHORT"])
        qty = st.number_input("Quantity", min_value=1, step=1, value=1)
        entry = st.number_input("Entry Price", min_value=0.0, step=0.05, value=0.0)
    with col3:
        exit_price = st.number_input("Exit Price", min_value=0.0, step=0.05, value=0.0)
        sl = st.number_input("Stop Loss", min_value=0.0, step=0.05, value=0.0)
        tp = st.number_input("Target Price", min_value=0.0, step=0.05, value=0.0)

    col4, col5, col6 = st.columns(3)
    with col4:
        fees = st.number_input("Fees / Charges", min_value=0.0, step=1.0, value=0.0)
    with col5:
        setup = st.text_input("Setup (pattern/strategy)", "Breakout")
        tag_1 = st.text_input("Tag 1", "Index")
        tag_2 = st.text_input("Tag 2", "Intraday")
    with col6:
        emotion_before = st.selectbox(
            "Emotion Before",
            ["Calm", "Fear", "Greed", "Revenge", "FOMO", "Tilt"],
            index=0,
        )
        emotion_after = st.selectbox(
            "Emotion After",
            ["Happy", "Neutral", "Regret", "Angry", "Overconfident"],
            index=1,
        )

    screenshot = st.text_input("Screenshot URL (optional)")
    notes = st.text_area("Notes / Reason (Entry + Exit)")

    # Compute P&L and R:R
    rr_planned = None
    if sl and tp and entry:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_planned = reward / risk if risk > 0 else None

    pnl = None
    pnl_pct = None
    rr_realized = None
    if entry and exit_price:
        direction = 1 if side == "LONG" else -1
        pnl = (exit_price - entry) * direction * qty - fees
        pnl_pct = (exit_price - entry) * direction / entry * 100 if entry > 0 else None
        if sl and entry:
            risk = abs(entry - sl) * qty
            rr_realized = pnl / risk if risk > 0 else None

    st.markdown("---")
    st.write("**Preview:**")
    st.write(f"P&L: {round(pnl,2) if pnl is not None else '-'}")
    st.write(f"Return %: {round(pnl_pct,2) if pnl_pct is not None else '-'}")
    st.write(f"Planned R:R: {round(rr_planned,2) if rr_planned is not None else '-'}")
    st.write(f"Realized R:R: {round(rr_realized,2) if rr_realized is not None else '-'}")

    if st.button("✅ Save Trade"):
        new_row = {
            "date": date,
            "time": time.strftime("%H:%M:%S"),
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "entry": entry,
            "exit": exit_price,
            "sl": sl,
            "tp": tp,
            "fees": fees,
            "rr_planned": rr_planned,
            "rr_realized": rr_realized,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "setup": setup,
            "tag_1": tag_1,
            "tag_2": tag_2,
            "emotion_before": emotion_before,
            "emotion_after": emotion_after,
            "screenshot": screenshot,
            "notes": notes,
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_journal(df)
        st.success("Trade saved to journal.")
        st.experimental_rerun()

# ------------- DASHBOARD TAB -------------
with tab_dashboard:
    st.subheader("Performance Dashboard")

    if df.empty:
        st.info("No trades yet. Log your first trade in the 'New Trade' tab.")
    else:
        # Date filter
        df["date"] = pd.to_datetime(df["date"]).dt.date
        min_d, max_d = df["date"].min(), df["date"].max()
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            date_range = st.date_input(
                "Date range",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d,
            )
        with col_f2:
            sym_filter = st.multiselect(
                "Symbol filter", sorted(df["symbol"].unique()), []
            )
        with col_f3:
            side_filter = st.multiselect(
                "Side filter", ["LONG", "SHORT"], []
            )

        df_f = df.copy()
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_d, end_d = date_range
            df_f = df_f[(df_f["date"] >= start_d) & (df_f["date"] <= end_d)]
        if sym_filter:
            df_f = df_f[df_f["symbol"].isin(sym_filter)]
        if side_filter:
            df_f = df_f[df_f["side"].isin(side_filter)]

        stats = calc_stats(df_f)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total P&L", stats.get("total_pnl", 0))
        c2.metric("Win Rate %", stats.get("win_rate", 0))
        c3.metric("Avg R:R", stats.get("avg_rr", 0))
        c4.metric("Max Drawdown", stats.get("max_drawdown", 0))

        # Equity curve
        df_f = df_f.sort_values(["date", "time"])
        df_f["cum_pnl"] = df_f["pnl"].cumsum()

        fig_eq = px.line(
            df_f,
            x="date",
            y="cum_pnl",
            title="Equity Curve",
        )
        st.plotly_chart(fig_eq, use_container_width=True)

        # PnL by symbol
        pnl_by_sym = df_f.groupby("symbol")["pnl"].sum().reset_index()
        fig_sym = px.bar(
            pnl_by_sym,
            x="symbol",
            y="pnl",
            title="P&L by Symbol",
            color="pnl",
            color_continuous_scale="RdYlGn",
        )
        st.plotly_chart(fig_sym, use_container_width=True)

        st.subheader("Journal Table")
        st.dataframe(df_f.sort_values(["date", "time"], ascending=[False, False]),
                     use_container_width=True)
