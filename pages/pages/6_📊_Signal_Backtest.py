import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Institutional Swing Backtest", layout="wide")

BINANCE_FAPI = "https://fapi.binance.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

st.title("📊 4-Day Institutional Signal Performance & Visualizer")
st.markdown("গত ৪ দিনে এপিআইয়ের তৈরি করা সিগন্যালগুলোর সিমুলেশন এবং লাইভ রেজাল্ট যাচাইকরণ।")

@st.cache_data(ttl=600)
def get_historical_klines(symbol, interval="4h", limit=100):
    url = f"{BINANCE_FAPI}/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=10).json()
        if not isinstance(res, list) or len(res) < 50:
            return None
        df = pd.DataFrame(res, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_base_vol", "taker_quote_vol", "ignore"
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df
    except Exception:
        return None

def simulate_strategy(df):
    """৫০ ও ২০০ মুভিং এভারেজ রিটেস্ট সিমুলেট করে সিগন্যালের রেজাল্ট বের করে"""
    df["sma50"] = df["close"].rolling(50).mean()
    df["sma200"] = df["close"].rolling(200).mean()
    
    signals = []
    # গত ৪ দিন = ২৪টি ক্যান্ডেল (4H টাইমফ্রেমে)
    scan_start_idx = max(50, len(df) - 24)
    
    for i in range(scan_start_idx, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # ৫০ অথবা ২০০ এসএমএ রিটেস্ট ফিল্টার
        for ma_col, ma_name in [("sma50", "50 SMA"), ("sma200", "200 SMA")]:
            ma_val = row[ma_col]
            if pd.isna(ma_val):
                continue
                
            dist_pct = ((row["close"] - ma_val) / ma_val) * 100
            retest_hit = (row["low"] <= ma_val) or (0 <= dist_pct <= 4.5)
            
            # সিগন্যাল ফর্মেশন শর্ত
            if retest_hit and row["close"] >= ma_val:
                entry_price = row["close"]
                stop_loss = ma_val * 0.965
                risk = max(entry_price - stop_loss, entry_price * 0.035)
                
                tp1 = entry_price + (risk * 1.5)
                tp2 = entry_price + (risk * 2.5)
                tp3 = entry_price + (risk * 4.0)
                
                # পরবর্তী ক্যান্ডেলগুলোতে রেজাল্ট ট্র্যাকিং
                outcome = "ACTIVE"
                pnl_pct = 0.0
                hit_time = None
                
                for j in range(i + 1, len(df)):
                    future_row = df.iloc[j]
                    # স্টপ লস হিট চেক
                    if future_row["low"] <= stop_loss:
                        outcome = "SL HIT ❌"
                        pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
                        hit_time = future_row["open_time"]
                        break
                    # টিপি ৩ হিট চেক
                    elif future_row["high"] >= tp3:
                        outcome = "TP 3 HIT 🚀"
                        pnl_pct = ((tp3 - entry_price) / entry_price) * 100
                        hit_time = future_row["open_time"]
                        break
                    # টিপি ২ হিট চেক
                    elif future_row["high"] >= tp2:
                        outcome = "TP 2 HIT 🎯"
                        pnl_pct = ((tp2 - entry_price) / entry_price) * 100
                        hit_time = future_row["open_time"]
                        break
                    # টিপি ১ হিট চেক
                    elif future_row["high"] >= tp1:
                        outcome = "TP 1 HIT 🟢"
                        pnl_pct = ((tp1 - entry_price) / entry_price) * 100
                        hit_time = future_row["open_time"]
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
                    "TP3": tp3,
                    "Status": outcome,
                    "PnL %": pnl_pct,
                    "Signal Index": i
                })
                break  # একই ক্যান্ডেলে ডাবল কাউন্ট রোধ
                
    return signals

# সাইডবার কন্ট্রোল
st.sidebar.header("⚙️ সিমুলেশন কন্ট্রোল")
target_symbol = st.sidebar.text_input("কয়েনের প্রতীক লিখুন (যেমন: MEMEUSDT, TRXUSDT):", value="MEMEUSDT").upper()

if target_symbol:
    with st.spinner(f"{target_symbol} এর ডেটা ফেচ ও সিমুলেট করা হচ্ছে..."):
        df = get_historical_klines(target_symbol, interval="4h", limit=120)
        
    if df is not None:
        signals = simulate_strategy(df)
        
        # ১. পারফরম্যান্স মেট্রিকস কার্ডস
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
            
            # সিগন্যাল টেবিল
            st.dataframe(
                sig_df[["Signal Time", "MA Type", "Entry", "Stop Loss", "TP1", "TP2", "Status", "PnL %"]]
                .style.format({"Entry": "{:.6f}", "Stop Loss": "{:.6f}", "TP1": "{:.6f}", "TP2": "{:.6f}", "PnL %": "{:+.2f}%"})
            )
            
            # ২. Plotly ইন্টারেক্টিভ ক্যান্ডেলস্টিক চার্ট
            st.subheader("🕯️ ইন্টারেক্টিভ চার্ট ও ট্রেড লেভেল ভিউ")
            
            fig = go.Figure()
            
            # ক্যান্ডেলস্টিক প্লট
            fig.add_trace(go.Candlestick(
                x=df["open_time"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="Price"
            ))
            
            # ৫০ এবং ২০০ মুভিং এভারেজ
            fig.add_trace(go.Scatter(x=df["open_time"], y=df["sma50"], line=dict(color='blue', width=1.5), name="SMA 50"))
            if not df["sma200"].isna().all():
                fig.add_trace(go.Scatter(x=df["open_time"], y=df["sma200"], line=dict(color='orange', width=1.5), name="SMA 200"))
            
            # চার্টে সিগন্যালগুলো চিহ্নিত করা
            for s in signals:
                s_time = s["Signal Time"]
                entry_p = s["Entry"]
                sl_p = s["Stop Loss"]
                tp1_p = s["TP1"]
                tp2_p = s["TP2"]
                
                # এন্ট্রি পয়েন্ট মার্কার
                fig.add_annotation(
                    x=s_time, y=entry_p,
                    text=f"BUY ({s['Status']})",
                    showarrow=True, arrowhead=2, arrowcolor="green", arrowsize=1.2,
                    bgcolor="black", font=dict(color="white", size=10)
                )
                
                # অনুভূমিক লেভেল লাইন (এন্ট্রি, এসএল, টিপি)
                fig.add_shape(type="line", x0=s_time, x1=df["open_time"].iloc[-1], y0=entry_p, y1=entry_p, line=dict(color="cyan", width=1, dash="dot"))
                fig.add_shape(type="line", x0=s_time, x1=df["open_time"].iloc[-1], y0=sl_p, y1=sl_p, line=dict(color="red", width=1, dash="dash"))
                fig.add_shape(type="line", x0=s_time, x1=df["open_time"].iloc[-1], y0=tp1_p, y1=tp1_p, line=dict(color="green", width=1, dash="dash"))
            
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=650,
                template="plotly_dark",
                title=f"{target_symbol} 4H Execution Structure & Signals",
                yaxis_title="Price (USDT)",
                xaxis_title="Date & Time"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("ℹ️ এই কয়েনটিতে গত ৪ দিনে ৫০/২০০ SMA রিটেস্ট ফিল্টার অনুযায়ী কোনো ভ্যালিড কনফ্লুয়েন্স সিগন্যাল তৈরি হয়নি।")
    else:
        st.error("ডেটা লোড করা যায়নি। প্রতীক ঠিক আছে কি না যাচাই করুন।")
