from datetime import datetime 
from zoneinfo import ZoneInfo
import os
import pytz
import requests
import sys
import yfinance as yf

# துல்லியமான இந்திய நேரம் (IST) எடுக்க:
ist_time = datetime.now(ZoneInfo("Asia/Kolkata"))
current_time = ist_time.strftime('%d-%b-%Y | %I:%M %p')

# GitHub Secrets
TOKEN = os.getenv("SUMMARY_BOT_TOKEN")
CHAT_ID = os.getenv("SUMMARY_CHAT_ID")

WATCHLIST = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BEL.NS", "BPCL.NS",
    "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS",
    "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
    "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS",
    "LT.NS", "LTM.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS",
    "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS",
    "SHRIRAMFIN.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS",
    "TMPV.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS",
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
    msg = "📋 *YOUR WATCHLIST HEALTH MATRIX*\n" + "—" * 25 + "\n\n"
    
    # 1. காலியான லிஸ்ட் ஒன்றை முதலில் உருவாக்கவும்
    stock_results = []
    
    for symbol in WATCHLIST:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info or {}
            de_ratio = (info.get("debtToEquity") or 0) / 100
            roe = (info.get("returnOnEquity") or 0) * 100
            pe = info.get("trailingPE", 0) or 0

            score = 0
            if roe >= 15 and de_ratio < 0.5:
                score += 25
            if pe > 0 and pe < 25:
                score += 25
            # (உங்களது மற்ற ஸ்கோர் கண்டிஷன்கள் இங்கே தொடரும்...)

            # ஸ்டேட்டஸ் நிர்ணயிப்பது
            if score >= 75:
                status = "🟢 Excellent"
            elif score >= 50:
                status = "🟡 Moderate"
            else:
                status = "🔴 Weak"

            # தற்போதைய பங்கு விலையை எடுக்கும் பகுதி (உங்களது கோடில் உள்ளபடி)
            # ...
            
            # 2. கணக்கிட்ட தகவல்களை லிஸ்ட்டில் சேர்க்கவும்
            stock_results.append({
                "symbol": symbol.replace(".NS", ""),
                "score": score,
                "status": status,
                "text_line": f"• {symbol.replace('.NS', '')}: Score {score}/100 ({status})\n"
            })
            
        except Exception as e:
            print(f"Error on {symbol}: {e}")

    # 3. Score அடிப்படையில் உயர்ந்ததிலிருந்து குறைவாக (Descending) சார்ட் செய்ய:
    stock_results = sorted(stock_results, key=lambda x: x["score"], reverse=True)

    # 4. வரிசைப்படுத்தப்பட்ட பட்டியலை மெசேஜில் இணைக்க:
    for item in stock_results:
        msg += item["text_line"]

    return msg

def send_morning_alert():
    print("🌅 Sending Morning Alert...")
    try:
        today = datetime.now().strftime("%d-%b-%Y | %I:%M %p")
        
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

        msg = (
            f"🌅 *காலை சர்வதேச சந்தை அறிக்கை (10:30 AM)*\n"
            f"📆 *நேரம்:* {today}\n\n"
            f"🌍 *உலகளாவிய காரணிகள் (Global Macro):*\n"
            f"• *Gold (Comex):* ${gold_price:.2f}\n"
            f"• *Brent Crude Oil:* ${oil_price:.2f}\n"
            f"• *USD / INR:* ₹{usdinr_price:.2f} ({usdinr_emoji} {usdinr_pct:+.2f}%)\n\n"
            f"📊 *இந்திய சந்தை நிலவரம்:*\n"
            f"• *Nifty 50:* {nifty_price:.2f} ({nifty_emoji} {nifty_pct:+.2f}%)\n\n"
            f"💡 *குறிப்பு: கவனமாக வர்த்தகம் செய்யுங்கள்!*"
        )
        send_telegram_msg(msg)
    except Exception as e:
        print(f"Error in morning alert: {e}")

def send_evening_alert():
    print("🌆 Sending Evening Alert...")
    try:
        today = datetime.now().strftime("%d-%b-%Y | %I:%M %p")
        
        gold = yf.Ticker("GC=F").history(period="2d")
        oil = yf.Ticker("BZ=F").history(period="2d")
        usdinr = yf.Ticker("INR=X").history(period="2d")
        nifty = yf.Ticker("^NSEI").history(period="2d")
        sensex = yf.Ticker("^BSESN").history(period="2d")

        def get_closing_data(ticker_obj):
            if not ticker_obj.empty and len(ticker_obj) >= 1:
                price = ticker_obj["Close"].iloc[-1]
                prev = ticker_obj["Close"].iloc[-2] if len(ticker_obj) > 1 else price
                pct = ((price - prev) / prev) * 100 if prev else 0
                emoji = "🟢" if pct >= 0 else "🔴"
                return price, pct, emoji
            return 0.0, 0.0, "⚪"

        gold_price, gold_pct, gold_emoji = get_closing_data(gold)
        oil_price, oil_pct, oil_emoji = get_closing_data(oil)
        usdinr_price, usdinr_pct, usdinr_emoji = get_closing_data(usdinr)
        nifty_price, nifty_pct, nifty_emoji = get_closing_data(nifty)
        sensex_price, sensex_pct, sensex_emoji = get_closing_data(sensex)

        watchlist_data = analyze_watchlist()

        msg = (
            f"🌆 *மாலை சந்தை நிறைவு அறிக்கை (4:00 PM Summary)*\n"
            f"📆 *நேரம்:* {current_time}\n"
            f"📊 *இந்திய சந்தை முடிவு (Indian Market Closing):*\n"
            f"• *Nifty 50:* {nifty_price:.2f} ({nifty_emoji} {nifty_pct:+.2f}%)\n"
            f"• *Sensex:* {sensex_price:.2f} ({sensex_emoji} {sensex_pct:+.2f}%)\n\n"
            f"🌍 *சர்வதேச காரணிகள் நிலை (Global Commodities):*\n"
            f"• *Gold (Comex):* ${gold_price:.2f} ({gold_emoji} {gold_pct:+.2f}%)\n"
            f"• *Brent Crude Oil:* ${oil_price:.2f} ({oil_emoji} {oil_pct:+.2f}%)\n"
            f"• *USD / INR:* ₹{usdinr_price:.2f} ({usdinr_emoji} {usdinr_pct:+.2f}%)\n\n"
        )

        if watchlist_data:
            msg += f"📋 *Watchlist பங்குகள் நிலவரம்:*\n{watchlist_data}\n\n"

        msg += "✨ *இன்றைய வர்த்தக நாள் இனிதே நிறைவுற்றது*!"

        send_telegram_msg(msg)
    except Exception as e:
        print(f"Error in evening alert: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "morning":
            send_morning_alert()
        elif mode == "evening":
            send_evening_alert()