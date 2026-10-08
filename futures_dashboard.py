import streamlit as st
import pandas as pd
import ccxt
import time
import requests
import os

LOGO_PATH = "logo.png"
has_custom_logo = os.path.exists(LOGO_PATH)

st.set_page_config(
    page_title="Mobin's Crypto Terminal",
    page_icon=LOGO_PATH if has_custom_logo else "🚀",
    layout="wide"
)

# হেডার
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
sma_choice = st.sidebar.selectbox("মুভিং এভারেজ নির্বাচন করুন", [50, 200], index=0)
timeframe = st.sidebar.selectbox("টাইমফ্রেম", ["1d", "4h"], index=0)
max_dist = st.sidebar.slider("SMA থেকে সর্বোচ্চ দূরত্ব (%)", min_value=1.0, max_value=8.0, value=4.5, step=0.5)

# CCXT এক্সচেঞ্জ ইনিশিয়ালাইজেশন (ক্লাউড ব্লক বাইপাস মোড)
@st.cache_resource
def get_exchange():
    return ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })

def get_tokenomics(clean_symbol):
    """টোকেনোমিক্স ও সাপ্লাই বিশ্লেষণ"""
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://api.coingecko.com/api/v3/search?query={clean_symbol}"
    try:
        s_res = requests.get(search_url, headers=headers, timeout=5).json()
        coins = s_res.get('coins', [])
        target_id = next((c['id'] for c in coins if c['symbol'].upper() == clean_symbol), coins[0]['id'] if coins else None)
        if not target_id:
            return {"Circulating": "N/A", "Total_Supply": "N/A", "Circ_%": "N/A", "Unlock_Status": "Limited Data"}

        data_url = f"https://api.coingecko.com/api/v3/coins/{target_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
        d_res = requests.get(data_url, headers=headers, timeout=5).json()
        market_data = d_res.get('market_data', {})
        
        circulating = market_data.get('circulating_supply') or 0
        total_or_max = market_data.get('max_supply') or market_data.get('total_supply') or 0
        
        if circulating and total_or_max and total_or_max > 0:
            circ_pct = round((circulating / total_or_max) * 100, 2)
            if circ_pct >= 85:
                status = f"🟢 Low Risk ({circ_pct}% Unlocked)"
            elif circ_pct <= 35:
                status = f"🔴 High Dilution ({circ_pct}% Circ)"
            else:
                status = f"🟡 Moderate ({circ_pct}% Circ)"
            return {
                "Circulating": f"{round(circulating/1e6, 2)}M",
                "Total_Supply": f"{round(total_or_max/1e6, 2)}M",
                "Circ_%": f"{circ_pct}%",
                "Unlock_Status": status
            }
        elif circulating:
            return {
                "Circulating": f"{round(circulating/1e6, 2)}M",
                "Total_Supply": "Uncapped",
                "Circ_%": "N/A",
                "Unlock_Status": "No Hard Cap"
            }
    except Exception:
        pass
    return {"Circulating": "N/A", "Total_Supply": "N/A", "Circ_%": "N/A", "Unlock_Status": "N/A"}

def check_sma_retest(exchange, symbol, sma_period, interval, max_distance):
    """CCXT এর মাধ্যমে ক্যান্ডেল ডাটা নিয়ে SMA ক্যালকুলেশন"""
    try:
        limit = sma_period + 30
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
        if len(ohlcv) < (sma_period + 5):
            return None
        
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        df['sma'] = df['close'].rolling(window=sma_period).mean()
        
        current_close = df['close'].iloc[-1]
        current_low = df['low'].iloc[-1]
        current_sma = df['sma'].iloc[-1]
        
        if current_close < current_sma:
            return None
            
        distance_pct = ((current_close - current_sma) / current_sma) * 100
        retesting = (distance_pct <= max_distance) or (current_low <= current_sma and current_close >= current_sma)
        if not retesting:
            return None
            
        was_below = any(df['close'].iloc[-i] < df['sma'].iloc[-i] for i in range(2, 8))
        if was_below:
            return {
                'Symbol': symbol.replace(":USDT", ""),
                'Price ($)': current_close,
                f'SMA_{sma_period}': round(current_sma, 4),
                'Distance (%)': f"{round(distance_pct, 2)}%"
            }
    except Exception:
        return None
    return None

# স্ক্যান বাটন
if st.sidebar.button("🚀 Start Scan", use_container_width=True):
    exchange = get_exchange()
    
    with st.spinner("বাইনান্স ফিউচার্স মার্কেট ডাটা সংযোগ করা হচ্ছে..."):
        try:
            markets = exchange.load_markets()
            # USDT পারপিচুয়াল ফিউচার্স ফিল্টার
            symbols = [
                s for s in markets 
                if '/USDT:USDT' in s or (s.endswith('/USDT') and markets[s].get('future', False))
            ]
        except Exception as e:
            symbols = []

    if not symbols:
        # ফলব্যাক মার্কেট লিস্ট (যাতে কোনো অবস্থাতেই এরর না আসে)
        symbols = [
            'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT', 'XRP/USDT:USDT',
            'DOGE/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'SUI/USDT:USDT', 'NEAR/USDT:USDT',
            'LINK/USDT:USDT', 'APT/USDT:USDT', 'PEPE/USDT:USDT', 'SHIB/USDT:USDT', 'ARBUSDT:USDT'
        ]

    st.info(f"বাইনান্স থেকে {len(symbols)}টি সক্রিয় ফিউচার্স পেয়ার লোড হয়েছে। {sma_choice} SMA স্ক্যান চলছে...")
    
    progress = st.progress(0)
    status_label = st.empty()
    matched_data = []
    
    # প্রথম ৬০-৭০টি পেয়ার দ্রুত স্ক্যান
    scan_list = symbols[:80]
    
    for idx, sym in enumerate(scan_list):
        progress.progress((idx + 1) / len(scan_list))
        status_label.text(f"স্ক্যানিং: {sym.split('/')[0]} ({idx+1}/{len(scan_list)})")
        
        match = check_sma_retest(exchange, sym, sma_choice, timeframe, max_dist)
        if match:
            clean_sym = sym.split('/')[0]
            tokenomics = get_tokenomics(clean_sym)
            arkham_link = f"https://platform.arkhamintelligence.com/explorer/token/{clean_sym.lower()}"
            
            match.update(tokenomics)
            match['Arkham Intelligence'] = arkham_link
            matched_data.append(match)
            time.sleep(0.3)
            
        time.sleep(0.05)
        
    progress.empty()
    status_label.empty()
    
    if matched_data:
        st.success(f"🎉 স্ক্যান সম্পন্ন! মোট {len(matched_data)}টি টোকেন {sma_choice} SMA শর্ত পূরণ করেছে।")
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
            label="📥 CSV রিপোর্ট ডাউনলোড করুন",
            data=csv_file,
            file_name=f"mobin_crypto_{sma_choice}sma_report.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"বর্তমান ফিল্টারে {sma_choice} SMA-এর কোনো রিটেস্ট কয়েন পাওয়া যায়নি। দূরত্বের শতাংশ বাড়িয়ে দেখতে পারেন।")

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
