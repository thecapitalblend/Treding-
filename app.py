from datetime import datetime
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
import yaml
from dotenv import load_dotenv

from core.aggregator import MasterAggregator
from core.paper_execution import PaperExecutionEngine
from core.risk_manager import RiskManager
from modules.astro_engine import CelestialEngine
from modules.sentiment_engine import SentimentEngine
from modules.technical_engine import TechnicalAnalyzer

load_dotenv()

st.set_page_config(page_title="Jarvis Trading Assistant", page_icon="🤖", layout="wide")

@st.cache_data(ttl=60)
def load_market_data(symbol, period, interval):
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.columns = [str(c).lower() for c in df.columns]
    return df.dropna(subset=["open","high","low","close"])

def load_config():
    with open("config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

st.title("🤖 Jarvis Trading Assistant")
st.caption("Quantitative + Sentiment + Celestial research dashboard | PAPER MODE")

with st.sidebar:
    st.header("Controls")
    symbol = st.text_input("Symbol", os.getenv("DEFAULT_SYMBOL", cfg["app"]["default_symbol"]))
    period = st.selectbox("History", ["5d","1mo","3mo","6mo"], index=1)
    interval = st.selectbox("Interval", ["5m","15m","30m","1h","1d"], index=0)
    finbert_enabled = st.checkbox("Enable FinBERT", os.getenv("FINBERT_ENABLED","false").lower()=="true")
    st.warning("PAPER MODE: no real broker orders are sent.")

df = load_market_data(symbol, period, interval)
if df.empty:
    st.error("No market data returned. Check symbol/interval.")
    st.stop()

tech = TechnicalAnalyzer(
    cfg["technical"]["ema_fast"], cfg["technical"]["ema_slow"],
    cfg["technical"]["rsi_length"], cfg["technical"]["atr_length"]
)
features = tech.generate_features(df)
technical = tech.evaluate(features)

st.subheader("Market Chart")
fig = go.Figure()
fig.add_trace(go.Candlestick(x=features.index, open=features["open"], high=features["high"],
                              low=features["low"], close=features["close"], name="Price"))
fig.add_trace(go.Scatter(x=features.index, y=features["ema_fast"], name="EMA Fast"))
fig.add_trace(go.Scatter(x=features.index, y=features["ema_slow"], name="EMA Slow"))
fig.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

c1,c2,c3,c4 = st.columns(4)
c1.metric("Technical", f"{technical['score']:.1f}")
c2.metric("RSI", f"{technical.get('rsi',0):.2f}")
c3.metric("ATR", f"{technical.get('atr',0):.2f}")
c4.metric("Signal", technical["signal"])

st.subheader("📰 Sentiment Engine")
headline_text = st.text_area("Latest financial headlines (one per line)")
headlines = [x.strip() for x in headline_text.splitlines() if x.strip()]
sentiment_score = SentimentEngine(finbert_enabled).aggregate(headlines)
st.metric("Sentiment Score", f"{sentiment_score:+.3f}")

st.subheader("🌌 Celestial Engine")
astro_result = CelestialEngine().research_score(datetime.now())
st.metric("Celestial Research Score", f"{astro_result['score']:+.1f}", astro_result["label"])

rows = []
for p in astro_result["positions"].values():
    rows.append({"Planet":p.name,"Longitude":round(p.longitude,4),"Zodiac":p.zodiac,
                 "Nakshatra":p.nakshatra,"Retrograde":p.retrograde})
if rows:
    with st.expander("Planetary positions"):
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.subheader("🧠 Master Decision")
agg = MasterAggregator(
    cfg["aggregator"]["technical_weight"], cfg["aggregator"]["sentiment_weight"],
    cfg["aggregator"]["celestial_weight"], cfg["aggregator"]["buy_threshold"],
    cfg["aggregator"]["sell_threshold"], cfg["aggregator"]["risk_off_threshold"]
)
price = float(features["close"].iloc[-1])
atr = float(technical.get("atr",0) or 0)
decision = agg.decide(technical["score"], sentiment_score, astro_result["score"], atr, price)

m1,m2,m3 = st.columns(3)
m1.metric("Confidence", f"{decision.confidence:+.1f}/100")
m2.metric("Action", decision.action)
m3.metric("Regime", decision.regime)
st.info(decision.explanation)

st.subheader("🛡️ Risk Manager")
risk = RiskManager(
    cfg["risk"]["account_size"], cfg["risk"]["risk_per_trade_pct"],
    cfg["risk"]["atr_stop_multiplier"], cfg["risk"]["max_quantity"]
)
risk_side = "BUY" if decision.confidence >= 0 else "SELL"
risk_result = risk.calculate(price, atr, risk_side)
r1,r2,r3 = st.columns(3)
r1.metric("Suggested Qty", risk_result["quantity"])
r2.metric("ATR Stop", risk_result["stop"] if risk_result["stop"] else "N/A")
r3.metric("Risk Amount", f"₹{risk_result['risk_amount']:,.0f}")

st.subheader("🧪 Paper Execution")
paper = PaperExecutionEngine()
if st.button("Simulate Current Signal"):
    if decision.action in {"BUY","SELL"}:
        order = paper.place_order(symbol, decision.action, risk_result["quantity"], price)
        st.success(f"Paper order: {order['side']} {order['quantity']} @ {order['price']}")
        st.json(order)
    else:
        st.warning("No executable BUY/SELL signal right now.")

st.subheader("📋 Technical Details")
st.write(technical["reason"])
st.caption("Research software only. Validate every rule with backtesting and paper trading before live execution.")
