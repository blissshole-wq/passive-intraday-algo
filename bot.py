import logging
from telethon import TelegramClient, events
from deep_translator import GoogleTranslator

# லாகிங் செட்டப்
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# உங்க விபரங்கள்
API_ID = 25923754
API_HASH = 'b6b77b51f951f6a640e596e7f3f9470e'

# 📍 இங்கே தான் உங்க எல்லா சோர்ஸ் சேனல் ஐடிகளையும் கமா (,) போட்டு குடுக்கணும் மாப்ள!
# இப்போதைக்கு நீங்க குடுத்த இங்கிலீஷ் சோர்ஸ் ஐடியை வச்சிருக்கேன்.
SOURCE_CHATS = [-1001215466904, -1001299805329, -1001450185719. -1001165029723, -1001247488093, -1001345563500, -1001011047399, -1001849833349, -1001734719628, -1001640086866, -1001380369188, -1001274268284, -1001904407328, -1001756386574]

# 🎯 உங்க ஒரே ஒரு டெஸ்டினேஷன் குரூப் ஐடி
DESTINATION_CHAT = -1001913322116

# டெலிகிராம் கிளையண்ட் ஸ்டார்ட் பண்றோம்
client = TelegramClient('my_forwarder_session', API_ID, API_HASH)

print("🚀 மல்டிபிள் சேனல் டிரான்ஸ்லேட்டர் பாட் பேக்ரவுண்ட்ல ரெடி ஆகிட்டு இருக்கு மாப்ள...")

# SOURCE_CHATS லிஸ்ட்ல இருக்குற எந்த சேனல்ல மெசேஜ் வந்தாலும் இது வேலை செய்யும்
@client.on(events.NewMessage(chats=SOURCE_CHATS))
async def forward_and_translate_handler(event):
    try:
        if event.message.text:
            original_text = event.message.text
            logging.info(f"📥 ஒரு சோர்ஸ் சேனல்ல இருந்து வந்த மெசேஜ்: {original_text}")
            
            # 🔄 எந்த மொழியா இருந்தாலும் (English / Hindi) அதை ஆட்டோமேட்டிக்கா தமிழுக்கு (ta) மாத்தும்
            translated_text = GoogleTranslator(source='auto', target='ta').translate(original_text)
            
            if event.message.media:
                event.message.text = translated_text
                await client.send_message(DESTINATION_CHAT, event.message)
            else:
                await client.send_message(DESTINATION_CHAT, translated_text)
                
            logging.info("✅ மெசேஜ் வெற்றிகரமாக தமிழுக்கு மொழிபெயர்க்கப்பட்டு அனுப்பப்பட்டது!")
        
        elif event.message.media:
            await client.forward_messages(DESTINATION_CHAT, event.message)
            logging.info("✅ டெக்ஸ்ட் இல்லாத மீடியா ஃபார்வேர்ட் செய்யப்பட்டது.")
            
    except Exception as e:
        logging.error(f"❌ டிரான்ஸ்லேஷன் செய்வதில் சிக்கல்: {e}")

with client:
    print("🔥 பாட் வெற்றிகரமாக ஆன் ஆகிவிட்டது மாப்ள! இப்போ எல்லா சோர்ஸ் சேனல் மெசேஜ்களும் தமிழ்ல மாறி டெஸ்டினேஷனுக்கு போகும்.")
    client.run_until_disconnected()