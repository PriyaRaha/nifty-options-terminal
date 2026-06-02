"""Exact Groww design system — tokens extracted from groww.in CSS."""
import streamlit as st

# ── Groww exact dark-theme tokens (data-theme=dark) ──────────────────────────
G_BG_PRIMARY    = "#060809"   # --background-primary
G_BG_SECONDARY  = "#151819"   # --background-secondary
G_BG_TERTIARY   = "#252525"   # --background-tertiary
G_BG_SURFACE    = "#1e2224"   # --background-surface-primary
G_BORDER        = "#2e2e2e"   # --border-primary

G_TEXT_PRIMARY   = "#f2f5f7"  # --content-primary
G_TEXT_SECONDARY = "#989ea0"  # --content-secondary
G_TEXT_DISABLED  = "#44494b"  # --content-disabled

G_POSITIVE      = "#04b488"   # --green9 (green500) — gains, profit, bullish
G_NEGATIVE      = "#ff5e3b"   # --red9 (dark) — loss, bearish
G_WARNING       = "#f5bc56"   # --content-on-warning-subtle

G_FONT_URL = "https://resources.groww.in/web-assets/font/GrowwSans-Variable.woff2"
G_FONT_FAMILY = "GrowwSans, NotoSans, system-ui, -apple-system, sans-serif"

# ── Streamlit config.toml values ─────────────────────────────────────────────
# (kept in .streamlit/config.toml, matching below)
# primaryColor = G_POSITIVE
# backgroundColor = G_BG_PRIMARY
# secondaryBackgroundColor = G_BG_SURFACE

GROWW_CSS = f"""
<style>
/* ── Load GrowwSans Variable Font ── */
@font-face {{
  font-family: 'GrowwSans';
  src: url('{G_FONT_URL}') format('woff2');
  font-weight: 100 900;
  font-display: swap;
}}

/* ── Reset & Base ── */
html, body, [class*="css"], [class*="st-"] {{
  font-family: {G_FONT_FAMILY} !important;
  background-color: {G_BG_PRIMARY} !important;
  color: {G_TEXT_PRIMARY} !important;
  -webkit-font-smoothing: antialiased;
}}
body {{ font-weight: 435; }}

/* Hide Streamlit chrome */
#MainMenu, footer, header, [data-testid="stToolbar"] {{ visibility: hidden; height: 0; }}
[data-testid="stDecoration"] {{ display: none; }}

/* ── App background ── */
.stApp, [data-testid="stAppViewContainer"] {{
  background-color: {G_BG_PRIMARY} !important;
}}
[data-testid="stAppViewContainer"] > .main {{
  background-color: {G_BG_PRIMARY} !important;
  padding-top: 12px;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
  background-color: {G_BG_SECONDARY} !important;
  border-right: 1px solid {G_BORDER};
}}
[data-testid="stSidebar"] * {{ color: {G_TEXT_PRIMARY} !important; }}
[data-testid="stSidebarNav"] a {{
  color: {G_TEXT_SECONDARY} !important;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 5px;
}}
[data-testid="stSidebarNav"] a:hover {{
  background: {G_BG_TERTIARY} !important;
  color: {G_TEXT_PRIMARY} !important;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
  background: {G_BG_SURFACE};
  border: 1px solid {G_BORDER};
  border-radius: 5px;
  padding: 16px;
}}
[data-testid="metric-container"] label {{
  color: {G_TEXT_SECONDARY} !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}}
[data-testid="stMetricValue"] {{
  font-size: 22px !important;
  font-weight: 600 !important;
  color: {G_TEXT_PRIMARY} !important;
  font-family: {G_FONT_FAMILY} !important;
}}

/* ── Buttons ── */
.stButton > button {{
  background-color: {G_POSITIVE} !important;
  color: #000 !important;
  border: none !important;
  border-radius: 5px !important;
  font-family: {G_FONT_FAMILY} !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  padding: 8px 20px !important;
  transition: opacity 0.15s ease !important;
}}
.stButton > button:hover {{ opacity: 0.88 !important; }}

/* ── Tabs ── */
[data-baseweb="tab-list"] {{
  background: {G_BG_SURFACE} !important;
  border-radius: 5px !important;
  padding: 3px !important;
  gap: 2px !important;
  border-bottom: none !important;
}}
[data-baseweb="tab"] {{
  border-radius: 4px !important;
  color: {G_TEXT_SECONDARY} !important;
  font-family: {G_FONT_FAMILY} !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  padding: 8px 18px !important;
  transition: background 0.15s !important;
}}
[aria-selected="true"] {{
  background: {G_POSITIVE} !important;
  color: #000 !important;
  font-weight: 600 !important;
}}

/* ── Inputs ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
  background: {G_BG_SURFACE} !important;
  border: 1px solid {G_BORDER} !important;
  border-radius: 5px !important;
  color: {G_TEXT_PRIMARY} !important;
  font-family: {G_FONT_FAMILY} !important;
  font-size: 14px !important;
}}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus {{
  border-color: {G_POSITIVE} !important;
  box-shadow: 0 0 0 2px rgba(4,180,136,0.15) !important;
}}
input::placeholder {{ color: {G_TEXT_DISABLED} !important; }}

/* ── Labels ── */
label, [data-testid="stWidgetLabel"] p {{
  color: {G_TEXT_SECONDARY} !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}}

/* ── Radio buttons ── */
[data-testid="stRadio"] label {{ text-transform: none !important; letter-spacing: 0; font-size: 14px !important; }}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{ color: {G_TEXT_PRIMARY} !important; font-size: 14px !important; }}

/* ── Sliders ── */
[data-testid="stSlider"] [role="slider"] {{
  background: {G_POSITIVE} !important;
  border-color: {G_POSITIVE} !important;
}}
[data-testid="stSlider"] [data-baseweb="slider"] div[style*="background"] {{
  background: {G_POSITIVE} !important;
}}

/* ── Dataframe / tables ── */
[data-testid="stDataFrame"] {{
  border: 1px solid {G_BORDER} !important;
  border-radius: 5px !important;
  overflow: hidden;
}}
[data-testid="stDataFrame"] th {{
  background: {G_BG_SECONDARY} !important;
  color: {G_TEXT_SECONDARY} !important;
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  font-weight: 600 !important;
  border-bottom: 1px solid {G_BORDER} !important;
}}
[data-testid="stDataFrame"] td {{
  background: {G_BG_SURFACE} !important;
  color: {G_TEXT_PRIMARY} !important;
  font-size: 13px !important;
  border-bottom: 1px solid {G_BORDER} !important;
}}

/* ── Expander ── */
[data-testid="stExpander"] {{
  background: {G_BG_SURFACE} !important;
  border: 1px solid {G_BORDER} !important;
  border-radius: 5px !important;
}}
[data-testid="stExpander"] summary {{
  color: {G_TEXT_PRIMARY} !important;
  font-weight: 500 !important;
  font-size: 14px !important;
}}

/* ── Alert boxes ── */
[data-testid="stAlert"] {{
  border-radius: 5px !important;
  border: none !important;
  font-size: 13px !important;
}}
[data-testid="stAlert"][data-baseweb="notification"] {{
  background: rgba(4,180,136,0.1) !important;
  color: {G_POSITIVE} !important;
}}

/* ── Divider ── */
hr {{ border-color: {G_BORDER} !important; margin: 16px 0 !important; }}

/* ── Headings ── */
h1 {{
  font-family: {G_FONT_FAMILY} !important;
  font-size: 22px !important;
  font-weight: 600 !important;
  color: {G_TEXT_PRIMARY} !important;
  letter-spacing: -0.2px;
  margin-bottom: 4px !important;
}}
h2 {{
  font-family: {G_FONT_FAMILY} !important;
  font-size: 17px !important;
  font-weight: 600 !important;
  color: {G_TEXT_PRIMARY} !important;
  margin-top: 24px !important;
  margin-bottom: 12px !important;
}}
h3 {{
  font-size: 13px !important;
  font-weight: 500 !important;
  color: {G_TEXT_SECONDARY} !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
p, li {{ color: {G_TEXT_PRIMARY}; font-size: 14px; line-height: 1.5; }}

/* ── Caption / small text ── */
[data-testid="stCaptionContainer"] p,
.caption, small {{
  color: {G_TEXT_SECONDARY} !important;
  font-size: 12px !important;
}}

/* ── Progress bar ── */
[data-testid="stProgress"] > div > div > div {{
  background: {G_POSITIVE} !important;
  border-radius: 2px !important;
}}
[data-testid="stProgress"] > div > div {{
  background: {G_BG_TERTIARY} !important;
  border-radius: 2px !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: {G_BG_PRIMARY}; }}
::-webkit-scrollbar-thumb {{ background: {G_BORDER}; border-radius: 2px; }}
::-webkit-scrollbar-thumb:hover {{ background: {G_TEXT_DISABLED}; }}

/* ── Number input arrows ── */
input[type=number]::-webkit-outer-spin-button,
input[type=number]::-webkit-inner-spin-button {{ opacity: 0.4; }}
</style>
"""

PLOTLY_THEME = dict(
    plot_bgcolor  = G_BG_SURFACE,
    paper_bgcolor = G_BG_PRIMARY,
    font          = dict(family=G_FONT_FAMILY, color=G_TEXT_PRIMARY, size=12),
    xaxis         = dict(gridcolor=G_BORDER, zerolinecolor=G_BORDER, linecolor=G_BORDER),
    yaxis         = dict(gridcolor=G_BORDER, zerolinecolor=G_BORDER, linecolor=G_BORDER),
    legend        = dict(bgcolor=G_BG_SURFACE, bordercolor=G_BORDER, borderwidth=1),
)


def apply_groww_style():
    st.markdown(GROWW_CSS, unsafe_allow_html=True)


def groww_metric(col, label, price, chng, chng_pct, fmt="{:,.2f}"):
    arrow = "▲" if chng >= 0 else "▼"
    color = G_POSITIVE if chng >= 0 else G_NEGATIVE
    col.markdown(
        f"<div style='background:{G_BG_SURFACE};border:1px solid {G_BORDER};"
        f"border-radius:5px;padding:16px 18px'>"
        f"<div style='color:{G_TEXT_SECONDARY};font-size:11px;font-weight:500;"
        f"text-transform:uppercase;letter-spacing:0.4px;margin-bottom:6px'>{label}</div>"
        f"<div style='font-size:22px;font-weight:600;color:{G_TEXT_PRIMARY};"
        f"font-family:{G_FONT_FAMILY};letter-spacing:-0.3px'>{fmt.format(price)}</div>"
        f"<div style='color:{color};font-size:13px;font-weight:500;margin-top:5px'>"
        f"{arrow} {abs(chng):,.2f} "
        f"<span style='opacity:0.75'>({chng_pct:+.2f}%)</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def groww_signal_card(col, label, value, status, fmt="{:.2f}", unit=""):
    color_map = {
        "bullish": G_POSITIVE, "high": G_POSITIVE,
        "bearish": G_NEGATIVE, "low": G_NEGATIVE,
        "neutral": G_WARNING,  "normal": G_WARNING,
    }
    color = color_map.get(status.lower(), G_TEXT_SECONDARY)
    col.markdown(
        f"<div style='background:{G_BG_SURFACE};border:1px solid {G_BORDER};"
        f"border-radius:5px;padding:16px 18px;text-align:center'>"
        f"<div style='color:{G_TEXT_SECONDARY};font-size:11px;font-weight:500;"
        f"text-transform:uppercase;letter-spacing:0.4px;margin-bottom:8px'>{label}</div>"
        f"<div style='font-size:26px;font-weight:600;color:{color};"
        f"font-family:{G_FONT_FAMILY}'>{fmt.format(value)}{unit}</div>"
        f"<div style='color:{color};font-size:11px;font-weight:600;margin-top:5px;"
        f"text-transform:uppercase;letter-spacing:0.5px'>{status}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def groww_greek_card(col, name, val, note=""):
    color = G_POSITIVE if val >= 0 else G_NEGATIVE
    if isinstance(val, float):
        display = f"{val:.4f}"
    else:
        display = str(val)
    col.markdown(
        f"<div style='background:{G_BG_SURFACE};border:1px solid {G_BORDER};"
        f"border-radius:5px;padding:14px 16px;text-align:center'>"
        f"<div style='color:{G_TEXT_SECONDARY};font-size:11px;font-weight:500;"
        f"text-transform:uppercase;letter-spacing:0.4px;margin-bottom:6px'>{name}</div>"
        f"<div style='font-size:18px;font-weight:600;color:{color};"
        f"font-family:{G_FONT_FAMILY}'>{display}</div>"
        f"<div style='color:{G_TEXT_DISABLED};font-size:10px;margin-top:4px'>{note}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# Expose constants for direct use in pages
GROWW_GREEN    = G_POSITIVE
GROWW_RED      = G_NEGATIVE
GROWW_YELLOW   = G_WARNING
GROWW_PURPLE   = G_POSITIVE   # accent = green on Groww (not purple)
GROWW_CARD     = G_BG_SURFACE
GROWW_BG       = G_BG_PRIMARY
GROWW_BORDER   = G_BORDER
GROWW_MUTED    = G_TEXT_SECONDARY
