import os
import time
import datetime
import requests
import pandas as pd

LOG_FILE = "forward_cycle_log.csv"
now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
print(f"[{now_str}] Starting Binance Futures Forward Pump Forensic Scan...")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json"
})

# বাইনান্সের ফিউচার্স গেটওয়ে
BINANCE_FUTURES_URLS = [
    "https://fapi.binance.com",
    "https://fapi.binance.me",
    "https://fapi4.binance.com"
]

def make_binance_request(endpoint):
    for base in BINANCE_FUTURES_URLS:
        try:
            url = f"{base}{endpoint}"
            r = session.get(url, timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            continue
    return None

# ১. বাইনান্স ফিউচার্স ২৪ ঘণ্টার টিকার সরাসরি সংগ্রহ
print("Fetching 24hr Binance Futures tickers...")
raw_tickers = make_binance_request("/fapi/v1/ticker/24hr")

# ব্যাকআপ মিরর
if not raw_tickers or not isinstance(raw_tickers, list):
    try:
        alt_url = "https://data-api.binance.vision/api/v3/ticker/24hr"
        resp = session.get(alt_url, timeout=8)
        if resp.status_code == 200:
            raw_tickers = resp.json()
    except Exception:
        pass

tickers = raw_tickers if isinstance(raw_tickers, list) else []
print(f"✅ Loaded {len(tickers)} tickers from Binance.")

# ২. বাইনান্স ফিউচার্স লাইভ ফান্ডিং রেট ম্যাপ
funding_map = {}
premium_data = make_binance_request("/fapi/v1/premiumIndex")
if premium_data and isinstance(premium_data, list):
    for item in premium_data:
        sym = item.get("symbol", "")
        if sym.endswith("USDT"):
            funding_map[sym] = float(item.get("lastFundingRate", 0.0) or 0.0) * 100
    print(f"✅ Loaded {len(funding_map)} Binance Futures live funding rates.")

EXCLUDE_LIST = {"CREAM", "PNT", "BOND", "WTC", "VGX", "DF", "BTS", "PERP", "USDC", "FDUSD"}

# ৩. বাইনান্সের নিজস্ব ফিউচার্স ওআই ও হিস্টোরিক্যাল মেট্রিক্স
def get_binance_exact_metrics(symbol_usdt):
    live_oi = 0.0
    pre_oi = 0.0
    pre_fr = 0.0
    
    # লাইভ ওপেন ইন্টারেস্ট
    oi_data = make_binance_request(f"/fapi/v1/openInterest?symbol={symbol_usdt}")
    if oi_data and isinstance(oi_data, dict):
        live_oi = float(oi_data.get("openInterest", 0.0) or 0.0)

    # ২৪ ঘণ্টা আগের ওপেন ইন্টারেস্ট
    oi_hist = make_binance_request(f"/futures/data/openInterestHist?symbol={symbol_usdt}&period=1h&limit=24")
    if oi_hist and isinstance(oi_hist, list) and len(oi_hist) > 0:
        pre_oi = float(oi_hist[0].get("sumOpenInterest", 0.0) or 0.0)

    # আগের সাইকেলের ফান্ডিং রেট
    fr_hist = make_binance_request(f"/fapi/v1/fundingRate?symbol={symbol_usdt}&limit=2")
    if fr_hist and isinstance(fr_hist, list):
        if len(fr_hist) > 1:
            pre_fr = float(fr_hist[0].get("fundingRate", 0.0) or 0.0) * 100
        elif len(fr_hist) == 1:
            pre_fr = float(fr_hist[0].get("fundingRate", 0.0) or 0.0) * 100

    return live_oi, pre_oi, pre_fr

# ৪. ফরেনসিক অ্যানালাইসিস লজিক
def classify_forensic(chg, cur_fr, pre_fr, oi_surge, vol):
    if pre_fr <= -0.03 or cur_fr <= -0.05:
        return "🚨 Confirmed Short Squeeze"
    elif oi_surge >= 35.0 and vol >= 8000000:
        return "💎 Institutional Accumulation"
    elif oi_surge >= 15.0 and vol >= 2500000:
        return "⚡ Smart Money Inflow"
    elif oi_surge < 5.0 and chg >= 20.0:
        return "⚠️ Spot/Whale Manipulated"
    else:
        return "📊 Momentum Trend"

# ৫. কয়েন ফিল্টারিং
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
            chg = float(t.get("priceChangePercent", 0.0))
            vol = float(t.get("quoteVolume", 0.0))
            price = float(t.get("lastPrice", 0.0))
            high = float(t.get("highPrice", 0.0))
            
            # ১৫%+ গেইন ও ৫০K ভলিউম ফিল্টার
            if chg >= 15.0 and vol >= 50000 and price > 0:
                cur_fr = funding_map.get(sym, 0.0)
                live_oi, pre_oi, pre_fr = get_binance_exact_metrics(sym)
                
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
                print(f"🎯 DETECTED: {clean_sym} (+{chg:.2f}%) | Binance OI: {live_oi:,.0f} | Surge: {oi_surge}% | Binance FR: {cur_fr:.4f}%")
                time.sleep(0.08)
        except Exception:
            continue

print(f"Total target tokens processed: {len(rows)}")

# ৬. ফাইলে সংরক্ষণ
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
    print(f"✅ SUCCESS: Wrote {len(df_final)} records into {LOG_FILE}")
else:
    print("⚠️ No 15%+ pumpers. Saving top gainers for health check...")
    top_list = []
    sorted_tickers = sorted(tickers, key=lambda x: float(x.get("priceChangePercent", 0.0)), reverse=True)
    for t in sorted_tickers:
        s = str(t.get("symbol", ""))
        if s.endswith("USDT") and not s.startswith("1000"):
            clean_s = s.replace("USDT", "")
            if clean_s in EXCLUDE_LIST:
                continue
            chg = float(t.get("priceChangePercent", 0.0))
            price = float(t.get("lastPrice", 0.0))
            vol = float(t.get("quoteVolume", 0.0))
            cur_fr = funding_map.get(s, 0.0)
            live_oi, pre_oi, pre_fr = get_binance_exact_metrics(s)
            
            top_list.append({
                "Detected_Time": now_str,
                "Symbol": clean_s,
                "Detected_Gain_Pct": round(chg, 2),
                "Detected_Price": price,
                "Current_Price": price,
                "Peak_Price": float(t.get("highPrice", price)),
                "24h_Volume_USD": vol,
                "Pre_Pump_OI": round(pre_oi, 2),
                "Current_OI": round(live_oi, 2),
                "OI_Surge_Pct": 15.0,
                "Pre_Funding_Rate": round(pre_fr, 4),
                "Current_Funding_Rate": round(cur_fr, 4),
                "Forensic_Reason": "📊 Leading Momentum",
                "Outcome_Category": "Analyzing...",
                "Hours_Sustained": 1.0,
                "Status": "ACTIVE_TRACKING"
            })
            if len(top_list) >= 3:
                break
    if top_list:
        pd.DataFrame(top_list).to_csv(LOG_FILE, index=False)
        print(f"✅ Saved fallback {len(top_list)} tokens into {LOG_FILE}")
