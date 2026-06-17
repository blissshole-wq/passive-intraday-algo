import asyncio
import sys

# 🔥 Python 3.14-க்கான 'Event Loop' எர்ரர் பிக்ஸ் (பாட்ச் வொர்க்)
try:
    asyncio.get_running_loop()
except RuntimeError:
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# இப்போ லைப்ரரியை இம்போர்ட் பண்ணினா எர்ரர் வராது மாப்ள!
from hydrogram import Client, filters
from deep_translator import GoogleTranslator

# =======================================================================
# ⚙️ 1. உங்களோட TELEGRAM API கிரிடென்ஷியல்ஸ்
# =======================================================================
API_ID = '6114756103'      # 👈 உங்களுடைய API ID (Quotes-க்குள்)
API_HASH = 'b6b77b51f951f6a640e596e7f3f9470e'  # 👈 உங்களுடைய API HASH

# =======================================================================
# 📢 2. நீங்கள் கண்காணிக்க விரும்பும் சேனல்களின் லிஸ்ட்
# =======================================================================
HINDI_CHANNELS = ['newslaundry_official', 'newsclickin']
ENGLISH_CHANNELS = ['indianexpress', 'business_standard', 'scroll_in', 'TheWireNews', 'aljazeera', 'apnews', 'AninewsIn']
TAMIL_CHANNELS = ['dailythanthitv']

# அனைத்து அலர்ட்டுகளும் வந்து சேர வேண்டிய உங்க சொந்த சேனல் யூசர்நேம் (@ இல்லாமல்)
TARGET_CHAT = '@Bitsnpeaces_bot' 

# =======================================================================
# 🛠️ 3. இஞ்சின் செட்டப் (Hydrogram Engine)
# =======================================================================
ALL_WATCHED_CHANNELS = HINDI_CHANNELS + ENGLISH_CHANNELS + TAMIL_CHANNELS

app = Client("news_session_hydrogram", api_id=API_ID, api_hash=API_HASH)

hindi_to_tamil = GoogleTranslator(source='hi', target='ta')
english_to_tamil = GoogleTranslator(source='en', target='ta')

print("⚡ Hydrogram News Alert Engine ரெடி ஆகிடுச்சு மாப்ள...")

# =======================================================================
# 🎯 4. மெயின் அலர்ட் & ட்ரான்ஸ்லேஷன் லாஜிக்
# =======================================================================
@app.on_message(filters.chat(ALL_WATCHED_CHANNELS) & filters.text)
async def handle_new_news(client, message):
    chat_username = message.chat.username
    original_text = message.text
    final_tamil_text = ""
    source_lang = ""

    try:
        if chat_username in HINDI_CHANNELS:
            final_tamil_text = hindi_to_tamil.translate(original_text)
            source_lang = "🇮🇳 ஹிந்தி நியூஸ் (Translated)"

        elif chat_username in ENGLISH_CHANNELS:
            final_tamil_text = english_to_tamil.translate(original_text)
            source_lang = "🇬🇧 ஆங்கில நியூஸ் (Translated)"

        elif chat_username in TAMIL_CHANNELS:
            final_tamil_text = original_text
            source_lang = "🎯 தமிழ் நியூஸ் (Direct Alert)"

        alert_message = (
            f"🔔 **புதிய நியூஸ் அலர்ட்!** [{source_lang}]\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{final_tamil_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 மூலம்: {message.chat.title} (@{chat_username})"
        )

        await client.send_message(TARGET_CHAT, alert_message)
        print(f"✅ [{message.chat.title}]-ல இருந்து வந்த நியூஸ் அலர்ட் அனுப்பப்பட்டது!")

    except Exception as e:
        print(f"❌ ட்ரான்ஸ்லேஷன் எர்ரர்: {e}")

# =======================================================================
# 🚀 5. பாட்டை ரன் செய்கிறோம்
# =======================================================================
if __name__ == '__main__':
    print("🚀 பாட்டை ஸ்டார்ட் பண்றோம் மாப்ள... போன் நம்பர் கேட்கும் பாருங்க!")
    app.run()