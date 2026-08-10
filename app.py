import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timezone
from modules.technical_engine import TechnicalAnalyzer
from modules.sentiment_engine import SentimentEngine
from modules.astro_engine import CelestialEngine
from core.aggregator import MasterAggregator
from core.risk_manager import RiskManager
from core.paper_execution import PaperExecutionEngine

st.set_page_config(page_title="Jarvis Trading Assistant", page_icon="🤖", layout="wide")

st.title("🤖 Jarvis Trading Assistant")
st.caption("Quantitative + Sentiment + Celestial research dashboard | PAPER MODE")

with st.sidebar:
    st.header("Controls")
    symbol = st.text_input("Symbol", "^NSEI")
    period = st.selectbox("History", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)
    interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=1)
    enable_finbert = st.checkbox("Enable FinBERT", value=False)
    news_query = st.text_input("News query", "Nifty 50 India markets")
    st.info("PAPER MODE: no real broker orders are sent.")

@st.cache_data(ttl=60)
def load_data(symbol, period, interval):
    try:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df.columns = [str(c).lower() for c in df.columns]
        required = ["open", "high", "low", "close", "volume"]
        if not all(c in df.columns for c in required):
            return pd.DataFrame()
        return df[required].dropna()
    except Exception:
        return pd.DataFrame()

df = load_data(symbol, period, interval)

if df.empty:
    st.error("Market data could not be loaded. Try ^NSEI, a different interval, or refresh the app.")
    st.stop()

tech = TechnicalAnalyzer(df.copy()).generate_features()
tech_signal = TechnicalAnalyzer(tech).evaluate_signals()

sentiment = SentimentEngine(enable_finbert=enable_finbert)
sent_score, headlines = sentiment.aggregate_market_sentiment(news_query)

astro = CelestialEngine()
astro_result = astro.analyze(datetime.now(timezone.utc))

aggregator = MasterAggregator()
decision = aggregator.decide(
    technical_score=tech_signal["score"],
    sentiment_score=sent_score,
    celestial_score=astro_result["score"],
    atr=float(tech["atr"].iloc[-1]) if pd.notna(tech["atr"].iloc[-1]) else 0.0,
    regime=tech_signal["regime"],
)

risk = RiskManager()
levels = risk.calculate(
    entry=float(tech["close"].iloc[-1]),
    atr=float(tech["atr"].iloc[-1]) if pd.notna(tech["atr"].iloc[-1]) else 0.0,
    side=decision["signal"],
)

last_price = float(tech["close"].iloc[-1])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Price", f"{last_price:,.2f}")
c2.metric("Signal", decision["signal"])
c3.metric("Confidence", f'{decision["confidence"]:+.0f}/100')
c4.metric("Technical Score", f'{tech_signal["score"]:+.0f}')

st.subheader("Market Chart")
chart_df = tech.tail(250).copy()
st.line_chart(chart_df[["close", "ema_fast", "ema_slow"]], height=430)

tcol, scol, acol = st.columns(3)

with tcol:
    st.subheader("📈 Technical")
    st.write(f"Trend: **{tech_signal['trend']}**")
    st.write(f"RSI: **{tech['rsi'].iloc[-1]:.2f}**")
    st.write(f"MACD: **{tech['macd'].iloc[-1]:.4f}**")
    st.write(f"ATR: **{tech['atr'].iloc[-1]:.2f}**")
    vwap = tech["vwap"].iloc[-1]
    st.write(f"VWAP: **{vwap:.2f}**" if pd.notna(vwap) else "VWAP: **Unavailable**")
    st.write(f"ADX: **{tech['adx'].iloc[-1]:.2f}**" if pd.notna(tech['adx'].iloc[-1]) else "ADX: **Unavailable**")

with scol:
    st.subheader("📰 Sentiment")
    st.write(f"Score: **{sent_score:+.2f}**")
    st.write(f"Status: **{sentiment.status(sent_score, headlines)}**")
    if headlines:
        for h in headlines[:5]:
            st.caption("• " + h)

with acol:
    st.subheader("🌙 Celestial")
    st.write(f"Score: **{astro_result['score']:+.0f}**")
    st.write(f"Moon: **{astro_result['moon_longitude']:.2f}°**")
    st.write(f"Nakshatra: **{astro_result['nakshatra']}**")
    st.write(f"Moon sign: **{astro_result['moon_sign']}**")
    st.caption("Research layer only; celestial signals are not scientifically validated predictors.")

st.subheader("🎯 Risk / Master Decision")
r1, r2, r3, r4, r5 = st.columns(5)
r1.metric("Technical", f'{tech_signal["score"]:+.0f}')
r2.metric("Sentiment", f'{sent_score:+.2f}')
r3.metric("Celestial", f'{astro_result["score"]:+.0f}')
r4.metric("Confidence", f'{decision["confidence"]:+.0f}')
r5.metric("Regime", decision["regime"])

st.write(f"**Reason:** {decision['reason']}")
if decision["signal"] in ("BUY", "SELL"):
    st.write(f"Entry: **{levels['entry']:.2f}** | SL: **{levels['sl']:.2f}** | TP1: **{levels['tp1']:.2f}** | TP2: **{levels['tp2']:.2f}**")
else:
    st.write("No trade: wait for stronger confluence.")

paper = PaperExecutionEngine()
if st.button("Record Current Decision in Paper Journal"):
    paper.record(decision, levels, symbol)
    st.success("Paper decision recorded. No real order was sent.")

st.caption("Data and model outputs can be delayed or unavailable. This application is for research/testing; it does not guarantee trading accuracy.")
