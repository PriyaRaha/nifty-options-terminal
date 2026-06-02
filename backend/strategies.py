"""
All options strategies with payoff diagrams and Greeks.
Each strategy function returns a StrategyResult.
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from backend.greeks import calculate_greeks, position_greeks, call_price, put_price
from config import LOT_SIZE, RISK_FREE_RATE


@dataclass
class Leg:
    opt: str        # "CE" or "PE"
    strike: float
    qty: int        # +1 long, -1 short (per lot)
    price: float    # premium per unit


@dataclass
class StrategyResult:
    name: str
    legs: list[Leg]
    net_premium: float        # per lot, positive = credit
    max_profit: float         # per lot
    max_loss: float           # per lot (positive = loss amount)
    breakevens: list[float]
    greeks: dict
    payoff_df: pd.DataFrame   # columns: spot, pnl_per_lot, pnl_total
    notes: str = ""
    lots: int = 1

    def pnl_at_expiry(self, spot: float) -> float:
        """P&L per lot at expiry."""
        pnl = 0.0
        for leg in self.legs:
            intrinsic = max(spot - leg.strike, 0) if leg.opt == "CE" else max(leg.strike - spot, 0)
            pnl += leg.qty * (intrinsic - leg.price)
        return pnl * LOT_SIZE


def _payoff_series(legs: list[Leg], spot_center: float, width_pct=0.12) -> pd.DataFrame:
    lo = spot_center * (1 - width_pct)
    hi = spot_center * (1 + width_pct)
    spots = np.linspace(lo, hi, 300)
    pnls = []
    for s in spots:
        pnl = sum(
            leg.qty * ((max(s - leg.strike, 0) if leg.opt == "CE" else max(leg.strike - s, 0)) - leg.price)
            for leg in legs
        )
        pnls.append(pnl * LOT_SIZE)
    return pd.DataFrame({"spot": spots, "pnl_per_lot": pnls})


def _legs_to_position(S, T, r, legs: list[Leg]) -> list[dict]:
    return [
        {"S": S, "K": leg.strike, "T": T, "r": r,
         "sigma": calculate_greeks(S, leg.strike, T, r, 0.15, leg.opt)["price"],  # placeholder
         "opt": leg.opt, "qty": leg.qty}
        for leg in legs
    ]


def _price(S, K, T, r, iv, opt):
    """Option price from IV (as %, e.g. 15.0 = 15%)."""
    sigma = iv / 100
    g = calculate_greeks(S, K, T, r, sigma, opt)
    return g["price"], g


def _greeks_from_legs(S, T, r, legs_with_iv: list[tuple]) -> dict:
    """legs_with_iv: list of (Leg, iv_pct)."""
    pos = []
    for leg, iv in legs_with_iv:
        pos.append({"S": S, "K": leg.strike, "T": T, "r": r,
                    "sigma": iv / 100, "opt": leg.opt, "qty": leg.qty})
    return position_greeks(pos)


# ─────────────────────────────────────────────────────────────────────────────
# Iron Condor
# ─────────────────────────────────────────────────────────────────────────────

def iron_condor(
    S: float, T: float,
    call_short_K: float, call_long_K: float,
    put_short_K: float, put_long_K: float,
    call_iv: float = 15.0, put_iv: float = 16.0,
    r: float = RISK_FREE_RATE, lots: int = 1,
) -> StrategyResult:
    """
    Standard Iron Condor:
      Short Call @ call_short_K  +  Long Call @ call_long_K  (bear call spread)
      Short Put  @ put_short_K   +  Long Put  @ put_long_K   (bull put spread)
    """
    c_sc, _ = _price(S, call_short_K, T, r, call_iv, "CE")
    c_lc, _ = _price(S, call_long_K,  T, r, call_iv, "CE")
    p_sp, _ = _price(S, put_short_K,  T, r, put_iv,  "PE")
    p_lp, _ = _price(S, put_long_K,   T, r, put_iv,  "PE")

    call_credit = c_sc - c_lc
    put_credit  = p_sp - p_lp
    net_credit  = call_credit + put_credit

    legs = [
        Leg("CE", call_short_K, -1, c_sc),
        Leg("CE", call_long_K,  +1, c_lc),
        Leg("PE", put_short_K,  -1, p_sp),
        Leg("PE", put_long_K,   +1, p_lp),
    ]

    call_width = call_long_K - call_short_K
    put_width  = put_short_K - put_long_K
    max_loss   = max(call_width, put_width) - net_credit

    greeks = _greeks_from_legs(S, T, r, [
        (legs[0], call_iv), (legs[1], call_iv),
        (legs[2], put_iv),  (legs[3], put_iv),
    ])

    return StrategyResult(
        name="Iron Condor",
        legs=legs,
        net_premium=net_credit,
        max_profit=net_credit,
        max_loss=max_loss,
        breakevens=[put_short_K - net_credit, call_short_K + net_credit],
        greeks=greeks,
        payoff_df=_payoff_series(legs, S),
        notes=(f"Credit: ₹{net_credit:.2f}/unit | "
               f"Max Loss: ₹{max_loss:.2f}/unit | "
               f"Width: {call_width:.0f}c / {put_width:.0f}p"),
        lots=lots,
    )


def delta_neutral_iron_condor(
    S: float, T: float,
    wing_width: float = 200,
    otm_offset: float = 150,
    call_iv: float = 15.0, put_iv: float = 16.0,
    r: float = RISK_FREE_RATE, lots: int = 1,
) -> StrategyResult:
    """
    Builds a delta-near-neutral IC by iterating on call/put offsets.
    Puts are typically slightly closer to ATM to offset the skew bias.
    """
    # Start symmetric, then nudge put side out to reduce positive delta from put side
    best = None
    best_delta = 999
    for put_adj in range(-50, 51, 10):
        csk = round(S / 50) * 50 + otm_offset
        clk = csk + wing_width
        psk = round(S / 50) * 50 - otm_offset + put_adj
        plk = psk - wing_width
        if plk <= 0:
            continue
        result = iron_condor(S, T, csk, clk, psk, plk, call_iv, put_iv, r, lots)
        net_delta = abs(result.greeks["delta"])
        if net_delta < best_delta:
            best_delta = net_delta
            best = result
    if best:
        best.name = "Delta-Neutral Iron Condor"
        best.notes += f" | Net Δ ≈ {best.greeks['delta']:.3f}"
    return best


def skewed_iron_condor(
    S: float, T: float,
    call_short_K: float, call_long_K: float,
    put_short_K: float, put_long_K: float,
    call_iv: float = 15.0, put_iv: float = 16.0,
    r: float = RISK_FREE_RATE, lots: int = 1,
    bias: str = "neutral",          # "bullish" | "bearish" | "neutral"
) -> StrategyResult:
    """
    Skewed Iron Condor — adjusts widths based on market bias.
    Bullish: wider put spread (collect more put premium, accept more downside risk).
    Bearish: wider call spread (collect more call premium, accept more upside risk).
    """
    result = iron_condor(S, T, call_short_K, call_long_K,
                         put_short_K, put_long_K, call_iv, put_iv, r, lots)
    call_w = call_long_K - call_short_K
    put_w  = put_short_K - put_long_K
    result.name = f"Skewed Iron Condor ({bias})"
    result.notes += (f" | Bias: {bias} | Call width {call_w:.0f} / Put width {put_w:.0f}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Straddles & Strangles
# ─────────────────────────────────────────────────────────────────────────────

def short_straddle(S, T, atm_iv=15.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    K = round(S / 50) * 50
    cp, _ = _price(S, K, T, r, atm_iv, "CE")
    pp, _ = _price(S, K, T, r, atm_iv, "PE")
    credit = cp + pp
    legs = [Leg("CE", K, -1, cp), Leg("PE", K, -1, pp)]
    greeks = _greeks_from_legs(S, T, r, [(legs[0], atm_iv), (legs[1], atm_iv)])
    return StrategyResult(
        name="Short Straddle", legs=legs,
        net_premium=credit, max_profit=credit, max_loss=float("inf"),
        breakevens=[K - credit, K + credit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Credit: ₹{credit:.2f} | BEs: {K-credit:.0f} / {K+credit:.0f}", lots=lots,
    )


def long_straddle(S, T, atm_iv=15.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    K = round(S / 50) * 50
    cp, _ = _price(S, K, T, r, atm_iv, "CE")
    pp, _ = _price(S, K, T, r, atm_iv, "PE")
    debit = cp + pp
    legs = [Leg("CE", K, +1, cp), Leg("PE", K, +1, pp)]
    greeks = _greeks_from_legs(S, T, r, [(legs[0], atm_iv), (legs[1], atm_iv)])
    return StrategyResult(
        name="Long Straddle", legs=legs,
        net_premium=-debit, max_profit=float("inf"), max_loss=debit,
        breakevens=[K - debit, K + debit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Debit: ₹{debit:.2f} | BEs: {K-debit:.0f} / {K+debit:.0f}", lots=lots,
    )


def short_strangle(S, T, call_K, put_K, call_iv=14.0, put_iv=16.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    cp, _ = _price(S, call_K, T, r, call_iv, "CE")
    pp, _ = _price(S, put_K,  T, r, put_iv,  "PE")
    credit = cp + pp
    legs = [Leg("CE", call_K, -1, cp), Leg("PE", put_K, -1, pp)]
    greeks = _greeks_from_legs(S, T, r, [(legs[0], call_iv), (legs[1], put_iv)])
    return StrategyResult(
        name="Short Strangle", legs=legs,
        net_premium=credit, max_profit=credit, max_loss=float("inf"),
        breakevens=[put_K - credit, call_K + credit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Credit: ₹{credit:.2f}", lots=lots,
    )


def long_strangle(S, T, call_K, put_K, call_iv=14.0, put_iv=16.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    cp, _ = _price(S, call_K, T, r, call_iv, "CE")
    pp, _ = _price(S, put_K,  T, r, put_iv,  "PE")
    debit = cp + pp
    legs = [Leg("CE", call_K, +1, cp), Leg("PE", put_K, +1, pp)]
    greeks = _greeks_from_legs(S, T, r, [(legs[0], call_iv), (legs[1], put_iv)])
    return StrategyResult(
        name="Long Strangle", legs=legs,
        net_premium=-debit, max_profit=float("inf"), max_loss=debit,
        breakevens=[put_K - debit, call_K + debit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Debit: ₹{debit:.2f}", lots=lots,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Iron Butterfly
# ─────────────────────────────────────────────────────────────────────────────

def iron_butterfly(S, T, wing_width=200, atm_iv=15.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    K_atm = round(S / 50) * 50
    K_lc  = K_atm + wing_width
    K_lp  = K_atm - wing_width
    cp_sc, _ = _price(S, K_atm, T, r, atm_iv, "CE")
    cp_lc, _ = _price(S, K_lc,  T, r, atm_iv, "CE")
    pp_sp, _ = _price(S, K_atm, T, r, atm_iv, "PE")
    pp_lp, _ = _price(S, K_lp,  T, r, atm_iv, "PE")
    credit = cp_sc - cp_lc + pp_sp - pp_lp
    legs = [
        Leg("CE", K_atm, -1, cp_sc), Leg("CE", K_lc, +1, cp_lc),
        Leg("PE", K_atm, -1, pp_sp), Leg("PE", K_lp, +1, pp_lp),
    ]
    greeks = _greeks_from_legs(S, T, r, [(l, atm_iv) for l in legs])
    return StrategyResult(
        name="Iron Butterfly", legs=legs,
        net_premium=credit, max_profit=credit, max_loss=wing_width - credit,
        breakevens=[K_atm - credit, K_atm + credit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Credit: ₹{credit:.2f} | Wing: {wing_width}", lots=lots,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Vertical Spreads
# ─────────────────────────────────────────────────────────────────────────────

def bull_call_spread(S, T, buy_K, sell_K, iv=15.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    buy_p, _ = _price(S, buy_K,  T, r, iv, "CE")
    sel_p, _ = _price(S, sell_K, T, r, iv, "CE")
    debit = buy_p - sel_p
    width = sell_K - buy_K
    legs  = [Leg("CE", buy_K, +1, buy_p), Leg("CE", sell_K, -1, sel_p)]
    greeks = _greeks_from_legs(S, T, r, [(l, iv) for l in legs])
    return StrategyResult(
        name="Bull Call Spread", legs=legs,
        net_premium=-debit, max_profit=width - debit, max_loss=debit,
        breakevens=[buy_K + debit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Debit: ₹{debit:.2f} | Max Profit: ₹{width-debit:.2f}", lots=lots,
    )


def bear_put_spread(S, T, buy_K, sell_K, iv=15.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    buy_p, _ = _price(S, buy_K,  T, r, iv, "PE")
    sel_p, _ = _price(S, sell_K, T, r, iv, "PE")
    debit = buy_p - sel_p
    width = buy_K - sell_K
    legs  = [Leg("PE", buy_K, +1, buy_p), Leg("PE", sell_K, -1, sel_p)]
    greeks = _greeks_from_legs(S, T, r, [(l, iv) for l in legs])
    return StrategyResult(
        name="Bear Put Spread", legs=legs,
        net_premium=-debit, max_profit=width - debit, max_loss=debit,
        breakevens=[buy_K - debit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Debit: ₹{debit:.2f} | Max Profit: ₹{width-debit:.2f}", lots=lots,
    )


def bull_put_spread(S, T, sell_K, buy_K, iv=16.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    """Credit put spread — sell higher strike put, buy lower."""
    sel_p, _ = _price(S, sell_K, T, r, iv, "PE")
    buy_p, _ = _price(S, buy_K,  T, r, iv, "PE")
    credit = sel_p - buy_p
    width  = sell_K - buy_K
    legs   = [Leg("PE", sell_K, -1, sel_p), Leg("PE", buy_K, +1, buy_p)]
    greeks = _greeks_from_legs(S, T, r, [(l, iv) for l in legs])
    return StrategyResult(
        name="Bull Put Spread (Credit)", legs=legs,
        net_premium=credit, max_profit=credit, max_loss=width - credit,
        breakevens=[sell_K - credit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Credit: ₹{credit:.2f} | Max Loss: ₹{width-credit:.2f}", lots=lots,
    )


def bear_call_spread(S, T, sell_K, buy_K, iv=15.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    """Credit call spread — sell lower strike call, buy higher."""
    sel_p, _ = _price(S, sell_K, T, r, iv, "CE")
    buy_p, _ = _price(S, buy_K,  T, r, iv, "CE")
    credit = sel_p - buy_p
    width  = buy_K - sell_K
    legs   = [Leg("CE", sell_K, -1, sel_p), Leg("CE", buy_K, +1, buy_p)]
    greeks = _greeks_from_legs(S, T, r, [(l, iv) for l in legs])
    return StrategyResult(
        name="Bear Call Spread (Credit)", legs=legs,
        net_premium=credit, max_profit=credit, max_loss=width - credit,
        breakevens=[sell_K + credit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Credit: ₹{credit:.2f} | Max Loss: ₹{width-credit:.2f}", lots=lots,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Jade Lizard
# ─────────────────────────────────────────────────────────────────────────────

def jade_lizard(S, T, put_K, call_short_K, call_long_K,
                put_iv=17.0, call_iv=14.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    """
    Sell OTM Put + Bear Call Spread.
    No upside risk if call_spread_credit >= put_premium (total credit > call width).
    """
    pp,  _ = _price(S, put_K,       T, r, put_iv,  "PE")
    csc, _ = _price(S, call_short_K, T, r, call_iv, "CE")
    clc, _ = _price(S, call_long_K,  T, r, call_iv, "CE")
    credit = pp + (csc - clc)
    call_w = call_long_K - call_short_K
    has_upside_risk = credit < call_w
    legs = [
        Leg("PE", put_K,       -1, pp),
        Leg("CE", call_short_K, -1, csc),
        Leg("CE", call_long_K,  +1, clc),
    ]
    greeks = _greeks_from_legs(S, T, r, [
        (legs[0], put_iv), (legs[1], call_iv), (legs[2], call_iv)
    ])
    return StrategyResult(
        name="Jade Lizard", legs=legs,
        net_premium=credit, max_profit=credit,
        max_loss=put_K - credit if not has_upside_risk else max(put_K, call_w) - credit,
        breakevens=[put_K - credit],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=(f"Credit: ₹{credit:.2f} | "
               f"Upside risk: {'YES' if has_upside_risk else 'NO'}"), lots=lots,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Broken Wing Butterfly
# ─────────────────────────────────────────────────────────────────────────────

def broken_wing_butterfly(S, T, atm_K, lower_K, skip_K, iv=15.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    """
    Put BWB: Buy 1 ATM put, Sell 2 lower puts, Buy 1 skip put (further out).
    Net credit or small debit. No risk above ATM.
    """
    p_atm,  _ = _price(S, atm_K,   T, r, iv, "PE")
    p_low,  _ = _price(S, lower_K, T, r, iv, "PE")
    p_skip, _ = _price(S, skip_K,  T, r, iv, "PE")
    net = p_atm - 2 * p_low + p_skip
    legs = [
        Leg("PE", atm_K,   +1, p_atm),
        Leg("PE", lower_K, -2, p_low),
        Leg("PE", skip_K,  +1, p_skip),
    ]
    greeks = _greeks_from_legs(S, T, r, [(l, iv) for l in legs])
    return StrategyResult(
        name="Broken Wing Butterfly (Put)", legs=legs,
        net_premium=-net, max_profit=atm_K - lower_K + net,
        max_loss=lower_K - skip_K - (atm_K - lower_K) - net,
        breakevens=[],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Net: {'Credit' if net > 0 else 'Debit'} ₹{abs(net):.2f}", lots=lots,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Calendar / Ratio
# ─────────────────────────────────────────────────────────────────────────────

def calendar_spread(S, K, T_near, T_far, iv_near=15.0, iv_far=14.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    """Sell near-month, Buy far-month (same strike)."""
    p_near, _ = _price(S, K, T_near, r, iv_near, "CE")
    p_far,  _ = _price(S, K, T_far,  r, iv_far,  "CE")
    debit = p_far - p_near
    legs  = [Leg("CE", K, -1, p_near), Leg("CE", K, +1, p_far)]
    greeks = _greeks_from_legs(S, T_near, r, [(legs[0], iv_near), (legs[1], iv_far)])
    return StrategyResult(
        name="Calendar Spread", legs=legs,
        net_premium=-debit, max_profit=p_near, max_loss=debit,
        breakevens=[],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Debit: ₹{debit:.2f} | Profit from near-month decay", lots=lots,
    )


def ratio_spread(S, T, buy_K, sell_K, ratio=2, iv=15.0, r=RISK_FREE_RATE, lots=1) -> StrategyResult:
    """Buy 1 ATM call, Sell 2 OTM calls (1:2 ratio)."""
    p_buy, _ = _price(S, buy_K,  T, r, iv, "CE")
    p_sel, _ = _price(S, sell_K, T, r, iv, "CE")
    net = p_buy - ratio * p_sel
    legs = [Leg("CE", buy_K, +1, p_buy), Leg("CE", sell_K, -ratio, p_sel)]
    greeks = _greeks_from_legs(S, T, r, [(l, iv) for l in legs])
    return StrategyResult(
        name=f"Ratio Spread (1:{ratio})", legs=legs,
        net_premium=-net, max_profit=(sell_K - buy_K) - net,
        max_loss=float("inf"),
        breakevens=[buy_K + net if net > 0 else buy_K],
        greeks=greeks, payoff_df=_payoff_series(legs, S),
        notes=f"Net: {'Credit' if net < 0 else 'Debit'} ₹{abs(net):.2f} | UNLIMITED upside risk", lots=lots,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Return calculator helpers
# ─────────────────────────────────────────────────────────────────────────────

def expected_return(result: StrategyResult, capital: float, weeks_per_year=48) -> dict:
    """
    Annualised return assuming the strategy is run every week.
    capital: margin deployed per lot.
    """
    per_lot_credit = result.net_premium * LOT_SIZE
    total_credit   = per_lot_credit * result.lots
    weekly_roi     = total_credit / capital if capital > 0 else 0
    annual_roi     = weekly_roi * weeks_per_year
    return {
        "premium_per_lot": round(per_lot_credit, 0),
        "total_premium":   round(total_credit, 0),
        "weekly_roi_pct":  round(weekly_roi * 100, 2),
        "annual_roi_pct":  round(annual_roi * 100, 1),
    }
