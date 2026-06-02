import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from backend.market_data import get_market_news

st.set_page_config(page_title="Market News", layout="wide")
st.title("📰 Market News")

MARKET_KEYWORDS = [
    "nifty", "sensex", "rbi", "repo rate", "inflation", "gdp", "ipo",
    "fii", "dii", "budget", "fed", "fomc", "cpi", "earnings", "results",
    "sebi", "options", "futures", "derivatives", "rally", "selloff",
]

st.caption("Aggregated from ET Markets, Business Standard, Mint. Refresh every 10 min.")

if st.button("🔄 Refresh News"):
    st.cache_data.clear()

articles = get_market_news()

# Filter controls
col1, col2 = st.columns([3, 1])
search = col1.text_input("Search news", placeholder="e.g. RBI, inflation, results...")
source_filter = col2.selectbox("Source", ["All", "ET Markets", "Business Standard", "Mint Markets"])

def _is_market_relevant(article: dict) -> bool:
    text = (article["title"] + " " + article["summary"]).lower()
    return any(kw in text for kw in MARKET_KEYWORDS)

if search:
    articles = [a for a in articles if search.lower() in (a["title"] + a["summary"]).lower()]
if source_filter != "All":
    articles = [a for a in articles if a["source"] == source_filter]

market_articles = [a for a in articles if _is_market_relevant(a)]
other_articles  = [a for a in articles if not _is_market_relevant(a)]

ordered = market_articles + other_articles

if not ordered:
    st.info("No news articles available. Check your internet connection.")
else:
    st.markdown(f"**{len(ordered)} articles** | {len(market_articles)} market-relevant")
    st.divider()

    for article in ordered:
        is_relevant = _is_market_relevant(article)
        border = "#00d4aa" if is_relevant else "#333"
        st.markdown(
            f"<div style='border-left:3px solid {border};padding:12px 16px;"
            f"background:#1a1d2e;border-radius:0 8px 8px 0;margin-bottom:12px'>"
            f"<div style='color:#888;font-size:11px'>{article['source']} &nbsp;·&nbsp; {article['published']}</div>"
            f"<div style='font-size:15px;font-weight:600;color:#e0e0e0;margin:4px 0'>{article['title']}</div>"
            f"<div style='color:#aaa;font-size:12px;line-height:1.5'>{article['summary']}</div>"
            f"<a href='{article['link']}' target='_blank' style='color:#00d4aa;font-size:12px'>Read more →</a>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Weekly events calendar ────────────────────────────────────────────────────
st.divider()
st.subheader("Key Weekly Events to Watch")
events = [
    ("Monday",    "FII/DII provisional data, Global market cues (Dow, Nasdaq, Nikkei)"),
    ("Tuesday",   "RBI bulletin releases, Corporate earnings (if season)"),
    ("Wednesday", "US CPI/PPI (monthly), FOMC minutes (when applicable)"),
    ("Thursday",  "NSE Weekly Expiry — rollover activity, India IIP data (monthly)"),
    ("Friday",    "US NFP (first Friday of month), India WPI data, Weekend rollover"),
]
for day, desc in events:
    st.markdown(f"**{day}:** {desc}")

st.info(
    "**Iron Condor timing tip:** Deploy on Monday/Tuesday when IV is stable. "
    "Avoid entering on expiry Thursday — high gamma risk. "
    "Exit at 50% profit or before Thursday morning if profitable."
)
