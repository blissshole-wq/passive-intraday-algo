import asyncio
import json
import aiohttp
from groq import Groq
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
import threading
import config

# ==========================================
# 1. Flask Server Setup (UptimeRobot-க்காக)
# ==========================================
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is alive and running!", 200

def run_flask():
    # Render-ல் 10000 போர்ட் தான் பயன்படுத்த வேண்டும்
    app.run(host='0.0.0.0', port=10000)

# ==========================================
# 2. Telegram & Groq Setup
# ==========================================
groq_client = Groq(api_key=config.GROQ_API_KEY)

# String Session பயன்படுத்தி Client-ஐ உருவாக்குதல்
client = TelegramClient(StringSession(config.STRING_SESSION), config.API_ID, config.API_HASH)

async def process_with_ai(text):
    prompt = f"""
    You are an expert news editor, translator, and categorizer. Analyze the following text:
    "{text}"
    
    Task 1: Categorize this text into exactly one of these categories based on the context and meaning:
    - "news": For detailed articles, world events, politics, and long-form journalism.
    - "updates": For short, urgent alerts, software updates, new product launches, or breaking news alerts.
    - "tips": For how-to guides, tricks, hacks, tutorials, or useful advice.
    - "general": For anything else that doesn't fit the above.
    
    Task 2: Create a highly specific summary in Tamil (around 50 words). 
    CRITICAL RULE: You MUST include the names of the main entities (Company names, People, Organizations) mentioned in the text. Do NOT write a generic summary. If facts/lists are present, use bullet points.
    
    Return the response STRICTLY as a JSON object with these keys:
    "category": "news", 
    "tamil_summary": "சுருக்கம் இங்கே..."
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-20b",
            response_format={"type": "json_object"},
            max_tokens=1000 
        )
        raw_content = chat_completion.choices[0].message.content
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        return json.loads(raw_content)
    except Exception as e:
        print(f"⚠️ Groq AI Error: {e}")
        return None

async def send_via_bot(chat_id, text):
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print(f"✅ வெற்றிகரமாக அனுப்பப்பட்டது! (Chat ID: {chat_id})")
                    return
                elif response.status == 429:
                    error_data = await response.json()
                    retry_after = error_data.get("parameters", {}).get("retry_after", 5)
                    print(f"⏳ வரம்பு மீறல்! {retry_after} வினாடிகள் காத்திருக்கிறது...")
                    await asyncio.sleep(retry_after)
                else:
                    error_text = await response.text()
                    print(f"❌ அனுப்ப முடியவில்லை. Error: {error_text}")
                    return
    print("❌ 3 முயற்சிகளுக்குப் பிறகும் அனுப்ப முடியவில்லை.")

@client.on(events.NewMessage(chats=config.SOURCE_CHANNEL))
async def handler(event):
    original_text = event.message.message 
    if not original_text:
        return 

    print(f"🤖 புதிய மெசேஜ் வந்தது (சேனல்: {event.chat_id})! AI ஆராய்கிறது...")
    
    ai_data = await process_with_ai(original_text)
    if not ai_data:
        return

    category = ai_data.get("category", "general").lower()
    target_id = config.TARGET_CHANNELS.get(category, config.TARGET_CHANNELS["general"])

    try:
        message_link = event.message.link
    except Exception:
        message_link = None

    if not message_link:
        chat_id_str = str(event.chat_id).replace("-100", "")
        message_link = f"https://t.me/c/{chat_id_str}/{event.message.id}"

    final_message = f"""**Summary:**
{ai_data['tamil_summary']}

🔗 **Read More:** [இங்கே கிளிக் செய்யவும்]({message_link})"""

    await send_via_bot(target_id, final_message)

# ==========================================
# 3. Main Execution
# ==========================================
async def main():
    print("⏳ டெலிகிராமுடன் இணைய முயற்சிக்கிறது...", flush=True)
    
    # start()க்கு பதிலாக connect() பயன்படுத்துகிறோம் (ஹேங் ஆகாமல் இருக்க)
    await client.connect()
    
    # செஷன் சரியானதா என்று செக் செய்கிறோம்
    if not await client.is_user_authorized():
        print("❌ ERROR: STRING_SESSION செல்லாதது (Invalid) அல்லது API_ID/HASH தவறு!", flush=True)
        return  # லாகின் ஆகவில்லை என்றால் இங்கேயே நிறுத்திவிடும்
        
    print("🚀 Bot started! Listening to sources...", flush=True)
    
    # --- டிபக் செய்யும் பகுதி ---
    print("--- சேனல்களை ஆய்வு செய்கிறது ---", flush=True)
    for channel in config.SOURCE_CHANNEL:
        try:
            entity = await client.get_entity(channel)
            print(f"✅ கிடைத்தது: {entity.title} (ID: {channel})", flush=True)
        except Exception as e:
            print(f"❌ கிடைக்கவில்லை: {channel} - Error: {e}", flush=True)
    print("---------------------------------", flush=True)

    await client.run_until_disconnected()