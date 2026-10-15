import requests
import pandas as pd
import datetime
import os
import time

LOG_FILE = "forward_cycle_log.csv"
now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
print(f"[{now_str}] Starting Binance Futures Forward Pump Forensic Scan...")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# ১. লাইভ Funding Rate এবং সক্রিয় ফিউচার্স কন্ট্রাক্ট সংগ্রহ (সবচেয়ে নির্ভরযোগ্য এন্ডপয়েন্ট)
funding_map = {}
valid_futures_symbols = set()

premium_endpoints = [
    "https://fapi.binance.com/fapi/v1/premiumIndex",
    "https://fapi.binance.org/fapi/v1/premiumIndex"
]

for p_url in premium_endpoints:
    try:
        r = requests.get(p_url, headers=headers, timeout=12)
        if r.status_code == 200:
            for item in r.json():
                s = item.get("symbol", "")
                if s.endswith("USDT"):
                    valid_futures_symbols.add(s)
                    funding_map[s] = float(item.get("lastFundingRate", 0)) * 100
            print(f"✅ Loaded {len(valid_futures_symbols)} ACTIVE Binance Futures pairs from {p_url}")
            break
    except Exception as e:
        print(f"PremiumIndex error on {p_url}: {e}")

# ২. লাইভ ২৪ ঘণ্টার ফিউচার্স টিকার ফেচ
tickers = []
ticker_endpoints = [
    "https://fapi.binance.com/fapi/v1/ticker/24hr",
    "https://fapi.binance.org/fapi/v1/ticker/24hr"
]

for t_url in ticker_endpoints:
    try:
        r = requests.get(t_url, headers=headers, timeout=12)
        if r.status_code == 200:
            tickers = r.json()
            print(f"✅ Loaded {len(tickers)} tickers from {t_url}")
            break
    except Exception as e:
        print(f"Ticker error on {t_url}: {e}")

# ৩. লাইভ ওপেন ইন্টারেস্ট (OI) ফেচ ফাংশন
def get_live_oi(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}"
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            return float(res.json().get("openInterest", 0))
    except Exception:
        pass
    return 0.0

# ৪. ফরেনসিক লজিক ক্লাসিফিকেশন
def classify_forensic_reason(chg_pct, funding_rate, vol_usd):
    if funding_rate <= -0.05:
        return "🚨 Short Squeeze (Heavy Neg Funding)"
    elif funding_rate < 0.0:
        return "⚡ Bear Trap / Mild Short Squeeze"
    elif chg_pct >= 35.0 and vol_usd >= 15000000:
        return "💎 Institutional Mega Trend (Heavy Vol)"
    elif vol_usd >= 3000000:
        return "⚡ Aggressive Momentum Accumulation"
    else:
        return "⚠️ Low-Float / Whale Spike"

# ৫. পাম্পিং কয়েন ফিল্টার
rows = []
for t in tickers:
    if not isinstance(t, dict):
        continue
    sym = str(t.get("symbol", ""))

    # ভেরিফাইড অ্যাক্টিভ ফিউচার্স পেয়ার এবং ইনডেক্স টোকেন বাদ
    if (sym in valid_futures_symbols or sym.endswith("USDT")) and not sym.startswith("1000"):
        try:
            chg = float(t.get("priceChangePercent", 0))
            vol = float(t.get("quoteVolume", 0))
            price = float(t.get("lastPrice", 0))
            high = float(t.get("highPrice", 0))

            # ১৫%+ পাম্প ও ভলিউম ফিল্টার
            if chg >= 15.0 and vol >= 50000 and price > 0:
                clean_sym = sym.replace("USDT", "")
                funding_pct = funding_map.get(sym, 0.0)
                live_oi = get_live_oi(sym)
                reason = classify_forensic_reason(chg, funding_pct, vol)

                rows.append({
                    "Detected_Time": now_str,
                    "Symbol": clean_sym,
                    "Detected_Gain_Pct": round(chg, 2),
                    "Detected_Price": price,
                    "Current_Price": price,
                    "Peak_Price": high,
                    "24h_Volume_USD": vol,
                    "Funding_Rate_Pct": round(funding_pct, 4),
                    "Open_Interest": live_oi,
                    "Forensic_Reason": reason,
                    "Outcome_Category": "Analyzing...",
                    "Hours_Sustained": 1.0,
                    "Status": "ACTIVE_TRACKING"
                })
                print(f"🎯 DETECTED: {clean_sym} (+{chg:.2f}%) | FR: {funding_pct:.4f}% | OI: {live_oi:,.0f} | Reason: {reason}")
                time.sleep(0.05)
        except Exception:
            continue

print(f"Total target tokens identified: {len(rows)}")

# ৬. ফাইলে নিশ্চিতভাবে রাইট করা (Force Write)
if rows:
    df_new = pd.DataFrame(rows).sort_values(by="Detected_Gain_Pct", ascending=False)
    df_new.to_csv(LOG_FILE, index=False)
    print(f"✅ SUCCESS: Written {len(df_new)} pure active futures coins into {LOG_FILE}")
else:
    print("No tokens met the criteria in this scan.")
