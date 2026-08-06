import sys
import datetime
import time
import requests
import yfinance as yf
import pytz
import os

# Telegram Credentials
TOKEN = "8808327706:AAGamqaWXerHYJ8Ioq0wO7uP4r-DbFTSBcU"
CHAT_ID = "6114756103"

# ✅ Debug: Check if token and chat ID are correct
def debug_telegram():
    print("=" * 50)
    print("🔍 Debugging Telegram Connection")
    print(f"Token: {TOKEN[:10]}...{TOKEN[-5:]}")
    print(f"Chat ID: {CHAT_ID}")
    print("=" * 50)
    
    # Test getMe
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url)
        data = response.json()
        if data.get("ok"):
            print(f"✅ Bot connected: {data['result']['first_name']}")
            print(f"✅ Bot username: @{data['result']['username']}")
        else:
            print(f"❌ Bot connection failed: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test send message
    try:
        test_msg = "🧪 Test message from Market Alert Bot"
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": test_msg
        }
        response = requests.post(url, json=payload)
        data = response.json()
        if data.get("ok"):
            print("✅ Test message sent successfully!")
            return True
        else:
            print(f"❌ Send test failed: {data.get('description')}")
            print(f"Full response: {data}")
            return False
    except Exception as e:
        print(f"❌ Error sending test: {e}")
        return False

# ✅ Call debug function
debug_telegram()

# IST Timezone setup
IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    return datetime.datetime.now(IST)

def get_ist_time_str():
    ist_time = get_ist_time()
    return ist_time.strftime('%d-%b-%Y | %I:%M %p')

def send_telegram_msg(text, chat_id=CHAT_ID):
    # ✅ Debug: Print what we're sending
    print(f"📤 Sending to Chat ID: {chat_id}")
    print(f"📝 Message preview: {text[:100]}...")
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        print("⏳ Sending request...")
        res = requests.post(url, json=payload, timeout=10)
        print(f"📊 Response status: {res.status_code}")
        
        data = res.json()
        print(f"📊 Response data: {data}")
        
        if data.get("ok"):
            print("✅ Telegram message sent successfully!")
            return True
        else:
            print(f"❌ Telegram Error: {data.get('description')}")
            print(f"❌ Error code: {data.get('error_code')}")
            
            # ✅ Provide solution suggestions
            if data.get('error_code') == 404:
                print("\n💡 SOLUTION: Bot token is invalid!")
                print("1. Create new bot: @BotFather → /newbot")
                print("2. Copy new token")
                print("3. Update TOKEN variable")
            elif data.get('error_code') == 403:
                print("\n💡 SOLUTION: Bot is blocked by user!")
                print("1. Send /start to your bot in Telegram")
                print("2. Unblock the bot")
            elif data.get('description') and 'chat not found' in data.get('description'):
                print("\n💡 SOLUTION: Chat ID is wrong!")
                print("1. Send any message to your bot")
                print("2. Visit: https://api.telegram.org/bot<TOKEN>/getUpdates")
                print("3. Find your chat_id from response")
            return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - Check internet connection")
        return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

# Rest of your functions...
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

# Update send_morning_alert and send_evening_alert with debug
def send_morning_alert():
    print("🌅 Sending Morning Alert...")
    try:
        today = get_ist_time_str()
        print(f"📅 Current IST: {today}")
        
        # Test Telegram connection first
        print("⏳ Testing Telegram connection...")
        if not debug_telegram():
            print("❌ Telegram connection failed. Check your credentials.")
            return
        
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

        msg = (
            f"🌅 *காலை சர்வதேச சந்தை அறிக்கை (10:30 AM)*\n"
            f"📆 *நேரம்:* {today} IST\n\n"
            f"🌍 *உலகளாவிய காரணிகள் (Global Macro):*\n"
            f"• *Gold (Comex):* ${gold_price:.2f}\n"
            f"• *Brent Crude Oil:* ${oil_price:.2f}\n"
            f"• *USD / INR:* ₹{usdinr_price:.2f} ({usdinr_emoji} {usdinr_pct:+.2f}%)\n\n"
            f"📊 *இந்திய சந்தை நிலவரம்:*\n"
            f"• *Nifty 50:* {nifty_price:.2f} ({nifty_emoji} {nifty_pct:+.2f}%)\n\n"
            f"💡 *குறிப்பு: கவனமாக வர்த்தகம் செய்யுங்கள்!*"
        )
        
        send_telegram_msg(msg)
        print("✅ Morning alert completed")
    except Exception as e:
        print(f"❌ Error in morning alert: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Market Alert Bot - Debug Mode")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "morning":
            send_morning_alert()
        elif mode == "evening":
            # send_evening_alert()
            print("Evening alert function")
        else:
            print(f"❌ Unknown mode: {mode}")
    else:
        print("Usage: python Mkt_summary_alert.py [morning|evening]")