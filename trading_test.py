import yfinance as yf
import xlwings as xw
import time
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURATION ---
WATCHLIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
             "BHARTIARTL.NS", "SBIN.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS"]

SL_PCT = 0.01      # 1% Stop Loss
TARGET_PCT = 0.02  # 2% Target
TRAIL_PCT = 0.005  # 0.5% Trailing

# --- 2. SETUP ---
try:
    wb = xw.books.active
    sheet = wb.sheets[0]
except:
    wb = xw.Book()
    sheet = wb.sheets[0]

HEADERS = ["Stock", "LTP", "EMA-20", "RSI-14", "Husband Status", "H_Entry", "H_PnL(Rs)", "H_PnL(%)", 
           "Wife Status", "W_Entry", "W_PnL(Rs)", "W_PnL(%)", "Combined PnL", "Time"]

portfolio = {t: {"h_entry": 0, "h_status": "IDLE", "h_sl": 0, "h_tgt": 0,
                 "w_entry": 0, "w_status": "IDLE", "w_sl": 0, "w_tgt": 0} for t in WATCHLIST}

def get_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.clip(lower=0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs.iloc[-1]))

print("🚀 Engine Active: SL/Target/Trailing Logic Enabled...")

while True:
    try:
        report_data = []
        for ticker in WATCHLIST:
            hist = yf.Ticker(ticker).history(period="1mo", interval="1d")
            if hist.empty: continue
            
            price = float(hist['Close'].iloc[-1])
            ema = float(hist['Close'].ewm(span=20, adjust=False).mean().iloc[-1])
            rsi = get_rsi(hist['Close'])
            
            p = portfolio[ticker]
            
            # HUSBAND LOGIC (EMA)
            if p["h_status"] == "IDLE" and price > ema:
                p.update({"h_entry": price, "h_status": "BOUGHT", "h_sl": price*(1-SL_PCT), "h_tgt": price*(1+TARGET_PCT)})
            elif p["h_status"] == "BOUGHT":
                if price > p["h_entry"] * (1 + TRAIL_PCT): p["h_sl"] = price * (1 - TRAIL_PCT) # Trailing
                if price <= p["h_sl"] or price >= p["h_tgt"]: p["h_status"] = "IDLE" # Exit
            
            # WIFE LOGIC (RSI)
            if p["w_status"] == "IDLE" and rsi < 45:
                p.update({"w_entry": price, "w_status": "BOUGHT", "w_sl": price*(1-SL_PCT), "w_tgt": price*(1+TARGET_PCT)})
            elif p["w_status"] == "BOUGHT":
                if price <= p["w_sl"] or price >= p["w_tgt"]: p["w_status"] = "IDLE" # Exit
            
            # Calculations
            h_rs = (price - p["h_entry"]) * 10 if p["h_status"] == "BOUGHT" else 0
            h_pct = ((price - p["h_entry"])/p["h_entry"])*100 if p["h_status"] == "BOUGHT" else 0
            w_rs = (price - p["w_entry"]) * 10 if p["w_status"] == "BOUGHT" else 0
            w_pct = ((price - p["w_entry"])/p["w_entry"])*100 if p["w_status"] == "BOUGHT" else 0
            
            report_data.append([ticker.replace(".NS",""), price, round(ema,2), round(rsi,2), 
                                p["h_status"], round(p["h_entry"],2), round(h_rs,2), round(h_pct,2),
                                p["w_status"], round(p["w_entry"],2), round(w_rs,2), round(w_pct,2), 
                                round(h_rs+w_rs,2), datetime.now().strftime("%H:%M:%S")])

        # SORTING & EXCEL UPDATE
        df = pd.DataFrame(report_data, columns=HEADERS)
        df = df.sort_values(by="Combined PnL", ascending=False)
        
        sheet.range("A1").value = HEADERS
        sheet.range("A2:N50").clear_contents()
        sheet.range("A2").value = df.values.tolist()
            
        time.sleep(5)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)