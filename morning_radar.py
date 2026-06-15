import requests
import datetime

# ⚠️ உங்க போட் டோக்கன் மற்றும் சாட் ஐடியை இங்கே போடுங்க ப்ரோ:
TOKEN = "8272836968:AAFIiPvIvFRSELJ5RFlqzYm4rOkzgDsJr5o"
CHAT_ID = "6114756103"

def get_market_summary():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    report = (
        f"📊 *DALAL STREET MORNING RADAR ({today} | 09:30 AM)*\n\n"
        f"🟢 *நேற்றைய இந்திய மார்க்கெட் முடிவு:*\n"
        f"• *Nifty 50:* 23,853.90 (+0.98%)\n"
        f"• *Sensex:* 75,527.95 (+2.30%)\n"
        f"• *மார்க்கெட் பின்னணி:* அமெரிக்கா - ஈரான் அமைதி உடன்படிக்கையினால் ஜியோ-பொலிடிகல் ரிஸ்க் குறைந்து உலகளாவிய சந்தைகளில் அதிரடி ரேலி ஏற்பட்டுள்ளது!\n\n"
        
        f"🏗️ *முக்கிய செக்டார் நிலவரம்:*\n"
        f"• Nifty Auto மற்றும் Nifty IT துறைகள் வலுவான ஏற்றம் கண்டுள்ளன.\n\n"
        
        f"🌍 *உலகளாவிய காரணிகள் (Global Factors):*\n"
        f"• *Brent Crude Oil:* $83.00 (பீஸ் டீல் காரணமாக 4.7% சரிவு! இந்தியாவுக்கு செம பாசிட்டிவ்)\n"
        f"• *US Fed Rate:* 3.5% - 3.75% என்ற வரம்பில் தற்போதைக்கு மாறாமல் உள்ளது (புதிய சேர்மன் கெவின் வார்ஷ் தலைமையில் ஜூன் 17 மீட்டிங் வரவுள்ளது).\n\n"
        
        f"🏦 *FII / DII ஆக்டிவிட்டி (NSE Cash Market):*\n"
        f"• *DII (உள்நாட்டு நிறுவனங்கள்):* 🟢 +₹5,341.29 கோடி அதிரடி கொள்முதல்!\n"
        f"• *FII (வெளிநாட்டு முதலீட்டாளர்கள்):* 🔴 -₹1,082.18 கோடி லேசான விற்பனை.\n\n"
        
        f"🎯 *இன்றைய ஓப்பனிங் கணிப்பு:* \n"
        f"கச்சா எண்ணெய் விலை சரிவு மற்றும் ஆசிய சந்தைகளின் (Nikkei, Kospi) பாசிட்டிவ் மூவ்ஸ் காரணமாக இன்று இந்திய சந்தை ஒரு வலுவான கேப்-அப் (Gap-Up) ஓப்பனிங்கை நோக்கி நகர்கிறது!"
    )
    return report

def send_to_telegram():
    text = get_market_summary()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    send_to_telegram()