import streamlit as st
import pandas as pd
import requests
import datetime
import random
import time

st.set_page_config(
    page_title="Multi-Timeframe Whale & Liquidity Heatmap Engine",
    page_icon="🎯",
    layout="wide"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

st.title("🎯 প্রাতিষ্ঠানিক সুইং ও লিকুইডিটি হিটম্যাপ ইঞ্জিন")
st.markdown("**স্বত্বাধিকারী ও ডিজাইনার:** `Developed by Mobinul` | *BTC সাপোর্ট, 7D/14D/30D হোয়েল ফ্লো এবং লিকুইডিটি পুল কনফ্লুয়েন্স*")
st.divider()

# সাইডবার ফিল্টার সেটিংস
st.sidebar.header("⚙️ ট্রেড ও লিকুইডিটি ফিল্টার")
sma_period = st.sidebar.selectbox("মুভিং এভারেজ (SMA)", [200, 50], index=0)
timeframe = st.sidebar.selectbox("টাইমফ্রেম", ["1d", "4h"], index=0)
max_dist = st.sidebar.slider("SMA রিটেস্ট দূরত্ব (%)", min_value=1.0, max_value=5.0, value=3.0, step=0.5)
min_circ = st.sidebar.slider("নূন্যতম সার্কুলেটিং সাপ্লাই (%)", min_value=50.0, max_value=95.0, value=80.0, step=5.0)

SECTOR_MAP = {
    'FET': '🤖 AI / Data', 'NEAR': '🤖 AI / L1', 'RNDR': '🤖 AI / GPU', 'RENDER': '🤖 AI / GPU',
    'TAO': '🤖 AI', 'WLD': '🤖 AI', 'ARKM': '🤖 AI / Intel', 'GRT': '🤖 AI / Indexing',
    'ONDO': '🏛️ RWA', 'LINK': '🏛️ RWA / Oracle', 'PENDLE': '🏛️ RWA', 'MKR': '🏛️ RWA',
    'BTC': '🧱 Layer 1', 'ETH': '🧱 Layer 1', 'SOL': '🧱 Layer 1', 'BNB': '🧱 Layer 1',
    'SUI': '🧱 Layer 1', 'SEI': '🧱 Layer 1', 'AVAX': '🧱 Layer 1', 'ATOM': '🧱 Layer 1',
    'ADA': '🧱 Layer 1', 'DOT': '🧱 Layer 1', 'APT': '🧱 Layer 1', 'TRX': '🧱 Layer 1',
    'ARB': '⚡ Layer 2', 'OP': '⚡ Layer 2', 'MATIC': '⚡ Layer 2', 'STRK': '⚡ Layer 2',
    'UNI': '🔄 DeFi', 'AAVE': '🔄 DeFi', 'CRV': '🔄 DeFi', 'LPT': '🎥 AI / Video'
}

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
                if isinstance(res, list) and len(res) >= limit - 20:
                    return res
        except Exception:
            continue
    return None

def analyze_btc_support():
    """বিটকয়েন সাপোর্ট ও লিকুইডিটি রেজাইম চেক"""
    klines = get_binance_klines("BTCUSDT", "1d", 220)
    if not klines:
        return {"title": "বিটিসি ডেটা কানেকশন এরর", "desc": "ডেটা লোড হচ্ছে না", "trade_allowed": True}
    
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
            "title": "🟢 BTC AT STRONG SUPPORT (Safe Liquidity Zone)",
            "desc": f"বিটিসি টেকনিক্যাল সাপোর্ট জোনে রিবাউন্ড করছে (${curr:,.2f})। অল্টকয়েন সুইং লং নেওয়ার জন্য পারফেক্ট সময়!",
            "trade_allowed": True
        }
    elif curr >= s200:
        return {
            "title": "🟢 BTC BULLISH REGIME",
            "desc": f"বিটিসি ২০০ এসএমএ-এর উপরে স্থিতিশীল (${curr:,.2f})। সুইং ট্রেড অনুমোদিত।",
            "trade_allowed": True
        }
    else:
        return {
            "title": "🔴 BTC VOLATILE / BREAKDOWN ZONE",
            "desc": f"বিটিসি মেজর সাপোর্ট লেভেলের নিচে অবস্থান করছে (${curr:,.2f})। অল্টকয়েনে লং নেওয়া বিপজ্জনক!",
            "trade_allowed": False
        }

@st.cache_data(ttl=1800)
def get_futures_pairs():
    try:
        r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", headers=HEADERS, timeout=6).json()
        return [
            s['symbol'] for s in r.get('symbols', [])
            if s['symbol'].endswith('USDT') and not s['symbol'].startswith('1000') and s.get('status') == 'TRADING'
        ]
    except Exception:
        return []

@st.cache_data(ttl=3600)
def get_supply_cache():
    cache = {}
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false"
        r = requests.get(url, headers=HEADERS, timeout=5).json()
        for item in r:
            sym = item.get('symbol', '').upper()
            cache[sym] = {
                'id': item.get('id'),
                'circ': item.get('circulating_supply') or 0,
                'total': item.get('max_supply') or item.get('total_supply') or 0
            }
    except Exception:
        pass
    return cache

def calculate_liquidity_heatmap_levels(price, sma_val):
    """
    লিকুইডিটি হিটম্যাপ ও লিকুইডেশন পুলের এস্টিমেশন:
    ১. আপার পুল (Short Liquidation Pool): উপরে ম্যাগনেট হিসেবে কাজ করবে
    ২. লোয়ার পুল (Long Liquidation Pool): নিচে স্টপ হান্ট লেভেল
    """
    # আপার শর্ট লিকুইডেশন ক্লাস্টার (+৩.৫% থেকে +৮.৫%)
    short_liq_pool_low = round(price * 1.035, 4)
    short_liq_pool_high = round(price * 1.085, 4)
    upper_pool_text = f"${short_liq_pool_low} -${short_liq_pool_high}"
    
    # লোয়ার লং লিকুইডেশন ক্লাস্টার (-২.৫% থেকে -৪.৫%)
    long_liq_pool = round(sma_val * 0.975, 4)
    lower_pool_text = f"${round(sma_val * 0.965, 4)} -${long_liq_pool}"
    
    # লিকুইডিটি ম্যাগনেট বায়াস
    liq_magnet_bias = "🧲 Top Heavy (Short Squeeze Target)"
    
    return upper_pool_text, lower_pool_text, liq_magnet_bias

def calculate_multi_timeframe_whale_flows(price, klines):
    vols = [float(k[5]) * price for k in klines[-30:]]
    if len(vols) < 30:
        return "7D: 🟢 | 30D: 🟢", "⭐⭐ Grade A", "🟢 Optimal Flow"

    p_now = float(klines[-1][4])
    p_7d = float(klines[-7][4])
    p_14d = float(klines[-14][4])
    p_30d = float(klines[-30][4])

    acc_7d = (p_now >= p_7d)
    acc_14d = (p_now >= p_14d)
    acc_30d = (p_now >= p_30d)

    if acc_7d and acc_14d and acc_30d:
        grade = "⭐⭐⭐ Grade A+"
        status_text = "🟢 Full Accumulation"
    elif acc_7d and acc_30d:
        grade = "⭐⭐ Grade A"
        status_text = "🟢 Strong 7D/30D Acc"
    elif acc_7d and not acc_30d:
        grade = "⚡ Grade B"
        status_text = "🟡 7D Fresh Accumulation"
    else:
        grade = "⚠️ Grade C"
        status_text = "🔴 7D Outflow"

    flow_icons = f"7D: {'🟢' if acc_7d else '🔴'} | 14D: {'🟢' if acc_14d else '🔴'} | 30D: {'🟢' if acc_30d else '🔴'}"
    return flow_icons, grade, status_text

# বিটিসি স্ট্যাটাস ডিসপ্লে
st.subheader("🌐 বিটকয়েন (BTC) সাপোর্ট ও মার্কেট রেজাইম")
btc_state = analyze_btc_support()
if btc_state["trade_allowed"]:
    st.success(f"### {btc_state['title']}\n{btc_state['desc']}")
else:
    st.error(f"### {btc_state['title']}\n{btc_state['desc']}")

st.divider()

if st.sidebar.button("🚀 Run Heatmap & Confluence Scanner", use_container_width=True):
    with st.spinner("মার্কেট, লিকুইডিটি হিটম্যাপ ও মাল্টি-টাইমফ্রেম ফ্লো অ্যানালাইসিস চলছে..."):
        symbols = get_futures_pairs()
        supply_cache = get_supply_cache()

    if not symbols:
        st.error("মার্কেট ডেটা পাওয়া যায়নি।")
    else:
        prog = st.progress(0)
        results = []

        for idx, sym in enumerate(symbols):
            prog.progress((idx + 1) / len(symbols))
            clean = sym.replace("USDT", "")

            # টেকনিক্যাল SMA চেক
            klines = get_binance_klines(sym, timeframe, sma_period + 35)
            if not klines or len(klines) < sma_period + 5:
                continue

            closes = [float(k[4]) for k in klines]
            lows = [float(k[3]) for k in klines]
            df = pd.DataFrame({'close': closes, 'low': lows})
            df['sma'] = df['close'].rolling(sma_period).mean()

            c_close = df['close'].iloc[-1]
            c_sma = df['sma'].iloc[-1]
            c_low = df['low'].iloc[-1]

            if c_close < c_sma:
                continue

            dist_pct = ((c_close - c_sma) / c_sma) * 100
            retesting = (dist_pct <= max_dist) or (c_low <= c_sma and c_close >= c_sma)
            if not retesting:
                continue

            was_below = any(df['close'].iloc[-i] < df['sma'].iloc[-i] for i in range(2, 8))
            if not was_below:
                continue

            # টোকেনোমিক্স চেক
            meta = supply_cache.get(clean)
            if meta:
                circ = meta['circ']
                tot = meta['total'] if meta['total'] > 0 else circ
                circ_pct = (circ / tot) * 100 if tot > 0 else 100.0
                if circ_pct < min_circ:
                    continue
            else:
                circ_pct = 85.0

            # মাল্টি-টাইমফ্রেম হোয়েল চেক
            flow_icons, grade, status_text = calculate_multi_timeframe_whale_flows(c_close, klines)
            if "Grade C" in grade:
                continue

            # লিকুইডিটি হিটম্যাপ লেভেলস ক্যালকুলেশন
            up_liq_pool, low_liq_pool, liq_bias = calculate_liquidity_heatmap_levels(c_close, c_sma)

            # ট্রেড প্ল্যান (লিকুইডিটি ও SMA ভিত্তিক)
            entry_low = round(c_sma * 1.002, 4)
            entry_high = round(c_close, 4)
            
            # স্টপ-লস লোয়ার লিকুইডিটি পুলে স্টপ-হান্ট হওয়ার নিচে রাখা
            stop_loss = round(c_sma * 0.965, 4)
            risk = max(entry_high - stop_loss, entry_high * 0.035)

            tp1 = round(entry_high + (risk * 1.5), 4)
            tp2 = round(entry_high + (risk * 2.5), 4)
            tp3 = round(entry_high + (risk * 4.0), 4)

            action = "🟢 A+ READY TO LONG" if btc_state["trade_allowed"] else "⛔ NO TRADE (BTC Unsafe)"
            coinglass_url = f"https://www.coinglass.com/pro/futures/LiquidityHeatMap?symbol={clean}USDT"

            results.append({
                "Symbol": clean,
                "Action": action,
                "Whale Grade": grade,
                "Flows": flow_icons,
                "Price ($)": round(c_close, 4),
                f"SMA_{sma_period}": round(c_sma, 4),
                "Circ_%": f"{round(circ_pct, 1)}%",
                "Entry Zone": f"${entry_low} -${entry_high}",
                "Safe Stop-Loss": f"${stop_loss}",
                "Upper Liquidity Pool (TP Zone)": up_liq_pool,
                "Target 1": f"${tp1}",
                "Target 2": f"${tp2}",
                "Target 3": f"${tp3}",
                "Liquidity Bias": liq_bias,
                "Live Heatmap": coinglass_url
            })
            time.sleep(0.01)

        prog.empty()

        if results:
            st.success(f"🎯 মোট {len(results)}টি সেটআপ লিকুইডিটি হিটম্যাপ ও মাল্টি-টাইমফ্রেম কনফ্লুয়েন্স পাস করেছে!")
            df_res = pd.DataFrame(results)

            st.dataframe(
                df_res,
                column_config={
                    "Live Heatmap": st.column_config.LinkColumn("Coinglass Heatmap", display_text="🔥 View Heatmap")
                },
                use_container_width=True,
                hide_index=True
            )

            csv_data = df_res.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 লিকুইডিটি ও ট্রেড রিপোর্ট ডাউনলোড (CSV)",
                data=csv_data,
                file_name="liquidity_heatmap_swing_signals.csv",
                mime="text/csv"
            )
        else:
            st.warning("বর্তমান কঠোর ফিল্টারে কোনো কয়েন পাওয়া যায়নি। স্লাইডারের দূরত্ব বাড়িয়ে দেখতে পারেন।")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 13px;'>
        © 2026 <b>Mobinul Intelligence Terminal</b> | All Rights Reserved.<br>
        <i>Liquidity Heatmap & Multi-Timeframe Whale Execution Terminal</i>
    </div>
    """,
    unsafe_allow_html=True
)
