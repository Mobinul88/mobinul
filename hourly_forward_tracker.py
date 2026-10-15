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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# এপিআই থেকে টিকার সংগ্রহ
tickers = []
endpoints = [
    "https://fapi.binance.com/fapi/v1/ticker/24hr",
    "https://data-api.binance.vision/api/v3/ticker/24hr"
]

for ep in endpoints:
    try:
        r = requests.get(ep, headers=headers, timeout=12)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                tickers = data
                print(f"Success fetching from: {ep}")
                break
    except Exception as e:
        print(f"Failed {ep}: {e}")

if not tickers:
    print("Warning: Could not fetch tickers from endpoints.")

def get_metrics(sym):
    fr = 0.0
    oi = 0.0
    try:
        r_fr = requests.get(f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={sym}", headers=headers, timeout=4).json()
        fr = float(r_fr.get("lastFundingRate", 0)) * 100
    except Exception:
        pass
    try:
        r_oi = requests.get(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={sym}", headers=headers, timeout=4).json()
        oi = float(r_oi.get("openInterest", 0))
    except Exception:
        pass
    return fr, oi

def classify_reason(chg, fr, vol):
    if fr <= -0.05:
        return "🚨 Short Squeeze (Heavy Neg Funding)"
    elif chg >= 40.0 and vol >= 20000000:
        return "💎 Institutional Mega Trend"
    elif vol >= 5000000:
        return "⚡ Aggressive Momentum Accumulation"
    else:
        return "⚠️ Low-Float / Spike"

rows = []
for t in tickers:
    if not isinstance(t, dict):
        continue
    sym = str(t.get("symbol", ""))
    if sym.endswith("USDT") and not sym.startswith("1000"):
        try:
            chg = float(t.get("priceChangePercent", 0))
            vol = float(t.get("quoteVolume", 0))
            price = float(t.get("lastPrice", 0))
            high = float(t.get("highPrice", 0))

            # ১৫%+ গেইন ও ৫০K ভলিউম
            if chg >= 15.0 and vol >= 50000 and price > 0:
                clean_sym = sym.replace("USDT", "")
                fr, oi = get_metrics(sym)
                reason = classify_reason(chg, fr, vol)
                
                rows.append({
                    "Detected_Time": now_str,
                    "Symbol": clean_sym,
                    "Detected_Gain_Pct": round(chg, 2),
                    "Detected_Price": price,
                    "Current_Price": price,
                    "Peak_Price": high,
                    "24h_Volume_USD": vol,
                    "Funding_Rate_Pct": round(fr, 4),
                    "Open_Interest": oi,
                    "Forensic_Reason": reason,
                    "Outcome_Category": "Analyzing...",
                    "Hours_Sustained": 1.0,
                    "Status": "ACTIVE_TRACKING"
                })
                print(f"-> Captured: {clean_sym} (+{chg:.2f}%)")
        except Exception:
            continue

print(f"Total target coins identified: {len(rows)}")

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
    print(f"SUCCESS: Wrote {len(df_final)} coins into {LOG_FILE}")
else:
    print("No coins met the criteria in this cycle.")
