import asyncio
import json
import aiohttp
import time
import threading
from groq import Groq
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
import config

# 1. Flask Server Setup (UptimeRobot-க்காக)
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is alive", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# 2. Telegram & Groq Setup
groq_client = Groq(api_key=config.GROQ_API_KEY)
client = TelegramClient(StringSession(config.STRING_SESSION), config.API_ID, config.API_HASH)

async def process_with_ai(text):
    prompt = f"""
    You are an expert news editor, translator, and categorizer. Analyze the following text:
    "{text}"
    
    Task 1: Categorize this text into exactly one of these categories: ["news", "tips", "updates", "general"].
    Task 2: Create a highly specific summary in Tamil (around 50 words). 
    CRITICAL RULE: You MUST include the names of the main entities. If facts/lists are present, use bullet points.
    
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
        print(f"⚠️ Groq AI Error: {e}", flush=True)
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
                    print(f"✅ வெற்றிகரமாக அனுப்பப்பட்டது! (Chat ID: {chat_id})", flush=True)
                    return
                elif response.status == 429:
                    error_data = await response.json()
                    retry_after = error_data.get("parameters", {}).get("retry_after", 5)
                    print(f"⏳ வரம்பு மீறல்! {retry_after} வினாடிகள் காத்திருக்கிறது...", flush=True)
                    await asyncio.sleep(retry_after)
                else:
                    error_text = await response.text()
                    print(f"❌ அனுப்ப முடியவில்லை. Error: {error_text}", flush=True)
                    return
    print("❌ 3 முயற்சிகளுக்குப் பிறகும் அனுப்ப முடியவில்லை.", flush=True)

@client.on(events.NewMessage(chats=config.SOURCE_CHANNEL))
async def handler(event):
    original_text = event.message.message 
    if not original_text:
        return 

    print(f"🤖 புதிய மெசேஜ் வந்தது (சேனல்: {event.chat_id})! AI ஆராய்கிறது...", flush=True)
    
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

# 3. Telethon Main Logic
async def start_telegram_bot():
    try:
        print("⏳ டெலிகிராமுடன் இணைய முயற்சிக்கிறது...", flush=True)
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ ERROR: STRING_SESSION செல்லாதது (Invalid) அல்லது API_ID/HASH தவறு!", flush=True)
            return # இங்கே நிறுத்தினாலும், கீழே உள்ள while loop பாட்டை ஆன் ஆக வைத்திருக்கும்
            
        print("🚀 Bot started! Listening to sources...", flush=True)
        
        print("--- சேனல்களை ஆய்வு செய்கிறது ---", flush=True)
        for channel in config.SOURCE_CHANNEL:
            try:
                entity = await client.get_entity(channel)
                print(f"✅ கிடைத்தது: {entity.title} (ID: {channel})", flush=True)
            except Exception as e:
                print(f"❌ கிடைக்கவில்லை: {channel} - Error: {e}", flush=True)
        print("---------------------------------", flush=True)

        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Telethon Error: {e}", flush=True)

# 4. Execution (The Magic Trick)
if __name__ == '__main__':
    # 1. Flask Server-ஐ தனி த்ரெட்டில் ரன் செய்கிறோம்
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✅ Flask Server started on port 10000", flush=True)

    # 2. டெலிகிராம் பாட்டை தனி த்ரெட்டில் ரன் செய்கிறோம்
    def run_telegram():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_telegram_bot())
        
    tele_thread = threading.Thread(target=run_telegram)
    tele_thread.daemon = True
    tele_thread.start()

    # 3. பாட் க்ராஷ் ஆனாலும், Render-ல் ஸ்கிரிப்ட் நிற்காமல் இருக்க இந்த லூப்
    while True:
        time.sleep(1)