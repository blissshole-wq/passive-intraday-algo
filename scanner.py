import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta 
import requests
import os # <--- இதை சேர்க்கவும்

# --- 1. அலர்ட் அனுப்பும் ஃபங்க்ஷன் ---
def send_telegram_alert(message):
    # ஹார்ட்கோட் செய்யாம, சிஸ்டம்-ல இருந்து எடுக்கும் படி மாத்தியிருக்கோம்
    bot_token = os.environ.get("BOT_TOKEN") 
    chat_id = os.environ.get("CHAT_ID")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        print("Telegram Error:", e)


# --- 2. டெக்னிக்கல் அனாலிசிஸ் செய்யும் ஃபங்க்ஷன் ---
def check_technical_setup(symbol):
    ticker = yf.Ticker(f"{symbol}.NS")
    df = ticker.history(period="3mo", interval="1d")
    
    if df.empty:
        return False, "Data not found"

    # இண்டிகேட்டர்கள் கணக்கிடுதல்
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    latest_close = df['Close'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1]
    rsi = df['RSI'].iloc[-1]

    # லாஜிக்: விலை 20SMA-க்கு மேல இருக்கணும் + RSI 60-க்கு கீழ இருக்கணும்
    if latest_close > sma_20 and rsi < 60:
        return True, f"Price: ₹{latest_close:.2f} | RSI: {rsi:.2f} (Above 20MA)"
    else:
        return False, f"Price: ₹{latest_close:.2f} | RSI: {rsi:.2f} (No Setup)"

# --- 3. மெயின் ஸ்கேனர் லாஜிக் ---
def run_scanner():
    # உங்க படத்துல இருந்து எடுத்த ஸ்டாக்ஸ் லிஸ்ட்
    stock_list = ["HAL", "IDEA", "HITACHI", "ALKEM", "NMDC", "BDL", "PAGEIND", "IRCTC", "MANAPPURAM", "OLAELEC", "TATAPOWER", "HINDCOPPER", "MIDHANI", "GRSE", "POWERMECH", "LALITHA"] 
    
    print("Scanning started...")
    best_picks = []

    for stock in stock_list:
        print(f"Checking {stock}...")
        is_good_trade, details = check_technical_setup(stock)
        
        if is_good_trade:
            best_picks.append(f"✅ *{stock}*\n{details}")

    # --- 4. அலர்ட் அனுப்புதல் ---
    if best_picks:
        alert_message = "🚀 *High Probability Picks Today:*\n\n" + "\n\n".join(best_picks)
        send_telegram_alert(alert_message)
        print("Alerts sent to Telegram!")
    else:
        send_telegram_alert("😴 No High Probability setups found today based on current logic.")
        print("No setups found.")

if __name__ == "__main__":
    run_scanner()