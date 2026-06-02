import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from backend.market_data import get_options_chain, get_nifty_spot, time_to_expiry_days
from backend.technical import pcr, pcr_volume, max_pain, oi_buildup_signal, support_resistance_from_oi
from backend.greeks import calculate_greeks
from config import RISK_FREE_RATE, LOT_SIZE

st.set_page_config(page_title="Options Chain", layout="wide")
st.title("🔗 Options Chain — Nifty 50")

# ── Controls ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 1])
symbol = col1.selectbox("Index", ["NIFTY", "BANKNIFTY", "MIDCPNIFTY"], index=0)
data   = get_options_chain(symbol)
expiry_dates = data["expiry_dates"]

if not expiry_dates:
    st.error("Could not load options chain. NSE API may be down — try refreshing.")
    st.stop()

expiry   = col2.selectbox("Expiry", expiry_dates)
strikes  = col3.number_input("Strikes around ATM", 10, 30, 15, step=5)

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

data   = get_options_chain(symbol, expiry)
df     = data["df"]
spot   = data["underlying"] or get_nifty_spot()["price"]
ts     = data["timestamp"]
dte    = time_to_expiry_days()

st.caption(f"Underlying: **{spot:,.2f}** | Data as of: {ts}")

# ── Enrich with Greeks ────────────────────────────────────────────────────────
T = max(dte / 365, 1 / 365)

def add_greeks(df):
    for side in ("CE", "PE"):
        opt  = side
        deltas, gammas, thetas, vegas = [], [], [], []
        for _, row in df.iterrows():
            iv = row[f"{side}_IV"] / 100 if row[f"{side}_IV"] > 0 else 0.15
            g  = calculate_greeks(spot, row["strikePrice"], T, RISK_FREE_RATE, iv, opt)
            deltas.append(round(g["delta"], 3))
            gammas.append(round(g["gamma"], 5))
            thetas.append(round(g["theta"], 2))
            vegas.append(round(g["vega"], 2))
        df[f"{side}_Delta"] = deltas
        df[f"{side}_Gamma"] = gammas
        df[f"{side}_Theta"] = thetas
        df[f"{side}_Vega"]  = vegas
    return df

if not df.empty:
    df = add_greeks(df)

# ── ATM filter ────────────────────────────────────────────────────────────────
if not df.empty:
    all_strikes = df["strikePrice"].tolist()
    atm = min(all_strikes, key=lambda k: abs(k - spot))
    atm_idx = all_strikes.index(atm)
    lo_idx  = max(0, atm_idx - strikes)
    hi_idx  = min(len(all_strikes) - 1, atm_idx + strikes)
    filtered = df[(df["strikePrice"] >= all_strikes[lo_idx]) &
                  (df["strikePrice"] <= all_strikes[hi_idx])].copy()
else:
    filtered = df.copy()

# ── OI metrics ────────────────────────────────────────────────────────────────
pcr_oi  = pcr(df)
pcr_vol = pcr_volume(df)
mp      = max_pain(df) if not df.empty else 0
buildup = oi_buildup_signal(df, spot)
sr      = support_resistance_from_oi(df, spot)

m1, m2, m3, m4 = st.columns(4)
m1.metric("PCR (OI)",     f"{pcr_oi:.2f}",  help="Put-Call Ratio by Open Interest")
m2.metric("PCR (Volume)", f"{pcr_vol:.2f}", help="Put-Call Ratio by traded volume")
m3.metric("Max Pain",     f"{mp:,.0f}",     help="Strike where most option buyers lose")
m4.metric("DTE",          f"{dte:.1f} days")

# ── Support / Resistance ──────────────────────────────────────────────────────
if sr["resistance"] or sr["support"]:
    st.markdown(
        f"**OI Resistance:** {' | '.join([f'{r:,.0f}' for r in sr['resistance']])}  &nbsp;&nbsp; "
        f"**OI Support:** {' | '.join([f'{s:,.0f}' for s in sr['support']])}"
    )

# ── OI heatmap bar chart ──────────────────────────────────────────────────────
st.subheader("Open Interest Distribution")
if not df.empty:
    fig_oi = go.Figure()
    fig_oi.add_trace(go.Bar(
        x=df["strikePrice"], y=df["CE_OI"],
        name="Call OI", marker_color="#ff4d4d", opacity=0.8,
    ))
    fig_oi.add_trace(go.Bar(
        x=df["strikePrice"], y=df["PE_OI"],
        name="Put OI", marker_color="#00d4aa", opacity=0.8,
    ))
    fig_oi.add_vline(x=spot, line_dash="dash", line_color="#ffd700",
                     annotation_text=f"Spot {spot:,.0f}", annotation_position="top")
    if mp:
        fig_oi.add_vline(x=mp, line_dash="dot", line_color="#888",
                         annotation_text=f"Max Pain {mp:,.0f}", annotation_position="bottom right")
    fig_oi.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
        height=300, barmode="group", margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(bgcolor="#1a1d2e"),
        xaxis_title="Strike", yaxis_title="Open Interest (contracts)",
    )
    fig_oi.update_xaxes(gridcolor="#2a2d3e")
    fig_oi.update_yaxes(gridcolor="#2a2d3e")
    st.plotly_chart(fig_oi, use_container_width=True)

# ── Options chain table ───────────────────────────────────────────────────────
st.subheader("Options Chain")

if not filtered.empty:
    display_cols = {
        "CE_OI":    "CE OI",
        "CE_chngOI": "CE ΔOI",
        "CE_volume": "CE Vol",
        "CE_IV":    "CE IV%",
        "CE_LTP":   "CE LTP",
        "CE_Delta": "CE Δ",
        "CE_Theta": "CE Θ",
        "CE_Vega":  "CE Vega",
        "strikePrice": "STRIKE",
        "PE_Delta": "PE Δ",
        "PE_Theta": "PE Θ",
        "PE_Vega":  "PE Vega",
        "PE_LTP":   "PE LTP",
        "PE_IV":    "PE IV%",
        "PE_volume": "PE Vol",
        "PE_chngOI": "PE ΔOI",
        "PE_OI":    "PE OI",
    }
    show = filtered[[c for c in display_cols if c in filtered.columns]].rename(columns=display_cols)

    def _highlight(row):
        strike = row["STRIKE"]
        styles = []
        for col in row.index:
            if col == "STRIKE":
                if abs(strike - spot) < 51:
                    styles.append("background-color:#2a2d1a;font-weight:bold;color:#ffd700")
                else:
                    styles.append("color:#fff;font-weight:bold")
            elif col.startswith("CE"):
                styles.append("background-color:#1a1520;color:#ffaaaa")
            elif col.startswith("PE"):
                styles.append("background-color:#0e1a15;color:#aaffcc")
            else:
                styles.append("")
        return styles

    styled = show.style.apply(_highlight, axis=1).format({
        "CE OI": "{:,.0f}", "PE OI": "{:,.0f}",
        "CE Vol": "{:,.0f}", "PE Vol": "{:,.0f}",
        "CE ΔOI": "{:+,.0f}", "PE ΔOI": "{:+,.0f}",
        "STRIKE": "{:,.0f}",
        "CE LTP": "{:.2f}", "PE LTP": "{:.2f}",
        "CE IV%": "{:.1f}", "PE IV%": "{:.1f}",
        "CE Δ": "{:.3f}", "PE Δ": "{:.3f}",
        "CE Θ": "{:.2f}", "PE Θ": "{:.2f}",
        "CE Vega": "{:.2f}", "PE Vega": "{:.2f}",
    })
    st.dataframe(styled, use_container_width=True, height=500)
else:
    st.info("No options chain data available for selected expiry.")

# ── OI buildup legend ─────────────────────────────────────────────────────────
with st.expander("OI Buildup Signals"):
    st.markdown(
        f"**Calls near ATM:** `{buildup['calls']}`  \n"
        f"**Puts near ATM:** `{buildup['puts']}`  \n\n"
        "| Signal | Price | OI | Interpretation |\n"
        "|---|---|---|---|\n"
        "| Long Buildup | ↑ | ↑ | Fresh buying |\n"
        "| Short Buildup | ↓ | ↑ | Fresh selling |\n"
        "| Long Unwinding | ↓ | ↓ | Longs exiting |\n"
        "| Short Covering | ↑ | ↓ | Shorts covering |\n"
    )
