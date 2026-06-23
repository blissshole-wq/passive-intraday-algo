import pandas as pd
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
    pd.DataFrame(positions_list).to_csv(DB_FILE, index=False)

def get_advanced_metrics(watchlist):
    # watchlist என்பது ஒரு லிஸ்ட் அல்லது டேட்டாஃப்ரேம் என்று வைத்துக்கொள்வோம்
    # இப்போதைக்கு நாம் DB_FILE-ல் இருந்து டேட்டாவை வாசிப்போம்
    try:
        df = pd.read_csv('positions_db.csv')
        if not df.empty:
            df['PnL_Rs'] = (df['LTP'] - df['Buy_Price']) * df['Quantity']
            df['PnL_Percent'] = (df['PnL_Rs'] / (df['Buy_Price'] * df['Quantity'])) * 100
            
            return df[['Stock', 'PnL_Rs', 'PnL_Percent']] # இதைத்தான் dashboard.py எடுத்துக்கொள்ளும்
        
    except Exception as e:
        print(f"Error in metrics calculation: {e}")
        
    return pd.DataFrame() # பிழை இருந்தால் காலி டேட்டா

# 5. மார்க்கெட் க்ளோஸ் டைம் செக் - Main Loop
def main_loop():
    print("--- 🚀 Algo Engine Online ---")
    while True:  # இங்க லூப் கண்டிப்பா வேணும்!
        try:
            print("Loop is running... Saving data to CSV...")
            # டெஸ்டிங்க்காக டேட்டா
            test_positions = [{"Stock": "RELIANCE", "LTP": 1323.0}]
            save_positions(test_positions)
            
            # லாக் டெஸ்ட் (உங்களுக்கு தேவைப்பட்டால் மட்டும் இதை uncomment பண்ணுங்க)
            # log_trade("RELIANCE", 500, "husband")
            
            time.sleep(10) # 10 வினாடி ஒருமுறை ரன் ஆகும்
        except Exception as e:
            print(f"Error in loop: {e}")
            break
            
if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nShutdown requested...exiting")
    finally:
        print("Engine stopped.")