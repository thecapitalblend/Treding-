import yfinance as yf
def load_news(query):
    try:
        s=yf.Search(query,news_count=10); out=[]
        for item in getattr(s,'news',[])[:10]:
            title=item.get('title') or item.get('content',{}).get('title')
            if title: out.append(title)
        return out
    except Exception:return []
