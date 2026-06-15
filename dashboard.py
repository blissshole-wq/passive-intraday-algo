import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import time as dtime
import datetime as global_dt
import pytz
import os
import time

st.set_page_config(layout="wide")
st.title("🚀 PASSIVE HYBRID ALGO - V19.0 (CARRY FORWARD & FUND TRACKER ENGINE)")

# 🕒 லைவ் டைம் டிரேக்கர் செட்டப்
ist = pytz.timezone('Asia/Kolkata')
now = global_dt.datetime.now(ist).time()
today_str = global_dt.datetime.now(ist).strftime('%Y-%m-%d')

# 📂 1. POSITION & FUND TRACKER ENGINE (டேட்டாபேஸ் ஃபைல் ப்ரோ)
DB_FILE = "positions_db.csv"
FUND_FILE = "fund_tracker.csv"

def load_positions():
    import os
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return []
    try:
        return pd.read_csv(DB_FILE).to_dict(orient="records")
    except pd.errors.EmptyDataError:
        return []  
def save_positions(positions_list):
    pd.DataFrame(positions_list).to_csv(DB_FILE, index=False)

def load_funds():
    if os.path.exists(FUND_FILE):
        return pd.read_csv(FUND_FILE).to_dict(orient="records")[0]
    # ஆரம்ப நிதி (Default Initial Capital: 1,000,000)
    return {"initial_capital": 100000.0, "available_funds": 100000.0}

def save_funds(fund_dict):
    pd.DataFrame([fund_dict]).to_csv(FUND_FILE, index=False)

# லோக்கல் டேட்டாவை லோடு செய்றோம் ப்ரோ
existing_positions = load_positions()
funds = load_funds()

# 💰 ஃபண்ட் ட்ராக்கர் டிஸ்ப்ளே (டாப்லேயே காட்டும்)
st.sidebar.markdown(f"## 💰 Fund Tracker")
st.sidebar.metric("ஆரம்ப மூலதனம் (Initial Capital)", f"₹ {funds['initial_capital']:,.2f}")
st.sidebar.metric("கைவசம் உள்ள தொகை (Available Funds)", f"₹ {funds['available_funds']:,.2f}")

# 1. காலையில 9:15-க்கு முன்னாடி அல்கோ காத்திருக்க
if now < dtime(9, 15):
    st.info("🕒 மார்க்கெட் இன்னும் ஓபன் ஆகவில்லை. 9:15 AM வரை அல்கோ காத்திருக்கிறது...")
    time.sleep(30)
    st.rerun()

# 2. லைவ் டிக்கர் நேரம் கச்சிதமாகக் காட்ட
current_time = global_dt.datetime.now(ist).strftime('%Y-%m-%d %I:%M:%S %p')
st.markdown(f"### 🕒 **கடைசியாக புதுப்பிக்கப்பட்ட நேரம் (Live Ticker):** `{current_time}`")

# 3. 🚨 மதியம் 3:15 மணி ஆன உடனே ஆட்டோ க்ளோஸ் செய்ய
if now >= dtime(15, 15):
        st.warning("🚨 மதியம் 3:15 ஆகிவிட்டது! அல்கோ நிறுத்தப்படுகிறது.")
        
        try:
            # ஃபர்ஸ்ட் நார்மலா எக்ஸிஸ்டிங் பொசிஷனை சேவ் பண்ண ட்ரை பண்ணும்
            save_positions(existing_positions)
        except NameError:
            # ஒருவேளை அந்த வேரியபிள் இல்லைனா எர்ரர் வராம காலியான லிஸ்ட்டை சேவ் பண்ணும்
            save_positions([])
            
        save_funds(funds)
        time.sleep(5)
        os._exit(0)
# 🔒 டைனமிக் லிமிட்ஸ்
MIN_TARGET = 0.6
MAX_TARGET = 1.5
MIN_SL = 0.4
MAX_SL = 0.8

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", 
    "HINDUNILVR.NS", "LT.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", 
    "BAJFINANCE.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", 
    "SUNPHARMA.NS", "ULTRACEMCO.NS", "TATASTEEL.NS", "NESTLEIND.NS", "POWERGRID.NS", 
    "HCLTECH.NS", "JSWSTEEL.NS", "M&M.NS", "ADANIENT.NS"
]

TRADE_QTY = 1 

def check_algo_conditions(hist, day_hist):
    try:
        price = hist['Close'].iloc[-1]
        hist['RSI'] = ta.momentum.rsi(hist['Close'], window=14)
        hist['VWAP'] = (hist['Volume'] * hist['Close']).cumsum() / hist['Volume'].cumsum()
        hist['EMA_20'] = ta.trend.ema_indicator(hist['Close'], window=20)
        hist['ATR'] = ta.volatility.average_true_range(hist['High'], hist['Low'], hist['Close'], window=14)
        
        rsi = hist['RSI'].iloc[-1]
        vwap = hist['VWAP'].iloc[-1]
        ema_20 = hist['EMA_20'].iloc[-1]
        atr = hist['ATR'].iloc[-1] if not pd.isna(hist['ATR'].iloc[-1]) else (price * 0.002)
        
        prev_close = day_hist['Close'].iloc[-2]
        prev_high = day_hist['High'].iloc[-2]
        
        if rsi >= 65:
            dynamic_target = MAX_TARGET
        elif rsi <= 50:
            dynamic_target = MIN_TARGET
        else:
            dynamic_target = 1.0
            
        atr_pct = (atr / price) * 100
        if atr_pct > 0.3:
            dynamic_sl = MAX_SL
        elif atr_pct < 0.15:
            dynamic_sl = MIN_SL
        else:
            dynamic_sl = 0.5

        # 🚨 உங்க பழைய இன்ட்ராடே கண்டிஷன்ஸ் எதையுமே மாத்தல ப்ரோ!
        c1 = hist['Open'].iloc[-1] < prev_close  
        c2 = price > prev_close                  
        c3 = price > vwap                        
        c4 = price > ema_20                      
        c5 = rsi > 40                            
        c6 = hist['Volume'].iloc[-1] > hist['Volume'].rolling(20).mean().iloc[-1] 
        c7 = price > prev_high                   
        
        fails = []
        if not c1: fails.append("C1")
        if not c2: fails.append("C2")
        if not c3: fails.append("C3")
        if not c4: fails.append("C4")  
        if not c5: fails.append("C5")  
        if not c6: fails.append("C6")
        if not c7: fails.append("C7")
        
        critical_fails = [f for f in fails if f not in ["C1", "C5", "C6", "C7"]]
        wife_pass = len(critical_fails) == 0  
        
        streak_exit = (price < ema_20) or (price < vwap) or (rsi < 40)
        
        streak_reason = ""
        if price < ema_20: streak_reason = "❌ STREAK (EMA FAIL)"
        elif price < vwap: streak_reason = "❌ STREAK (VWAP FAIL)"
        elif rsi < 40: streak_reason = "❌ STREAK (RSI FAIL)"
        
        highest_price = hist['High'].max()
        
        return {
            "all_passed": len(fails) == 0,
            "wife_passed": wife_pass,
            "fail_msg": f"IDLE ({', '.join(fails)})" if fails else "BUY",
            "streak_exit": streak_exit,
            "streak_reason": streak_reason,
            "highest_price": highest_price,
            "dynamic_target": dynamic_target,
            "dynamic_sl": dynamic_sl
        }
    except:
        return {"all_passed": False, "wife_passed": False, "fail_msg": "DATA_ERR", "streak_exit": False, "streak_reason": "", "highest_price": 0.0, "dynamic_target": 1.0, "dynamic_sl": 0.5}

report_data = []
new_saved_positions = []
total_h_investment, total_h_pnl_rs = 0.0, 0.0
total_w_investment, total_w_pnl_rs = 0.0, 0.0

h_total, h_wins, h_losses = 0, 0, 0
w_total, w_wins, w_losses = 0, 0, 0

used_funds_today = 0.0

for ticker in WATCHLIST:
    try:
        stock_name = ticker.replace(".NS", "")
        data = yf.Ticker(ticker)
        hist = data.history(period="5d", interval="15m")
        day_hist = data.history(period="5d", interval="1d")
        
        if hist.empty or len(hist) < 20: continue

        price = round(hist['Close'].iloc[-1], 2)
        day_open_price = round(hist['Open'].iloc[0], 2) 
        
        algo = check_algo_conditions(hist, day_hist)
        tg = algo["dynamic_target"]
        sl = algo["dynamic_sl"]

        h_status, h_entry, h_pnl_rs, h_pnl_pct_str = "-", 0.0, 0.0, "-"
        w_status, w_entry, w_pnl_rs, w_pnl_pct_str = "-", 0.0, 0.0, "-"

        # 🧠 2. CARRY FORWARD LOGIC
        past_pos = next((p for p in existing_positions if p["stock"] == stock_name), None)

        # --- Husband Account (Swing Mode with Carry Forward) ---
        if algo["all_passed"] or past_pos:
            h_entry = past_pos["entry_price"] if past_pos else day_open_price
            pnl_pct = ((price - h_entry) / h_entry) * 100
            h_total += 1
            total_h_investment += (h_entry * TRADE_QTY)
            
            if not past_pos:
                used_funds_today += (h_entry * TRADE_QTY)

            gains_pct = ((algo["highest_price"] - h_entry) / h_entry) * 100
            current_sl_pct = sl
            if gains_pct >= 0.5:
                jumps = int(gains_pct / 0.5)
                current_sl_pct = -sl + (jumps * 0.3)

            if pnl_pct >= tg:
                h_status = f"🎯 TARGET HIT ({tg}%)"
                h_pnl_rs = round((h_entry * (tg/100)) * TRADE_QTY, 2)
                h_pnl_pct_str = f"{tg}%"
                h_wins += 1
                if past_pos: funds["available_funds"] += (h_entry * TRADE_QTY) + h_pnl_rs
            elif pnl_pct <= current_sl_pct and current_sl_pct < 0:
                h_status = f"🚨 SL HIT (-{sl}%)"
                h_pnl_rs = round((-h_entry * (sl/100)) * TRADE_QTY, 2)
                h_pnl_pct_str = f"-{sl}%"
                h_losses += 1
                if past_pos: funds["available_funds"] += (h_entry * TRADE_QTY) + h_pnl_rs
            elif pnl_pct <= current_sl_pct and current_sl_pct >= 0:
                h_status = "📈 TSL HIT (PROFIT)"
                h_pnl_rs = round((h_entry * (current_sl_pct/100)) * TRADE_QTY, 2)
                h_pnl_pct_str = f"{round(current_sl_pct, 2)}%"
                h_wins += 1
                if past_pos: funds["available_funds"] += (h_entry * TRADE_QTY) + h_pnl_rs
            else:
                h_status = f"🥇 SWING HOLD (T:{tg}%/S:{sl}%)"
                h_pnl_rs = round((price - h_entry) * TRADE_QTY, 2)
                h_pnl_pct_str = f"{round(pnl_pct, 2)}%"
                # டார்கெட் அடிக்காத வரை நாளைக்கு Carry Forward ஆகும் ப்ро!
                new_saved_positions.append({"stock": stock_name, "entry_price": h_entry, "date": today_str})
            
            total_h_pnl_rs += h_pnl_rs
        else:
            h_status = algo["fail_msg"]

        # --- Wife Account (Pure Intraday Mode) ---
        if algo["wife_passed"]:
            w_entry = day_open_price
            pnl_pct = ((price - w_entry) / w_entry) * 100
            w_total += 1
            total_w_investment += (w_entry * TRADE_QTY)
            
            gains_pct = ((algo["highest_price"] - w_entry) / w_entry) * 100
            current_sl_pct = -sl
            if gains_pct >= 0.5:
                jumps = int(gains_pct / 0.5)
                current_sl_pct = -sl + (jumps * 0.3)

            if pnl_pct >= tg:
                w_status = f"🎯 TARGET HIT ({tg}%)"
                w_pnl_rs = round((w_entry * (tg/100)) * TRADE_QTY, 2)
                w_pnl_pct_str = f"{tg}%"
                w_wins += 1
            elif pnl_pct <= current_sl_pct and current_sl_pct < 0:
                w_status = f"🚨 SL HIT (-{sl}%)"
                w_pnl_rs = round((-w_entry * (sl/100)) * TRADE_QTY, 2)
                w_pnl_pct_str = f"-{sl}%"
                w_losses += 1
            elif pnl_pct <= current_sl_pct and current_sl_pct >= 0:
                w_status = "📈 TSL HIT (PROFIT)"
                w_pnl_rs = round((w_entry * (current_sl_pct/100)) * TRADE_QTY, 2)
                w_pnl_pct_str = f"{round(current_sl_pct, 2)}%"
                w_wins += 1
            elif algo["streak_exit"]:
                w_status = algo["streak_reason"]
                w_pnl_rs = round((price - w_entry) * TRADE_QTY, 2)
                w_pnl_pct_str = f"{round(pnl_pct, 2)}%"
                if w_pnl_rs >= 0: w_wins += 1
                else: w_losses += 1
            else:
                w_status = f"⚡ DAY-TRADE BUY (T:{tg}%/S:{sl}%)"
                w_pnl_rs = round((price - w_entry) * TRADE_QTY, 2)
                w_pnl_pct_str = f"{round(pnl_pct, 2)}%"
                
            total_w_pnl_rs += w_pnl_rs
        else:
            w_fails = [f for f in algo["fail_msg"].replace("IDLE (", "").replace(")", "").split(", ") if f not in ["C1", "C5", "C6", "C7"]]
            w_status = f"IDLE ({', '.join(w_fails)})" if w_fails and w_fails != [''] else algo["fail_msg"]

        report_data.append([
            stock_name, price,
            h_status, h_entry if h_entry > 0 else "-", f"₹{h_pnl_rs}" if h_entry > 0 else "-", h_pnl_pct_str,
            w_status, w_entry if w_entry > 0 else "-", f"₹{w_pnl_rs}" if w_entry > 0 else "-", w_pnl_pct_str
        ])
        
    except Exception:
        continue

# 💾 3. ஃபண்ட் மற்றும் பொசிஷன் அப்டேட்களை சேவ் செய்கிறோம்
if used_funds_today > 0 and len(existing_positions) == 0:
    funds["available_funds"] -= used_funds_today

save_positions(new_saved_positions)
save_funds(funds)

columns = [
    "Stock", "LTP", 
    "Husband (Swing Mode)", "H_Entry", "H_PnL(Rs)", "H_PnL(%)",
    "Wife (Day-Trade Mode)", "W_Entry", "W_PnL(Rs)", "W_PnL(%)"
]

df = pd.DataFrame(report_data, columns=columns)
st.dataframe(df, width="stretch", hide_index=True)

total_h_pnl_pct = round((total_h_pnl_rs / total_h_investment) * 100, 2) if total_h_investment > 0 else 0.0
total_w_pnl_pct = round((total_w_pnl_rs / total_w_investment) * 100, 2) if total_w_investment > 0 else 0.0

combined_pnl_rs = total_h_pnl_rs + total_w_pnl_rs
combined_investment = total_h_investment + total_w_investment
combined_pnl_pct = round((combined_pnl_rs / combined_investment) * 100, 2) if combined_investment > 0 else 0.0

st.markdown("---")
st.subheader("📊 Hybrid Portfolio Summary (V19.0 - Live Tracker)")

if combined_pnl_rs >= 0:
    st.success(f"### 🤝 Combined Family Performance: **₹ {combined_pnl_rs:,.2f} ({combined_pnl_pct}%)**")
else:
    st.error(f"### 🤝 Combined Family Performance: **₹ {combined_pnl_rs:,.2f} ({combined_pnl_pct}%)**")

col1, col2 = st.columns(2)
with col1:
    st.info(f"""
    ### 🤵 Husband Account (Swing Mode)
    * **Total PnL:** **₹ {total_h_pnl_rs:,.2f} ({total_h_pnl_pct}%)**
    * **Trades Active/Closed:** `{h_total}` | Wins: `{h_wins}` | Losses: `{h_losses}`
    """)

with col2:
    st.success(f"""
    ### 👩 Wife Account (Intraday Mode)
    * **Total PnL:** **₹ {total_w_pnl_rs:,.2f} ({total_w_pnl_pct}%)**
    * **Trades:** Total: `{w_total}` | Wins: `{w_wins}` | Losses: `{w_losses}`
    """)

if st.button("Refresh Live Data"):
    st.rerun()