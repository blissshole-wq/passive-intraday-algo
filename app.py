import os
import threading
import time
import requests
import yfinance as yf
from flask import Flask, jsonify

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set!")
    exit(1)

def send_telegram_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
        print("✅ Message sent")
    except Exception as e:
        print(f"Error: {e}")

def analyze_stock(symbol):
    return f"📊 *{symbol}* - Analysis complete"

def watchlist():
    return "📋 *Watchlist* - 10 stocks"

def bot_listener():
    print("🤖 Bot is running 24/7...")
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
                    send_telegram_msg("👋 *Welcome to Market Bot!*\n\nCommands:\n/analyze - Stock analysis\n/watchlist - Health scores\n/time - Current time")
                
                elif text == "/time":
                    send_telegram_msg("🕐 Bot is running 24/7 on Render!")
                
                elif text == "/watchlist":
                    send_telegram_msg("⏳ Scanning watchlist...")
                    report = watchlist()
                    send_telegram_msg(report)
                
                elif text.startswith("/analyze"):
                    parts = text.split()
                    if len(parts) > 1:
                        stock = parts[1]
                        send_telegram_msg(f"⏳ Analyzing *{stock}*...")
                        report = analyze_stock(stock)
                        send_telegram_msg(report)
                    else:
                        send_telegram_msg("Usage: `/analyze RELIANCE`")
                        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(3)
        
        time.sleep(1)

@app.route('/')
def home():
    return {"status": "Bot is running 24/7 on Render!"}

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

if __name__ == "__main__":
    print("🚀 Bot starting...")
    
    # Start bot in background
    bot_thread = threading.Thread(target=bot_listener)
    bot_thread.daemon = True
    bot_thread.start()
    print("✅ Bot thread started")
    
    # Start Flask server
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ Flask server starting on port {port}")
    app.run(host="0.0.0.0", port=port)