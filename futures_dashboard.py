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

# হেডার ব্র্যান্ডিং
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if has_custom_logo:
        st.image(LOGO_PATH, width=95)
    else:
        st.markdown("# 🚀")

with col_title:
    st.title("বাইনান্স ফিউচার্স ইন্টেলিজেন্স টার্মিনাল")
    st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *Powered by Binance & Institutional Metrics*")

st.divider()

# সাইডবার সেটিংস
st.sidebar.markdown("### 👑 Creator Profile")
if has_custom_logo:
    st.sidebar.image(LOGO_PATH, width=120)

st.sidebar.markdown("**Created by:** Mobinul")
st.sidebar.caption("Crypto Algorithmic & On-Chain Researcher")
st.sidebar.markdown("---")

st.sidebar.header("⚙️ স্ক্যান সেটিংস")
sma_choice = st.sidebar.selectbox("মুভিং এভারেজ নির্বাচন করুন", [50, 200], index=1)
timeframe = st.sidebar.selectbox("টাইমফ্রেম", ["1d", "4h"], index=0)
max_dist = st.sidebar.slider("SMA থেকে সর্বোচ্চ দূরত্ব (%)", min_value=1.0, max_value=15.0, value=6.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.header("🔥 প্রাতিষ্ঠানিক লিডিং ফিল্টার")
enable_compression = st.sidebar.checkbox("৩-দিনের ভোলাটিলিটি কম্প্রেশন ফিল্টার", value=True)
max_compression_range = st.sidebar.slider("সর্বোচ্চ ৩-দিনের রেঞ্জ (%)", 5.0, 25.0, 18.0, 1.0) if enable_compression else 100.0

enable_volume_surge = st.sidebar.checkbox("৪-ঘণ্টার ভলিউম সার্জ ফিল্টার", value=True)
min_vol_surge = st.sidebar.slider("ন্যূনতম ভলিউম গুণক (x)", 1.0, 3.0, 1.3, 0.1) if enable_volume_surge else 0.0

enable_oi_check = st.sidebar.checkbox("২৪ ঘণ্টার ওপেন ইন্টারেস্ট (OI) গ্রোথ ট্র্যাকার", value=True)

@st.cache_data(ttl=1800)
def get_all_futures_symbols():
    """বাইনান্সের সক্রিয় পারপেচুয়াল পেয়ার সংগ্রহ"""
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
    """CoinGecko ও CoinCap থেকে ক্রিপ্টো সাপ্লাই মেটাডাটা ক্যাশ করা"""
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
            if isinstance(data,
