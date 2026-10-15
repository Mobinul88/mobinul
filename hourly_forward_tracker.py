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
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
})

# ১. ফিউচার্স টিকার ফেচ (বাইনান্সের অল্টারনেটিভ মিরর রুট)
tickers = []
active_base = None

MIRRORS = [
    "https://fapi.binance.com",
    "https://fapi.binance.me",
    "https://data-api.binance.vision",
]

for base in MIRRORS:
  try:
    if "vision" in base:
      url = f"{base}/api/v3/ticker/24hr"
    else:
      url = f"{base}/fapi/v1/ticker/24hr"

    resp = session.get(url, timeout=10)
    if resp.status_code == 200:
      data = resp.json()
      if isinstance(data, list) and len(data) > 0:
        tickers = data
        active_base = base
        print(f"✅ Loaded {len(tickers)} tickers from: {base}")
        break
  except Exception as e:
    print(f"Mirror failed {base}: {e}")

# ২. ফিউচার্স প্রিমিয়াম ইনডেক্স ও ফান্ডিং রেট ম্যাপ
funding_map = {}
premium_urls = [
    "https://fapi.binance.com/fapi/v1/premiumIndex",
    "https://fapi.binance.me/fapi/v1/premiumIndex",
]
for p_url in premium_urls:
  try:
    r_fr = session.get(p_url, timeout=8)
    if r_fr.status_code == 200:
      for item in r_fr.json():
        sym = item.get("symbol", "")
        if sym.endswith("USDT"):
          funding_map[sym] = float(item.get("lastFundingRate", 0)) * 100
      print(f"✅ Loaded {len(funding_map)} live funding rates.")
      break
  except Exception:
    pass


# ৩. লাইভ ওপেন ইন্টারেস্ট
def get_current_oi(symbol):
  for b in ["https://fapi.binance.com", "https://fapi.binance.me"]:
    try:
      url = f"{b}/fapi/v1/openInterest?symbol={symbol}"
      res = session.get(url, timeout=4)
      if res.status_code == 200:
        return float(res.json().get("openInterest", 0))
    except Exception:
      continue
  return 0.0


# ৪. পাম্পের আগের হিস্টোরিক্যাল ডেটা (Pre-Pump OI ও Pre-Pump Funding)
def get_pre_pump_data(symbol):
  pre_oi = 0.0
  pre_funding = 0.0

  # ২৪ ঘণ্টার আগের ওআই
  for b in ["https://fapi.binance.com", "https://fapi.binance.me"]:
    try:
      url = f"{b}/futures/data/openInterestHist?symbol={symbol}&period=1h&limit=24"
      res = session.get(url, timeout=4)
      if res.status_code == 200:
        d = res.json()
        if isinstance(d, list) and len(d) > 0:
          pre_oi = float(d[0].get("sumOpenInterest", 0))
          break
    except Exception:
      continue

  # আগের সাইকেলের ফান্ডিং রেট
  for b in ["https://fapi.binance.com", "https://fapi.binance.me"]:
    try:
      url = f"{b}/fapi/v1/fundingRate?symbol={symbol}&limit=2"
      res = session.get(url, timeout=4)
      if res.status_code == 200:
        d = res.json()
        if isinstance(d, list) and len(d) > 1:
          pre_funding = float(d[0].get("fundingRate", 0)) * 100
        elif isinstance(d, list) and len(d) == 1:
          pre_funding = float(d[0].get("fundingRate", 0)) * 100
        break
    except Exception:
      continue

  return pre_oi, pre_funding


# ৫. ক্লাসিফিকেশন লজিক
def classify_forensic(chg, cur_fr, pre_fr, oi_surge, vol):
  if pre_fr <= -0.03 or cur_fr <= -0.05:
    return "🚨 Confirmed Short Squeeze"
  elif oi_surge >= 40.0 and vol >= 10000000:
    return "💎 Institutional Accumulation"
  elif oi_surge >= 15.0 and vol >= 3000000:
    return "⚡ Smart Money Momentum"
  elif oi_surge < 5.0 and chg >= 20.0:
    return "⚠️ Spot/Whale Manipulated"
  else:
    return "📊 Momentum Trend"


# ৬. টোকেন ফিল্টারিং ও প্রসেসিং
rows = []
# ডিলিস্টেড কয়েন ঠেকানোর ফিল্টার
EXCLUDE_SYMBOLS = {"CREAM", "PNT", "BOND", "WTC", "VGX", "DF"}

for t in tickers:
  if not isinstance(t, dict):
    continue
  sym = str(t.get("symbol", ""))

  if sym.endswith("USDT") and not sym.startswith("1000"):
    clean_sym = sym.replace("USDT", "")
    if clean_sym in EXCLUDE_SYMBOLS:
      continue

    try:
      chg = float(t.get("priceChangePercent", 0))
      vol = float(t.get("quoteVolume", 0))
      price = float(t.get("lastPrice", 0))
      high = float(t.get("highPrice", 0))

      # ১৫%+ গেইন ও ৫০K ভলিউম
      if chg >= 15.0 and vol >= 50000 and price > 0:
        cur_fr = funding_map.get(sym, 0.0)
        cur_oi = get_current_oi(sym)
        pre_oi, pre_fr = get_pre_pump_data(sym)

        oi_surge = (
            round(((cur_oi - pre_oi) / pre_oi) * 100, 2) if pre_oi > 0 else 0.0
        )
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
            "Current_OI": round(cur_oi, 2),
            "OI_Surge_Pct": oi_surge,
            "Pre_Funding_Rate": round(pre_fr, 4),
            "Current_Funding_Rate": round(cur_fr, 4),
            "Forensic_Reason": reason,
            "Outcome_Category": "Analyzing...",
            "Hours_Sustained": 1.0,
            "Status": "ACTIVE_TRACKING",
        })
        print(
            f"🎯 DETECTED: {clean_sym} (+{chg:.2f}%) | Pre-OI: {pre_oi:,.0f} ->"
            f" Cur-OI: {cur_oi:,.0f} (+{oi_surge}%)"
        )
        time.sleep(0.08)
    except Exception:
      continue

print(f"Total target tokens identified: {len(rows)}")

# ৭. সিএসভি ফাইলে সেভ করা
if rows:
  df_new = pd.DataFrame(rows).sort_values(
      by="Detected_Gain_Pct", ascending=False
  )

  if os.path.exists(LOG_FILE):
    try:
      df_old = pd.read_csv(LOG_FILE)
      if not df_old.empty and "Symbol" in df_old.columns:
        df_final = pd.concat([df_new, df_old], ignore_index=True).drop_duplicates(
            subset=["Symbol"], keep="first"
        )
      else:
        df_final = df_new
    except Exception:
      df_final = df_new
  else:
    df_final = df_new

  df_final.to_csv(LOG_FILE, index=False)
  print(f"✅ SUCCESS: Wrote {len(df_final)} records into {LOG_FILE}")
else:
  print("No coins reached 15%+ in this cycle.")
