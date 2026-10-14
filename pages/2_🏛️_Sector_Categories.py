import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Crypto Sector & Category Intelligence",
    page_icon="🏛️",
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

/* Glowing Title */
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

/* Frosted Glass Control Panel */
.glass-panel {
    background: rgba(17, 24, 39, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 22px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
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

/* Download Button Styling */
.stDownloadButton > button {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
    transition: all 0.3s ease !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #34D399 0%, #10B981 100%) !important;
    transform: translateY(-2px);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ========================================================
# Sidebar (Profile Only)
# ========================================================
st.sidebar.markdown("### 👑 Creator Profile")
st.sidebar.markdown("**Terminal Architect:** `Mobinul`")
st.sidebar.caption("Quantitative Algorithmic & Sector Flow Researcher")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Navigation Note:** Category selector and filters are integrated directly into the main dashboard panel.")

# ========================================================
# Header Section
# ========================================================
st.markdown("<div class='terminal-title'>🏛️ CRYPTO SECTOR & CATEGORY INTELLIGENCE</div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-subtitle'><b>Terminal Architect:</b> Developed by <code>Mobinul</code> | Market Capital Rotation & On-Chain Intelligence</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Predefined Top Cryptos per Sector
SECTOR_DATA = {
    "🤖 Artificial Intelligence (AI)": [
        "near-protocol", "render-token", "bittensor", "artificial-superintelligence-alliance", 
        "worldcoin-wld", "arkham", "the-graph", "io-net", "ocean-protocol"
    ],
    "🏛️ Real World Assets (RWA)": [
        "ondo-finance", "chainlink", "pendle", "maker", "centrifuge", "truefi", "polymath"
    ],
    "🧱 Layer 1 Blockchains": [
        "bitcoin", "ethereum", "solana", "binancecoin", "sui", "sei-network", 
        "avalanche-2", "cosmos", "cardano", "polkadot", "kaspa", "aptos", "injective-protocol"
    ],
    "⚡ Layer 2 Networks": [
        "arbitrum", "optimism", "polygon-ecosystem-token", "starknet", "manta-network", 
        "metis-token", "immutable-x"
    ],
    "🔄 Decentralized Finance (DeFi)": [
        "uniswap", "aave", "curve-dao-token", "dydx-chain", "synthetix-network-token", 
        "jupiter-exchange-solana", "raydium", "lido-dao"
    ],
    "🐶 Meme Tokens": [
        "dogecoin", "shiba-inu", "pepe", "dogwifcoin", "bonk", "floki"
    ],
    "📦 DePIN & Storage": [
        "filecoin", "arweave", "helium", "theta-token"
    ]
}

# ========================================================
# Main Page Control Dashboard (No Settings in Sidebar)
# ========================================================
st.markdown("""
    <div class='glass-panel'>
        <h4 style='color: #38BDF8; margin-top: 0; margin-bottom: 12px;'>🧭 Sector & Rotation Navigator</h4>
    </div>
""", unsafe_allow_html=True)

col_ctrl1, col_ctrl2 = st.columns([2, 1], gap="medium")

with col_ctrl1:
    selected_sector = st.selectbox(
        "Select Market Category / Sector:", 
        list(SECTOR_DATA.keys()), 
        index=0
    )

with col_ctrl2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    refresh_btn = st.button("🔄 Refresh Sector Metrics", use_container_width=True)

# ========================================================
# Data Engine
# ========================================================
@st.cache_data(ttl=900)
def fetch_sector_tokens(coin_ids):
    """Fetch live market metrics & tokenomics from CoinGecko"""
    ids_str = ",".join(coin_ids)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}&order=market_cap_desc&sparkline=false"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            raw_coins = r.json()
            formatted = []
            for c in raw_coins:
                circ = float(c.get('circulating_supply') or 0)
                total = float(c.get('max_supply') or c.get('total_supply') or 0)
                sym_clean = c.get('symbol', '').upper()
                
                if circ > 0 and total > 0:
                    circ_pct = round((circ / total) * 100, 2)
                    status = "🟢 Low Risk" if circ_pct >= 80 else ("🔴 High Dilution" if circ_pct <= 35 else "🟡 Moderate")
                    unlock_info = f"{status} ({circ_pct}%)"
                else:
                    circ_pct = "N/A"
                    unlock_info = "🟢 Uncapped / No Cap"

                coinglass_url = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={sym_clean}USDT"

                formatted.append({
                    "Rank": c.get('market_cap_rank', 'N/A'),
                    "Symbol": sym_clean,
                    "Name": c.get('name', ''),
                    "Price ($)": c.get('current_price', 0),
                    "24h Change (%)": f"{round(c.get('price_change_percentage_24h') or 0, 2)}%",
                    "Market Cap": f"${round((c.get('market_cap') or 0)/1e6, 2)}M",
                    "Circulating": f"{round(circ/1e6, 2)}M" if circ else "N/A",
                    "Total Supply": f"{round(total/1e6, 2)}M" if total else "N/A",
                    "Unlock Status": unlock_info,
                    "Heatmap Link": coinglass_url,
                    "Arkham Link": f"https://arkm.com/explorer/token/{c.get('id')}"
                })
            return pd.DataFrame(formatted)
    except Exception:
        pass
    return pd.DataFrame()

# ========================================================
# Result Display
# ========================================================
st.markdown(f"##### 📊 Active Category: `{selected_sector}` — Live Asset Analytics")

target_coins = SECTOR_DATA[selected_sector]
with st.spinner(f"Synchronizing live metrics for {selected_sector}..."):
    df_category = fetch_sector_tokens(target_coins)

if not df_category.empty:
    st.dataframe(
        df_category,
        column_config={
            "Heatmap Link": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
            "Arkham Link": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    # Download Button
    clean_filename = selected_sector.split(' ')[-1].replace('(', '').replace(')', '').lower()
    csv_data = df_category.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download {selected_sector} Institutional CSV Report",
        data=csv_data,
        file_name=f"{clean_filename}_sector_report.csv",
        mime="text/csv"
    )
else:
    st.warning("Unable to fetch category data at the moment. Please wait a few moments and refresh.")

st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #94A3B8; font-size: 13px;'>
        © 2026 <b>Mobinul Institutional Terminal</b> | All Rights Reserved.<br>
        <i>Sector Rotation & Categorical Intelligence Powered by CoinGecko, CoinGlass & Arkham</i>
    </div>
    """,
    unsafe_allow_html=True
)
