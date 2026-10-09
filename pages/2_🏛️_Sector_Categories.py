import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Crypto Sector & Category Intelligence",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ টপ ক্রিপ্টো সেক্টর ও ক্যাটাগরি ট্র্যাকার")
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *মার্কেট ক্যাটাগরি ও সেক্টর রোটেশন ইন্টেলিজেন্স*")
st.divider()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# জনপ্রিয় সেক্টরভিত্তিক শীর্ষ কয়েনের তালিকা
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

# সাইডবার ফিল্টার
selected_sector = st.sidebar.selectbox("সেক্টর বা ক্যাটাগরি বেছে নিন:", list(SECTOR_DATA.keys()))

@st.cache_data(ttl=900)
def fetch_sector_tokens(coin_ids):
    """CoinGecko বাল্ক ডাটা থেকে নির্দিষ্ট ক্যাটাগরির লাইভ মেট্রিক্স সংগ্রহ"""
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
                
                if circ > 0 and total > 0:
                    circ_pct = round((circ / total) * 100, 2)
                    status = "🟢 Low Risk" if circ_pct >= 80 else ("🔴 High Dilution" if circ_pct <= 35 else "🟡 Moderate")
                    unlock_info = f"{status} ({circ_pct}%)"
                else:
                    circ_pct = "N/A"
                    unlock_info = "🟢 Uncapped / No Cap"

                formatted.append({
                    "Rank": c.get('market_cap_rank', 'N/A'),
                    "Symbol": c.get('symbol', '').upper(),
                    "Name": c.get('name', ''),
                    "Price ($)": c.get('current_price', 0),
                    "24h Change (%)": f"{round(c.get('price_change_percentage_24h') or 0, 2)}%",
                    "Market Cap": f"${round((c.get('market_cap') or 0)/1e6, 2)}M",
                    "Circulating": f"{round(circ/1e6, 2)}M" if circ else "N/A",
                    "Total Supply": f"{round(total/1e6, 2)}M" if total else "N/A",
                    "Unlock Status": unlock_info,
                    "Arkham Link": f"https://arkm.com/explorer/token/{c.get('id')}"
                })
            return pd.DataFrame(formatted)
    except Exception:
        pass
    return pd.DataFrame()

# মূল ডিসপ্লে
st.subheader(f"📊 {selected_sector}-এর শীর্ষ কয়েন ও অন-চেইন তথ্য")

target_coins = SECTOR_DATA[selected_sector]
with st.spinner(f"{selected_sector} ডাটা রিফ্রেশ হচ্ছে..."):
    df_category = fetch_sector_tokens(target_coins)

if not df_category.empty:
    st.dataframe(
        df_category,
        column_config={
            "Arkham Link": st.column_config.LinkColumn("On-Chain Data", display_text="Open Arkham")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # CSV ডাউনলোড
    csv_data = df_category.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 {selected_sector} রিপোর্ট ডাউনলোড করুন",
        data=csv_data,
        file_name=f"{selected_sector}_sector_report.csv",
        mime="text/csv"
    )
else:
    st.warning("ক্যাটাগরি ডেটা লোড হতে পারছে না। কিছুক্ষণ পর আবার চেষ্টা করুন।")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 13px;'>
        © 2026 <b>Mobinul Intelligence Terminal</b> | All Rights Reserved.<br>
        <i>Sector Rotation & Categorical Terminal</i>
    </div>
    """,
    unsafe_allow_html=True
)
