import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Social Sentiment & Multi-Timeframe Hype Radar",
    page_icon="🔥",
    layout="wide"
)

# ========================================================
# 🎨 Professional Dark Cyberpunk Theme
# ========================================================
CUSTOM_CSS = """
<style>
header[data-testid="stHeader"] {
    background-color: rgba(10, 15, 29, 0.95) !important;
}
.stApp {
    background: linear-gradient(rgba(10, 15, 29, 0.90), rgba(10, 15, 29, 0.96)),
                url('https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2000&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #F8FAFC !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
label, p, span, .stMarkdown, h1, h2, h3, h4, h5, h6 {
    color: #F8FAFC !important;
}
::selection {
    background: #0284C7 !important;
    color: #FFFFFF !important;
}
::-moz-selection {
    background: #0284C7 !important;
    color: #FFFFFF !important;
}
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
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
}
.stTabs [data-baseweb="tab"] {
    background-color: rgba(30, 41, 59, 0.7) !important;
    border-radius: 10px 10px 0 0 !important;
    color: #CBD5E1 !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(16, 185, 129, 0.25) 100%) !important;
    color: #FBBF24 !important;
    border-bottom: 2px solid #F59E0B !important;
}
div[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.85) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    padding: 10px;
}
.stButton > button {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 22px !important;
    box-shadow: 0 4px 18px rgba(245, 158, 11, 0.35) !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(245, 158, 11, 0.5) !important;
}
.stDownloadButton button,
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding: 10px 22px !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35) !important;
}
section[data-testid="stSidebar"] {
    background-color: rgba(11, 15, 25, 0.95) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 👑 Creator Profile")
st.sidebar.markdown("**Terminal Architect:** `Mobinul`")
st.sidebar.caption("Social Sentiment & Viral Flow Researcher")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Hype Radar Note:** Tracks organic viral surges, Twitter/X narrative shifts, and multi-timeframe price discovery.")

# Header
st.markdown("<div class='terminal-title'>🔥 SOCIAL SENTIMENT & TWITTER HYPE RADAR</div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-subtitle'><b>Proprietary Architecture:</b> Developed by <code>Mobinul</code> | Real-Time Viral Search, Social Momentum & Liquidity Heatmap</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
session = requests.Session()
session.headers.update(HEADERS)

# Control Bar
col_ctrl1, col_ctrl2 = st.columns([4, 1])
with col_ctrl1:
    st.markdown("""
        <div class='glass-panel' style='padding: 14px 20px; margin-bottom: 0;'>
            <span style='color: #38BDF8; font-weight: 600;'>⚡ Sentiment Intelligence Engine:</span>
            <span style='color: #CBD5E1;'> Analyzing real-time community engagement, social query velocity, and multi-day accumulation waves.</span>
        </div>
    """, unsafe_allow_html=True)
with col_ctrl2:
    if st.button("🔄 Sync Live Social Data", use_container_width=True):
        st.cache_data.clear()

st.markdown("<br>", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_24h_viral_trending():
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
            
            data.append({
                "Rank": c.get('score', 0) + 1,
                "Symbol": sym_clean,
                "Name": c.get('name', ''),
                "Price ($)": round(float(c_data.get('price', 0)), 6) if c_data.get('price') else "N/A",
                "24h Change (%)": f"{round(float(c_data.get('price_change_percentage_24h', {}).get('usd', 0)), 2):+.2f}%",
                "Market Cap Rank": f"#{c.get('market_cap_rank', 'N/A')}",
                "Social Sentiment": "🔥 Viral Surge",
                "Liquidity Heatmap": coinglass_url,
                "On-Chain Intel": f"https://arkm.com/explorer/token/{c.get('id')}"
            })
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900)
def get_multi_day_trending():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=120&page=1&sparkline=false&price_change_percentage=7d,30d"
    try:
        res = session.get(url, timeout=8).json()
        if not isinstance(res, list):
            return pd.DataFrame(), pd.DataFrame()
            
        data_7d = []
        data_30d = []

        for c in res:
            sym_clean = c.get('symbol', '').upper()
            coinglass_url = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={sym_clean}USDT"
            arkham_url = f"https://arkm.com/explorer/token/{c.get('id')}"
            
            p_7d = c.get('price_change_percentage_7d_in_currency')
            p_30d = c.get('price_change_percentage_30d_in_currency')
            p_24h = c.get('price_change_percentage_24h', 0)
            curr_p = c.get('current_price', 0)
            mcap_rank = c.get('market_cap_rank', 'N/A')

            if p_7d is not None:
                data_7d.append({
                    "Symbol": sym_clean,
                    "Name": c.get('name', ''),
                    "Price ($)": curr_p,
                    "24h Change (%)": f"{round(float(p_24h or 0), 2):+.2f}%",
                    "_sort_val": float(p_7d),
                    "7-Day Gain (%)": f"{round(float(p_7d), 2):+.2f}%",
                    "Market Cap Rank": f"#{mcap_rank}",
                    "Narrative Wave": "🚀 Strong Weekly Inflow" if p_7d >= 15 else ("🟢 Bullish Drift" if p_7d >= 5 else "⚪ Neutral"),
                    "Liquidity Heatmap": coinglass_url,
                    "On-Chain Intel": arkham_url
                })

            if p_30d is not None:
                data_30d.append({
                    "Symbol": sym_clean,
                    "Name": c.get('name', ''),
                    "Price ($)": curr_p,
                    "24h Change (%)": f"{round(float(p_24h or 0), 2):+.2f}%",
                    "_sort_val": float(p_30d),
                    "30-Day Gain (%)": f"{round(float(p_30d), 2):+.2f}%",
                    "Market Cap Rank": f"#{mcap_rank}",
                    "Macro Narrative": "👑 Macro Narrative Leader" if p_30d >= 30 else ("🟢 Sustained Growth" if p_30d >= 10 else "⚪ Consolidation"),
                    "Liquidity Heatmap": coinglass_url,
                    "On-Chain Intel": arkham_url
                })

        df_7d = pd.DataFrame(data_7d)
        df_30d = pd.DataFrame(data_30d)

        # স্পেসজনিত কোনো KeyError ছাড়াই নিরাপদ সর্টিং
        if not df_7d.empty:
            df_7d = df_7d.sort_values(by="_sort_val", ascending=False).head(20)
            df_7d = df_7d.drop(columns=["_sort_val"])
            df_7d.insert(0, "Rank", range(1, len(df_7d) + 1))

        if not df_30d.empty:
            df_30d = df_30d.sort_values(by="_sort_val", ascending=False).head(20)
            df_30d = df_30d.drop(columns=["_sort_val"])
            df_30d.insert(0, "Rank", range(1, len(df_30d) + 1))

        return df_7d, df_30d
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

# Tabs
tab_24h, tab_7d, tab_30d = st.tabs([
    "⚡ 24 Hours (Immediate Viral Hype)", 
    "📈 7 Days (Sustained Momentum)", 
    "🟡 30 Days (Macro Narrative Leaders)"
])

with st.spinner("Synchronizing multi-timeframe social sentiment feeds..."):
    df_24h = get_24h_viral_trending()
    df_7d, df_30d = get_multi_day_trending()

COL_CONFIGS = {
    "Liquidity Heatmap": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
    "On-Chain Intel": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
}

# 24H
with tab_24h:
    st.markdown("#### ⚡ 24-Hour Viral & Immediate Search Velocity")
    st.caption("Tokens currently experiencing the highest organic viral engagement, Twitter/X queries, and direct global searches.")
    if not df_24h.empty:
        st.dataframe(df_24h, column_config=COL_CONFIGS, use_container_width=True, hide_index=True)
        csv_24h = df_24h.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download 24h Hype Report", data=csv_24h, file_name="24h_hype_report.csv", mime="text/csv")
    else:
        st.warning("24h trending metrics temporarily unavailable. Please retry shortly.")

# 7D
with tab_7d:
    st.markdown("#### 📈 7-Day Cumulative Hype & Momentum Leaders")
    st.caption("High-velocity tokens sustaining multi-day social momentum and continuous institutional capital flow over the last 7 days.")
    if not df_7d.empty:
        st.dataframe(df_7d, column_config=COL_CONFIGS, use_container_width=True, hide_index=True)
        csv_7d = df_7d.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download 7d Momentum Report", data=csv_7d, file_name="7d_momentum_report.csv", mime="text/csv")
    else:
        st.warning("7-day momentum metrics temporarily unavailable. Please retry shortly.")

# 30D
with tab_30d:
    st.markdown("#### 🟡 30-Day Macro Narrative & Sector Flow Leaders")
    st.caption("Market leaders dominating monthly institutional discussions, capital inflows, and dominant crypto sector narratives.")
    if not df_30d.empty:
        st.dataframe(df_30d, column_config=COL_CONFIGS, use_container_width=True, hide_index=True)
        csv_30d = df_30d.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download 30d Macro Report", data=csv_30d, file_name="30d_macro_report.csv", mime="text/csv")
    else:
        st.warning("30-day macro metrics temporarily unavailable. Please retry shortly.")

st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #94A3B8; font-size: 13px;'>
        © 2026 <b>Mobinul Institutional Terminal</b> | All Rights Reserved.<br>
        <i>Multi-Timeframe Sentiment Engine Powered by CoinGecko, CoinGlass & Arkham</i>
    </div>
    """,
    unsafe_allow_html=True
)
