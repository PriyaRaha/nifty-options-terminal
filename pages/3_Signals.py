import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import apply_groww_style, PLOTLY_THEME, GROWW_GREEN, GROWW_RED, GROWW_PURPLE, GROWW_CARD, GROWW_BORDER, GROWW_MUTED
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backend.market_data import get_nifty_history, get_vix_history, get_options_chain, get_nifty_spot
from backend.technical import (
    rsi, macd, bollinger_bands, atr, pcr, max_pain,
    iv_rank, iv_percentile, support_resistance_from_oi, interpret_signals,
)

st.set_page_config(page_title="Signals", layout="wide")
apply_groww_style()
st.title("🎯 Market Signals")

period = st.selectbox("Lookback", ["1mo", "3mo", "6mo"], index=1)
df     = get_nifty_history(period)
vix_df = get_vix_history(period)
chain  = get_options_chain("NIFTY")
spot   = get_nifty_spot()["price"]

if df.empty:
    st.error("Price data unavailable.")
    st.stop()

close   = df["Close"]
rsi_s   = rsi(close)
macd_d  = macd(close)
bb      = bollinger_bands(close)
atr_s   = atr(df)

rsi_now  = float(rsi_s.iloc[-1])
macd_now = float(macd_d["macd"].iloc[-1])
sig_now  = float(macd_d["signal"].iloc[-1])
bb_pct   = float(bb["pct_b"].iloc[-1])
vix_now  = float(vix_df["Close"].iloc[-1]) if not vix_df.empty else 0
pcr_val  = pcr(chain["df"])
mp       = max_pain(chain["df"]) if not chain["df"].empty else 0
ivr      = iv_rank(vix_df["Close"]) if not vix_df.empty else 0
ivp      = iv_percentile(vix_df["Close"]) if not vix_df.empty else 0
sr       = support_resistance_from_oi(chain["df"], spot)

# ── Signal scorecard ──────────────────────────────────────────────────────────
st.subheader("Signal Scorecard")
signals = [
    ("RSI (14)",         rsi_now,  "Overbought >70 | Oversold <30",
     "🔴" if rsi_now > 70 else "🟢" if rsi_now < 30 else "🟡"),
    ("MACD vs Signal",   macd_now - sig_now, "Positive = bullish",
     "🟢" if macd_now > sig_now else "🔴"),
    ("BB %B",            bb_pct,  "Above 1 = overbought | Below 0 = oversold",
     "🔴" if bb_pct > 1 else "🟢" if bb_pct < 0 else "🟡"),
    ("PCR (OI)",         pcr_val, "Above 1.3 = bullish sentiment | Below 0.7 = bearish",
     "🟢" if pcr_val > 1.3 else "🔴" if pcr_val < 0.7 else "🟡"),
    ("VIX Level",        vix_now, "Above 20 = high IV (good to sell)",
     "🟢" if vix_now > 20 else "🔴" if vix_now < 13 else "🟡"),
    ("IV Rank",          ivr,     "Above 50 = relatively high IV",
     "🟢" if ivr > 50 else "🔴" if ivr < 25 else "🟡"),
]

cols = st.columns(3)
for i, (name, val, desc, icon) in enumerate(signals):
    col = cols[i % 3]
    col.markdown(
        f"<div style='background:#1a1d2e;padding:12px;border-radius:8px;margin-bottom:8px'>"
        f"<div style='font-size:20px'>{icon} <b>{name}</b></div>"
        f"<div style='font-size:22px;color:#fff'>{val:.2f}</div>"
        f"<div style='color:#888;font-size:11px'>{desc}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── OI-based levels ───────────────────────────────────────────────────────────
st.subheader("OI-Based Support & Resistance")
lc, rc = st.columns(2)
with lc:
    st.markdown("**Call Resistance (CE writers)**")
    for r_level in sr["resistance"]:
        pct = (r_level - spot) / spot * 100
        st.markdown(f"- **{r_level:,.0f}** (+{pct:.1f}%)")
with rc:
    st.markdown("**Put Support (PE writers)**")
    for s_level in sr["support"]:
        pct = (s_level - spot) / spot * 100
        st.markdown(f"- **{s_level:,.0f}** ({pct:.1f}%)")

st.metric("Max Pain Strike", f"{mp:,.0f}",
          delta=f"{mp - spot:+,.0f} from spot" if mp else "")

st.divider()

# ── RSI + MACD chart ──────────────────────────────────────────────────────────
st.subheader("Technical Indicator Charts")
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    subplot_titles=["Nifty + Bollinger Bands", "RSI (14)", "MACD"],
    row_heights=[0.5, 0.25, 0.25],
    vertical_spacing=0.05,
)

fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
    name="Price", increasing_line_color="#00d4aa", decreasing_line_color="#ff4d4d",
), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=bb["upper"],  line=dict(color="#4488ff", width=1, dash="dot"), name="BB Up"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=bb["middle"], line=dict(color="#888", width=1), name="SMA20"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=bb["lower"],  line=dict(color="#4488ff", width=1, dash="dot"),
                          fill="tonexty", fillcolor="rgba(68,136,255,0.05)", name="BB Low"), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=rsi_s, line=dict(color="#ffd700", width=1.5), name="RSI"), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="#ff4d4d", opacity=0.5, row=2, col=1)
fig.add_hline(y=50, line_dash="dot",  line_color="#888",    opacity=0.3, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="#00d4aa", opacity=0.5, row=2, col=1)

hist_colors = ["#00d4aa" if v >= 0 else "#ff4d4d" for v in macd_d["hist"]]
fig.add_trace(go.Bar(x=df.index, y=macd_d["hist"], marker_color=hist_colors, name="Hist"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=macd_d["macd"],   line=dict(color="#00d4aa", width=1), name="MACD"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=macd_d["signal"], line=dict(color="#ff4d4d", width=1), name="Signal"), row=3, col=1)

fig.update_layout(
    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
    height=650, xaxis_rangeslider_visible=False, showlegend=False,
    margin=dict(l=10, r=10, t=30, b=10),
)
fig.update_xaxes(gridcolor="#2a2d3e")
fig.update_yaxes(gridcolor="#2a2d3e")
st.plotly_chart(fig, use_container_width=True)

# ── Trading view ──────────────────────────────────────────────────────────────
st.subheader("Composite Market View")
summary = interpret_signals(rsi_now, pcr_val, vix_now)
for part in summary.split(" | "):
    st.markdown(f"• {part}")

atr_val = float(atr_s.iloc[-1])
st.info(
    f"**ATR (14d):** {atr_val:,.0f} points — expected daily range. "
    f"For iron condor, place short strikes ≥ **{atr_val * 1.5:,.0f} pts** from spot for ~1σ buffer."
)
