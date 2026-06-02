"""Groww-inspired CSS injected into every page."""
import streamlit as st

# Groww color palette
GROWW_PURPLE  = "#5367FF"
GROWW_GREEN   = "#00B386"
GROWW_RED     = "#E74C3C"
GROWW_BG      = "#0F0F0F"
GROWW_CARD    = "#1A1A1A"
GROWW_BORDER  = "#2A2A2A"
GROWW_TEXT    = "#FFFFFF"
GROWW_MUTED   = "#7C7C7C"
GROWW_YELLOW  = "#F5A623"

GROWW_CSS = f"""
<style>
/* ── Global ── */
html, body, [class*="css"] {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: {GROWW_BG};
    color: {GROWW_TEXT};
}}

/* Hide Streamlit branding */
#MainMenu, footer, header {{ visibility: hidden; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background-color: #111111;
    border-right: 1px solid {GROWW_BORDER};
}}
[data-testid="stSidebar"] .css-1d391kg {{ padding-top: 2rem; }}

/* ── Top navbar strip ── */
[data-testid="stAppViewContainer"] > .main {{
    background-color: {GROWW_BG};
    padding-top: 0;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
    background: {GROWW_CARD};
    border: 1px solid {GROWW_BORDER};
    border-radius: 12px;
    padding: 16px;
}}
[data-testid="metric-container"] label {{
    color: {GROWW_MUTED} !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 22px !important;
    font-weight: 700 !important;
    color: {GROWW_TEXT} !important;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] svg {{
    display: none;
}}

/* ── Buttons ── */
.stButton > button {{
    background: {GROWW_PURPLE};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 14px;
    transition: opacity 0.2s;
}}
.stButton > button:hover {{ opacity: 0.85; background: {GROWW_PURPLE}; }}

/* ── Tabs ── */
[data-baseweb="tab-list"] {{
    background: {GROWW_CARD};
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border-bottom: none !important;
}}
[data-baseweb="tab"] {{
    border-radius: 8px !important;
    color: {GROWW_MUTED} !important;
    font-weight: 500;
    padding: 8px 20px !important;
}}
[aria-selected="true"] {{
    background: {GROWW_PURPLE} !important;
    color: white !important;
}}

/* ── Selectbox / dropdowns ── */
[data-testid="stSelectbox"] > div > div {{
    background: {GROWW_CARD};
    border: 1px solid {GROWW_BORDER};
    border-radius: 8px;
    color: {GROWW_TEXT};
}}

/* ── Number inputs ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {{
    background: {GROWW_CARD} !important;
    border: 1px solid {GROWW_BORDER} !important;
    border-radius: 8px !important;
    color: {GROWW_TEXT} !important;
}}

/* ── Sliders ── */
[data-testid="stSlider"] div[role="slider"] {{
    background: {GROWW_PURPLE} !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {GROWW_BORDER};
    border-radius: 12px;
    overflow: hidden;
}}

/* ── Divider ── */
hr {{ border-color: {GROWW_BORDER}; }}

/* ── Info / warning / success boxes ── */
[data-testid="stAlert"] {{
    border-radius: 10px;
    border: none;
}}

/* ── Headings ── */
h1 {{ font-size: 24px !important; font-weight: 700 !important; color: {GROWW_TEXT}; }}
h2 {{ font-size: 18px !important; font-weight: 600 !important; color: {GROWW_TEXT}; }}
h3 {{ font-size: 15px !important; font-weight: 600 !important; color: {GROWW_MUTED}; }}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background: {GROWW_CARD};
    border: 1px solid {GROWW_BORDER} !important;
    border-radius: 10px;
}}

/* ── Progress bar ── */
[data-testid="stProgress"] > div > div > div {{
    background: {GROWW_PURPLE} !important;
}}
</style>
"""

PLOTLY_THEME = dict(
    plot_bgcolor  = "#1A1A1A",
    paper_bgcolor = "#1A1A1A",
    font_color    = "#FFFFFF",
    xaxis         = dict(gridcolor="#2A2A2A", zerolinecolor="#2A2A2A"),
    yaxis         = dict(gridcolor="#2A2A2A", zerolinecolor="#2A2A2A"),
)


def apply_groww_style():
    st.markdown(GROWW_CSS, unsafe_allow_html=True)


def groww_metric(col, label, price, chng, chng_pct, fmt="{:,.2f}"):
    """Groww-style metric card with price and change."""
    arrow  = "▲" if chng >= 0 else "▼"
    color  = GROWW_GREEN if chng >= 0 else GROWW_RED
    col.markdown(
        f"<div style='"
        f"background:{GROWW_CARD};"
        f"border:1px solid {GROWW_BORDER};"
        f"border-radius:12px;"
        f"padding:18px 20px;"
        f"'>"
        f"<div style='color:{GROWW_MUTED};font-size:11px;text-transform:uppercase;"
        f"letter-spacing:0.8px;margin-bottom:6px'>{label}</div>"
        f"<div style='font-size:24px;font-weight:700;color:{GROWW_TEXT};"
        f"letter-spacing:-0.5px'>{fmt.format(price)}</div>"
        f"<div style='color:{color};font-size:13px;font-weight:600;margin-top:4px'>"
        f"{arrow} {abs(chng):,.2f} "
        f"<span style='opacity:0.8'>({chng_pct:+.2f}%)</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def groww_signal_card(col, label, value, status, fmt="{:.2f}", unit=""):
    color_map = {
        "bullish":  GROWW_GREEN,
        "bearish":  GROWW_RED,
        "neutral":  GROWW_YELLOW,
        "high":     GROWW_GREEN,
        "low":      GROWW_RED,
        "normal":   GROWW_YELLOW,
    }
    color = color_map.get(status.lower(), GROWW_MUTED)
    col.markdown(
        f"<div style='"
        f"background:{GROWW_CARD};"
        f"border:1px solid {GROWW_BORDER};"
        f"border-radius:12px;"
        f"padding:18px 20px;"
        f"text-align:center;"
        f"'>"
        f"<div style='color:{GROWW_MUTED};font-size:11px;text-transform:uppercase;"
        f"letter-spacing:0.8px;margin-bottom:8px'>{label}</div>"
        f"<div style='font-size:28px;font-weight:700;color:{color}'>"
        f"{fmt.format(value)}{unit}</div>"
        f"<div style='color:{color};font-size:12px;font-weight:600;margin-top:4px'>"
        f"{status.upper()}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def groww_greek_card(col, name, val, note=""):
    color = GROWW_GREEN if val >= 0 else GROWW_RED
    col.markdown(
        f"<div style='"
        f"background:{GROWW_CARD};"
        f"border:1px solid {GROWW_BORDER};"
        f"border-radius:12px;"
        f"padding:16px;"
        f"text-align:center;"
        f"'>"
        f"<div style='color:{GROWW_MUTED};font-size:11px;text-transform:uppercase;"
        f"letter-spacing:0.8px;margin-bottom:6px'>{name}</div>"
        f"<div style='font-size:20px;font-weight:700;color:{color}'>{val}</div>"
        f"<div style='color:{GROWW_MUTED};font-size:10px;margin-top:4px'>{note}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
