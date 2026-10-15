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
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

# ১. শুধুমাত্র সক্রিয় ফিউচার্স কন্ট্রাক্ট যাচাই (ডিলিস্টেড কয়েন বাদ দেওয়া)
active_futures_symbols = set()
try:
  info_res = requests.get(
      "https://fapi.binance.com/fapi/v1/exchangeInfo",
      headers=headers,
      timeout=15,
  )
  if info_res.status_code == 200:
    for s in info_res.json().get("symbols", []):
      if (
          s.get("status") == "TRADING"
          and s.get("contractType") == "PERPETUAL"
          and s.get("quoteAsset") == "USDT"
      ):
        active_futures_symbols.add(s.get("symbol"))
    print(
        f"✅ Loaded {len(active_futures_symbols)} ACTIVE Binance Futures pairs."
    )
except Exception as e:
  print(f"ExchangeInfo Error: {e}")

# ২. লাইভ ফিউচার্স টিকার সংগ্রহ
tickers = []
try:
  r = requests.get(
      "https://fapi.binance.com/fapi/v1/ticker/24hr", headers=headers, timeout=12
  )
  if r.status_code == 200:
    tickers = r.json()
except Exception as e:
  print(f"Futures Tickers Error: {e}")

# ৩. লাইভ Funding Rate ম্যাপ তৈরি
funding_map = {}
try:
  fr_res = requests.get(
      "https://fapi.binance.com/fapi/v1/premiumIndex",
      headers=headers,
      timeout=12,
  )
  if fr_res.status_code == 200:
    for item in fr_res.json():
      sym = item.get("symbol")
      rate = float(item.get("lastFundingRate", 0)) * 100
      funding_map[sym] = rate
except Exception as e:
  print(f"PremiumIndex Error: {e}")


# ৪. ওপেন ইন্টারেস্ট (OI) সংগ্রহের ফাংশন
def get_live_oi(symbol_pair):
  try:
    url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol_pair}"
    r = requests.get(url, headers=headers, timeout=4)
    if r.status_code == 200:
      return float(r.json().get("openInterest", 0))
  except Exception:
    pass
  return 0.0


# ৫. ফরেনসিক লজিক ক্লাসিফিকেশন
def classify_forensic_reason(chg_pct, funding_rate, vol_usd):
  if funding_rate <= -0.05:
    return "🚨 Short Squeeze (Heavy Neg Funding)"
  elif funding_rate < 0.0:
    return "⚡ Bear Trap / Mild Short Squeeze"
  elif chg_pct >= 35.0 and vol_usd >= 15000000:
    return "💎 Institutional Mega Trend (Heavy Vol)"
  elif vol_usd >= 3000000:
    return "⚡ Aggressive Momentum Accumulation"
  else:
    return "⚠️ Low-Float / Whale Spike"


# ৬. টোকেন ফিল্টারিং
rows = []
for t in tickers:
  if not isinstance(t, dict):
    continue
  sym = str(t.get("symbol", ""))

  # নিশ্চিত করা যে টোকেনটি বর্তমানে সক্রিয়ভাবে ফিউচার্সে ট্রেড হচ্ছে
  if sym in active_futures_symbols and not sym.startswith("1000"):
    try:
      chg = float(t.get("priceChangePercent", 0))
      vol = float(t.get("quoteVolume", 0))
      price = float(t.get("lastPrice", 0))
      high = float(t.get("highPrice", 0))

      # ১৫%+ গেইন ও অন্তত ৫০,০০০ ভলিউম
      if chg >= 15.0 and vol >= 50000 and price > 0:
        clean_sym = sym.replace("USDT", "")
        funding_pct = funding_map.get(sym, 0.0)
        live_oi = get_live_oi(sym)
        reason = classify_forensic_reason(chg, funding_pct, vol)

        rows.append({
            "Detected_Time": now_str,
            "Symbol": clean_sym,
            "Detected_Gain_Pct": round(chg, 2),
            "Detected_Price": price,
            "Current_Price": price,
            "Peak_Price": high,
            "24h_Volume_USD": vol,
            "Funding_Rate_Pct": round(funding_pct, 4),
            "Open_Interest": live_oi,
            "Forensic_Reason": reason,
            "Outcome_Category": "Analyzing...",
            "Hours_Sustained": 1.0,
            "Status": "ACTIVE_TRACKING",
        })
        print(
            f"🎯 DETECTED: {clean_sym} (+{chg:.2f}%) | FR: {funding_pct:.4f}% |"
            f" OI: {live_oi:,.0f} | Reason: {reason}"
        )
        time.sleep(0.1)
    except Exception:
      continue

print(f"Total verified active futures tokens: {len(rows)}")

# ৭. ডেটা ফাইলে সংরক্ষণ
if rows:
  df_new = pd.DataFrame(rows).sort_values(
      by="Detected_Gain_Pct", ascending=False
  )

  # পুরনো ডিলিস্টেড টোকেন মুছে সম্পূর্ণ ফ্রেশ অ্যাক্টিভ ডেটা সংরক্ষণ
  df_new.to_csv(LOG_FILE, index=False)
  print(
      f"✅ SUCCESS: Wrote {len(df_new)} pure active futures coins into"
      f" {LOG_FILE}"
  )
else:
  print("No active futures coins met the pump criteria right now.")
