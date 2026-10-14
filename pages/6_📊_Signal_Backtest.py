import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Institutional Signal Audit", layout="wide")

st.title("🏛️ Grade-A+ Institutional Signal Audit (Full Confluence)")
st.markdown("ডেইলি ম্যাক্রো ট্রেন্ড, ৩D/৭D কম্প্রেশন, RSI, MACD, ভলিউম এবং ফান্ডিং রেট সমন্বিত প্রাতিষ্ঠানিক অডিট।")

SCAN_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "TRXUSDT", "DOGEUSDT", "BNBUSDT", 
    "XRPUSDT", "ADAUSDT", "AVAXUSDT", "SUIUSDT", "NEARUSDT", "LINKUSDT",
    "APTUSDT", "PEPEUSDT", "WIFUSDT", "FETUSDT", "TAOUSDT", "RENDERUSDT",
    "INJUSDT", "ARBUSDT", "OPUSDT", "TIAUSDT", "SEIUSDT", "SUNUSDT",
    "MEMEUSDT", "BATUSDT", "MAGICUSDT", "LUMIAUSDT", "AAVEUSDT", "GALAUSDT"
]

@st.cache_data(ttl=600)
def fetch_data(symbol):
    """বাইনান্স / অল্টারনেটিভ এক্সচেঞ্জ থেকে ৪এইচ ও ডেইলি ডেটা ফেচিং"""
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        clean_sym = symbol.replace("USDT", "") + "/USDT"
        
        # ৪ ঘণ্টার ক্যান্ডেল
        ohlcv_4h = exchange.fetch_ohlcv(clean_sym, timeframe="4h", limit=120)
        # ডেইলি ক্যান্ডেল
        ohlcv_1d = exchange.fetch_ohlcv(clean_sym, timeframe="1d", limit=60)
        
        # ফান্ডিং রেট চেক
        try:
            funding_info = exchange.fetch_funding_rate(clean_sym + ":USDT")
            funding_rate = float(funding_info.get('fundingRate', 0.0))
        except Exception:
            funding_rate = 0.005 # ডিফল্ট নিরাপদ মান

        if ohlcv_4h and len(ohlcv_4h) >= 30 and ohlcv_1d and len(ohlcv_1d) >= 30:
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
    """RSI এবং MACD হিসাব"""
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

    # ভলিউম মুভিং এভারেজ
    df["vol_sma"] = df["volume"].rolling(20, min_periods=5).mean()
    return df

def analyze_institutional_setup(df_4h, df_1d, funding_rate, symbol):
    # ডেইলি ইন্ডিকেটর
    df_1d["sma50"] = df_1d["close"].rolling(50, min_periods=20).mean()
    df_1d["sma200"] = df_1d["close"].rolling(200, min_periods=30).mean()
    
    latest_daily = df_1d.iloc[-1]
    d_close = latest_daily["close"]
    d_sma50 = latest_daily["sma50"]
    d_sma200 = latest_daily["sma200"]

    # শর্ত ১: Daily Macro Filter (ডেইলি ক্লোজিং SMA 50 বা SMA 200 এর উপরে থাকতে হবে)
    daily_bullish = False
    if not pd.isna(d_sma50) and d_close >= d_sma50:
        daily_bullish = True
    elif not pd.isna(d_sma200) and d_close >= d_sma200:
        daily_bullish = True

    if not daily_bullish:
        return None

    # শর্ত ২: ৩ দিন এবং ৭ দিনের কম্প্রেশন/অ্যাকুমুলেশন চেক
    range_3d = (df_1d["high"].tail(3).max() - df_1d["low"].tail(3).min()) / d_close * 100
    range_7d = (df_1d["high"].tail(7).max() - df_1d["low"].tail(7).min()) / d_close * 100
    is_accumulating = (range_3d <= 14.0) or (range_7d <= 22.0)

    # শর্ত ৩: ফান্ডিং রেট ফিল্টার (রিটেইল অতিরিক্ত লং থাকলে বাদ)
    if funding_rate > 0.02:
        return None

    # ৪-ঘণ্টার টেকনিক্যাল
    df_4h = calculate_technical_indicators(df_4h)
    df_4h["sma50"] = df_4h["close"].rolling(50, min_periods=20).mean()
    df_4h["sma200"] = df_4h["close"].rolling(200, min_periods=30).mean()

    # গত ৪ দিনের স্ক্যান (২৪টি ক্যান্ডেল)
    scan_start = max(20, len(df_4h) - 24)

    for i in range(scan_start, len(df_4h)):
        row = df_4h.iloc[i]
        
        for ma_col, ma_name in [("sma50", "4H SMA 50"), ("sma200", "4H SMA 200")]:
            ma_val = row[ma_col]
            if pd.isna(ma_val):
                continue

            # শর্ত ৪: রিটেস্ট ও বাউন্স
            touched_ma = (row["low"] <= ma_val * 1.01) and (row["close"] >= ma_val)
            is_green = (row["close"] >= row["open"])
            
            # শর্ত ৫: ভলিউম এবং মোমেন্টাম কনফার্মেশন (RSI > 45, MACD হিস্টোগ্রাম বেটার)
            good_rsi = row["rsi"] >= 43
            good_volume = row["volume"] >= (row["vol_sma"] * 0.95)
            bullish_macd = row["macd_hist"] > -0.05

            if touched_ma and is_green and good_rsi and (good_volume or is_accumulating) and bullish_macd:
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
                    "Daily Macro": "Bullish (> SMA)",
                    "3D/7D Status": "Accumulation" if is_accumulating else "Standard",
                    "Entry": entry,
                    "Stop Loss": sl,
                    "TP1": tp1,
                    "TP2": tp2,
                    "Status": outcome,
                    "PnL %": pnl,
                    "df": df_4h
                }
    return None

# এক্সিকিউশন
with st.spinner("প্রাতিষ্ঠানিক সবকটি ফিল্টার মিলিয়ে নিখুঁত সিগন্যাল অডিট করা হচ্ছে..."):
    results = []
    for sym in SCAN_SYMBOLS:
        df_4h, df_1d, fr = fetch_data(sym)
        if df_4h is not None and df_1d is not None:
            sig = analyze_institutional_setup(df_4h, df_1d, fr, sym)
            if sig:
                results.append(sig)

if results:
    res_df = pd.DataFrame(results)

    st.subheader("📌 প্রাতিষ্ঠানিক অডিট সামারি (Institutional Confluence Results)")
    total_signals = len(res_df)
    tp_hits = len(res_df[res_df["Status"].str.contains("TP")])
    sl_hits = len(res_df[res_df["Status"].str.contains("SL")])
    active_trades = len(res_df[res_df["Status"] == "ACTIVE"])
    win_rate = (tp_hits / (tp_hits + sl_hits)) * 100 if (tp_hits + sl_hits) > 0 else 0
    total_pnl = res_df["PnL %"].sum()
    avg_pnl = res_df["PnL %"].mean()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("কোয়ালিটি সিগন্যাল", f"{total_signals} টি")
    m2.metric("সফল (TP Hit)", f"{tp_hits} টি", f"{win_rate:.1f}% Win Rate")
    m3.metric("স্টপ লস (SL Hit)", f"{sl_hits} টি")
    m4.metric("চলমান (Active)", f"{active_trades} টি")
    m5.metric("সর্বমোট PnL", f"{total_pnl:+.2f}%", f"গড়: {avg_pnl:+.2f}%")

    st.markdown("---")

    display_cols = ["Symbol", "First Signal Time", "Daily Macro", "3D/7D Status", "Entry", "Stop Loss", "TP1", "TP2", "Status", "PnL %"]
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
        title=f"{selected_symbol} 4H Institutional Execution",
        yaxis_title="Price (USDT)"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ এই সম্পূর্ণ কনফ্লুয়েন্স নিয়মে গত ৪ দিনে কোনো কয়েন কোয়ালিফাই করেনি। অর্থাৎ মার্কেট ঝুঁকিপূর্ণ থাকা অবস্থায় বট কোনো ভুল ট্রেড নেয়নি।")
