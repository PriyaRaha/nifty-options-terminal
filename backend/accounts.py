"""Multi-account P&L tracker — persists to data/accounts.json."""
import json
import uuid
from pathlib import Path
from datetime import date
from config import ACCOUNTS, LOT_SIZE

DATA_FILE = Path(__file__).parent.parent / "data" / "accounts.json"


def _load() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    base = {
        "accounts": {
            acc["id"]: {
                "name":            acc["name"],
                "initial_capital": acc["initial_capital"],
                "trades":          [],
            }
            for acc in ACCOUNTS
        }
    }
    _save(base)
    return base


def _save(data: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def get_accounts() -> dict:
    return _load()["accounts"]


def add_trade(
    account_id: str,
    strategy: str,
    symbol: str,
    expiry: str,
    lots: int,
    legs: list[dict],         # [{opt, strike, qty, price}]
    premium_per_unit: float,  # net credit (+) or debit (-)
    notes: str = "",
) -> str:
    data = _load()
    trade_id = str(uuid.uuid4())[:8]
    trade = {
        "id":               trade_id,
        "date":             date.today().isoformat(),
        "strategy":         strategy,
        "symbol":           symbol,
        "expiry":           expiry,
        "lots":             lots,
        "legs":             legs,
        "premium_per_unit": premium_per_unit,
        "premium_total":    round(premium_per_unit * LOT_SIZE * lots, 2),
        "status":           "open",
        "close_date":       None,
        "close_premium":    None,
        "pnl":              None,
        "notes":            notes,
    }
    data["accounts"][account_id]["trades"].append(trade)
    _save(data)
    return trade_id


def close_trade(account_id: str, trade_id: str, close_premium: float):
    data = _load()
    for trade in data["accounts"][account_id]["trades"]:
        if trade["id"] == trade_id:
            trade["status"]        = "closed"
            trade["close_date"]    = date.today().isoformat()
            trade["close_premium"] = close_premium
            # For credit strategies: profit = entry credit - exit debit
            entry = trade["premium_per_unit"]
            pnl   = (entry - close_premium) * LOT_SIZE * trade["lots"]
            trade["pnl"] = round(pnl, 2)
            break
    _save(data)


def get_trade_summary(account_id: str) -> dict:
    data   = _load()
    trades = data["accounts"][account_id]["trades"]
    closed = [t for t in trades if t["status"] == "closed"]
    open_  = [t for t in trades if t["status"] == "open"]

    realized_pnl   = sum(t["pnl"] for t in closed if t["pnl"])
    unrealized_est = sum(t["premium_total"] for t in open_)  # max potential if held to expiry
    initial_cap    = data["accounts"][account_id]["initial_capital"]
    roi_pct        = realized_pnl / initial_cap * 100 if initial_cap else 0

    return {
        "total_trades":   len(trades),
        "open_trades":    len(open_),
        "closed_trades":  len(closed),
        "realized_pnl":   round(realized_pnl, 2),
        "unrealized_est": round(unrealized_est, 2),
        "initial_capital": initial_cap,
        "roi_pct":        round(roi_pct, 2),
        "win_rate":       round(
            sum(1 for t in closed if (t["pnl"] or 0) > 0) / max(len(closed), 1) * 100, 1
        ),
    }
