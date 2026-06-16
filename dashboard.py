import sys
import asyncio  
import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import time as dtime
import datetime as global_dt
import pytz
import os
import time

# 🚨 விண்டோஸ் நெட்வொர்க் எர்ரரை தடுக்கும் பாலிசி
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

st.set_page_config(layout="wide")
st.title("🚀 PASSIVE HYBRID ALGO - V19.0 (CARRY FORWARD & FUND TRACKER ENGINE)")

# 🕒 லைவ் டைம் டிரேக்கர் செட்டப்
ist = pytz.timezone('Asia/Kolkata')
now_time = global_dt.datetime.now(ist).time()
today_str = global_dt.datetime.now(ist).strftime('%Y-%m-%d')

# 📂 1. POSITION & FUND TRACKER ENGINE
DB_FILE = "positions_db.csv"
FUND_FILE = "fund_tracker.csv"

def load_positions():
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
    return {"initial_capital": 100000.0, "available_funds": 100000.0}

def save_funds(fund_dict):
    pd.DataFrame([fund_dict]).to_csv(FUND_FILE, index=False)

# =======================================================================
# 🎯 2. டேட்டாவை ஆரம்பத்திலேயே லோடு செய்து, லாபத்தை கணக்கிடுகிறோம்!
# =======================================================================
existing_positions = load_positions()
funds = load_funds()

live_pnl = 0.0
if existing_positions:
    for pos in existing_positions:
        try:
            pnl_val = pos.get('W_PnL(Rs)', 0)
            if isinstance(pnl_val, str):
                pnl_val = pnl_val.replace('₹', '').replace(',', '').strip()
                if pnl_val == '-' or pnl_val == '': 
                    pnl_val = 0.0
            live_pnl += float(pnl_val)
        except:
            pass

# =======================================================================
# 🎯 3. SIDEBAR செக்ஷன்: Fund Tracker & Live Margin Estimator (பக்கா பிக்ஸ்!)
# =======================================================================
st.sidebar.markdown(f"## 💰 Live Fund Tracker")
original_capital = funds.get('initial_capital', 100000.00)
current_available = funds.get('available_funds', 100000.00)

# லைவ் ப்ராஃபிட்டை அவைலபிள் ஃபண்டில் கூட்டுகிறோம்
realtime_available = current_available + live_pnl

st.sidebar.metric("ஆரம்ப மூலதனம் (Initial Capital)", f"₹ {original_capital:,.2f}")
# 🔥 இப்போ எந்த கண்டிஷனும் இல்லாம எப்போவுமே 'கைவசம் உள்ள தொகை' காட்டும் மாப்ள!
st.sidebar.metric("கைவசம் உள்ள தொகை (Available Funds)", f"₹ {realtime_available:,.2f}")

if live_pnl > 0:
    st.sidebar.success(f"📈 இன்றைய லாபம் சேர்க்கப்பட்டது: +₹ {live_pnl:,.2f}")

st.sidebar.markdown("---")

# 🧮 LIVE MARGIN ESTIMATOR விட்ஜெட்
st.sidebar.markdown("### 🧮 Live Margin Estimator")
ltp_input = st.sidebar.number_input("ஸ்டாக் விலை (LTP ₹)", min_value=1.0, value=1505.0, step=0.5)
qty_input = st.sidebar.number_input("குவாண்டிட்டி (Quantity)", min_value=1, value=10, step=1)
mode_input = st.sidebar.selectbox("டிரேடிங் மோடு (Mode)", ["Husband (Swing - 1x)", "Wife (Intraday - 5x)"])

# மார்ஜின் கால்குலேஷன் லாஜிக்
gross_order_value = ltp_input * qty_input
if "Wife" in mode_input:
    margin_required = gross_order_value / 5
    leverage_text = "(5x Leverage Applied)"
else:
    margin_required = gross_order_value
    leverage_text = "(1x Leverage Applied - No Margin Benefit)"

simulated_balance = realtime_available - margin_required

st.sidebar.markdown("#### ⚡ Estimated Balance After Order")
st.sidebar.metric("மீதமுள்ள தொகை (Simulated Available)", f"₹ {simulated_balance:,.2f}")

# மார்ஜின் ஹைலைட் பாக்ஸ்
st.sidebar.info(f"**இந்த ஆர்டருக்கு பிடிக்கும் மார்ஜின்:** ₹ {margin_required:,.2f}")
st.sidebar.caption(f"மொத்த ஆர்டர் மதிப்பு: ₹ {gross_order_value:,.2f}  \n{leverage_text}")


# =======================================================================
# 🎯 4. மெயின் பக்கத்து டேபிளை டிஸ்ப்ளே செய்கிறோம்!
# =======================================================================
if existing_positions:
    df = pd.DataFrame(existing_positions)
    df = df.replace('-', 0).fillna(0)
    df = df.apply(pd.to_numeric, errors='ignore')
    
    df_display = df.astype(str).replace(r'^\s*-\s*$', '0', regex=True).replace('nan', '0')
    st.write(df_display) 

# ⏰ மதியம் 3:15 அல்கோ ஆட்டோ-கட்ஆஃப் லாஜிக் 
import datetime
current_now = datetime.datetime.now().time()
dtime_obj = datetime.time

if current_now >= dtime_obj(15, 15):
    st.warning("🚨 மதியம் 3:15 ஆகிவிட்டது! அல்கோ நிறுத்தப்படுகிறது.")
    
    try:
        save_positions(existing_positions if existing_positions else [])
        save_funds(funds if funds else {})
        time.sleep(5)
        os._exit(0)
    except Exception as e:
        st.error(f"Save Error: {e}")
        try:
            save_positions([])
        except Exception:
            pass
        try:
            save_funds(funds if funds else {})
        except Exception:
            pass
        time.sleep(5)
        os._exit(0)

# 🔒 ஸ்ட்ரேட்டஜி பாராமீட்டர்கள்
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

        past_pos = next((p for p in existing_positions if p["stock"] == stock_name), None)

        # --- Husband Account (Swing Mode) ---
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

# 💾 5. ஃபண்ட் மற்றும் பொசிஷன் அப்டேட்களை சேவ் செய்கிறோம்
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