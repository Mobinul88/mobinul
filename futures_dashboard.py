import streamlit as st
import pandas as pd
import requests
import time
import os

LOGO_PATH = "logo.png"
has_custom_logo = os.path.exists(LOGO_PATH)

st.set_page_config(
    page_title="Mobin's Institutional Crypto Terminal",
    page_icon=LOGO_PATH if has_custom_logo else "🚀",
    layout="wide"
)

# ========================================================
# 🎨 Professional Dark Cyberpunk Glassmorphic Theme
# ========================================================
CUSTOM_CSS = """
<style>
/* Darken top Streamlit header bar */
header[data-testid="stHeader"] {
    background-color: rgba(10, 15, 29, 0.95) !important;
}

/* Full Page Background with Overlay */
.stApp {
    background: linear-gradient(rgba(10, 15, 29, 0.90), rgba(10, 15, 29, 0.96)),
                url('https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2000&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #F8FAFC !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Global Text and Label Contrast */
label, p, span, .stMarkdown, h1, h2, h3, h4, h5, h6 {
    color: #F8FAFC !important;
}

/* Frosted Glass Panels */
.glass-panel {
    background: rgba(17, 24, 39, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
}

/* Header Glowing Gradient Title */
.terminal-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #F59E0B, #10B981, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}

.terminal-subtitle {
    font-size: 0.95rem;
    color: #CBD5E1 !important;
    margin-top: -6px;
}

/* Dropdown Inputs Styling */
div[data-baseweb="select"] {
    background-color: rgba(30, 41, 59, 0.9) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}

div[data-baseweb="select"] * {
    color: #FFFFFF !important;
}

/* Action Execution Button */
.stButton > button {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
    color: #000000 !important;
    font-weight: 800 !important;
    font-size: 1.15rem !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 14px 28px !important;
    box-shadow: 0 4px 20px rgba(245, 158, 11, 0.4) !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 28px rgba(245, 158, 11, 0.6) !important;
    background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%) !important;
}

/* Dataframe Glass Styling */
div[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.85) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    padding: 10px;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: rgba(11, 15, 25, 0.95) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)

# Predefined Sector Mapping
SECTOR_MAP = {
    'FET': '🤖 AI / Data', 'NEAR': '🤖 AI / L1', 'RNDR': '🤖 AI / GPU', 'RENDER': '🤖 AI / GPU',
    'TAO': '🤖 AI', 'WLD': '🤖 AI / Identity', 'AGIX': '🤖 AI', 'ARKM': '🤖 AI / Intel',
    'OCEAN': '🤖 AI / Data', 'GRT': '🤖 AI / Indexing', 'IO': '🤖 AI / Compute',

    'ONDO': '🏛️ RWA', 'LINK': '🏛️ Oracle / RWA', 'PENDLE': '🏛️ RWA / Yield',
    'MKR': '🏛️ RWA / DeFi', 'CFG': '🏛️ RWA', 'TRU': '🏛️ RWA', 'POLYX': '🏛️ RWA',

    'BTC': '🧱 Layer 1', 'ETH': '🧱 Layer 1', 'SOL': '🧱 Layer 1', 'BNB': '🧱 Layer 1',
    'SUI': '🧱 Layer 1', 'SEI': '🧱 Layer 1', 'AVAX': '🧱 Layer 1', 'ATOM': '🧱 Layer 1',
    'ADA': '🧱 Layer 1', 'DOT': '🧱 Layer 1', 'KAS': '🧱 Layer 1', 'ALGO': '🧱 Layer 1',
    'FTM': '🧱 Layer 1', 'INJ': '🧱 Layer 1 / DeFi', 'APT': '🧱 Layer 1', 'TON': '🧱 Layer 1',

    'ARB': '⚡ Layer 2', 'OP': '⚡ Layer 2', 'MATIC': '⚡ Layer 2', 'POL': '⚡ Layer 2',
    'STRK': '⚡ Layer 2', 'MANTA': '⚡ Layer 2', 'METIS': '⚡ Layer 2', 'BLAST': '⚡ Layer 2',
    'ZK': '⚡ Layer 2 (ZK)', 'IMX': '⚡ Layer 2 / Gaming',

    'UNI': '🔄 DeFi', 'AAVE': '🔄 DeFi / Lending', 'CRV': '🔄 DeFi', 'DYDX': '🔄 DeFi / Perp',
    'SNX': '🔄 DeFi', 'CAKE': '🔄 DeFi', 'JUP': '🔄 DeFi / Solana', 'RAY': '🔄 DeFi / Solana',
    'COMP': '🔄 DeFi', 'SUSHI': '🔄 DeFi', '1INCH': '🔄 DeFi', 'LDO': '🔄 Liquid Staking',

    'DOGE': '🐶 Meme', 'SHIB': '🐶 Meme', 'PEPE': '🐶 Meme', 'WIF': '🐶 Meme',
    'BONK': '🐶 Meme', 'FLOKI': '🐶 Meme', 'BOME': '🐶 Meme', 'MEME': '🐶 Meme',

    'GALA': '🎮 Gaming', 'AXS': '🎮 Gaming', 'SAND': '🎮 Metaverse', 'MANA': '🎮 Metaverse',
    'BEAM': '🎮 Gaming', 'PIXEL': '🎮 Gaming', 'NOT': '🎮 Web3 Gaming',

    'FIL': '📦 DePIN / Storage', 'AR': '📦 Storage', 'HNT': '📡 DePIN', 'THETA': '📡 DePIN / Video'
}

# ========================================================
# Sidebar Configuration
# ========================================================
st.sidebar.markdown("### 👑 Creator Profile")
if has_custom_logo:
    st.sidebar.image(LOGO_PATH, width=120)

st.sidebar.markdown("**Terminal Architect:** `Mobinul`")
st.sidebar.caption("Quantitative Algorithmic & On-Chain Researcher")
st.sidebar.markdown("---")
st.sidebar.info("💡 **System Note:** All institutional technical & leading indicators are managed from the main terminal console.")

# ========================================================
# Terminal Header
# ========================================================
col_head1, col_head2 = st.columns([1, 8])
with col_head1:
    if has_custom_logo:
        st.image(LOGO_PATH, width=80)
    else:
        st.markdown("<h1 style='font-size: 3rem;'>⚡</h1>", unsafe_allow_html=True)

with col_head2:
    st.markdown("<div class='terminal-title'>BINANCE FUTURES INTELLIGENCE TERMINAL</div>", unsafe_allow_html=True)
    st.markdown("<div class='terminal-subtitle'><b>Proprietary Architecture:</b> Developed by <code>Mobinul</code> | Powered by Binance Futures, CoinGlass & Arkham</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========================================================
# Main Controls Dashboard (Glassmorphic Grid)
# ========================================================
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.markdown("""
        <div class='glass-panel'>
            <h4 style='color: #38BDF8; margin-top: 0;'>📊 Technical Trend Configuration</h4>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        sma_choice = st.selectbox("Moving Average (SMA)", [50, 200], index=0)
    with c2:
        timeframe = st.selectbox("Execution Timeframe", ["1d", "4h"], index=0)
    
    max_dist = st.slider("Max Distance from Support SMA (%)", min_value=1.0, max_value=25.0, value=10.0, step=0.5)

with col_right:
    st.markdown("""
        <div class='glass-panel'>
            <h4 style='color: #F59E0B; margin-top: 0;'>🔥 Institutional Leading Signals</h4>
        </div>
    """, unsafe_allow_html=True)
    
    enable_compression = st.checkbox("3-Day Volatility Squeeze Filter", value=True)
    if enable_compression:
        max_compression_range = st.slider("Max 3-Day Squeeze Range (%)", 5.0, 30.0, 18.0, 1.0)
    else:
        max_compression_range = 100.0

    enable_volume_surge = st.checkbox("4-Hour Volume Surge Filter", value=True)
    if enable_volume_surge:
        min_vol_surge = st.slider("Min Relative Volume Multiplier (x)", 1.0, 3.0, 1.2, 0.1)
    else:
        min_vol_surge = 0.0

    enable_oi_check = st.checkbox("Track 24h Open Interest (OI) Growth", value=True)

# Scan Execution Button
st.markdown("<br>", unsafe_allow_html=True)
scan_triggered = st.button("🚀 EXECUTE FULL MARKET SCAN", use_container_width=True)

# ========================================================
# Backend Market Data Fetchers
# ========================================================
@st.cache_data(ttl=1800)
def get_all_futures_symbols():
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
    url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=4h&limit=7"
    try:
        req = session.get(url, timeout=1.8)
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
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        r = session.get(url, timeout=2.2)
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
    """Institutional breakout setup check"""
    df = get_klines_data(symbol, interval=interval, limit=sma_period + 30)
    if df is None:
        return None

    df['sma'] = df['close'].rolling(window=sma_period).mean()
    current_close = df['close'].iloc[-1]
    current_sma = df['sma'].iloc[-1]
    
    # 1. Bullish structural filter (Close must hold above SMA)
    if pd.isna(current_sma) or current_close < current_sma:
        return None
        
    dist_pct = ((current_close - current_sma) / current_sma) * 100
    if dist_pct > max_distance:
        return None

    # 2. 3-Day Volatility Contraction Filter
    df_1d = df if interval == "1d" else get_klines_data(symbol, interval="1d", limit=10)
    range_3d = 0.0
    if df_1d is not None and len(df_1d) >= 3:
        high_3d = df_1d["high"].tail(3).max()
        low_3d = df_1d["low"].tail(3).min()
        range_3d = ((high_3d - low_3d) / current_close) * 100
        if enable_compression and range_3d > max_compression_range:
            return None

    # 3. 4-Hour Volume Surge Filter
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

    # 4. Open Interest Growth Tracker
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
# Execution & Result Output
# ========================================================
if scan_triggered:
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    with st.spinner("Synchronizing Binance Futures & Institutional Feeds..."):
        symbols = get_all_futures_symbols()
        market_cache = get_global_market_assets()
        
    if not symbols:
        st.error("⚠️ Failed to load active pairs from Binance API.")
    else:
        st.info(f"Loaded {len(symbols)} active pairs. Initiating institutional scanning engine...")
        
        progress = st.progress(0)
        status_label = st.empty()
        matched_data = []
        
        for idx, sym in enumerate(symbols):
            progress.progress((idx + 1) / len(symbols))
            clean_sym = sym.replace("USDT", "")
            status_label.text(f"Analyzing [{idx+1}/{len(symbols)}]: {clean_sym}")
            
            match = check_institutional_setup(sym, sma_choice, timeframe, max_dist)
            if match:
                tokenomics = extract_tokenomics(clean_sym, market_cache)
                slug_val = tokenomics.pop('slug', clean_sym.lower())
                arkham_url = f"https://arkm.com/explorer/token/{slug_val}"
                
                match.update(tokenomics)
                match['Arkham Link'] = arkham_url
                matched_data.append(match)
                
            time.sleep(0.005)
            
        progress.empty()
        status_label.empty()
        
        if matched_data:
            st.success(f"🎉 Scan Completed! Identified {len(matched_data)} high-probability institutional setups.")
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
                label="📥 Download Full Institutional CSV Report",
                data=csv_file,
                file_name=f"mobin_institutional_{sma_choice}sma_report.csv",
                mime="text/csv"
            )
        else:
            st.warning("No pairs met the current institutional filters. Consider slightly adjusting the SMA distance or volume multiplier above.")

st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #94A3B8; font-size: 13px;'>
        © 2026 <b>Mobinul Institutional Terminal</b> | All Rights Reserved.<br>
        <i>Institutional High-Frequency Data Engine Powered by Binance API</i>
    </div>
    """,
    unsafe_allow_html=True
)
