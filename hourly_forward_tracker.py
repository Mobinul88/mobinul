import requests
import pandas as pd
import datetime
import os
import time

LOG_FILE = "forward_cycle_log.csv"
CONFIG_FILE = "engine_config.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(HEADERS)

def get_current_cycle_week(start_date_str):
    """শুরুর তারিখ থেকে বর্তমান সপ্তাহ (Week 1 থেকে Week 8) বের করা"""
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    today = datetime.date.today()
    days_passed = max(0, (today - start_date).days)
    week_no = (days_passed // 7) + 1
    return min(week_no, 8), days_passed

def init_engine():
    """ইঞ্জিনের স্টার্টিং ডেট কনফিগার করা"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    if not os.path.exists(CONFIG_FILE):
        df_cfg = pd.DataFrame([{"start_date": today_str, "total_target_days": 60}])
        df_cfg.to_json(CONFIG_FILE, orient="records")
        return today_str
    else:
        df_cfg = pd.read_json(CONFIG_FILE)
        return df_cfg.iloc[0]["start_date"]

def run_hourly_scan():
    start_date = init_engine()
    current_week, days_elapsed = get_current_cycle_week(start_date)

    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            return
        tickers = r.json()
    except Exception:
        return

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.date.today().strftime("%Y-%m-%d")

    price_map = {}
    new_candidates = []

    for t in tickers:
        sym = t.get("symbol", "")
        if not sym.endswith("USDT") or sym.startswith("1000"):
            continue

        clean_sym = sym.replace("USDT", "")
        last_price = float(t.get("lastPrice", 0))
        pct_change = float(t.get("priceChangePercent", 0))
        vol_usd = float(t.get("quoteVolume", 0))
        price_map[clean_sym] = last_price

        # পাম্প ফিল্টার: ২০%+ গেইন ও কমপক্ষে ৩ মিলিয়ন ডলার ভলিউম
        if pct_change >= 20.0 and vol_usd >= 3000000:
            new_candidates.append({
                "Timestamp": now_str,
                "Date": today_date,
                "Week_Batch": f"Week {current_week}",
                "Days_Elapsed": days_elapsed,
                "Symbol": clean_sym,
                "Trigger_Price": last_price,
                "Trigger_Gain_24h": pct_change,
                "Trigger_Volume_USD": vol_usd,
                "Peak_Price": last_price,
                "Current_Price": last_price,
                "Hours_Tracked": 0,
                "Dump_Detected": False,
                "Hours_To_Dump": None,
                "Status": "Tracking..."
            })

    if os.path.exists(LOG_FILE):
        df_log = pd.read_csv(LOG_FILE)
    else:
        df_log = pd.DataFrame()

    # নতুন পেয়ার যুক্ত করা (ডুপ্লিকেট এড়ানো)
    if not df_log.empty:
        active_tracked = df_log[df_log["Status"] == "Tracking..."]["Symbol"].tolist()
        to_add = [c for c in new_candidates if c["Symbol"] not in active_tracked]
        if to_add:
            df_log = pd.concat([df_log, pd.DataFrame(to_add)], ignore_index=True)
    else:
        if new_candidates:
            df_log = pd.DataFrame(new_candidates)

    # চলমান পেয়ারগুলোর ট্র্যাকিং আপডেট
    if not df_log.empty:
        for idx, row in df_log.iterrows():
            if row["Status"] != "Tracking...":
                continue

            sym = row["Symbol"]
            curr_p = price_map.get(sym)
            if not curr_p:
                continue

            trigger_p = float(row["Trigger_Price"])
            peak_p = max(float(row["Peak_Price"]), curr_p)
            df_log.at[idx, "Peak_Price"] = peak_p
            df_log.at[idx, "Current_Price"] = curr_p

            hours_count = int(row["Hours_Tracked"]) + 1
            df_log.at[idx, "Hours_Tracked"] = hours_count

            # ডাম্প ডিটেকশন (পিক থেকে ৩০% নিচে নামলে)
            drawdown = ((peak_p - curr_p) / peak_p) * 100
            if drawdown >= 30.0 and pd.isna(row["Hours_To_Dump"]):
                df_log.at[idx, "Dump_Detected"] = True
                df_log.at[idx, "Hours_To_Dump"] = hours_count

            # ৭২ ঘণ্টা ট্র্যাকিং সম্পন্ন হলে ফাইনাল ক্লাসিফিকেশন
            if hours_count >= 72:
                gain_from_start = ((curr_p - trigger_p) / trigger_p) * 100
                if gain_from_start >= 15.0 and not df_log.at[idx, "Dump_Detected"]:
                    df_log.at[idx, "Status"] = "🔥 Multi-Day Super-Trend"
                elif df_log.at[idx, "Dump_Detected"] or curr_p < trigger_p:
                    df_log.at[idx, "Status"] = "⚠️ Flash Pump & Dump Trap"
                else:
                    df_log.at[idx, "Status"] = "🟡 Consolidation Range"

        df_log.to_csv(LOG_FILE, index=False)
        print(f"[{now_str}] Week {current_week} Scan Executed. Total Logs: {len(df_log)}")

if __name__ == "__main__":
    run_hourly_scan()
