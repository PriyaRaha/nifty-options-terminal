import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from backend.market_data import get_nifty_spot, time_to_expiry_days, get_options_chain
from backend.strategies import (
    iron_condor, delta_neutral_iron_condor, skewed_iron_condor,
    short_straddle, long_straddle, short_strangle, long_strangle,
    iron_butterfly, bull_call_spread, bear_put_spread,
    bull_put_spread, bear_call_spread, jade_lizard,
    broken_wing_butterfly, calendar_spread, ratio_spread,
    expected_return, StrategyResult,
)
from config import LOT_SIZE, RISK_FREE_RATE, STRATEGY_LIST

st.set_page_config(page_title="Strategy Builder", layout="wide")
st.title("⚡ Strategy Builder")

# ── Global inputs ─────────────────────────────────────────────────────────────
spot_live = get_nifty_spot()["price"]
dte_live  = time_to_expiry_days()
chain     = get_options_chain("NIFTY")
chain_df  = chain["df"]

col1, col2, col3 = st.columns(3)
spot      = col1.number_input("Spot Price (Nifty)", value=float(round(spot_live)), step=50.0)
dte_input = col2.number_input("Days to Expiry", value=max(int(dte_live), 1), min_value=1, max_value=90)
lots      = col3.number_input("Lots", value=2, min_value=1, max_value=50)

T = dte_input / 365
atm = round(spot / 50) * 50

strategy_choice = st.selectbox("Select Strategy", STRATEGY_LIST)
st.divider()


# ── Helper: render result ─────────────────────────────────────────────────────

def render_result(result: StrategyResult, capital: float = 500000):
    if result is None:
        st.error("Could not build strategy — check inputs.")
        return

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    max_l = result.max_loss if result.max_loss != float("inf") else "Unlimited"
    max_p = result.max_profit if result.max_profit != float("inf") else "Unlimited"
    m1.metric("Net Premium (unit)", f"₹{result.net_premium:.2f}")
    m2.metric("Net Premium (total)", f"₹{result.net_premium * LOT_SIZE * result.lots:,.0f}")
    m3.metric("Max Profit / lot", f"₹{max_p * LOT_SIZE:,.0f}" if isinstance(max_p, float) else "Unlimited")
    m4.metric("Max Loss / lot",   f"₹{max_l * LOT_SIZE:,.0f}" if isinstance(max_l, float) else "Unlimited")

    if result.breakevens:
        bes = " | ".join([f"{b:,.0f}" for b in result.breakevens])
        st.caption(f"Breakevens: **{bes}**")
    st.caption(result.notes)

    st.divider()

    # Greeks
    st.subheader("Position Greeks")
    g = result.greeks
    gc1, gc2, gc3, gc4, gc5 = st.columns(5)

    def _greek_card(col, name, val, note=""):
        color = "#00d4aa" if val >= 0 else "#ff4d4d"
        col.markdown(
            f"<div style='background:#1a1d2e;padding:12px;border-radius:8px;text-align:center'>"
            f"<div style='color:#888;font-size:11px'>{name}</div>"
            f"<div style='font-size:22px;font-weight:700;color:{color}'>{val:.4f}</div>"
            f"<div style='color:#666;font-size:10px'>{note}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    _greek_card(gc1, "Delta (Δ)",  g["delta"], "per lot")
    _greek_card(gc2, "Gamma (Γ)",  g["gamma"], "per lot")
    _greek_card(gc3, "Theta (Θ)",  g["theta"], f"₹{g['theta']*LOT_SIZE*lots:.0f}/day")
    _greek_card(gc4, "Vega (V)",   g["vega"],  "per 1% IV move")
    _greek_card(gc5, "Net Prem",   g["net_premium"], "per unit")

    st.markdown("")
    if abs(g["delta"]) < 0.05:
        st.success(f"Delta Δ = {g['delta']:.4f} — Position is **effectively delta neutral**.")
    else:
        bias = "Bullish" if g["delta"] > 0 else "Bearish"
        st.warning(f"Delta Δ = {g['delta']:.4f} — Position has **{bias}** bias.")

    st.divider()

    # P&L payoff chart
    st.subheader("P&L at Expiry")
    pf = result.payoff_df
    if not pf.empty:
        fig = go.Figure()
        pnl_lots = pf["pnl_per_lot"] * result.lots
        colors   = ["#00d4aa" if v >= 0 else "#ff4d4d" for v in pnl_lots]
        fig.add_trace(go.Scatter(
            x=pf["spot"], y=pnl_lots,
            fill="tozeroy",
            fillcolor="rgba(0,212,170,0.1)",
            line=dict(color="#00d4aa", width=2),
            name="P&L",
        ))
        fig.add_hline(y=0, line_color="#888", line_dash="dash")
        fig.add_vline(x=spot, line_color="#ffd700", line_dash="dot",
                      annotation_text=f"Spot {spot:,.0f}", annotation_position="top")
        for be in result.breakevens:
            fig.add_vline(x=be, line_color="#ff8888", line_dash="dash", opacity=0.6,
                          annotation_text=f"BE {be:,.0f}")
        fig.update_layout(
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
            height=380, showlegend=False, margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Spot at Expiry", yaxis_title="P&L (₹)",
        )
        fig.update_xaxes(gridcolor="#2a2d3e")
        fig.update_yaxes(gridcolor="#2a2d3e")
        st.plotly_chart(fig, use_container_width=True)

    # Return calculator
    st.subheader("Return Calculator")
    capital = st.number_input("Capital / Margin deployed (₹)", value=500000, step=50000)
    ret = expected_return(result, capital)
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Premium / lot",   f"₹{ret['premium_per_lot']:,.0f}")
    r2.metric("Total Premium",   f"₹{ret['total_premium']:,.0f}")
    r3.metric("Weekly ROI",      f"{ret['weekly_roi_pct']:.2f}%")
    r4.metric("Annualised ROI",  f"{ret['annual_roi_pct']:.1f}%",
              delta=f"Target: 18–20%",
              delta_color="normal" if ret["annual_roi_pct"] >= 18 else "inverse")

    # Legs table
    st.subheader("Strategy Legs")
    leg_rows = []
    for leg in result.legs:
        leg_rows.append({
            "Type":   leg.opt,
            "Strike": f"{leg.strike:,.0f}",
            "Action": "SELL" if leg.qty < 0 else "BUY",
            "Qty":    abs(leg.qty) * lots,
            "Premium": f"₹{leg.price:.2f}",
            "Value":  f"₹{leg.price * LOT_SIZE * abs(leg.qty) * lots:,.0f}",
        })
    st.dataframe(leg_rows, use_container_width=True)


# ── Strategy-specific inputs & execution ─────────────────────────────────────

if strategy_choice == "Iron Condor":
    st.subheader("Iron Condor Parameters")
    c1, c2, c3, c4 = st.columns(4)
    cs = c1.number_input("Short Call Strike", value=atm + 150, step=50)
    cl = c2.number_input("Long Call Strike",  value=atm + 300, step=50)
    ps = c3.number_input("Short Put Strike",  value=atm - 150, step=50)
    pl = c4.number_input("Long Put Strike",   value=atm - 300, step=50)
    iv_c = c1.slider("Call IV (%)", 8.0, 40.0, 15.0)
    iv_p = c3.slider("Put IV (%)",  8.0, 40.0, 16.0)
    result = iron_condor(spot, T, cs, cl, ps, pl, iv_c, iv_p, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Skewed Iron Condor":
    st.subheader("Skewed Iron Condor — Adjust for Market Bias")
    bias = st.radio("Market Bias", ["neutral", "bullish", "bearish"], horizontal=True)
    c1, c2, c3, c4 = st.columns(4)
    default_call_offset = 200 if bias == "bearish" else 150
    default_put_offset  = 200 if bias == "bullish" else 150
    cs = c1.number_input("Short Call Strike", value=atm + default_call_offset, step=50)
    cl = c2.number_input("Long Call Strike",  value=cs + 150, step=50)
    ps = c3.number_input("Short Put Strike",  value=atm - default_put_offset, step=50)
    pl = c4.number_input("Long Put Strike",   value=ps - 150, step=50)
    iv_c = st.slider("Call IV (%)", 8.0, 40.0, 14.0)
    iv_p = st.slider("Put IV (%)",  8.0, 40.0, 17.0)
    result = skewed_iron_condor(spot, T, cs, cl, ps, pl, iv_c, iv_p, RISK_FREE_RATE, lots, bias)
    render_result(result)

elif strategy_choice == "Short Straddle":
    iv = st.slider("ATM IV (%)", 8.0, 40.0, 15.0)
    result = short_straddle(spot, T, iv, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Long Straddle":
    iv = st.slider("ATM IV (%)", 8.0, 40.0, 15.0)
    result = long_straddle(spot, T, iv, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Short Strangle":
    c1, c2 = st.columns(2)
    ck = c1.number_input("Call Strike", value=atm + 200, step=50)
    pk = c2.number_input("Put Strike",  value=atm - 200, step=50)
    iv_c = c1.slider("Call IV (%)", 8.0, 40.0, 14.0)
    iv_p = c2.slider("Put IV (%)",  8.0, 40.0, 16.0)
    result = short_strangle(spot, T, ck, pk, iv_c, iv_p, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Long Strangle":
    c1, c2 = st.columns(2)
    ck = c1.number_input("Call Strike", value=atm + 200, step=50)
    pk = c2.number_input("Put Strike",  value=atm - 200, step=50)
    iv_c = c1.slider("Call IV (%)", 8.0, 40.0, 14.0)
    iv_p = c2.slider("Put IV (%)",  8.0, 40.0, 16.0)
    result = long_strangle(spot, T, ck, pk, iv_c, iv_p, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Iron Butterfly":
    c1, c2 = st.columns(2)
    wing = c1.number_input("Wing Width (pts)", value=200, step=50)
    iv   = c2.slider("IV (%)", 8.0, 40.0, 15.0)
    result = iron_butterfly(spot, T, wing, iv, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Bull Call Spread":
    c1, c2, c3 = st.columns(3)
    bk  = c1.number_input("Buy Strike (Call)", value=atm, step=50)
    sk  = c2.number_input("Sell Strike (Call)", value=atm + 150, step=50)
    iv  = c3.slider("IV (%)", 8.0, 40.0, 15.0)
    result = bull_call_spread(spot, T, bk, sk, iv, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Bear Put Spread":
    c1, c2, c3 = st.columns(3)
    bk  = c1.number_input("Buy Strike (Put)", value=atm, step=50)
    sk  = c2.number_input("Sell Strike (Put)", value=atm - 150, step=50)
    iv  = c3.slider("IV (%)", 8.0, 40.0, 15.0)
    result = bear_put_spread(spot, T, bk, sk, iv, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Bull Put Spread (Credit)":
    c1, c2, c3 = st.columns(3)
    sk  = c1.number_input("Sell Strike (Put)", value=atm - 100, step=50)
    bk  = c2.number_input("Buy Strike (Put)",  value=atm - 250, step=50)
    iv  = c3.slider("IV (%)", 8.0, 40.0, 16.0)
    result = bull_put_spread(spot, T, sk, bk, iv, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Bear Call Spread (Credit)":
    c1, c2, c3 = st.columns(3)
    sk  = c1.number_input("Sell Strike (Call)", value=atm + 100, step=50)
    bk  = c2.number_input("Buy Strike (Call)",  value=atm + 250, step=50)
    iv  = c3.slider("IV (%)", 8.0, 40.0, 15.0)
    result = bear_call_spread(spot, T, sk, bk, iv, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Jade Lizard":
    c1, c2, c3 = st.columns(3)
    pk   = c1.number_input("Short Put Strike",  value=atm - 150, step=50)
    csk  = c2.number_input("Short Call Strike", value=atm + 150, step=50)
    clk  = c3.number_input("Long Call Strike",  value=atm + 300, step=50)
    iv_p = c1.slider("Put IV (%)",  8.0, 40.0, 17.0)
    iv_c = c2.slider("Call IV (%)", 8.0, 40.0, 14.0)
    result = jade_lizard(spot, T, pk, csk, clk, iv_p, iv_c, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Broken Wing Butterfly":
    c1, c2, c3 = st.columns(3)
    atm_k  = c1.number_input("ATM Put Strike",    value=atm, step=50)
    lower  = c2.number_input("Lower Put Strike",  value=atm - 150, step=50)
    skip   = c3.number_input("Skip Put Strike",   value=atm - 350, step=50)
    iv     = st.slider("IV (%)", 8.0, 40.0, 15.0)
    result = broken_wing_butterfly(spot, T, atm_k, lower, skip, iv, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Calendar Spread":
    c1, c2, c3 = st.columns(3)
    K        = c1.number_input("Strike", value=atm, step=50)
    dte_near = c2.number_input("Near-Month DTE", value=7, min_value=1, max_value=30)
    dte_far  = c3.number_input("Far-Month DTE",  value=30, min_value=8, max_value=90)
    iv_n = c2.slider("Near IV (%)", 8.0, 40.0, 16.0)
    iv_f = c3.slider("Far IV (%)",  8.0, 40.0, 14.0)
    result = calendar_spread(spot, K, dte_near / 365, dte_far / 365, iv_n, iv_f, RISK_FREE_RATE, lots)
    render_result(result)

elif strategy_choice == "Ratio Spread":
    c1, c2, c3 = st.columns(3)
    bk    = c1.number_input("Buy Strike (ATM call)", value=atm, step=50)
    sk    = c2.number_input("Sell Strike (OTM call)", value=atm + 150, step=50)
    ratio = c3.number_input("Ratio (sell)", value=2, min_value=2, max_value=4)
    iv    = st.slider("IV (%)", 8.0, 40.0, 15.0)
    st.warning("Ratio Spread has unlimited upside risk. Use with caution.")
    result = ratio_spread(spot, T, bk, sk, ratio, iv, RISK_FREE_RATE, lots)
    render_result(result)
