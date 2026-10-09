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
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

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
                if isinstance(res, list) and len(res) >= 60:
                    return res
        except Exception:
            continue
    return None

def check_btc_regime():
    klines = get_binance_klines("BTCUSDT", "1d", 220)
    if not klines:
        return True, "Data Bypass", 0.0
    closes = [float(k[4]) for k in klines]
    s50 = pd.Series(closes).rolling(50).mean().iloc[-1]
    s200 = pd.Series(closes).rolling(200).mean().iloc[-1] if len(closes) >= 200 else s50
    curr = closes[-1]
    
    if curr >= s200 or curr >= s50:
        regime = "🟢 Bullish / Strong Support"
    else:
        regime = "🟡 Neutral / Caution Mode"
        
    return True, regime, curr

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
    print("🚀 Starting Scan...")
    _, btc_regime, btc_price = check_btc_regime()
    
    # স্ক্যান শুরু হওয়ার তাৎক্ষণিক টেস্ট পিং টেলিগ্রামে পাঠানো
    start_msg = f"🔍 *[MOBINUL ENGINE: SCAN STARTED]*\n🌐 BTC: `${btc_price:,.0f}` | Regime: `{btc_regime}`\n⏳ Scanning 250+ Binance pairs for 50/200 SMA retests..."
    send_telegram_alert(start_msg)

    pairs = get_futures_pairs()
    if not pairs:
        print("Failed to fetch pairs.")
        return

    print(f"Scanning {len(pairs)} pairs...")
    signals = []

    for sym in pairs:
        clean = sym.replace("USDT", "")
        klines = get_binance_klines(sym, "1d", 220)
        if not klines or len(klines) < 60:
            continue

        closes = [float(k[4]) for k in klines]
        lows = [float(k[3]) for k in klines]
        df = pd.DataFrame({'close': closes, 'low': lows})
        
        # ৫০ ও ২০০ এসএমএ হিসাব
        df['sma50'] = df['close'].rolling(50).mean()
        has_200 = len(df) >= 200
        if has_200:
            df['sma200'] = df['close'].rolling(200).mean()

        curr_p = df['close'].iloc[-1]
        c_low = df['low'].iloc[-1]
        s50 = df['sma50'].iloc[-1]
        s200 = df['sma200'].iloc[-1] if has_200 else s50

        # প্রাইস ৫০ বা ২০০ এসএমএ-এর যেটিতে কাছে আছে সেটি নির্বাচন
        chosen_sma = s200 if (has_200 and abs(curr_p - s200) < abs(curr_p - s50)) else s50
        sma_label = "200 SMA" if (chosen_sma == s200 and has_200) else "50 SMA"

        if curr_p < chosen_sma:
            continue

        dist_pct = ((curr_p - chosen_sma) / chosen_sma) * 100
        
        # রিটেস্ট রেঞ্জ (০% থেকে ৪.৫% এর মধ্যে বা আজকের লো এসএমএ টাচ করেছে)
        if not (dist_pct <= 4.5 or c_low <= chosen_sma):
            continue

        # ৭ দিনের গতিশীলতা
        acc_7d = curr_p >= closes[-7]
        if not acc_7d:
            continue

        funding_rate = get_derivatives(clean)

        # ট্রেড লেভেল
        entry_low = round(chosen_sma * 1.002, 4)
        entry_high = round(curr_p, 4)
        stop_loss = round(chosen_sma * 0.965, 4)
        risk = max(entry_high - stop_loss, entry_high * 0.035)

        tp1 = round(entry_high + (risk * 1.5), 4)
        tp2 = round(entry_high + (risk * 2.5), 4)
        tp3 = round(entry_high + (risk * 4.0), 4)

        trade_card = f"""🚨 *[A+ SWING SIGNAL: #{clean}USDT]* 🚨

📊 *Price:* `${curr_p:,.4f}` ({sma_label} Retest: `+{dist_pct:.2f}%`)
🎯 *Entry Zone:* `${entry_low} - ${entry_high}`
🛡️ *Anti-Hunt SL:* `${stop_loss}`

💰 *Take-Profit Targets:*
• TP 1: `${tp1}` (+1:1.5 RR)
• TP 2: `${tp2}` (+1:2.5 RR)
• TP 3: `${tp3}` (+1:4.0 RR)

⚡ *Funding Rate:* `{funding_rate:.4f}%`
🐋 *Whale Flow (7D):* Net Inflow 🟢
🌐 *BTC Price:* `${btc_price:,.0f}`

🔍 [Coinglass Heatmap](https://www.coinglass.com/pro/futures/LiquidityHeatMap?symbol={clean}USDT) | [Arkham](https://arkm.com/explorer/token/{clean.lower()})"""

        send_telegram_alert(trade_card)
        signals.append(clean)
        time.sleep(1)

    summary_msg = f"🏁 *[SCAN COMPLETE]*\nTotal Scanned: {len(pairs)} pairs.\n✅ Verified A+ Setups Found: {len(signals)}"
    if signals:
        summary_msg += f"\nTokens: {', '.join(signals)}"
    send_telegram_alert(summary_msg)

if __name__ == "__main__":
    run_institutional_scanner()
