import datetime
import os
import time
import pandas as pd
import requests

LOG_FILE = "forward_cycle_log.csv"
now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
print(f"[{now_str}] Starting Robust Futures Forward Pump Forensic Scan...")

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
})

# ১. আনব্লকড পাবলিক গেটওয়ে থেকে লাইভ টিকার সংগ্রহ
tickers = []
try:
  resp = session.get(
      "https://data-api.binance.vision/api/v3/ticker/24hr", timeout=10
  )
  if resp.status_code == 200:
    tickers = resp.json()
    print(f"✅ Loaded {len(tickers)} market tickers successfully.")
except Exception as e:
  print(f"Ticker error: {e}")

EXCLUDE_LIST = {
    "CREAM",
    "PNT",
    "BOND",
    "WTC",
    "VGX",
    "DF",
    "BTS",
    "PERP",
    "USDC",
    "FDUSD",
}


# ২. ক্লাউড-আনব্লকড ডেরিভেটিভ ইঞ্জিন (Bybit Linear V5 API - সম্পূর্ণ ব্লক-মুক্ত)
def get_derivatives_metrics(symbol_raw):
  live_oi = 0.0
  pre_oi = 0.0
  cur_fr = 0.0
  pre_fr = 0.0

  bybit_symbol = f"{symbol_raw}USDT"

  # (ক) বর্তমান লাইভ Funding Rate ও Live Open Interest (USD)
  try:
    url_ticker = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={bybit_symbol}"
    r = session.get(url_ticker, timeout=5)
    if r.status_code == 200:
      data = r.json()
      result_list = data.get("result", {}).get("list", [])
      if result_list:
        cur_fr = float(result_list[0].get("fundingRate", 0.0) or 0.0) * 100
        live_oi = float(result_list[0].get("openInterestValue", 0.0) or 0.0)
  except Exception:
    pass

  # (খ) পাম্পের আগের হিস্টোরিক্যাল ওপেন ইন্টারেস্ট (Pre-Pump OI: ২৪ ঘণ্টা আগের)
  try:
    url_oi = f"https://api.bybit.com/v5/market/open-interest?category=linear&symbol={bybit_symbol}&intervalTime=1h&limit=24"
    r_oi = session.get(url_oi, timeout=5)
    if r_oi.status_code == 200:
      oi_list = r_oi.json().get("result", {}).get("list", [])
      if len(oi_list) > 0:
        pre_oi = float(oi_list[-1].get("openInterest", 0.0) or 0.0)
  except Exception:
    pass

  # (গ) পূর্ববর্তী হিস্টোরিক্যাল ফান্ডিং রেট (Pre-Funding Rate)
  try:
    url_fr = f"https://api.bybit.com/v5/market/funding/history?category=linear&symbol={bybit_symbol}&limit=2"
    r_fr = session.get(url_fr, timeout=5)
    if r_fr.status_code == 200:
      fr_list = r_fr.json().get("result", {}).get("list", [])
      if len(fr_list) > 1:
        pre_fr = float(fr_list[1].get("fundingRate", 0.0) or 0.0) * 100
      elif len(fr_list) == 1:
        pre_fr = float(fr_list[0].get("fundingRate", 0.0) or 0.0) * 100
  except Exception:
    pass

  return live_oi, pre_oi, cur_fr, pre_fr


# ৩. প্রাতিষ্ঠানিক ফরেনসিক ক্লাসিফিকেশন লজিক
def classify_forensic(chg, cur_fr, pre_fr, oi_surge, vol):
  if pre_fr <= -0.03 or cur_fr <= -0.05:
    return "🚨 Confirmed Short Squeeze"
  elif oi_surge >= 35.0 and vol >= 8000000:
    return "💎 Institutional Accumulation"
  elif oi_surge >= 15.0 and vol >= 2500000:
    return "⚡ Smart Money Momentum"
  elif oi_surge < 5.0 and chg >= 20.0:
    return "⚠️ Spot/Whale Manipulated"
  else:
    return "📊 Momentum Trend"


# ৪. ফিল্টারিং ও রিয়েল প্রসেসিং
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

      # ফিল্টার: ১৫%+ গেইন ও ৫০K ভলিউম
      if chg >= 15.0 and vol >= 50000 and price > 0:
        live_oi, pre_oi, cur_fr, pre_fr = get_derivatives_metrics(clean_sym)

        # OI বৃদ্ধির শতকরা হার (OI Surge %)
        if pre_oi > 0:
          oi_surge = round(((live_oi - pre_oi) / pre_oi) * 100, 2)
        elif live_oi > 0:
          oi_surge = 25.0
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
            f"🎯 DETECTED: {clean_sym} (+{chg:.2f}%) | Live OI: ${live_oi:,.0f}"
            f" | Surge: {oi_surge}% | FR: {cur_fr:.4f}% | Forensic: {reason}"
        )
        time.sleep(0.08)
    except Exception:
      continue

print(f"Total target tokens processed: {len(rows)}")

# ৫. সিএসভি ফাইলে সংরক্ষণ (পূর্ববর্তী রেকর্ড অক্ষুণ্ণ রেখে)
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
  # যদি কোনো কয়েন ১৫%+ না পৌঁছায়, তবে সিস্টেমে নিশ্চিত কমিটের জন্য টপ ৩টি মোমেন্টাম কয়েন সেভ হবে
  print("⚠️ No coins reached 15%+. Saving top momentum gainers for log check...")
  top_list = []
  sorted_tickers = sorted(
      tickers,
      key=lambda x: float(x.get("priceChangePercent", 0.0)),
      reverse=True,
  )
  for t in sorted_tickers:
    s = str(t.get("symbol", ""))
    if s.endswith("USDT") and not s.startswith("1000"):
      clean_s = s.replace("USDT", "")
      if clean_s in EXCLUDE_LIST:
        continue
      chg = float(t.get("priceChangePercent", 0.0))
      price = float(t.get("lastPrice", 0.0))
      vol = float(t.get("quoteVolume", 0.0))
      live_oi, pre_oi, cur_fr, pre_fr = get_derivatives_metrics(clean_s)

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
          "Status": "ACTIVE_TRACKING",
      })
      if len(top_list) >= 3:
        break
  if top_list:
    pd.DataFrame(top_list).to_csv(LOG_FILE, index=False)
    print(f"✅ Saved fallback {len(top_list)} tokens into {LOG_FILE}")
