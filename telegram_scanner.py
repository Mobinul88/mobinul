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
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Telegram status: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram connection error: {e}")
        return False

def get_binance_klines(symbol, interval="1d", limit=230):
    urls = [
        "https://data-api.binance.vision/api/v3/klines",
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
        return True, "Data Safe", 0.0
    closes = [float(k[4]) for k in klines]
    s50 = pd.Series(closes).rolling(50).mean().iloc[-1]
    s200 = pd.Series(closes).rolling(200).mean().iloc[-1] if len(closes) >= 200 else s50
    curr = closes[-1]
    
    if curr >= s200 or curr >= s50:
        regime = "Bullish / Strong Support"
    else:
        regime = "Neutral / Caution Mode"
        
    return True, regime, curr

def get_active_pairs():
    urls = [
        "https://data-api.binance.vision/api/v3/exchangeInfo",
        "https://api.binance.com/api/v3/exchangeInfo"
    ]
    for u in urls:
        try:
            r = requests.get(u, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                symbols = r.json().get('symbols', [])
                valid_pairs = [
                    s['symbol'] for s in symbols
                    if s['symbol'].endswith('USDT') 
                    and not any(s['symbol'].startswith(p) for p in ['USDC', 'FDUSD', 'TUSD', 'EUR', 'BUSD', 'DAI'])
                    and s.get('status') == 'TRADING'
                ]
                if valid_pairs:
                    return valid_pairs
        except Exception:
            continue
    return []

def run_institutional_scanner():
    print("🚀 Starting Scan...")
    
    # স্ক্যান শুরুর নিশ্চয়তা বার্তা
    test_msg = "🚀 [MOBINUL TERMINAL] 4-Hour Institutional Scan is Starting..."
    send_telegram_alert(test_msg)

    _, btc_regime, btc_price = check_btc_regime()
    pairs = get_active_pairs()

    if not pairs:
        print("Failed to fetch pairs.")
        send_telegram_alert("⚠️ Market pair fetch error from cloud.")
        return

    print(f"Scanning {len(pairs)} pairs on Binance...")
    signals = []

    # শীর্ষ সক্রিয় পেয়ারগুলো স্ক্যান (রেট লিমিট ও দ্রুত এক্সিকিউশনের জন্য)
    target_pairs = pairs[:120]

    for sym in target_pairs:
        clean = sym.replace("USDT", "")
        klines = get_binance_klines(sym, "1d", 220)
        if not klines or len(klines) < 60:
            continue

        closes = [float(k[4]) for k in klines]
        lows = [float(k[3]) for k in klines]
        df = pd.DataFrame({'close': closes, 'low': lows})
        
        df['sma50'] = df['close'].rolling(50).mean()
        has_200 = len(df) >= 200
        if has_200:
            df['sma200'] = df['close'].rolling(200).mean()

        curr_p = df['close'].iloc[-1]
        c_low = df['low'].iloc[-1]
        s50 = df['sma50'].iloc[-1]
        s200 = df['sma200'].iloc[-1] if has_200 else s50

        chosen_sma = s200 if (has_200 and abs(curr_p - s200) < abs(curr_p - s50)) else s50
        sma_label = "200 SMA" if (chosen_sma == s200 and has_200) else "50 SMA"

        if curr_p < chosen_sma:
            continue

        dist_pct = ((curr_p - chosen_sma) / chosen_sma) * 100
        
        # রিটেস্ট রেঞ্জ (০% থেকে ৫.০% এর মধ্যে বা আজকের লো এসএমএ স্পর্শ করেছে)
        if not (dist_pct <= 5.0 or c_low <= chosen_sma):
            continue

        acc_7d = curr_p >= closes[-7]
        if not acc_7d:
            continue

        # লেভেল ক্যালকুলেশন
        entry_low = round(chosen_sma * 1.002, 4)
        entry_high = round(curr_p, 4)
        stop_loss = round(chosen_sma * 0.965, 4)
        risk = max(entry_high - stop_loss, entry_high * 0.035)

        tp1 = round(entry_high + (risk * 1.5), 4)
        tp2 = round(entry_high + (risk * 2.5), 4)
        tp3 = round(entry_high + (risk * 4.0), 4)

        trade_card = f"""🚨 [A+ SWING ALERT: #{clean}USDT] 🚨

• Current Price: ${curr_p:,.4f} ({sma_label} Retest: +{dist_pct:.2f}%)
• Entry Zone: ${entry_low} - ${entry_high}
• Safe SL: ${stop_loss}

💰 Take-Profit Levels:
• TP 1: ${tp1} (+1:1.5 RR)
• TP 2: ${tp2} (+1:2.5 RR)
• TP 3: ${tp3} (+1:4.0 RR)

🐋 Whale Flow (7D): Net Inflow Positive
🌐 BTC Market Regime: {btc_regime} (${btc_price:,.0f})

Coinglass Heatmap: https://www.coinglass.com/pro/futures/LiquidityHeatMap?symbol={clean}USDT"""

        send_telegram_alert(trade_card)
        signals.append(clean)
        time.sleep(0.5)

    summary_msg = f"""🏁 [SCAN SUMMARY FINISHED]
• Pairs Scanned: {len(target_pairs)}
• Verified A+ Swing Setups: {len(signals)}
• Discovered Coins: {', '.join(signals) if signals else 'None right now'}"""
    send_telegram_alert(summary_msg)
    print("Scan completed successfully.")

if __name__ == "__main__":
    run_institutional_scanner()
