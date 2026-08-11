
import urllib.parse, requests, feedparser

TRUSTED={"Reuters","CNBC-TV18","Moneycontrol","Economic Times"}

def load_news(query="Nifty 50 India markets",limit=8):
    try:
        q=f'({query}) (site:reuters.com OR site:cnbctv18.com OR site:moneycontrol.com OR site:economictimes.indiatimes.com)'
        url="https://news.google.com/rss/search?q="+urllib.parse.quote(q)+"&hl=en-IN&gl=IN&ceid=IN:en"
        r=requests.get(url,timeout=10,headers={"User-Agent":"JarvisTradingAssistant/3.0"})
        r.raise_for_status()
        feed=feedparser.parse(r.content)
        out=[]; seen=set()
        for e in feed.entries:
            title=(getattr(e,"title","") or "").strip()
            link=(getattr(e,"link","") or "").strip()
            source=""
            if hasattr(e,"source") and e.source:
                source=(getattr(e.source,"title","") or "").strip()
            if " - " in title:
                t,s=title.rsplit(" - ",1)
                if s in TRUSTED: title,source=t.strip(),s
            if source not in TRUSTED or not title or title.lower() in seen: continue
            seen.add(title.lower())
            out.append({"title":title,"source":source,"link":link})
            if len(out)>=limit: break
        return out
    except Exception as e:
        return [{"error":f"Trusted news feed unavailable: {e}"}]
