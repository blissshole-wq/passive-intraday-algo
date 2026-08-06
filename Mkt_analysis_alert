import os
import sys
import time
import requests
import yfinance as yf
import datetime

# Use ANALYZE secrets
TOKEN = os.getenv("ANALYZE_BOT_TOKEN")
CHAT_ID = os.getenv("ANALYZE_CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("❌ Missing ANALYZE_BOT_TOKEN or ANALYZE_CHAT_ID")
    sys.exit(1)

def get_ist_time():
    utc_now = datetime.datetime.utcnow()
    return utc_now + datetime.timedelta(hours=5, minutes=30)

def get_ist_time_str():
    ist_time = get_ist_time()
    return ist_time.strftime('%d-%b-%Y | %I:%M %p')

def send_telegram_msg(text, chat_id=CHAT_ID):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload).json()
        if res.get("ok"):
            print("✅ Message sent!")
        else:
            print(f"❌ Error: {res.get('description')}")
    except Exception as e:
        print(f"Error: {e}")

def analyze_stock(symbol):
    # Your analyze function here
    return f"📊 *{symbol}* - Analysis ready"

def analyze_watchlist():
    # Your watchlist function here
    return "📋 *Watchlist* - Ready"

def handle_bot_commands():
    print("🤖 Analyze Bot is running 24/7...")
    print(f"🕐 IST: {get_ist_time_str()}")
    print("=" * 60)
    
    last_update_id = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=10"
            res = requests.get(url, timeout=15).json()

            if not res.get("ok"):
                time.sleep(5)
                continue

            results = res.get("result", [])
            for result in results:
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

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(3)

        time.sleep(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Analyze Bot Starting...")
    print(f"🕐 IST: {get_ist_time_str()}")
    print("=" * 60)
    handle_bot_commands()