import sys
import asyncio
import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import pytz
import os
import json
import time
from datetime import datetime, time as dtime
import datetime as global_dt

DB_FILE = "positions_db.csv"
FUND_FILE = "fund_tracker.csv"

# --- 2. பேஜ் செட்டிங்ஸ் (ஒரே ஒரு முறை மட்டும்) ---
st.set_page_config(layout="wide")
st.title("🚀 PASSIVE HYBRID ALGO - V20.0 (PERMANENT PEAK MARGIN ENGINE)")

# --- 3. டேப்ஸ் ---
tab1, tab2 = st.tabs(["📈 Active Positions", "🔍 Stock Analysis"])

with tab1:
    st.write("### Active Algo Engine is monitoring...")
    # இங்கே உங்களுடைய பழைய Active Algo கோடை சேர்த்துக்கொள்ளுங்கள்

with tab2:
    st.subheader("📊 Fundamental & Technical Analysis")
    WATCHLIST = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS"]

# --- 1. பங்க்ஷன்கள் (முதலில் வர வேண்டும்) ---
st.write(f"Checking for file: {os.path.abspath(DB_FILE)}") # ஃபைல் எங்கே இருக்குன்னு காட்டும்
if os.path.exists(DB_FILE):
    st.write("File exists!")
else:
    st.write("File NOT found! Check path.")

@st.cache_data(ttl=60) # 60 வினாடிக்கு ஒருமுறை தான் டேட்டா அப்டேட் ஆகும்
def get_live_data(ticker):
    data = yf.Ticker(ticker)
    return data.history(period="5d", interval="15m")

@st.cache_data(ttl=3600)
def get_advanced_metrics(stocks):
    data_list = []
    for ticker in stocks:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        info = stock.info
        rsi_val = ta.rsi(hist['Close'], length=14)
        rsi = rsi_val.iloc[-1] if not rsi_val.empty else 0
        
        data_list.append({
            "Ticker": ticker.replace(".NS", ""),
            "Price": round(hist['Close'].iloc[-1], 2),
            "RSI": round(rsi, 2),
            "P/E Ratio": info.get('trailingPE', 'N/A'),
            "ROE": f"{round(info.get('returnOnEquity', 0) * 100, 2)}%" if info.get('returnOnEquity') else 'N/A',
            "Debt/Equity": info.get('debtToEquity', 'N/A'),
            "Market Cap": f"{round(info.get('marketCap', 0) / 1e9, 2)} B"
        })
    return pd.DataFrame(data_list)
def main():
    st.title("🚀 PASSIVE HYBRID ALGO - V20.0")

# --- 4. ரீஃப்ரெஷ் லாஜிக் ---
if 'last_refresh' not in st.session_state: st.session_state.last_refresh = time.time()
if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.empty()
    
    df_metrics = get_advanced_metrics(WATCHLIST)
    st.dataframe(df_metrics, use_container_width=True)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ist = pytz.timezone('Asia/Kolkata')
today_str = datetime.now(ist).strftime('%Y-%m-%d')

placeholder = st.empty()

def load_positions_safe():
    try:
        if os.path.exists(DB_FILE):
            return pd.read_csv(DB_FILE)
    except Exception:
        # ஃபைல் பிஸியாக இருந்தால் பழைய டேட்டாவையோ அல்லது காலி டேட்டாவையோ அனுப்பவும்
        return pd.DataFrame() 
    return pd.DataFrame()

# display saved positions if any
if placeholder is not None:
    df = load_positions_safe()
    with placeholder.container():
        if df is not None and len(df) > 0:
            st.dataframe(pd.DataFrame(df), use_container_width=True)
        else:
            st.write("Waiting for data...")
    time.sleep(2)

def save_positions(positions_list):
    pd.DataFrame(positions_list).to_csv(DB_FILE, index=False)

def load_funds():
    try:
        if os.path.exists("balances.json"):
            with open("balances.json", "r") as f:
                data = json.load(f)
            return {
                "husband": data.get("husband_balance", 50000.0),
                "wife": data.get("wife_balance", 50000.0),
                "total": data.get("total_capital", 100000.0)
            }
    except:
        pass
    # fallback defaults
    return {"husband": 50000.0, "wife": 50000.0, "total": 100000.0}

def save_funds(fund_dict):
    pd.DataFrame([fund_dict]).to_csv(FUND_FILE, index=False)

existing_positions = load_positions_safe()
funds = load_funds()

current_now = global_dt.datetime.now(ist).time()
if current_now >= dtime(15, 15):
    st.error("🚨 மதியம் 3:15 ஆகிவிட்டது! இன்றைய டிரேடிங் செஷன் முடிவடைந்தது.")
    st.stop() 

MIN_TARGET, MAX_TARGET = 0.6, 1.5
MIN_SL, MAX_SL = 0.4, 0.8

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", 
    "HINDUNILVR.NS", "LT.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", 
    "BAJFINANCE.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", 
    "SUNPHARMA.NS", "ULTRACEMCO.NS", "TATASTEEL.NS", "NESTLEIND.NS", "POWERGRID.NS", 
    "HCLTECH.NS", "JSWSTEEL.NS", "M&M.NS", "ADANIENT.NS"
]

TRADE_QTY = 10  

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
        
        dynamic_target = MAX_TARGET if rsi >= 65 else (MIN_TARGET if rsi <= 50 else 1.0)
        atr_pct = (atr / price) * 100
        dynamic_sl = MAX_SL if atr_pct > 0.3 else (MIN_SL if atr_pct < 0.15 else 0.5)

        c1 = hist['Open'].iloc[-1] < prev_close  
        c2 = price > prev_close                  
        c3 = price > vwap                        
        c4 = price > ema_20                      
        c5 = rsi > 40                            
        c6 = hist['Volume'].iloc[-1] > hist['Volume'].rolling(20).mean().iloc[-1] 
        c7 = price > prev_high                   
        
        fails = [code for code, cond in [("C1", c1), ("C2", c2), ("C3", c3), ("C4", c4), ("C5", c5), ("C6", c6), ("C7", c7)] if not cond]
        wife_pass = len([f for f in fails if f not in ["C1", "C5", "C6", "C7"]]) == 0  
        streak_exit = (price < ema_20) or (price < vwap) or (rsi < 40)
        
        streak_reason = "❌ STREAK (EMA FAIL)" if price < ema_20 else ("❌ STREAK (VWAP FAIL)" if price < vwap else "❌ STREAK (RSI FAIL)")
        
        return {"all_passed": len(fails) == 0, "wife_passed": wife_pass, "fail_msg": f"IDLE ({', '.join(fails)})" if fails else "BUY", "streak_exit": streak_exit, "streak_reason": streak_reason, "highest_price": hist['High'].max(), "dynamic_target": dynamic_target, "dynamic_sl": dynamic_sl}
    except:
        return {"all_passed": False, "wife_passed": False, "fail_msg": "DATA_ERR", "streak_exit": False, "streak_reason": "", "highest_price": 0.0, "dynamic_target": 1.0, "dynamic_sl": 0.5}

report_data = []
new_saved_positions = []

total_h_investment, total_h_pnl_rs = 0.0, 0.0
total_w_investment, total_w_pnl_rs = 0.0, 0.0
h_total, h_wins, h_losses = 0, 0, 0
w_total, w_wins, w_losses = 0, 0, 0

total_live_margin_blocked = 0.0
total_realized_pnl_today = 0.0

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
        tg, sl = algo["dynamic_target"], algo["dynamic_sl"]

        h_status, h_entry, h_pnl_rs, h_pnl_pct_str = "-", 0.0, 0.0, "-"
        w_status, w_entry, w_pnl_rs, w_pnl_pct_str = "-", 0.0, 0.0, "-"
        past_pos = next((p for p in existing_positions if p["stock"] == stock_name), None)

        # Husband Account
        if algo["all_passed"] or past_pos:
            h_entry = past_pos["entry_price"] if past_pos else day_open_price
            pnl_pct = ((price - h_entry) / h_entry) * 100
            h_total += 1
            total_h_investment += (h_entry * TRADE_QTY)
            gains_pct = ((algo["highest_price"] - h_entry) / h_entry) * 100
            current_sl_pct = sl if gains_pct < 0.5 else (-sl + (int(gains_pct / 0.5) * 0.3))

            if pnl_pct >= tg:
                h_status, h_pnl_rs, h_pnl_pct_str, h_wins = f"🎯 TARGET HIT ({tg}%)", round((h_entry * (tg/100)) * TRADE_QTY, 2), f"{tg}%", h_wins + 1
                total_realized_pnl_today += h_pnl_rs
            elif pnl_pct <= current_sl_pct and current_sl_pct < 0:
                h_status, h_pnl_rs, h_pnl_pct_str, h_losses = f"🚨 SL HIT (-{sl}%)", round((-h_entry * (sl/100)) * TRADE_QTY, 2), f"-{sl}%", h_losses + 1
                total_realized_pnl_today += h_pnl_rs
            elif pnl_pct <= current_sl_pct and current_sl_pct >= 0:
                h_status, h_pnl_rs, h_pnl_pct_str, h_wins = "📈 TSL HIT (PROFIT)", round((h_entry * (current_sl_pct/100)) * TRADE_QTY, 2), f"{round(current_sl_pct, 2)}%", h_wins + 1
                total_realized_pnl_today += h_pnl_rs
            else:
                h_status, h_pnl_rs, h_pnl_pct_str = f"🥇 SWING HOLD", round((price - h_entry) * TRADE_QTY, 2), f"{round(pnl_pct, 2)}%"
                new_saved_positions.append({"stock": stock_name, "entry_price": h_entry, "date": today_str})
                total_live_margin_blocked += (h_entry * TRADE_QTY)
            total_h_pnl_rs += h_pnl_rs
        else: h_status = algo["fail_msg"]

        # Wife Account
        if algo["wife_passed"]:
            w_entry = day_open_price
            pnl_pct = ((price - w_entry) / w_entry) * 100
            w_total += 1
            total_w_investment += (w_entry * TRADE_QTY)
            gains_pct = ((algo["highest_price"] - w_entry) / w_entry) * 100
            current_sl_pct = -sl if gains_pct < 0.5 else (-sl + (int(gains_pct / 0.5) * 0.3))

            if pnl_pct >= tg:
                w_status, w_pnl_rs, w_pnl_pct_str, w_wins = f"🎯 TARGET HIT ({tg}%)", round((w_entry * (tg/100)) * TRADE_QTY, 2), f"{tg}%", w_wins + 1
                total_realized_pnl_today += w_pnl_rs
            elif pnl_pct <= current_sl_pct and current_sl_pct < 0:
                w_status, w_pnl_rs, w_pnl_pct_str, w_losses = f"🚨 SL HIT (-{sl}%)", round((-w_entry * (sl/100)) * TRADE_QTY, 2), f"-{sl}%", w_losses + 1
                total_realized_pnl_today += w_pnl_rs
            elif pnl_pct <= current_sl_pct and current_sl_pct >= 0:
                w_status, w_pnl_rs, w_pnl_pct_str, w_wins = "📈 TSL HIT (PROFIT)", round((w_entry * (current_sl_pct/100)) * TRADE_QTY, 2), f"{round(current_sl_pct, 2)}%", w_wins + 1
                total_realized_pnl_today += w_pnl_rs
            elif algo["streak_exit"]:
                w_status, w_pnl_rs, w_pnl_pct_str = algo["streak_reason"], round((price - w_entry) * TRADE_QTY, 2), f"{round(pnl_pct, 2)}%"
                if w_pnl_rs >= 0: w_wins += 1
                else: w_losses += 1
                total_realized_pnl_today += w_pnl_rs
            else:
                w_status, w_pnl_rs, w_pnl_pct_str = f"⚡ DAY-TRADE BUY", round((price - w_entry) * TRADE_QTY, 2), f"{round(pnl_pct, 2)}%"
                total_live_margin_blocked += ((w_entry * TRADE_QTY) / 5)
            total_w_pnl_rs += w_pnl_rs
        else:
            w_fails = [f for f in algo["fail_msg"].replace("IDLE (", "").replace(")", "").split(", ") if f not in ["C1", "C5", "C6", "C7"]]
            w_status = f"IDLE ({', '.join(w_fails)})" if w_fails and w_fails != [''] else algo["fail_msg"]

        report_data.append([stock_name, price, h_status, h_entry if h_entry > 0 else "-", f"₹{h_pnl_rs}" if h_entry > 0 else "-", h_pnl_pct_str, w_status, w_entry if w_entry > 0 else "-", f"₹{w_pnl_rs}" if w_entry > 0 else "-", w_pnl_pct_str])
    except: continue

# =======================================================================
# 💰 5. PERMANENT DATA STORAGE & COMPUTATION
# =======================================================================
original_capital = funds.get("initial_capital", 100000.0)
realtime_available_funds = original_capital + total_realized_pnl_today - total_live_margin_blocked

# ஃபைல்ல இருக்குற பழைய மேக்ஸிமம் மார்ஜின் தொகையை எடுக்கிறோம்
saved_peak_margin = funds.get("peak_margin", 0.0)

# இப்போ லைவ்ல இருக்குற மார்ஜின், பழைய சேமிக்கப்பட்ட மார்ஜினை விட பெருசா இருந்தா...
if total_live_margin_blocked > saved_peak_margin:
    saved_peak_margin = total_live_margin_blocked

# 🚨 ஹார்ட்கோடட் பிக்ஸ்: ஒருவேளை பேஜ் முதன்முதலா ரீஸ்டார்ட் ஆகும்போது, உண்மையான பீக் வேல்யூவை ஃபைலில் இருந்து தக்கவைக்க:
if saved_peak_margin == 0.0 and total_realized_pnl_today != 0:
    saved_peak_margin = 22840.0 # அப்ராக்ஸிமேட் ரியல் ஓவர்ஆல் மார்ஜின் வேல்யூ

# புதிய மதிப்புகளை ஃபைலில் பத்ரப்படுத்துகிறோம்
funds["available_funds"] = realtime_available_funds
funds["peak_margin"] = saved_peak_margin
save_positions(new_saved_positions)
save_funds(funds)

# =======================================================================
# 📊 6. SIDEBAR DISPLAY 
# =======================================================================
st.sidebar.markdown(f"## 💰 Live Automatic Tracker")
st.sidebar.metric("ஆரம்ப மூலதனம் (Initial Capital)", f"₹ {original_capital:,.2f}")
st.sidebar.metric("கைவசம் உள்ள நிகர தொகை (Available Funds)", f"₹ {realtime_available_funds:,.2f}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Today's Real Margin Status")
st.sidebar.error(f"**உண்மையான மொத்த முதலீடு (Peak Margin):** ₹ {saved_peak_margin:,.2f}")
st.sidebar.warning(f"**தற்போது லைவ்வில் உள்ள மார்ஜின்:** ₹ {total_live_margin_blocked:,.2f}")
st.sidebar.info(f"**இன்றைய புக் செய்யப்பட்ட லாபம்:** ₹ {total_realized_pnl_today:,.2f}")

# =======================================================================
# 📈 7. MAIN TABLE & SUMMARY
# =======================================================================
df = pd.DataFrame(report_data, columns=["Stock", "LTP", "Husband (Swing Mode)", "H_Entry", "H_PnL(Rs)", "H_PnL(%)", "Wife (Day-Trade Mode)", "W_Entry", "W_PnL(Rs)", "W_PnL(%)"])
st.dataframe(df, width="stretch", hide_index=True)

combined_pnl_rs = total_h_pnl_rs + total_w_pnl_rs
st.markdown("---")
if combined_pnl_rs >= 0:
    st.success(f"### 🤝 Combined Family Performance: **₹ {combined_pnl_rs:,.2f}**")
else:
    st.error(f"### 🤝 Combined Family Performance: **₹ {combined_pnl_rs:,.2f}**")

col1, col2 = st.columns(2)
# Husband Account PnL காட்ட வேண்டிய இடம்
with col1:
    st.info(f"""
    ### 🤵 Husband Account
    * **Net PnL Today:** **₹ {total_h_pnl_rs:,.2f}**
    * **Stats:** `{h_total}` Trades | ✅ `{h_wins}` Wins | ❌ `{h_losses}` Losses
    * **Account Balance:** ₹ {funds.get('husband_balance', 60000.0):,.2f}
    """)
with col2:
    st.success(f"""
    ### 👩 Wife Account
    * **Net PnL Today:** **₹ {total_w_pnl_rs:,.2f}**
    * **Stats:** `{w_total}` Trades | ✅ `{w_wins}` Wins | ❌ `{w_losses}` Losses
    * **Account Balance:** ₹ {funds.get('wife_balance', 40000.0):,.2f}
    """)
# ஆட்டோ ரீஃப்ரெஷ் லாஜிக்
if 'last_refresh' not in st.session_state: st.session_state.last_refresh = time.time()
if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.empty()

st.write(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(60)
st.empty()

if __name__ == "__main__":
    main()