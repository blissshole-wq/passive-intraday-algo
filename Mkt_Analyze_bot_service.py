import sys
import time
import requests
import yfinance as yf

# Telegram Credentials
TOKEN = "8844114153:AAH2ckVvRNm42bkbo0_c2oipsUjuauL4wr4"
CHAT_ID = "6114756103"

# Nifty 50 பங்குகளின் முழுமையான பட்டியல் (Yahoo Finance Tickers)
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
        return f"❌ *{raw_symbol}* பற்றிய விபரங்கள் Yahoo Finance-ல் பெற முடியவில்லை. குறியீட்டு பெயர் (Symbol) சரியா எனச் சரிபார்க்கவும்."

    try:
        current_price = hist["Close"].iloc[-1]
        company_name = info.get("shortName") or info.get("longName") or valid_symbol.replace(".NS", "").replace(".BO", "")
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
            insights.append("🟢 *Strong Efficiency:* High ROE (>15%) & Low Debt.")
        elif de_ratio > 1.5:
            insights.append("🔴 *High Debt Risk:* D/E Ratio is >1.5.")

        if operating_cf > 0 and operating_cf >= net_income:
            score += 25
            insights.append("🟢 *Real Cash Profit:* Cash Flow >= Net Profit.")
        elif operating_cf > 0:
            insights.append("🟡 *Paper Profit Warning:* OCF is lower than Net Profit.")

        if promoter_hold >= 40:
            score += 25
            insights.append(f"🟢 *Promoter Holding:* Good ({promoter_hold:.1f}%).")

        if 0 < pe < 35:
            score += 25
            insights.append(f"🟢 *Valuation:* Fair P/E ({pe:.1f}).")

        if not insights:
            insights.append("ℹ️ நேரலைச் சந்தை விலை பெறப்பட்டது.")

        if de_ratio > 0.8:
            macro = "🚀 *FED/RBI Rate Cut Impact:* POSITIVE!"
        else:
            macro = "🛡️ *FED/RBI Rate Cut Impact:* STABLE"

        mcap_str = f"₹{mcap:,.0f} Cr" if mcap > 0 else "N/A"
        pe_str = f"{pe:.2f}" if pe > 0 else "N/A"
        de_str = f"{de_ratio:.2f}" if de_ratio > 0 else "N/A"

        report = (
            f"📊 *DEEP MATRIX REPORT: {company_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💵 *Current Price:* ₹{current_price:,.2f}\n"
            f"🏢 *Market Cap:* {mcap_str}\n"
            f"📊 *P/E Ratio:* {pe_str} | *D/E Ratio:* {de_str}\n"
            f"📈 *ROE:* {roe:.2f}% | *Promoter Stake:* {promoter_hold:.1f}%\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *HEALTH SCORE:* `{score} / 100`\n\n"
            f"📌 *CORRELATION INSIGHTS:*\n"
            + "\n".join([f"• {i}" for i in insights])
            + f"\n\n🌐 *EVENT-BASED PREDICTION:*\n• {macro}"
        )
        return report

    except Exception as e:
        return f"❌ அறிக்கை உருவாக்குவதில் பிழை: {e}"

def analyze_watchlist():
    msg = "📋 *YOUR WATCHLIST HEALTH MATRIX*\n━━━━━━━━━━━━━━━━━━━\n"
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
            if (info.get("operatingCashflow") or 0) >= (info.get("netIncomeToCommon") or 0):
                score += 25
            if ((info.get("heldPercentInsiders") or 0) * 100) >= 40:
                score += 25
            if 0 < pe < 35:
                score += 25

            status = "🟢 Excellent" if score >= 75 else "🟡 Moderate" if score >= 50 else "🔴 Weak"
            price_info = get_ticker_data(symbol)
            msg += f"• *{symbol.replace('.NS', '')}:* ₹{price_info} | Score `{score}/100` ({status})\n"
        except Exception:
            msg += f"• *{symbol}:* Data unavailable\n"
    msg += "\n💡 *குறிப்பு:* விரிவான அறிக்கைக்கு `/analyze <stock>` என டைப் செய்யவும்."
    return msg

def handle_bot_commands():
    print("🤖 Telegram Bot Agent is listening for commands...")
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
                    welcome_msg = (
                        "👋 *வணக்கம்! உங்கள் AI Market Assistant தயார்!*\n\n"
                        "1️⃣ `/analyze TATAMOTORS` - Matrix Analysis பெற\n"
                        "2️⃣ `/watchlist` - Watchlist Health Score பெற\n"
                    )
                    send_telegram_msg(welcome_msg, chat_id)

                elif text.startswith("/analyze"):
                    parts = text.split()
                    if len(parts) > 1:
                        stock_name = parts[1]
                        send_telegram_msg(f"⏳ *{stock_name}* தரவுகள் சேகரிக்கப்படுகின்றன...", chat_id)
                        report = analyze_stock(stock_name)
                        send_telegram_msg(report, chat_id)
                    else:
                        send_telegram_msg("⚠️ தயவுசெய்து பங்கின் பெயரைச் சேர்க்கவும். (எ.கா: `/analyze RELIANCE`)", chat_id)

                elif text == "/watchlist":
                    send_telegram_msg("⏳ Watchlist ஸ்கேன் செய்யப்படுகிறது...", chat_id)
                    report = analyze_watchlist()
                    send_telegram_msg(report, chat_id)

        except Exception as e:
            print(f"⚠️ Polling Exception: {e}")
            time.sleep(3)

        time.sleep(1)

if __name__ == "__main__":
    handle_bot_commands()