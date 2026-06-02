import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import apply_groww_style, PLOTLY_THEME, GROWW_GREEN, GROWW_RED, GROWW_PURPLE, GROWW_CARD, GROWW_BORDER, GROWW_MUTED
import plotly.graph_objects as go
import pandas as pd
from datetime import date

from backend.accounts import get_accounts, add_trade, close_trade, get_trade_summary
from backend.market_data import get_options_chain
from config import ACCOUNTS, LOT_SIZE, STRATEGY_LIST

st.set_page_config(page_title="Accounts", layout="wide")
apply_groww_style()
st.title("💼 Account Manager")

accounts = get_accounts()
account_names = {acc["id"]: acc["name"] for acc in ACCOUNTS}

tabs = st.tabs([acc["name"] for acc in ACCOUNTS] + ["📊 Portfolio Summary"])

# ── Per-account tabs ──────────────────────────────────────────────────────────
for i, acc_cfg in enumerate(ACCOUNTS):
    acc_id = acc_cfg["id"]
    with tabs[i]:
        summary = get_trade_summary(acc_id)
        trades  = accounts[acc_id]["trades"]

        # Summary metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Initial Capital",  f"₹{summary['initial_capital']:,.0f}")
        m2.metric("Realized P&L",     f"₹{summary['realized_pnl']:,.0f}",
                  delta=f"{summary['roi_pct']:+.2f}%")
        m3.metric("Open Positions",   summary["open_trades"])
        m4.metric("Win Rate",         f"{summary['win_rate']:.0f}%")
        m5.metric("Total Trades",     summary["total_trades"])

        st.divider()

        # Add trade form
        with st.expander("➕ Add New Trade"):
            chain = get_options_chain("NIFTY")
            expiry_dates = chain["expiry_dates"]

            fc1, fc2, fc3, fc4 = st.columns(4)
            strategy_new  = fc1.selectbox("Strategy",     STRATEGY_LIST, key=f"strat_{acc_id}")
            expiry_new    = fc2.selectbox("Expiry",       expiry_dates,  key=f"exp_{acc_id}")
            lots_new      = fc3.number_input("Lots",      1, 50, 1,      key=f"lots_{acc_id}")
            premium_new   = fc4.number_input("Net Premium/unit (+ for credit, - for debit)",
                                              -500.0, 500.0, 100.0, step=0.5,
                                              key=f"prem_{acc_id}")

            notes_new = st.text_input("Notes (strikes, IV, etc.)", key=f"notes_{acc_id}")

            if st.button("Add Trade", key=f"add_{acc_id}"):
                trade_id = add_trade(
                    account_id=acc_id,
                    strategy=strategy_new,
                    symbol="NIFTY",
                    expiry=expiry_new,
                    lots=lots_new,
                    legs=[],
                    premium_per_unit=premium_new,
                    notes=notes_new,
                )
                st.success(f"Trade added: ID `{trade_id}` | "
                           f"Total premium: ₹{premium_new * LOT_SIZE * lots_new:,.0f}")
                st.rerun()

        # Open trades
        open_trades = [t for t in trades if t["status"] == "open"]
        if open_trades:
            st.subheader("Open Positions")
            for trade in open_trades:
                with st.container():
                    tc1, tc2, tc3, tc4, tc5 = st.columns([2, 2, 1, 1, 2])
                    tc1.markdown(f"**{trade['strategy']}**  \n`{trade['id']}`")
                    tc2.markdown(f"Expiry: {trade['expiry']}  \nLots: {trade['lots']}")
                    tc3.markdown(f"Credit/unit  \n₹{trade['premium_per_unit']:.2f}")
                    tc4.markdown(f"Total  \n₹{trade['premium_total']:,.0f}")

                    close_prem = tc5.number_input(
                        "Close at (₹/unit)", 0.0, 1000.0, 0.0, step=0.5,
                        key=f"close_{trade['id']}"
                    )
                    if tc5.button("Close Trade", key=f"btn_{trade['id']}"):
                        close_trade(acc_id, trade["id"], close_prem)
                        pnl = (trade["premium_per_unit"] - close_prem) * LOT_SIZE * trade["lots"]
                        if pnl > 0:
                            st.success(f"Closed for PROFIT ₹{pnl:,.0f}")
                        else:
                            st.error(f"Closed for LOSS ₹{pnl:,.0f}")
                        st.rerun()

                    if trade["notes"]:
                        st.caption(trade["notes"])
                    st.markdown("---")
        else:
            st.info("No open positions.")

        # Closed trades
        closed_trades = [t for t in trades if t["status"] == "closed"]
        if closed_trades:
            st.subheader("Closed Trades")
            rows = []
            for t in closed_trades:
                rows.append({
                    "Date":     t["date"],
                    "Strategy": t["strategy"],
                    "Expiry":   t["expiry"],
                    "Lots":     t["lots"],
                    "Entry ₹":  t["premium_per_unit"],
                    "Exit ₹":   t["close_premium"],
                    "P&L ₹":    t["pnl"],
                    "Status":   "✅ Win" if (t["pnl"] or 0) > 0 else "❌ Loss",
                    "Notes":    t.get("notes", ""),
                })
            df = pd.DataFrame(rows)
            st.dataframe(
                df.style.map(
                    lambda v: "color:#00d4aa" if isinstance(v, (int, float)) and v > 0
                    else ("color:#ff4d4d" if isinstance(v, (int, float)) and v < 0 else ""),
                    subset=["P&L ₹"]
                ),
                use_container_width=True,
            )

            # P&L curve
            if len(rows) > 1:
                cumulative = pd.DataFrame(rows)[["Date", "P&L ₹"]].copy()
                cumulative["P&L ₹"]     = pd.to_numeric(cumulative["P&L ₹"], errors="coerce").fillna(0)
                cumulative["Cumulative"] = cumulative["P&L ₹"].cumsum()
                fig = go.Figure(go.Scatter(
                    x=cumulative["Date"], y=cumulative["Cumulative"],
                    fill="tozeroy",
                    fillcolor="rgba(0,212,170,0.1)",
                    line=dict(color="#00d4aa", width=2),
                ))
                fig.update_layout(
                    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
                    height=220, margin=dict(l=10, r=10, t=10, b=10),
                    xaxis_title="Date", yaxis_title="Cumulative P&L (₹)",
                    showlegend=False,
                )
                fig.update_xaxes(gridcolor="#2a2d3e")
                fig.update_yaxes(gridcolor="#2a2d3e")
                st.plotly_chart(fig, use_container_width=True)

# ── Portfolio summary tab ─────────────────────────────────────────────────────
with tabs[len(ACCOUNTS)]:
    st.subheader("Portfolio Summary — All Accounts")
    total_pnl  = 0
    total_cap  = 0
    for acc_cfg in ACCOUNTS:
        s = get_trade_summary(acc_cfg["id"])
        total_pnl += s["realized_pnl"]
        total_cap += s["initial_capital"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(acc_cfg["name"], f"₹{s['realized_pnl']:,.0f}", f"{s['roi_pct']:+.2f}%")
        col2.metric("Win Rate",  f"{s['win_rate']:.0f}%")
        col3.metric("Open",      s["open_trades"])
        col4.metric("Closed",    s["closed_trades"])
        st.markdown("---")

    st.metric("Combined P&L", f"₹{total_pnl:,.0f}",
              delta=f"{total_pnl / total_cap * 100:+.2f}% on ₹{total_cap:,.0f} combined capital")

    # Target tracker
    target_annual = total_cap * 0.18
    st.progress(
        min(max(total_pnl / target_annual, 0), 1.0),
        text=f"Progress to 18% annual target: ₹{total_pnl:,.0f} / ₹{target_annual:,.0f}"
    )
