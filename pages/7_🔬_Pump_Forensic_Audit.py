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
    font
