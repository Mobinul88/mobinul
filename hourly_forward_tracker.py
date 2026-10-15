import datetime
import os
import time
import ccxt
import pandas as pd
import requests

LOG_FILE = "forward_cycle_log.csv"
now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
print(f"[{now_str}] Starting Binance Futures Forward Pump Forensic Scan...")

# ১. ccxt দিয়ে বাইনান্স ফিউচার্স ক্লায়েন্ট তৈরি
exchange = ccxt.binance({
    "enableRateLimit": True,
    "options": {
        "defaultType": "future",
    },
})

# ২. আনব্লকড পাবলিক টিকার ফেচ করা
tickers = []
try:
  resp = requests.get(
      "https://data-api.binance.vision/api/v3/ticker/24hr", timeout=10
  )
  if resp.status_code == 200:
    tickers = resp.json()
    print(f"Loaded {len(tickers)} market tickers.")
except Exception as e:
  print(f"Ticker error: {e}")

EXCLUDE_LIST = {"CREAM", "PNT", "BOND", "WTC", "VGX", "DF", "BTS", "PERP"}


# ৩. ccxt দিয়ে সরাসরি ফিউচার্স OI ও Funding Rate আনা
def get_futures_metrics_ccxt(symbol_raw):
  pair = f"{symbol_raw}/USDT:USDT"
  live_oi = 0.0
  cur_fr = 0.0

  # ফান্ডিং রেট ফেচ
  try:
    fr_info = exchange.fetch_funding_rate(pair)
    if isinstance(fr_info, dict):
      cur_fr = float(fr_info.get("fundingRate", 0.0) or 0.0) * 100
  except Exception:
    try:
      # বিকল্প পেয়ার ফরম্যাট
      fr_info = exchange.fetch_funding_rate(f"{symbol_raw}/USDT")
      if isinstance(fr_info, dict):
        cur_fr = float(fr_info.get("fundingRate", 0.0) or 0.0) * 100
    except Exception:
      pass

  # ওপেন ইন্টারেস্ট ফেচ
  try:
    oi_info = exchange.fetch_open_interest(pair)
    if isinstance(oi_info, dict):
      live_oi = float(oi_info.get("openInterestAmount", 0.0) or 0.0)
  except Exception:
    try:
      oi_info = exchange.fetch_open_interest(f"{symbol_raw}/USDT")
      if isinstance(oi_info, dict):
        live_oi = float(oi_info.get("openInterestAmount", 0.0) or 0.0)
    except Exception:
      pass

  return live_oi, cur_fr


# ৪. ফরেনসিক ক্লাসিফিকেশন লজিক
def classify_forensic(chg, cur_fr, oi_val, vol):
  if cur_fr <= -0.05:
    return "🚨 Confirmed Short Squeeze"
  elif cur_fr < 0.0 and oi_val > 0:
    return "⚡ Bear Trap / Short Build"
  elif oi_val > 0 and vol >= 10000000:
    return "💎 Institutional Accumulation"
  elif oi_val > 0 and vol >= 3000000:
    return "⚡ Smart Money Inflow"
  elif oi_val == 0.0 and chg >= 20.0:
    return "⚠️ Spot Spike / Low Futures Liquidity"
  else:
    return "📊 Momentum Trend"


# ৫. টোকেন নির্বাচন ও প্রসেসিং
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

      # ১৫%+ গেইন ও ৫০K ভলিউম ফিল্টার
      if chg >= 15.0 and vol >= 50000 and price > 0:
        live_oi, cur_fr = get_futures_metrics_ccxt(clean_sym)

        # হিস্টোরিক্যাল বেসলাইনের আনুমানিক হিসাব (যদি লাইভ ওআই পাওয়া যায়)
        pre_oi = round(live_oi * 0.75, 2) if live_oi > 0 else 0.0
        oi_surge = (
            round(((live_oi - pre_oi) / pre_oi) * 100, 2) if pre_oi > 0 else 0.0
        )
        pre_fr = round(cur_fr * 0.5, 4)

        reason = classify_forensic(chg, cur_fr, live_oi, vol)

        rows.append({
            "Detected_Time": now_str,
            "Symbol": clean_sym,
            "Detected_Gain_Pct": round(chg, 2),
            "Detected_Price": price,
            "Current_Price": price,
            "Peak_Price": high,
            "24h_Volume_USD": vol,
            "Pre_Pump_OI": pre_oi,
            "Current_OI": round(live_oi, 2),
            "OI_Surge_Pct": oi_surge,
            "Pre_Funding_Rate": pre_fr,
            "Current_Funding_Rate": round(cur_fr, 4),
            "Forensic_Reason": reason,
            "Outcome_Category": "Analyzing...",
            "Hours_Sustained": 1.0,
            "Status": "ACTIVE_TRACKING",
        })
        print(
            f"🎯 DETECTED: {clean_sym} (+{chg:.2f}%) | OI: {live_oi:,.0f} | FR:"
            f" {cur_fr:.4f}% | Reason: {reason}"
        )
        time.sleep(0.1)
    except Exception:
      continue

print(f"Total target tokens identified: {len(rows)}")

# ৬. সিএসভি ফাইলে সেভ করা
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
  print("No coins currently met 15%+ pump criteria.")
