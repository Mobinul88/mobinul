import datetime
import os
import time
import pandas as pd
import requests

LOG_FILE = "forward_cycle_log.csv"
now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
print(f"[{now_str}] Starting Binance Futures Forward Pump Forensic Scan...")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# ১. লাইভ ফিউচার্স প্রিমিয়াম ইনডেক্স ও ফান্ডিং রেট ম্যাপ
funding_map = {}
valid_futures_symbols = set()

try:
  r_fr = requests.get(
      "https://fapi.binance.com/fapi/v1/premiumIndex",
      headers=headers,
      timeout=12,
  )
  if r_fr.status_code == 200:
    for item in r_fr.json():
      s = item.get("symbol", "")
      if s.endswith("USDT"):
        valid_futures_symbols.add(s)
        funding_map[s] = float(item.get("lastFundingRate", 0)) * 100
    print(
        f"✅ Loaded {len(valid_futures_symbols)} Active Futures pairs with"
        " Funding Rates."
    )
except Exception as e:
  print(f"Error fetching premium index: {e}")

# ২. ২৪ ঘণ্টার লাইভ ফিউচার্স টিকার সংগ্রহ
tickers = []
try:
  r_t = requests.get(
      "https://fapi.binance.com/fapi/v1/ticker/24hr", headers=headers, timeout=12
  )
  if r_t.status_code == 200:
    tickers = r_t.json()
    print(f"✅ Loaded {len(tickers)} tickers from Futures API.")
except Exception as e:
  print(f"Error fetching tickers: {e}")


# ৩. লাইভ ওপেন ইন্টারেস্ট (Current Live OI)
def get_current_oi(symbol):
  try:
    url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}"
    res = requests.get(url, headers=headers, timeout=4)
    if res.status_code == 200:
      return float(res.json().get("openInterest", 0))
  except Exception:
    pass
  return 0.0


# ৪. পাম্পের আগের হিস্টোরিক্যাল ওআই এবং হিস্টোরিক্যাল ফান্ডিং রেট (Pre-Pump Metrics)
def get_pre_pump_metrics(symbol):
  pre_oi = 0.0
  pre_funding = 0.0

  # (ক) ২৪ ঘণ্টা আগের হিস্টোরিক্যাল ওপেন ইন্টারেস্ট (Historical OI)
  try:
    oi_url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=1h&limit=24"
    r_oi = requests.get(oi_url, headers=headers, timeout=5)
    if r_oi.status_code == 200:
      oi_data = r_oi.json()
      if isinstance(oi_data, list) and len(oi_data) > 0:
        # ২৪ ঘণ্টা আগের প্রথম রেকর্ড করা ওপেন ইন্টারেস্ট
        pre_oi = float(oi_data[0].get("sumOpenInterest", 0))
  except Exception:
    pass

  # (খ) ঠিক আগের সাইকেলের ফান্ডিং রেট (Pre-Pump Funding Rate)
  try:
    fr_url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=2"
    r_hist_fr = requests.get(fr_url, headers=headers, timeout=5)
    if r_hist_fr.status_code == 200:
      fr_data = r_hist_fr.json()
      if isinstance(fr_data, list) and len(fr_data) > 1:
        # পূর্ববর্তী সাইকেলের রেট
        pre_funding = float(fr_data[0].get("fundingRate", 0)) * 100
      elif isinstance(fr_data, list) and len(fr_data) == 1:
        pre_funding = float(fr_data[0].get("fundingRate", 0)) * 100
  except Exception:
    pass

  return pre_oi, pre_funding


# ৫. উন্নত ফরেনসিক ক্লাসিফিকেশন লজিক (Pre-Pump + Post-Pump Analysis)
def classify_advanced_forensics(chg_pct, cur_fr, pre_fr, oi_surge, vol_usd):
  # পাম্পের আগেও যদি ফান্ডিং নেগেটিভ থাকে এবং ওআই বাড়ে -> কনফার্মড শর্ট স্কুইজ
  if pre_fr <= -0.03 or cur_fr <= -0.05:
    return "🚨 Confirmed Short Squeeze (Forced Liquidations)"
  elif oi_surge >= 50.0 and vol_usd >= 10000000:
    return "💎 Institutional Accumulation (Massive Fresh Inflow)"
  elif oi_surge >= 20.0 and vol_usd >= 3000000:
    return "⚡ Aggressive Momentum (Smart Money Entry)"
  elif oi_surge < 5.0 and chg_pct >= 25.0:
    return "⚠️ Spot/Whale Manipulated (Low OI Participation)"
  else:
    return "📊 Momentum Drift"


# ৬. টোকেন প্রসেসিং ও ক্যালকুলেশন
rows = []
for t in tickers:
  if not isinstance(t, dict):
    continue
  sym = str(t.get("symbol", ""))

  # ভ্যালিড সক্রিয় ফিউচার্স পেয়ার
  if sym in valid_futures_symbols and not sym.startswith("1000"):
    try:
      chg = float(t.get("priceChangePercent", 0))
      vol = float(t.get("quoteVolume", 0))
      price = float(t.get("lastPrice", 0))
      high = float(t.get("highPrice", 0))

      # ১৫%+ গেইন ও ৫০K ভলিউম
      if chg >= 15.0 and vol >= 50000 and price > 0:
        clean_sym = sym.replace("USDT", "")

        # লাইভ ও হিস্টোরিক্যাল ডেটা ফেচ
        cur_funding = funding_map.get(sym, 0.0)
        cur_oi = get_current_oi(sym)
        pre_oi, pre_funding = get_pre_pump_metrics(sym)

        # OI বৃদ্ধির শতকরা হার (OI Surge %)
        if pre_oi > 0:
          oi_surge_pct = round(((cur_oi - pre_oi) / pre_oi) * 100, 2)
        else:
          oi_surge_pct = 0.0

        # উন্নত ফরেনসিক লজিক
        reason = classify_advanced_forensics(
            chg, cur_funding, pre_funding, oi_surge_pct, vol
        )

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
            "OI_Surge_Pct": oi_surge_pct,
            "Pre_Funding_Rate": round(pre_funding, 4),
            "Current_Funding_Rate": round(cur_funding, 4),
            "Forensic_Reason": reason,
            "Outcome_Category": "Analyzing...",
            "Hours_Sustained": 1.0,
            "Status": "ACTIVE_TRACKING",
        })
        print(
            f"🎯 DETECTED: {clean_sym} (+{chg:.2f}%) | OI Surge:"
            f" +{oi_surge_pct}% | Pre-FR: {pre_funding:.4f}% | Cur-FR:"
            f" {cur_funding:.4f}%"
        )
        time.sleep(0.1)
    except Exception:
      continue

print(f"Total target tokens processed: {len(rows)}")

# ৭. ফাইলে নতুন কলামসহ সংরক্ষণ
if rows:
  df_new = pd.DataFrame(rows).sort_values(
      by="Detected_Gain_Pct", ascending=False
  )
  df_new.to_csv(LOG_FILE, index=False)
  print(
      f"✅ SUCCESS: Saved {len(df_new)} coins with Pre vs Post Pump Metrics into"
      f" {LOG_FILE}"
  )
else:
  print("No coins currently met the 15%+ pump criteria.")
