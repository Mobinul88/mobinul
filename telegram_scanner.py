import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# ========================================================
# টেলিগ্রাম কনফিগারেশন
# ========================================================
TELEGRAM_BOT_TOKEN = "8968950600:AAEF8nDDEYMYmDQQe59Yoi70dqWuKQZTL0k"
TELEGRAM_CHAT_ID = "8605377336"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

EXCLUDE_SYMBOLS = [
    "USDCUSDT", "PAXGUSDT", "BTCDOMUSDT", "EURUSDT", 
    "GBPUSDT", "FDUSDUSDT", "TUSDUSDT", "BUSDUSDT"
]

session = requests.Session()
session.headers.update(HEADERS)

def send_telegram_message(message):
    """টেলিগ্রামে এইচটিএমএল ফরম্যাটে মেসেজ পাঠায়"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        res = session.post(url, json=payload, timeout=8)
        print("Telegram Status Code:", res.status_code)
        if res.status_code == 200:
            print("✅ Telegram notification sent successfully!")
        else:
            print("Telegram Error Response:", res.text)
    except Exception as e:
        print(f"Telegram Exception: {e}")

def get_binance_futures_symbols():
    """বাইনান্সের সক্রিয় পেয়ার সংগ্রহ"""
    url = "https://data-api.binance.vision/api/v3/exchangeInfo"
    try:
        res = session.get(url, timeout=8).json()
        symbols = [
            s['symbol'] for s in res.get('symbols', [])
            if s.get('status') == 'TRADING' and s['symbol'].endswith('USDT') and s['symbol'] not in EXCLUDE_SYMBOLS
        ]
        if len(symbols) >= 50:
            symbols = sorted(list(set(symbols)))
            print(f"✅ বাইনান্স থেকে মোট সক্রিয় পেয়ার পাওয়া গেছে: {len(symbols)} টি")
            return symbols
    except Exception as e:
        print(f"Fetch Warning: {e}")

    return [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "TRXUSDT", "DOGEUSDT", "BNBUSDT", 
        "XRPUSDT", "ADAUSDT", "AVAXUSDT", "SUIUSDT", "NEARUSDT", "LINKUSDT", 
        "APTUSDT", "PEPEUSDT", "WIFUSDT", "FETUSDT", "RENDERUSDT", "BATUSDT"
    ]

def get_binance_klines_fast(symbol, interval="1d", limit=60):
    """বাইনান্স দ্রুতগতির ক্যান্ডেলস্টিক ফেচিং"""
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = session.get(url, timeout=2.5).json()
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

def get_oi_growth(symbol):
    """বাইনান্স ফিউচার্স ওপেন ইন্টারেস্ট (OI) গ্রোথ - নিরাপদ মেথড"""
    url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=4h&limit=7"
    try:
        req = session.get(url, timeout=2.0)
        if req.status_code == 200:
            data = req.json()
            if isinstance(data, list) and len(data) >= 2:
                initial_oi = float(data[0].get("sumOpenInterestValue", 0))
                current_oi = float(data[-1].get("sumOpenInterestValue", 0))
                if initial_oi > 0:
                    return ((current_oi - initial_oi) / initial_oi) * 100
    except Exception:
        pass
    return 0.0

def run_scanner():
    start_time = time.time()
    pairs = get_binance_futures_symbols()
    total_pairs = len(pairs)
    
    valid_setups = []
    scanned_count = 0

    print(f">> বাইনান্সের মোট {total_pairs} টি কয়েন লিডিং স্ক্যানার দিয়ে স্ক্যান শুরু হচ্ছে...")

    for sym in pairs:
        scanned_count += 1
        if scanned_count % 50 == 0 or scanned_count == total_pairs:
            print(f"Progress: [{scanned_count}/{total_pairs}] টি সম্পন্ন...")

        # ১. ডেইলি ট্রেন্ড ও SMA চেক
        df_1d = get_binance_klines_fast(sym, interval="1d", limit=60)
        if df_1d is None:
            continue

        df_1d["sma50"] = df_1d["close"].rolling(50, min_periods=20).mean()
        df_1d["sma200"] = df_1d["close"].rolling(200, min_periods=30).mean()

        d_close = df_1d.iloc[-1]["close"]
        d_50 = df_1d.iloc[-1]["sma50"]
        d_200 = df_1d.iloc[-1]["sma200"]

        daily_bullish = False
        ma_label = ""
        if (not pd.isna(d_50)) and (d_close >= d_50):
            daily_bullish = True
            ma_label = "Daily SMA 50"
        elif (not pd.isna(d_200)) and (d_close >= d_200):
            daily_bullish = True
            ma_label = "Daily SMA 200"

        if not daily_bullish:
            continue

        # ২. ৩-দিনের কম্প্রেশন চেক (<18%)
        range_3d = (df_1d["high"].tail(3).max() - df_1d["low"].tail(3).min()) / d_close * 100
        if range_3d > 18.0:
            continue

        # ৩. ৪-ঘণ্টার ক্যান্ডেল এবং ভলিউম সার্জ রেশিও (Volume Surge)
        df_4h = get_binance_klines_fast(sym, interval="4h", limit=30)
        if df_4h is None:
            continue

        df_4h["vol_sma"] = df_4h["volume"].rolling(20, min_periods=5).mean()
        last_4h = df_4h.iloc[-1]
        
        avg_vol = last_4h["vol_sma"]
        current_vol = last_4h["volume"]
        vol_surge_ratio = (current_vol / avg_vol) if avg_vol > 0 else 1.0

        is_green = last_4h["close"] >= last_4h["open"]
        has_volume_surge = is_green and (vol_surge_ratio >= 1.3)

        if not has_volume_surge:
            continue

        # ৪. ওপেন ইন্টারেস্ট গ্রোথ চেক
        oi_growth_pct = get_oi_growth(sym)

        entry_p = d_close
        sl_p = entry_p * 0.95
        tp1_p = entry_p * 1.05
        tp2_p = entry_p * 1.10

        valid_setups.append({
            "symbol": sym,
            "price": entry_p,
            "ma_type": ma_label,
            "range_3d": range_3d,
            "vol_surge": vol_surge_ratio,
            "oi_growth": oi_growth_pct,
            "sl": sl_p,
            "tp1": tp1_p,
            "tp2": tp2_p
        })

    elapsed = int(time.time() - start_time)
    today_date = datetime.utcnow().strftime("%Y-%m-%d")

    # টেলিগ্রামে রিপোর্ট পাঠানো
    if valid_setups:
        msg = f"🔥 <b>INSTITUTIONAL LEADING BREAKOUT ALERT</b>\n"
        msg += f"📅 তারিখ: <code>{today_date}</code> (High Probability Entry)\n"
        msg += f"🔍 মোট স্ক্যান করা পেয়ার: <b>{total_pairs} টি</b>\n"
        msg += f"⏱️ সময় লেগেছে: <b>{elapsed} সেকেন্ড</b>\n"
        msg += f"🎯 কোয়ালিফাই করেছে: <b>{len(valid_setups)} টি</b>\n\n"

        for coin in valid_setups:
            msg += f"💎 <b>#{coin['symbol']}</b>\n"
            msg += f"• সাপোর্ট স্ট্রাকচার: <code>{coin['ma_type']}</code>\n"
            msg += f"• এন্ট্রি রেট: <code>{coin['price']:.4f}</code>\n"
            msg += f"• ৩-দিনের রেঞ্জ: <code>{coin['range_3d']:.2f}% (Compressed)</code>\n"
            msg += f"• 🚀 <b>ভলিউম স্পাইক:</b> <code>{coin['vol_surge']:.2f}x (Surge)</code>\n"
            if coin['oi_growth'] != 0.0:
                msg += f"• 📈 <b>OI গ্রোথ (24h):</b> <code>{coin['oi_growth']:+.2f}%</code>\n"
            msg += f"🛑 স্টপ-লস: <code>{coin['sl']:.4f} (-5.0%)</code>\n"
            msg += f"🎯 TP 1: <code>{coin['tp1']:.4f} (+5.0%)</code>\n"
            msg += f"🚀 TP 2: <code>{coin['tp2']:.4f} (+10.0%)</code>\n"
            msg += "----------------------------\n"
        send_telegram_message(msg)
    else:
        msg = f"🏛️ <b>BINANCE INSTITUTIONAL SCAN REPORT</b>\n"
        msg += f"📅 তারিখ: <code>{today_date}</code> (Day Close Review)\n"
        msg += f"🔍 মোট স্ক্যান করা বাইনান্স পেয়ার: <b>{total_pairs} টি</b>\n"
        msg += f"⏱️ সময় লেগেছে: <b>{elapsed} সেকেন্ড</b>\n\n"
        msg += "🛡️ <b>ফলাফল: কোনো কয়েনে লিডিং স্পাইক মেলেনি।</b>\n"
        msg += "💡 <i>কোনো কয়েনে একসাথে নিরাপদ SMA সাপোর্ট, কম্প্রেশন এবং ভলিউম স্পাইক (≥1.3x) কনফার্মেশন পাওয়া যায়নি। ক্যাপিটাল সুরক্ষিত রাখুন।</i>"
        send_telegram_message(msg)

if __name__ == "__main__":
    run_scanner()
