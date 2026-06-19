import yfinance as yf
import datetime
import requests


TOKEN = "8272836968:AAFIiPvIvFRSELJ5RFlqzYm4rOkzgDsJr5o"
CHAT_ID = "6114756103"

import requests

def get_fii_dii_data():
    url = "https://www.nseindia.com/api/fiidiiTodayStats"
    # NSE-க்கு நாம ஒரு பிரவுசர் மாதிரி காட்டணும், இல்லன்னா பிளாக் பண்ணிடுவாங்க
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    # முதல்ல NSE மெயின் பேஜை ஒரு வாட்டி ஹிட் பண்ணி குக்கீஸை எடுத்துக்கணும்
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    
    # இப்போ டேட்டா லிங்க்கை ஹிட் பண்ணுவோம்
    response = session.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        # இப்போ நமக்கு வேணுங்கற வேல்யூவை மட்டும் எடுக்கலாம்
        fii_net = data[-1]['fiiNetInvestment']
        dii_net = data[-1]['diiNetInvestment']
        return f"🟢 DII: {dii_net} Cr | 🔴 FII: {fii_net} Cr"
    else:
        return "FII/DII டேட்டா தற்போது கிடைக்கவில்லை."

def get_live_market_data():
    today = datetime.datetime.now().strftime("%Y-%m-%d | %I:%M %p")
    today_date = datetime.datetime.now().strftime("%B %d, %Y")
    
    # yfinance மூலம் டேட்டா எடுப்போம்
    # Oil (BZ=F), Gold (GC=F), Nifty (^NSEI)
    oil = yf.Ticker("BZ=F")
    oil_price = oil.history(period="1d")['Close'].iloc[-1]
    
    nifty = yf.Ticker("^NSEI")
    nifty_price = nifty.history(period="1d")['Close'].iloc[-1]

    # FII/DII டேட்டாவை இங்கே கால் பண்ணுங்க!
    fii_dii_info = get_fii_dii_data()

    report = (
        f"📊 *DALAL STREET LIVE RADAR ({today})*\n\n"
        f"🟢 *இன்றைய லைவ் மார்க்கெட் அப்டேட் ({today_date}):*\n"
        f"• *Nifty 50:* {nifty_price:.2f} (லைவ் அப்டேட் ப்ரோ!)\n\n"
        
        f"🌍 *உலகளாவிய நேரலை காரணிகள்:* \n"
        f"• *Brent Crude Oil:* ${oil_price:.2f} (லைவ் டேட்டா).\n\n"
        
        f"🏦 *FII / DII ஆக்டிவிட்டி:* \n"
        f"• {fii_dii_info}\n\n" # இங்கே அந்த வேரியபிளை மாத்துங்க
        
        f"🎯 *அல்கோ ட்ரேடிங் சிக்னல்:* \n"
        f"அல்கோ இன்ஜின் இப்போ லைவ் மார்க்கெட்ல ஆக்டிவா இருக்கு!"
    )
    return report

def send_to_telegram():
    text = get_live_market_data()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    send_to_telegram()