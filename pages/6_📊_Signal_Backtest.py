import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(
    page_title="Telegram Signal Live Audit & Performance",
    page_icon="📊",
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

/* Global Text Colors */
label, p, span, .stMarkdown, h1, h2, h3, h4, h5, h6 {
    color: #F8FAFC !important;
}

/* Selection Color Fix: No white glitch on clicks */
::selection {
    background: #0284C7 !important;
    color: #FFFFFF !important;
}
::-moz-selection {
    background: #0284C7 !important;
    color: #FFFFFF !important;
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

/* Download Button Fix */
.stDownloadButton button,
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding: 10px 22px !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35) !important;
    transition: all 0.3s ease !important;
}
.stDownloadButton button:hover,
div[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, #34D399 0%, #10B981 100%) !important;
    color: #FFFFFF !important;
    transform: translateY(-2px);
}

/* Sync Button */
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

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: rgba(11, 15, 25, 0.95) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ========================================================
# Sidebar (Profile Only)
# ========================================================
st.sidebar.markdown("### 👑 Creator Profile")
st.sidebar.markdown("**Terminal Architect:** `Mobinul`")
st.sidebar.caption("Telegram Signal Forensics & Execution Quant")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Signal Ledger Note:** Automatically syncs generated Telegram signals with live Binance price action to verify TP/SL hits and capital inflow.")

# ========================================================
# Header Section
# ========================================================
st.markdown("<div class='terminal-title'>📊 TELEGRAM SIGNAL AUDIT & LIVE PERFORMANCE</div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-subtitle'><b>Proprietary Architecture:</b> Developed by <code>Mobinul</code> | Real-Time Signal Validation, Inflow Metrics & Live Win-Rate Ledger</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

LOG_FILE = "telegram_signals_log.csv"

# বাইনান্স লাইভ প্রাইস আনা
@st.cache_data(ttl=20)
def get_live_prices():
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/price"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        return {p['symbol'].replace("USDT", ""): float(p['price']) for p in res if p['symbol'].endswith("USDT")}
    except Exception:
        return {}

# ========================================================
# Main Page Control Bar (No Settings in Sidebar)
# ========================================================
col_ctrl1, col_ctrl2 = st.columns([4, 1])
with col_ctrl1:
    st.markdown("""
        <div class='glass-panel' style='padding: 14px 20px; margin-bottom: 0;'>
            <span style='color: #38BDF8; font-weight: 600;'>🎯 Live Signal Execution Ledger:</span>
            <span style='color: #CBD5E1;'> Automatic verification of entries, targets, and stops directly against live Binance liquidity.</span>
        </div>
    """, unsafe_allow_html=True)
with col_ctrl2:
    if st.button("🔄 Sync Live Signal Status", use_container_width=True):
        st.cache_data.clear()

st.markdown("<br>", unsafe_allow_html=True)

# ========================================================
# Processing Signal History
# ========================================================
if not os.path.exists(LOG_FILE):
    st.info("💡 এখনও পর্যন্ত কোনো সিগন্যাল লগ তৈরি হয়নি। টেলিগ্রাম স্ক্যানার সিগন্যাল পাঠালে স্বয়ংক্রিয়ভাবে এখানে তালিকা তৈরি হবে।")
else:
    try:
        df = pd.read_csv(LOG_FILE)
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        st.info("💡 সিগন্যাল ফাইলটি বর্তমানে খালি। নতুন সিগন্যালের অপেক্ষায়...")
    else:
        live_prices = get_live_prices()
        
        # লাইভ রেজাল্ট চেক ও স্ট্যাটাস আপডেট
        for idx, row in df.iterrows():
            sym = str(row["Symbol"]).replace("USDT", "").upper()
            curr_price = live_prices.get(sym)
            
            if curr_price:
                entry = float(row["Entry_Price"])
                tp = float(row["Take_Profit"])
                sl = float(row["Stop_Loss"])
                sig_type = str(row["Signal_Type"]).upper()
                
                # লং সিগন্যাল রেজাল্ট
                if sig_type == "LONG":
                    if curr_price >= tp:
                        df.at[idx, "Status"] = "🎯 Target Hit (WIN)"
                    elif curr_price <= sl:
                        df.at[idx, "Status"] = "🛑 Stop Loss Hit (LOSS)"
                    else:
                        pnl_pct = ((curr_price - entry) / entry) * 100
                        df.at[idx, "Status"] = f"⏳ Running ({pnl_pct:+.2f}%)"
                        
                # শর্ট সিগন্যাল রেজাল্ট
                elif sig_type == "SHORT":
                    if curr_price <= tp:
                        df.at[idx, "Status"] = "🎯 Target Hit (WIN)"
                    elif curr_price >= sl:
                        df.at[idx, "Status"] = "🛑 Stop Loss Hit (LOSS)"
                    else:
                        pnl_pct = ((entry - curr_price) / entry) * 100
                        df.at[idx, "Status"] = f"⏳ Running ({pnl_pct:+.2f}%)"

                df.at[idx, "Current_Price"] = curr_price

        # মেট্রিক্স হিসেব
        total_signals = len(df)
        wins = len(df[df["Status"].str.contains("Target Hit", na=False)])
        losses = len(df[df["Status"].str.contains("Stop Loss", na=False)])
        running = len(df[df["Status"].str.contains("Running", na=False)])
        
        decided_trades = wins + losses
        win_rate = (wins / decided_trades * 100) if decided_trades > 0 else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Telegram Signals", f"{total_signals}")
        c2.metric("Target Achieved (Wins)", f"{wins}", f"Win Rate: {win_rate:.1f}%")
        c3.metric("Stop Loss Hit (Losses)", f"{losses}")
        c4.metric("Active Running Signals", f"{running}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Live Signal Execution & Audit Ledger")
        st.caption("All generated signals from telegram_scanner.py logged in real-time with continuous TP/SL checking:")

        # লিংক ও কলাম কনফিগারেশন
        df["Liquidity Heatmap"] = df["Symbol"].apply(lambda s: f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={s}USDT")
        df["On-Chain Intel"] = df["Symbol"].apply(lambda s: f"https://arkm.com/explorer/token/{str(s).lower()}")

        display_cols = [
            "Signal_Time", "Symbol", "Signal_Type", "Entry_Price", 
            "Take_Profit", "Stop_Loss", "Current_Price", "Inflow_Volume_USD", 
            "Status", "Liquidity Heatmap", "On-Chain Intel"
        ]
        available_cols = [c for c in display_cols if c in df.columns]

        st.dataframe(
            df[available_cols],
            column_config={
                "Entry_Price": st.column_config.NumberColumn("Entry ($)", format="$%.4f"),
                "Take_Profit": st.column_config.NumberColumn("TP Target ($)", format="$%.4f"),
                "Stop_Loss": st.column_config.NumberColumn("Stop Loss ($)", format="$%.4f"),
                "Current_Price": st.column_config.NumberColumn("Live Price ($)", format="$%.4f"),
                "Inflow_Volume_USD": st.column_config.NumberColumn("Inflow Vol ($)", format="$%.2f"),
                "Liquidity Heatmap": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
                "On-Chain Intel": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
            },
            use_container_width=True,
            hide_index=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Telegram Signal Audit Report (CSV)",
            data=csv_data,
            file_name="telegram_signals_audit_report.csv",
            mime="text/csv"
        )

# ========================================================
# Footer
# ========================================================
st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #94A3B8; font-size: 13px;'>
        © 2026 <b>Mobinul Institutional Terminal</b> | All Rights Reserved.<br>
        <i>Telegram Signal Ledger & Live Execution Engine Powered by Binance Futures</i>
    </div>
    """,
    unsafe_allow_html=True
)
