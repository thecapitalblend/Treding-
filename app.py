import streamlit as st
import pandas as pd, numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone
from modules.technical_engine import TechnicalAnalyzer
from modules.sentiment_engine import SentimentEngine
from modules.astro_engine import CelestialEngine
from core.aggregator import MasterAggregator
from core.risk_manager import RiskManager

st.set_page_config(page_title="Jarvis Trading Assistant", page_icon="🤖", layout="wide")
st.title("🤖 Jarvis Trading Assistant")
st.caption("Quantitative + Sentiment + Celestial research dashboard | PAPER MODE")

with st.sidebar:
    st.header("Controls")
    symbol=st.text_input("Symbol","^NSEI")
    period=st.selectbox("History",["5d","1mo","3mo","6mo"],1)
    interval=st.selectbox("Interval",["5m","15m","30m","1h","1d"],0)
    finbert=st.checkbox("Enable FinBERT",False)
    if st.button("🔄 Refresh Market Data"): st.cache_data.clear()
    st.warning("PAPER MODE: no real broker orders are sent.")

@st.cache_data(ttl=60)
def load_data(symbol,period,interval):
    import yfinance as yf
    d=yf.download(symbol,period=period,interval=interval,auto_adjust=False,progress=False)
    if d is None or d.empty: return pd.DataFrame()
    if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
    d.columns=[str(c).lower() for c in d.columns]
    return d[["open","high","low","close","volume"]].dropna(subset=["close"])

df=load_data(symbol,period,interval)
if df.empty: st.error("Market data could not be loaded."); st.stop()

tech=TechnicalAnalyzer(df).generate_features()
tv=TechnicalAnalyzer(tech).evaluate()
sent=SentimentEngine(finbert).market_score([])
cel=CelestialEngine().analyze(datetime.now(timezone.utc))
dec=MasterAggregator().calculate(tv,sent,cel)
risk=RiskManager().calculate(float(tech.close.iloc[-1]),tv["atr"],dec["signal"])

a,b,c,d=st.columns(4)
a.metric("Price",f'{tech.close.iloc[-1]:,.2f}')
b.metric("Signal",dec["signal"])
c.metric("Confidence",f'{dec["confidence"]:+.0f}/100')
d.metric("Technical Score",f'{tv["score"]:+.0f}')

st.subheader("Market Chart")
fig=go.Figure()
fig.add_trace(go.Candlestick(x=tech.index,open=tech.open,high=tech.high,low=tech.low,close=tech.close,name="Price"))
fig.add_trace(go.Scatter(x=tech.index,y=tech.ema_fast,name="EMA Fast"))
fig.add_trace(go.Scatter(x=tech.index,y=tech.ema_slow,name="EMA Slow"))
fig.update_layout(height=520,template="plotly_dark",xaxis_rangeslider_visible=False)
st.plotly_chart(fig,use_container_width=True)

x,y,z=st.columns(3)
with x:
    st.subheader("📈 Technical")
    st.write(f"Trend: **{tv['trend']}**")
    st.write(f"RSI: **{tv['rsi']:.2f}**")
    st.write(f"MACD: **{tv['macd']:.4f}**")
    st.write(f"ATR: **{tv['atr']:.2f}**")
    st.write(f"VWAP: **{tv['vwap']:.2f}**")
with y:
    st.subheader("📰 Sentiment")
    st.write(f"Score: **{sent['score']:+.2f}**")
    st.write(f"Status: **{sent['label']}**")
with z:
    st.subheader("🌙 Celestial")
    st.write(f"Score: **{cel['score']:+.0f}**")
    st.write(f"Moon: **{cel['moon_longitude']:.2f}°**")
    st.write(f"Nakshatra: **{cel['moon_nakshatra']}**")
    st.caption("Experimental research layer; not a validated predictor.")

st.subheader("🎯 Master Decision")
q1,q2,q3,q4=st.columns(4)
q1.metric("Technical",f'{dec["components"]["technical"]:+.0f}')
q2.metric("Sentiment",f'{dec["components"]["sentiment"]:+.0f}')
q3.metric("Celestial",f'{dec["components"]["celestial"]:+.0f}')
q4.metric("Confidence",f'{dec["confidence"]:+.0f}')
st.info(dec["reason"])

st.subheader("🛡️ Paper Risk Plan")
r1,r2,r3,r4=st.columns(4)
r1.metric("Entry",f'{risk["entry"]:,.2f}')
r2.metric("Stop Loss",f'{risk["stop_loss"]:,.2f}')
r3.metric("Target 1",f'{risk["target1"]:,.2f}')
r4.metric("Target 2",f'{risk["target2"]:,.2f}')

with st.expander("Technical Data"):
    st.dataframe(tech.tail(30),use_container_width=True)
