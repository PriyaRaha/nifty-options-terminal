LOT_SIZE = 75            # Nifty 50 lot size (post Oct 2024)
RISK_FREE_RATE = 0.065   # India 10Y G-Sec yield ~6.5%
DEFAULT_LOTS = 2

ACCOUNTS = [
    {"id": "self",    "name": "My Account",       "initial_capital": 1000000},
    {"id": "husband", "name": "Husband's Account", "initial_capital": 1000000},
    {"id": "father",  "name": "Father's Account",  "initial_capital": 700000},
]

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

NEWS_RSS_FEEDS = [
    {
        "name": "ET Markets",
        "url": "https://economictimes.indiatimes.com/markets/rss.cms",
    },
    {
        "name": "Business Standard",
        "url": "https://www.business-standard.com/rss/markets-106.rss",
    },
    {
        "name": "Mint Markets",
        "url": "https://www.livemint.com/rss/markets",
    },
]

TARGET_RETURN_PCT = 18   # annual target before tax
THETA_TARGET_DAYS = 7    # Weekly expiry focus

STRATEGY_LIST = [
    "Iron Condor",
    "Skewed Iron Condor",
    "Short Straddle",
    "Long Straddle",
    "Short Strangle",
    "Long Strangle",
    "Iron Butterfly",
    "Bull Call Spread",
    "Bear Put Spread",
    "Bull Put Spread (Credit)",
    "Bear Call Spread (Credit)",
    "Jade Lizard",
    "Broken Wing Butterfly",
    "Calendar Spread",
    "Ratio Spread",
]
