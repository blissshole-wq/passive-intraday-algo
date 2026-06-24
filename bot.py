import logging
import re

try:
    import requests
    from bs4 import BeautifulSoup
    from telethon import TelegramClient, events
    from deep_translator import GoogleTranslator
except Exception as exc:  # pragma: no cover - environment-dependent
    requests = None
    BeautifulSoup = None
    TelegramClient = None
    events = None
    GoogleTranslator = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

logging.basicConfig(level=logging.INFO)

API_ID = 25923754
API_HASH = 'b6b77b51f951f6a640e596e7f3f9470e'
SOURCE_CHATS = [-1003776187626, -1001377338855, -1001215466904, -1001299805329, -1001450185719, -1001165029723, -1001247488093, -1001345563500, -1001011047399, -1001849833349, -1001734719628, -1001640086866, -1001380369188, -1001274268284, -1001904407328, -1001756386574]
DESTINATION_CHAT = -1001913322116

client = TelegramClient('news_translator_session', API_ID, API_HASH) if TelegramClient is not None else None


def get_content(url):
    if requests is None or BeautifulSoup is None:
        return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        p_tags = soup.find_all('p')
        return " ".join([p.get_text() for p in p_tags[:5]])
    except Exception:
        return ""


def clean_text_for_translation(text):
    cleaned = re.sub(r'https?://\S+', '', text or "")
    cleaned = re.sub(r'@\w+', '', cleaned)
    cleaned = re.sub(r'#[\w-]+', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def detect_source_language(text):
    if not text:
        return 'auto'
    if re.search(r'[\u0900-\u097F]', text):
        return 'hi'
    if re.search(r'[A-Za-z]', text):
        return 'en'
    return 'auto'


def translate_text(text, target='ta'):
    cleaned = clean_text_for_translation(text)
    if not cleaned:
        return ""
    if GoogleTranslator is None:
        return cleaned

    source_lang = detect_source_language(cleaned)
    try:
        translated = GoogleTranslator(source=source_lang, target=target).translate(cleaned)
        if translated and translated.strip():
            translated = translated.strip()
            if target == 'ta':
                translated = translated.replace('செய்தி', 'செய்தி')
                translated = translated.replace('அறிவிப்பு', 'அறிவிப்பு')
                translated = translated.replace('முக்கியமான', 'முக்கியம்')
                translated = translated.replace('அதிகாரப்பூர்வமாக', 'அதிகாரபூர்வமாக')
                translated = translated.replace('உண்மையில்', 'உண்மையில்')
                translated = translated.replace('பொறுப்பான', 'பொறுப்பான')
                translated = translated.replace('தொடர்ந்து', 'தொடர்ந்து')
                translated = translated.replace('அதிகாரப்பூர்வ', 'அதிகாரபூர்வ')
                translated = translated.replace('விவரங்களை', 'விவரங்கள்')
                translated = translated.replace('தகவல்களை', 'தகவல்கள்')
                translated = translated.replace('அதிகாரபூர்வமாக', 'அதிகாரபூர்வமாக')
                translated = translated.replace('செய்திகள்', 'செய்திகள்')
            return translated
    except Exception as exc:
        logging.warning("Translation failed: %s", exc)

    return cleaned


if client is not None and events is not None and GoogleTranslator is not None:
    @client.on(events.NewMessage(chats=SOURCE_CHATS))
    async def handler(event):
        message_text = (
            getattr(event.message, 'message', None)
            or getattr(event.message, 'text', None)
            or getattr(event, 'raw_text', None)
            or ""
        )
        translated_text = translate_text(message_text)
        urls = re.findall(r'(https?://\S+)', message_text or "")

        final_output = translated_text
        for url in urls:
            if "t.me/" in url:
                continue
            synopsis = get_content(url)
            if synopsis:
                ta_synopsis = translate_text(synopsis[:500])
                final_output += f"\n\n📋 **செய்தியின் சுருக்கம்:**\n{ta_synopsis}..."

        if event.message.media:
            await client.send_file(DESTINATION_CHAT, event.message.media, caption=final_output, parse_mode='markdown')
        else:
            await client.send_message(DESTINATION_CHAT, final_output, parse_mode='markdown', link_preview=False)
else:
    async def handler(*args, **kwargs):
        print("Telegram bot dependencies are unavailable. Install telethon, bs4, requests, and deep_translator to enable the translator bot.")
        return None


def main():
    if IMPORT_ERROR is not None:
        print(f"Telegram bot disabled: {IMPORT_ERROR}")
        return
    if client is None:
        print("Telegram client could not be initialised.")
        return
    with client:
        client.run_until_disconnected()


if __name__ == "__main__":
    main()