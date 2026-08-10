import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone
from pathlib import Path

from core.aggregator import MasterAggregator
from core.paper_execution import PaperExecutionEngine

st.set_page_config(page_title="Jarvis Trading Assistant V3", page_icon="🤖", layout="wide")

# ---------- Helpers ----------
@st.cache_data(ttl=60, show_spinner=False)
def load_market(symbol: str, interval: str):
    return MasterAggregator.fetch_market_data(symbol, interval)

def fmt(x, digits=2):
    if x is None or not np.isfinite(float(x)):
        return "—"
    return f"{float(x):,.{digits}f}"

# ---------- Header ----------
st.title("🤖 Jarvis Trading Assistant V3")
st.caption("Technical + News Sentiment + Celestial research dashboard | PAPER MODE")

with st.sidebar:
    st.header("Controls")
    symbol = st.text_input("Symbol", "^NSEI")
    interval = st.selectbox("Interval", ["5m", "15m", "30m", "1h"], index=1)
    history = st.selectbox("History", ["5d", "1mo", "3mo"], index=1)
    news_query = st.text_input("News query", "Nifty 50 India markets")
    enable_finbert = st.checkbox("Enable FinBERT (optional)", False)
    refresh = st.button("🔄 Refresh data", use_container_width=True)
    st.info("PAPER MODE: no real broker orders are sent.")
    st.caption("Educational/research tool. Signals are not guaranteed and should not be treated as financial advice.")

if refresh:
    st.cache_data.clear()
    st.rerun()

# ---------- Data ----------
try:
    df = load_market(symbol.strip() or "^NSEI", interval)
except Exception as e:
    st.error(f"Market data error: {e}")
    st.stop()

if df is None or df.empty:
    st.error("No market data returned. Try ^NSEI and 5m/15m again.")
    st.stop()

# Apply requested history locally when possible
try:
    now = pd.Timestamp.now(tz="UTC")
    if history == "5d":
        df = df[df.index >= now - pd.Timedelta(days=5)]
    elif history == "1mo":
        df = df[df.index >= now - pd.Timedelta(days=31)]
    elif history == "3mo":
        df = df[df.index >= now - pd.Timedelta(days=95)]
except Exception:
    pass

if len(df) < 30:
    st.warning(f"Only {len(df)} candles are available. Some indicators may be unavailable.")

# ---------- Engines ----------
agg = MasterAggregator()
result = agg.analyze(
    df=df,
    symbol=symbol.strip() or "^NSEI",
    news_query=news_query,
    enable_finbert=enable_finbert,
)

tech = result["technical"]
sent = result["sentiment"]
astro = result["celestial"]
decision = result["decision"]
levels = result["levels"]

# ---------- Top metrics ----------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Price", fmt(result["price"]))
c2.metric("Signal", decision["signal"])
c3.metric("Confidence", f'{decision["confidence"]:+.0f}/100')
c4.metric("Technical", f'{decision["technical_score"]:+.0f}')
c5.metric("Bull/Bear", f'{decision["bull_probability"]:.0f}% / {decision["bear_probability"]:.0f}%')

# ---------- Chart ----------
st.subheader("📈 Market Chart")
plot_df = df.tail(min(250, len(df))).copy()
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=plot_df.index, open=plot_df["open"], high=plot_df["high"],
    low=plot_df["low"], close=plot_df["close"], name="Price"
))
for col, name in [("ema_fast", "EMA Fast"), ("ema_slow", "EMA Slow"), ("vwap", "VWAP")]:
    if col in plot_df.columns:
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df[col], mode="lines", name=name))
fig.update_layout(
    height=560, xaxis_rangeslider_visible=False,
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h")
)
st.plotly_chart(fig, use_container_width=True)

# ---------- Engine cards ----------
a, b, c = st.columns(3)

with a:
    st.subheader("📈 Technical")
    st.write(f"Trend: **{tech['trend']}**")
    st.write(f"RSI: **{fmt(tech['rsi'])}**")
    st.write(f"MACD: **{fmt(tech['macd'], 4)}**")
    st.write(f"ATR: **{fmt(tech['atr'])}**")
    st.write(f"VWAP: **{fmt(tech['vwap'])}**")
    st.write(f"ADX: **{fmt(tech['adx'])}**")
    st.write(f"DI+: **{fmt(tech['di_plus'])}**")
    st.write(f"DI-: **{fmt(tech['di_minus'])}**")
    st.write(f"Technical score: **{tech['score']:+.0f}**")

with b:
    st.subheader("📰 Sentiment")
    st.write(f"Score: **{sent['score']:+.2f}**")
    st.write(f"Status: **{sent['status']}**")
    st.write(f"Articles used: **{sent['articles_used']}**")
    if sent["headlines"]:
        for h in sent["headlines"][:5]:
            st.caption("• " + h)
    else:
        st.caption("No usable news returned right now.")

with c:
    st.subheader("🌙 Celestial")
    st.write(f"Score: **{astro['score']:+.0f}**")
    st.write(f"Moon: **{fmt(astro['moon_longitude'])}°**")
    st.write(f"Moon sign: **{astro['moon_sign']}**")
    st.write(f"Nakshatra: **{astro['nakshatra']}**")
    st.write(f"Tithi: **{astro['tithi_name']} ({fmt(astro['tithi_number'], 0)})**")
    st.write(f"Retrograde: **{astro['retrograde']}**")
    st.caption("Celestial layer is experimental research, not a scientifically validated predictor.")

# ---------- Master Decision ----------
st.subheader("🎯 Master Decision")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Technical", f'{decision["technical_score"]:+.0f}')
m2.metric("Sentiment", f'{decision["sentiment_score"]:+.2f}')
m3.metric("Celestial", f'{decision["celestial_score"]:+.0f}')
m4.metric("Confidence", f'{decision["confidence"]:+.0f}')

st.info(
    f'Decision: **{decision["signal"]}** | '
    f'T/S/C = {decision["technical_score"]:+.0f}/{decision["sentiment_score"]:+.2f}/{decision["celestial_score"]:+.0f} | '
    f'weights = 0.65/0.25/0.10'
)

# ---------- Trade plan ----------
st.subheader("🎯 Trade Plan")
p1, p2, p3, p4, p5 = st.columns(5)
p1.metric("Direction", levels["direction"])
p2.metric("Entry", fmt(levels["entry"]))
p3.metric("Stop Loss", fmt(levels["stop_loss"]))
p4.metric("Target 1", fmt(levels["target1"]))
p5.metric("Target 2", fmt(levels["target2"]))

if decision["signal"] in ("BUY CALL", "BUY PUT"):
    st.success(
        f'Potential {decision["signal"]} setup | '
        f'Entry {fmt(levels["entry"])} | SL {fmt(levels["stop_loss"])} | '
        f'T1 {fmt(levels["target1"])} | T2 {fmt(levels["target2"])}'
    )
else:
    st.warning("⏳ No trade: wait for stronger multi-engine confluence.")

# ---------- Details ----------
with st.expander("🔬 Detailed Engine Data"):
    st.json({
        "technical": tech,
        "sentiment": sent,
        "celestial": astro,
        "decision": decision,
        "levels": levels,
    })

# ---------- Paper journal ----------
st.subheader("📝 Paper Trading")
journal = PaperExecutionEngine()
if st.button("Record Current Decision in Paper Journal"):
    journal.record({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "interval": interval,
        "signal": decision["signal"],
        "price": result["price"],
        "confidence": decision["confidence"],
        "entry": levels["entry"],
        "stop_loss": levels["stop_loss"],
        "target1": levels["target1"],
        "target2": levels["target2"],
    })
    st.success("Decision recorded in paper journal.")

try:
    trades = journal.read()
    if not trades.empty:
        st.dataframe(trades.tail(20), use_container_width=True, hide_index=True)
except Exception:
    pass
