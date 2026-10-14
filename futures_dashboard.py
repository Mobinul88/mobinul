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

session = requests.Session()
session.headers.update(HEADERS)

# সেক্টর ম্যাপিং
SECTOR_MAP = {
    # AI & Big Data
    'FET': '🤖 AI / Data', 'NEAR': '🤖 AI / L1', 'RNDR': '🤖 AI / GPU', 'RENDER': '🤖 AI / GPU',
    'TAO': '🤖 AI', 'WLD': '🤖 AI / Identity', 'AGIX': '🤖 AI', 'ARKM': '🤖 AI / Intel',
    'OCEAN': '🤖 AI / Data', 'GRT': '🤖 AI / Indexing', 'IO': '🤖 AI / Compute',

    # RWA
    'ONDO': '🏛️ RWA', 'LINK': '🏛️ Oracle / RWA', 'PENDLE': '🏛️ RWA / Yield',
    'MKR': '🏛️ RWA / DeFi', 'CFG': '🏛️ RWA', 'TRU': '🏛️ RWA', 'POLYX': '🏛️ RWA',

    # Layer 1
    'BTC': '🧱 Layer 1', 'ETH': '🧱 Layer 1', 'SOL': '🧱 Layer 1', 'BNB': '🧱 Layer 1',
    'SUI': '🧱 Layer 1', 'SEI': '🧱 Layer 1', 'AVAX': '🧱 Layer 1', 'ATOM': '🧱 Layer 1',
    'ADA': '🧱 Layer 1', 'DOT': '🧱 Layer 1', 'KAS': '🧱 Layer 1', 'ALGO': '🧱 Layer 1',
    'FTM': '🧱 Layer 1', 'INJ': '🧱 Layer 1 / DeFi', 'APT': '🧱 Layer 1', 'TON': '🧱 Layer 1',

    # Layer 2
    'ARB': '⚡ Layer 2', 'OP': '⚡ Layer 2', 'MATIC': '⚡ Layer 2', 'POL': '⚡ Layer 2',
    'STRK': '⚡ Layer 2', 'MANTA': '⚡ Layer 2', 'METIS': '⚡ Layer 2', 'BLAST': '⚡ Layer 2',
    'ZK': '⚡ Layer 2 (ZK)', 'IMX': '⚡ Layer 2 / Gaming',

    # DeFi
    'UNI': '🔄 DeFi', 'AAVE': '🔄 DeFi / Lending', 'CRV': '🔄 DeFi', 'DYDX': '🔄 DeFi / Perp',
    'SNX': '🔄 DeFi', 'CAKE': '🔄 DeFi', 'JUP': '🔄 DeFi / Solana', 'RAY': '🔄 DeFi / Solana',
    'COMP': '🔄 DeFi', 'SUSHI': '🔄 DeFi', '1INCH': '🔄 DeFi', 'LDO': '🔄 Liquid Staking',

    # Meme Coins
    'DOGE': '🐶 Meme', 'SHIB': '🐶 Meme', 'PEPE': '🐶 Meme', 'WIF': '🐶 Meme',
    'BONK': '🐶 Meme', 'FLOKI': '🐶 Meme', 'BOME': '🐶 Meme', 'MEME': '🐶 Meme',

    # Gaming & Metaverse
    'GALA': '🎮 Gaming', 'AXS': '🎮 Gaming', 'SAND': '🎮 Metaverse', 'MANA': '🎮 Metaverse',
    'BEAM': '🎮 Gaming', 'PIXEL': '🎮 Gaming', 'NOT': '🎮 Web3 Gaming',

    # DePIN & Storage
    'FIL': '📦 DePIN / Storage', 'AR': '📦 Storage', 'HNT': '📡 DePIN', 'THETA': '📡 DePIN / Video'
}

# ========================================================
# সাইডবার (শুধুমাত্র প্রোফাইল ও পরিচিতি)
# ========================================================
st.sidebar.markdown("### 👑 Creator Profile")
if has_custom_logo:
    st.sidebar.image(LOGO_PATH, width=120)

st.sidebar.markdown("**Created by:** Mobinul")
st.sidebar.caption("Crypto Algorithmic & On-Chain Researcher")
st.sidebar.markdown("---")
st.sidebar.info("💡 **টিপস:** সব ধরনের স্ক্যান ও লিডিং ফিল্টার সেটিংস এখন সরাসরি মূল ড্যাশবোর্ডের ওপরে রয়েছে।")

# ========================================================
# হেডার ব্র্যান্ডিং
# ========================================================
col_logo, col_title = st.columns([1, 8])
with col_logo:
    if has_custom_logo:
        st.image(LOGO_PATH, width=85)
    else:
        st.markdown("# 🚀")

with col_title:
    st.title("বাইনান্স ফিউচার্স প্রাতিষ্ঠানিক ইন্টেলিজেন্স টার্মিনাল")
    st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *Powered by Binance, CoinGlass & Arkham*")

st.divider()

# ========================================================
# মেইন পেজ সেটিংস ড্যাশবোর্ড (গ্রিড লেআউট)
# ========================================================
with st.container():
    st.subheader("⚙️ স্ক্যান কন্ট্রোল ও লিডিং ফিল্টার ড্যাশবোর্ড")
    
    col_tech, col_inst = st.columns([1, 1], gap="medium")
    
    with col_tech:
        st.markdown("##### 📊 টেকনিক্যাল ও ট্রেন্ড ফিল্টার")
        c1, c2 = st.columns(2)
        with c1:
            sma_choice = st.selectbox("মুভিং এভারেজ (SMA)", [50, 200], index=1)
        with c2:
            timeframe = st.selectbox("টাইমফ্রেম", ["1d", "4h"], index=0)
        
        max_dist = st.slider("SMA থেকে সর্বোচ্চ সাপোর্ট দূরত্ব (%)", min_value=1.0, max_value=15.0, value=6.0, step=0.5)

    with col_inst:
        st.markdown("##### 🔥 প্রাতিষ্ঠানিক লিডিং সিগন্যাল")
        enable_compression = st.checkbox("৩-দিনের ভোলাটিলিটি কম্প্রেশন ফিল্টার", value=True)
        if enable_compression:
            max_compression_range = st.slider("সর্বোচ্চ ৩-দিনের রেঞ্জ (%)", 5.0, 25.0, 18.0, 1.0)
        else:
            max_compression_range = 100.0

        enable_volume_surge = st.checkbox("৪-ঘণ্টার ভলিউম সার্জ ফিল্টার", value=True)
        if enable_volume_surge:
            min_vol_surge = st.slider("ন্যূনতম ভলিউম গুণক (x)", 1.0, 3.0, 1.3, 0.1)
        else:
            min_vol_surge = 0.0

        enable_oi_check = st.checkbox("২৪ ঘণ্টার ওপেন ইন্টারেস্ট (OI) বৃদ্ধি ট্র্যাকার", value=True)

# মেইন পেজ স্ক্যান বাটন
st.markdown("<br>", unsafe_allow_html=True)
scan_triggered = st.button("🚀 স্ক্যান শুরু করুন (Run Full Market Scan)", use_container_width=True, type="primary")

# ========================================================
# ব্যাকএন্ড ডেটা ফেচিং ফাংশনসমূহ
# ========================================================
@st.cache_data(ttl=1800)
def get_all_futures_symbols():
    """বাইনান্সের সক্রিয় পেয়ার সংগ্রহ"""
    sources = [
        "https://data-api.binance.vision/api/v3/exchangeInfo",
        "https://fapi.binance.com/fapi/v1/exchangeInfo"
    ]
    for url in sources:
        try:
            r = session.get(url, timeout=6)
            if r.status_code == 200:
                data = r.json()
                symbols = [
                    s['symbol'] for s in data.get('symbols', [])
                    if s['symbol'].endswith('USDT') 
                    and not s['symbol'].startswith('1000')
                    and s.get('status') == 'TRADING'
                ]
                if len(symbols) > 50:
                    return sorted(list(set(symbols)))
        except Exception:
            continue
    return []

@st.cache_data(ttl=3600)
def get_global_market_assets():
    """CoinGecko ও CoinCap থেকে ক্রিপ্টো মেটাডাটা ক্যাশ করা"""
    cache_map = {}
    for page in [1, 2, 3]:
        try:
            cg_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page={page}&sparkline=false"
            r = session.get(cg_url, timeout=5)
            if r.status_code == 200:
                for item in r.json():
                    sym = item.get('symbol', '').upper()
                    if sym:
                        cache_map[sym] = {
                            'id': item.get('id'),
                            'supply': item.get('circulating_supply'),
                            'maxSupply': item.get('max_supply') or item.get('total_supply')
                        }
        except Exception:
            pass

    try:
        cc_url = "https://api.coincap.io/v2/assets?limit=1000"
        r2 = session.get(cc_url, timeout=5)
        if r2.status_code == 200:
            for item in r2.json().get('data', []):
                sym = item.get('symbol', '').upper()
                if sym and sym not in cache_map:
                    cache_map[sym] = {
                        'id': item.get('id'),
                        'supply': float(item.get('supply') or 0),
                        'maxSupply': float(item.get('maxSupply') or 0)
                    }
    except Exception:
        pass
        
    return cache_map

def extract_tokenomics(clean_sym, market_cache):
    item = market_cache.get(clean_sym)
    slug = clean_sym.lower()
    
    if item:
        slug = item.get('id') or clean_sym.lower()
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
                    "Unlock_Status": f"{status} ({circ_pct}%)",
                    "slug": slug
                }
            elif supply > 0:
                return {
                    "Circulating": f"{round(supply/1e6, 2)}M",
                    "Total_Supply": "Uncapped",
                    "Circ_%": "N/A",
                    "Unlock_Status": "🟢 No Hard Cap",
                    "slug": slug
                }
        except Exception:
            pass

    return {
        "Circulating": "N/A",
        "Total_Supply": "N/A",
        "Circ_%": "N/A",
        "Unlock_Status": "ℹ️ Check Details",
        "slug": slug
    }

def get_oi_growth(symbol):
    """২৪ ঘণ্টার ওপেন ইন্টারেস্ট গ্রোথ হিসাব"""
    url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=4h&limit=7"
    try:
        req = session.get(url, timeout=2.0)
        if req.status_code == 200:
            data = req.json()
            if isinstance(data, list) and len(data) >= 2:
                initial_oi = float(data[0].get("sumOpenInterestValue", 0))
                current_oi = float(data[-1].get("sumOpenInterestValue", 0))
                if initial_oi > 0:
                    return ((current_oi - initial_oi) / initial_oi) * 100
    except Exception:
        pass
    return 0.0

def get_klines_data(symbol, interval, limit):
    """ক্যান্ডেলস্টিক ডেটা ফেচিং"""
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        r = session.get(url, timeout=2.5)
        if r.status_code == 200:
            res = r.json()
            if isinstance(res, list) and len(res) >= 20:
                df = pd.DataFrame(res, columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_base_vol", "taker_quote_vol", "ignore"
                ])
                for col in ["open", "high", "low", "close", "volume"]:
                    df[col] = df[col].astype(float)
                return df
    except Exception:
        pass
    return None

def check_institutional_setup(symbol, sma_period, interval, max_distance):
    """SMA Retest + 3D Compression + 4H Volume Surge ইন্টিগ্রেটেড ফিল্টার"""
    df = get_klines_data(symbol, interval=interval, limit=sma_period + 30)
    if df is None:
        return None

    df['sma'] = df['close'].rolling(window=sma_period).mean()
    current_close = df['close'].iloc[-1]
    current_low = df['low'].iloc[-1]
    current_sma = df['sma'].iloc[-1]
    
    if pd.isna(current_sma) or current_close < current_sma:
        return None
        
    dist_pct = ((current_close - current_sma) / current_sma) * 100
    retesting = (dist_pct <= max_distance) or (current_low <= current_sma and current_close >= current_sma)
    if not retesting:
        return None
        
    was_below = any(df['close'].iloc[-i] < df['sma'].iloc[-i] for i in range(2, 8))
    if not was_below:
        return None

    # ৩-দিনের কম্প্রেশন ফিল্টার
    df_1d = df if interval == "1d" else get_klines_data(symbol, interval="1d", limit=10)
    range_3d = 0.0
    if df_1d is not None and len(df_1d) >= 3:
        high_3d = df_1d["high"].tail(3).max()
        low_3d = df_1d["low"].tail(3).min()
        range_3d = ((high_3d - low_3d) / current_close) * 100
        if enable_compression and range_3d > max_compression_range:
            return None

    # ৪-ঘণ্টার ভলিউম সার্জ ফিল্টার
    df_4h = df if interval == "4h" else get_klines_data(symbol, interval="4h", limit=25)
    vol_surge_ratio = 1.0
    if df_4h is not None and len(df_4h) >= 20:
        df_4h["vol_sma"] = df_4h["volume"].rolling(20, min_periods=5).mean()
        last_4h = df_4h.iloc[-1]
        avg_vol = last_4h["vol_sma"]
        current_vol = last_4h["volume"]
        vol_surge_ratio = (current_vol / avg_vol) if avg_vol > 0 else 1.0
        is_green = last_4h["close"] >= last_4h["open"]

        if enable_volume_surge:
            if not (is_green and vol_surge_ratio >= min_vol_surge):
                return None

    # ওপেন ইন্টারেস্ট গ্রোথ
    oi_pct = get_oi_growth(symbol) if enable_oi_check else 0.0

    clean_name = symbol.replace("USDT", "")
    category = SECTOR_MAP.get(clean_name, "🌐 Ecosystem")
    coinglass_url = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={clean_name}USDT"

    return {
        'Symbol': clean_name,
        'Category': category,
        'Price ($)': current_close,
        f'SMA_{sma_period}': round(current_sma, 4),
        'Distance (%)': f"{round(dist_pct, 2)}%",
        '3D Range (%)': f"{round(range_3d, 2)}%",
        '4H Vol Surge': f"{round(vol_surge_ratio, 2)}x",
        '24h OI Growth': f"{oi_pct:+.2f}%" if oi_pct != 0.0 else "N/A",
        'Heatmap Link': coinglass_url
    }

# ========================================================
# স্ক্যান প্রসেসিং ও রেজাল্ট ডিসপ্লে
# ========================================================
if scan_triggered:
    st.markdown("---")
    with st.spinner("মার্কেট ও গ্লোবাল টোকেনোমিক্স ডেটা সিঙ্ক করা হচ্ছে..."):
        symbols = get_all_futures_symbols()
        market_cache = get_global_market_assets()
        
    if not symbols:
        st.error("⚠️ পেয়ার লিস্ট লোড করা সম্ভব হয়নি।")
    else:
        st.info(f"বাইনান্স থেকে সফলভাবে {len(symbols)}টি সক্রিয় পেয়ার লোড হয়েছে। নির্বাচিত ফিল্টারে স্ক্যানিং চলছে...")
        
        progress = st.progress(0)
        status_label = st.empty()
        matched_data = []
        
        for idx, sym in enumerate(symbols):
            progress.progress((idx + 1) / len(symbols))
            clean_sym = sym.replace("USDT", "")
            status_label.text(f"স্ক্যান হচ্ছে [{idx+1}/{len(symbols)}]: {clean_sym}")
            
            match = check_institutional_setup(sym, sma_choice, timeframe, max_dist)
            if match:
                tokenomics = extract_tokenomics(clean_sym, market_cache)
                slug_val = tokenomics.pop('slug', clean_sym.lower())
                arkham_url = f"https://arkm.com/explorer/token/{slug_val}"
                
                match.update(tokenomics)
                match['Arkham Link'] = arkham_url
                matched_data.append(match)
                
            time.sleep(0.01)
            
        progress.empty()
        status_label.empty()
        
        if matched_data:
            st.success(f"🎉 স্ক্যান সম্পন্ন! মোট {len(matched_data)}টি পেয়ার শর্ত পূরণ করেছে।")
            df_result = pd.DataFrame(matched_data)
            
            cols = [
                'Symbol', 'Category', 'Price ($)', f'SMA_{sma_choice}', 'Distance (%)', 
                '3D Range (%)', '4H Vol Surge', '24h OI Growth',
                'Heatmap Link', 'Arkham Link',
                'Circulating', 'Total_Supply', 'Circ_%', 'Unlock_Status'
            ]
            available_cols = [c for c in cols if c in df_result.columns]
            df_result = df_result[available_cols]

            st.dataframe(
                df_result,
                column_config={
                    "Heatmap Link": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
                    "Arkham Link": st.column_config.LinkColumn("Arkham Intelligence", display_text="Open Arkham")
                },
                use_container_width=True,
                hide_index=True
            )
            
            csv_file = df_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 সম্পূর্ণ CSV রিপোর্ট ডাউনলোড",
                data=csv_file,
                file_name=f"mobin_crypto_institutional_{sma_choice}sma_report.csv",
                mime="text/csv"
            )
        else:
            st.warning(f"বর্তমান ফিল্টারে (SMA Retest + 3D Compression + Vol Surge) কোনো কয়েন মেলেনি। উপরের প্যানেল থেকে সেটিংস সামান্য অ্যাডজাস্ট করে আবার স্ক্যান দিন।")

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
