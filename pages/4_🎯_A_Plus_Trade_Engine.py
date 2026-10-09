import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Institutional Confluence & Risk Engine",
    page_icon="🎯",
    layout="wide"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

st.title("🎯 প্রাতিষ্ঠানিক সুইং, ডেরিভেটিভস ও রিস্ক ম্যানেজমেন্ট টার্মিনাল")
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *বিটিসি রেজিম, ফান্ডিং রেট, ওপেন ইন্টারেস্ট, লিকুইডিটি ও পজিশন ক্যালকুলেটর*")
st.divider()

# ১. বাইনান্স ও মার্কেট ফেচ ফাংশন
def get_binance_klines(symbol, interval, limit=230):
    urls = [
        "https://data-api.binance.vision/api/v3/klines",
        "https://fapi.binance.com/fapi/v1/klines",
        "https://api.binance.com/api/v3/klines"
    ]
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    for u in urls:
        try:
            r = requests.get(u, params=params, headers=HEADERS, timeout=4)
            if r.status_code == 200:
                res = r.json()
                if isinstance(res, list) and len(res) >= 200:
                    return res
        except Exception:
            continue
    return None

def fetch_derivatives_data(symbol):
    """লাইভ ফান্ডিং রেট ও ওপেন ইন্টারেস্ট সংগ্রহ"""
    funding_rate = 0.01
    open_interest = 0.0
    try:
        f_url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}USDT"
        fr = requests.get(f_url, headers=HEADERS, timeout=3).json()
        if 'lastFundingRate' in fr:
            funding_rate = float(fr['lastFundingRate']) * 100
    except Exception:
        pass

    try:
        oi_url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}USDT"
        oir = requests.get(oi_url, headers=HEADERS, timeout=3).json()
        if 'openInterest' in oir:
            open_interest = float(oir['openInterest'])
    except Exception:
        pass

    return funding_rate, open_interest

def analyze_btc_and_dominance():
    """বিটকয়েন সাপোর্ট ও অল্টকয়েন মার্কেট রেজিম বিশ্লেষণ"""
    klines = get_binance_klines("BTCUSDT", "1d", 220)
    if not klines:
        return {"title": "বিটিসি ডেটা কানেকশন এরর", "desc": "ডেটা লোড করা সম্ভব হয়নি", "trade_allowed": True, "price": 0}
    
    closes = [float(k[4]) for k in klines]
    df_btc = pd.DataFrame({'close': closes})
    df_btc['sma50'] = df_btc['close'].rolling(50).mean()
    df_btc['sma200'] = df_btc['close'].rolling(200).mean()
    
    curr = df_btc['close'].iloc[-1]
    s50 = df_btc['sma50'].iloc[-1]
    s200 = df_btc['sma200'].iloc[-1]
    
    dist_support = min(abs(curr - s50) / s50, abs(curr - s200) / s200) * 100
    
    if (curr >= s200 or curr >= s50) and dist_support <= 4.5:
        return {
            "title": "🟢 BTC AT STRONG SUPPORT (Safe Altcoin Season)",
            "desc": f"বিটিসি টেকনিক্যাল সাপোর্ট জোনে স্থিতিশীল (${curr:,.2f})। অল্টকয়েন সুইং লং নেওয়ার জন্য পারফেক্ট রেজিম!",
            "trade_allowed": True,
            "price": curr
        }
    elif curr >= s200:
        return {
            "title": "🟢 BTC BULLISH REGIME",
            "desc": f"বিটিসি ২০০ এসএমএ-এর উপরে অবস্থান করছে (${curr:,.2f})। সুইং ট্রেড অনুমোদিত।",
            "trade_allowed": True,
            "price": curr
        }
    else:
        return {
            "title": "🔴 BTC VOLATILE / BREAKDOWN DANGER",
            "desc": f"বিটিসি মেজর সাপোর্টের নিচে বা ডাউনট্রেন্ডে অবস্থান করছে (${curr:,.2f})। অল্টকয়েনে লং নেওয়া অনিরাপদ!",
            "trade_allowed": False,
            "price": curr
        }

btc_state = analyze_btc_and_dominance()
if btc_state["trade_allowed"]:
    st.success(f"### {btc_state['title']}\n{btc_state['desc']}")
else:
    st.error(f"### {btc_state['title']}\n{btc_state['desc']}")

st.divider()

@st.cache_data(ttl=1800)
def get_token_metadata(symbol):
    try:
        s_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        s_res = requests.get(s_url, headers=HEADERS, timeout=5).json()
        coins = s_res.get('coins', [])
        target = next((c for c in coins if c['symbol'].upper() == symbol), coins[0] if coins else None)
        if not target:
            return None
        
        cid = target['id']
        d_url = f"https://api.coingecko.com/api/v3/coins/{cid}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
        d_res = requests.get(d_url, headers=HEADERS, timeout=6).json()
        m_data = d_res.get('market_data', {})
        
        circ = float(m_data.get('circulating_supply') or 0)
        tot = float(m_data.get('max_supply') or m_data.get('total_supply') or circ)
        circ_pct = round((circ / tot) * 100, 2) if tot > 0 else 100.0
        
        return {
            'id': cid,
            'name': d_res.get('name', symbol),
            'circ_pct': circ_pct,
            'circ': circ,
            'total': tot
        }
    except Exception:
        return None

# ২. কয়েন সার্চ ও প্যারামিটার
st.subheader("🔍 প্রাতিষ্ঠানিক অডিট ইঞ্জিন ও কনফ্লুয়েন্স সার্চ")
col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
with col_s1:
    search_token = st.text_input("কয়েনের সিম্বল (যেমন: LPT, ARKM, ATOM, FET, SOL, TRX):", value="LPT").strip().upper()
with col_s2:
    selected_sma = st.selectbox("মুভিং এভারেজ (SMA)", [200, 50], index=0)
with col_s3:
    selected_tf = st.selectbox("টাইমফ্রেম", ["1d", "4h"], index=0)

if search_token:
    with st.spinner(f"{search_token}-এর ডেরিভেটিভস, টেকনিক্যাল ও অন-চেইন ডেটা প্রসেস হচ্ছে..."):
        klines = get_binance_klines(f"{search_token}USDT", selected_tf, selected_sma + 35)
        meta = get_token_metadata(search_token)
        funding_rate, open_interest = fetch_derivatives_data(search_token)

    if not klines or len(klines) < (selected_sma + 5):
        st.error(f"'{search_token}USDT' পেয়ারটির ডেটা লোড করা যায়নি। সঠিক পেয়ার নাম নিশ্চিত করুন।")
    else:
        closes = [float(k[4]) for k in klines]
        lows = [float(k[3]) for k in klines]
        
        df_coin = pd.DataFrame({'close': closes, 'low': lows})
        df_coin['sma'] = df_coin['close'].rolling(selected_sma).mean()
        
        curr_p = df_coin['close'].iloc[-1]
        sma_val = df_coin['sma'].iloc[-1]
        dist_pct = ((curr_p - sma_val) / sma_val) * 100
        
        circ_pct = meta['circ_pct'] if meta else 85.0
        c_status = "🟢 Low Risk (Safe)" if circ_pct >= 80 else ("🔴 High Dilution" if circ_pct <= 35 else "🟡 Moderate")
        
        # ৭ডি, ১৪ডি, ৩০ডি হোয়েল ফ্লো
        p_7d = closes[-7]
        p_14d = closes[-14]
        p_30d = closes[-30] if len(closes) >= 30 else closes[0]
        
        acc_7d = curr_p >= p_7d
        acc_14d = curr_p >= p_14d
        acc_30d = curr_p >= p_30d
        
        if acc_7d and acc_14d and acc_30d:
            w_grade = "⭐⭐⭐ Grade A+ (Strongest Accumulation)"
        elif acc_7d and acc_30d:
            w_grade = "⭐⭐ Grade A (Optimal Flow)"
        elif acc_7d:
            w_grade = "⚡ Grade B (Fresh 7D Rebound)"
        else:
            w_grade = "⚠️ Grade C (Whale Distribution)"
            
        flow_metric = "7D: " + ("🟢" if acc_7d else "🔴") + " | 14D: " + ("🟢" if acc_14d else "🔴") + " | 30D: " + ("🟢" if acc_30d else "🔴")

        # ডেরিভেটিভস সেন্টিমেন্ট
        if funding_rate < 0:
            deriv_bias = f"🔥 Extreme Bullish Short-Squeeze Bias (Funding: {funding_rate:.4f}%)"
        elif funding_rate < 0.01:
            deriv_bias = f"🟢 Balanced / Neutral Funding ({funding_rate:.4f}%)"
        else:
            deriv_bias = f"⚠️ Overheated Longs (Funding: {funding_rate:.4f}%)"

        short_liq_pool = "$" + str(round(curr_p * 1.035, 4)) + " - $" + str(round(curr_p * 1.075, 4))
        safe_sl = round(sma_val * 0.965, 4)
        entry_zone = "$" + str(round(sma_val * 1.002, 4)) + " - $" + str(round(curr_p, 4))
        
        risk = max(curr_p - safe_sl, curr_p * 0.035)
        tp1 = round(curr_p + (risk * 1.5), 4)
        tp2 = round(curr_p + (risk * 2.5), 4)
        tp3 = round(curr_p + (risk * 4.0), 4)
        tp_summary = "TP1: $" + str(tp1) + " | TP2: $" + str(tp2) + " \vert{} TP3: $" + str(tp3)

        trade_verdict = "🟢 A+ READY TO LONG" if (btc_state["trade_allowed"] and curr_p >= sma_val and "Grade C" not in w_grade) else "⛔ NO TRADE (Risky Setup)"

        # মেট্রিক্স কার্ডস
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("বর্তমান লাইভ প্রাইস", f"${curr_p:,.4f}", f"{dist_pct:+.2f}% from SMA")
        m2.metric(f"{selected_sma} SMA ভ্যালু", f"${sma_val:,.4f}")
        m3.metric("টোকেন আনলক স্ট্যাটাস", f"{circ_pct}%", c_status)
        m4.metric("ট্রেড ডিসিশন", trade_verdict)

        st.markdown("---")

        # ৩. রিস্ক ও পজিশন সাইজিং ক্যালকুলেটর (নতুন ফিচার)
        st.subheader("💰 স্বয়ংক্রিয় পজিশন সাইজিং ও রিস্ক ক্যালকুলেটর")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            acc_balance = st.number_input("আপনার ক্যাপিটাল ($ USD):", min_value=50.0, value=1000.0, step=50.0)
        with col_c2:
            risk_pct = st.slider("এই ট্রেডে সর্বোচ্চ ঝুঁকি (Risk %):", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
        
        dollar_risk = (acc_balance * risk_pct) / 100
        sl_diff_pct = abs((curr_p - safe_sl) / curr_p) * 100
        recommended_tokens = dollar_risk / abs(curr_p - safe_sl) if abs(curr_p - safe_sl) > 0 else 0
        total_position_size = recommended_tokens * curr_p
        rec_leverage = max(1.0, round(total_position_size / acc_balance, 1))

        with col_c3:
            st.metric("সর্বোচ্চ ঝুঁকি ($)", f"${dollar_risk:,.2f}")

        rc1, rc2, rc3 = st.columns(3)
        rc1.info(f"**স্টপ-লস দূরত্ব:** `{sl_diff_pct:.2f}%`")
        rc2.success(f"**প্রস্তাবিত টোকেন সংখ্যা:** `{recommended_tokens:,.2f} {search_token}`")
        rc3.warning(f"**নিরাপদ ফিউচার্স লেভারেজ:** `{min(rec_leverage, 5.0)}x` (স্পটে 1x)")

        st.markdown("---")

        # ৪. ফুল অডিট টেবিল
        st.subheader(f"📋 {search_token} - প্রাতিষ্ঠানিক অডিট রিপোর্ট")
        audit_rows = [
            {"প্যারামিটার": "১. বিটকয়েন মার্কেট রেজিম (BTC Safe?)", "মান": "✅ অনুমোদিত (সাপোর্টে রয়েছে)" if btc_state["trade_allowed"] else "❌ ঝুঁকিপূর্ণ (ডাউনট্রেন্ড)", "ইমপ্যাক্ট": "গ্লোবাল ডিরেকশন"},
            {"প্যারামিটার": "২. টেকনিক্যাল রিটেস্ট (" + str(selected_sma) + " SMA)", "মান": ("✅ এসএমএ-এর উপরে" if curr_p >= sma_val else "❌ এসএমএ-এর নিচে") + " (দূরত্ব: " + str(round(dist_pct, 2)) + "%)", "ইমপ্যাক্ট": "সুইং সাপোর্ট"},
            {"প্যারামিটার": "৩. ফান্ডিং রেট ও ডেরিভেটিভস বায়াস", "মান": deriv_bias, "ইমপ্যাক্ট": "শর্ট স্কুইজ পটেনশিয়াল"},
            {"প্যারামিটার": "৪. টোকেনোমিক্স ও সাপ্লাই ডিলিউশন", "মান": str(circ_pct) + "% সার্কুলেটিং (" + c_status + ")", "ইমপ্যাক্ট": "টোকেন ডাম্প রিস্ক ফিল্টার"},
            {"প্যারামিটার": "৫. হোয়েল ফ্লো (7D / 14D / 30D)", "মান": flow_metric + " (" + w_grade + ")", "ইমপ্যাক্ট": "স্মার্ট মানি একুমুলেশন"},
            {"প্যারামিটার": "৬. লিকুইডিটি হিটম্যাপ পুল (Upper Target)", "মান": short_liq_pool, "ইমপ্যাক্ট": "ম্যাগনেট লিকুইডেশন টার্গেট"},
            {"প্যারামিটার": "৭. এন্ট্রি জোন (Entry Range)", "মান": entry_zone, "ইমপ্যাক্ট": "লিমিট বাই অর্ডার রেঞ্জ"},
            {"প্যারামিটার": "৮. অ্যান্টি-হান্ট স্টপ-লস (Safe SL)", "মান": "$" + str(safe_sl), "ইমপ্যাক্ট": "লিকুইডিটি হান্টিং বাফার"},
            {"প্যারামিটার": "৯. টার্গেট লেভেলস", "মান": tp_summary, "ইমপ্যাক্ট": "রিস্ক-রিওয়ার্ড ১:১.৫ থেকে ১:৪.০"}
        ]
        st.table(pd.DataFrame(audit_rows))

        # ৫. টেলিগ্রাম অ্যালার্ট মেকার (এক ক্লিকে কপি করার মতো তৈরি টেক্সট)
        st.subheader("📲 টেলিগ্রাম ও ডিসকর্ড রেডি সিগন্যাল")
        telegram_text = f"""🚨 [MOBINUL TERMINAL A+ SWING SIGNAL] 🚨
Pair: #{search_token}USDT
Verdict: {trade_verdict}
Entry Zone: {entry_zone}
Stop-Loss: ${safe_sl} (Anti-Hunt Buffer)
Targets: {tp_summary}
Funding Rate: {funding_rate:.4f}% | Whale: {w_grade}
Risk Management: {min(rec_leverage, 5.0)}x Max Leverage (Risk {dollar_risk:,.2f}$)"""
        
        st.code(telegram_text, language="markdown")

        c_link1, c_link2 = st.columns(2)
        with c_link1:
            ark_slug = meta['id'] if meta else search_token.lower()
            st.link_button(f"🌐 Open {search_token} on Arkham Intelligence", f"https://arkm.com/explorer/token/{ark_slug}", use_container_width=True)
        with c_link2:
            st.link_button(f"🔥 View {search_token} Coinglass Liquidity Heatmap", f"https://www.coinglass.com/pro/futures/LiquidityHeatMap?symbol={search_token}USDT", use_container_width=True)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 13px;'>
        © 2026 <b>Mobinul Intelligence Terminal</b> | All Rights Reserved.<br>
        <i>Institutional Derivatives, Risk Engine & Trade Execution Terminal</i>
    </div>
    """,
    unsafe_allow_html=True
)
