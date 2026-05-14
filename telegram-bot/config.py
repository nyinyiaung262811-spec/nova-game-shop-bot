import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

SMILEONE_EMAIL = os.getenv("SMILEONE_EMAIL", "")
SMILEONE_API_KEY = os.getenv("SMILEONE_API_KEY", "")
SMILEONE_BASE_URL = "https://www.smile.one/smilecoin/api/"

KPAY_ACCOUNT = os.getenv("KPAY_ACCOUNT", "")
KPAY_NAME = os.getenv("KPAY_NAME", "")
WAVEPAY_ACCOUNT = os.getenv("WAVEPAY_ACCOUNT", "")
WAVEPAY_NAME = os.getenv("WAVEPAY_NAME", "")

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")

DB_PATH = "telegram-bot/orders.db"

DIAMOND_PACKAGES = [
    {"id": "1",  "product_id": "2024",  "diamonds": 11,   "price": 800},
    {"id": "2",  "product_id": "2025",  "diamonds": 22,   "price": 1600},
    {"id": "3",  "product_id": "2026",  "diamonds": 56,   "price": 4000},
    {"id": "4",  "product_id": "2027",  "diamonds": 86,   "price": 6000},
    {"id": "5",  "product_id": "2028",  "diamonds": 112,  "price": 8000},
    {"id": "6",  "product_id": "2029",  "diamonds": 172,  "price": 12000},
    {"id": "7",  "product_id": "2030",  "diamonds": 225,  "price": 16000},
    {"id": "8",  "product_id": "2031",  "diamonds": 344,  "price": 24000},
    {"id": "9",  "product_id": "2032",  "diamonds": 568,  "price": 40000},
    {"id": "10", "product_id": "2033",  "diamonds": 706,  "price": 48000},
    {"id": "11", "product_id": "2034",  "diamonds": 878,  "price": 60000},
    {"id": "12", "product_id": "2035",  "diamonds": 1706, "price": 115000},
    {"id": "13", "product_id": "2036",  "diamonds": 3688, "price": 245000},
]
