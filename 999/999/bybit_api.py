import requests
import time

last_data = {"buy": None, "sell": None}

def get_p2p_data(side="1"):
    """
    side = "1" -> Покупка (BUY)
    side = "0" -> Продажа (SELL)
    """
    url = "https://api2.bybit.com/fiat/otc/item/online"
    payload = {
        "userId": "",
        "tokenId": "USDT",
        "currencyId": "KGS",
        "payment": [],
        "side": side,
        "size": 10,
        "page": 1,
    }

    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get("result", {}).get("items", [])
                if items:
                    last_data["buy" if side == "1" else "sell"] = items
                    return items
        except Exception as e:
            print(f"❌ Попытка {attempt + 1}/3 — ошибка: {e}")
            time.sleep(2)

    cached = last_data.get("buy" if side == "1" else "sell")
    if cached:
        print("⚠️ Используются последние кэшированные данные Bybit.")
        return cached

    print("🚫 Нет данных Bybit вообще.")
    return []
