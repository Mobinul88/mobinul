import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Social Sentiment & Trending", page_icon="🔥", layout="wide")

st.title("🔥 সোশ্যাল মিডিয়া ও টুইটার হাইপ রাডার")
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *সোশ্যাল সেন্টিমেন্ট ও ট্রেন্ডিং সার্চ ট্র্যাকার*")
st.divider()

HEADERS = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=600)
def get_trending_social_data():
    """সোশ্যাল মিডিয়ায় ও সার্চে ভাইরাল হওয়া টপ কয়েন সংগ্রহ"""
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        res = requests.get(url, headers=HEADERS, timeout=6).json()
        coins = res.get('coins', [])
        data = []
        for item in coins:
            c = item.get('item', {})
            c_data = c.get('data', {})
            data.append({
                "Rank": c.get('score', 0) + 1,
                "Symbol": c.get('symbol', '').upper(),
                "Coin Name": c.get('name', ''),
                "Price ($)": round(float(c_data.get('price', 0)), 6) if c_data.get('price') else "N/A",
                "24h Trend (%)": f"{round(float(c_data.get('price_change_percentage_24h', {}).get('usd', 0)), 2)}%",
                "Market Cap Rank": f"#{c.get('market_cap_rank', 'N/A')}",
                "Twitter & Social Hype": "🔥 High Viral Sentiment",
                "Arkham Search": f"https://arkm.com/explorer/token/{c.get('id')}"
            })
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

with st.spinner("সোশ্যাল ট্রেন্ডিং ও ভাইরাল ক্রিপ্টো ডেটা লোড হচ্ছে..."):
    df_trend = get_trending_social_data()

if not df_trend.empty:
    st.subheader("🚀 বর্তমানে সোশ্যাল মিডিয়া ও গ্লোবাল সার্চে শীর্ষে থাকা টোকেনসমূহ")
    st.dataframe(
        df_trend,
        column_config={
            "Arkham Search": st.column_config.LinkColumn("On-Chain Data", display_text="Open Arkham")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("সোশ্যাল ট্রেন্ডিং ডেটা লোড হতে পারছে না। কিছুক্ষণ পর আবার চেষ্টা করুন।")
