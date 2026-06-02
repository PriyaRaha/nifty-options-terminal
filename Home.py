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
from styles import (
    apply_groww_style, groww_metric, groww_signal_card,
    PLOTLY_THEME, GROWW_GREEN, GROWW_RED, GROWW_PURPLE,
    GROWW_CARD, GROWW_BORDER, GROWW_MUTED, GROWW_YELLOW,
)

st.set_page_config(
    page_title="Nifty Options Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_groww_style()

IST = pytz.timezone("Asia/Kolkata")
now_ist    = datetime.now(IST)
mkt_status = "🟢 OPEN" if is_market_open() else "🔴 CLOSED"
expiry     = next_weekly_expiry()
dte        = time_to_expiry_days()

# ── Header bar ───────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='display:flex;align-items:center;justify-content:space-between;"
    f"padding:12px 0 20px 0;border-bottom:1px solid {GROWW_BORDER};margin-bottom:24px'>"
    f"<div>"
    f"<span style='font-size:22px;font-weight:700;color:#fff'>📈 Nifty Options Terminal</span>"
    f"</div>"
    f"<div style='text-align:right'>"
    f"<div style='font-size:12px;color:{GROWW_MUTED}'>"
    f"{now_ist.strftime('%a, %d %b %Y  %H:%M IST')}</div>"
    f"<div style='font-size:12px;margin-top:2px'>"
    f"{mkt_status} &nbsp;|&nbsp; "
    f"<span style='color:{GROWW_PURPLE}'>Expiry {expiry.strftime('%d %b')} "
    f"({dte:.1f}d)</span></div>"
    f"</div>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Market metrics ────────────────────────────────────────────────────────────
nifty  = get_nifty_spot()
vix    = get_india_vix()
bnifty = get_bank_nifty()
sensex = get_sensex()

c1, c2, c3, c4 = st.columns(4)
groww_metric(c1, "Nifty 50",   nifty["price"],  nifty["change"],  nifty["change_pct"])
groww_metric(c2, "India VIX",  vix["price"],    vix["change"],    vix["change_pct"],   fmt="{:.2f}")
groww_metric(c3, "Bank Nifty", bnifty["price"], bnifty["change"], bnifty["change_pct"])
groww_metric(c4, "Sensex",     sensex["price"], sensex["change"], sensex["change_pct"])

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Signal cards ─────────────────────────────────────────────────────────────
chain_data = get_options_chain("NIFTY")
df_chain   = chain_data["df"]
pcr_val    = pcr(df_chain) if not df_chain.empty else 1.0

history = get_nifty_history("1mo", "1d")
rsi_val = 50.0
if not history.empty and "Close" in history.columns:
    rsi_val = float(rsi(history["Close"]).iloc[-1])

s1, s2, s3 = st.columns(3)

pcr_status = "Bullish" if pcr_val > 1.3 else ("Bearish" if pcr_val < 0.7 else "Neutral")
rsi_status = "Bearish" if rsi_val > 70  else ("Bullish" if rsi_val < 30 else "Neutral")
vix_status = "High"    if vix["price"] > 20 else ("Low" if vix["price"] < 13 else "Normal")

groww_signal_card(s1, "PCR (OI)",   pcr_val,       pcr_status, fmt="{:.2f}")
groww_signal_card(s2, "RSI (14d)",  rsi_val,       rsi_status, fmt="{:.1f}")
groww_signal_card(s3, "VIX Level",  vix["price"],  vix_status, fmt="{:.1f}")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Nifty chart ───────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='font-size:16px;font-weight:600;margin-bottom:12px;color:#fff'>"
    f"Nifty 50 — 3 Month</div>",
    unsafe_allow_html=True,
)

hist3m = get_nifty_history("3mo", "1d")
if not hist3m.empty:
    rsi_series = rsi(hist3m["Close"]) if "Close" in hist3m.columns else None
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.75, 0.25], vertical_spacing=0.04,
    )
    fig.add_trace(go.Candlestick(
        x=hist3m.index,
        open=hist3m["Open"], high=hist3m["High"],
        low=hist3m["Low"],   close=hist3m["Close"],
        name="Nifty 50",
        increasing_line_color=GROWW_GREEN,
        decreasing_line_color=GROWW_RED,
        increasing_fillcolor=GROWW_GREEN,
        decreasing_fillcolor=GROWW_RED,
    ), row=1, col=1)

    if rsi_series is not None:
        fig.add_trace(go.Scatter(
            x=hist3m.index, y=rsi_series,
            line=dict(color=GROWW_PURPLE, width=1.8),
            name="RSI(14)",
        ), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color=GROWW_RED,   opacity=0.4, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color=GROWW_GREEN, opacity=0.4, row=2, col=1)

    fig.update_layout(
        **PLOTLY_THEME,
        height=480,
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Signal summary ────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='font-size:16px;font-weight:600;margin-bottom:12px;color:#fff'>"
    f"Signal Summary</div>",
    unsafe_allow_html=True,
)
summary = interpret_signals(rsi_val, pcr_val, vix["price"])
for part in summary.split(" | "):
    icon  = "🟡"
    color = GROWW_YELLOW
    if any(w in part for w in ["overbought", "low — premium"]):
        icon, color = "🔴", GROWW_RED
    elif any(w in part for w in ["oversold", "elevated"]):
        icon, color = "🟢", GROWW_GREEN
    st.markdown(
        f"<div style='background:{GROWW_CARD};border:1px solid {GROWW_BORDER};"
        f"border-left:3px solid {color};border-radius:0 8px 8px 0;"
        f"padding:10px 14px;margin-bottom:6px;font-size:13px'>"
        f"{icon} {part}</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"<div style='color:{GROWW_MUTED};font-size:10px;margin-top:24px'>"
    f"Data: NSE India (options), Yahoo Finance (spot prices). "
    f"For personal use only — not SEBI-registered investment advice.</div>",
    unsafe_allow_html=True,
)
