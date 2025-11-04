# p2p_signal_bot.py
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode

# ==============================
# 🔧 НАСТРОЙКИ
# ==============================
BOT_TOKEN = "8254878765:AAGrVibWhbH4pavhfpVDk_iTdWL8N1bU0CM"
CHAT_ID = "491116016"
PAIR = "USDT"
FIAT = "KGS"
UPDATE_INTERVAL = 45  # сек между обновлениями

# API адреса
BYBIT_P2P_URL = "https://api2.bybit.com/fiat/otc/item/online"
BINANCE_P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher()

# ==============================
# 📡 ЗАПРОСЫ К API
# ==============================
def get_bybit_p2p(side="BUY"):
    """Bybit P2P"""
    data = {
        "userId": "",
        "tokenId": PAIR,
        "currencyId": FIAT,
        "payment": [],
        "side": side,
        "size": 5,
        "page": 1,
        "amount": "",
        "authMaker": False
    }
    try:
        r = requests.post(BYBIT_P2P_URL, json=data, timeout=10)
        offers = r.json()["result"]["items"]
        parsed = []
        for o in offers:
            price = float(o["price"])
            name = o["nickName"]
            user_id = o["userId"]
            link = f"https://www.bybit.com/p2p/user/{user_id}"
            parsed.append({"price": price, "name": name, "link": link})
        return parsed
    except Exception as e:
        print("❌ Ошибка Bybit:", e)
        return []


def get_binance_p2p(side="BUY"):
    """Binance P2P"""
    data = {
        "asset": PAIR,
        "fiat": FIAT,
        "tradeType": side,
        "rows": 5,
        "page": 1,
        "payTypes": []
    }
    try:
        r = requests.post(BINANCE_P2P_URL, json=data, timeout=10)
        offers = r.json()["data"]
        parsed = []
        for o in offers:
            price = float(o["adv"]["price"])
            name = o["advertiser"]["nickName"]
            link = f"https://p2p.binance.com/ru/advertiserDetail?advertiserNo={o['advertiser']['userNo']}"
            parsed.append({"price": price, "name": name, "link": link})
        return parsed
    except Exception as e:
        print("❌ Ошибка Binance:", e)
        return []

# ==============================
# 💬 ФОРМИРОВАНИЕ СООБЩЕНИЙ
# ==============================
def format_message(source, color, buy_list, sell_list):
    if not buy_list or not sell_list:
        return f"{color} *{source}*\n⚠️ Нет данных.\n"

    best_buy = buy_list[0]
    best_sell = sell_list[0]
    margin = (best_buy['price'] - best_sell['price']) / best_sell['price'] * 100

    msg = f"{color} *{source}*\n"
    msg += f"🔼 *Покупают (BUY)* — кто хочет купить у тебя:\n"
    for b in buy_list:
        msg += f"• [{b['name']}]({b['link']}) — {b['price']:.2f} {FIAT}\n"

    msg += f"\n🔽 *Продают (SELL)* — у кого ты можешь купить:\n"
    for s in sell_list:
        msg += f"• [{s['name']}]({s['link']}) — {s['price']:.2f} {FIAT}\n"

    msg += f"\n📊 *Маржа:* `{margin:.2f}%`\n"
    if margin > 0.3:
        msg += "💵 Есть шанс на прибыль.\n\n"
    else:
        msg += "😐 Маленькая маржа.\n\n"

    return msg

# ==============================
# 🔁 ОСНОВНОЙ ЦИКЛ
# ==============================
async def monitor_loop():
    while True:
        # Bybit
        bybit_buy = get_bybit_p2p("BUY")
        bybit_sell = get_bybit_p2p("SELL")
        bybit_msg = format_message("Bybit P2P", "🖤", bybit_buy, bybit_sell)

        # Binance
        binance_buy = get_binance_p2p("BUY")
        binance_sell = get_binance_p2p("SELL")
        binance_msg = format_message("Binance P2P", "🟧", binance_buy, binance_sell)

        full_msg = bybit_msg + binance_msg
        try:
            await bot.send_message(CHAT_ID, full_msg)
        except Exception as e:
            print("Ошибка Telegram:", e)

        await asyncio.sleep(UPDATE_INTERVAL)

# ==============================
# ▶️ ЗАПУСК
# ==============================
async def main():
    await bot.send_message(CHAT_ID, "🤖 P2P Signal Bot запущен. Следим за Bybit (🖤) и Binance (🟧)")
    asyncio.create_task(monitor_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
