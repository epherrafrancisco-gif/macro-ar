import json, urllib.request, time, re, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
U = {
 "mx_economista_eco": "https://www.eleconomista.com.mx/rss/economia",
 "mx_economista_mer": "https://www.eleconomista.com.mx/rss/mercados",
 "mx_economista_all": "https://www.eleconomista.com.mx/rss/ultimas-noticias",
 "mx_financiero": "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml",
 "mx_financiero_eco": "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/category/economia/?outputType=xml",
 "mx_expansion": "https://expansion.mx/rss/economia",
 "mx_expansion2": "https://expansion.mx/rss",
 "mx_jornada": "https://www.jornada.com.mx/rss/economia.xml",
 "mx_universal": "https://www.eluniversal.com.mx/arc/outboundfeeds/rss/category/cartera/?outputType=xml",
 "mx_forbes": "https://www.forbes.com.mx/feed/",
 "eu_expansion_eco": "https://e00-expansion.uecdn.es/rss/economia.xml",
 "eu_cincodias": "https://feeds.elpais.com/mrss-s/pages/ep/site/cincodias.elpais.com/portada",
 "eu_euronews_eco": "https://es.euronews.com/rss?level=theme&name=economy",
 "eu_eleconomista_es": "https://www.eleconomista.es/rss/rss-economia.php",
 "eu_dw": "https://rss.dw.com/xml/rss-sp-eco",
 "br_infobae_am": "https://www.infobae.com/arc/outboundfeeds/rss/category/america/",
 "br_france24_am": "https://www.france24.com/es/am%C3%A9rica-latina/rss",
 "br_elpais_am": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/america/portada",
 "br_bbc": "https://feeds.bbci.co.uk/mundo/rss.xml",
 "br_ambito_mundo": "https://www.ambito.com/rss/pages/mundo.xml",
 "br_infobae_eco": "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/",
 "br_cnn_es": "https://cnnespanol.cnn.com/feed/",
 "br_dw_lat": "https://rss.dw.com/xml/rss-sp-al",
 "us_elpais_us": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/us/portada",
 "us_france24": "https://www.france24.com/es/econom%C3%ADa/rss",
 "us_infobae_eeuu": "https://www.infobae.com/arc/outboundfeeds/rss/category/estados-unidos/",
}
corte = datetime.now(timezone.utc) - timedelta(hours=48)
def fecha(t):
    t=(t or "").strip()
    try: d=parsedate_to_datetime(t)
    except Exception:
        try: d=datetime.fromisoformat(t.replace("Z","+00:00"))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
out={}
for k,u in U.items():
    try:
        req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"*/*"})
        with urllib.request.urlopen(req,timeout=30) as r: raw=r.read()
        root=ET.fromstring(raw); tit=[]; tot=0
        for it in root.iter():
            if it.tag.split("}")[-1] not in ("item","entry"): continue
            h={c.tag.split("}")[-1]:c for c in it}; tot+=1
            d=fecha(next((h[x].text for x in ("pubDate","published","updated","date") if x in h),""))
            t=(h["title"].text or "").strip() if "title" in h else ""
            if d and d>=corte: tit.append(t)
        out[k]={"ok":True,"total":tot,"48h":len(tit),"ej":tit[:25]}
    except Exception as e:
        out[k]={"ok":False,"err":repr(e)[:200]}
    time.sleep(0.5)
open("probe.json","w").write(json.dumps(out,ensure_ascii=False,indent=1))
