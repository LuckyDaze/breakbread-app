from __future__ import annotations
import yfinance as yf
import streamlit as st

def get_yf_data(symbol: str, period: str = "1d"):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return None
        
        return {
            "symbol": symbol,
            "current_price": hist["Close"].iloc[-1],
            "52w_high": hist["High"].max(),
            "52w_low": hist["Low"].min(),
            "change": hist["Close"].iloc[-1] - hist["Close"].iloc[0],
            "change_percent": ((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0]) * 100
        }
    except Exception as e:
        st.error(f"Error fetching {symbol}: {e}")
        return None
import os
import pandas as pd
import streamlit as st
from app.banking import ensure_demo_users, USERS, TRANSACTIONS, send_money
from app.market_data import market_data, cached
from app.alt_investments import altx
from app.portfolio import diversification_score

# ---------- Page config ----------
icon_path = "assets/favicon.png"
st.set_page_config(
    page_title="Break Bread • Banking & Investing",
    page_icon=icon_path if os.path.exists(icon_path) else "🍞",
    layout="wide",
)

# ---------- Header ----------
logo_path = "assets/BB_logo.png"
cols = st.columns([1, 6])
with cols[0]:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.header("🍞")
with cols[1]:
    st.title("Break Bread")
    st.caption("_**Break Bread. Build Wealth.**_  — unified banking and investing")

st.divider()

# Seed demo users
ensure_demo_users()

# ---------- Sidebar ----------
st.sidebar.subheader("Market Overview")
for tkr, name in {"^GSPC": "S&P 500", "^IXIC": "NASDAQ", "BTC-USD": "Bitcoin"}.items():
    data = get_yf_data(tkr, "5d")  # 5-day window gives some % change
    if data:
        st.sidebar.metric(
            name,
            f"${data['current_price']:.2f}",
            f"{data['change_percent']:.2f}%"
        )
    else:
        st.sidebar.write(f"{name}: n/a")

# ---------- Tabs ----------
tab_dash, tab_bank, tab_market, tab_startups, tab_royalties, tab_metals, tab_edu = st.tabs(
    ["📊 Dashboard","💸 Banking","📈 Market Data","🚀 Startups","🎵 Royalties","🥇 Metals","📚 Education"]
)

# ----- Dashboard -----
with tab_dash:
    st.subheader("Portfolio Snapshot")
    # mock allocation example
    alloc = {"stocks":45,"bonds":20,"crypto":8,"startups":12,"royalties":5,"precious_metals":10}
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Diversification Score", f"{diversification_score(alloc)}/100")
    with c2: st.metric("Alt Investments", "27%", "Target 25%")
    with c3: st.metric("YTD Return", "+6.1%")
    with c4: st.metric("Monthly Cash Flow", "$420")

    st.subheader("Allocation")
    df_alloc = pd.DataFrame({"Asset Class": list(alloc.keys()), "Percent": list(alloc.values())})
    st.bar_chart(df_alloc.set_index("Asset Class")["Percent"], use_container_width=True)

    st.subheader("Recent Activity")
    if TRANSACTIONS:
        view = pd.DataFrame([{
            "When": t["ts"].strftime("%Y-%m-%d"),
            "Type": "P2P Transfer",
            "Amount": f"${t['amount']:.2f}",
            "Fee": f"${t['fee']:.2f}",
            "To": t["recipient_id"]
        } for t in sorted(TRANSACTIONS, key=lambda x: x["ts"], reverse=True)[:10]])
        st.dataframe(view, use_container_width=True)
    else:
        st.info("No recent transactions yet.")

# ----- Banking -----
with tab_bank:
    st.subheader("Send Money")
    colA, colB = st.columns(2)
    with colA:
        recipient = st.text_input("Recipient (username / email)", value="janedoe")
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
        note = st.text_input("Note (optional)")
        if st.button("Send", type="primary"):
            ok, msg = send_money(who, recipient, amount, note)
            st.success(msg) if ok else st.error(msg)
    with colB:
        st.subheader("Balances")
        st.write({u["app_id"]: f"${u['balance']:.2f}" for u in USERS.values()})

# ----- Market Data -----
with tab_market:
    st.subheader("Research")
    c1,c2,c3 = st.columns([3,1.2,1.2])
    with c1:
        sym = st.text_input("Symbol / Crypto", value="AAPL", placeholder="e.g., AAPL, TSLA, BTC-USD")
    with c2:
        period = st.selectbox("Period", ["1d","5d","1mo","3mo","6mo","1y","2y","5y"], index=5)
    with c3:
        ctype = st.selectbox("Chart", ["Line","Candlestick"])

    if st.button("Load Chart", type="primary"):
        data = cached(sym.upper(), period)
        if not data or data["historical"] is None or data["historical"].empty:
            st.error("No data returned. Try another period or symbol.")
        else:
            k1,k2,k3 = st.columns(3)
            with k1: st.metric("Price", f"${data['current_price']:.2f}", f"{data['change']:.2f} ({data['change_percent']:.2f}%)")
            with k2: st.metric("52W High", f"${data['52w_high']:.2f}")
            with k3: st.metric("52W Low", f"${data['52w_low']:.2f}")
            fig = market_data.chart(data["historical"], sym.upper(), ctype.lower())
            if fig: st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Quick Metals**")
    cols = st.columns(4)
    for i, (ticker, label) in enumerate([("GC=F","Gold"),("SI=F","Silver"),("PL=F","Platinum"),("PA=F","Palladium")]):
        try:
            d = cached(ticker, "1d")
            with cols[i]: st.metric(label, f"${d['current_price']:.2f}", f"{d['change_percent']:.2f}%")
        except Exception:
            with cols[i]: st.write(f"{label}: n/a")

# ----- Startups -----
with tab_startups:
    st.subheader("Vetted Startup Opportunities")
    platform = st.selectbox("Platform", ["All","StartEngine","Republic","Wefunder"])
    for opp in altx.startups("all" if platform=="All" else platform.lower()):
        st.markdown(f"""
        <div style="border:1px solid #ddd;border-radius:10px;padding:12px;margin:8px 0;">
            <h4 style="margin:0">{opp['company']}</h4>
            <p style="margin:4px 0 10px 0">{opp['description']}</p>
            <b>Platform:</b> {opp['platform'].title()} &nbsp;|&nbsp;
            <b>Min:</b> ${opp['min_investment']} &nbsp;|&nbsp;
            <b>Valuation:</b> ${opp['valuation']:,} &nbsp;|&nbsp;
            <b>Progress:</b> {opp['raised_percentage']}% &nbsp;|&nbsp;
            <b>Days Left:</b> {opp['days_remaining']}
        </div>
        """, unsafe_allow_html=True)

# ----- Royalties -----
with tab_royalties:
    st.subheader("Royalty / IP Opportunities")
    t = st.selectbox("Asset Type", ["All","Music","Patents"])
    for r in altx.royalties("all" if t=="All" else t.lower()):
        st.markdown(f"""
        <div style="border:1px solid #ddd;border-radius:10px;padding:12px;margin:8px 0;">
            <h4 style="margin:0">{r['name']}</h4>
            <p style="margin:4px 0 10px 0"><b>Type:</b> {r['asset_type'].title()} • <b>Platform:</b> {r['platform'].title()}</p>
            <b>Min:</b> ${r['min_investment']} &nbsp;|&nbsp;
            <b>Expected Yield:</b> {r['expected_yield']}% &nbsp;|&nbsp;
            <b>Auction Ends:</b> {r['auction_end']}
        </div>
        """, unsafe_allow_html=True)

# ----- Metals -----
with tab_metals:
    st.subheader("Buy Precious Metals (demo)")
    metal = st.selectbox("Metal", ["Gold","Silver","Platinum","Palladium"])
    amt = st.number_input("Amount ($)", min_value=100.0, step=50.0)
    storage = st.radio("Storage", ["Digital Certificate","Secured Vault","Physical Delivery"], horizontal=True)
    if st.button("Purchase", type="primary"):
        st.success(f"Purchased ${amt:.2f} of {metal} via {storage}")

# ----- Education -----
with tab_edu:
    st.subheader("Financial Education")
    for item in altx.education():
        with st.expander(f"{item.title} — {item.source.title()} ({item.difficulty})"):
            st.write(item.content)
            st.caption(f"Published: {item.publish_date.strftime('%b %d, %Y')}")
            st.markdown(f"[Read more]({item.url})")
