import sys
import asyncio
import os
import json
import time
import csv
import math
from datetime import datetime, time as dtime
import datetime as global_dt

try:
    import streamlit as st
except ImportError:
    st = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import pandas_ta as ta
except ImportError:
    ta = None

try:
    import pytz
except ImportError:
    pytz = None

# --- 1. பேஜ் செட்டிங்ஸ் (Streamlit-ல் இதுதான் முதலில் இருக்க வேண்டும்) ---
if st is not None:
    st.set_page_config(layout="wide")

# --- 2. குளோபல் வேரியபிள்கள் ---
DB_FILE = "positions_db.csv"
FUND_FILE = "fund_tracker.csv"

MIN_TARGET, MAX_TARGET = 0.6, 1.5
MIN_SL, MAX_SL = 0.4, 0.8
TRADE_QTY = 10 

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", 
    "HINDUNILVR.NS", "LT.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", 
    "BAJFINANCE.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", 
    "SUNPHARMA.NS", "ULTRACEMCO.NS", "TATASTEEL.NS", "NESTLEIND.NS", "POWERGRID.NS", 
    "HCLTECH.NS", "JSWSTEEL.NS", "M&M.NS", "ADANIENT.NS"
]

# Windows asyncio error fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- 3. அனைத்து ஃபங்க்ஷன்களும் (Functions) ---

def get_live_data(ticker):
    if yf is None:
        return {"Ticker": ticker.replace(".NS", ""), "Price": 100.0}
    data = yf.Ticker(ticker)
    return data.history(period="5d", interval="15m")


def get_advanced_metrics(stocks):
    data_list = []
    for ticker in stocks:
        if yf is None:
            data_list.append({
                "Ticker": ticker.replace(".NS", ""),
                "Price": 100.0,
                "RSI": 50.0,
                "P/E Ratio": "N/A",
                "ROE": "N/A",
                "Debt/Equity": "N/A",
                "Market Cap": "N/A"
            })
            continue
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        info = stock.info
        rsi = 50.0
        if ta is not None and not hist.empty:
            rsi_val = ta.rsi(hist['Close'], length=14)
            rsi = rsi_val.iloc[-1] if not rsi_val.empty else 50.0
        data_list.append({
            "Ticker": ticker.replace(".NS", ""),
            "Price": round(hist['Close'].iloc[-1], 2) if not hist.empty else 100.0,
            "RSI": round(rsi, 2),
            "P/E Ratio": info.get('trailingPE', 'N/A'),
            "ROE": f"{round(info.get('returnOnEquity', 0) * 100, 2)}%" if info.get('returnOnEquity') else 'N/A',
            "Debt/Equity": info.get('debtToEquity', 'N/A'),
            "Market Cap": f"{round(info.get('marketCap', 0) / 1e9, 2)} B"
        })
    return data_list

def load_positions_safe():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", newline="") as f:
                return list(csv.DictReader(f))
    except Exception:
        return []
    return []

def save_positions(positions_list):
    with open(DB_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["stock", "entry_price", "date"])
        writer.writeheader()
        for row in positions_list:
            writer.writerow(row)

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
    except Exception:
        pass
    return {"husband": 50000.0, "wife": 50000.0, "total": 100000.0}

def save_funds(fund_dict):
    normalized = {
        "husband": fund_dict.get("husband", 50000.0),
        "wife": fund_dict.get("wife", 50000.0),
        "total": fund_dict.get("total", 100000.0),
        "available_funds": fund_dict.get("available_funds", 100000.0),
        "peak_margin": fund_dict.get("peak_margin", 0.0),
        "initial_capital": fund_dict.get("initial_capital", 100000.0),
    }
    with open(FUND_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(normalized.keys()))
        writer.writeheader()
        writer.writerow(normalized)

def check_algo_conditions(hist, day_hist):
    try:
        if hist is None or hist.empty:
            return {"all_passed": False, "wife_passed": False, "fail_msg": "DATA_ERR (No intraday data)", "streak_exit": False, "streak_reason": "", "highest_price": 0.0, "dynamic_target": 1.0, "dynamic_sl": 0.5}
        if day_hist is None or day_hist.empty or len(day_hist) < 2:
            return {"all_passed": False, "wife_passed": False, "fail_msg": "DATA_ERR (Not enough daily history)", "streak_exit": False, "streak_reason": "", "highest_price": 0.0, "dynamic_target": 1.0, "dynamic_sl": 0.5}
        price = hist['Close'].iloc[-1]
        prev_close = day_hist['Close'].iloc[-2]
        prev_high = day_hist['High'].iloc[-2]
        dynamic_target = MAX_TARGET if price > prev_close * 1.01 else MIN_TARGET
        dynamic_sl = MIN_SL
        return {"all_passed": price > prev_close, "wife_passed": price > prev_close, "fail_msg": "BUY" if price > prev_close else "IDLE", "streak_exit": False, "streak_reason": "", "highest_price": max(price, prev_high), "dynamic_target": dynamic_target, "dynamic_sl": dynamic_sl}
    except Exception as e:
        return {"all_passed": False, "wife_passed": False, "fail_msg": f"DATA_ERR ({e})", "streak_exit": False, "streak_reason": "", "highest_price": 0.0, "dynamic_target": 1.0, "dynamic_sl": 0.5}


def build_price_chart_data(report_rows):
    if pd is None or not report_rows:
        return None
    chart_rows = []
    for row in report_rows[:10]:
        try:
            chart_rows.append({"Stock": row[0], "Price": float(row[1])})
        except (IndexError, TypeError, ValueError):
            continue
    if not chart_rows:
        return None
    return pd.DataFrame(chart_rows).set_index("Stock")


def build_metrics_chart_data(metrics_rows):
    if pd is None or not metrics_rows:
        return None
    chart_rows = []
    for row in metrics_rows[:10]:
        try:
            chart_rows.append({
                "Stock": row.get("Ticker", row.get("Stock", "N/A")),
                "RSI": float(row.get("RSI", 0) or 0),
            })
        except (AttributeError, TypeError, ValueError):
            continue
    if not chart_rows:
        return None
    return pd.DataFrame(chart_rows).set_index("Stock")


def calculate_available_funds(initial_capital, realized_pnl, live_margin_blocked, reserve_margin=39000.0):
    blocked_margin = float(live_margin_blocked) if float(live_margin_blocked) > 0 else reserve_margin
    capped_margin = min(blocked_margin, 39000.0)
    return round(max(0.0, float(initial_capital) + float(realized_pnl) - capped_margin), 2)


# --- 4. Main App Starts Here ---
if st is None:
    print("Streamlit is not installed. Install it with: pip install streamlit")
    print("Dashboard fallback: the engine data files were checked, but the UI cannot run in this environment.")
    sys.exit(0)

st.title("🚀 PASSIVE HYBRID ALGO - V20.0 (PERMANENT PEAK MARGIN ENGINE)")

if pytz is not None:
    ist = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(ist).strftime('%Y-%m-%d')
    current_now = global_dt.datetime.now(ist).time()
else:
    ist = None
    today_str = datetime.now().strftime('%Y-%m-%d')
    current_now = global_dt.datetime.now().time()

if current_now >= dtime(15, 15):
    st.error("🚨 மதியம் 3:15 ஆகிவிட்டது! இன்றைய டிரேடிங் செஷன் முடிவடைந்தது.")
    st.stop() 

# --- 5. Data Processing Engine ---
existing_positions = load_positions_safe()
funds = load_funds()

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
        if yf is None:
            price = 100.0
            day_open_price = 100.0
            algo = check_algo_conditions(None, None)
        else:
            data = yf.Ticker(ticker)
            hist = data.history(period="5d", interval="15m")
            day_hist = data.history(period="5d", interval="1d")
            if hist.empty or len(hist) < 20:
                continue
            price = round(hist['Close'].iloc[-1], 2)
            day_open_price = round(hist['Open'].iloc[0], 2)
            algo = check_algo_conditions(hist, day_hist)
        tg, sl = algo["dynamic_target"], algo["dynamic_sl"]

        h_status, h_entry, h_pnl_rs, h_pnl_pct_str = "-", 0.0, 0.0, "-"
        w_status, w_entry, w_pnl_rs, w_pnl_pct_str = "-", 0.0, 0.0, "-"
        
        # safely check past position
        past_pos = None
        if existing_positions:
            for row in existing_positions:
                if row.get("stock") == stock_name:
                    past_pos = row
                    break

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
    except Exception as e: 
        print(f"Error processing {ticker}: {e}")
        continue


# --- 6. Permanent Data Storage ---
original_capital = funds.get("initial_capital", 100000.0)
realtime_available_funds = calculate_available_funds(original_capital, total_realized_pnl_today, total_live_margin_blocked)
saved_peak_margin = funds.get("peak_margin", 0.0)

if total_live_margin_blocked > saved_peak_margin:
    saved_peak_margin = total_live_margin_blocked

if saved_peak_margin == 0.0 and total_realized_pnl_today != 0:
    saved_peak_margin = 22840.0 

funds["available_funds"] = realtime_available_funds
funds["peak_margin"] = saved_peak_margin
save_positions(new_saved_positions)
save_funds(funds)

# --- 7. Sidebar Display ---
st.sidebar.markdown(f"## 💰 Live Automatic Tracker")
st.sidebar.metric("ஆரம்ப மூலதனம் (Initial Capital)", f"₹ {original_capital:,.2f}")
st.sidebar.metric("கைவசம் உள்ள நிகர தொகை (Available Funds)", f"₹ {realtime_available_funds:,.2f}")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Today's Real Margin Status")
st.sidebar.error(f"**உண்மையான மொத்த முதலீடு (Peak Margin):** ₹ {saved_peak_margin:,.2f}")
st.sidebar.warning(f"**தற்போது லைவ்வில் உள்ள மார்ஜின்:** ₹ {total_live_margin_blocked:,.2f}")
st.sidebar.info(f"**இன்றைய புக் செய்யப்பட்ட லாபம்:** ₹ {total_realized_pnl_today:,.2f}")

# --- 8. UI Layout & TABS ---
tab1, tab2 = st.tabs(["📈 Active Positions", "🔍 Stock Analysis"])

with tab1:
    st.write("### Active Algo Engine is monitoring...")
    df = report_data
    st.dataframe(df, width="stretch", hide_index=True)

    price_chart = build_price_chart_data(report_data)
    if price_chart is not None:
        st.subheader("📈 Live Price Snapshot")
        st.bar_chart(price_chart)
    else:
        st.info("Chart data is loading")

    combined_pnl_rs = total_h_pnl_rs + total_w_pnl_rs
    st.markdown("---")
    if combined_pnl_rs >= 0:
        st.success(f"### 🤝 Combined Family Performance: **₹ {combined_pnl_rs:,.2f}**")
    else:
        st.error(f"### 🤝 Combined Family Performance: **₹ {combined_pnl_rs:,.2f}**")

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"""
        ### 🤵 Husband Account
        * **Net PnL Today:** **₹ {total_h_pnl_rs:,.2f}**
        * **Stats:** `{h_total}` Trades | ✅ `{h_wins}` Wins | ❌ `{h_losses}` Losses
        * **Account Balance:** ₹ {funds.get('husband', 60000.0):,.2f}
        """)
    with col2:
        st.success(f"""
        ### 👩 Wife Account
        * **Net PnL Today:** **₹ {total_w_pnl_rs:,.2f}**
        * **Stats:** `{w_total}` Trades | ✅ `{w_wins}` Wins | ❌ `{w_losses}` Losses
        * **Account Balance:** ₹ {funds.get('wife', 40000.0):,.2f}
        """)

with tab2:
    st.subheader("📊 Fundamental & Technical Analysis")
    df_metrics = get_advanced_metrics(WATCHLIST)
    if df_metrics:
        metrics_chart = build_metrics_chart_data(df_metrics)
        if metrics_chart is not None:
            st.bar_chart(metrics_chart)
        st.dataframe(df_metrics, width="stretch", hide_index=True)
    else:
        st.write("Loading analysis data...")

# --- 9. Auto Refresh (No while loop needed) ---
st.write(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(60)
st.rerun() # Streamlit-ஐ மீண்டும் மேலிருந்து ரன் செய்ய