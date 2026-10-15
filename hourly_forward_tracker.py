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
        " like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
})

# ১. আনব্লকড পাবলিক টিকার
tickers = []
try:
  resp = session.get(
      "https://data-api.binance.vision/api/v3/ticker/24hr", timeout=10
  )
  if resp.status_code == 200:
    tickers = resp.json()
    print(f"Loaded {len(tickers)} tickers.")
except Exception as e:
  print(f"Ticker error: {e}")

EXCLUDE_LIST = {"CREAM", "PNT", "BOND", "WTC", "VGX", "DF", "BTS", "PERP"}


# ২. ক্লাউড ব্লকিং বাইপাস করে লাইভ ওআই এবং ফান্ডিং রেট সংগ্রহের ফাংশন
def fetch_unblocked_futures_metrics(symbol_usdt):
  live_oi = 0.0
  pre_oi = 0.0
  cur_fr = 0.0
  pre_fr = 0.0

  # ক্লাউড রানারের জন্য পাবলিক বাইপাস গেটওয়ে রাউটিং
  target_url = (
      f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol_usdt}"
  )
  proxy_urls = [
      target_url,
      f"https://api.allorigins.win/raw?url={target_url}",
      f"https://fapi.binance.me/fapi/v1/premiumIndex?symbol={symbol_usdt}",
  ]

  for p_url in proxy_urls:
    try:
      r = session.get(p_url, timeout=5)
      if r.status_code == 200:
        d = r.json()
        if isinstance(d, dict):
          cur_fr = float(d.get("lastFundingRate", 0)) * 100
          break
    except Exception:
      continue

  # ওপেন ইন্টারেস্ট ফেচ
  oi_target = (
      f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol_usdt}"
  )
  oi_proxies = [
      oi_target,
      f"https://api.allorigins.win/raw?url={oi_target}",
      f"https://fapi.binance.me/fapi/v1/openInterest?symbol={symbol_usdt}",
  ]

  for p_url in oi_proxies:
    try:
      r = session.get(p_url, timeout=5)
      if r.status_code == 200:
        d = r.json()
        if isinstance(d, dict):
          live_oi = float(d.get("openInterest", 0))
          break
    except Exception:
      continue

  # হিস্টোরিক্যাল ওআই (২৪ ঘণ্টা আগের ওআই)
  hist_target = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol_usdt}&period=1h&limit=24"
  for p_url in [
      hist_target,
      f"https://api.allorigins.win/raw?url={hist_target}",
  ]:
    try:
      r = session.get(p_url, timeout=5)
      if r.status_code == 200:
        hd = r.json()
        if isinstance(hd, list) and len(hd) > 0:
          pre_oi = float(hd[0].get("sumOpenInterest", 0))
          break
    except Exception:
      continue

  # হিস্টোরিক্যাল ফান্ডিং রেট (পূর্ববর্তী সাইকেল)
  fr_target = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol_usdt}&limit=2"
  for p_url in [fr_target, f"https://api.allorigins.win/raw?url={fr_target}"]:
    try:
      r = session.get(p_url, timeout=5)
      if r.status_code == 200:
        fhd = r.json()
        if isinstance(fhd, list) and len(fhd) > 1:
          pre_fr = float(fhd[0].get("fundingRate", 0)) * 100
          break
        elif isinstance(fhd, list) and len(fhd) == 1:
          pre_fr = float(fhd[0].get("fundingRate", 0)) * 100
          break
    except Exception:
      continue

  return live_oi, pre_oi, cur_fr, pre_fr


# ৩. ফরেনসিক ক্লাসিফিকেশন লজিক
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


# ৪. ফিল্টারিং ও প্রসেসিং
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

      # ১৫%+ গেইন ও ৫০K ভলিউম
      if chg >= 15.0 and vol >= 50000 and price > 0:
        live_oi, pre_oi, cur_fr, pre_fr = fetch_unblocked_futures_metrics(sym)

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
            "Status": "ACTIVE_TRACKING",
        })
        print(
            f"DETECTED: {clean_sym} (+{chg:.2f}%) | OI: {live_oi:,.0f} | Surge:"
            f" {oi_surge}% | FR: {cur_fr:.4f}%"
        )
        time.sleep(0.08)
    except Exception:
      continue

print(f"Total target tokens identified: {len(rows)}")

# ৫. সিএসভি ফাইলে সেভ
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
  print(f"SUCCESS: Wrote {len(df_final)} records into {LOG_FILE}")
else:
  print("No coins currently met 15%+ pump criteria.")
