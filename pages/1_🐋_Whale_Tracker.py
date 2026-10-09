import streamlit as st
import requests
import pandas as pd
import datetime

st.set_page_config(
    page_title="Whale & 30-Day Flow Tracker",
    page_icon="🐋",
    layout="wide"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

st.title("🐋 হোয়েল ট্র্যাকিং ও ৩০ দিনের এক্সচেঞ্জ ফ্লো")
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *লার্জ ট্রানজ্যাকশন ও ৩০ দিনের হিস্টোরিক্যাল অন-চেইন ফ্লো*")
st.divider()

# শীর্ষ ফান্ড ও প্রাতিষ্ঠানিক লিঙ্ক
st.markdown("### 🏦 প্রাতিষ্ঠানিক ফান্ড ও এক্সচেঞ্জ রিজার্ভ")
col_e1, col_e2, col_e3, col_e4 = st.columns(4)
with col_e1:
    st.markdown("[🏛️ **Binance CEX Reserves**](https://arkm.com/explorer/entity/binance)")
with col_e2:
    st.markdown("[🦅 **Jump Trading Portfolio**](https://arkm.com/explorer/entity/jump-trading)")
with col_e3:
    st.markdown("[❄️ **Wintermute Trading**](https://arkm.com/explorer/entity/wintermute)")
with col_e4:
    st.markdown("[💼 **DWF Labs Activity**](https://arkm.com/explorer/entity/dwf-labs)")

st.divider()

col_search, col_days = st.columns([3, 1])
with col_search:
    user_token = st.text_input("যেকোনো কয়েনের সিম্বল লিখুন (যেমন: BTC, ETH, SOL, LPT, NEAR, FET):", value="BTC").strip().upper()
with col_days:
    days_choice = st.selectbox("হিস্ট্রি রেঞ্জ নির্বাচন করুন:", [7, 14, 30], index=2)

def fetch_token_info(symbol):
    """কয়েন আইডি ও মেটাডাটা সংগ্রহ"""
    try:
        s_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        s_res = requests.get(s_url, headers=HEADERS, timeout=6).json()
        coins = s_res.get('coins', [])
        target = next((c for c in coins if c['symbol'].upper() == symbol), coins[0] if coins else None)
        return target
    except Exception:
        return None

def fetch_historical_30d_data(coin_id, days):
    """গত ৩০ দিনের লাইভ প্রাইস ও ভলিউম ডেটা সংগ্রহ"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
    try:
        r = requests.get(url, headers=HEADERS, timeout=7)
        if r.status_code == 200:
            res = r.json()
            prices = res.get('prices', [])
            volumes = res.get('total_volumes', [])
            market_caps = res.get('market_caps', [])
            
            rows = []
            for p, v, mc in zip(prices, volumes, market_caps):
                date_str = datetime.datetime.fromtimestamp(p[0] / 1000).strftime('%Y-%m-%d')
                price_val = round(p[1], 4)
                vol_val = v[1]
                mc_val = mc[1]
                
                vol_mc_ratio = round((vol_val / mc_val) * 100, 2) if mc_val > 0 else 0
                
                # ৩০ দিনের স্মার্ট মানি ট্রেন্ড ডিটেকশন
                if vol_mc_ratio >= 20:
                    sentiment = "🔥 High Whale Turnover"
                elif vol_mc_ratio >= 10:
                    sentiment = "⚡ Smart Money Flow"
                else:
                    sentiment = "🟢 Normal Retail"
                    
                rows.append({
                    "তারিখ (Date)": date_str,
                    "প্রাইস ($)": price_val,
                    "দৈনিক ভলিউম ($)": f"${round(vol_val/1e6, 2)}M",
                    "মার্কেট ক্যাপ ($)": f"${round(mc_val/1e6, 2)}M",
                    "ভলিউম/ক্যাপ (%)": f"{vol_mc_ratio}%",
                    "হোয়েল অ্যাক্টিভিটি": sentiment,
                    "Raw_Date": date_str,
                    "Raw_Price": price_val,
                    "Raw_Vol": round(vol_val/1e6, 2)
                })
            return pd.DataFrame(rows)
    except Exception:
        pass
    return pd.DataFrame()

if user_token:
    with st.spinner(f"{user_token}-এর গত {days_choice} দিনের হিস্টোরিক্যাল ডেটা আনা হচ্ছে..."):
        token_info = fetch_token_info(user_token)

    if token_info:
        coin_id = token_info['id']
        coin_name = token_info.get('name', user_token)
        
        hist_df = fetch_historical_30d_data(coin_id, days_choice)
        
        if not hist_df.empty:
            # সংক্ষিপ্ত মেট্রিক্স
            current_price = hist_df['Raw_Price'].iloc[-1]
            oldest_price = hist_df['Raw_Price'].iloc[0]
            change_period = round(((current_price - oldest_price) / oldest_price) * 100, 2)
            avg_vol = round(hist_df['Raw_Vol'].mean(), 2)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("বর্তমান প্রাইস", f"${current_price:,.4f}", f"{change_period}% ({days_choice} দিনে)")
            m2.metric(f"গত {days_choice} দিনের গড় ভলিউম", f"${avg_vol}M / দিন")
            m3.metric("ডেটা পয়েন্ট সংখ্যা", f"{len(hist_df)} দিন")
            
            st.markdown("---")
            
            # ৩০ দিনের প্রাইস ও ভলিউম ট্রেন্ড চার্ট
            st.subheader(f"📈 {coin_name} ({user_token}) - গত {days_choice} দিনের প্রাইস ও ট্রেডিং ভলিউম ট্রেন্ড")
            chart_data = hist_df.set_index('Raw_Date')[['Raw_Price']]
            chart_data.columns = ['Price ($)']
            st.line_chart(chart_data)
            
            st.markdown("---")
            
            # ৩০ দিনের বিস্তারিত দিনভিত্তিক হিস্ট্রি টেবিল
            st.subheader(f"🗓️ গত {days_choice} দিনের দিনভিত্তিক বিস্তারিত হিস্ট্রি ও হোয়েল অ্যানালাইসিস")
            
            display_cols = ["তারিখ (Date)", "প্রাইস ($)", "দৈনিক ভলিউম ($)", "মার্কেট ক্যাপ ($)", "ভলিউম/ক্যাপ (%)", "হোয়েল অ্যাক্টিভিটি"]
            # সাম্প্রতিক দিনগুলো সবার উপরে দেখানো (Descending Order)
            st.dataframe(
                hist_df[display_cols].iloc[::-1],
                use_container_width=True,
                hide_index=True
            )
            
            # CSV ডাউনলোড বাটন
            csv_30d = hist_df[display_cols].to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 {days_choice} দিনের সম্পূর্ণ হিস্ট্রি রিপোর্ট ডাউনলোড করুন (CSV)",
                data=csv_30d,
                file_name=f"{user_token}_{days_choice}d_history_report.csv",
                mime="text/csv"
            )
            
            st.info(f"💡 এই কয়েনটির প্রতিটি নির্দিষ্ট অন-চেইন ট্রানজ্যাকশন দেখতে Arkham-এ সরাসরি যেতে পারেন:")
            st.markdown(f"[🌐 Open {coin_name} On-Chain Explorer](https://arkm.com/explorer/token/{coin_id})")
        else:
            st.warning("হিস্টোরিক্যাল ডাটা লোড হতে পারেনি। কিছুক্ষণ পর চেষ্টা করুন।")
    else:
        st.warning(f"'{user_token}' সিম্বলটির মেটাডাটা পাওয়া যায়নি। সঠিক সিম্বল লিখুন (যেমন: BTC, ETH, SOL, LPT)।")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 13px;'>
        © 2026 <b>Mobinul Intelligence Terminal</b> | All Rights Reserved.<br>
        <i>Historical On-Chain & Whale Intelligence Engine</i>
    </div>
    """,
    unsafe_allow_html=True
)
