import requests
import pandas as pd
import datetime
import os
import time

# ========================================================
# 🤖 TELEGRAM BOT CREDENTIALS
# ========================================================
# আপনার টেলিগ্রাম বট টোকেন এবং চ্যাট আইডি দিন (অথবা এনভায়রনমেন্ট ভ্যারিয়েবল ব্যবহার করুন)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

LOG_FILE = "telegram_signals_log.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(HEADERS)

def send_telegram_alert(message):
    """টেলিগ্রামে সিগন্যাল মেসেজ পাঠানোর ফাংশন"""
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not TELEGRAM_BOT_TOKEN:
        print("⚠️ Telegram credentials not configured. Message preview:")
        print(message)
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = session.post(url, json=payload, timeout=8)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram Send Error: {e}")
        return False

def log_signal_to_csv(symbol, signal_type, entry_price, tp_price, sl_price, volume_usd):
    """ড্যাশবোর্ডের জন্য প্রতিটি সিগন্যাল লাইভ ফাইলে রেকর্ড করা"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_sym = symbol.replace("USDT", "").upper()
    
    new_entry = {
        "Signal_Time": now_str,
        "Symbol": clean_sym,
        "Signal_Type": signal_type.upper(),
        "Entry_Price": float(entry_price),
        "Take_Profit": float(tp_price),
        "Stop_Loss": float(sl_price),
        "Inflow_Volume_USD": float(volume_usd),
        "Status": "OPEN"
    }
    
    df_new = pd.DataFrame([new_entry])
    if os.path.exists(LOG_FILE):
        try:
            df_old = pd.read_csv(LOG_FILE)
            df_updated = pd.concat([df_old, df_new], ignore_index=True)
            df_updated.to_csv(LOG_FILE, index=False)
        except Exception:
            df_new.to_csv(LOG_FILE, index=False)
    else:
        df_new.to_csv(LOG_FILE, index=False)
    print(f"✅ Logged to {LOG_FILE}: {clean_sym} ({signal_type}) Entry: {entry_price}")

def scan_binance_market():
    """বাইনান্স ফিউচার্স থেকে সিগন্যাল খুঁজে বের করা ও ফায়ার করা"""
    print(f"[{datetime.datetime.now()}] Scanning Binance Futures for High-Probability Setups...")
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        res = session.get(url, timeout=10).json()
        if not isinstance(res, list):
            return
    except Exception as e:
        print(f"Market fetch error: {e}")
        return

    # ইতিমধ্যে যে কয়েনগুলোতে আজকে সিগন্যাল গেছে সেগুলোর তালিকা যাতে একই কয়েনে বারবার সিগন্যাল না যায়
    logged_today = []
    if os.path.exists(LOG_FILE):
        try:
            df_log = pd.read_csv(LOG_FILE)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            logged_today = df_log[df_log["Signal_Time"].str.contains(today_str, na=False)]["Symbol"].tolist()
        except Exception:
            pass

    for item in res:
        symbol = item.get("symbol", "")
        if not symbol.endswith("USDT") or symbol.startswith("1000"):
            continue

        clean_sym = symbol.replace("USDT", "")
        if clean_sym in logged_today:
            continue

        price = float(item.get("lastPrice", 0))
        pct_change = float(item.get("priceChangePercent", 0))
        vol_usd = float(item.get("quoteVolume", 0))

        # সিগন্যাল অ্যালগরিদম ক্রাইটেরিয়া:
        # বুলিশ ব্রেকআউট (LONG): ভলিউম >= $15M এবং ২৪ ঘণ্টায় ৭% থেকে ১৮% এর মধ্যে মোমেন্টাম শুরু
        if pct_change >= 7.0 and vol_usd >= 15000000 and price > 0:
            signal_type = "LONG"
            entry_price = price
            tp_price = round(entry_price * 1.08, 6)   # +8% Target (TP)
            sl_price = round(entry_price * 0.96, 6)   # -4% Stop Loss (1:2 Risk/Reward)

            msg = (
                f"🚨 <b>MOBINUL QUANT SIGNAL ALERT</b> 🚨\n\n"
                f"💎 <b>Coin:</b> #{clean_sym}USDT\n"
                f"⚡ <b>Action:</b> {signal_type} 🟢\n"
                f"🎯 <b>Entry Price:</b> ${entry_price}\n"
                f"🏆 <b>Take Profit (TP):</b> ${tp_price} (+8.0%)\n"
                f"🛑 <b>Stop Loss (SL):</b> ${sl_price} (-4.0%)\n"
                f"📊 <b>24h Inflow Vol:</b> ${round(vol_usd/1e6, 2)}M\n\n"
                f"🔥 <a href='https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={clean_sym}USDT'>View Liquidity Heatmap</a> | "
                f"<a href='https://arkm.com/explorer/token/{clean_sym.lower()}'>Arkham Intel</a>"
            )

            # ১. টেলিগ্রামে পাঠানো
            send_telegram_alert(msg)

            # ২. ফাইলে স্বয়ংক্রিয়ভাবে লগ করা
            log_signal_to_csv(clean_sym, signal_type, entry_price, tp_price, sl_price, vol_usd)
            logged_today.append(clean_sym)
            time.sleep(1)

if __name__ == "__main__":
    scan_binance_market()
