import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import apply_groww_style, PLOTLY_THEME, GROWW_GREEN, GROWW_RED, GROWW_PURPLE, GROWW_CARD, GROWW_BORDER, GROWW_MUTED
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from backend.market_data import (
    get_nifty_history, get_vix_history, get_nifty_spot, get_india_vix,
)
from backend.technical import (
    rsi, macd, bollinger_bands, iv_rank, iv_percentile,
)

st.set_page_config(page_title="Market Overview", layout="wide")
apply_groww_style()
st.title("📊 Market Overview")

period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y"], index=1)
df     = get_nifty_history(period, "1d")

if df.empty:
    st.error("Could not load price data. Check your internet connection.")
    st.stop()

close  = df["Close"]
rsi_s  = rsi(close)
macd_d = macd(close)
bb     = bollinger_bands(close)

# ── Candlestick + BB ──────────────────────────────────────────────────────────
st.subheader("Nifty 50 — Price + Bollinger Bands")
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    row_heights=[0.6, 0.2, 0.2],
    vertical_spacing=0.03,
)

fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
    name="OHLC",
    increasing_line_color="#00d4aa", decreasing_line_color="#ff4d4d",
), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=bb["upper"],  name="BB Upper",  line=dict(color="#4488ff", width=1, dash="dot")), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=bb["middle"], name="BB Middle", line=dict(color="#888888", width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=bb["lower"],  name="BB Lower",  line=dict(color="#4488ff", width=1, dash="dot"),
                          fill="tonexty", fillcolor="rgba(68,136,255,0.05)"), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=rsi_s, name="RSI(14)", line=dict(color="#ffd700", width=1.5)), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="#ff4d4d", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="#00d4aa", opacity=0.5, row=2, col=1)

colors = ["#00d4aa" if v >= 0 else "#ff4d4d" for v in macd_d["hist"]]
fig.add_trace(go.Bar(x=df.index, y=macd_d["hist"], name="MACD Hist", marker_color=colors), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=macd_d["macd"],   name="MACD",   line=dict(color="#00d4aa", width=1)), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=macd_d["signal"], name="Signal", line=dict(color="#ff4d4d", width=1)), row=3, col=1)

fig.update_layout(
    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
    height=620, xaxis_rangeslider_visible=False, showlegend=True,
    legend=dict(bgcolor="#1a1d2e", bordercolor="#333"),
    margin=dict(l=10, r=10, t=10, b=10),
)
fig.update_xaxes(gridcolor="#2a2d3e")
fig.update_yaxes(gridcolor="#2a2d3e")
st.plotly_chart(fig, use_container_width=True)

# ── VIX chart ─────────────────────────────────────────────────────────────────
st.subheader("India VIX")
vix_df = get_vix_history(period)

if not vix_df.empty and "Close" in vix_df.columns:
    ivr  = iv_rank(vix_df["Close"])
    ivp  = iv_percentile(vix_df["Close"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Current VIX", f"{get_india_vix()['price']:.2f}")
    col2.metric("IV Rank (52w)", f"{ivr:.1f}%", help="(Current - Low) / (High - Low) × 100")
    col3.metric("IV Percentile", f"{ivp:.1f}%", help="% of days IV was below current")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=vix_df.index, y=vix_df["Close"],
        fill="tozeroy", fillcolor="rgba(255,77,77,0.15)",
        line=dict(color="#ff4d4d", width=1.5), name="VIX",
    ))
    fig2.add_hline(y=20, line_dash="dash", line_color="#ffd700", opacity=0.7,
                   annotation_text="High IV (20)", annotation_position="top right")
    fig2.add_hline(y=14, line_dash="dash", line_color="#888", opacity=0.5,
                   annotation_text="Low IV (14)")
    fig2.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
        height=220, showlegend=False, margin=dict(l=10, r=10, t=10, b=10),
    )
    fig2.update_xaxes(gridcolor="#2a2d3e")
    fig2.update_yaxes(gridcolor="#2a2d3e")
    st.plotly_chart(fig2, use_container_width=True)

    if ivr > 50:
        st.success(f"VIX IV Rank {ivr:.0f}% — IV is **elevated**. Favourable for premium selling (Iron Condor, Straddle).")
    else:
        st.warning(f"VIX IV Rank {ivr:.0f}% — IV is **compressed**. Premium selling less attractive; consider debit strategies.")

# ── Key stats ─────────────────────────────────────────────────────────────────
st.subheader("Key Statistics")
spot    = get_nifty_spot()
high52  = float(close.max())
low52   = float(close.min())
curr    = spot["price"]

col1, col2, col3, col4 = st.columns(4)
col1.metric(f"{period} High", f"{high52:,.2f}")
col2.metric(f"{period} Low",  f"{low52:,.2f}")
col3.metric("RSI (14d)", f"{float(rsi_s.iloc[-1]):.1f}")
col4.metric("ATR (14d)", f"{float((df['High'] - df['Low']).rolling(14).mean().iloc[-1]):,.0f}",
            help="Average True Range — expected daily move")

pct_from_high = (curr - high52) / high52 * 100
pct_from_low  = (curr - low52)  / low52  * 100
st.info(
    f"Current Nifty **{curr:,.0f}** | "
    f"{pct_from_high:.1f}% from {period} high | "
    f"{pct_from_low:+.1f}% from {period} low"
)
