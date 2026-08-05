import datetime

try:
    import requests
except Exception:  # pragma: no cover - environment-dependent
    requests = None

try:
    import yfinance as yf
except Exception:  # pragma: no cover - environment-dependent
    yf = None

TOKEN = "8272836968:AAFIiPvIvFRSELJ5RFlqzYm4rOkzgDsJr5o"
CHAT_ID = "6114756103"


def get_fii_dii_data():
    if requests is None:
        return "FII/DII data unavailable in this environment."

    url = "https://www.nseindia.com/api/fiidiiTodayStats"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        response = session.get(url, headers=headers, timeout=10)
    except Exception:
        return "FII/DII data temporarily unavailable."

    if response.status_code == 200:
        data = response.json()
        fii_net = data[-1]['fiiNetInvestment']
        dii_net = data[-1]['diiNetInvestment']
        return f"🟢 DII: {dii_net} Cr | 🔴 FII: {fii_net} Cr"
    return "FII/DII data currently unavailable."


def get_live_market_data():
    if yf is None:
        return "Market data is unavailable because yfinance is not installed."

    today = datetime.datetime.now().strftime("%Y-%m-%d | %I:%M %p")
    today_date = datetime.datetime.now().strftime("%B %d, %Y")

    oil = yf.Ticker("BZ=F")
    oil_price = oil.history(period="1d")['Close'].iloc[-1]

    nifty = yf.Ticker("^NSEI")
    nifty_price = nifty.history(period="1d")['Close'].iloc[-1]

    fii_dii_info = get_fii_dii_data()
    return (
        f"📊 *DALAL STREET LIVE RADAR ({today})*\n\n"
        f"🟢 *இன்றைய லைவ் மார்க்கெட் அப்டேட் ({today_date}):*\n"
        f"• *Nifty 50:* {nifty_price:.2f} (லைவ் அப்டேட் ப்ரோ!)\n\n"
        f"🌍 *உலகளாவிய நேரலை காரணிகள்:* \n"
        f"• *Brent Crude Oil:* ${oil_price:.2f} (லைவ் டேட்டா).\n\n"
        f"🏦 *FII / DII ஆக்டிவிட்டி:* \n"
        f"• {fii_dii_info}\n\n"
        f"🎯 *அல்கோ ட்ரேடிங் சிக்னல்:* \n"
        f"அல்கோ இன்ஜின் இப்போ லைவ் மார்க்கெட்ல ஆக்டிவா இருக்கு!"
    )


def send_to_telegram():
    if requests is None:
        print("Telegram sender disabled because requests is unavailable.")
        return
    text = get_live_market_data()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)


def main():
    print(get_live_market_data())


if __name__ == "__main__":
    main()