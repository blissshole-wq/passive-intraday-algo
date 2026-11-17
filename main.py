import time
import pytz
from datetime import datetime
import requests

# டெலிகிராம் போட் விவரங்கள்
    bot_token = os.environ.get("BOT_TOKEN") 
    chat_id = os.environ.get("CHAT_ID"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def job_morning():
    # இந்திய நேரத்தை உறுதி செய்தல்
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
    
    msg = f"☀️ **காலை உலக சந்தை மற்றும் உள்ளூர் செய்தித் தொகுப்பு**\nநேரம்: {current_time}\n\n(இங்கு உங்கள் காலைச் செய்தி விவரங்கள் இடம்பெறும்...)"
    send_telegram_message(msg)

def job_evening():
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
    
    msg = f"🌙 **இரவு உலக சந்தை மற்றும் கமாடிட்டி மூடப்புச் சுருக்கம்**\nநேரம்: {current_time}\n\n(இங்கு உங்கள் இரவுச் சந்தை மற்றும் துறை வாரியான பகுப்பாய்வு இடம்பெறும்...)"
    send_telegram_message(msg)

if __name__ == "__main__":
    print("Background Worker started successfully...")
    
    # நேரத்தை இந்திய நேரப்படி (IST) செட் செய்தல்
    # கவனத்திற்கு: Render சர்வர் பின்னணியில் எப்போதும் ஓடிக்கொண்டிருக்கும் போது, 
    # லூப் (Loop) மூலம் நேரத்தைச் சரிபார்த்து குறிப்பிட்ட நேரத்தில் மெசேஜ் அனுப்பும்.
    
    while True:
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_hour = now.hour
        current_minute = now.minute
        
        # காலை 7:00 மணி (7:00 AM IST)
        if current_hour == 7 and current_minute == 0:
            job_morning()
            time.sleep(60) # ஒரு நிமிடம் தடுத்து மீண்டும் ஒரே முறையில் சுற்றாமல் இருக்க
            
        # இரவு 8:00 மணி (8:00 PM IST)
        elif current_hour == 20 and current_minute == 0:
            job_evening()
            time.sleep(60)
            
        time.sleep(30) # ஒவ்வொரு 30 வினாடிகளுக்கு ஒருமுறை நேரத்தைச் சரிபார்க்கும்