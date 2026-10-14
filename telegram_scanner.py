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
    """বাইনান্স ফিউচার্স ওপেন ইন্টারেস্ট (OI) গ্রোথ - সম্পূর্ণ নিরাপদ ও নন-ক্র্যাশ মেথড"""
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
        if not pd.isna(d_50) and
