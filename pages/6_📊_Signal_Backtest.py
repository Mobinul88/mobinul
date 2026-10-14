import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Portfolio Signal Audit", layout="wide")

st.title("🏛️ Grade-A+ Institutional Signal Audit & Inspector")
st.markdown("টেলিগ্রাম বটের জেনারেট করা সিগন্যালের সাথে ডেইলি ক্যান্ডেল, RSI, MACD ও ভলিউম কনফার্মেশনের সরাসরি অডিট।")

# সর্বাধিক ট্রেডেড শীর্ষ পেয়ারের তালিকা
TOP_PAIRS = [
    "TRXUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "BNBUSDT", 
    "XRPUSDT", "ADAUSDT", "SUIUSDT", "NEARUSDT", "LINKUSDT", "PEPEUSDT", 
    "WIFUSDT", "FETUSDT", "RENDERUSDT", "BATUSDT", "SUNUSDT", "MEMEUSDT"
]

@st.cache_data(ttl=300)
def fetch_klines_safe(symbol, timeframe="4h", limit=100):
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        clean_sym = symbol.replace("USDT", "") + "/USDT"
        ohlcv = exchange.fetch_ohlcv(clean_sym, timeframe=timeframe, limit=limit)
        if ohlcv and len(ohlcv) >= 25:
            df = pd.DataFrame(ohlcv, columns=["open_time", "open", "high", "low", "close", "volume"])
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            for c in ["open", "high", "low", "close", "volume"]:
                df[c] = df[c].astype(float)
            return df
    except Exception:
        pass
    return None

def calculate_indicators(df):
    df["sma50"] = df["close"].rolling(50, min_periods=10).mean()
    df["sma200"] = df["close"].rolling(200, min_periods=15).mean()
    df["vol_sma"] = df["volume"].rolling(20, min_periods=5).mean()

    # RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df

def scan_symbol(symbol):
    df_4h = fetch_klines_safe(symbol, timeframe="4h", limit=100)
    df_1d = fetch_klines_safe(symbol, timeframe="1d", limit=40)
    
    if df_4h is None:
        return None

    df_4h = calculate_indicators(df_4h)
    
    # ডেইলি ডাটা ও ম্যাক্রো ট্রেন্ড চেক
    daily_status = "N/A"
    if df_1d is not None and len(df_1d) >= 15:
        df_1d = calculate_indicators(df_1d)
        d_close = df_1d.iloc[-1]["close"]
        d_50 = df_1d.iloc[-1]["sma50"]
        d_200 = df_1d.iloc[-1]["sma200"]
        if not pd.isna(d_50) and d_close >= d_50:
            daily_status = "Bullish (> 50 SMA)"
        elif not pd.isna(d_200) and d_close >= d_200:
            daily_status = "Bullish (> 200 SMA)"
        else:
            daily_status = "Bearish (< SMA)"

    # গত ৪ দিনের স্ক্যান (২৪টি ক্যান্ডেল)
    scan_start = max(10, len(df_4h) - 24)

    for i in range(scan_start, len(df_4h)):
        row = df_4h.iloc[i]
        
        for ma_col, ma_name in [("sma50", "4H SMA 50"), ("sma200", "4H SMA 200")]:
            ma_val = row[ma_col]
            if pd.isna(ma_val):
                continue

            dist_pct = ((row["close"] - ma_val) / ma_val) * 100
            # মূল রিটেস্ট ফিল্টার
            retest_hit = (row["low"] <= ma_val * 1.01) or (0 <= dist_pct <= 4.5)

            if retest_hit and row["close"] >= ma_val * 0.99:
                entry = float(row["close"])
                sl = float(ma_val * 0.965)
                risk = max(entry - sl, entry * 0.03)

                tp1 = entry + (risk * 1.5)
                tp2 = entry + (risk * 2.5)

                outcome = "ACTIVE"
                pnl = 0.0

                for j in range(i + 1, len(df_4h)):
                    f_row = df_4h.iloc[j]
                    if float(f_row["low"]) <= sl:
                        outcome = "SL HIT ❌"
                        pnl = ((sl - entry) / entry) * 100
                        break
                    elif float(f_row["high"]) >= tp2:
                        outcome = "TP 2 HIT 🎯"
                        pnl = ((tp2 - entry) / entry) * 100
                        break
                    elif float(f_row["high"]) >= tp1:
                        outcome = "TP 1 HIT 🟢"
                        pnl = ((tp1 - entry) / entry) * 100
                        break

                if outcome == "ACTIVE":
                    pnl = ((float(df_4h.iloc[-1]["close"]) - entry) / entry) * 100

                # কনফার্মেশন চেকিং
                is_green = "Green 🟢" if row["close"] >= row["open"] else "Red 🔴"
                rsi_val = f"{row['rsi']:.1f}" if not pd.isna(row["rsi"]) else "N/A"
                vol_status = "High 🔥" if row["volume"] >= row["vol_sma"] else "Low 💤"

                return {
                    "Symbol": symbol,
                    "First Signal Time": row["open_time"].strftime("%Y-%m-%d %H:%M"),
                    "Daily Macro": daily_status,
                    "Candle": is_green,
                    "RSI": rsi_val,
                    "Volume": vol_status,
                    "Entry": entry,
                    "Stop Loss": sl,
                    "TP1": tp1,
                    "Status": outcome,
                    "PnL %": pnl,
                    "df": df_4h
                }
    return None

with st.spinner("মার্কেট স্ক্যান করে সিগন্যাল ও কনফ্লুয়েন্স রেজাল্ট লোড করা হচ্ছে..."):
    results = []
    for s in TOP_PAIRS:
        res = scan_symbol(s)
        if res:
            results.append(res)

if results:
    res_df = pd.DataFrame(results)

    st.subheader("📌 প্রাতিষ্ঠানিক অডিট সামারি (Overall Portfolio Status)")
    total_signals = len(res_df)
    tp_hits = len(res_df[res_df["Status"].str.contains("TP")])
    sl_hits = len(res_df[res_df["Status"].str.contains("SL")])
    active_trades = len(res_df[res_df["Status"] == "ACTIVE"])
    win_rate = (tp_hits / (tp_hits + sl_hits)) * 100 if (tp_hits + sl_hits) > 0 else 0
    total_pnl = res_df["PnL %"].sum()
    avg_pnl = res_df["PnL %"].mean()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("মোট সিগন্যাল", f"{total_signals} টি")
    m2.metric("সফল (TP Hit)", f"{tp_hits} টি", f"{win_rate:.1f}% Win Rate")
    m3.metric("স্টপ লস (SL Hit)", f"{sl_hits} টি")
    m4.metric("চলমান (Active)", f"{active_trades} টি")
    m5.metric("সর্বমোট PnL", f"{total_pnl:+.2f}%", f"গড়: {avg_pnl:+.2f}%")

    st.markdown("---")

    display_cols = ["Symbol", "First Signal Time", "Daily Macro", "Candle", "RSI", "Volume", "Entry", "Stop Loss", "TP1", "Status", "PnL %"]
    st.dataframe(
        res_df[display_cols].style.format({
            "Entry": "{:.6f}",
            "Stop Loss": "{:.6f}",
            "TP1": "{:.6f}",
            "PnL %": "{:+.2f}%"
        }),
        use_container_width=True
    )

    st.markdown("---")

    st.subheader("🕯️ সিগন্যালের চার্ট ভিজ্যুয়ালাইজার")
    selected_symbol = st.selectbox("চার্ট দেখার জন্য কয়েন নির্বাচন করুন:", res_df["Symbol"].tolist())
    selected_data = next(item for item in results if item["Symbol"] == selected_symbol)
    df_plot = selected_data["df"]

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_plot["open_time"], open=df_plot["open"], high=df_plot["high"], low=df_plot["low"], close=df_plot["close"],
        name="Price"
    ))
    fig.add_trace(go.Scatter(x=df_plot["open_time"], y=df_plot["sma50"], line=dict(color='blue', width=1.5), name="4H SMA 50"))
    if not df_plot["sma200"].isna().all():
        fig.add_trace(go.Scatter(x=df_plot["open_time"], y=df_plot["sma200"], line=dict(color='orange', width=1.5), name="4H SMA 200"))

    s_time = selected_data["First Signal Time"]
    entry_p = selected_data["Entry"]
    fig.add_annotation(
        x=s_time, y=entry_p,
        text=f"BUY ({selected_data['Status']})",
        showarrow=True, arrowhead=2, arrowcolor="green", arrowsize=1.2,
        bgcolor="black", font=dict(color="white", size=10)
    )
    fig.add_shape(type="line", x0=s_time, x1=df_plot["open_time"].iloc[-1], y0=entry_p, y1=entry_p, line=dict(color="cyan", width=1, dash="dot"))
    fig.add_shape(type="line", x0=s_time, x1=df_plot["open_time"].iloc[-1], y0=selected_data["Stop Loss"], y1=selected_data["Stop Loss"], line=dict(color="red", width=1, dash="dash"))
    fig.add_shape(type="line", x0=s_time, x1=df_plot["open_time"].iloc[-1], y0=selected_data["TP1"], y1=selected_data["TP1"], line=dict(color="green", width=1, dash="dash"))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=550,
        template="plotly_dark",
        title=f"{selected_symbol} 4H Structure & Inspection",
        yaxis_title="Price (USDT)"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ স্ক্যান করা পেয়ারগুলোতে গত ৪ দিনে কোনো রিটেস্ট ডাটা পাওয়া যায়নি।")
