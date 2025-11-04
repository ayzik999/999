# p2p_arbitrage_bot.py
import asyncio
import requests
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode

# ====== Настройки (можешь менять) ======
BOT_TOKEN = "8254878765:AAGrVibWhbH4pavhfpVDk_iTdWL8N1bU0CM"
CHAT_ID = 491116016
PAIR = "USDT"
FIAT = "KGS"
CHECK_INTERVAL = 30            # сек
MIN_MARGIN_PERCENT = 0.5       # сигнал при >= 0.5%
SAMPLE_USDT = 1000             # для расчёта примерной прибыли
BYBIT_P2P_URL = "https://api2.bybit.com/fiat/otc/item/online"
BINANCE_P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
HEADERS = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
# =======================================

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher()

def fetch_binance(side="BUY", rows=5):
    """BUY = who buys USDT (so you sell), SELL = who sells USDT (so you buy)"""
    payload = {"asset": PAIR, "fiat": FIAT, "tradeType": side, "rows": rows, "page": 1, "payTypes": []}
    try:
        r = requests.post(BINANCE_P2P_URL, json=payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
        offers = []
        for it in data:
            adv = it.get("adv", {})
            adv_price = float(adv.get("price", 0))
            min_amt = adv.get("minSingleTransAmount")
            max_amt = adv.get("maxSingleTransAmount")
            adv_id = it.get("advertiser", {}).get("userNo")
            nick = it.get("advertiser", {}).get("nickName", "unknown")
            # link to advertiser detail
            link = f"https://p2p.binance.com/ru/advertiserDetail?advertiserNo={adv_id}"
            offers.append({"price": adv_price, "nick": nick, "min": min_amt, "max": max_amt, "link": link})
        return offers
    except Exception as e:
        print("binance fetch error:", e)
        return []

def fetch_bybit(side="BUY", size=5):
    """Bybit P2P. side=BUY means who buys USDT (they give KGS)"""
    payload = {"userId":"", "tokenId": PAIR, "currencyId": FIAT, "payment": [], "side": side, "size": size, "page": 1, "amount":"", "authMaker": False}
    try:
        r = requests.post(BYBIT_P2P_URL, json=payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        res = r.json()
        items = res.get("result", {}).get("items", []) or []
        offers = []
        for o in items:
            price = float(o.get("price", 0))
            nick = o.get("nickName") or o.get("userName") or "unknown"
            user_id = o.get("userId")
            min_amt = o.get("minSingleTransAmount")
            max_amt = o.get("maxSingleTransAmount")
            link = f"https://www.bybit.com/p2p/user/{user_id}" if user_id else "https://www.bybit.com/p2p"
            offers.append({"price": price, "nick": nick, "min": min_amt, "max": max_amt, "link": link})
        return offers
    except Exception as e:
        print("bybit fetch error:", e)
        return []

def top_price_info(offers, best='min'):
    """returns sorted list and best offer (for BUY side best=min price for buyer? careful)"""
    if not offers:
        return [], None
    sorted_offers = sorted(offers, key=lambda x: x["price"])
    if best == 'min':
        return sorted_offers, sorted_offers[0]
    else:
        return sorted_offers[::-1], sorted_offers[0]

def build_buttons(buy_offer, sell_offer):
    kb = InlineKeyboardMarkup(row_width=2)
    if buy_offer and buy_offer.get("link"):
        kb.add(InlineKeyboardButton(text=f"Open BUY @{buy_offer['nick']}", url=buy_offer["link"]))
    if sell_offer and sell_offer.get("link"):
        kb.add(InlineKeyboardButton(text=f"Open SELL @{sell_offer['nick']}", url=sell_offer["link"]))
    return kb

def pretty_list(offers):
    return "\n".join([f"• `{o['price']:.2f}` KGS — {o['nick']} (min:{o.get('min')}, max:{o.get('max')})" for o in offers])

async def check_and_send():
    last_signal = None  # (buy_price, sell_price, source_buy, source_sell)
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Binance: SELL = who sells USDT -> where you can BUY cheap (we want min sell)
        binance_sell = fetch_binance("SELL", rows=5)
        # Bybit: BUY = who buys USDT -> where you can SELL higher (we want max buy)
        bybit_buy = fetch_bybit("BUY", size=5)

        if binance_sell and bybit_buy:
            # best places
            bin_sell_sorted, bin_best_sell = top_price_info(binance_sell, best='min')  # cheapest seller (you buy here)
            byb_buy_sorted, byb_best_buy = top_price_info(bybit_buy, best='max')       # highest buyer (you sell here)

            # compute margin: sell on Bybit (get KGS) minus buy on Binance (pay KGS)
            buy_price = bin_best_sell["price"]    # price to buy USDT (KGS per USDT)
            sell_price = byb_best_buy["price"]    # price to sell USDT (KGS per USDT)
            margin_abs = sell_price - buy_price
            margin_pct = (margin_abs / buy_price) * 100 if buy_price else 0

            # estimate profit for SAMPLE_USDT (ignoring fees/time)
            profit_est = margin_abs * SAMPLE_USDT

            print(f"[{now}] bin_buy={buy_price:.2f} byb_sell={sell_price:.2f} margin={margin_pct:.3f}% profit~{profit_est:.2f} KGS")

            send_signal = False
            cur_sig = (round(buy_price, 4), round(sell_price, 4))
            # send if margin threshold OR first time OR price changed significantly
            if margin_pct >= MIN_MARGIN_PERCENT:
                send_signal = True
            elif last_signal is None:
                send_signal = False  # avoid spamming on first run unless margin enough
            else:
                lb, ls = last_signal
                if abs(buy_price - lb) >= 0.3 or abs(sell_price - ls) >= 0.3:
                    send_signal = True

            if send_signal:
                # Compose message: include both markets, colored markers
                text = f"*P2P ARBITRAGE SCAN*\n`{now}`\n\n"
                # Binance block (orange) — where to buy
                text += "🟧 *Binance P2P* — где купить (дёшево):\n"
                text += pretty_list(bin_sell_sorted[:5]) + "\n\n"
                # Bybit block (black) — where to sell
                text += "🖤 *Bybit P2P* — где продать (дороже):\n"
                text += pretty_list(byb_buy_sorted[:5]) + "\n\n"
                text += f"📊 *Margin*: `{margin_abs:.4f}` KGS  — `{margin_pct:.3f}%`\n"
                text += f"💰 *Est. profit for {SAMPLE_USDT} USDT*: `{profit_est:.0f}` KGS\n"
                if margin_pct >= MIN_MARGIN_PERCENT:
                    text += "\n⚡ *ARBITRAGE OPPORTUNITY!*"
                else:
                    text += "\nℹ️ Маржа меньше порога."

                kb = build_buttons(byb_best_buy, bin_best_sell)  # buttons to jump to offers
                try:
                    await bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=kb)
                    last_signal = cur_sig
                except Exception as e:
                    print("Telegram send error:", e)
        else:
            print(f"[{now}] ⚠️ Нет данных с одной из бирж")

        await asyncio.sleep(CHECK_INTERVAL)

@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("🤖 Arbitrage scanner started. Scanning Binance (🟧) vs Bybit (🖤).")

@dp.message(commands=["status"])
async def cmd_status(message: types.Message):
    await message.reply("Running. Use /stop_processor (not implemented) to stop if needed.")

async def main():
    # start background scanner then polling
    asyncio.create_task(check_and_send())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
