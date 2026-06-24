import os
import time
import csv
import json
import datetime

# --- கான்ஃபிகரேஷன் ---
BALANCES_FILE = 'balances.json'
LOG_FILE = 'trade_log.csv'
DB_FILE = "positions_db.csv"

# 1. பேலன்ஸ் ரீட் பண்ண
def get_balances():
    if not os.path.exists(BALANCES_FILE):
        default_data = {"husband_balance": 50000.0, "wife_balance": 50000.0, "total_capital": 100000.0}
        save_balances(default_data)
        return default_data
    with open(BALANCES_FILE, 'r') as f:
        return json.load(f)

# 2. பேலன்ஸ் சேவ் பண்ண
def save_balances(data):
    with open(BALANCES_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# 3. PnL அப்டேட் பண்ண
def update_pnl(mode, pnl):
    balances = get_balances()
    balances[f'{mode}_balance'] += pnl
    balances['total_capital'] = balances.get('husband_balance', 50000) + balances.get('wife_balance', 50000)
    save_balances(balances)
    print(f"💰 {mode.capitalize()} PnL Updated: {pnl}. New Balance: {balances[f'{mode}_balance']}")

# 4. ட்ரேடு லாக் பண்ண
def log_trade(stock, pnl, mode):
    result = 'WIN' if pnl > 0 else 'LOSS'
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Stock', 'PnL', 'Result', 'Mode'])
        writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stock, pnl, result, mode])
    update_pnl(mode, pnl)

def save_positions(positions_list):
    expected_columns = ["Stock", "LTP", "Buy_Price", "Quantity", "Husband_Status", "H_Entry", "H_PnL_Rs", "Wife_Status", "W_Entry", "W_PnL_Rs"]
    with open(DB_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=expected_columns)
        writer.writeheader()
        for row in positions_list:
            normalized = {col: row.get(col, 0.0 if col.endswith(("Price", "PnL_Rs", "LTP")) else 0) for col in expected_columns}
            writer.writerow(normalized)
    return positions_list


def get_advanced_metrics(watchlist):
    try:
        with open(DB_FILE, "r", newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            return []
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
    except Exception as e:
        print(f"Error in metrics calculation: {e}")
        return []

# 5. மார்க்கெட் க்ளோஸ் டைம் செக் - Main Loop
# 1. முதலில் get_ltp பங்க்ஷனைச் சரிபார்க்கவும் (இது விலையைத் தர வேண்டும்)
def get_ltp(ticker):
    prices = {
        'RELIANCE': 1300.0, 'TCS': 2100.0, 'HDFCBANK': 800.0, 
        'ICICIBANK': 1350.0, 'INFY': 1050.0, 'ITC': 290.0, 
        'HINDUNILVR': 2150.0, 'LT': 4100.0, 'SBIN': 1000.0, 'BHARTIARTL': 1800.0
    }
    return prices.get(ticker, 100.0)

# 2. main_loop-ஐ இப்படி மாற்றுங்கள்
def main_loop():
    while True:
        try:
            positions_list = []
            stocks = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "ITC", "HINDUNILVR", "LT", "SBIN", "BHARTIARTL"]

            for ticker in stocks:
                price = get_ltp(ticker)

                stock_data = {
                    'Stock': ticker,
                    'LTP': price,
                    'Buy_Price': 1000.0,
                    'Quantity': 1,
                    'Husband_Status': 'IDLE',
                    'H_Entry': 0.0,
                    'H_PnL_Rs': 0.0,
                    'Wife_Status': 'IDLE',
                    'W_Entry': 0.0,
                    'W_PnL_Rs': 0.0
                }
                positions_list.append(stock_data)

            save_positions(positions_list)
            time.sleep(10)
        except Exception as e:
            print(f"Error: {e}")
            break
                        
if __name__ == "__main__":
    main_loop()