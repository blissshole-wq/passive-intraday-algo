import logging
import re
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events
from deep_translator import GoogleTranslator

# லாகிங்
logging.basicConfig(level=logging.INFO)

# உங்க டீடெயில்ஸ்
API_ID = 25923754
API_HASH = 'b6b77b51f951f6a640e596e7f3f9470e'
SOURCE_CHATS = [-1003776187626, -1001215466904, -1001299805329, -1001450185719, -1001165029723, -1001247488093, -1001345563500, -1001011047399, -1001849833349, -1001734719628, -1001640086866, -1001380369188, -1001274268284, -1001904407328, -1001756386574]
DESTINATION_CHAT = -1001913322116

client = TelegramClient('news_translator_session', API_ID, API_HASH)

# வெப்சைட்டிலிருந்து கன்டென்ட் எடுக்கும் பங்க்ஷன்
def get_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        p_tags = soup.find_all('p')
        return " ".join([p.get_text() for p in p_tags[:5]])
    except:
        return ""

@client.on(events.NewMessage(chats=SOURCE_CHATS))
async def handler(event):
    # லிங்க் பிரீவியூவை தவிர்க்க லிங்க்ஸை டெக்ஸ்ட்டிலிருந்து நீக்குகிறோம்
    text = re.sub(r'https?://\S+', '', event.message.text or "")
    
    # தமிழ் மொழிபெயர்ப்பு
    translated_text = GoogleTranslator(source='auto', target='ta').translate(text)
    
    # லிங்க்குகளை மட்டும் எடுக்கிறோம்
    urls = re.findall(r'(https?://\S+)', event.message.text or "")
    
    final_output = translated_text
    
    for url in urls:
        if "t.me/" in url: continue
        synopsis = get_content(url)
        if synopsis:
            ta_synopsis = GoogleTranslator(source='auto', target='ta').translate(synopsis[:500])
            final_output += f"\n\n📋 **செய்தியின் சுருக்கம்:**\n{ta_synopsis}..."
        
        google_trans_url = f"https://translate.google.com/translate?sl=en&tl=ta&u={url}"        
    # மெசேஜ் அனுப்புகிறோம் (link_preview=False போட்டாச்சு)
    if event.message.media:
        await client.send_file(DESTINATION_CHAT, event.message.media, caption=final_output, parse_mode='markdown')
    else:
        await client.send_message(DESTINATION_CHAT, final_output, parse_mode='markdown', link_preview=False)

with client:
    client.run_until_disconnected()