import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from core.data import load_market_data
from core.indicators import add_indicators
from core.levels import support_resistance
from core.decision import build_decision
from core.astro import get_sidereal_positions
from modules.gift_nifty import load_gift_nifty
from modules.news import load_news

st.set_page_config(page_title='Jarvis Trading Assistant', page_icon='🤖', layout='wide')
st.title('🤖 Jarvis Trading Assistant')
st.caption('NIFTY technical + market context + live sidereal Lahiri planetary positions | PAPER MODE')
with st.sidebar:
    st.header('Controls')
    symbol = st.text_input('Symbol', '^NSEI')
    interval = st.selectbox('Interval', ['1m','5m','15m','30m','1h','1d'], index=2)
    period = st.selectbox('History', ['5d','1mo','3mo','6mo','1y'], index=1)
    show_sr = st.checkbox('Support / Resistance', True)
    show_ma = st.checkbox('Moving averages', True)
    show_vwap = st.checkbox('VWAP', True)
    show_volume = st.checkbox('Volume', True)
    news_query = st.text_input('News query', 'Nifty 50 India markets')
    st.info('PAPER MODE: no broker orders are sent.')
try:
    df = add_indicators(load_market_data(symbol, period, interval))
except Exception as e:
    st.error(f'Market data error: {e}')
    st.stop()
if df.empty or len(df) < 30:
    st.warning('Not enough candles returned. Try 5m/15m with 1mo or 3mo history.')
    st.stop()
levels = support_resistance(df)
decision = build_decision(df, levels)
c1,c2,c3,c4=st.columns(4)
c1.metric('Price',f"{df['Close'].iloc[-1]:,.2f}")
c2.metric('Signal',decision['signal'])
c3.metric('Confidence',f"{decision['confidence']:.0f}/100")
c4.metric('Technical Score',f"{decision['technical_score']:+.0f}")
st.subheader('📈 Market Chart')
rows=2 if show_volume else 1
fig=make_subplots(rows=rows,cols=1,shared_xaxes=True,vertical_spacing=0.03,row_heights=[0.78,0.22] if show_volume else [1.0])
fig.add_trace(go.Candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close,name='NIFTY 50',increasing_line_color='#26a69a',decreasing_line_color='#ef5350'),row=1,col=1)
if show_ma:
    for col,name,dash in [('EMA20','EMA 20',None),('EMA50','EMA 50',None),('SMA200','SMA 200','dot')]:
        fig.add_trace(go.Scatter(x=df.index,y=df[col],name=name,line=dict(width=1.6,dash=dash) if dash else dict(width=1.6)),row=1,col=1)
if show_vwap and df.VWAP.notna().any():
    fig.add_trace(go.Scatter(x=df.index,y=df.VWAP,name='VWAP',line=dict(width=1.8)),row=1,col=1)
if show_sr:
    for price,name in [(levels['support'],'Support'),(levels['resistance'],'Resistance')]:
        fig.add_hline(y=price,line_dash='dash',annotation_text=f'{name} {price:,.2f}',annotation_position='top left',row=1,col=1)
if show_volume:
    fig.add_trace(go.Bar(x=df.index,y=df.Volume,name='Volume',opacity=0.45),row=2,col=1)
fig.update_layout(height=720,template='plotly_dark',xaxis_rangeslider_visible=False,hovermode='x unified',margin=dict(l=20,r=20,t=20,b=20),legend=dict(orientation='h',y=1.02))
fig.update_yaxes(title_text='Price',row=1,col=1)
if show_volume: fig.update_yaxes(title_text='Volume',row=2,col=1)
st.plotly_chart(fig,use_container_width=True)
tech,ctx,astro=st.columns(3)
with tech:
    st.subheader('📈 Technical')
    st.write(f"**Trend:** {decision['trend']}")
    st.write(f"**RSI:** {df.RSI.iloc[-1]:.2f}")
    st.write(f"**MACD:** {df.MACD.iloc[-1]:.4f}")
    st.write(f"**ATR:** {df.ATR.iloc[-1]:.2f}")
    st.write(f"**VWAP:** {df.VWAP.iloc[-1]:,.2f}" if pd.notna(df.VWAP.iloc[-1]) else '**VWAP:** unavailable')
    st.write(f"**ADX:** {df.ADX.iloc[-1]:.2f}")
    st.write(f"**DI+:** {df.DI_PLUS.iloc[-1]:.2f}")
    st.write(f"**DI-:** {df.DI_MINUS.iloc[-1]:.2f}")
    st.write(f"**Support:** {levels['support']:,.2f}")
    st.write(f"**Resistance:** {levels['resistance']:,.2f}")
with ctx:
    st.subheader('📰 Market Context')
    news=load_news(news_query)
    if news:
        for item in news[:5]: st.write('• '+item)
    else: st.write('No news returned.')
    gift=load_gift_nifty()
    st.subheader('🌏 GIFT Nifty')
    if gift['available']: st.metric('GIFT Nifty',f"{gift['price']:,.2f}",f"{gift['change_pct']:+.2f}%"); st.caption(gift['source'])
    else: st.warning(gift['message'])
with astro:
    st.subheader('🌙 Live Vedic Transit — Sidereal Lahiri')
    a=get_sidereal_positions()
    if a['available']:
        st.write(f"**Moon:** {a['moon_sign']} {a['moon_degree']:.2f}°")
        st.write(f"**Nakshatra:** {a['nakshatra']}")
        st.write(f"**Tithi:** {a['tithi']}")
        st.write(f"**Retrograde:** {', '.join(a['retrograde']) or 'None'}")
        st.dataframe(pd.DataFrame(a['planets']),hide_index=True,use_container_width=True)
    else: st.error(a['message'])
st.subheader('🎯 Master Decision')
m1,m2,m3,m4=st.columns(4)
m1.metric('Technical',f"{decision['technical_score']:+.0f}"); m2.metric('Context',f"{decision['context_score']:+.0f}"); m3.metric('Celestial',f"{decision['celestial_score']:+.0f}"); m4.metric('Confidence',f"{decision['confidence']:.0f}")
st.info(f"Decision: **{decision['signal']}** | Entry {decision['entry']:,.2f} | SL {decision['stop']:,.2f} | T1 {decision['target1']:,.2f} | T2 {decision['target2']:,.2f}")
st.caption('Astrology is an experimental research layer and is not a scientifically validated predictor. Paper mode only.')
