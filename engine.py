import pandas as pd
import os
import csv
import json
import time

# 1. Trade Log அப்டேட் பண்ண
def log_trade(stock, pnl, mode):
    result = 'WIN' if pnl > 0 else 'LOSS'
    file_exists = os.path.isfile('trade_log.csv')
    
    with open('trade_log.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Stock', 'PnL', 'Result', 'Mode'])
        writer.writerow([stock, pnl, result, mode])

# 2. பேலன்ஸ் செக் பண்ண
def get_balances():
    with open('balances.json', 'r') as f:
        return json.load(f)

# 3. ட்ரேடு எடுக்கும்போது மார்ஜினை கழிக்க
def execute_trade(stock, mode, margin_required):
    balances = get_balances() # இது இப்போ ஒரு Dictionary
    
    if balances[f'{mode}_balance'] >= margin_required:
        balances[f'{mode}_balance'] -= margin_required
        
        with open('balances.json', 'w') as f:
            json.dump(balances, f, indent=4)
        
        return True
    return False    
def add_pnl(mode, pnl):
    balances = get_balances()
    balances[f'{mode}_balance'] += pnl
    balances.to_json('balances.json', orient='columns', indent=4)

def square_off_wife_positions():
    
    with open('wife_positions.csv', 'w') as f:
        f.write("") # Clear file
    print("Wife account squared off for the day!") 

def main_loop():
    while True:
        time.sleep(10) # இது ரொம்ப முக்கியம்!

# --- engine.py-ன் கடைசி பகுதி இப்படி இருக்கட்டும் ---
if __name__ == "__main__":
    print("--- 🚀 Algo Engine Online ---")
    # இங்கதான் உங்க main_loop() இருக்கணும்
    main_loop()