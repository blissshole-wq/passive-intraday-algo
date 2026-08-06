import sys
import datetime
import time
import requests
import yfinance as yf
import pytz
import os

# FORCE IST TIMEZONE
os.environ['TZ'] = 'Asia/Kolkata'
try:
    time.tzset()
except:
    pass

# Telegram Credentials
TOKEN = "8808327706:AAGamqaWXerHYJ8Ioq0wO7uP4r-DbFTSBcU"
CHAT_ID = "6114756103"

# IST Timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    try:
        return datetime.datetime.now(IST)
    except:
        utc_now = datetime.datetime.utcnow()
        return utc_now + datetime.timedelta(hours=5, minutes=30)

def get_ist_time_str():
    ist_time = get_ist_time()
    return ist_time.strftime('%d-%b-%Y | %I:%M %p')

# ============================================
# WATCHLIST - Nifty 50 Stocks
# ============================================
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

def send_telegram_msg(text, chat_id=CHAT_ID):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload).json()
        if res.get("ok"):
            print("✅ Telegram message sent successfully!")
        else:
            print(f"❌ Telegram Error: {res.get('description')}")
    except Exception as e:
        print(f"Error sending msg: {e}")

def get_ticker_data(symbol):
    """Get current price and change % for a symbol"""
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

def analyze_watchlist():
    """Get watchlist health scores"""
    msg = "📋 *WATCHLIST HEALTH MATRIX*\n━━━━━━━━━━━━━━━━━━━\n"
    count = 0
    
    for symbol in WATCHLIST[:10]:  # First 10 stocks to avoid timeout
        try:
            stock = yf.Ticker(symbol)
            info = stock.info or {}
            
            # Get fundamental data
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
            
            # Status
            if score >= 75:
                status = "🟢 Excellent"
            elif score >= 50:
                status = "🟡 Moderate"
            else:
                status = "🔴 Weak"
            
            # Price info
            price_info = get_ticker_data(symbol)
            name = symbol.replace('.NS', '').replace('.BO', '')
            
            msg += f"• *{name}:* ₹{price_info} | Score `{score}/100` ({status})\n"
            count += 1
            
        except Exception as e:
            name = symbol.replace('.NS', '').replace('.BO', '')
            msg += f"• *{name}:* ⚠️ Data unavailable\n"
    
    msg += f"\n📊 *Showing {count} stocks* (Limited to avoid timeout)"
    msg += "\n💡 *Tip:* Use `/analyze STOCK` for detailed report"
    return msg

def analyze_stock(symbol):
    """Detailed analysis for a single stock"""
    try:
        raw_symbol = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        stock = yf.Ticker(f"{raw_symbol}.NS")
        info = stock.info or {}
        hist = stock.history(period="5d")
        
        if hist.empty:
            return f"❌ *{raw_symbol}* data not found"
        
        current_price = hist["Close"].iloc[-1]
        company_name = info.get("shortName") or info.get("longName") or raw_symbol
        mcap = info.get("marketCap", 0) / 10**7 if info.get("marketCap") else 0
        pe = info.get("trailingPE", 0) or 0
        de_ratio = (info.get("debtToEquity") or 0) / 100
        roe = (info.get("returnOnEquity") or 0) * 100
        promoter_hold = (info.get("heldPercentInsiders") or 0) * 100
        net_income = info.get("netIncomeToCommon", 0) or 0
        operating_cf = info.get("operatingCashflow", 0) or 0
        
        # Calculate score
        score = 0
        insights = []
        
        if roe >= 15 and de_ratio < 0.5:
            score += 25
            insights.append("🟢 *Strong Efficiency:* High ROE (>15%) & Low Debt")
        elif de_ratio > 1.5:
            insights.append("🔴 *High Debt Risk:* D/E Ratio >1.5")
        
        if operating_cf > 0 and operating_cf >= net_income:
            score += 25
            insights.append("🟢 *Real Cash Profit:* Cash Flow >= Net Profit")
        elif operating_cf > 0:
            insights.append("🟡 *Paper Profit Warning:* OCF < Net Profit")
        
        if promoter_hold >= 40:
            score += 25
            insights.append(f"🟢 *Promoter Holding:* Good ({promoter_hold:.1f}%)")
        
        if 0 < pe < 35:
            score += 25
            insights.append(f"🟢 *Valuation:* Fair P/E ({pe:.1f})")
        
        if not insights:
            insights.append("ℹ️ Real-time price fetched")
        
        macro = "🚀 *Rate Cut Impact:* POSITIVE" if de_ratio > 0.8 else "🛡️ *Rate Cut Impact:* STABLE"
        
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
        return f"❌ Error analyzing {symbol}: {e}"

def send_morning_alert():
    print("🌅 Sending Morning Alert...")
    try:
        today = get_ist_time_str()
        print(f"📅 IST Time: {today}")
        
        # Get market data
        gold = yf.Ticker("GC=F").history(period="2d")
        oil = yf.Ticker("BZ=F").history(period="2d")
        usdinr = yf.Ticker("INR=X").history(period="2d")
        nifty = yf.Ticker("^NSEI").history(period="2d")

        gold_price = gold["Close"].iloc[-1] if not gold.empty else 0
        oil_price = oil["Close"].iloc[-1] if not oil.empty else 0

        usdinr_price = usdinr["Close"].iloc[-1] if not usdinr.empty else 0
        usdinr_prev = usdinr["Close"].iloc[-2] if len(usdinr) > 1 else usdinr_price
        usdinr_pct = ((usdinr_price - usdinr_prev) / usdinr_prev) * 100 if usdinr_prev else 0
        usdinr_emoji = "🟢" if usdinr_pct >= 0 else "🔴"

        nifty_price = nifty["Close"].iloc[-1] if not nifty.empty else 0
        nifty_prev = nifty["Close"].iloc[-2] if len(nifty) > 1 else nifty_price
        nifty_pct = ((nifty_price - nifty_prev) / nifty_prev) * 100 if nifty_prev else 0
        nifty_emoji = "🟢" if nifty_pct >= 0 else "🔴"

        # ✅ Get watchlist data
        print("⏳ Fetching watchlist data...")
        watchlist_data = analyze_watchlist()

        msg = (
            f"🌅 *காலை சர்வதேச சந்தை அறிக்கை (10:30 AM)*\n"
            f"📆 *நேரம்:* {today} IST\n\n"
            f"🌍 *உலகளாவிய காரணிகள் (Global Macro):*\n"
            f"• *Gold (Comex):* ${gold_price:.2f}\n"
            f"• *Brent Crude Oil:* ${oil_price:.2f}\n"
            f"• *USD / INR:* ₹{usdinr_price:.2f} ({usdinr_emoji} {usdinr_pct:+.2f}%)\n\n"
            f"📊 *இந்திய சந்தை நிலவரம்:*\n"
            f"• *Nifty 50:* {nifty_price:.2f} ({nifty_emoji} {nifty_pct:+.2f}%)\n\n"
            f"{watchlist_data}\n\n"
            f"💡 *குறிப்பு: கவனமாக வர்த்தகம் செய்யுங்கள்!*"
        )
        
        send_telegram_msg(msg)
        print(f"✅ Morning alert sent at {today}")
    except Exception as e:
        print(f"❌ Error: {e}")

def send_evening_alert():
    print("🌆 Sending Evening Alert...")
    try:
        today = get_ist_time_str()
        print(f"📅 IST Time: {today}")
        
        # Get market data
        gold = yf.Ticker("GC=F").history(period="2d")
        oil = yf.Ticker("BZ=F").history(period="2d")
        usdinr = yf.Ticker("INR=X").history(period="2d")
        nifty = yf.Ticker("^NSEI").history(period="2d")
        sensex = yf.Ticker("^BSESN").history(period="2d")

        def get_data(ticker_obj):
            if not ticker_obj.empty and len(ticker_obj) >= 1:
                price = ticker_obj["Close"].iloc[-1]
                prev = ticker_obj["Close"].iloc[-2] if len(ticker_obj) > 1 else price
                pct = ((price - prev) / prev) * 100 if prev else 0
                emoji = "🟢" if pct >= 0 else "🔴"
                return price, pct, emoji
            return 0.0, 0.0, "⚪"

        gold_price, gold_pct, gold_emoji = get_data(gold)
        oil_price, oil_pct, oil_emoji = get_data(oil)
        usdinr_price, usdinr_pct, usdinr_emoji = get_data(usdinr)
        nifty_price, nifty_pct, nifty_emoji = get_data(nifty)
        sensex_price, sensex_pct, sensex_emoji = get_data(sensex)

        # ✅ Get watchlist data
        print("⏳ Fetching watchlist data...")
        watchlist_data = analyze_watchlist()

        msg = (
            f"🌆 *மாலை சந்தை நிறைவு அறிக்கை (4:00 PM Summary)*\n"
            f"📆 *நேரம்:* {today} IST\n\n"
            f"📊 *இந்திய சந்தை முடிவு:*\n"
            f"• *Nifty 50:* {nifty_price:.2f} ({nifty_emoji} {nifty_pct:+.2f}%)\n"
            f"• *Sensex:* {sensex_price:.2f} ({sensex_emoji} {sensex_pct:+.2f}%)\n\n"
            f"🌍 *சர்வதேச காரணிகள்:*\n"
            f"• *Gold:* ${gold_price:.2f} ({gold_emoji} {gold_pct:+.2f}%)\n"
            f"• *Brent Crude:* ${oil_price:.2f} ({oil_emoji} {oil_pct:+.2f}%)\n"
            f"• *USD/INR:* ₹{usdinr_price:.2f} ({usdinr_emoji} {usdinr_pct:+.2f}%)\n\n"
            f"{watchlist_data}\n\n"
            f"✨ *இன்றைய வர்த்தக நாள் இனிதே நிறைவுற்றது!*"
        )

        send_telegram_msg(msg)
        print(f"✅ Evening alert sent at {today}")
    except Exception as e:
        print(f"❌ Error: {e}")

# ============================================
# TELEGRAM BOT COMMANDS
# ============================================
def handle_bot_commands():
    print("🤖 Bot listening for commands...")
    print(f"🕐 Current IST: {get_ist_time_str()}")
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
                        "👋 *வணக்கம்! AI Market Assistant*\n\n"
                        f"🕐 *IST:* {get_ist_time_str()}\n\n"
                        "📌 *Commands:*\n"
                        "• `/watchlist` - Health scores\n"
                        "• `/analyze STOCK` - Detailed report\n"
                        "• `/time` - Current IST\n"
                        "• `/morning` - Morning alert\n"
                        "• `/evening` - Evening alert"
                    )
                    send_telegram_msg(welcome, chat_id)

                elif text == "/time":
                    send_telegram_msg(f"🕐 *IST:* {get_ist_time_str()}", chat_id)

                elif text == "/watchlist":
                    send_telegram_msg("⏳ Scanning watchlist...", chat_id)
                    report = analyze_watchlist()
                    send_telegram_msg(report, chat_id)

                elif text.startswith("/analyze"):
                    parts = text.split()
                    if len(parts) > 1:
                        stock = parts[1]
                        send_telegram_msg(f"⏳ Analyzing *{stock}*...", chat_id)
                        report = analyze_stock(stock)
                        send_telegram_msg(report, chat_id)
                    else:
                        send_telegram_msg("⚠️ Usage: `/analyze RELIANCE`", chat_id)

                elif text == "/morning":
                    send_morning_alert()

                elif text == "/evening":
                    send_evening_alert()

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(3)
        time.sleep(1)

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Market Alert Bot")
    print(f"🕐 IST: {get_ist_time_str()}")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "morning":
            send_morning_alert()
        elif mode == "evening":
            send_evening_alert()
        else:
            print(f"❌ Unknown mode: {mode}")
    else:
        handle_bot_commands()