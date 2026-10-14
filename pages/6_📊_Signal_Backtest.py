import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Institutional Signal Audit", layout="wide")

st.title("🏛️ Grade-A+ Institutional Signal Audit & Inspector")
st.markdown("ডেইলি ট্রেন্ড, ৪-ঘণ্টার বাউন্স, ভলিউম, RSI এবং ডাইনামিক কনফ্লুয়েন্স অডিট।")

# সর্বাধিক সক্রিয় শীর্ষ পেয়ার
TOP_PAIRS = [
    "TRXUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "BNBUSDT", 
    "XRPUSDT", "ADAUSDT", "SUIUSDT", "NEARUSDT", "LINKUSDT", "PEPEUSDT", 
    "WIFUSDT", "FETUSDT", "RENDERUSDT", "BATUSDT", "SUNUSDT"
]

@st.cache_data(ttl=300)
def fetch_klines_safe(symbol, timeframe="4h", limit=100):
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        clean_sym = symbol.replace("USDT", "") + "/USDT"
        ohlcv = exchange.fetch_ohlcv(clean_sym, timeframe=timeframe, limit=limit)
        if ohlcv and len(ohlcv) >= 30:
            df = pd.DataFrame(ohlcv, columns=["open_time", "open", "high", "low", "close", "volume"])
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            for c in ["open", "high", "low", "close", "volume"]:
                df[c] = df[c].astype(float)
            return df
    except Exception:
        pass
    return None

def calculate_indicators(df):
    df["sma50"] = df["close"].rolling(50, min_periods=15).mean()
    df["sma200"] = df["close"].rolling(200, min_periods=25).mean()
    df["vol_sma"] = df["volume"].rolling(20, min_periods=5).mean()

    # RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    return df

def scan_symbol(symbol):
    df_4h = fetch_klines_safe(symbol, timeframe="4h", limit=100)
    df_1d = fetch_klines_safe(symbol, timeframe="1d", limit=40)
    
    if df_4h is None or df_1d is None:
        return None

    df_4h = calculate_indicators(df_4h)
    df_1d = calculate_indicators(df_1d)

    latest_d = df_1d.iloc[-1]
    d_close = latest_d["close"]
    d_sma50 = latest_d["sma50"]
    d_sma200 = latest_d["sma200"]

    # Daily Confluence Score
    daily_score = 0
    if not pd.isna(d_sma50) and d_close >= d_sma50:
        daily_score += 2
    elif not pd.isna(d_sma200) and d_close >= d_sma200:
        daily_score += 1.5
    elif len(df_1d) >= 4 and d_close >= df_1d.iloc[-4]["close"]:
        daily_score += 1

    # গত ৪ দিন = ২৪টি 4-ঘণ্টার ক্যান্ডেল
    scan_start = max(15, len(df_4h) - 24)

    for i in range(scan_start, len(df_4h)):
        row = df_4h.iloc[i]
        
        for ma_col, ma_name in [("sma50", "4H SMA 50"), ("sma200", "4H SMA 200")]:
            ma_val = row[ma_col]
            if pd.isna(ma_val):
                continue

            # বাউন্স টেস্ট: লো টাচ করেছে অথবা ৩% এর মধ্যে সাপোর্ট
            dist_pct = ((row["close"] - ma_val) / ma_val) * 100
            touched = (row["low"] <= ma_val * 1.015) and (-2.0 <= dist_pct <= 4.0)
            is_green = (row["close"] >= row["open"])

            if touched and is_green:
                # স্কোর গণনা
                score = daily_score
                if row["rsi"] >= 40: score += 1
                if row["volume"] >= row["vol_sma"] * 0.8: score += 1

                # ন্যূনতম ২.৫ বা ৩ স্কোর পেলেই ট্রিগার
                if score >= 2.5:
                    entry = float(row["close"])
                    sl = float(min(row["low"], ma_val * 0.97))
                    risk = max(entry - sl, entry * 0.025)

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

                    return {
                        "Symbol": symbol,
                        "First Signal Time": row["open_time"].strftime("%Y-%m-%d %H:%M"),
                        "Score": f"{score:.1f}/5.0 ⭐",
                        "MA Setup": ma_name,
                        "Entry": entry,
                        "Stop Loss": sl,
                        "TP1": tp1,
                        "TP2": tp2,
                        "Status": outcome,
                        "PnL %": pnl,
                        "df": df_4h
                    }
    return None

# রান স্ক্যান
with st.spinner("মার্কেট স্ক্যান করে কনফ্লুয়েন্স সিগন্যাল খোঁজা হচ্ছে..."):
    results = []
    for s in TOP_PAIRS:
        res = scan_symbol(s)
        if res:
            results.append(res)

if results:
    res_df = pd.DataFrame(results)

    st.subheader("📌 প্রাতিষ্ঠানিক অডিট সামারি (Dynamic Confluence Results)")
    total_signals = len(res_df)
    tp_hits = len(res_df[res_df["Status"].str.contains("TP")])
    sl_hits = len(res_df[res_df["Status"].str.contains("SL")])
    active_trades = len(res_df[res_df["Status"] == "ACTIVE"])
    win_rate = (tp_hits / (tp_hits + sl_hits)) * 100 if (tp_hits + sl_hits) > 0 else 0
    total_pnl = res_df["PnL %"].sum()
    avg_pnl = res_df["PnL %"].mean()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("নির্বাচিত সিগন্যাল", f"{total_signals} টি")
    m2.metric("সফল (TP Hit)", f"{tp_hits} টি", f"{win_rate:.1f}% Win Rate")
    m3.metric("স্টপ লস (SL Hit)", f"{sl_hits} টি")
    m4.metric("চলমান (Active)", f"{active_trades} টি")
    m5.metric("সর্বমোট PnL", f"{total_pnl:+.2f}%", f"গড়: {avg_pnl:+.2f}%")

    st.markdown("---")

    display_cols = ["Symbol", "First Signal Time", "Score", "MA Setup", "Entry", "Stop Loss", "TP1", "TP2", "Status", "PnL %"]
    st.dataframe(
        res_df[display_cols].style.format({
            "Entry": "{:.6f}",
            "Stop Loss": "{:.6f}",
            "TP1": "{:.6f}",
            "TP2": "{:.6f}",
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
        text=f"BUY ({selected_data['Score']})",
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
        title=f"{selected_symbol} 4H Institutional Execution",
        yaxis_title="Price (USDT)"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ গত ৪ দিনে স্ক্যান করা শীর্ষ কয়েনগুলোতে ন্যূনতম কনফ্লুয়েন্স বাউন্স তৈরি হয়নি।")
