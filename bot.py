import logging
import re
from telethon import TelegramClient, events
from deep_translator import GoogleTranslator
from newspaper import Article

# லாகிங் செட்டப்
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# உங்க விபரங்கள்
API_ID = 25923754
API_HASH = 'b6b77b51f951f6a640e596e7f3f9470e'

# சோர்ஸ் மற்றும் டெஸ்டினேஷன் ஐடிக்கள்
SOURCE_CHATS = [-1003776187626, -1001215466904, -1001299805329, -1001450185719, -1001165029723, -1001247488093, -1001345563500, -1001011047399, -1001849833349, -1001734719628, -1001640086866, -1001380369188, -1001274268284, -1001904407328, -1001756386574] 
DESTINATION_CHAT = -1001913322116

client = TelegramClient('my_forwarder_session', API_ID, API_HASH)

print("🚀 அல்டிமேட் நியூஸ் ஸ்க்ரேப்பர் & டிரான்ஸ்லேட்டர் பாட் ரெடி மாப்ள...")

@client.on(events.NewMessage(chats=SOURCE_CHATS))
async def forward_and_translate_handler(event):
    try:
        if event.message.text:
            original_text = event.message.text
            logging.info(f"📥 சோர்ஸ் மெசேஜ் வந்தது...")
            
            # 🔄 மெயின் மெசேஜை தமிழ்ல மாத்துறோம்
            main_translated = GoogleTranslator(source='auto', target='ta').translate(original_text)
            
            final_response = f"{main_translated}\n"
            
            # 🔗 மெசேஜ்ல ஏதாச்சும் வெப்சைட் லிங்க் இருக்கான்னு தேடுது
            urls = re.findall(r'(https?://[^\s]+)', original_text)
            
            if urls:
                for url in urls:
                    try:
                        logging.info(f"🕸️ லிங்க் உள்ள இருக்குற கன்டென்ட்டை சுரண்டுகிறேன்: {url}")
                        # லிங்க் உள்ள இருக்குற நியூஸை மட்டும் ஸ்க்ரேப் பண்றோம்
                        article = Article(url)
                        article.download()
                        article.parse()
                        
                        web_text = article.text  # வெப்சைட் உள்ள இருக்குற முழு நியூஸ் டெக்ஸ்ட்
                        
                        if web_text:
                            # 1500 வார்த்தைக்கு மேல இருந்தா கூகுள் டிரான்ஸ்லேட் எரர் அடிக்கும், அதனால சுருக்கிக்கிறோம்
                            short_web_text = web_text[:1500] 
                            
                            # வெப்சைட் கன்டென்ட்டை தமிழ்ல மாத்துறோம்
                            translated_web_text = GoogleTranslator(source='auto', target='ta').translate(short_web_text)
                            
                            final_response += f"\n--- 📄 **வலைத்தள செய்தி விவரம்** ---\n{translated_web_text}...\n"
                    except Exception as web_err:
                        logging.error(f"⚠️ லிங்க் கன்டென்ட் எடுப்பதில் குட்டி சிக்கல்: {web_err}")
                        final_response += f"\n🔗 [ஒரிஜினல் லிங்க்]({url})\n"

            # போட்டோ/மீடியா இருந்தா அதோட சேர்த்து அனுப்பும், இல்லனா வெறும் டெக்ஸ்ட்
            if event.message.media:
                event.message.text = final_response
                await client.send_message(DESTINATION_CHAT, event.message)
            else:
                await client.send_message(DESTINATION_CHAT, final_response, parse_mode='markdown')
                
            logging.info("✅ மெசேஜ் மற்றும் லிங்க் கன்டென்ட் முழுமையாக தமிழ் வடிவில் அனுப்பப்பட்டது!")
            
        elif event.message.media:
            await client.forward_messages(DESTINATION_CHAT, event.message)
            
    except Exception as e:
        logging.error(f"❌ எரர்: {e}")

with client:
    client.run_until_disconnected()