import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

from backend.market_data import (
    get_nifty_spot, get_india_vix, get_bank_nifty, get_sensex,
    get_nifty_history, get_options_chain, next_weekly_expiry,
    time_to_expiry_days, is_market_open,
)
from backend.technical import pcr, rsi, interpret_signals

st.set_page_config(
    page_title="Nifty Options Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

IST = pytz.timezone("Asia/Kolkata")

# ── Header ────────────────────────────────────────────────────────────────────
now_ist = datetime.now(IST)
mkt_status = "🟢 MARKET OPEN" if is_market_open() else "🔴 MARKET CLOSED"
expiry = next_weekly_expiry()
dte    = time_to_expiry_days()

st.markdown(
    f"<h1 style='margin-bottom:0'>📈 Nifty Options Terminal</h1>"
    f"<p style='color:#888;margin-top:4px'>{now_ist.strftime('%A, %d %b %Y  %H:%M:%S IST')} &nbsp;|&nbsp; "
    f"{mkt_status} &nbsp;|&nbsp; Next Expiry: {expiry.strftime('%d %b')} "
    f"({dte:.1f} days)</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── Market metrics ────────────────────────────────────────────────────────────
nifty   = get_nifty_spot()
vix     = get_india_vix()
bnifty  = get_bank_nifty()
sensex  = get_sensex()

c1, c2, c3, c4 = st.columns(4)

def _metric(col, label, price, chng, chng_pct, fmt="{:,.2f}"):
    arrow = "▲" if chng >= 0 else "▼"
    color = "#00d4aa" if chng >= 0 else "#ff4d4d"
    col.markdown(
        f"<div style='background:#1a1d2e;padding:16px;border-radius:8px;border-left:3px solid {color}'>"
        f"<div style='color:#888;font-size:12px;text-transform:uppercase'>{label}</div>"
        f"<div style='font-size:26px;font-weight:700;color:#fff'>{fmt.format(price)}</div>"
        f"<div style='color:{color};font-size:13px'>{arrow} {abs(chng):,.2f} ({chng_pct:+.2f}%)</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

_metric(c1, "Nifty 50",   nifty["price"],  nifty["change"],  nifty["change_pct"])
_metric(c2, "India VIX",  vix["price"],    vix["change"],    vix["change_pct"], "{:.2f}")
_metric(c3, "Bank Nifty", bnifty["price"], bnifty["change"], bnifty["change_pct"])
_metric(c4, "Sensex",     sensex["price"], sensex["change"], sensex["change_pct"])

st.markdown("<br>", unsafe_allow_html=True)

# ── PCR + RSI quick view ──────────────────────────────────────────────────────
chain_data = get_options_chain("NIFTY")
df_chain   = chain_data["df"]
pcr_val    = pcr(df_chain) if not df_chain.empty else 1.0

history = get_nifty_history("1mo", "1d")
rsi_val = 50.0
if not history.empty and "Close" in history.columns:
    rsi_series = rsi(history["Close"])
    rsi_val    = float(rsi_series.iloc[-1])

s1, s2, s3 = st.columns(3)

def _signal_card(col, label, value, low, mid_lo, mid_hi, high, unit="", fmt="{:.2f}"):
    if value < mid_lo:
        color, mood = "#ff4d4d", "Bearish"
    elif value > mid_hi:
        color, mood = "#00d4aa", "Bullish"
    else:
        color, mood = "#ffd700", "Neutral"
    col.markdown(
        f"<div style='background:#1a1d2e;padding:14px;border-radius:8px;text-align:center'>"
        f"<div style='color:#888;font-size:12px'>{label}</div>"
        f"<div style='font-size:28px;font-weight:700;color:{color}'>{fmt.format(value)}{unit}</div>"
        f"<div style='color:{color};font-size:12px'>{mood}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

_signal_card(s1, "PCR (OI)",  pcr_val,    0, 0.7, 1.3, 2, fmt="{:.2f}")
_signal_card(s2, "RSI (14d)", rsi_val,    0, 40,  60, 100, fmt="{:.1f}")
_signal_card(s3, "VIX Level", vix["price"], 0, 14, 20, 40, fmt="{:.1f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Nifty 50 chart ────────────────────────────────────────────────────────────
st.subheader("Nifty 50 — 3 Month Chart")
hist3m = get_nifty_history("3mo", "1d")

if not hist3m.empty:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.04,
    )
    fig.add_trace(go.Candlestick(
        x=hist3m.index,
        open=hist3m["Open"], high=hist3m["High"],
        low=hist3m["Low"],   close=hist3m["Close"],
        name="Nifty 50",
        increasing_line_color="#00d4aa",
        decreasing_line_color="#ff4d4d",
    ), row=1, col=1)

    rsi_s = rsi(hist3m["Close"]) if "Close" in hist3m.columns else None
    if rsi_s is not None:
        fig.add_trace(go.Scatter(
            x=hist3m.index, y=rsi_s,
            name="RSI(14)", line=dict(color="#ffd700", width=1.5),
        ), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ff4d4d", opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00d4aa", opacity=0.5, row=2, col=1)

    fig.update_layout(
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="#e0e0e0",
        height=500,
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig.update_xaxes(gridcolor="#2a2d3e")
    fig.update_yaxes(gridcolor="#2a2d3e")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Historical data unavailable.")

# ── Market signal summary ─────────────────────────────────────────────────────
st.subheader("Signal Summary")
summary = interpret_signals(rsi_val, pcr_val, vix["price"])
for part in summary.split(" | "):
    icon = "🟡"
    if "overbought" in part or "low — premium" in part:
        icon = "🔴"
    elif "oversold" in part or "elevated" in part:
        icon = "🟢"
    st.markdown(f"**{icon} {part}**")

st.markdown(
    "<br><div style='color:#555;font-size:11px'>"
    "Data: NSE India (options), Yahoo Finance (spot). "
    "For educational and personal use only. Not SEBI-registered advice.</div>",
    unsafe_allow_html=True,
)
