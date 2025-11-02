import requests
import logging
import json

# === Константа для Bybit P2P ===
BYBIT_URL = "https://api2.bybit.com/fiat/otc/item/online"

def get_p2p_data(side="1", token="USDT", currency="KGS", rows=10):
    """
    Получает список объявлений P2P с Bybit.
    side = "1" — покупка (BUY)
    side = "0" — продажа (SELL)
    """
    payload = {
        "userId": "",
        "tokenId": token,
        "currencyId": currency,
        "payment": [],
        "side": side,  # 1 — купить, 0 — продать
        "size": rows,
        "page": 1,
        "amount": "",
        "authMaker": False,
        "canTrade": False
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "999USDT/1.0"
    }

    try:
        response = requests.post(BYBIT_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Универсальная проверка — может быть "result" или сразу "data"
        items = None
        if isinstance(data, dict):
            if "result" in data and "items" in data["result"]:
                items = data["result"]["items"]
            elif "items" in data:
                items = data["items"]
            elif "data" in data and isinstance(data["data"], list):
                items = data["data"]

        if not items:
            logging.warning(f"⚠️ Bybit вернул пустой ответ: {data}")
            return []

        # Возвращаем объявления с ценами
        valid = [x for x in items if "price" in x]
        return valid

    except requests.exceptions.Timeout:
        logging.error("❌ Ошибка: запрос к Bybit истёк по тайм-ауту.")
        return []
    except Exception as e:
        logging.error(f"❌ Ошибка при получении данных Bybit: {e}")
        return []
