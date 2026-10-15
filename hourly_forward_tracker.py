import datetime
import os
import time
import pandas as pd
import requests

LOG_FILE = "forward_cycle_log.csv"
now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
print(f"[{now_str}] Starting Binance Futures Forward Pump Forensic Scan...")

session = requests.Session()
# ক্লাউড রানার ব্লকিং এড়াতে ব্রাউজার ইমুলেশন হেডার
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/",
    "client-type": "web"
})

tickers = []
TICKER_SOURCES = [
    "https://data-api.binance.vision/api/v3/ticker/24hr",
    "https://api.binance.com/api/v3/ticker/24hr"
]

for src in TICKER_SOURCES:
    try:
        resp = session.get(src, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                tickers = data
                print(f"Loaded {len(tickers)} tickers from: {src}")
                break
    except Exception as e:
        print(f"Failed {src}: {e}")

EXCLUDE_LIST = {"CREAM", "PNT", "BOND", "WTC", "VGX", "DF", "BTS", "PERP"}

# বাইনান্স ফিউচার্স গেটওয়ে লিস্ট
FUTURES_MIRRORS = [
    "https://fapi.binance.com",
    "https://fapi.binance.me",
    "https://fapi4.binance.com"
]

def get_futures_metrics(symbol_usdt):
    live_oi = 0.0
    pre_oi = 0.0
    cur_fr = 0.0
    pre_fr = 0.0

    # ১. ফান্ডিং রেট ফেচ
    for base in FUTURES_MIRRORS:
        try:
            r = session.get(f"{base}/fapi/v1/premiumIndex?symbol={symbol_usdt}", timeout=4)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    cur_fr = float(data.get("lastFundingRate", 0)) * 100
                    break
        except Exception:
            continue

    # ২. লাইভ ওপেন ইন্টারেস্ট ফেচ
    for base in FUTURES_MIRRORS:
        try:
            r = session.get(f"{base}/fapi/v1/openInterest?symbol={symbol_usdt}", timeout=4)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    live_oi = float(data.get("openInterest", 0))
                    break
        except Exception:
            continue

    # ৩. হিস্টোরিক্যাল ওআই (২৪ ঘণ্টা আগের ওআই)
    for base in FUTURES_MIRRORS:
        try:
            url = f"{base}/futures/data/openInterestHist?symbol={symbol_usdt}&period=1h&limit=24"
            r_hist = session.get(url, timeout=4)
            if r_hist.status_code == 200:
                h_data = r_hist.json()
                if isinstance(h_data, list) and len(h_data) > 0:
                    pre_oi = float(h_data[0].get("sumOpenInterest", 0))
                    break
        except Exception:
            continue

    # ৪. হিস্টোরিক্যাল ফান্ডিং রেট (Pre-Funding)
    for base in FUTURES_MIRRORS:
        try:
            url = f"{base}/fapi/v1/fundingRate?symbol={symbol_usdt}&limit=2"
            r_fr_hist = session.get(url, timeout=4)
            if r_fr_hist.status_code == 200:
                fh_data = r_fr_hist.json()
                if isinstance(fh_data, list) and len(fh_data) > 1:
                    pre_fr = float(fh_data[0].get("fundingRate", 0)) * 100
                    break
                elif isinstance(fh_data, list) and len(fh_data) == 1:
                    pre_fr = float(fh_data[0].get("fundingRate", 0)) * 100
                    break
        except Exception:
            continue

    return live_oi, pre_oi, cur_fr, pre_fr

def classify_forensic(chg, cur_fr, pre_fr, oi_surge, vol):
    if pre_fr <= -0.03 or cur_fr <= -0.05:
        return "🚨 Confirmed Short Squeeze"
    elif oi_surge >= 35.0 and vol >= 10000000:
        return "💎 Institutional Accumulation"
    elif oi_surge >= 15.0 and vol >= 3000000:
        return "⚡ Smart Money Inflow"
    elif oi_surge < 5.0 and chg >= 20.0:
        return "⚠️ Whale Spike / Trap Risk"
    else:
        return "📊 Momentum Trend"

rows = []
for t in tickers:
    if not isinstance(t, dict):
        continue
    sym = str(t.get("symbol", ""))

    if sym.endswith("USDT") and not sym.startswith("1000"):
        clean_sym = sym.replace("USDT", "")
        if clean_sym in EXCLUDE_LIST:
            continue

        try:
            chg = float(t.get("priceChangePercent", 0))
            vol = float(t.get("quoteVolume", 0))
            price = float(t.get("lastPrice", 0))
            high = float(t.get("highPrice", 0))

            if chg >= 15.0 and vol >= 50000 and price > 0:
                live_oi, pre_oi, cur_fr, pre_fr = get_futures_metrics(sym)

                if pre_oi > 0:
                    oi_surge = round(((live_oi - pre_oi) / pre_oi) * 100, 2)
                elif live_oi > 0:
                    oi_surge = 20.0
                else:
                    oi_surge = 0.0

                reason = classify_forensic(chg, cur_fr, pre_fr, oi_surge, vol)

                rows.append({
                    "Detected_Time": now_str,
                    "Symbol": clean_sym,
                    "Detected_Gain_Pct": round(chg, 2),
                    "Detected_Price": price,
                    "Current_Price": price,
                    "Peak_Price": high,
                    "24h_Volume_USD": vol,
                    "Pre_Pump_OI": round(pre_oi, 2),
                    "Current_OI": round(live_oi, 2),
                    "OI_Surge_Pct": oi_surge,
                    "Pre_Funding_Rate": round(pre_fr, 4),
                    "Current_Funding_Rate": round(cur_fr, 4),
                    "Forensic_Reason": reason,
                    "Outcome_Category": "Analyzing...",
                    "Hours_Sustained": 1.0,
                    "Status": "ACTIVE_TRACKING"
                })
                print(f"DETECTED: {clean_sym} (+{chg:.2f}%) | OI: {live_oi} | Surge: {oi_surge}% | FR: {cur_fr:.4f}%")
                time.sleep(0.08)
        except Exception:
            continue

print(f"Total target tokens identified: {len(rows)}")

if rows:
    df_new = pd.DataFrame(rows).sort_values(by="Detected_Gain_Pct", ascending=False)
    if os.path.exists(LOG_FILE):
        try:
            df_old = pd.read_csv(LOG_FILE)
            if not df_old.empty and "Symbol" in df_old.columns:
                df_final = pd.concat([df_new, df_old], ignore_index=True).drop_duplicates(subset=["Symbol"], keep="first")
            else:
                df_final = df_new
        except Exception:
            df_final = df_new
    else:
        df_final = df_new
    df_final.to_csv(LOG_FILE, index=False)
    print(f"SUCCESS: Wrote {len(df_final)} records into {LOG_FILE}")
else:
    print("No coins currently met 15%+ pump criteria.")
