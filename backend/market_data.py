import requests
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
import streamlit as st
import time
from datetime import datetime, timedelta
import pytz

from config import NSE_HEADERS, NEWS_RSS_FEEDS


IST = pytz.timezone("Asia/Kolkata")

# ── NSE session ──────────────────────────────────────────────────────────────

def _new_nse_session() -> requests.Session:
    s = requests.Session()
    try:
        s.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=8)
        time.sleep(0.5)
    except Exception:
        pass
    return s


@st.cache_resource(ttl=300)
def get_nse_session():
    return _new_nse_session()


def _nse_get(path: str) -> dict | None:
    session = get_nse_session()
    url = f"https://www.nseindia.com/api{path}"
    try:
        r = session.get(url, headers=NSE_HEADERS, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception:
        # Refresh session and retry once
        try:
            new_s = _new_nse_session()
            r = new_s.get(url, headers=NSE_HEADERS, timeout=12)
            return r.json()
        except Exception:
            return None


# ── Spot prices ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_nifty_spot() -> dict:
    """Returns current Nifty 50 price + change."""
    try:
        ticker = yf.Ticker("^NSEI")
        info = ticker.fast_info
        price = float(info.last_price)
        prev  = float(info.previous_close)
        chng  = price - prev
        pct   = chng / prev * 100
        return {"price": price, "change": chng, "change_pct": pct, "prev_close": prev}
    except Exception:
        return {"price": 0, "change": 0, "change_pct": 0, "prev_close": 0}


@st.cache_data(ttl=60)
def get_india_vix() -> dict:
    try:
        ticker = yf.Ticker("^INDIAVIX")
        info = ticker.fast_info
        price = float(info.last_price)
        prev  = float(info.previous_close)
        chng  = price - prev
        pct   = chng / prev * 100
        return {"price": price, "change": chng, "change_pct": pct}
    except Exception:
        return {"price": 0, "change": 0, "change_pct": 0}


@st.cache_data(ttl=60)
def get_bank_nifty() -> dict:
    try:
        ticker = yf.Ticker("^NSEBANK")
        info = ticker.fast_info
        price = float(info.last_price)
        prev  = float(info.previous_close)
        chng  = price - prev
        pct   = chng / prev * 100
        return {"price": price, "change": chng, "change_pct": pct}
    except Exception:
        return {"price": 0, "change": 0, "change_pct": 0}


@st.cache_data(ttl=60)
def get_sensex() -> dict:
    try:
        ticker = yf.Ticker("^BSESN")
        info = ticker.fast_info
        price = float(info.last_price)
        prev  = float(info.previous_close)
        chng  = price - prev
        pct   = chng / prev * 100
        return {"price": price, "change": chng, "change_pct": pct}
    except Exception:
        return {"price": 0, "change": 0, "change_pct": 0}


def get_gift_nifty() -> dict:
    """
    Gift Nifty trades on NSE IFSC and is not available via free APIs.
    We return None so the UI shows a subscription notice.
    """
    return None


# ── Historical data ───────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_nifty_history(period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    try:
        df = yf.download("^NSEI", period=period, interval=interval,
                         progress=False, auto_adjust=True)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.index = pd.to_datetime(df.index)
        return df.dropna()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_vix_history(period: str = "3mo") -> pd.DataFrame:
    try:
        df = yf.download("^INDIAVIX", period=period, interval="1d",
                         progress=False, auto_adjust=True)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        return df.dropna()
    except Exception:
        return pd.DataFrame()


# ── Options chain ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def get_options_chain(symbol: str = "NIFTY", expiry: str | None = None) -> dict:
    """
    Returns dict with keys:
      - df: DataFrame with one row per strike
      - expiry_dates: list of available expiry strings
      - underlying: spot price from NSE
      - timestamp: data timestamp
    """
    data = _nse_get(f"/option-chain-indices?symbol={symbol}")
    if not data:
        return {"df": pd.DataFrame(), "expiry_dates": [], "underlying": 0, "timestamp": ""}

    records     = data.get("records", {})
    all_data    = records.get("data", [])
    expiries    = records.get("expiryDates", [])
    underlying  = records.get("underlyingValue", 0)
    timestamp   = records.get("timestamp", "")

    target_expiry = expiry or (expiries[0] if expiries else None)
    rows = []
    for item in all_data:
        if item.get("expiryDate") != target_expiry:
            continue
        row = {"strikePrice": item["strikePrice"]}
        for side in ("CE", "PE"):
            d = item.get(side, {})
            row[f"{side}_OI"]         = d.get("openInterest", 0)
            row[f"{side}_chngOI"]     = d.get("changeinOpenInterest", 0)
            row[f"{side}_volume"]     = d.get("totalTradedVolume", 0)
            row[f"{side}_IV"]         = d.get("impliedVolatility", 0)
            row[f"{side}_LTP"]        = d.get("lastPrice", 0)
            row[f"{side}_change"]     = d.get("change", 0)
            row[f"{side}_bid"]        = d.get("bidprice", 0)
            row[f"{side}_ask"]        = d.get("askPrice", 0)
        rows.append(row)

    df = pd.DataFrame(rows).sort_values("strikePrice").reset_index(drop=True)
    return {
        "df": df,
        "expiry_dates": expiries,
        "underlying": underlying,
        "timestamp": timestamp,
    }


# ── Market schedule ───────────────────────────────────────────────────────────

def next_weekly_expiry() -> datetime:
    """Next Thursday (NSE weekly expiry day) in IST."""
    now = datetime.now(IST)
    days_ahead = (3 - now.weekday()) % 7  # 3 = Thursday
    if days_ahead == 0 and now.hour >= 15:
        days_ahead = 7
    expiry = now + timedelta(days=days_ahead)
    return expiry.replace(hour=15, minute=30, second=0, microsecond=0)


def time_to_expiry_days() -> float:
    """Trading days (calendar) until next expiry, including partial today."""
    now    = datetime.now(IST)
    expiry = next_weekly_expiry()
    delta  = expiry - now
    return max(delta.total_seconds() / 86400, 0)


def is_market_open() -> bool:
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    market_open  = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    return market_open <= now <= market_close


# ── News feed ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_market_news(max_per_feed: int = 8) -> list[dict]:
    articles = []
    for feed_cfg in NEWS_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            for entry in feed.entries[:max_per_feed]:
                articles.append({
                    "source":  feed_cfg["name"],
                    "title":   entry.get("title", ""),
                    "summary": entry.get("summary", "")[:300],
                    "link":    entry.get("link", ""),
                    "published": entry.get("published", ""),
                })
        except Exception:
            continue
    return articles
