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

# ========================================================
# 🎨 আল্ট্রা-প্রো ডার্ক ক্রিপ্টো গ্লাস থিম (100% Contrast Fixed)
# ========================================================
CUSTOM_CSS = """
<style>
/* ওপরের সাদা হেডার বার ডার্ক করা */
header[data-testid="stHeader"] {
    background-color: rgba(10, 15, 29, 0.95) !important;
}

/* ফুল পেজ ব্যাকগ্রাউন্ড */
.stApp {
    background: linear-gradient(rgba(10, 15, 29, 0.90), rgba(10, 15, 29, 0.96)),
                url('https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2000&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #F8FAFC !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* সব টেক্সট ও লেবেলের উজ্জ্বলতা ফিক্স */
label, p, span, .stMarkdown, h1, h2, h3, h4, h5, h6 {
    color: #F8FAFC !important;
}

/* ফ্রস্টেড গ্লাস কার্ড */
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

/* হেডার টাইটেল */
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

/* ড্রপডাউন সিলেক্ট বক্স ফিক্স */
div[data-baseweb="select"] {
    background-color: rgba(30, 41, 59, 0.9) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}

div[data-baseweb="select"] * {
    color: #FFFFFF !important;
}

/* রান স্ক্যান বাটন */
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

/* টেবিল গ্লাস ব্যাকগ্রাউন্ড */
div[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.85) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    padding: 10px;
}

/* সাইডবার */
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

# সেক্টর ম্যাপিং
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

# সাইডবার
st.sidebar
