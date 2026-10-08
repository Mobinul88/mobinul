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
    st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *Powered by Binance & Arkham*")

st.divider()

# সাইডবার
st.sidebar.markdown("### 👑 Creator Profile")
if has_custom_logo:
    st.sidebar.image(LOGO_PATH, width=120)

st.sidebar.markdown("**Create by:** Mobinul")
st.sidebar.caption("Crypto Algorithmic & On-Chain Researcher")
st.sidebar.markdown("---")

st.sidebar.header("⚙️ স্ক্যান সেটিংস")
sma_choice = st.sidebar.selectbox("মুভিং এভারেজ নির্বাচন করুন", [50, 200], index=1)
timeframe = st.sidebar.selectbox("টাইমফ্রেম", ["1d", "4h"], index=0)
max_dist = st.sidebar.slider("SMA থেকে সর্বোচ্চ দূরত্ব (%)", min_value=1.0, max_value=10.0, value=5.0, step=0.5)

@st.cache_data(ttl=1800)
def get_all_futures_symbols():
    """বাইনান্সের ১০০% ভ্যালিড সক্রিয় পেয়ার সংগ্রহ"""
    sources = [
        "https://fapi.binance.com/fapi/v1/exchangeInfo",
        "https://data-api.binance.vision/api/v3/exchangeInfo"
    ]
    for url in sources:
        try:
            r = requests.get(url, headers=HEADERS, timeout=6)
            if r.status_code == 200:
                data = r.json()
                symbols = [
                    s['symbol'] for s in data.get('symbols', [])
                    if s['symbol'].endswith('USDT') 
                    and not s['symbol'].startswith('1000') # কনভার্টেড মেমে টোকেন বাদ দেওয়া
                    and s.get('status') == 'TRADING'
                ]
                if len(symbols) > 50:
                    return symbols
        except Exception:
            continue
    return []

@st.cache_data(ttl=3600)
def get_global_market_assets():
    """CoinCap থেকে সব ক্রিপ্টোর সাপ্লাই ডাটা একবারে লোড করা (রেট-লিমিট ছাড়া)"""
    try:
        url = "https://api.coincap.io/v2/assets?limit=1500"
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            asset_list = r.json().get('data', [])
            cache_map = {}
            for item in asset_list:
                cache_map[item['symbol'].upper()] = item
            return cache_map
    except Exception:
        pass
    return {}

def extract_tokenomics(clean_sym, market_cache):
    """সাপ্লাই ও আনলক রেশিও হিসাব"""
    item = market_cache.get(clean_sym)
    if item:
        try:
            supply = float(item.get('supply') or 0)
            max_sup = float(item.get('maxSupply') or 0)
            
            if supply > 0 and max_sup > 0:
                circ_pct = round((supply / max_sup) * 100, 2)
                status = "🟢 Low Risk" if circ_pct >= 80 else ("🔴 High Dilution" if circ_pct <= 35 else "🟡 Moderate")
                return {
                    "Circulating": f"{round(supply/1e6, 2)}M",
                    "Total_Supply": f"{round(max_sup/1e6, 2)}M",
                    "Circ_%": f"{circ_pct}%",
                    "Unlock_Status": f"{status} ({circ_pct}%)"
                }
            elif supply > 0:
                return {
                    "Circulating": f"{round(supply/1e6, 2)}M",
                    "Total_Supply": "Uncapped",
                    "Circ_%": "N/A",
                    "Unlock_Status": "🟢 No Hard Cap"
                }
        except Exception:
            pass

    # ব্যাকআপ হিসেবে কয়েনগেকো সিঙ্গেল কল (যদি CoinCap-এ না পাওয়া যায়)
    try:
        cg_url = f"https://api.coingecko.com/api/v3/coins/{clean_sym.lower()}"
        res = requests.get(cg_url, headers=HEADERS, timeout=3).json()
        m_data = res.get('market_data', {})
        c_sup = m_data.get('circulating_supply') or 0
        t_sup = m_data.get('max_supply') or m_data.get('total_supply') or 0
        if c_sup and t_sup:
            pct = round((c_sup / t_sup) * 100, 2)
            st_text = "🟢 Low Risk" if pct >= 80 else "🟡 Moderate"
            return {
                "Circulating": f"{round(c_sup/1e6, 2)}M",
                "Total_Supply": f"{round(t_sup/1e6, 2)}M",
                "Circ_%": f"{pct}%",
                "Unlock_Status": f"{st_text} ({pct}%)"
            }
    except Exception:
        pass

    return {"Circulating": "N/A", "Total_Supply": "N/A", "Circ_%": "N/A", "Unlock_Status": "Limited Data"}

def check_sma_retest(symbol, sma_period, interval, max_distance):
    """ক্যান্ডেল ডাটা সংগ্রহ ও রিটেস্ট অ্যালগরিদম"""
    urls = [
        "https://data-api.binance.vision/api/v3/klines",
        "https://fapi.binance.com/fapi/v1/klines",
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
                'Symbol': symbol.replace("USDT", ""),
                'Price ($)': current_close,
                f'SMA_{sma_period}': round(current_sma, 4),
                'Distance (%)': f"{round(dist_pct, 2)}%"
            }
    except Exception:
        return None
    return None

# স্ক্যান ট্রিগার
if st.sidebar.button("🚀 Start Scan", use_container_width=True):
    with st.spinner("মার্কেট ও অন-চেইন মেটাডাটা সিঙ্ক করা হচ্ছে..."):
        symbols = get_all_futures_symbols()
        market_cache = get_global_market_assets()
        
    if not symbols:
        st.error("⚠️ পেয়ার লিস্ট লোড করা সম্ভব হয়নি।")
    else:
        st.info(f"বাইনান্স থেকে সফলভাবে {len(symbols)}টি সক্রিয় পেয়ার লোড হয়েছে। স্ক্যানিং চলছে...")
        
        progress = st.progress(0)
        status_label = st.empty()
        matched_data = []
        
        for idx, sym in enumerate(symbols):
            progress.progress((idx + 1) / len(symbols))
            clean_sym = sym.replace("USDT", "")
            status_label.text(f"স্ক্যান হচ্ছে [{idx+1}/{len(symbols)}]: {clean_sym}")
            
            match = check_sma_retest(sym, sma_choice, timeframe, max_dist)
            if match:
                tokenomics = extract_tokenomics(clean_sym, market_cache)
                # Arkham ইন্টেলিজেন্সের ডাইরেক্ট এক্সপ্লোরার লিঙ্ক
                arkham_url = f"https://platform.arkhamintelligence.com/explorer/token/{clean_sym.lower()}"
                
                match.update(tokenomics)
                match['Arkham Link'] = arkham_url
                matched_data.append(match)
                
            time.sleep(0.01)
            
        progress.empty()
        status_label.empty()
        
        if matched_data:
            st.success(f"🎉 স্ক্যান সম্পন্ন! মোট {len(matched_data)}টি পেয়ার {sma_choice} SMA রিটেস্ট ফিল্টারে পাওয়া গেছে।")
            df_result = pd.DataFrame(matched_data)
            
            st.dataframe(
                df_result,
                column_config={
                    "Arkham Link": st.column_config.LinkColumn("Arkham Intelligence", display_text="Open Arkham")
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
            st.warning(f"বর্তমান ফিল্টারে {sma_choice} SMA-এর কোনো রিটেস্ট কয়েন পাওয়া যায়নি। দূরত্বের শতাংশ একটু বাড়িয়ে দেখতে পারেন।")

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
