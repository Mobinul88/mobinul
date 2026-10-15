import requests
import pandas as pd
import datetime
import os
import json
import time

LOG_FILE = "forward_cycle_log.csv"
CONFIG_FILE = "engine_config.json"
BINANCE_FAPI_BASE = "https://fapi.binance.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = requests.Session()
session.headers.update(HEADERS)

def get_market_tickers():
    url = f"{BINANCE_FAPI_BASE}/fapi/v1/ticker/24hr"
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error fetching 24hr tickers: {e}")
    return []

def get_funding_and_oi(symbol):
    funding_rate = 0.0
    open_interest = 0.0
    try:
        f_url = f"{BINANCE_FAPI_BASE}/fapi/v1/premiumIndex?symbol={symbol}"
        fr_res = session.get(f_url, timeout=5).json()
        funding_rate = float(fr_res.get("lastFundingRate", 0)) * 100
    except Exception:
        pass

    try:
        oi_url = f"{BINANCE_FAPI_BASE}/fapi/v1/openInterest?symbol={symbol}"
        oi_res = session.get(oi_url, timeout=5).json()
        open_interest = float(oi_res.get("openInterest", 0))
    except Exception:
        pass

    return funding_rate, open_interest

def classify_pump_reason(chg_pct, funding_rate, vol_usd):
    if funding_rate <= -0.05:
        return "🚨 Short Squeeze (Heavy Neg Funding)"
    elif chg_pct >= 40.0 and vol_usd >= 20000000:
        return "💎 Institutional Mega Trend (Heavy Vol)"
    elif vol_usd >= 5000000:
        return "⚡ Aggressive Momentum Accumulation"
    else:
        return "⚠️ Low-Float / Whale Spike"

def run_hourly_forensic_scan():
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] Starting Hourly Binance Forward Pump Tracker...")

    tickers = get_market_tickers()
    if not tickers or not isinstance(tickers, list):
        print("No ticker data received from Binance API.")
        return

    df_log = pd.DataFrame()
    if os.path.exists(LOG_FILE):
        try:
            df_log = pd.read_csv(LOG_FILE)
        except Exception:
            df_log = pd.DataFrame()

    new_entries = []
    for item in tickers:
        sym = item.get("symbol", "")
        if not sym.endswith("USDT") or sym.startswith("1000"):
            continue

        clean_sym = sym.replace("USDT", "")

        try:
            chg = float(item.get("priceChangePercent", 0))
            vol = float(item.get("quoteVolume", 0))
            price = float(item.get("lastPrice", 0))
            high_24h = float(item.get("highPrice", 0))

            # ১৫%+ গেইন ও অন্তত ৫০,০০০ ভলিউম হলেই তাৎক্ষণিক রেকর্ড হবে
            if chg >= 15.0 and vol >= 50000 and price > 0:
                funding, oi = get_funding_and_oi(sym)
                reason = classify_pump_reason(chg, funding, vol)

                new_entries.append({
                    "Detected_Time": now_str,
                    "Symbol": clean_sym,
                    "Detected_Gain_Pct": round(chg, 2),
                    "Detected_Price": price,
                    "Current_Price": price,
                    "Peak_Price": high_24h,
                    "24h_Volume_USD": vol,
                    "Funding_Rate_Pct": round(funding, 4),
                    "Open_Interest": oi,
                    "Forensic_Reason": reason,
                    "Outcome_Category": "Analyzing...",
                    "Hours_Sustained": 1.0,
                    "Status": "ACTIVE_TRACKING"
                })
        except Exception:
            continue

    if new_entries:
        df_new = pd.DataFrame(new_entries)
        # যদি ফাইল খালি থাকে বা নতুন হয়
        if df_log.empty or "Symbol" not in df_log.columns:
            df_final = df_new
        else:
            # ডুপ্লিকেট বাদ দিয়ে মার্জ করা
            df_final = pd.concat([df_new, df_log], ignore_index=True).drop_duplicates(subset=["Symbol"], keep="first")
        
        # পার্সেন্টেজ অনুযায়ী বড় থেকে ছোট সাজানো
        df_final = df_final.sort_values(by="Detected_Gain_Pct", ascending=False)
        df_final.to_csv(LOG_FILE, index=False)
        print(f"✅ SUCCESS: Wrote {len(df_final)} coins into {LOG_FILE}")
    else:
        print("ℹ️ No 15%+ gainers detected.")

if __name__ == "__main__":
    run_hourly_forensic_scan()
