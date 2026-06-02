"""Black-Scholes Greeks calculator for Indian options."""
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


def _d1(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return 0.0
    return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))


def _d2(S, K, T, r, sigma):
    return _d1(S, K, T, r, sigma) - sigma * np.sqrt(T)


def call_price(S, K, T, r, sigma):
    if T <= 0:
        return max(S - K, 0.0)
    d1, d2 = _d1(S, K, T, r, sigma), _d2(S, K, T, r, sigma)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


def put_price(S, K, T, r, sigma):
    if T <= 0:
        return max(K - S, 0.0)
    d1, d2 = _d1(S, K, T, r, sigma), _d2(S, K, T, r, sigma)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def delta(S, K, T, r, sigma, opt="CE"):
    if T <= 0:
        if opt == "CE":
            return 1.0 if S > K else 0.0
        return -1.0 if S < K else 0.0
    d1 = _d1(S, K, T, r, sigma)
    return norm.cdf(d1) if opt == "CE" else norm.cdf(d1) - 1.0


def gamma(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))


def theta(S, K, T, r, sigma, opt="CE"):
    """Per-day theta (divided by 365)."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
    if opt == "CE":
        return (term1 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        return (term1 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365


def vega(S, K, T, r, sigma):
    """Vega per 1% change in IV."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    return S * norm.pdf(d1) * np.sqrt(T) / 100


def rho(S, K, T, r, sigma, opt="CE"):
    """Rho per 1% change in risk-free rate."""
    if T <= 0:
        return 0.0
    d2 = _d2(S, K, T, r, sigma)
    if opt == "CE":
        return K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        return -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100


def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float, opt: str = "CE") -> dict:
    """
    Full Greeks for one leg.
    T in years, sigma as decimal (0.15 = 15%), r as decimal.
    """
    price_fn = call_price if opt == "CE" else put_price
    return {
        "price": round(price_fn(S, K, T, r, sigma), 2),
        "delta": round(delta(S, K, T, r, sigma, opt), 4),
        "gamma": round(gamma(S, K, T, r, sigma), 6),
        "theta": round(theta(S, K, T, r, sigma, opt), 2),
        "vega":  round(vega(S, K, T, r, sigma), 2),
        "rho":   round(rho(S, K, T, r, sigma, opt), 2),
    }


def implied_volatility(market_price: float, S: float, K: float, T: float, r: float, opt: str = "CE") -> float:
    """Newton-Raphson IV solver. Returns IV as decimal (0.15 = 15%)."""
    if T <= 0 or market_price <= 0:
        return 0.0
    intrinsic = max(S - K, 0) if opt == "CE" else max(K - S, 0)
    if market_price <= intrinsic:
        return 0.0
    price_fn = call_price if opt == "CE" else put_price
    try:
        iv = brentq(lambda s: price_fn(S, K, T, r, s) - market_price, 1e-6, 5.0, xtol=1e-6)
        return round(iv, 4)
    except Exception:
        return 0.0


def position_greeks(legs: list[dict]) -> dict:
    """
    Aggregate Greeks for a multi-leg strategy.
    Each leg dict: {S, K, T, r, sigma, opt, qty}  where qty is signed (+1 long, -1 short).
    """
    agg = {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0, "net_premium": 0}
    for leg in legs:
        g = calculate_greeks(leg["S"], leg["K"], leg["T"], leg["r"], leg["sigma"], leg["opt"])
        qty = leg["qty"]
        agg["delta"]       += qty * g["delta"]
        agg["gamma"]       += qty * g["gamma"]
        agg["theta"]       += qty * g["theta"]
        agg["vega"]        += qty * g["vega"]
        agg["rho"]         += qty * g["rho"]
        agg["net_premium"] += qty * g["price"]  # positive = credit received
    return {k: round(v, 4) for k, v in agg.items()}
