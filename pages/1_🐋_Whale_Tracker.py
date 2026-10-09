import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Whale & Smart Money Intelligence",
    page_icon="🐋",
    layout="wide"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

st.title("🐋 হোয়েল ট্র্যাকিং ও স্মার্ট মানি ওয়াচিং")
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *অন-চেইন লার্জ হোল্ডার ও স্মার্ট মানি ইন্টেলিজেন্স*")
st.divider()

# শীর্ষ ফান্ড ও মার্কেট মেকারদের কুইক রেফারেন্স
st.markdown("### 🏦 টপ প্রাতিষ্ঠানিক ফান্ড ও মার্কেট মেকার্স")
col_e1, col_e2, col_e3, col_e4 = st.columns(4)
with col_e1:
    st.markdown("[🏛️ **Binance CEX Reserves**](https://arkm.com/explorer/entity/binance)")
with col_e2:
    st.markdown("[🦅 **Jump Trading Portfolio**](https://arkm.com/explorer/entity/jump-trading)")
with col_e3:
    st.markdown("[❄️ **Wintermute (Top MM)**](https://arkm.com/explorer/entity/wintermute)")
with col_e4:
    st.markdown("[💼 **DWF Labs On-Chain**](https://arkm.com/explorer/entity/dwf-labs)")

st.divider()

# ইন-পেজ টোকেন সার্চ
st.subheader("🔍 নির্দিষ্ট টোকেনের লাইভ হোয়েল ও অন-চেইন ইন্টেলিজেন্স")
user_token = st.text_input("যেকোনো ক্রিপ্টোর সিম্বল লিখুন (যেমন: BTC, ETH, SOL, LPT, NEAR, FET):", value="BTC").strip().upper()

def fetch_token_deep_data(symbol):
    """কয়েনটির গভীর অন-চেইন ও মার্কেট ডেটা একই পেজে আনার জন্য ফেচিং"""
    try:
        # আইডি খোঁজা
        s_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        s_res = requests.get(s_url, headers=HEADERS, timeout=5).json()
        coins = s_res.get('coins', [])
        
        target_coin = next((c for c in coins if c['symbol'].upper() == symbol), coins[0] if coins else None)
        if not target_coin:
            return None
            
        coin_id = target_coin['id']
        d_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
        d_res = requests.get(d_url, headers=HEADERS, timeout=6).json()
        
        m_data = d_res.get('market_data', {})
        return {
            'id': coin_id,
            'name': d_res.get('name'),
            'symbol': symbol,
            'price': m_data.get('current_price', {}).get('usd', 0),
            'market_cap': m_data.get('market_cap', {}).get('usd', 0),
            'total_volume': m_data.get('total_volume', {}).get('usd', 0),
            'circ_supply': m_data.get('circulating_supply') or 0,
            'total_supply': m_data.get('total_supply') or 0,
            'max_supply': m_data.get('max_supply') or 0,
            'change_24h': m_data.get('price_change_percentage_24h', 0),
            'ath_change': m_data.get('ath_change_percentage', {}).get('usd', 0),
            'sentiment_up': d_res.get('sentiment_votes_up_percentage', 50)
        }
    except Exception:
        return None

if user_token:
    with st.spinner(f"{user_token}-এর অন-চেইন ও হোয়েল ডেটা প্রসেস করা হচ্ছে..."):
        data = fetch_token_deep_data(user_token)

    if data:
        # মেট্রিক্স কার্ডস
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("বর্তমান প্রাইস", f"${data['price']:,.4f}", f"{data['change_24h']:.2f}%")
        m2.metric("২৪ ঘণ্টার ট্রেডিং ভলিউম", f"${data['total_volume']/1e6:,.2f}M")
        m3.metric("মার্কেট ক্যাপ", f"${data['market_cap']/1e6:,.2f}M")
        m4.metric("ATH থেকে পতন", f"{data['ath_change']:.2f}%")

        st.markdown("---")
        
        # সাপ্লাই ও স্মার্ট মানি ডিলিউশন টেবিল
        st.markdown(f"#### 🐋 {data['name']} ({data['symbol']}) - হোয়েল ও সাপ্লাই ডিস্ট্রিবিউশন")
        
        circ = data['circ_supply']
        tot = data['max_supply'] if data['max_supply'] > 0 else (data['total_supply'] if data['total_supply'] > 0 else circ)
        
        circ_pct = round((circ / tot) * 100, 2) if tot > 0 else 100.0
        vol_mc_ratio = round((data['total_volume'] / data['market_cap']) * 100, 2) if data['market_cap'] > 0 else 0
        
        # স্মার্ট মানি ভলিউম অ্যানালাইসিস
        if vol_mc_ratio >= 25:
            whale_activity = "🔥 Extreme Whale / High Turnover Activity"
        elif vol_mc_ratio >= 10:
            whale_activity = "⚡ Strong Institutional Trading Flow"
        else:
            whale_activity = "🟢 Normal Retail Accumulation"

        status = "🟢 Low Concentration Risk" if circ_pct >= 80 else ("🔴 High Dilution / Unlock Risk" if circ_pct <= 35 else "🟡 Moderate Risk")

        summary_df = pd.DataFrame([{
            "মেট্রিক": "সার্কুলেটিং সাপ্লাই", "মান": f"{round(circ/1e6, 2)}M",
            "ব্যাখ্যা": "বর্তমানে মার্কেটে সক্রিয় কয়েনের পরিমাণ"
        }, {
            "মেট্রিক": "সর্বোচ্চ / মোট সাপ্লাই", "মান": f"{round(tot/1e6, 2)}M" if tot > 0 else "Uncapped",
            "ব্যাখ্যা": "টোকেনের মোট লিমিট"
        }, {
            "মেট্রিক": "আনলক / সার্কুলেটিং রেশিও", "মান": f"{circ_pct}%",
            "ব্যাখ্যা": status
        }, {
            "মেট্রিক": "ভলিউম / মার্কেট ক্যাপ রেশিও", "মান": f"{vol_mc_ratio}%",
            "ব্যাখ্যা": whale_activity
        }])
        
        st.table(summary_df)

        # বিস্তারিত অন-চেইন দেখার ব্যাকআপ
        st.info(f"💡 সরাসরি Arkham গ্রাফে {data['name']}-এর লাইভ ওয়ালেট ও এক্সচেঞ্জ ট্রান্সফার দেখতে চাইলে:")
        st.markdown(f"[🌐 Arkham On-Chain Explorer-এ **{data['name']}** ওপেন করুন](https://arkm.com/explorer/token/{data['id']})")
    else:
        st.warning(f"'{user_token}' সিম্বলটির মেটাডাটা পাওয়া যায়নি। অনুগ্রহ করে সঠিক সিম্বল দিন (যেমন: BTC, SOL, ETH, LPT)।")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 13px;'>
        © 2026 <b>Mobinul Intelligence Terminal</b> | All Rights Reserved.<br>
        <i>Smart Money & Whale Intelligence Module</i>
    </div>
    """,
    unsafe_allow_html=True
)
