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
    """বাইনান্স ফিউচার্স থেকে লাইভ টিকার ডেটা নিয়ে আসা"""
    url = f"{BINANCE_FAPI_BASE}/fapi/v1/ticker/24hr"
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error fetching 24hr tickers: {e}")
    return []

def get_funding_and_oi(symbol):
    """কয়েনটি কেন পাম্প করছে তা যাচাই করতে Funding Rate এবং Open Interest অ্যানালাইসিস"""
    funding_rate = 0.0
    open_interest = 0.0
    
    # Funding Rate
    try:
        f_url = f"{BINANCE_FAPI_BASE}/fapi/v1/premiumIndex?symbol={symbol}"
        fr_res = session.get(f_url, timeout=5).json()
        funding_rate = float(fr_res.get("lastFundingRate", 0)) * 100  # পার্সেন্টেজে রূপান্তর
    except Exception:
        pass

    # Open Interest
    try:
        oi_url = f"{BINANCE_FAPI_BASE}/fapi/v1/openInterest?symbol={symbol}"
        oi_res = session.get(oi_url, timeout=5).json()
        open_interest = float(oi_res.get("openInterest", 0))
    except Exception:
        pass

    return funding_rate, open_interest

def classify_pump_reason(chg_pct, funding_rate, vol_usd):
    """
    ফরেনসিক লজিক: কয়েনটি কেন পাম্প করছে?
    """
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

    # ১. আগের তৈরি করা লগ ফাইল লোড করা
    if os.path.exists(LOG_FILE):
        try:
            df_log = pd.read_csv(LOG_FILE)
        except Exception:
            df_log = pd.DataFrame()
    else:
        df_log = pd.DataFrame()

    # ২. চলমান অ্যাক্টিভ ট্রেডগুলোর বর্তমান অবস্থা ট্র্যাক ও আপডেট করা
    if not df_log.empty and "Status" in df_log.columns:
        price_map = {}
        for item in tickers:
            sym = item.get("symbol", "")
            if sym.endswith("USDT"):
                price_map[sym.replace("USDT", "")] = float(item.get("lastPrice", 0))

        for idx, row in df_log.iterrows():
            if row.get("Status") == "ACTIVE_TRACKING":
                s_name = row["Symbol"]
                cur_p = price_map.get(s_name)
                if cur_p:
                    entry_p = float(row["Detected_Price"])
                    peak_p = max(float(row.get("Peak_Price", entry_p)), cur_p)
                    df_log.at[idx, "Peak_Price"] = peak_p
                    df_log.at[idx, "Current_Price"] = cur_p
                    
                    # কয়েনটি কত ঘণ্টা ধরে প্রাইস ধরে রাখতে পেরেছে
                    try:
                        det_time = datetime.datetime.strptime(str(row["Detected_Time"]), "%Y-%m-%d %H:%M:%S")
                        hours_alive = (now - det_time).total_seconds() / 3600.0
                        df_log.at[idx, "Hours_Sustained"] = round(hours_alive, 1)
                    except Exception:
                        hours_alive = 1.0

                    # ক্যাটাগরি নির্ধারণ (Super-Trend নাকি Flash Trap)
                    drawdown_from_peak = ((peak_p - cur_p) / peak_p) * 100
                    if drawdown_from_peak >= 18.0:
                        df_log.at[idx, "Outcome_Category"] = "Flash Trap"
                        if hours_alive >= 24:
                            df_log.at[idx, "Status"] = "CLOSED_DUMPED"
                    elif cur_p >= entry_p and hours_alive >= 12:
                        df_log.at[idx, "Outcome_Category"] = "Super-Trend"

    # ৩. ইতিমধ্যে আজকে রেকর্ড হওয়া সিম্বলগুলোর তালিকা
    logged_symbols_today = []
    if not df_log.empty and "Detected_Time" in df_log.columns:
        today_str = now.strftime("%Y-%m-%d")
        logged_symbols_today = df_log[df_log["Detected_Time"].str.contains(today_str, na=False)]["Symbol"].tolist()

    # ৪. নতুন পাম্পিং কয়েন স্ক্যান করা (১৫%+ গেইন এবং অন্তত $১০০,০০০ ভলিউম)
    new_entries = []
    for item in tickers:
        sym = item.get("symbol", "")
        # শুধুমাত্র USDT ফিউচার্স পেয়ার
        if not sym.endswith("USDT") or sym.startswith("1000"):
            continue

        clean_sym = sym.replace("USDT", "")
        if clean_sym in logged_symbols_today:
            continue

        try:
            chg = float(item.get("priceChangePercent", 0))
            vol = float(item.get("quoteVolume", 0))
            price = float(item.get("lastPrice", 0))
            high_24h = float(item.get("highPrice", 0))

            # আপনার দেওয়া ক্রাইটেরিয়া: ১৫% গেইন ও ১০০K ভলিউম
            if chg >= 15.0 and vol >= 100000 and price > 0:
                funding, oi = get_funding_and_oi(sym)
                reason = classify_pump_reason(chg, funding, vol)

                new_row = {
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
                }
                new_entries.append(new_row)
                print(f"🎯 DETECTED: {clean_sym} (+{chg:.2f}%) | Vol: ${round(vol/1e6, 2)}M | Reason: {reason}")
                time.sleep(0.3)
        except Exception:
            continue

    # ৫. নতুন এন্ট্রি থাকলে ফাইলে সংরক্ষণ করা
    if new_entries:
        df_new = pd.DataFrame(new_entries)
        if df_log.empty:
            df_final = df_new
        else:
            df_final = pd.concat([df_log, df_new], ignore_index=True)
        df_final.to_csv(LOG_FILE, index=False)
        print(f"✅ Successfully written {len(new_entries)} coins to {LOG_FILE}")
    else:
        if not df_log.empty:
            df_log.to_csv(LOG_FILE, index=False)
        print("ℹ️ No new unlogged 15%+ gainers in this hourly scan.")

if __name__ == "__main__":
    run_hourly_forensic_scan()
