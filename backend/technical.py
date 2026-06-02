"""Technical indicators and OI-based signals."""
import numpy as np
import pandas as pd


# ── Price-based indicators ────────────────────────────────────────────────────

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def macd(series: pd.Series, fast=12, slow=26, signal=9) -> pd.DataFrame:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({
        "macd":     macd_line,
        "signal":   signal_line,
        "hist":     macd_line - signal_line,
    })


def bollinger_bands(series: pd.Series, period=20, std_dev=2) -> pd.DataFrame:
    sma   = series.rolling(period).mean()
    std   = series.rolling(period).std()
    return pd.DataFrame({
        "upper":  sma + std_dev * std,
        "middle": sma,
        "lower":  sma - std_dev * std,
        "pct_b":  (series - (sma - std_dev * std)) / (2 * std_dev * std),
    })


def atr(df: pd.DataFrame, period=14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def supertrend(df: pd.DataFrame, period=10, multiplier=3) -> pd.Series:
    _atr = atr(df, period)
    hl2 = (df["High"] + df["Low"]) / 2
    upper = hl2 + multiplier * _atr
    lower = hl2 - multiplier * _atr
    supertrend = pd.Series(index=df.index, dtype=float)
    for i in range(1, len(df)):
        close = df["Close"].iloc[i]
        if close > upper.iloc[i - 1]:
            supertrend.iloc[i] = lower.iloc[i]
        elif close < lower.iloc[i - 1]:
            supertrend.iloc[i] = upper.iloc[i]
        else:
            supertrend.iloc[i] = supertrend.iloc[i - 1]
    return supertrend


def iv_rank(iv_series: pd.Series) -> float:
    """IV Rank = (current - 52w low) / (52w high - 52w low) × 100."""
    if iv_series.empty:
        return 0.0
    curr = iv_series.iloc[-1]
    lo   = iv_series.min()
    hi   = iv_series.max()
    if hi == lo:
        return 50.0
    return round((curr - lo) / (hi - lo) * 100, 1)


def iv_percentile(iv_series: pd.Series) -> float:
    """% of days in past year where IV was below current IV."""
    if len(iv_series) < 2:
        return 50.0
    curr = iv_series.iloc[-1]
    return round((iv_series < curr).mean() * 100, 1)


# ── OI-based signals ──────────────────────────────────────────────────────────

def pcr(df: pd.DataFrame) -> float:
    """Put-Call Ratio by OI."""
    if df.empty:
        return 1.0
    total_ce_oi = df["CE_OI"].sum()
    total_pe_oi = df["PE_OI"].sum()
    if total_ce_oi == 0:
        return 1.0
    return round(total_pe_oi / total_ce_oi, 2)


def pcr_volume(df: pd.DataFrame) -> float:
    """Put-Call Ratio by volume."""
    if df.empty:
        return 1.0
    ce_vol = df["CE_volume"].sum()
    pe_vol = df["PE_volume"].sum()
    if ce_vol == 0:
        return 1.0
    return round(pe_vol / ce_vol, 2)


def max_pain(df: pd.DataFrame) -> float:
    """Strike where total ITM option value is minimum (max pain for buyers)."""
    if df.empty:
        return 0.0
    strikes = df["strikePrice"].tolist()
    pain_map = {}
    for K in strikes:
        call_pain = sum(
            max(K - s, 0) * df.loc[df["strikePrice"] == s, "CE_OI"].values[0]
            for s in strikes
        )
        put_pain = sum(
            max(s - K, 0) * df.loc[df["strikePrice"] == s, "PE_OI"].values[0]
            for s in strikes
        )
        pain_map[K] = call_pain + put_pain
    return min(pain_map, key=pain_map.get)


def oi_buildup_signal(df: pd.DataFrame, spot: float) -> dict:
    """
    Classify OI buildup into Long Buildup / Short Buildup / etc.
    Uses price change + OI change as proxies.
    """
    atm_range = 0.05 * spot
    near = df[(df["strikePrice"] >= spot - atm_range) &
              (df["strikePrice"] <= spot + atm_range)]
    if near.empty:
        return {"calls": "N/A", "puts": "N/A"}

    ce_oi_chng = near["CE_chngOI"].sum()
    pe_oi_chng = near["PE_chngOI"].sum()

    ce_signal = (
        "Long Buildup"   if ce_oi_chng > 0 else
        "Short Covering" if ce_oi_chng < 0 else
        "Neutral"
    )
    pe_signal = (
        "Long Buildup"   if pe_oi_chng > 0 else
        "Short Covering" if pe_oi_chng < 0 else
        "Neutral"
    )
    return {"calls": ce_signal, "puts": pe_signal}


def support_resistance_from_oi(df: pd.DataFrame, spot: float, n=3) -> dict:
    """Top n call/put OI strikes act as resistance/support."""
    if df.empty:
        return {"resistance": [], "support": []}
    above = df[df["strikePrice"] > spot].nlargest(n, "CE_OI")["strikePrice"].tolist()
    below = df[df["strikePrice"] < spot].nlargest(n, "PE_OI")["strikePrice"].tolist()
    return {"resistance": sorted(above), "support": sorted(below, reverse=True)}


def interpret_signals(rsi_val: float, pcr_val: float, vix_val: float) -> str:
    """Simple rule-based market view for options selling."""
    signals = []
    if rsi_val > 70:
        signals.append("RSI overbought — watch for reversal")
    elif rsi_val < 30:
        signals.append("RSI oversold — watch for bounce")
    else:
        signals.append(f"RSI neutral ({rsi_val:.0f})")

    if pcr_val > 1.3:
        signals.append("PCR high — bullish contrarian signal")
    elif pcr_val < 0.7:
        signals.append("PCR low — bearish contrarian signal")
    else:
        signals.append(f"PCR neutral ({pcr_val:.2f})")

    if vix_val > 20:
        signals.append("VIX elevated — good for premium selling")
    elif vix_val < 12:
        signals.append("VIX low — premium selling less attractive")
    else:
        signals.append(f"VIX normal ({vix_val:.1f})")

    return " | ".join(signals)
