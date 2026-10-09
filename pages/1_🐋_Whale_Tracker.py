import streamlit as st

st.set_page_config(page_title="Whale Tracker", page_icon="🐋", layout="wide")

st.title("🐋 হোয়েল ট্র্যাকিং ও স্মার্ট মানি ওয়াচিং")
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *স্মার্ট মানি ও এক্সচেঞ্জ ফ্লো ট্র্যাকার*")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏦 টপ এক্সচেঞ্জ ও ফান্ড হোল্ডিংস")
    st.write("বিশ্বের সবচেয়ে বড় বড় মার্কেট মেকার ও ফান্ডগুলোর ওয়ালেট সরাসরি ট্র্যাক করুন:")
    st.markdown("- [🏛️ Binance CEX Hot/Cold Wallets](https://arkm.com/explorer/entity/binance)")
    st.markdown("- [🦅 Jump Trading Portfolio](https://arkm.com/explorer/entity/jump-trading)")
    st.markdown("- [❄️ Wintermute Trading (Top Market Maker)](https://arkm.com/explorer/entity/wintermute)")
    st.markdown("- [💼 DWF Labs On-Chain Activity](https://arkm.com/explorer/entity/dwf-labs)")

with col2:
    st.markdown("### 🔍 নির্দিষ্ট কয়েনের হোয়েল সার্চ")
    token_input = st.text_input("যেকোনো টোকেনের সিম্বল লিখুন (যেমন: BTC, ETH, SOL, FET):", value="BTC")
    if st.button("কয়েনটির শীর্ষ হোয়েল ওয়ালেট দেখুন"):
        arkham_direct = f"https://arkm.com/explorer/token/{token_input.lower()}"
        st.success(f"সরাসরি লিঙ্ক প্রস্তুত! নিচের বোতামে ক্লিক করে {token_input}-এর টপ হোল্ডারদের তালিকা দেখুন:")
        st.link_button(f"🌐 Open {token_input} Whale Dashboard", arkham_direct)
