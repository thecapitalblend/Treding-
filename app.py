import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from core.data import load_market_data
from core.indicators import add_indicators
from core.levels import support_resistance
from core.decision import build_decision, signal_history
from core.astro import get_sidereal_positions
from core.chakra import run_all_chakras
from modules.gift_nifty import load_gift_nifty
from modules.news import load_news
from modules.tv_widget import render_tradingview_chart, INTERVAL_MAP
from core.broker_angelone import get_nifty_ltp
from core.pivots import get_pivots
from core.mtf import mtf_confirmation
from core.backtest import backtest
from core.events import expiry_flag
from core.risk import position_size
from modules.options_data import get_india_vix, get_option_chain_summary
from modules.global_cues import get_global_cues

# Cache expensive network/computation calls so the app stays smooth on every
# widget interaction (Streamlit reruns the whole script on each change).
load_market_data = st.cache_data(ttl=60)(load_market_data)
load_gift_nifty = st.cache_data(ttl=30)(load_gift_nifty)
load_news = st.cache_data(ttl=300)(load_news)
get_sidereal_positions = st.cache_data(ttl=300)(get_sidereal_positions)
run_all_chakras = st.cache_data(ttl=300)(run_all_chakras)
get_nifty_ltp = st.cache_data(ttl=5)(get_nifty_ltp)
get_pivots = st.cache_data(ttl=3600)(get_pivots)
mtf_confirmation = st.cache_data(ttl=60)(mtf_confirmation)
get_india_vix = st.cache_data(ttl=60)(get_india_vix)
get_option_chain_summary = st.cache_data(ttl=90)(get_option_chain_summary)
get_global_cues = st.cache_data(ttl=120)(get_global_cues)

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
    chart_source = st.radio('Chart source', ['TradingView live embed', 'Custom (Plotly + signals)'], index=0)
    news_query = st.text_input('News query', 'Nifty 50 India markets')
    st.divider()
    st.subheader('Risk management')
    capital = st.number_input('Capital (INR)', min_value=10000, value=200000, step=10000)
    risk_pct = st.slider('Risk per trade (%)', 0.25, 5.0, 1.0, 0.25)
    lot_size = st.number_input('NIFTY lot size', min_value=1, value=75, step=1, help='Check current NSE lot size -- it changes periodically.')
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
raw_signals, signal_counts, signal_transitions = signal_history(df)

exp = expiry_flag()
if exp['expiry_today']:
    st.error(f"⚠️ {exp['note']}")

mtf = mtf_confirmation(symbol, interval, decision['trend'] if decision['trend'] != 'NEUTRAL' else ('BULLISH' if decision['technical_score']>0 else 'BEARISH'))

c1,c2,c3,c4=st.columns(4)
if symbol in ('^NSEI', 'NIFTY', 'NIFTY50', 'NIFTY 50'):
    live = get_nifty_ltp()
    if live.get('available'):
        c1.metric('Price (Angel One LIVE)', f"{live['price']:,.2f}", f"{live['price']-live['close']:+,.2f}" if live.get('close') else None)
    else:
        c1.metric('Price (delayed, yfinance)', f"{df['Close'].iloc[-1]:,.2f}")
        if 'not set' not in live.get('message',''):
            st.sidebar.caption(f"Angel One live feed: {live.get('message')}")
else:
    c1.metric('Price',f"{df['Close'].iloc[-1]:,.2f}")
c2.metric('Signal',decision['signal'])
if mtf.get('available'):
    badge = '✅ MTF Confirmed' if mtf['aligned'] else '⚠️ MTF Conflict'
    c3.metric('Confidence',f"{decision['confidence']:.0f}/100", badge)
else:
    c3.metric('Confidence',f"{decision['confidence']:.0f}/100")
c4.metric('Technical Score',f"{decision['technical_score']:+.0f}")
st.subheader('📈 Market Chart')
if chart_source == 'TradingView live embed':
    render_tradingview_chart(symbol=symbol, interval=INTERVAL_MAP.get(interval, '15'), height=720)
    st.caption('Live chart embedded directly from TradingView. BUY CALL/PUT markers below use our own signal engine and only appear on the custom chart view.')
else:
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
    buy_call_idx=df.index[raw_signals=='BUY CALL']
    buy_put_idx=df.index[raw_signals=='BUY PUT']
    fig.add_trace(go.Scatter(x=buy_call_idx,y=df.loc[buy_call_idx,'Low']*0.9995,mode='markers',
        marker=dict(symbol='triangle-up',size=10),name='BUY CALL'),row=1,col=1)
    fig.add_trace(go.Scatter(x=buy_put_idx,y=df.loc[buy_put_idx,'High']*1.0005,mode='markers',
        marker=dict(symbol='triangle-down',size=10),name='BUY PUT'),row=1,col=1)
    if show_volume:
        vol_colors=['#26a69a' if c>=o else '#ef5350' for o,c in zip(df.Open,df.Close)]
        fig.add_trace(go.Bar(x=df.index,y=df.Volume,name='Volume',opacity=0.6,marker_color=vol_colors),row=2,col=1)
    fig.update_layout(height=720,template='plotly_dark',xaxis_rangeslider_visible=False,hovermode='x unified',margin=dict(l=20,r=20,t=20,b=20),legend=dict(orientation='h',y=1.02))
    fig.update_yaxes(title_text='Price',row=1,col=1)
    if show_volume: fig.update_yaxes(title_text='Volume',row=2,col=1)
    st.plotly_chart(fig,use_container_width=True)
st.subheader('🎯 Signal Statistics')
ss1,ss2,ss3,ss4=st.columns(4)
ss1.metric('BUY CALL signals',signal_counts.get('BUY CALL',0))
ss2.metric('BUY PUT signals',signal_counts.get('BUY PUT',0))
ss3.metric('HOLD bars',signal_counts.get('HOLD',0))
ss4.metric('Signal transitions',len(signal_transitions))
if signal_transitions:
    last=signal_transitions[-1]
    st.caption(f"Last signal: **{last[1]}** | {last[0]} | score {last[2]:+.0f}")

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
    piv = get_pivots(symbol)
    if piv.get('available'):
        st.markdown('**Classic Pivots**')
        st.write(f"P {piv['classic']['pivot']:,.2f} | R1 {piv['classic']['r1']:,.2f} | S1 {piv['classic']['s1']:,.2f}")
        st.write(f"R2 {piv['classic']['r2']:,.2f} | R3 {piv['classic']['r3']:,.2f} | S2 {piv['classic']['s2']:,.2f} | S3 {piv['classic']['s3']:,.2f}")
        st.markdown('**Camarilla**')
        st.write(f"R3 {piv['camarilla']['r3']:,.2f} | R4 {piv['camarilla']['r4']:,.2f} | S3 {piv['camarilla']['s3']:,.2f} | S4 {piv['camarilla']['s4']:,.2f}")
        st.caption(f"Prev day H {piv['prev_high']:,.2f} / L {piv['prev_low']:,.2f} / C {piv['prev_close']:,.2f}")
    else:
        st.caption(piv.get('message',''))
    if mtf.get('available'):
        st.markdown('**Multi-timeframe confirmation**')
        st.write(f"{interval} trend: **{mtf['base_trend']}** | {mtf['higher_interval']} trend: **{mtf['higher_trend']}**")
        st.write('✅ Aligned' if mtf['aligned'] else '⚠️ Not aligned -- lower confidence')
    else:
        st.caption(mtf.get('message',''))
with ctx:
    st.subheader('📰 Market Context')
    news=load_news(news_query)
    if news and not news[0].get('error'):
        for item in news[:8]:
            st.markdown(f"• **{item['source']}** — {item['title']}")
            if item.get('link'): st.caption(item['link'])
    elif news: st.warning(news[0]['error'])
    else: st.info('No trusted article matched the query.')
    st.caption('Trusted sources: Reuters, CNBC-TV18, Moneycontrol, Economic Times.')
    gift=load_gift_nifty()
    st.subheader('🌏 GIFT Nifty')
    if gift['available']:
        delta=None if gift.get('change_pct') is None else f"{gift['change_pct']:+.2f}%"
        st.metric('GIFT Nifty',f"{gift['price']:,.2f}",delta)
        st.caption(f"{gift['source']} — {gift['url']}")
    else:
        st.warning(gift['message'])
        st.caption(f"{gift.get('source','NSE IX')} — {gift.get('url','')}")
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

st.subheader('📊 Options Data & Global Cues')
oc1, oc2 = st.columns(2)
with oc1:
    st.markdown('**Options — NIFTY**')
    vix = get_india_vix()
    if vix.get('available'):
        st.metric('India VIX', f"{vix['vix']:.2f}", f"{vix['change_pct']:+.2f}%")
        if vix['vix'] > 20:
            st.caption('High VIX -- widen stops, expect bigger swings.')
    else:
        st.caption(f"India VIX unavailable: {vix.get('message','')}")
    oc = get_option_chain_summary()
    if oc.get('available'):
        pcr_txt = f"{oc['pcr']:.2f}" if oc['pcr'] is not None else 'n/a'
        st.write(f"**PCR (OI):** {pcr_txt}")
        st.write(f"**Total Call OI:** {oc['total_ce_oi']:,} | **Total Put OI:** {oc['total_pe_oi']:,}")
        if oc.get('max_pain'):
            st.write(f"**Max Pain:** {oc['max_pain']:,.0f}")
        if oc.get('underlying'):
            st.caption(f"NSE underlying: {oc['underlying']:,.2f}")
    else:
        st.warning(f"Option chain unavailable: {oc.get('message','')}")
        st.caption('NSE frequently blocks server-side/cloud IPs for this endpoint. Runs more reliably from a residential IP or with a proper browser session/proxy.')
with oc2:
    st.markdown('**Global cues**')
    cues = get_global_cues()
    for label, v in cues.items():
        if v.get('available'):
            st.metric(label, f"{v['price']:,.2f}", f"{v['change_pct']:+.2f}%")
        else:
            st.caption(f"{label}: unavailable")


if symbol in ('^NSEI', 'NIFTY', 'NIFTY50', 'NIFTY 50'):
    st.subheader('🕉️ Medini Jyotish — 10 Chakra Analysis (NIFTY 50, Experimental)')
    ch = run_all_chakras()
    if ch['available']:
        st.warning('Experimental research layer only — NOT a validated predictor. No price targets are generated by this section; use your own risk management.')
        st.write(f"**Overall lean:** {ch['summary']}")
        for r in ch['chakras']:
            with st.expander(f"{r['chakra']} — {r['verdict']}"):
                st.write(r['detail'])
        st.caption(f"Computed from Swiss Ephemeris (Lahiri sidereal) at {ch['as_of']}")
    else:
        st.error(ch['message'])
st.subheader('🎯 Master Decision')
m1,m2,m3,m4=st.columns(4)
m1.metric('Technical',f"{decision['technical_score']:+.0f}"); m2.metric('Context',f"{decision['context_score']:+.0f}"); m3.metric('Celestial',f"{decision['celestial_score']:+.0f}"); m4.metric('Confidence',f"{decision['confidence']:.0f}")
st.info(f"Decision: **{decision['signal']}** | Entry {decision['entry']:,.2f} | SL {decision['stop']:,.2f} | T1 {decision['target1']:,.2f} | T2 {decision['target2']:,.2f}")

st.subheader('💰 Position Sizing')
if decision['signal'] != 'HOLD':
    ps = position_size(capital, risk_pct, decision['entry'], decision['stop'], lot_size)
    if ps.get('available'):
        p1,p2,p3 = st.columns(3)
        p1.metric('Max lots', ps['max_lots'])
        p2.metric('Quantity', ps['actual_qty'])
        p3.metric('Actual risk (INR)', f"{ps['actual_risk']:,.0f}")
        if ps.get('warning'):
            st.warning(ps['warning'])
    else:
        st.caption(ps.get('message',''))
else:
    st.caption('No active signal -- nothing to size.')

st.subheader('📉 Backtest — Signal Engine (this loaded window)')
bt = backtest(df)
if bt.get('available'):
    b1,b2,b3 = st.columns(3)
    b1.metric('Trades', bt['trade_count'])
    b2.metric('Win rate', f"{bt['win_rate']:.1f}%")
    b3.metric('Avg R-multiple', f"{bt['avg_r_multiple']:+.2f}R")
    st.caption('Bar-close simulation on the currently loaded period/interval only -- no slippage/costs modeled. Not a guarantee of future performance.')
    with st.expander('Trade log'):
        st.dataframe(pd.DataFrame(bt['trades']), hide_index=True, use_container_width=True)
else:
    st.caption(bt.get('message',''))

st.caption('Astrology is an experimental research layer and is not a scientifically validated predictor. Paper mode only.')
