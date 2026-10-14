import streamlit as st
import pandas as pd
import os
import datetime

st.set_page_config(
    page_title="Weekly & 60-Day Forward Forensic Audit",
    page_icon="🔬",
    layout="wide"
)

# Dark Theme CSS
st.markdown("""
<style>
.stApp {
    background: linear-gradient(rgba(10, 15, 29, 0.92), rgba(10, 15, 29, 0.98)),
                url('https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2000&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #F8FAFC !important;
}
.glass-panel {
    background: rgba(17, 24, 39, 0.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
}
.terminal-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #F59E0B, #10B981, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
div[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.85) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    padding: 10px;
}
.stDownloadButton button {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
}
div[data-baseweb="select"] {
    background-color: rgba(30, 41, 59, 0.9) !important;
    border-radius: 10px !important;
}
div[data-baseweb="select"] * {
    color: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='terminal-title'>🔬 WEEKLY & 60-DAY PUMP FORENSIC AUDIT ENGINE</div>", unsafe_allow_html=True)
st.markdown("<b>Execution Framework:</b> 7-Day Batch Interims with 60-Day Master Post-Mortem Intelligence.")
st.markdown("<br>", unsafe_allow_html=True)

LOG_FILE = "forward_cycle_log.csv"
CONFIG_FILE = "engine_config.json"

if not os.path.exists(LOG_FILE):
    st.warning("⚠️ ট্র্যাকিং ফাইল পাওয়া যায়নি। `hourly_forward_tracker.py` প্রথমবার রান করলে ডেটা সিঙ্ক শুরু হবে।")
else:
    df = pd.read_csv(LOG_FILE)
    start_date = "N/A"
    if os.path.exists(CONFIG_FILE):
        start_date = pd.read_json(CONFIG_FILE).iloc[0]["start_date"]

    # সাইকেল প্রগ্রেস কার্ডস
    total_days = max(df["Days_Elapsed"].max() if not df.empty and "Days_Elapsed" in df.columns else 0, 0)
    progress_pct = min(round((total_days / 60) * 100, 1), 100.0)

    st.markdown(f"""
        <div class='glass-panel'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <b>Engine Start Date:</b> <code>{start_date}</code> | 
                    <b>Days Elapsed:</b> <code>{total_days}/60 Days</code> | 
                    <b>Master Progress:</b> <code>{progress_pct}% Completed</code>
                </div>
                <div>
                    <span style='color: #10B981; font-weight: bold;'>● LIVE HOURLY SYNC ACTIVE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ভিউ সিলেকশন (সাপ্তাহিক অন্তর্বর্তীকালীন বনাম ৬০ দিনের মাস্টার অডিট)
    all_weeks = sorted(df["Week_Batch"].dropna().unique().tolist()) if not df.empty else []
    view_options = ["📊 Master 60-Day Cumulative Audit"] + [f"📅 {w} Report" for w in all_weeks]

    selected_view = st.selectbox("Select Audit Horizon / Weekly Interim:", view_options, index=0)

    if selected_view == "📊 Master 60-Day Cumulative Audit":
        audit_df = df.copy()
        report_title = "🏆 Master 60-Day Cumulative Forensic Analysis"
    else:
        target_week = selected_view.replace("📅 ", "").replace(" Report", "")
        audit_df = df[df["Week_Batch"] == target_week].copy()
        report_title = f"📅 {target_week} Interim Forensic Audit"

    if audit_df.empty:
        st.info("নির্বাচিত টাইমফ্রেমে কোনো রেকর্ড পাওয়া যায়নি।")
    else:
        # অ্যানালিটিক্স মেট্রিক
        total_pumps = len(audit_df)
        super_trends = audit_df[audit_df["Status"] == "🔥 Multi-Day Super-Trend"]
        traps = audit_df[audit_df["Status"] == "⚠️ Flash Pump & Dump Trap"]
        dumped_coins = audit_df[audit_df["Dump_Detected"] == True]

        avg_hours_to_dump = dumped_coins["Hours_To_Dump"].mean() if not dumped_coins.empty else 0
        super_trend_winrate = (len(super_trends) / total_pumps * 100) if total_pumps > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Explosive Surges Audited", f"{total_pumps} Events")
        c2.metric("Multi-Day Continuation Win Rate", f"{super_trend_winrate:.1f}%", f"{len(super_trends)} Super-Trends")
        c3.metric("Trap Dumps Detected", f"{len(traps)} Traps", f"{(len(traps)/total_pumps*100):.1f}% of total" if total_pumps > 0 else "0%")
        c4.metric("Avg Hours to Crash", f"{avg_hours_to_dump:.1f} Hours" if avg_hours_to_dump > 0 else "N/A", "Peak-to-Dump Velocity")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader(report_title)

        # লিংক ও ফরম্যাটিং
        audit_df["Liquidity Heatmap"] = audit_df["Symbol"].apply(lambda s: f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?symbol={s}USDT")
        audit_df["On-Chain Intel"] = audit_df["Symbol"].apply(lambda s: f"https://arkm.com/explorer/token/{s.lower()}")

        display_cols = [
            "Week_Batch", "Date", "Symbol", "Trigger_Gain_24h", "Trigger_Price", 
            "Peak_Price", "Current_Price", "Hours_Tracked", "Hours_To_Dump", 
            "Status", "Liquidity Heatmap", "On-Chain Intel"
        ]
        available_cols = [c for c in display_cols if c in audit_df.columns]

        st.dataframe(
            audit_df[available_cols],
            column_config={
                "Trigger_Gain_24h": st.column_config.NumberColumn("Surge %", format="%.2f%%"),
                "Liquidity Heatmap": st.column_config.LinkColumn("Liquidity Heatmap", display_text="🔥 View Heatmap"),
                "On-Chain Intel": st.column_config.LinkColumn("On-Chain Intel", display_text="Open Arkham")
            },
            use_container_width=True,
            hide_index=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = audit_df.to_csv(index=False).encode('utf-8')
        clean_name = selected_view.replace(" ", "_").replace("📊_", "").replace("📅_", "").lower()
        st.download_button(
            label=f"📥 Download {selected_view} Full Report (CSV)",
            data=csv_data,
            file_name=f"{clean_name}_forensic_report.csv",
            mime="text/csv"
        )

# Footer
st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #94A3B8; font-size: 13px;'>
        © 2026 <b>Mobinul Institutional Terminal</b> | All Rights Reserved.<br>
        <i>Multi-Week Forward-Testing Engine Powered by Binance Futures API, CoinGlass & Arkham</i>
    </div>
    """,
    unsafe_allow_html=True
)
