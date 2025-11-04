# crypto_signal_bot_safe.py
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError

# ==============================
# ⚙️ НАСТРОЙКИ
# ==============================
BOT_TOKEN = "8254878765:AAGrVibWhbH4pavhfpVDk_iTdWL8N1bU0CM"
CHAT_ID = "491116016"
CHECK_INTERVAL = 60  # проверять каждую минуту
DROP_ALERT = -3.0    # % падения за 15 мин
RISE_ALERT = 3.0     # % роста за 15 мин
SYMBOLS = ["BTCUSDT", "ETHUSDT", "TONUSDT", "SOLUSDT", "DOGEUSDT"]

# ==============================
# 📡 Инициализация бота
# ==============================
bot_props = DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
bot = Bot(token=BOT_TOKEN, default=bot_props)
dp = Dispatcher()

# ==============================
# 📈 Получение данных с Bybit
# ==============================
def get_price(symbol):
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
    try:
        r = requests.get(url, timeout=10).json()
        return float(r["result"]["list"][0]["lastPrice"])
    except Exception as e:
        print(f"Ошибка получения цены {symbol}: {e}")
        return None

def get_candle_change(symbol):
    url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={symbol}&interval=15"
    try:
        r = requests.get(url, timeout=10).json()
        candles = r["result"]["list"]
        if not candles:
            return None
        open_price = float(candles[-1][1])
        close_price = float(candles[-1][4])
        change = (close_price - open_price) / open_price * 100
        return change, close_price
    except Exception as e:
        print(f"Ошибка получения свечи {symbol}: {e}")
        return None

# ==============================
# 🔁 Основной цикл сигналов
# ==============================
async def signal_loop():
    while True:
        for symbol in SYMBOLS:
            data = get_candle_change(symbol)
            if not data:
                continue

            change, price = data
            msg = None
            if change <= DROP_ALERT:
                msg = f"📉 *{symbol}* {change:.2f}% за 15 мин\n💰 Цена: {price:.4f}\n🎯 Возможен *отскок вверх*"
            elif change >= RISE_ALERT:
                msg = f"📈 *{symbol}* +{change:.2f}% за 15 мин\n💰 Цена: {price:.4f}\n⚠️ Возможна *фиксация прибыли*"

            if msg:
                try:
                    await bot.send_message(CHAT_ID, msg, timeout=30)
                except TelegramNetworkError as e:
                    print(f"❌ Telegram недоступен: {e}")
                except Exception as e:
                    print(f"❌ Ошибка отправки сообщения: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

# ==============================
# ▶️ Запуск
# ==============================
async def main():
    try:
        await bot.send_message(CHAT_ID, "🚀 *Crypto Signal Bot* запущен (Bybit Spot)\nСледим за монетами.", timeout=30)
    except TelegramNetworkError as e:
        print(f"❌ Telegram недоступен при старте: {e}")
    except Exception as e:
        print(f"❌ Ошибка при старте бота: {e}")

    asyncio.create_task(signal_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
