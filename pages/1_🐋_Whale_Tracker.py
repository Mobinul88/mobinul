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
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *ইন-পেজ অন-চেইন ও লার্জ হোল্ডার অ্যানালিটিক্স*")
st.divider()

# শীর্ষ ফান্ড ও মার্কেট মেকার্স
st.markdown("### 🏦 প্রাতিষ্ঠানিক ফান্ড ও শীর্ষ এক্সচেঞ্জ রিজার্ভ")
col_e1, col_e2, col_e3, col_e4 = st.columns(4)
with col_e1:
    st.markdown("[🏛️ **Binance CEX Reserves**](https://arkm.com/explorer/entity/binance)")
with col_e2:
    st.markdown("[🦅 **Jump Trading Portfolio**](https://arkm.com/explorer/entity/jump-trading)")
with col_e3:
    st.markdown("[❄️ **Wintermute Trading**](https://arkm.com/explorer/entity/wintermute)")
with col_e4:
    st.markdown("[💼 **DWF Labs Activity**](https://arkm.com/explorer/entity/dwf-labs)")

st.divider()

# ইন-পেজ টোকেন সার্চ
st.subheader("🔍 লাইভ হোয়েল ও অন-চেইন ইন্টেলিজেন্স সার্চ")
user_token = st.text_input("যেকোনো ক্রিপ্টোর সিম্বল লিখুন (যেমন: BTC, ETH, SOL, LPT, NEAR, FET):", value="BTC").strip().upper()

def fetch_token_metrics(symbol):
    """কয়েনটির গভীর অন-চেইন ও মার্কেট ডেটা একই পেজে আনার জন্য ফেচিং"""
    try:
        s_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        s_res = requests.get(s_url, headers=HEADERS, timeout=6).json()
        coins = s_res.get('coins', [])
        
        target = next((c for c in coins if c['symbol'].upper() == symbol), coins[0] if coins else None)
        if not target:
            return None
            
        coin_id = target['id']
        d_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
        d_res = requests.get(d_url, headers=HEADERS, timeout=7).json()
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
            'high_24h': m_data.get('high_24h', {}).get('usd', 0),
            'low_24h': m_data.get('low_24h', {}).get('usd', 0)
        }
    except Exception:
        return None

if user_token:
    with st.spinner(f"{user_token}-এর লাইভ অন-চেইন ও মার্কেট ডেটা প্রসেস করা হচ্ছে..."):
        data = fetch_token_metrics(user_token)

    if data:
        # ৪টি বড় স্ট্যাটাস কার্ড
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("বর্তমান লাইভ প্রাইস", f"${data['price']:,.4f}", f"{data['change_24h']:.2f}%")
        m2.metric("২৪ ঘণ্টার ট্রেডিং ভলিউম", f"${data['total_volume']/1e6:,.2f}M")
        m3.metric("টোটাল মার্কেট ক্যাপ", f"${data['market_cap']/1e6:,.2f}M")
        m4.metric("ATH থেকে পতন", f"{data['ath_change']:.2f}%")

        st.markdown("---")
        
        # সাপ্লাই ও স্মার্ট মানি ডিলিউশন ম্যাট্রিক্স
        st.markdown(f"#### 📊 {data['name']} ({data['symbol']}) - অন-চেইন হোয়েল ও সাপ্লাই ডিস্ট্রিবিউশন")
        
        circ = data['circ_supply']
        tot = data['max_supply'] if data['max_supply'] > 0 else (data['total_supply'] if data['total_supply'] > 0 else circ)
        circ_pct = round((circ / tot) * 100, 2) if tot > 0 else 100.0
        
        # ভলিউম টু মার্কেট ক্যাপ (স্মার্ট মানি ফ্ল্যাগ)
        vol_mc_ratio = round((data['total_volume'] / data['market_cap']) * 100, 2) if data['market_cap'] > 0 else 0
        
        if vol_mc_ratio >= 25:
            whale_turnover = "🔥 Extreme Institutional / Whale Turnover"
        elif vol_mc_ratio >= 10:
            whale_turnover = "⚡ Strong Smart Money Accumulation"
        else:
            whale_turnover = "🟢 Normal Retail Flow"

        dilution_status = "🟢 Low Concentration Risk" if circ_pct >= 80 else ("🔴 High Unlock / Dilution Risk" if circ_pct <= 35 else "🟡 Moderate Risk")

        details_df = pd.DataFrame([
            {"প্যারামিটার": "সার্কুলেটিং সাপ্লাই (Circulating)", "পরিমাণ": f"{round(circ/1e6, 2)}M", "বিশ্লেষণ": "মার্কেটে বর্তমানে সচল টোকেন"},
            {"প্যারামিটার": "সর্বোচ্চ লিমিট (Max Supply)", "পরিমাণ": f"{round(tot/1e6, 2)}M" if tot > 0 else "Uncapped", "বিশ্লেষণ": "টোটাল সাপ্লাই ক্যাপ"},
            {"প্যারামিটার": "আনলক স্ট্যাটাস (Circulating %)", "পরিমাণ": f"{circ_pct}%", "বিশ্লেষণ": dilution_status},
            {"প্যারামিটার": "ভলিউম / মার্কেটক্যাপ রেশিও", "পরিমাণ": f"{vol_mc_ratio}%", "বিশ্লেষণ": whale_turnover},
            {"প্যারামিটার": "২৪ ঘণ্টার হাই / লো রেঞ্জ", "পরিমাণ": f"${data['low_24h']:,.4f} -${data['high_24h']:,.4f}", "বিশ্লেষণ": "দৈনিক ভোলাটিলিটি ব্যান্ড"}
        ])
        
        st.table(details_df)
    else:
        st.warning(f"'{user_token}' সিম্বলটির ডেটা পাওয়া যায়নি। অনুগ্রহ করে সঠিক সিম্বল দিন (যেমন: BTC, ETH, SOL, LPT)।")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 13px;'>
        © 2026 <b>Mobinul Intelligence Terminal</b> | All Rights Reserved.<br>
        <i>On-Chain & Smart Money Analysis Engine</i>
    </div>
    """,
    unsafe_allow_html=True
)
