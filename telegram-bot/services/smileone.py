import hashlib
import time
import aiohttp
from config import SMILEONE_EMAIL, SMILEONE_API_KEY, SMILEONE_BASE_URL


def _make_sign(params: dict) -> str:
    sorted_items = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_items if k != "sign")
    sign_str += SMILEONE_API_KEY
    return hashlib.md5(sign_str.encode()).hexdigest()


def _base_params() -> dict:
    return {
        "email": SMILEONE_EMAIL,
        "time": str(int(time.time())),
    }


async def check_user(uid: str, zone: str) -> dict:
    params = _base_params()
    params.update({
        "product": "mobilelegends",
        "uid": uid,
        "zone": zone,
    })
    params["sign"] = _make_sign(params)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SMILEONE_BASE_URL}checkrole.php",
            data=params,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            data = await resp.json(content_type=None)
            return data


async def create_order(uid: str, zone: str, product_id: str) -> dict:
    params = _base_params()
    params.update({
        "product": "mobilelegends",
        "uid": uid,
        "zone": zone,
        "product_id": product_id,
        "quantity": "1",
    })
    params["sign"] = _make_sign(params)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SMILEONE_BASE_URL}createorder.php",
            data=params,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await resp.json(content_type=None)
            return data


async def query_order(smileone_order_id: str) -> dict:
    params = _base_params()
    params.update({
        "order_id": smileone_order_id,
    })
    params["sign"] = _make_sign(params)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SMILEONE_BASE_URL}queryorder.php",
            data=params,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            data = await resp.json(content_type=None)
            return data
