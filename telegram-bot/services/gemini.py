import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

_BASE_PROMPT = """You are a customer service assistant for Nova Game Shop.
You help customers with MLBB (Mobile Legends: Bang Bang) diamond top up in Myanmar.

Shop website: http://nova.alphacloud.store

{price_list}

Payment methods: KPay and Wave Pay.
To place an order, customers should use the /top_up command.
To contact admin, customers can use the /admin command.
For more details, customers can visit the website: http://nova.alphacloud.store

Always reply in Myanmar language. Be friendly and helpful."""


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


async def ask_gemini(user_message: str) -> str:
    try:
        from database import get_packages
        packages = await get_packages(active_only=True)

        if packages:
            lines = ["Current Price List:"]
            for p in packages:
                lines.append(f"- {p['diamonds']} 💎 = {p['price']:,} Ks")
            price_section = "\n".join(lines)
        else:
            price_section = "Price list is currently unavailable."

        system_prompt = _BASE_PROMPT.format(price_list=price_section)

        client = get_client()
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "တောင်းပန်ပါသည်၊ ယခုဖြေမရနိုင်သေးပါ။ နောက်မှ ထပ်ကြိုးစားပါ။"
