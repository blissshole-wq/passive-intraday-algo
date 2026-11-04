import os

API_ID = int(os.environ.get("API_ID", 0)) 
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

STRING_SESSION = os.environ.get("STRING_SESSION", "")

SOURCE_CHANNEL = [


-1001096581370, 
-1002897476578,
-1001330148120,
-1001498073945,
-1001823497790,


]


TARGET_CHANNELS = {
    "news": -1003906746387,
    "tips": -1004461920119,
    "updates": -1004361876950,
    "general": -1004317836060
}

