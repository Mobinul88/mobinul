import streamlit as st
import pandas as pd
import requests
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Liquidity Heatmap Terminal",
    page_icon="🔥",
    layout="wide"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

st.title("🔥 লাইভ ক্রিপ্টো লিকুইডিটি হিটম্যাপ টার্মিনাল")
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *ইন-পেজ লাইভ চার্ট, লিকুইডেশন ক্লাস্টার ও ম্যাগনেট পুল অ্যানালাইসিস*")
st.divider()

# সার্চ বক্স
col_search, col_lev = st.columns([3, 1])
with col_search:
    target_token = st.text_input("কয়েনের সিম্বল লিখুন (যেমন: BTC, ETH, SOL, ARKM, LPT, TRX, DOGE):", value="BTC").strip().upper()
with col_lev:
    leverage_view = st.selectbox("হিটম্যাপ লিভারেজ ভিউ:", ["All Levels (25x - 100x)", "High Leverage (50x - 100x)", "Low Leverage (10x - 25x)"], index=0)

def fetch_live_price(symbol):
    """বাইনান্স থেকে লাইভ বর্তমান প্রাইস ও ২৪ ঘণ্টার ডেটা সংগ্রহ"""
    url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}USDT"
    try:
        r = requests.get(url, headers=HEADERS, timeout=4).json()
        if 'lastPrice' in r:
            return {
                'price': float(r['lastPrice']),
                'high': float(r['highPrice']),
                'low': float(r['lowPrice']),
                'volume': float(r['quoteVolume']),
                'change': float(r['priceChangePercent'])
            }
    except Exception:
        pass
    
    # স্পট ফলব্যাক
    try:
        url_spot = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
        r2 = requests.get(url_spot, headers=HEADERS, timeout=4).json()
        if 'lastPrice' in r2:
            return {
                'price': float(r2['lastPrice']),
                'high': float(r2['highPrice']),
                'low': float(r2['lowPrice']),
                'volume': float(r2['quoteVolume']),
                'change': float(r2['priceChangePercent'])
            }
    except Exception:
        pass
    return None

def build_liquidity_clusters(price):
    """গাণিতিক লিকুইডেশন পুল ও হিটম্যাপ লেভেলস প্রস্তুত করা"""
    # আপার শর্ট লিকুইডেশন ক্লাস্টার (Short Squeeze Targets)
    short_100x = round(price * 1.012, 4)
    short_50x  = round(price * 1.025, 4)
    short_25x  = round(price * 1.050, 4)
    short_10x  = round(price * 1.100, 4)

    # লোয়ার লং লিকুইডেশন ক্লাস্টার (Stop Hunt / Dip Targets)
    long_100x = round(price * 0.988, 4)
    long_50x  = round(price * 0.975, 4)
    long_25x  = round(price * 0.950, 4)
    long_10x  = round(price * 0.900, 4)

    clusters = [
        {"লেভেল": "🔴 10x Short Liquidation (Major TP)", "প্রাইস রেঞ্জ ($)": f"${short_10x:,.4f}", "লিকুইডিটি তীব্রতা": "🔥🔥🔥 Extreme High", "টাইপ": "Upper Magnet"},
        {"লেভেল": "🔴 25x Short Liquidation (Mid TP)", "প্রাইস রেঞ্জ ($)": f"${short_25x:,.4f}", "লিকুইডিটি তীব্রতা": "🔥🔥 High Density", "টাইপ": "Upper Magnet"},
        {"লেভেল": "🔴 50x-100x Short Liquidation", "প্রাইস রেঞ্জ ($)": f"${short_50x:,.4f} -${short_100x:,.4f}", "লিকুইডিটি তীব্রতা": "⚡ Quick Squeeze Zone", "টাইপ": "Upper Magnet"},
        {"লেভেল": "🎯 CURRENT LIVE PRICE", "প্রাইস রেঞ্জ ($)": f"${price:,.4f}", "লিকুইডিটি তীব্রতা": "⚖️ Equilibrium", "টাইপ": "Current"},
        {"লেভেল": "🟢 50x-100x Long Liquidation", "প্রাইস রেঞ্জ ($)": f"${long_100x:,.4f} -${long_50x:,.4f}", "লিকুইডিটি তীব্রতা": "⚡ Quick Wick Area", "টাইপ": "Lower Magnet"},
        {"লেভেল": "🟢 25x Long Liquidation (Stop Hunt)", "প্রাইস রেঞ্জ ($)": f"${long_25x:,.4f}", "লিকুইডিটি তীব্রতা": "🔥🔥 High Density", "টাইপ": "Lower Magnet"},
        {"লেভেল": "🟢 10x Long Liquidation (Deep Flush)", "প্রাইস রেঞ্জ ($)": f"${long_10x:,.4f}", "লিকুইডিটি তীব্রতা": "🔥🔥🔥 Extreme High", "টাইপ": "Lower Magnet"}
    ]
    return pd.DataFrame(clusters)

if target_token:
    with st.spinner(f"{target_token}-এর লাইভ লিকুইডিটি হিটম্যাপ ও এক্সচেঞ্জ ডেটা ফেচ করা হচ্ছে..."):
        m_data = fetch_live_price(target_token)

    if m_data:
        curr_p = m_data['price']
        
        # মেট্রিক্স কার্ডস
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("বর্তমান লাইভ প্রাইস", f"${curr_p:,.4f}", f"{m_data['change']:.2f}%")
        m2.metric("২৪ ঘণ্টার হাই", f"${m_data['high']:,.4f}")
        m3.metric("২৪ ঘণ্টার লো", f"${m_data['low']:,.4f}")
        m4.metric("২৪ ঘণ্টার ভলিউম", f"${m_data['volume']/1e6:,.2f}M")

        st.markdown("---")

        # ১. ইন-পেজ লাইভ চার্ট উইজেট (একই পেজে স্ক্রিন লোড হবে)
        st.subheader(f"📊 {target_token}USDT - লাইভ ইন্টারেক্টিভ ক্যান্ডেলস্টিক ও লিকুইডিটি চার্ট")
        st.caption("আপনার পেজের ভেতরেই লাইভ ক্যান্ডেল, ভলিউম ও টেকনিক্যাল অ্যানালাইসিস চার্ট:")

        tv_widget_html = f"""
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container" style="height:520px; width:100%;">
          <div id="tradingview_chart" style="height:calc(100% - 32px); width:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
            "autosize": true,
            "symbol": "BINANCE:{target_token}USDT",
            "interval": "60",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_top_toolbar": false,
            "allow_symbol_change": true,
            "save_image": false,
            "container_id": "tradingview_chart"
          }}
          );
          </script>
        </div>
        <!-- TradingView Widget END -->
        """
        components.html(tv_widget_html, height=540)

        st.markdown("---")

        # ২. লিকুইডেশন পুল ও হিটম্যাপ টেবিল
        st.subheader(f"🧲 {target_token} - রিয়েল-টাইম লিকুইডেশন পুল ও হিটম্যাপ ক্লাস্টার")
        st.caption("মার্কেট মেকাররা কোন কোন মূল্যে রিটেল ট্রেডারদের লিকুইডেশন হান্ট করতে পারে তার হিসাব:")

        df_heatmap = build_liquidity_clusters(curr_p)
        st.dataframe(
            df_heatmap,
            use_container_width=True,
            hide_index=True
        )

        # ৩. লিকুইডিটি সামারি ও ট্রেড গাইড
        st.markdown("#### 💡 প্রাতিষ্ঠানিক লিকুইডিটি ট্রেডিং গাইড:")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.info(f"**🎯 বুলিশ ম্যাগনেট জোন (Upper Squeeze Pool):**\n- প্রথম টার্গেট: **${round(curr_p * 1.025, 4):,.4f}** (৫০x শর্ট লিকুইডেশন)\n- মূল টার্গেট: **${round(curr_p * 1.050, 4):,.4f}** (২৫x শর্ট লিকুইডেশন)")
        with col_g2:
            st.warning(f"**🛡️ নিরাপদ স্টপ-লস জোন (Anti-Hunt Buffer):**\n- লিকুইডিটি হান্ট এড়াতে স্টপ-লস অন্তত **${round(curr_p * 0.965, 4):,.4f}**-এর নিচে রাখুন (যাতে ২৫x/৫০x লং উইকে আপনার ট্রেড লস না হয়)।")

    else:
        st.error(f"'{target_token}' পেয়ারটির লাইভ বাইনান্স ডেটা পাওয়া যায়নি। অনুগ্রহ করে সঠিক সিম্বল দিন (যেমন: BTC, ETH, SOL, ARKM, LPT, TRX)।")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 13px;'>
        © 2026 <b>Mobinul Intelligence Terminal</b> | All Rights Reserved.<br>
        <i>Real-Time In-Page Liquidity Heatmap & Cluster Engine</i>
    </div>
    """,
    unsafe_allow_html=True
)
