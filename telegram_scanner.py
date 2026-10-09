import requests
import pandas as pd
import time

BOT_TOKEN = "8968950600:AAEF8nDDEYMYmDQQe59Yoi70dqwUkQZTL0k"
CHAT_ID = "8605377336"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=8)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_binance_klines(symbol, interval="1d", limit=230):
    urls = [
        "https://data-api.binance.vision/api/v3/klines",
        "https://fapi.binance.com/fapi/v1/klines",
        "https://api.binance.com/api/v3/klines"
    ]
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    for u in urls:
        try:
            r = requests.get(u, params=params, headers=HEADERS, timeout=4)
            if r.status_code == 200:
                res = r.json()
                if isinstance(res, list) and len(res) >= 200:
                    return res
        except Exception:
            continue
    return None

def check_btc_support():
    klines = get_binance_klines("BTCUSDT", "1d", 220)
    if not klines:
        return True, 0.0
    closes = [float(k[4]) for k in klines]
    s50 = pd.Series(closes).rolling(50).mean().iloc[-1]
    s200 = pd.Series(closes).rolling(200).mean().iloc[-1]
    curr = closes[-1]
    
    # বিটিসি ২০০ বা ৫০ এসএমএ-এর ওপরে বা সাপোর্ট জোনে থাকলে নিরাপদ
    is_safe = (curr >= s200 or curr >= s50)
    return is_safe, curr

def get_derivatives(symbol):
    fr_val = 0.01
    try:
        url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}USDT"
        r = requests.get(url, headers=HEADERS, timeout=3).json()
        if 'lastFundingRate' in r:
            fr_val = float(r['lastFundingRate']) * 100
    except Exception:
        pass
    return fr_val

def get_futures_pairs():
    try:
        r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", headers=HEADERS, timeout=6).json()
        return [
            s['symbol'] for s in r.get('symbols', [])
            if s['symbol'].endswith('USDT') and not s['symbol'].startswith('1000') and s.get('status') == 'TRADING'
        ]
    except Exception:
        return []

def run_institutional_scanner():
    print("🚀 Starting 4-Hour Institutional Swing Scan...")
    btc_safe, btc_price = check_btc_support()
    if not btc_safe:
        print("⚠️ BTC Breakdown Zone. Skipping scan for capital protection.")
        return

    pairs = get_futures_pairs()
    if not pairs:
        print("Failed to fetch pairs.")
        return

    print(f"Scanning {len(pairs)} pairs on Binance...")
    found_signals = 0

    for sym in pairs:
        clean = sym.replace("USDT", "")
        klines = get_binance_klines(sym, "1d", 235)
        if not klines or len(klines) < 205:
            continue

        closes = [float(k[4]) for k in klines]
        lows = [float(k[3]) for k in klines]
        df = pd.DataFrame({'close': closes, 'low': lows})
        df['sma200'] = df['close'].rolling(200).mean()

        curr_p = df['close'].iloc[-1]
        c_sma = df['sma200'].iloc[-1]
        c_low = df['low'].iloc[-1]

        if curr_p < c_sma:
            continue

        dist_pct = ((curr_p - c_sma) / c_sma) * 100
        # SMA রিটেস্ট জোন (০.৫% থেকে ৩.০% দূরত্ব)
        if not (dist_pct <= 3.0 or (c_low <= c_sma and curr_p >= c_sma)):
            continue

        # ব্রেকআউট রিটেস্ট ভেরিফিকেশন
        was_below = any(df['close'].iloc[-i] < df['sma200'].iloc[-i] for i in range(2, 8))
        if not was_below:
            continue

        # ৭ডি এবং ৩০ডি একুমুলেশন চেক
        acc_7d = curr_p >= closes[-7]
        acc_30d = curr_p >= closes[-30]
        if not (acc_7d and acc_30d):
            continue

        funding_rate = get_derivatives(clean)

        # ট্রেড লেভেল হিসাব
        entry_low = round(c_sma * 1.002, 4)
        entry_high = round(curr_p, 4)
        stop_loss = round(c_sma * 0.965, 4)
        risk = max(entry_high - stop_loss, entry_high * 0.035)

        tp1 = round(entry_high + (risk * 1.5), 4)
        tp2 = round(entry_high + (risk * 2.5), 4)
        tp3 = round(entry_high + (risk * 4.0), 4)

        # টেলিগ্রাম অ্যালার্ট মেসেজ
        msg = f"""🚨 *[MOBINUL A+ SWING ALERT]* 🚨

🪙 *Pair:* `#{clean}USDT`
📊 *Price:* `${curr_p:,.4f}` (SMA Retest: `{dist_pct:.2f}%`)
🎯 *Entry Zone:* `${entry_low} - ${entry_high}`
🛡️ *Anti-Hunt SL:* `${stop_loss}`

💰 *Take-Profits:*
• TP 1: `${tp1}` (+1:1.5 RR)
• TP 2: `${tp2}` (+1:2.5 RR)
• TP 3: `${tp3}` (+1:4.0 RR)

⚡ *Derivatives:* Funding `{funding_rate:.4f}%`
🐋 *Whale Flow:* 7D & 30D Net Inflow 🟢
🌐 *BTC Regime:* Safe Support (${btc_price:,.0f})

🔍 [Coinglass Heatmap](https://www.coinglass.com/pro/futures/LiquidityHeatMap?symbol={clean}USDT) | [Arkham Flow](https://arkm.com/explorer/token/{clean.lower()})"""

        send_telegram_alert(msg)
        print(f"✅ Alert sent for {clean}")
        found_signals += 1
        time.sleep(1)

    print(f"Scan finished. Sent {found_signals} signals.")

if __name__ == "__main__":
    run_institutional_scanner()
