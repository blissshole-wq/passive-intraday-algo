import csv
import datetime as dt
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

BALANCES_FILE = "balances.json"
LOG_FILE = "trade_log.csv"
DB_FILE = "positions_db.csv"

WATCHLIST = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "ICICIBANK",
    "INFY",
    "ITC",
    "HINDUNILVR",
    "LT",
    "SBIN",
    "BHARTIARTL",
]

EXPECTED_COLUMNS = [
    "Stock",
    "LTP",
    "Buy_Price",
    "Quantity",
    "Husband_Status",
    "H_Entry",
    "H_PnL_Rs",
    "Wife_Status",
    "W_Entry",
    "W_PnL_Rs",
]


def default_balances() -> Dict[str, float]:
    return {"husband_balance": 50000.0, "wife_balance": 50000.0, "total_capital": 100000.0}


def get_balances() -> Dict[str, float]:
    if not os.path.exists(BALANCES_FILE):
        save_balances(default_balances())
        return default_balances()

    with open(BALANCES_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_balances(data: Dict[str, float]) -> None:
    with open(BALANCES_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4)


def update_pnl(mode: str, pnl: float) -> None:
    if mode not in {"husband", "wife"}:
        raise ValueError("mode must be 'husband' or 'wife'")

    balances = get_balances()
    balances[f"{mode}_balance"] += pnl
    balances["total_capital"] = balances.get("husband_balance", 50000.0) + balances.get("wife_balance", 50000.0)
    save_balances(balances)
    print(f"💰 {mode.capitalize()} PnL Updated: {pnl}. New Balance: {balances[f'{mode}_balance']}")


def log_trade(stock: str, pnl: float, mode: str) -> None:
    result = "WIN" if pnl > 0 else "LOSS"
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not file_exists:
            writer.writerow(["Timestamp", "Stock", "PnL", "Result", "Mode"])
        writer.writerow([dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stock, pnl, result, mode])
    update_pnl(mode, pnl)


def save_positions(positions_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    with open(DB_FILE, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        for row in positions_list:
            normalized: Dict[str, Any] = {}
            for col in EXPECTED_COLUMNS:
                value = row.get(col, 0)
                if isinstance(value, str):
                    normalized[col] = value
                elif col.endswith(("Price", "PnL_Rs", "LTP")):
                    normalized[col] = float(value)
                else:
                    normalized[col] = int(value)
            writer.writerow(normalized)
    return positions_list


def get_advanced_metrics() -> List[Dict[str, Any]]:
    try:
        if not os.path.exists(DB_FILE):
            return []

        with open(DB_FILE, "r", newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        for row in rows:
            try:
                row["LTP"] = float(row.get("LTP", 0))
                row["Buy_Price"] = float(row.get("Buy_Price", 0))
                row["Quantity"] = int(float(row.get("Quantity", 0)))
            except Exception:
                row["LTP"] = 0.0
                row["Buy_Price"] = 0.0
                row["Quantity"] = 0
            row["PnL_Rs"] = (row["LTP"] - row["Buy_Price"]) * row["Quantity"]
        return rows
    except Exception as exc:
        print(f"Error in metrics calculation: {exc}")
        return []


def get_ltp(ticker: str) -> float:
    sample_prices = {
        "RELIANCE": 1300.0,
        "TCS": 2100.0,
        "HDFCBANK": 800.0,
        "ICICIBANK": 1350.0,
        "INFY": 1050.0,
        "ITC": 290.0,
        "HINDUNILVR": 2150.0,
        "LT": 4100.0,
        "SBIN": 1000.0,
        "BHARTIARTL": 1800.0,
    }
    return sample_prices.get(ticker, 100.0)


def build_positions() -> List[Dict[str, Any]]:
    positions: List[Dict[str, Any]] = []
    for ticker in WATCHLIST:
        price = get_ltp(ticker)
        positions.append(
            {
                "Stock": ticker,
                "LTP": price,
                "Buy_Price": 1000.0,
                "Quantity": 1,
                "Husband_Status": "IDLE",
                "H_Entry": 0.0,
                "H_PnL_Rs": 0.0,
                "Wife_Status": "IDLE",
                "W_Entry": 0.0,
                "W_PnL_Rs": 0.0,
            }
        )
    return positions


def main_loop(interval_seconds: int = 10, max_iterations: Optional[int] = None) -> None:
    iteration = 0
    print("--- Algo Engine Online ---")

    while max_iterations is None or iteration < max_iterations:
        try:
            positions_list = build_positions()
            save_positions(positions_list)
            print(f"Data saved successfully... iteration={iteration + 1}")
            iteration += 1
            if max_iterations is not None and iteration >= max_iterations:
                break
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("Stopped by user.")
            break
        except Exception as exc:
            print(f"Error in loop: {exc}")
            break


if __name__ == "__main__":
    max_iterations: Optional[int] = None
    if len(sys.argv) > 1:
        try:
            max_iterations = int(sys.argv[1])
        except ValueError:
            print("Usage: python engine_clean.py [max_iterations]")
            sys.exit(1)

    main_loop(max_iterations=max_iterations)
