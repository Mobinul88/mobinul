import os
import time
import requests
import pandas as pd
import numpy as np
import ccxt
from datetime import datetime

# টেলিগ্রাম ক্রেডেনশিয়াল সংগ্রহ
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

EXCLUDE_SYMBOLS = [
    "USDCUSDT", "PAXGUSDT", "BTCDOMUSDT", "EURUSDT", 
    "GBPUSDT", "FDUSDUSDT", "TUSDUSDT", "BUSDUSDT"
]

def send_telegram_message(message):
    """টেলিগ্রামে মেসেজ প্রেরক"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram Credentials missing! Check GitHub Secrets.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code == 200:
            print("✅ Telegram notification sent successfully!")
        else:
            print(f"⚠️ Telegram send failed. Code: {res.status_code}, Resp: {res.text}")
    except Exception as e:
        print(f"Telegram Exception: {e}")

def get_all_futures_symbols():
    """CCXT এর মাধ্যমে বাইনান্সের সমস্ত পারপেচুয়াল পেয়ার ফেচ করা"""
    try:
        exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
        markets = exchange.load_markets()
        symbols = []
        for sym, data in markets.items():
            if data.get('linear') and data.get('active') and sym.endswith('/USDT:USDT'):
                clean_sym = sym.replace('/USDT:USDT', 'USDT')
                if clean_sym not in EXCLUDE_SYMBOLS:
                    symbols.append(clean_sym)
        if len(symbols) > 50:
            print(f"✅ CCXT দিয়ে মোট সক্রিয় ফিউচার্স পেয়ার পাওয়া গেছে: {len(symbols)} টি")
            return sorted(symbols)
    except Exception as e:
        print(f"CCXT Load Markets Warning: {e}")

    # ডাইরেক্ট ফলব্যাক
    try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10).json()
        symbols = [s['symbol'] for s in res.get('symbols', []) if s.get('status') == 'TRADING' and s['symbol'].endswith('USDT') and s['symbol'] not in EXCLUDE_SYMBOLS]
        if symbols:
            print(f"✅ ডিরেক্ট এপিআই দিয়ে সক্রিয় পেয়ার পাওয়া গেছে: {len(symbols)} টি")
            return sorted(symbols)
    except Exception:
        pass

    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "TRXUSDT", "DOGEUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "SUIUSDT", "NEARUSDT", "LINKUSDT", "PEPEUSDT", "WIFUSDT", "FETUSDT", "RENDERUSDT", "BATUSDT", "SUNUSDT", "MEMEUSDT"]

def get_klines(symbol, timeframe="1d", limit=60):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={timeframe}&limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=6).json()
        if isinstance(res, list) and len(res) >= 20:
            df = pd.DataFrame(res, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_base_vol", "taker_quote_vol", "ignore"
            ])
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            return df
    except Exception:
        pass
    return None

def get_funding_rate(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=4).json()
        return float(res.get("lastFundingRate", 0.0)) * 100
    except Exception:
        return 0.0

def run_scanner():
    start_time = time.time()
    pairs = get_all_futures_symbols()
    total_pairs = len(pairs)
    
    valid_setups = []
    scanned_count = 0

    print(f">> মোট {total_pairs} টি ফিউচার্স পেয়ার স্ক্যান শুরু হচ্ছে...")

    for sym in pairs:
        scanned_count += 1
        if scanned_count % 50 == 0 or scanned_count == total_pairs:
            print(f"Progress: [{scanned_count}/{total_pairs}] টি সম্পন্ন...")

        # ১. ডেইলি ট্রেন্ড চেক
        df_1d = get_klines(sym, timeframe="1d", limit=60)
        if df_1d is None:
            time.sleep(0.02)
            continue

        df_1d["sma50"] = df_1d["close"].rolling(50, min_periods=20).mean()
        df_1d["sma200"] = df_1d["close"].rolling(200, min_periods=30).mean()

        d_close = df_1d.iloc[-1]["close"]
        d_50 = df_1d.iloc[-1]["sma50"]
        d_200 = df_1d.iloc[-1]["sma200"]

        daily_bullish = False
        ma_label = ""
        if not pd.isna(d_50) and d_close >= d_50:
            daily_bullish = True
            ma_label = "Daily SMA 50"
        elif not pd.isna(d_200) and d_close >= d_200:
            daily_bullish = True
            ma_label = "Daily SMA 200"

        if not daily_bullish:
            time.sleep(0.02)
            continue

        # ২. ৩-দিনের কম্প্রেশন
        range_3d = (df_1d["high"].tail(3).max() - df_1d["low"].tail(3).min()) / d_close * 100
        if range_3d > 18.0:
            time.sleep(0.02)
            continue

        # ৩. ৪-ঘণ্টার বাউন্স ও ভলিউম
        df_4h = get_klines(sym, timeframe="4h", limit=30)
        if df_4h is None:
            time.sleep(0.02)
            continue

        df_4h["vol_sma"] = df_4h["volume"].rolling(20, min_periods=5).mean()
        last_4h = df_4h.iloc[-1]
        is_green = last_4h["close"] >= last_4h["open"]
        has_volume = last_4h["volume"] >= (last_4h["vol_sma"] * 0.75)

        # ৪. ফান্ডিং রেট ফিল্টার
        fr = get_funding_rate(sym)
        if fr > 0.025:
            time.sleep(0.02)
            continue

        if is_green and has_volume:
            entry_p = d_close
            sl_p = entry_p * 0.95
            tp1_p = entry_p * 1.05
            tp2_p = entry_p * 1.10

            valid_setups.append({
                "symbol": sym,
                "price": entry_p,
                "ma_type": ma_label,
                "range_3d": range_3d,
                "funding": fr,
                "sl": sl_p,
                "tp1": tp1_p,
                "tp2": tp2_p
            })

        time.sleep(0.02)

    elapsed = int(time.time() - start_time)
    today_date = datetime.utcnow().strftime("%Y-%m-%d")

    # টেলিগ্রাম রিপোর্ট
    if valid_setups:
        msg = f"🏛️ <b>FULL MARKET INSTITUTIONAL SCAN REPORT</b>\n"
        msg += f"📅 তারিখ: <code>{today_date}</code> (Day Close Review)\n"
        msg += f"🔍 মোট স্ক্যান করা পেয়ার: <b>{total_pairs} টি</b>\n"
        msg += f"⏱️ সময় লেগেছে: <b>{elapsed} সেকেন্ড</b>\n"
        msg += f"🎯 কোয়ালিফাই করেছে: <b>{len(valid_setups)} টি</b>\n\n"

        for coin in valid_setups:
            msg += f"💎 <b>#{coin['symbol']}</b>\n"
            msg += f"• সাপোর্ট বেস: <code>{coin['ma_type']}</code>\n"
            msg += f"• এন্ট্রি জোন: <code>{coin['price']:.4f}</code>\n"
            msg += f"• ৩-দিনের রেঞ্জ: <code>{coin['range_3d']:.2f}%</code>\n"
            msg += f"• ফান্ডিং রেট: <code>{coin['funding']:.4f}%</code>\n"
            msg += f"🛑 স্টপ-লস: <code>{coin['sl']:.4f} (-5.0%)</code>\n"
            msg += f"🎯 TP 1: <code>{coin['tp1']:.4f} (+5.0%)</code>\n"
            msg += f"🚀 TP 2: <code>{coin['tp2']:.4f} (+10.0%)</code>\n"
            msg += "----------------------------\n"
        send_telegram_message(msg)
    else:
        msg = f"🏛️ <b>FULL MARKET INSTITUTIONAL SCAN REPORT</b>\n"
        msg += f"📅 তারিখ: <code>{today_date}</code> (Day Close Review)\n"
        msg += f"🔍 মোট স্ক্যান করা পেয়ার: <b>{total_pairs} টি</b>\n"
        msg += f"⏱️ সময় লেগেছে: <b>{elapsed} সেকেন্ড</b>\n\n"
        msg += "🛡️ <b>ফলাফল: কোনো কয়েন শর্ত পূরণ করেনি।</b>\n"
        msg += "💡 <i>পুরো মার্কেটে কোনো কয়েনে নিরাপদ ডেইলি SMA সাপোর্ট ও বাউন্স মেলেনি। মূলধন সম্পূর্ণ সুরক্ষিত রাখুন।</i>"
        send_telegram_message(msg)

if __name__ == "__main__":
    run_scanner()
