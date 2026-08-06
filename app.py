import os
import threading
import time
import requests
import yfinance as yf
from flask import Flask, jsonify
import datetime

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set!")
    exit(1)

def get_ist_time():
    utc_now = datetime.datetime.utcnow()
    return utc_now + datetime.timedelta(hours=5, minutes=30)

def get_ist_time_str():
    ist_time = get_ist_time()
    return ist_time.strftime('%d-%b-%Y | %I:%M %p')

def send_telegram_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def get_ticker_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2d")
        if len(df) >= 2:
            prev_close = df["Close"].iloc[-2]
            curr_price = df["Close"].iloc[-1]
            change = curr_price - prev_close
            pct_change = (change / prev_close) * 100
            flag = "🟢 +" if change >= 0 else "🔴 "
            return f"{curr_price:.2f} ({flag}{pct_change:.2f}%)"
        elif len(df) == 1:
            return f"{df['Close'].iloc[-1]:.2f}"
    except Exception:
        pass
    return "N/A"

def analyze_stock(symbol):
    raw_symbol = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
    symbols_to_try = [f"{raw_symbol}.NS", f"{raw_symbol}.BO"]

    stock = None
    info = {}
    valid_symbol = None
    hist = None

    for sym in symbols_to_try:
        try:
            temp_stock = yf.Ticker(sym)
            temp_hist = temp_stock.history(period="5d")
            if temp_hist is not None and not temp_hist.empty:
                stock = temp_stock
                hist = temp_hist
                valid_symbol = sym
                try:
                    info = temp_stock.info or {}
                except Exception:
                    info = {}
                break
        except Exception:
            continue

    if not stock or hist is None or hist.empty:
        return f"❌ *{raw_symbol}* data not found"

    try:
        current_price = hist["Close"].iloc[-1]
        company_name = info.get("shortName") or info.get("longName") or raw_symbol
        mcap = info.get("marketCap", 0) / 10**7 if info.get("marketCap") else 0
        pe = info.get("trailingPE", 0) or 0
        de_ratio = (info.get("debtToEquity") or 0) / 100
        roe = (info.get("returnOnEquity") or 0) * 100
        promoter_hold = (info.get("heldPercentInsiders") or 0) * 100
        net_income = info.get("netIncomeToCommon", 0) or 0
        operating_cf = info.get("operatingCashflow", 0) or 0

        score = 0
        insights = []

        if roe >= 15 and de_ratio < 0.5:
            score += 25
            insights.append("🟢 Strong Efficiency: High ROE (>15%) & Low Debt")
        elif de_ratio > 1.5:
            insights.append("🔴 High Debt Risk: D/E Ratio >1.5")

        if operating_cf > 0 and operating_cf >= net_income:
            score += 25
            insights.append("🟢 Real Cash Profit: Cash Flow >= Net Profit")
        elif operating_cf > 0:
            insights.append("🟡 Paper Profit Warning: OCF < Net Profit")

        if promoter_hold >= 40:
            score += 25
            insights.append(f"🟢 Promoter Holding: Good ({promoter_hold:.1f}%)")

        if 0 < pe < 35:
            score += 25
            insights.append(f"🟢 Valuation: Fair P/E ({pe:.1f})")

        if not insights:
            insights.append("ℹ️ Real-time price fetched")

        if de_ratio > 0.8:
            macro = "🚀 Rate Cut Impact: POSITIVE"
        else:
            macro = "🛡️ Rate Cut Impact: STABLE"

        mcap_str = f"₹{mcap:,.0f} Cr" if mcap > 0 else "N/A"
        pe_str = f"{pe:.2f}" if pe > 0 else "N/A"
        de_str = f"{de_ratio:.2f}" if de_ratio > 0 else "N/A"

        report = (
            f"📊 *DEEP MATRIX REPORT: {company_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💵 *Price:* ₹{current_price:,.2f}\n"
            f"🏢 *Market Cap:* {mcap_str}\n"
            f"📊 *P/E:* {pe_str} | *D/E:* {de_str}\n"
            f"📈 *ROE:* {roe:.2f}% | *Promoter:* {promoter_hold:.1f}%\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *HEALTH SCORE:* `{score} / 100`\n\n"
            f"📌 *INSIGHTS:*\n" + "\n".join([f"• {i}" for i in insights]) +
            f"\n\n🌐 *PREDICTION:*\n• {macro}"
        )
        return report

    except Exception as e:
        return f"❌ Error: {e}"

def analyze_watchlist():
    WATCHLIST = [
        "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
        "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BEL.NS", "BPCL.NS",
        "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS",
        "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS",
        "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
        "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWMETAL.NS", "KOTAKBANK.NS",
        "LT.NS", "LTIM.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS",
        "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS",
        "SHRIRAMFIN.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS",
        "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS",
        "WIPRO.NS", "NATIONALUM.NS",
    ]
    
    # Create list to store stock data
    stock_data = []
    
    for symbol in WATCHLIST[:10]:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info or {}
            
            de_ratio = (info.get("debtToEquity") or 0) / 100
            roe = (info.get("returnOnEquity") or 0) * 100
            pe = info.get("trailingPE", 0) or 0
            promoter = (info.get("heldPercentInsiders") or 0) * 100
            ocf = info.get("operatingCashflow") or 0
            net_income = info.get("netIncomeToCommon") or 0
            
            # Calculate score
            score = 0
            if roe >= 15 and de_ratio < 0.5:
                score += 25
            if ocf >= net_income and ocf > 0:
                score += 25
            if promoter >= 40:
                score += 25
            if 0 < pe < 35:
                score += 25
            
            # Determine status
            if score >= 75:
                status = "🟢 Excellent"
                status_order = 1
            elif score >= 50:
                status = "🟡 Moderate"
                status_order = 2
            else:
                status = "🔴 Weak"
                status_order = 3
            
            price_info = get_ticker_data(symbol)
            name = symbol.replace('.NS', '').replace('.BO', '')
            
            # Store data with status order
            stock_data.append({
                'name': name,
                'price_info': price_info,
                'score': score,
                'status': status,
                'status_order': status_order
            })
            
        except Exception:
            name = symbol.replace('.NS', '').replace('.BO', '')
            stock_data.append({
                'name': name,
                'price_info': '⚠️ Data unavailable',
                'score': 0,
                'status': '❌ Error',
                'status_order': 4
            })
    
    # ✅ Sort by status_order (Excellent first, then Moderate, then Weak)
    stock_data.sort(key=lambda x: x['status_order'])
    
    # Build message
    msg = "📋 *WATCHLIST HEALTH MATRIX*\n━━━━━━━━━━━━━━━━━━━\n"
    count = 0
    
    for stock in stock_data:
        msg += f"• *{stock['name']}:* ₹{stock['price_info']} | Score `{stock['score']}/100` ({stock['status']})\n"
        count += 1
    
    msg += f"\n📊 *Showing {count} stocks*"
    msg += "\n💡 *Tip:* Use `/analyze STOCK` for detailed report"
    return msg

def bot_listener():
    print("🤖 Bot is running 24/7...")
    print(f"🕐 IST: {get_ist_time_str()}")
    last_update_id = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=10"
            res = requests.get(url, timeout=15).json()
            
            if not res.get("ok"):
                time.sleep(5)
                continue
            
            for result in res.get("result", []):
                last_update_id = result["update_id"]
                message = result.get("message", {})
                text = message.get("text", "").strip()
                chat_id = message.get("chat", {}).get("id")
                
                if not text or not chat_id:
                    continue
                
                if text == "/start":
                    welcome = (
                        f"👋 *வணக்கம்! AI Market Assistant*\n\n"
                        f"🕐 *IST:* {get_ist_time_str()}\n\n"
                        f"📌 *Commands:*\n"
                        f"• `/analyze STOCK` - Detailed report\n"
                        f"• `/watchlist` - Health scores\n"
                        f"• `/time` - Current IST\n"
                    )
                    send_telegram_msg(welcome)
                
                elif text == "/time":
                    send_telegram_msg(f"🕐 *IST:* {get_ist_time_str()}")
                
                elif text == "/watchlist":
                    send_telegram_msg("⏳ Scanning watchlist...")
                    report = analyze_watchlist()
                    send_telegram_msg(report)
                
                elif text.startswith("/analyze"):
                    parts = text.split()
                    if len(parts) > 1:
                        stock = parts[1]
                        send_telegram_msg(f"⏳ Analyzing *{stock}*...")
                        report = analyze_stock(stock)
                        send_telegram_msg(report)
                    else:
                        send_telegram_msg("⚠️ Usage: `/analyze RELIANCE`")
                        
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(3)
        
        time.sleep(1)

@app.route('/')
def home():
    return {"status": "Bot is running 24/7 on Render!", "time": get_ist_time_str()}

@app.route('/health')
def health():
    return {"status": "healthy", "time": get_ist_time_str()}, 200

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Bot starting on Render...")
    print(f"🕐 IST: {get_ist_time_str()}")
    print("=" * 60)
    
    # Start bot in background
    bot_thread = threading.Thread(target=bot_listener)
    bot_thread.daemon = True
    bot_thread.start()
    print("✅ Bot thread started")
    
    # Start Flask server
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ Flask server starting on port {port}")
    app.run(host="0.0.0.0", port=port)