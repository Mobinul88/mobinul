import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# টেলিগ্রাম ও এপিআই কনফিগারেশন
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINANCE_FAPI = "https://fapi.binance.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# স্টেবলকয়েন ও ইন্ডেক্স বাদ দেওয়ার তালিকা
EXCLUDE_SYMBOLS = [
    "USDCUSDT", "PAXGUSDT", "BTCDOMUSDT", "EURUSDT", 
    "GBPUSDT", "FDUSDUSDT", "TUSDUSDT", "BUSDUSDT"
]

def send_telegram_message(message):
    """টেলিগ্রামে এইচটিএমএল ফরম্যাটে মেসেজ পাঠায়"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram Credentials missing!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=12)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_all_perpetual_pairs():
    """বাইনান্স ফিউচার্সের সমস্ত সক্রিয় USDT পারপেচুয়াল পেয়ার সংগ্রহ করে"""
    try:
        url = f"{BINANCE_FAPI}/fapi/v1/exchangeInfo"
        res = requests.get(url, headers=HEADERS, timeout=15).json()
        
        symbols = []
        for s in res.get("symbols", []):
            sym = s.get("symbol", "")
            status = s.get("status", "")
            contract_type = s.get("contractType", "")
            
            # শুধুমাত্র TRADING স্ট্যাটাস ও PERPETUAL কন্ট্রাক্ট ফিল্টার
            if (sym.endswith("USDT") and 
                status == "TRADING" and 
                contract_type == "PERPETUAL" and 
                sym not in EXCLUDE_SYMBOLS):
                symbols.append(sym)
                
        symbols = sorted(list(set(symbols)))
        print(f"✅ মোট সক্রিয় ফিউচার্স পেয়ার পাওয়া গেছে: {len(symbols)} টি")
        return symbols
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return []

def get_klines_safe(symbol, interval="1d", limit=60):
    """ক্যান্ডেলস্টিক ডেটা ফেচ করার নিরাপদ ফাংশন"""
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        res = requests.get(f"{BINANCE_FAPI}/fapi/v1/klines", params=params, headers=HEADERS, timeout=8).json()
        if not isinstance(res, list) or len(res) < 25:
            return None
        df = pd.DataFrame(res, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_base_vol", "taker_quote_vol", "ignore"
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df
    except Exception:
        return None

def get_funding_rate_safe(symbol):
    """লাইভ ফান্ডিং রেট ফেচিং"""
    try:
        res = requests.get(f"{BINANCE_FAPI}/fapi/v1/premiumIndex", params={"symbol": symbol}, headers=HEADERS, timeout=5).json()
        return float(res.get("lastFundingRate", 0.0)) * 100
    except Exception:
        return 0.0

def run_full_market_scan():
    start_time = time.time()
    pairs = get_all_perpetual_pairs()
    total_pairs = len(pairs)
    
    if total_pairs == 0:
        send_telegram_message("⚠️ <b>স্ক্যানিং ত্রুটি:</b> বাইনান্স এপিআই থেকে পেয়ার তালিকা ফেচ করা যায়নি।")
        return

    valid_setups = []
    scanned_count = 0

    print(f">> সমস্ত {total_pairs} টি ফিউচার্স কয়েন স্ক্যান শুরু হচ্ছে...")

    for sym in pairs:
        scanned_count += 1
        if scanned_count % 50 == 0 or scanned_count == total_pairs:
            print(f"Progress: [{scanned_count}/{total_pairs}] টি কয়েন স্ক্যান সম্পন্ন...")

        # ১. ডেইলি ডাটা ফেচ
        df_1d = get_klines_safe(sym, interval="1d", limit=60)
        if df_1d is None:
            time.sleep(0.04)
            continue

        df_1d["sma50"] = df_1d["close"].rolling(50, min_periods=20).mean()
        df_1d["sma200"] = df_1d["close"].rolling(200, min_periods=30).mean()

        d_close = df_1d.iloc[-1]["close"]
        d_50 = df_1d.iloc[-1]["sma50"]
        d_200 = df_1d.iloc[-1]["sma200"]

        # ফিল্টার ১: ডেইলি ক্যান্ডেল ক্লোজিং অবশ্যই SMA 50 বা SMA 200 এর উপরে
        daily_bullish = False
        ma_label = ""
        if not pd.isna(d_50) and d_close >= d_50:
            daily_bullish = True
            ma_label = "Daily SMA 50"
        elif not pd.isna(d_200) and d_close >= d_200:
            daily_bullish = True
            ma_label = "Daily SMA 200"

        if not daily_bullish:
            time.sleep(0.04)
            continue

        # ফিল্টার ২: ৩ দিন বা ৭ দিনের কম্প্রেশন (প্রি-পাম্প অ্যাকুমুলেশন)
        range_3d = (df_1d["high"].tail(3).max() - df_1d["low"].tail(3).min()) / d_close * 100
        if range_3d > 16.0:  # অলরেডি পাম্প হওয়া ভোলাটাইল কয়েন বাদ
            time.sleep(0.04)
            continue

        # ফিল্টার ৩: ৪-ঘণ্টার ক্যান্ডেলে বাউন্স ও ভলিউম
        df_4h = get_klines_safe(sym, interval="4h", limit=30)
        if df_4h is None:
            time.sleep(0.04)
            continue

        df_4h["vol_sma"] = df_4h["volume"].rolling(20, min_periods=5).mean()
        last_4h = df_4h.iloc[-1]
        is_green = last_4h["close"] >= last_4h["open"]
        has_volume = last_4h["volume"] >= (last_4h["vol_sma"] * 0.8)

        # ফিল্টার ৪: ফান্ডিং রেট চেক
        fr = get_funding_rate_safe(sym)
        if fr > 0.02:
            time.sleep(0.04)
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

        time.sleep(0.04)  # রেট লিমিট প্রটেকশন

    elapsed_time = int(time.time() - start_time)
    today_date = datetime.utcnow().strftime("%Y-%m-%d")

    # টেলিগ্রামে পূর্ণাঙ্গ স্ক্যান রিপোর্ট পাঠানো
    if valid_setups:
        msg = f"🏛️ <b>FULL MARKET INSTITUTIONAL SCAN REPORT</b>\n"
        msg += f"📅 তারিখ: <code>{today_date}</code> (Day Close Review)\n"
        msg += f"🔍 মোট স্ক্যান করা ফিউচার্স পেয়ার: <b>{total_pairs} টি</b>\n"
        msg += f"⏱️ স্ক্যানিং সময়: <b>{elapsed_time} সেকেন্ড</b>\n"
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
        msg += f"🔍 মোট স্ক্যান করা ফিউচার্স পেয়ার: <b>{total_pairs} টি</b>\n"
        msg += f"⏱️ স্ক্যানিং সময়: <b>{elapsed_time} সেকেন্ড</b>\n\n"
        msg += "🛡️ <b>ফলাফল: কোনো কয়েন শর্ত পূরণ করেনি।</b>\n"
        msg += "💡 <i>পুরো ৫০০+ ফিউচার্স মার্কেটে কোনো কয়েনেই নিরাপদ ডেইলি SMA সাপোর্ট ও রিবাউন্ড মেলেনি। ক্যাপিটাল সম্পূর্ণ প্রটেক্টেড রাখুন।</i>"
        send_telegram_message(msg)

if __name__ == "__main__":
    run_full_market_scan()
