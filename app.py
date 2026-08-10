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
    interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=2)
    enable_finbert = st.checkbox("Enable FinBERT", value=False)
    news_query = st.text_input("News query", "Nifty 50 India markets")
    st.info("PAPER MODE: no real broker orders are sent.")

@st.cache_data(ttl=60)
def load_data(symbol, period, interval):
    try:
        df = yf.download(
            symbol, period=period, interval=interval,
            auto_adjust=False, progress=False, group_by="column"
        )
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [str(c[0]).lower() for c in df.columns]
        else:
            df.columns = [str(c).lower() for c in df.columns]
        required = ["open", "high", "low", "close", "volume"]
        if not all(c in df.columns for c in required):
            return pd.DataFrame()
        out = df[required].copy()
        for c in required:
            out[c] = pd.to_numeric(out[c], errors="coerce")
        return out.dropna(subset=["open", "high", "low", "close"])
    except Exception as e:
        st.error(f"Data error: {e}")
        return pd.DataFrame()

df = load_data(symbol, period, interval)
if df.empty:
    st.error("Market data could not be loaded. Try ^NSEI or refresh the app.")
    st.stop()

tech_engine = TechnicalAnalyzer(df)
tech = tech_engine.generate_features()
tech_signal = tech_engine.evaluate_signals()

sentiment = SentimentEngine(enable_finbert=enable_finbert)
sent_score, headlines = sentiment.aggregate_market_sentiment(news_query)

astro = CelestialEngine()
astro_result = astro.analyze(datetime.now(timezone.utc))

aggregator = MasterAggregator()
decision = aggregator.decide(
    technical=tech_signal,
    sentiment_score=sent_score,
    celestial=astro_result,
)

last_price = float(tech["close"].iloc[-1])
atr = float(tech["atr"].iloc[-1]) if pd.notna(tech["atr"].iloc[-1]) else 0.0

risk = RiskManager()
levels = risk.calculate(
    entry=last_price,
    atr=atr,
    action=decision["action"],
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Price", f"{last_price:,.2f}")
c2.metric("Action", decision["action"])
c3.metric("Confidence", f'{decision["confidence"]:+.0f}/100')
c4.metric("Technical", f'{tech_signal["score"]:+.0f}')
c5.metric("Regime", decision["regime"])

st.subheader("📊 Market Chart")
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    chart_df = tech.tail(250).copy()
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05, row_heights=[0.72, 0.28]
    )
    fig.add_trace(go.Candlestick(
        x=chart_df.index, open=chart_df["open"], high=chart_df["high"],
        low=chart_df["low"], close=chart_df["close"], name="Price"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["ema_fast"],
                             name="EMA 12", mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["ema_slow"],
                             name="EMA 26", mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["vwap"],
                             name="VWAP", mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["rsi"],
                             name="RSI", mode="lines"), row=2, col=1)
    fig.add_hline(y=70, row=2, col=1)
    fig.add_hline(y=30, row=2, col=1)
    fig.update_layout(
        height=650, xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=20, b=10),
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
except Exception:
    st.line_chart(tech[["close", "ema_fast", "ema_slow", "vwap"]].tail(250), height=500)

tcol, scol, acol = st.columns(3)

with tcol:
    st.subheader("📈 Technical")
    st.write(f"Trend: **{tech_signal['trend']}**")
    st.write(f"RSI: **{tech['rsi'].iloc[-1]:.2f}**")
    st.write(f"MACD: **{tech['macd'].iloc[-1]:.4f}**")
    st.write(f"ATR: **{atr:.2f}**")
    vwap = tech["vwap"].iloc[-1]
    st.write(f"VWAP: **{vwap:.2f}**" if pd.notna(vwap) else "VWAP: **Unavailable**")
    adx = tech["adx"].iloc[-1]
    st.write(f"ADX: **{adx:.2f}**" if pd.notna(adx) else "ADX: **Unavailable**")
    st.write(f"DI+: **{tech['di_plus'].iloc[-1]:.2f}**")
    st.write(f"DI-: **{tech['di_minus'].iloc[-1]:.2f}**")

with scol:
    st.subheader("📰 Sentiment")
    st.write(f"Score: **{sent_score:+.2f}**")
    st.write(f"Status: **{sentiment.status(sent_score, headlines)}**")
    for h in headlines[:7]:
        st.caption("• " + h)

with acol:
    st.subheader("🌙 Celestial")
    st.write(f"Score: **{astro_result['score']:+.0f}**")
    st.write(f"Moon: **{astro_result['moon_longitude']:.2f}°**")
    st.write(f"Nakshatra: **{astro_result['nakshatra']}**")
    st.write(f"Moon sign: **{astro_result['moon_sign']}**")
    st.write(f"Tithi: **{astro_result['tithi']:.1f}**")
    st.write(f"Retrograde: **{', '.join(astro_result['retrograde']) or 'None'}**")
    st.caption("Celestial/SBC/Ashtakavarga values are an experimental research layer, not a scientifically validated predictor.")

st.subheader("🎯 Master Decision")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Technical", f'{tech_signal["score"]:+.0f}')
m2.metric("Sentiment", f'{sent_score:+.2f}')
m3.metric("Celestial", f'{astro_result["score"]:+.0f}')
m4.metric("Confidence", f'{decision["confidence"]:+.0f}')

st.info(f"**Decision:** {decision['action']}  |  {decision['reason']}")

if decision["action"] in ("BUY CALL", "BUY PUT", "SELL / EXIT"):
    st.subheader("🛡️ Risk Levels")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Entry", f'{levels["entry"]:,.2f}')
    r2.metric("Stop Loss", f'{levels["sl"]:,.2f}')
    r3.metric("Target 1", f'{levels["tp1"]:,.2f}')
    r4.metric("Target 2", f'{levels["tp2"]:,.2f}')
else:
    st.write("⏳ No trade: wait for stronger multi-engine confluence.")

with st.expander("🔬 Detailed Engine Data"):
    st.json({
        "technical": tech_signal,
        "sentiment": {"score": sent_score, "headlines": headlines[:10]},
        "celestial": astro_result,
        "master": decision,
    })

paper = PaperExecutionEngine()
if st.button("Record Current Decision in Paper Journal"):
    paper.record({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "price": last_price,
        "action": decision["action"],
        "confidence": decision["confidence"],
        "technical": tech_signal["score"],
        "sentiment": sent_score,
        "celestial": astro_result["score"],
        "sl": levels["sl"],
        "tp1": levels["tp1"],
        "tp2": levels["tp2"],
    })
    st.success("Decision recorded in paper journal.")
