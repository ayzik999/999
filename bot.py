import asyncio
import logging
import os
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from dotenv import load_dotenv
from flask import Flask, jsonify
from bybit_api import get_p2p_data

# === Загрузка .env ===
load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# === Telegram БОТ ===
@dp.message(Command("start"))
async def start(msg: types.Message):
    web_app = WebAppInfo(url="https://твой-домен.uz/webapp/index.html")  # 🔗 Укажи ссылку на свою страницу
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💰 Открыть 999 USDT App", web_app=web_app)],
            [types.KeyboardButton(text="📊 Показать курс Bybit")]
        ],
        resize_keyboard=True
    )
    await msg.answer("👋 Привет! Это 999 USDT – P2P мониторинг Bybit", reply_markup=kb)

@dp.message(Command("kurs"))
async def kurs(msg: types.Message):
    buy = get_p2p_data(side="1")
    sell = get_p2p_data(side="0")
    if not buy or not sell:
        await msg.answer("⚠️ Нет данных Bybit P2P.")
        return
    try:
        top_buy, top_sell = float(buy[0]["price"]), float(sell[0]["price"])
        spread = top_buy - top_sell
        text = (
            f"💰 USDT/KGS P2P\n\n"
            f"🔼 BUY: {top_buy:.2f} KGS\n"
            f"🔽 SELL: {top_sell:.2f} KGS\n"
            f"📊 СПРЕД: {spread:.4f} KGS"
        )
        await msg.answer(text)
    except Exception as e:
        await msg.answer(f"❌ Ошибка обработки данных: {e}")

@dp.message(lambda message: message.text and "Показать курс" in message.text)
async def show_kurs(msg: types.Message):
    await kurs(msg)

# === Flask API ===
app = Flask(__name__)

@app.route("/api/p2p")
def p2p_api():
    buy = get_p2p_data(side="1")
    sell = get_p2p_data(side="0")
    if not buy or not sell:
        return jsonify({"error": "no data"})
    buy_price = float(buy[0]["price"])
    sell_price = float(sell[0]["price"])
    spread = buy_price - sell_price
    return jsonify({
        "buy": buy_price,
        "sell": sell_price,
        "spread": spread
    })

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# === Запуск обоих процессов ===
async def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
