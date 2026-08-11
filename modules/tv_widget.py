"""Renders TradingView's official free 'Advanced Real-Time Chart' widget.

This is TradingView's own embeddable widget (client-side JS, loaded from
tradingview.com), so the chart is genuinely TradingView's live chart, not a
recreation. No API key or account is required for the public widget.
"""

import streamlit.components.v1 as components

TV_SYMBOL_MAP = {
    "^NSEI": "NSE:NIFTY",
    "^NSEBANK": "NSE:BANKNIFTY",
}


def _tv_symbol(symbol: str) -> str:
    return TV_SYMBOL_MAP.get(symbol, symbol)


def render_tradingview_chart(symbol="^NSEI", interval="15", theme="dark", height=720):
    """Embed the TradingView Advanced Real-Time Chart widget.

    interval: TradingView's own codes, e.g. '1','5','15','30','60','D'.
    """
    tv_symbol = _tv_symbol(symbol)
    html = f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%;">
      <div id="tv_chart" style="height:100%;width:100%;"></div>
      <script src="https://s3.tradingview.com/tv.js"></script>
      <script>
        new TradingView.widget({{
          "autosize": true,
          "symbol": "{tv_symbol}",
          "interval": "{interval}",
          "timezone": "Asia/Kolkata",
          "theme": "{theme}",
          "style": "1",
          "locale": "in",
          "toolbar_bg": "#131722",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "studies": ["MASimple@tv-basicstudies", "RSI@tv-basicstudies"],
          "container_id": "tv_chart"
        }});
      </script>
    </div>
    """
    components.html(html, height=height + 10)


# Map our sidebar interval strings ('1m','5m','15m','30m','1h','1d') to
# TradingView's interval codes.
INTERVAL_MAP = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "1h": "60", "1d": "D"}
