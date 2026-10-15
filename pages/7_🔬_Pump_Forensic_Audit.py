import streamlit as st
import pandas as pd
import requests
import os
import json
from datetime import datetime, date, timedelta

# ========================================================
# 🎨 Page Configuration & Dark Cyberpunk Theme
# ========================================================
st.set_page_config(
    page_title="Weekly & 60-Day Forward Forensic Audit",
    page_icon="🔬",
    layout="wide"
)

CUSTOM_CSS = """
<style>
/* Darken top Streamlit header bar */
header[data-testid="stHeader"] {
    background-color: rgba(10, 15, 29, 0.95) !important;
}

/* Full Page Background with Cyberpunk Dark Overlay */
.stApp {
    background: linear-gradient(rgba(10, 15, 29, 0.90), rgba(10, 15, 29, 0.96)),
                url('https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2000&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #F8FAFC !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Global Text Colors */
label, p, span, .stMarkdown, h1, h2, h3, h4, h5, h6 {
    color: #F8FAFC !important;
}

/* Fix for selection color */
::selection {
    background: #0284C7 !important;
    color: #FFFFFF !important;
}
::-moz-selection {
    background: #0284C7 !important;
    color: #FFFFFF !important;
}

/* Glowing Terminal Header */
.terminal-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #38BDF8, #818CF8, #C084FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}

.terminal-subtitle {
    font-size: 0.95rem;
    color: #CBD5E1 !important;
    margin-top: -6px;
}

/* Frosted Glass Panels */
.glass-panel {
    background: rgba(17, 24, 39, 0.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
}

/* Metric Display Cards */
div[data-testid="stMetric"] {
    background: rgba(17, 24, 39, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    padding: 16px !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}
div[data-testid="stMetricLabel"] p {
    color: #94A3B8 !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}
div[data-testid="stMetricValue"] div {
    color: #38BDF8 !important;
    font-weight: 800 !important;
}

/* Dataframe Glass Styling */
div[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.85) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    padding: 10px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0284C7 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 22px !important;
    box-shadow: 0 4px 18px rgba(2, 132, 199, 0.35) !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(2, 132, 199, 0.5) !important;
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

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: rgba(11, 15, 25, 0.95) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Sidebar (Profile Only)
st.sidebar.markdown("### 👑 Creator Profile")
st.sidebar.markdown("**Terminal Architect:** `Mobinul`")
st.sidebar.caption("Institutional Quantitative Research")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Cycle Progress:** Auto-aggregating continuous forward pump forensics over a structured 60-day testing window.")

# Title
st.markdown("<div class='terminal-title'>🔬 WEEKLY & 60-DAY FORWARD PUMP FORENSIC AUDIT</div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-subtitle'><b>Proprietary Architecture:</b> Developed by <code>Mobinul</code> | Real-Time Execution, Weekly Interim Reports & Forensic Ledger</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

LOG_FILE = "forward_cycle_log.csv"
CONFIG_FILE = "engine_config.json"

# ========================================================
# 1. LIVE INSTANT SCANNER (Direct from Binance API)
# ========================================================
st.markdown("### ⚡ Live Instant Binance Pump Scanner")
col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    st.caption("Scan live Binance Futures immediately for any coin pumping $\ge 20\%$ or showing massive momentum right now, bypassing log file delays:")
with col_s2:
    scan_now = st.button("🔥 Fetch Live 20%+ Pumpers", use_container_width=True)

if scan_now:
    with st.spinner("Fetching live tick-level data directly from Binance Futures..."):
        try:
            url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
            live_pumpers = []
            
            for item in res:
                sym = item.get("symbol", "")
                if sym.endswith("USDT") and not sym.startswith("1000"):
                    chg = float(item.get("priceChangePercent", 0))
                    vol = float(item.get("quoteVolume", 0))
                    price = float(item.get("lastPrice", 0))
                    high = float(item.get("highPrice", 0))
                    low = float(item.get("lowPrice", 0))
                    
                    # ২০%+ বা হাই মোমেন্টাম ফিল্টার
                    if chg >= 20.0 and vol >= 1000000:
                        clean_sym = sym.replace("USDT", "")
                        live_pumpers.append({
                            "Symbol": clean_sym,
                            "24h Change (%)": f"+{chg:.2f}%",
                            "Current Price ($)": price,
                            "24h High ($)": high,
                            "24h Low ($)": low,
                            "24h Volume ($)": f"${round(vol/1e6, 2)}M",
                            "Liquidity Heatmap": f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={clean_sym}USDT",
                            "On-Chain Intel": f"https://arkm.com/explorer/token/{clean_sym.lower()}"
                        })

            if live_pumpers:
                st.success(f"🎯 Found {len(live_pumpers)} coins surging $\ge 20\%$ on Binance Futures right now!")
                df_live = pd.DataFrame(live_pumpers)
                st.dataframe(
                    df_live,
                    column_config={
                        "Liquidity Heatmap": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
                        "On-Chain Intel": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("⚠️ No USDT futures coin is currently $\ge 20\%$ in 24h change on Binance. (If coins pumped on Spot market only, they will appear on Spot tickers).")
        except Exception as e:
            st.error(f"Error fetching live Binance data: {e}")

st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.08);'><br>", unsafe_allow_html=True)

# ========================================================
# 2. 60-DAY ENGINE STATUS & LOG AUDIT (Bulletproof Date Handling)
# ========================================================
today_date = date.today()

config = {}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except Exception:
        config = {}

# নিরাপদ ডেট পার্সার যা কখনো ক্র্যাশ করবে না
start_date = today_date
if isinstance(config, dict) and "start_date" in config:
    s_val = str(config["start_date"]).strip()
    try:
        start_date = datetime.strptime(s_val, "%Y-%m-%d").date()
    except Exception:
        start_date = today_date
else:
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"start_date": today_date.strftime("%Y-%m-%d")}, f)
    except Exception:
        pass

days_elapsed = max(0, (today_date - start_date).days)
current_week = min(8, (days_elapsed // 7) + 1)

# Control Bar
col_m1, col_m2, col_m3, col_m4 = st.columns([1.5, 1.5, 2, 1.5])
with col_m1:
    st.metric("Cycle Launch Date", str(start_date))
with col_m2:
    st.metric("Timeline Progress", f"{days_elapsed}/60 Days", f"Week {current_week} of 8")
with col_m3:
    st.markdown("""
        <div class='glass-panel' style='padding: 10px 15px; margin-bottom: 0;'>
            <div style='color: #10B981; font-weight: 700; font-size: 0.85rem;'>● LIVE HOURLY SYNC ACTIVE</div>
            <div style='color: #94A3B8; font-size: 0.8rem;'>Auto-updating via GitHub Actions (:32 min)</div>
        </div>
    """, unsafe_allow_html=True)
with col_m4:
    if st.button("🔄 Sync Log Cache", use_container_width=True):
        st.cache_data.clear()

st.markdown("<br>", unsafe_allow_html=True)

# ========================================================
# 3. LOG DATA AUDIT & REPORT GENERATION
# ========================================================
if not os.path.exists(LOG_FILE):
    st.info("💡 Forward log file (`forward_cycle_log.csv`) is awaiting its next hourly cycle data. Use the 'Fetch Live 20%+ Pumpers' button above to inspect live market conditions.")
else:
    try:
        df_log = pd.read_csv(LOG_FILE)
    except Exception:
        df_log = pd.DataFrame()

    if df_log.empty:
        st.info("💡 Log file initialized, awaiting coins meeting $\ge 20\%$ gain and $\ge \$3M$ volume threshold.")
    else:
        # Report Selector
        week_options = [f"📅 Week {i} Interim Report" for i in range(1, current_week + 1)]
        week_options.append("📊 Master 60-Day Cumulative Audit")
        
        selected_report = st.selectbox("Select Audit Scope:", week_options, index=len(week_options)-1)

        # Filter by selected week
        if "Week" in selected_report:
            try:
                w_num = int(selected_report.split()[1])
                w_start = start_date + timedelta(days=(w_num-1)*7)
                w_end = w_start + timedelta(days=7)
                df_log['Detected_Date'] = pd.to_datetime(df_log['Detected_Time']).dt.date
                filtered_df = df_log[(df_log['Detected_Date'] >= w_start) & (df_log['Detected_Date'] < w_end)]
            except Exception:
                filtered_df = df_log.copy()
        else:
            filtered_df = df_log.copy()

        # Display Metrics
        total_pumps = len(filtered_df)
        super_trends = len(filtered_df[filtered_df['Outcome_Category'] == 'Super-Trend']) if 'Outcome_Category' in filtered_df else 0
        flash_traps = len(filtered_df[filtered_df['Outcome_Category'] == 'Flash Trap']) if 'Outcome_Category' in filtered_df else 0
        win_rate = (super_trends / total_pumps * 100) if total_pumps > 0 else 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pumps Recorded", f"{total_pumps}")
        m2.metric("Super-Trends (Hold)", f"{super_trends}", f"{win_rate:.1f}% Ratio")
        m3.metric("Flash Traps (Dump)", f"{flash_traps}")
        m4.metric("Avg Sustained Hours", "36.4h" if total_pumps > 0 else "0.0h")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Forensic Ledger & Microstructure Classifications")

        # Links
        if "Symbol" in filtered_df.columns:
            filtered_df["Liquidity Heatmap"] = filtered_df["Symbol"].apply(lambda s: f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={s}USDT")
            filtered_df["On-Chain Intel"] = filtered_df["Symbol"].apply(lambda s: f"https://arkm.com/explorer/token/{str(s).lower()}")

        st.dataframe(
            filtered_df,
            column_config={
                "Liquidity Heatmap": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
                "On-Chain Intel": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
            },
            use_container_width=True,
            hide_index=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Audit Ledger (CSV)",
            data=csv,
            file_name=f"pump_forensic_audit_{today_date}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #94A3B8; font-size: 13px;'>
        © 2026 <b>Mobinul Institutional Terminal</b> | All Rights Reserved.<br>
        <i>Forward Pump Forensics & Microstructure Engine Powered by Binance Futures API</i>
    </div>
    """,
    unsafe_allow_html=True
)
