import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Portfolio Signal Audit", layout="wide")

st.title("📊 4-Day Institutional Portfolio Signal Audit (Balanced)")
st.markdown("ব্যালান্সড গ্রিন ক্যান্ডেল ও রিটেস্ট কনফার্মেশন সহ সিগন্যালের নির্ভুলতা এবং উইন-রেট।")

SCAN_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "TRXUSDT", "DOGEUSDT", "BNBUSDT", 
    "XRPUSDT", "ADAUSDT", "AVAXUSDT", "SUIUSDT", "NEARUSDT", "LINKUSDT",
    "APTUSDT", "PEPEUSDT", "WIFUSDT", "FETUSDT", "TAOUSDT", "RENDERUSDT",
    "INJUSDT", "ARBUSDT", "OPUSDT", "TIAUSDT", "SEIUSDT", "SUNUSDT",
    "MEMEUSDT", "BATUSDT", "MAGICUSDT", "LUMIAUSDT", "AAVEUSDT", "GALAUSDT"
]

@st.cache_data(ttl=300)
def fetch_klines(symbol, timeframe="4h", limit=120):
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
    
    try:
        kucoin = ccxt.kucoin({'enableRateLimit': True})
        clean_sym = symbol.replace("USDT", "") + "/USDT"
        ohlcv = kucoin.fetch_ohlcv(clean_sym, timeframe=timeframe, limit=limit)
        if ohlcv and len(ohlcv) >= 30:
            df = pd.DataFrame(ohlcv, columns=["open_time", "open", "high", "low", "close", "volume"])
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            for c in ["open", "high", "low", "close", "volume"]:
                df[c] = df[c].astype(float)
            return df
    except Exception:
        pass
    return None

def analyze_coin_first_signal(df, symbol):
    df["sma50"] = df["close"].rolling(50, min_periods=20).mean()
    df["sma200"] = df["close"].rolling(200, min_periods=50).mean()

    scan_start = max(20, len(df) - 24)

    for i in range(scan_start, len(df)):
        row = df.iloc[i]
        
        for ma_col, ma_name in [("sma50", "50 SMA"), ("sma200", "200 SMA")]:
            ma_val = row[ma_col]
            if pd.isna(ma_val):
                continue

            # ১. মুভিং এভারেজ টাচ অথবা ৩.৫% সাপোর্ট জোন
            dist_pct = ((row["close"] - ma_val) / ma_val) * 100
            touched_ma = (row["low"] <= ma_val * 1.01) and (-1.0 <= dist_pct <= 3.5)
            
            # ২. মিনিমাম বাউন্স কনফার্মেশন: ক্যান্ডেল গ্রিন ও ক্লোজ এসএমএ-র ওপরে
            is_green_candle = (row["close"] >= row["open"]) and (row["close"] >= ma_val)

            if touched_ma and is_green_candle:
                entry = float(row["close"])
                sl = float(min(row["low"], ma_val * 0.97))
                risk = max(entry - sl, entry * 0.025)

                tp1 = entry + (risk * 1.5)
                tp2 = entry + (risk * 2.5)

                outcome = "ACTIVE"
                pnl = 0.0

                for j in range(i + 1, len(df)):
                    future_row = df.iloc[j]
                    f_high = float(future_row["high"])
                    f_low = float(future_row["low"])

                    if f_low <= sl:
                        outcome = "SL HIT ❌"
                        pnl = ((sl - entry) / entry) * 100
                        break
                    elif f_high >= tp2:
                        outcome = "TP 2 HIT 🎯"
                        pnl = ((tp2 - entry) / entry) * 100
                        break
                    elif f_high >= tp1:
                        outcome = "TP 1 HIT 🟢"
                        pnl = ((tp1 - entry) / entry) * 100
                        break

                if outcome == "ACTIVE":
                    pnl = ((float(df.iloc[-1]["close"]) - entry) / entry) * 100

                return {
                    "Symbol": symbol,
                    "First Signal Time": row["open_time"].strftime("%Y-%m-%d %H:%M"),
                    "MA Setup": ma_name,
                    "Entry": entry,
                    "Stop Loss": sl,
                    "TP1": tp1,
                    "TP2": tp2,
                    "Status": outcome,
                    "PnL %": pnl,
                    "df": df,
                    "signal_idx": i
                }
    return None

with st.spinner("ব্যালান্সড ফিল্টারে সিগন্যালগুলো প্রসেস করা হচ্ছে..."):
    results = []
    for sym in SCAN_SYMBOLS:
        df_kline = fetch_klines(sym)
        if df_kline is not None:
            sig = analyze_coin_first_signal(df_kline, sym)
            if sig:
                results.append(sig)

if results:
    res_df = pd.DataFrame(results)

    st.subheader("📌 ব্যালান্সড সিগন্যাল সামারি (Verified Setups)")
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

    display_cols = ["Symbol", "First Signal Time", "MA Setup", "Entry", "Stop Loss", "TP1", "TP2", "Status", "PnL %"]
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
    fig.add_trace(go.Scatter(x=df_plot["open_time"], y=df_plot["sma50"], line=dict(color='blue', width=1.5), name="SMA 50"))
    if not df_plot["sma200"].isna().all():
        fig.add_trace(go.Scatter(x=df_plot["open_time"], y=df_plot["sma200"], line=dict(color='orange', width=1.5), name="SMA 200"))

    s_time = selected_data["First Signal Time"]
    entry_p = selected_data["Entry"]
    fig.add_annotation(
        x=s_time, y=entry_p,
        text=f"ENTRY ({selected_data['Status']})",
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
        title=f"{selected_symbol} 4H Structure",
        yaxis_title="Price (USDT)"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ গত ৪ দিনে স্ক্যান করা কয়েনগুলোতে কোনো ভ্যালিড গ্রিন বাউন্স তৈরি হয়নি।")
