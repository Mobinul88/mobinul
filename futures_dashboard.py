import streamlit as st
import pandas as pd
import requests
import time
import os

LOGO_PATH = "logo.png"
has_custom_logo = os.path.exists(LOGO_PATH)

st.set_page_config(
    page_title="Mobin's Crypto Terminal",
    page_icon=LOGO_PATH if has_custom_logo else "🚀",
    layout="wide"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# হেডার ব্র্যান্ডিং
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if has_custom_logo:
        st.image(LOGO_PATH, width=95)
    else:
        st.markdown("# 🚀")

with col_title:
    st.title("বাইনান্স ফিউচার্স ইন্টেলিজেন্স টার্মিনাল")
    st.markdown(" `Developed by Mobinul` | *Powered by Binance & Arkham*")

st.divider()

# সাইডবার
st.sidebar.markdown("### 👑 Creator Profile")
if has_custom_logo:
    st.sidebar.image(LOGO_PATH, width=120)

st.sidebar.markdown("**Create by:** Mobinul")
st.sidebar.caption("Crypto Algorithmic & On-Chain Researcher")
st.sidebar.markdown("---")

st.sidebar.header("⚙️ স্ক্যান সেটিংস")
sma_choice = st.sidebar.selectbox("মুভিং এভারেজ নির্বাচন করুন", [50, 200], index=0)
timeframe = st.sidebar.selectbox("টাইমফ্রেম", ["1d", "4h"], index=0)
max_dist = st.sidebar.slider("SMA থেকে সর্বোচ্চ দূরত্ব (%)", min_value=1.0, max_value=10.0, value=5.0, step=0.5)

@st.cache_data(ttl=1800)
def get_all_futures_symbols():
    """বাইনান্সের সম্পূর্ণ ৫০০টি ফিউচার্স পেয়ার ক্লাউড-সেফ গেটওয়ে দিয়ে সংগ্রহ করা"""
    sources = [
        "https://fapi.binance.com/fapi/v1/exchangeInfo",
        "https://data-api.binance.vision/api/v3/exchangeInfo",
        "https://api.binance.com/api/v3/exchangeInfo"
    ]
    
    # প্রথম চেষ্টা: ফিউচার্স মূল তালিকা
    try:
        r = requests.get(sources[0], headers=HEADERS, timeout=7)
        if r.status_code == 200:
            symbols = [
                s['symbol'] for s in r.json().get('symbols', [])
                if s['symbol'].endswith('USDT') and s.get('status') == 'TRADING' and s.get('contractType') == 'PERPETUAL'
            ]
            if len(symbols) > 100:
                return symbols
    except Exception:
        pass

    # বিকল্প ব্যাকআপ: পাবলিক ওপেন গেটওয়ে থেকে সব সক্রিয় পেয়ার
    for url in sources[1:]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=7)
            if r.status_code == 200:
                symbols = [
                    s['symbol'] for s in r.json().get('symbols', [])
                    if s['symbol'].endswith('USDT') and s.get('status') == 'TRADING'
                ]
                if len(symbols) > 100:
                    return symbols
        except Exception:
            continue
            
    return []

def get_tokenomics(clean_symbol):
    """কয়েনগেকো অন-চেইন সাপ্লাই ডেটা"""
    try:
        s_url = f"https://api.coingecko.com/api/v3/search?query={clean_symbol}"
        s_res = requests.get(s_url, headers=HEADERS, timeout=4).json()
        coins = s_res.get('coins', [])
        target_id = next((c['id'] for c in coins if c['symbol'].upper() == clean_symbol), coins[0]['id'] if coins else None)
        
        if not target_id:
            return {"Circulating": "N/A", "Total_Supply": "N/A", "Circ_%": "N/A", "Unlock_Status": "Limited"}

        d_url = f"https://api.coingecko.com/api/v3/coins/{target_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
        market_data = requests.get(d_url, headers=HEADERS, timeout=4).json().get('market_data', {})
        
        circulating = market_data.get('circulating_supply') or 0
        total_or_max = market_data.get('max_supply') or market_data.get('total_supply') or 0
        
        if circulating and total_or_max and total_or_max > 0:
            circ_pct = round((circulating / total_or_max) * 100, 2)
            status = "🟢 Low Risk" if circ_pct >= 80 else ("🔴 High Dilution" if circ_pct <= 35 else "🟡 Moderate")
            return {
                "Circulating": f"{round(circulating/1e6, 2)}M",
                "Total_Supply": f"{round(total_or_max/1e6, 2)}M",
                "Circ_%": f"{circ_pct}%",
                "Unlock_Status": f"{status} ({circ_pct}%)"
            }
    except Exception:
        pass
    return {"Circulating": "N/A", "Total_Supply": "N/A", "Circ_%": "N/A", "Unlock_Status": "N/A"}

def check_sma_retest(symbol, sma_period, interval, max_distance):
    """ক্যান্ডেল ডাটা সংগ্রহ ও রিটেস্ট অ্যালগরিদম"""
    urls = [
        "https://fapi.binance.com/fapi/v1/klines",
        "https://data-api.binance.vision/api/v3/klines",
        "https://api.binance.com/api/v3/klines"
    ]
    params = {'symbol': symbol, 'interval': interval, 'limit': sma_period + 30}
    
    data = None
    for u in urls:
        try:
            r = requests.get(u, params=params, headers=HEADERS, timeout=3)
            if r.status_code == 200:
                res = r.json()
                if isinstance(res, list) and len(res) >= (sma_period + 5):
                    data = res
                    break
        except Exception:
            continue
            
    if not data:
        return None

    try:
        df = pd.DataFrame([{'low': float(c[3]), 'close': float(c[4])} for c in data])
        df['sma'] = df['close'].rolling(window=sma_period).mean()
        
        current_close = df['close'].iloc[-1]
        current_low = df['low'].iloc[-1]
        current_sma = df['sma'].iloc[-1]
        
        if current_close < current_sma:
            return None
            
        dist_pct = ((current_close - current_sma) / current_sma) * 100
        retesting = (dist_pct <= max_distance) or (current_low <= current_sma and current_close >= current_sma)
        if not retesting:
            return None
            
        was_below = any(df['close'].iloc[-i] < df['sma'].iloc[-i] for i in range(2, 8))
        if was_below:
            return {
                'Symbol': symbol,
                'Price ($)': current_close,
                f'SMA_{sma_period}': round(current_sma, 4),
                'Distance (%)': f"{round(dist_pct, 2)}%"
            }
    except Exception:
        return None
    return None

# স্ক্যান ট্রিগার
if st.sidebar.button("🚀 Start Scan", use_container_width=True):
    with st.spinner("বাইনান্সের সম্পূর্ণ পেয়ার লিস্ট সিঙ্ক করা হচ্ছে..."):
        symbols = get_all_futures_symbols()
        
    if not symbols:
        st.error("⚠️ পেয়ার লিস্ট লোড করা যায়নি। কিছুক্ষণ পর আবার চেষ্টা করুন।")
    else:
        st.success(f"বাইনান্স থেকে সফলভাবে মোট {len(symbols)}টি সক্রিয় পেয়ার লোড হয়েছে! স্ক্যানিং শুরু হচ্ছে...")
        
        progress = st.progress(0)
        status_label = st.empty()
        matched_data = []
        
        for idx, sym in enumerate(symbols):
            progress.progress((idx + 1) / len(symbols))
            status_label.text(f"স্ক্যান হচ্ছে [{idx+1}/{len(symbols)}]: {sym}")
            
            match = check_sma_retest(sym, sma_choice, timeframe, max_dist)
            if match:
                clean_sym = sym.replace("USDT", "")
                tokenomics = get_tokenomics(clean_sym)
                arkham_link = f"https://platform.arkhamintelligence.com/explorer/token/{clean_sym.lower()}"
                
                match.update(tokenomics)
                match['Arkham Intelligence'] = arkham_link
                matched_data.append(match)
                time.sleep(0.15)
                
            time.sleep(0.01)
            
        progress.empty()
        status_label.empty()
        
        if matched_data:
            st.success(f"🎉 স্ক্যান সম্পন্ন! মোট {len(matched_data)}টি পেয়ার {sma_choice} SMA রিটেস্ট শর্ত পূরণ করেছে।")
            df_result = pd.DataFrame(matched_data)
            
            st.dataframe(
                df_result,
                column_config={
                    "Arkham Intelligence": st.column_config.LinkColumn("Arkham Link", display_text="Open Arkham")
                },
                use_container_width=True,
                hide_index=True
            )
            
            csv_file = df_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 সম্পূর্ণ CSV রিপোর্ট ডাউনলোড",
                data=csv_file,
                file_name=f"mobin_crypto_{sma_choice}sma_full_report.csv",
                mime="text/csv"
            )
        else:
            st.warning(f"বর্তমান ফিল্টারে {sma_choice} SMA-এর কোনো রিটেস্ট কয়েন পাওয়া যায়নি। দূরত্বের স্লাইডারটি একটু বাড়িয়ে দেখতে পারেন।")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 13px;'>
        © 2026 <b>Mobinul Intelligence Terminal</b> | All Rights Reserved.<br>
        <i>Unauthorized redistribution of this tool or data logic is prohibited.</i>
    </div>
    """,
    unsafe_allow_html=True
)
