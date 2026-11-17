import requests

def send_telegram_message(message):
    # உங்கள் BotFather தந்த Token-ஐ இங்கே பதிவிடவும்
    bot_token = os.environ.get("BOT_TOKEN") 
    chat_id = os.environ.get("CHAT_ID")    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.text}")

# சோதனைச் செய்தி அனுப்புதல்
if __name__ == "__main__":
    send_telegram_message("🚀 டெஸ்க்டாப்பில் இருந்து டெலிகிராமிற்கு அனுப்பப்பட்ட சோதனைச் செய்தி (Test Alert) வெற்றிகரமாக வந்துசேர்ந்தது!")