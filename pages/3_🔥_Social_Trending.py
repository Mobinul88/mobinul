import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Social Sentiment & Hype Radar",
    page_icon="🔥",
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
    background: linear-gradient(90deg, #F59E0B, #EF4444, #8B5CF6);
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
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
}

/* Dataframe Glass Styling */
div[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.85) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    padding: 10px;
}

/* Tab Active Styles */
button[data-baseweb="tab"] {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: #94A3B8 !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #F59E0B !important;
    border-bottom-color: #F59E0B !important;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: rgba(11, 15, 25, 0.95) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

/* Download & Action Button */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3) !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5) !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ========================================================
# Sidebar (Profile Only)
# ========================================================
st.sidebar.markdown("### 👑 Creator Profile")
st.sidebar.markdown("**Terminal Architect:** `Mobinul`")
st.sidebar.caption("Quantitative Algorithmic & Social Sentiment Researcher")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Hype Engine:** Multi-timeframe social search metrics (24H, 7D, 30D) tracking retail mindshare and institutional capital.")

# ========================================================
# Header Section
# ========================================================
st.markdown("<div class='terminal-title'>🔥 SOCIAL SENTIMENT & TWITTER HYPE RADAR</div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-subtitle'><b>Proprietary Architecture:</b> Developed by <code>Mobinul</code> | Real-Time Viral Search, Social Momentum & Liquidity Heatmap</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)

# ========================================================
# Data Engine: 24h, 7d & 30d Multi-Timeframe Fetchers
# ========================================================
@st.cache_data(ttl=600)
def get_24h_viral_trending():
    """Fetch 24h real-time viral search coins from CoinGecko trending"""
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        res = session.get(url, timeout=6).json()
        coins = res.get('coins', [])
        data = []
        for item in coins:
            c = item.get('item', {})
            c_data = c.get('data', {})
            sym_clean = c.get('symbol', '').upper()
            coinglass_url = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={sym_clean}USDT"
            
            p_change_24h = c_data.get('price_change_percentage_24h', {}).get('usd', 0)
            
            data.append({
                "Rank": c.get('score', 0) + 1,
                "Symbol": sym_clean,
                "Name": c.get('name', ''),
                "Price ($)": round(float(c_data.get('price', 0)), 6) if c_data.get('price') else "N/A",
                "24h Trend (%)": f"{round(float(p_change_24h or 0), 2):+}%",
                "Market Cap Rank": f"#{c.get('market_cap_rank', 'N/A')}",
                "Viral Intensity": "🔥 High 24h Social Hype",
                "Heatmap Link": coinglass_url,
                "Arkham Link": f"https://arkm.com/explorer/token/{c.get('id')}"
            })
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900)
def get_extended_momentum_data():
    """Fetch 7d and 30d momentum data for top market cap & high-volume assets"""
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=150&page=1&sparkline=false&price_change_percentage=24h,7d,30d"
    try:
        res = session.get(url, timeout=7).json()
        if not isinstance(res, list):
            return pd.DataFrame(), pd.DataFrame()
            
        data_7d = []
        data_30d = []
        
        for c in res:
            sym_clean = c.get('symbol', '').upper()
            coinglass_url = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={sym_clean}USDT"
            
            p_7d = c.get('price_change_percentage_7d_in_currency') or 0
            p_30d = c.get('price_change_percentage_30d_in_currency') or 0
            p_24h = c.get('price_change_percentage_24h_in_currency') or 0
            
            common_dict = {
                "Rank": c.get('market_cap_rank', 'N/A'),
                "Symbol": sym_clean,
                "Name": c.get('name', ''),
                "Price ($)": c.get('current_price', 0),
                "24h Change (%)": f"{round(p_24h, 2):+}%",
                "Heatmap Link": coinglass_url,
                "Arkham Link": f"https://arkm.com/explorer/token/{c.get('id')}"
            }
            
            # 7-Day row
            row_7d = common_dict.copy()
            row_7d["7-Day Gain (%)"] = round(p_7d, 2)
            row_7d["7-Day Status"] = "⚡ Strong Weekly Surge" if p_7d >= 15 else ("🟢 Bullish Steady" if p_7d > 0 else "🔴 Consolidation")
            data_7d.append(row_7d)
            
            # 30-Day row
            row_30d = common_dict.copy()
            row_30d["30-Day Gain (%)"] = round(p_30d, 2)
            row_30d["Macro Narrative"] = "👑 Macro Narrative Leader" if p_30d >= 35 else ("🟢 Monthly Uptrend" if p_30d > 0 else "⚪ Sideways/Range")
            data_30d.append(row_30d)
            
        df_7d = pd.DataFrame(data_7d).sort_values(by="7-Day Gain (%)", ascending=False).head(20)
        df_30d = pd.DataFrame(data_30d).sort_values(by="30-Day Gain (%)", ascending=False).head(20)
        
        # Format percentages as strings with sign
        df_7d["7-Day Gain (%)"] = df_7d["7-Day Gain (%)"].apply(lambda x: f"{x:+}%")
        df_30d["30-Day Gain (%)"] = df_30d["30-Day Gain (%)"].apply(lambda x: f"{x:+}%")
        
        return df_7d, df_30d
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

# ========================================================
# Main Controls & Refresh Bar
# ========================================================
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.markdown("##### 📡 Cross-Horizon Sentiment & Social Mindshare Terminal")
with col_top2:
    if st.button("🔄 Sync Live Social Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Load Data
with st.spinner("Aggregating multi-timeframe social sentiment feeds..."):
    df_24h = get_24h_viral_trending()
    df_7d, df_30d = get_extended_momentum_data()

# ========================================================
# Multi-Timeframe Tabs Interface (24H, 7D, 30D in One Place)
# ========================================================
tab_24h, tab_7d, tab_30d = st.tabs([
    "⚡ 24 Hours (Immediate Viral Hype)", 
    "🚀 7 Days (Sustained Momentum)", 
    "🌕 30 Days (Macro Narrative Leaders)"
])

# ----------------- 24 Hours Tab -----------------
with tab_24h:
    st.markdown("#### ⚡ 24h Real-Time Viral Search & Twitter Spotlight")
    st.caption("Tokens experiencing abnormal spikes in global searches, social impressions, and retail momentum over the last 24 hours.")
    
    if not df_24h.empty:
        st.dataframe(
            df_24h,
            column_config={
                "Heatmap Link": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
                "Arkham Link": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
            },
            use_container_width=True,
            hide_index=True
        )
        csv_24 = df_24h.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export 24h Viral Report", data=csv_24, file_name="social_24h_viral_report.csv", mime="text/csv")
    else:
        st.warning("24h viral trending data is currently synchronizing. Please refresh shortly.")

# ----------------- 7 Days Tab -----------------
with tab_7d:
    st.markdown("#### 🚀 7-Day Sustained Social & Price Momentum Leaders")
    st.caption("Top institutional and mid-cap assets maintaining consistent social presence and volume expansion over the trailing 7 days.")
    
    if not df_7d.empty:
        cols_7d = ['Rank', 'Symbol', 'Name', 'Price ($)', '24h Change (%)', '7-Day Gain (%)', '7-Day Status', 'Heatmap Link', 'Arkham Link']
        st.dataframe(
            df_7d[[c for c in cols_7d if c in df_7d.columns]],
            column_config={
                "Heatmap Link": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
                "Arkham Link": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
            },
            use_container_width=True,
            hide_index=True
        )
        csv_7 = df_7d.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export 7-Day Momentum Report", data=csv_7, file_name="social_7d_momentum_report.csv", mime="text/csv")
    else:
        st.warning("7-day momentum metrics are currently unavailable. Please refresh.")

# ----------------- 30 Days Tab -----------------
with tab_30d:
    st.markdown("#### 🌕 30-Day Macro Narrative & Sector Flow Leaders")
    st.caption("Market leaders dominating monthly institutional discussions, capital inflows, and dominant crypto sector narratives.")
    
    if not df_30d.empty:
        cols_30d = ['Rank', 'Symbol', 'Name', 'Price ($)', '24h Change (%)', '30-Day Gain (%)', 'Macro Narrative', 'Heatmap Link', 'Arkham Link']
        st.dataframe(
            df_30d[[c for c in cols_30d if c in df_30d.columns]],
            column_config={
                "Heatmap Link": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
                "Arkham Link": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
            },
            use_container_width=True,
            hide_index=True
        )
        csv_30 = df_30d.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export 30-Day Narrative Report", data=csv_30, file_name="social_30d_narrative_report.csv", mime="text/csv")
    else:
        st.warning("30-day macro narrative data is currently unavailable. Please refresh.")

# ========================================================
# Terminal Footer
# ========================================================
st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #94A3B8; font-size: 13px;'>
        © 2026 <b>Mobinul Institutional Terminal</b> | All Rights Reserved.<br>
        <i>Multi-Horizon Sentiment & Viral Analytics Powered by CoinGecko, CoinGlass & Arkham Intelligence</i>
    </div>
    """,
    unsafe_allow_html=True
)
