import asyncio
import json
import aiohttp
from groq import Groq
from telethon import TelegramClient, events
import config

# Groq Client செட் அப்
groq_client = Groq(api_key=config.GROQ_API_KEY)

# Telegram Client
client = TelegramClient('auto_forward_session', config.API_ID, config.API_HASH)

async def process_with_ai(text):
    # AI-க்கு தெளிவான கட்டளை: கம்பெனி பெயர்களை விடக்கூடாது.
    prompt = f"""
    You are an expert news editor and translator. Analyze the following text:
    "{text}"
    
    Task 1: Categorize this text into exactly one of these categories: ["news", "tips", "updates", "general"].
    
    Task 2: Create a highly specific summary in Tamil (around 50 words). 
    CRITICAL RULE: You MUST include the names of the main entities (Company names, People, Organizations, Stock names) mentioned in the text. Do NOT write a generic summary. If facts/lists are present, use bullet points.
    
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
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ Groq AI Error: {e}")
        return None

async def process_with_ai(text):
    prompt = f"""
    You are an expert news editor and translator. Analyze the following text:
    "{text}"
    
    Task 1: Categorize this text into exactly one of these categories: ["news", "tips", "updates", "general"].
    
    Task 2: Create a highly specific summary in Tamil (around 50 words). 
    CRITICAL RULE: You MUST include the names of the main entities (Company names, People, Organizations, Stock names) mentioned in the text. Do NOT write a generic summary. If facts/lists are present, use bullet points.
    
    Return the response STRICTLY as a JSON object with these keys:
    "category": "news", 
    "tamil_summary": "சுருக்கம் இங்கே..."
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON. Do not use markdown blocks like ```json."},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-20b",
            response_format={"type": "json_object"},
            max_tokens=1000 
        )
        
        # AI கொடுக்கும் பதிலை எடுத்து, அதில் உள்ள தேவையற்ற குறியீடுகளை நீக்குதல்
        raw_content = chat_completion.choices[0].message.content
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(raw_content)
        
    except json.JSONDecodeError:
        print("⚠️ AI gave invalid JSON. Skipping this message.")
        return None
    except Exception as e:
        print(f"⚠️ Groq AI Error: {e}")
        return None 

    text_lower = original_text.lower()
    
    # --- படி 1: கீவேர்டு வடிகட்டி ---
    all_keywords = []
    for kws in config.CATEGORY_KEYWORDS.values():
        all_keywords.extend(kws)
        
    if all_keywords and not any(kw in text_lower for kw in all_keywords):
        print("⏭️ கீவேர்டு இல்லை, தவிர்க்கப்படுகிறது...")
        return 

    print("🤖 கீவேர்டு உள்ளது! AI வைத்து ஆராய்கிறது...")
    
    # --- படி 2: AI ஆய்வு ---
    ai_data = await process_with_ai(original_text)
    
    if not ai_data:
        return

    category = ai_data.get("category", "general").lower()
    target_id = config.TARGET_CHANNELS.get(category, config.TARGET_CHANNELS["general"])

    # --- படி 3: லிங்க் பிரச்சனைக்கு தீர்வு (Fallback) ---
    try:
        # முதலில் நேரடி லிங்க்கை எடுக்க முயற்சிக்கவும் (Public Channels-க்கு இது வேலை செய்யும்)
        message_link = event.message.link
    except Exception:
        message_link = None

    # லிங்க் இல்லை என்றால், நாமே உருவாக்குவோம் (Private Channels-க்கு இது வேலை செய்யும்)
    if not message_link:
        # event.chat_id வடிவம்: -1001234567890
        chat_id_str = str(event.chat_id).replace("-100", "")
        message_link = f"https://t.me/c/{chat_id_str}/{event.message.id}"

    # --- படி 4: இறுதி மெசேஜ் வடிவம் ---
    final_message = f"""**Summary:**
{ai_data['tamil_summary']}

🔗 **Read More:** [இங்கே கிளிக் செய்யவும்]({message_link})"""

    await send_via_bot(target_id, final_message)

async def main():
    await client.start()
    print("🚀 Bot started! Listening to sources...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())