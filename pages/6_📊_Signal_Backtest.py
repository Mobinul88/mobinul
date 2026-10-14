import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Institutional Signal Audit", layout="wide")

st.title("🏛️ Grade-A+ Institutional Signal Audit (Dynamic Scoring)")
st.markdown("ডেইলি ট্রেন্ড, ৪-ঘণ্টার বাউন্স, ভলিউম, RSI, MACD এবং ফান্ডিং রেটের মাল্টি-ফ্যাক্টর স্কোরিং মডেল।")

SCAN_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "TRXUSDT", "DOGEUSDT", "BNBUSDT", 
    "XRPUSDT", "ADAUSDT", "AVAXUSDT", "SUIUSDT", "NEARUSDT", "LINKUSDT",
    "APTUSDT", "PEPEUSDT", "WIFUSDT", "FETUSDT", "TAOUSDT", "RENDERUSDT",
    "INJUSDT", "ARBUSDT", "OPUSDT", "TIAUSDT", "SEIUSDT", "SUNUSDT",
    "MEMEUSDT", "BATUSDT", "MAGICUSDT", "LUMIAUSDT", "AAVEUSDT", "GALAUSDT"
]

@st.cache_data(ttl=300)
def fetch_data(symbol):
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        clean_sym = symbol.replace("USDT", "") + "/USDT"
        
        ohlcv_4h = exchange.fetch_ohlcv(clean_sym, timeframe="4h", limit=120)
        ohlcv_1d = exchange.fetch_ohlcv(clean_sym, timeframe="1d", limit=60)
        
        try:
            funding_info = exchange.fetch_funding_rate(clean_sym + ":USDT")
            funding_rate = float(funding_info.get('fundingRate', 0.0))
        except Exception:
            funding_rate = 0.005

        if ohlcv_4h and len(ohlcv_4h) >= 30 and ohlcv_1d and len(ohlcv_1d) >= 15:
            df_4h = pd.DataFrame(ohlcv_4h, columns=["open_time", "open", "high", "low", "close", "volume"])
            df_4h["open_time"] = pd.to_datetime(df_4h["open_time"], unit="ms")
            for c in ["open", "high", "low", "close", "volume"]:
                df_4h[c] = df_4h[c].astype(float)
                
            df_1d = pd.DataFrame(ohlcv_1d, columns=["open_time", "open", "high", "low", "close", "volume"])
            for c in ["open", "high", "low", "close", "volume"]:
                df_1d[c] = df_1d[c].astype(float)
                
            return df_4h, df_1d, funding_rate
    except Exception:
        pass
    return None, None, 0.0

def calculate_technical_indicators(df):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    df["vol_sma"] = df["volume"].rolling(20, min_periods=5).mean()
    return df

def analyze_institutional_setup(df_4h, df_1d, funding_rate, symbol):
    df_1d["sma50"] = df_1d["close"].rolling(50, min_periods=10).mean()
    df_1d["sma200"] = df_1d["close"].rolling(200, min_periods=15).mean()
    
    d_close = df_1d.iloc[-1]["close"]
    d_sma50 = df_1d.iloc[-1]["sma50"]
    d_sma200 = df_1d.iloc[-1]["sma200"]

    daily_score = 0
    if (not pd.isna(d_sma50) and d_close >= d_sma50) or (not pd.isna(d_sma200) and d_close >= d_sma200):
        daily_score = 2
    elif len(df_1d) >= 5 and d_close >= df_1d.iloc[-5]["close"]:
        daily_score = 1

    range_3d = (df_1d["high"].tail(3).max() - df_1d["low"].tail(3).min()) / d_close * 100
    compress_score = 1 if range_3d <= 20.0 else 0
    funding_score = 1 if funding_rate <= 0.02 else 0

    df_4h = calculate_technical_indicators(df_4h)
    df_4h["sma50"] = df_4h["close"].rolling(50, min_periods=15).mean()
    df_4h["sma200"] = df_4h["close"].rolling(200, min_periods=20).mean()

    scan_start = max(15, len(df_4h) - 24)

    for i in range(scan_start, len(df_4h)):
        row = df_4h.iloc[i]
        
        for ma_col, ma_name in [("sma50", "4H SMA 50"), ("sma200", "4H SMA 200")]:
            ma_val = row[ma_col]
            if pd.isna(ma_val):
                continue

            dist_pct = ((row["close"] - ma_val) / ma_val) * 100
            touched_ma = (row["low"] <= ma_val * 1.02) and (-2.0 <= dist_pct <= 5.0)
            is_green = (row["close"] >= row["open"]) and (row["close"] >= ma_val * 0.99)

            if touched_ma and is_green:
                score = daily_score + compress_score + funding_score
                if row["rsi"] >= 38: score += 1
                if row["volume"] >= (row["vol_sma"] * 0.75): score += 1
                if row["macd_hist"] > -0.15: score += 1

                # ৩ বা তার বেশি স্কোর পেলেই ট্রেড কোয়ালিফাই করবে
                if score >= 3:
                    entry = float(row["close"])
                    sl = float(min(row["low"], ma_val * 0.965))
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
                        "Score": f"{score}/7 ⭐",
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

with st.spinner("স্কোরিং মডেল অনুযায়ী প্রাতিষ্ঠানিক সিগন্যাল ফিল্টার করা হচ্ছে..."):
    results = []
    for sym in SCAN_SYMBOLS:
        df_4h, df_1d, fr = fetch_data(sym)
        if df_4h is not None and df_1d is not None:
            sig = analyze_institutional_setup(df_4h, df_1d, fr, sym)
            if sig:
                results.append(sig)

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
    st.info("ℹ️ স্ক্যান করা কোনো কয়েনেই ন্যূনতম ৩/৭ কনফ্লুয়েন্স স্কোর মেলেনি।")
