import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import apply_groww_style, PLOTLY_THEME, GROWW_GREEN, GROWW_RED, GROWW_PURPLE, GROWW_CARD, GROWW_BORDER, GROWW_MUTED
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from backend.greeks import calculate_greeks, implied_volatility
from backend.market_data import get_nifty_spot, time_to_expiry_days
from config import RISK_FREE_RATE, LOT_SIZE

st.set_page_config(page_title="Greeks Calculator", layout="wide")
apply_groww_style()
st.title("🔢 Greeks & IV Calculator")

tab1, tab2, tab3 = st.tabs(["Option Greeks", "IV Calculator", "Greeks Sensitivity"])

# ─────────────────────────────────────────────────────────────────────────────
# Tab 1: Greeks
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    spot_live = get_nifty_spot()["price"]
    dte_live  = time_to_expiry_days()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Inputs")
        S     = st.number_input("Spot Price",       value=float(round(spot_live)), step=50.0)
        K     = st.number_input("Strike Price",     value=float(round(spot_live / 50) * 50), step=50.0)
        dte   = st.number_input("Days to Expiry",   value=max(int(dte_live), 1), min_value=1, max_value=365)
        iv    = st.number_input("IV (%)",            value=15.0, min_value=1.0, max_value=150.0)
        r     = st.number_input("Risk-Free Rate (%)", value=6.5, min_value=0.0, max_value=20.0) / 100
        opt   = st.radio("Option Type", ["CE", "PE"], horizontal=True)
        n_lots = st.number_input("Number of Lots",  value=1, min_value=1, max_value=100)

    T = dte / 365
    g = calculate_greeks(S, K, T, r, iv / 100, opt)

    with col2:
        st.subheader("Greeks")

        def _gcard(name, val, note, color_positive=True):
            color = "#00d4aa" if (val >= 0) == color_positive else "#ff4d4d"
            st.markdown(
                f"<div style='background:#1a1d2e;padding:14px;border-radius:8px;margin-bottom:8px'>"
                f"<div style='color:#888;font-size:12px'>{name}</div>"
                f"<div style='font-size:24px;font-weight:700;color:{color}'>{val}</div>"
                f"<div style='color:#555;font-size:11px'>{note}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        _gcard("Option Price",
               f"₹{g['price']:.2f}",
               f"Total for {n_lots} lot(s): ₹{g['price'] * LOT_SIZE * n_lots:,.0f}")
        _gcard("Delta (Δ)",
               f"{g['delta']:.4f}",
               f"₹{g['delta'] * 1:,.2f} per 1 pt move in Nifty")
        _gcard("Gamma (Γ)",
               f"{g['gamma']:.6f}",
               f"Delta changes by {g['gamma']:.4f} per 1 pt spot move")
        _gcard("Theta (Θ)",
               f"₹{g['theta']:.2f} / day",
               f"Per lot: ₹{g['theta'] * LOT_SIZE:.0f} | Per {n_lots} lot(s): ₹{g['theta'] * LOT_SIZE * n_lots:.0f}",
               color_positive=False)
        _gcard("Vega (V)",
               f"₹{g['vega']:.2f}",
               f"Per lot: ₹{g['vega'] * LOT_SIZE:.0f} per 1% IV move")
        _gcard("Rho (ρ)",
               f"₹{g['rho']:.2f}",
               "Per 1% change in interest rate")

    # Moneyness
    st.divider()
    moneyness = (S - K) / K * 100 if opt == "CE" else (K - S) / K * 100
    status = "ITM" if moneyness > 0 else "OTM" if moneyness < 0 else "ATM"
    st.info(
        f"**{status}** | Moneyness: {moneyness:+.2f}% | "
        f"Intrinsic: ₹{max(S-K,0) if opt=='CE' else max(K-S,0):.2f} | "
        f"Time Value: ₹{g['price'] - (max(S-K,0) if opt=='CE' else max(K-S,0)):.2f}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2: IV Calculator
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Implied Volatility Calculator")
    spot_live = get_nifty_spot()["price"]
    dte_live  = time_to_expiry_days()

    col1, col2 = st.columns(2)
    with col1:
        mkt_price = st.number_input("Market Price of Option (₹)", value=100.0, min_value=0.5, step=0.5)
        S2 = st.number_input("Spot Price", value=float(round(spot_live)), step=50.0, key="iv_s")
        K2 = st.number_input("Strike Price", value=float(round(spot_live / 50) * 50), step=50.0, key="iv_k")
        dte2 = st.number_input("Days to Expiry", value=max(int(dte_live), 1), key="iv_dte")
        r2   = st.number_input("Risk-Free Rate (%)", value=6.5, key="iv_r") / 100
        opt2 = st.radio("Option Type", ["CE", "PE"], horizontal=True, key="iv_opt")

    T2   = dte2 / 365
    iv_r = implied_volatility(mkt_price, S2, K2, T2, r2, opt2)

    with col2:
        if iv_r > 0:
            st.metric("Implied Volatility", f"{iv_r * 100:.2f}%")
            g2 = calculate_greeks(S2, K2, T2, r2, iv_r, opt2)
            st.metric("Theoretical Price (verify)", f"₹{g2['price']:.2f}",
                      delta=f"{g2['price'] - mkt_price:+.2f} vs market",
                      delta_color="off")
            st.markdown(
                f"**IV = {iv_r * 100:.2f}%** implies the market expects Nifty to move "
                f"±**{iv_r * spot_live * (dte2/365)**0.5 :,.0f} pts** by expiry "
                f"(1σ move, {dte2}d)."
            )
            with st.expander("All Greeks at this IV"):
                for k, v in g2.items():
                    st.text(f"{k:12s}: {v}")
        else:
            st.error("Could not calculate IV. Check that market price > intrinsic value.")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3: Sensitivity (Greek surfaces)
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Greeks Sensitivity Charts")
    spot_live = get_nifty_spot()["price"]
    dte_live  = time_to_expiry_days()

    K3   = st.number_input("Strike", value=float(round(spot_live / 50) * 50), step=50.0, key="sens_k")
    dte3 = st.number_input("DTE", value=max(int(dte_live), 1), key="sens_dte")
    iv3  = st.slider("IV (%)", 8.0, 40.0, 15.0, key="sens_iv")
    opt3 = st.radio("Type", ["CE", "PE"], horizontal=True, key="sens_opt")

    T3    = dte3 / 365
    spots = np.linspace(spot_live * 0.9, spot_live * 1.1, 200)
    deltas, gammas, thetas, vegas, prices = [], [], [], [], []

    for s in spots:
        g3 = calculate_greeks(s, K3, T3, RISK_FREE_RATE, iv3 / 100, opt3)
        prices.append(g3["price"])
        deltas.append(g3["delta"])
        gammas.append(g3["gamma"])
        thetas.append(g3["theta"])
        vegas.append(g3["vega"])

    fig = go.Figure()
    greek_choice = st.selectbox("Display Greek", ["Price", "Delta", "Gamma", "Theta", "Vega"])
    data_map = {"Price": prices, "Delta": deltas, "Gamma": gammas, "Theta": thetas, "Vega": vegas}
    y_data = data_map[greek_choice]

    fig.add_trace(go.Scatter(
        x=spots, y=y_data,
        line=dict(color="#00d4aa", width=2),
        name=greek_choice,
    ))
    fig.add_vline(x=spot_live, line_dash="dash", line_color="#ffd700",
                  annotation_text=f"Spot {spot_live:,.0f}")
    fig.add_vline(x=K3, line_dash="dot", line_color="#ff8888",
                  annotation_text=f"Strike {K3:,.0f}")
    fig.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
        height=380, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Spot Price", yaxis_title=greek_choice,
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="#2a2d3e")
    fig.update_yaxes(gridcolor="#2a2d3e")
    st.plotly_chart(fig, use_container_width=True)

    # Summary table across DTE scenarios
    st.subheader("Greeks Across DTE Scenarios")
    rows = []
    for d in [1, 3, 5, 7, 14, 21, 30]:
        g_d = calculate_greeks(spot_live, K3, d / 365, RISK_FREE_RATE, iv3 / 100, opt3)
        rows.append({"DTE": d, **{k: round(v, 4) for k, v in g_d.items()}})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
