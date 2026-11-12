import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta 
import requests
import os

# --- 1. டெலிகிராம் அலர்ட் ஃபங்க்ஷன் ---
def send_telegram_alert(message):
    bot_token = os.environ.get("BOT_TOKEN") 
    chat_id = os.environ.get("CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        print("Telegram Error:", e)

# --- 2. டெக்னிக்கல் செக் (Chart Analysis) ---
def check_technical_setup(symbol):
    ticker = yf.Ticker(f"{symbol}.NS")
    df = ticker.history(period="3mo", interval="1d")
    
    if df.empty:
        return False, "Data not found"

    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    latest_close = df['Close'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1]
    rsi = df['RSI'].iloc[-1]

    # டெக்னிக்கல் லாஜிக்: விலை 20SMA-க்கு மேல + RSI 60-க்கு கீழ (Not overbought)
    if latest_close > sma_20 and rsi < 60:
        return True, f"Price: ₹{latest_close:.2f} | RSI: {rsi:.2f}"
    else:
        return False, f"Failed Tech Check (RSI: {rsi:.2f})"

# --- 3. மெயின் ஸ்கேனர் (Confluence Engine) ---
def run_confluence_scanner():
    print("Starting Confluence Scanner...")
    
    # ஃபண்டமெண்டல் படி ஸ்டாக்ஸ் எடு (தற்போதைக்கு இவை ஹார்ட்-கோட் செய்யப்பட்டுள்ளன)
    fundamental_stocks = ["HAL", "TATAPOWER", "NMDC"]
    
    best_buy_picks = []
    
    # டெக்னிக்கல் படி செக் பண்ணு
    for stock in fundamental_stocks:
        print(f"Checking {stock}...")
        is_tech_good, details = check_technical_setup(stock)
        
        if is_tech_good:
            best_buy_picks.append(f"✅ *{stock}*\nNews: Good | Chart: {details}")
            
    # ரெண்டும் பொருந்தினா மட்டும் அலர்ட் அனுப்பு
    if best_buy_picks:
        alert_message = "🔥 *CONFLUENCE BUY ALERTS!* (News + Tech)\n\n" + "\n\n".join(best_buy_picks)
        send_telegram_alert(alert_message)
        print("Alerts sent to Telegram!")
    else:
        print("No Confluence setups found today.")

if __name__ == "__main__":
    run_confluence_scanner()