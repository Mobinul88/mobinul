import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Institutional Swing Backtest", layout="wide")

st.title("📊 4-Day Institutional Signal Performance & Visualizer")
st.markdown("গত ৪ দিনে এপিআইয়ের তৈরি করা সিগন্যালগুলোর সিমুলেশন এবং লাইভ রেজাল্ট যাচাইকরণ।")

@st.cache_data(ttl=300)
def get_historical_klines(symbol, interval="4h", limit=120):
    """ফিউচার্স এবং স্পট উভয় এপিআই থেকে ডেটা ফেচ করার নিরাপদ ফাংশন"""
    endpoints = [
        f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}",
        f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=8).json()
            if isinstance(res, list) and len(res) >= 30:
                df = pd.DataFrame(res, columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_base_vol", "taker_quote_vol", "ignore"
                ])
                for col in ["open", "high", "low", "close", "volume"]:
                    df[col] = df[col].astype(float)
                df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
                return df
        except Exception:
            continue
    return None

def simulate_strategy(df):
    """মুভিং এভারেজ রিটেস্ট সিমুলেশন"""
    df["sma50"] = df["close"].rolling(50, min_periods=20).mean()
    df["sma200"] = df["close"].rolling(200, min_periods=50).mean()
    
    signals = []
    # গত ৪ দিন = ২৪টি 4-ঘণ্টার ক্যান্ডেল
    scan_start_idx = max(20, len(df) - 24)
    
    for i in range(scan_start_idx, len(df)):
        row = df.iloc[i]
        
        for ma_col, ma_name in [("sma50", "50 SMA"), ("sma200", "200 SMA")]:
            ma_val = row[ma_col]
            if pd.isna(ma_val):
                continue
                
            dist_pct = ((row["close"] - ma_val) / ma_val) * 100
            retest_hit = (row["low"] <= ma_val) or (0 <= dist_pct <= 4.5)
            
            if retest_hit and row["close"] >= ma_val:
                entry_price = row["close"]
                stop_loss = ma_val * 0.965
                risk = max(entry_price - stop_loss, entry_price * 0.035)
                
                tp1 = entry_price + (risk * 1.5)
                tp2 = entry_price + (risk * 2.5)
                tp3 = entry_price + (risk * 4.0)
                
                outcome = "ACTIVE"
                pnl_pct = 0.0
                
                for j in range(i + 1, len(df)):
                    future_row = df.iloc[j]
                    if future_row["low"] <= stop_loss:
                        outcome = "SL HIT ❌"
                        pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
                        break
                    elif future_row["high"] >= tp3:
                        outcome = "TP 3 HIT 🚀"
                        pnl_pct = ((tp3 - entry_price) / entry_price) * 100
                        break
                    elif future_row["high"] >= tp2:
                        outcome = "TP 2 HIT 🎯"
                        pnl_pct = ((tp2 - entry_price) / entry_price) * 100
                        break
                    elif future_row["high"] >= tp1:
                        outcome = "TP 1 HIT 🟢"
                        pnl_pct = ((tp1 - entry_price) / entry_price) * 100
                        break
                
                if outcome == "ACTIVE":
                    pnl_pct = ((df.iloc[-1]["close"] - entry_price) / entry_price) * 100

                signals.append({
                    "Signal Time": row["open_time"],
                    "MA Type": ma_name,
                    "Entry": entry_price,
                    "Stop Loss": stop_loss,
                    "TP1": tp1,
                    "TP2": tp2,
                    "Status": outcome,
                    "PnL %": pnl_pct
                })
                break
                
    return signals

# সাইডবার কন্ট্রোল
st.sidebar.header("⚙️ সিমুলেশন কন্ট্রোল")
target_symbol = st.sidebar.text_input("কয়েনের প্রতীক লিখুন:", value="TRXUSDT").upper().strip()

if target_symbol:
    with st.spinner(f"{target_symbol} এর ডেটা ফেচ ও সিমুলেট করা হচ্ছে..."):
        df = get_historical_klines(target_symbol, interval="4h", limit=120)
        
    if df is not None:
        signals = simulate_strategy(df)
        
        st.subheader(f"📈 {target_symbol} - গত ৪ দিনের সিগন্যাল সামারি")
        
        if signals:
            sig_df = pd.DataFrame(signals)
            
            col1, col2, col3, col4 = st.columns(4)
            total_sigs = len(sig_df)
            wins = len(sig_df[sig_df["Status"].str.contains("TP")])
            losses = len(sig_df[sig_df["Status"].str.contains("SL")])
            win_rate = (wins / total_sigs) * 100 if total_sigs > 0 else 0
            
            col1.metric("মোট সিগন্যাল", f"{total_sigs} টি")
            col2.metric("সফল সিগন্যাল (TP Hit)", f"{wins} টি", f"{win_rate:.1f}% Win Rate")
            col3.metric("স্টপ-লস (SL Hit)", f"{losses} টি")
            col4.metric("গড় PnL", f"{sig_df['PnL %'].mean():.2f}%")
            
            st.dataframe(
                sig_df[["Signal Time", "MA Type", "Entry", "Stop Loss", "TP1", "TP2", "Status", "PnL %"]]
                .style.format({"Entry": "{:.6f}", "Stop Loss": "{:.6f}", "TP1": "{:.6f}", "TP2": "{:.6f}", "PnL %": "{:+.2f}%"}),
                use_container_width=True
            )
            
            st.subheader("🕯️ ইন্টারেক্টিভ চার্ট ও ট্রেড লেভেল ভিউ")
            fig = go.Figure()
            
            fig.add_trace(go.Candlestick(
                x=df["open_time"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                name="Price"
            ))
            
            fig.add_trace(go.Scatter(x=df["open_time"], y=df["sma50"], line=dict(color='blue', width=1.5), name="SMA 50"))
            if not df["sma200"].isna().all():
                fig.add_trace(go.Scatter(x=df["open_time"], y=df["sma200"], line=dict(color='orange', width=1.5), name="SMA 200"))
            
            for s in signals:
                s_time = s["Signal Time"]
                entry_p = s["Entry"]
                
                fig.add_annotation(
                    x=s_time, y=entry_p,
                    text=f"BUY ({s['Status']})",
                    showarrow=True, arrowhead=2, arrowcolor="green", arrowsize=1.2,
                    bgcolor="black", font=dict(color="white", size=10)
                )
                fig.add_shape(type="line", x0=s_time, x1=df["open_time"].iloc[-1], y0=entry_p, y1=entry_p, line=dict(color="cyan", width=1, dash="dot"))
                fig.add_shape(type="line", x0=s_time, x1=df["open_time"].iloc[-1], y0=s["Stop Loss"], y1=s["Stop Loss"], line=dict(color="red", width=1, dash="dash"))
                fig.add_shape(type="line", x0=s_time, x1=df["open_time"].iloc[-1], y0=s["TP1"], y1=s["TP1"], line=dict(color="green", width=1, dash="dash"))
            
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=600,
                template="plotly_dark",
                title=f"{target_symbol} 4H Structure & Verified Trades",
                yaxis_title="Price (USDT)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ এই কয়েনটিতে গত ৪ দিনে ৫০/২০০ SMA রিটেস্ট ফিল্টার অনুযায়ী কোনো ভ্যালিড সিগন্যাল তৈরি হয়নি।")
    else:
        st.error("ডেটা লোড করা যায়নি। বাইনান্স এপিআই রেসপন্স দিচ্ছে না অথবা প্রতীক ভুল।")
