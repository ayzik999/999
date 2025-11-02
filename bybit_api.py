import requests
import logging
import json

# === Настройки ===
BYBIT_URL = "https://api2.bybit.com/fiat/otc/item/online"

# Функция получения P2P-данных
def get_p2p_data(side="1", token="USDT", currency="KGS", rows=5):
    """
    Получает список объявлений P2P с Bybit.
    side = "1" — покупка (BUY), "0" — продажа (SELL)
    token = "USDT" — валюта сделки
    currency = "KGS" — фиатная валюта
    rows = количество объявлений
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
        "canTrade": False,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "999USDT/1.0"
    }

    try:
        response = requests.post(BYBIT_URL, data=json.dumps(payload), headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "result" not in data or "items" not in data["result"]:
            logging.warning("⚠️ Неверный ответ Bybit: нет ключа 'result'")
            return []

        return data["result"]["items"]

    except requests.exceptions.Timeout:
        logging.error("❌ Ошибка: запрос к Bybit истёк по тайм-ауту.")
        return []
    except Exception as e:
        logging.error(f"❌ Ошибка при получении данных Bybit: {e}")
        return []
