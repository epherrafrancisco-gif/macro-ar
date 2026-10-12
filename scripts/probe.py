import json, urllib.request, urllib.parse, time, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, h=None):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*", **(h or {})})
    with urllib.request.urlopen(req, timeout=40) as r: return r.read()
out = {}
for k, u in {
 "bis_cbpol": "https://stats.bis.org/api/v1/data/WS_CBPOL/D.JP/all?startPeriod=2024-01-01&format=csv",
 "bis_xru": "https://stats.bis.org/api/v1/data/WS_XRU/D.JP.JPY.A/all?startPeriod=2026-09-20&format=csv",
 "bis_cpi": "https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.JP.771/all?startPeriod=2026-01&format=csv",
 "oecd_une": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/JPN..._Z.Y._T.Y_GE15..M?startPeriod=2026-01&format=csvfile",
 "oecd_gdp": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..JPN.S1..B1GQ......G1.?startPeriod=2025-Q1&format=csvfile",
}.items():
    try:
        t = get(u).decode(); rows = [l.split(",") for l in t.strip().split("\n")]
        hdr = rows[0]; i, j = hdr.index("TIME_PERIOD"), hdr.index("OBS_VALUE")
        out[k] = sorted((r[i], r[j]) for r in rows[1:] if len(r) > j)[-4:]
    except Exception as e: out[k] = repr(e)[:200]
syms = [".N225", ".TOPX", ".TOPIX", "TOPIX", "JP10Y-JP", "JP2Y-JP", "JP30Y-JP", "JPY=", "TM", "SONY", "MUFG", "SMFG", "MFG", "HMC", "NMR", "IX", "TAK", "CAJPY", "EWJ", "DXJ"]
try:
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=" + urllib.parse.quote("|".join(syms), safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1", {"Referer": "https://www.cnbc.com/"}))
    out["cnbc"] = [(r.get("symbol"), r.get("name"), r.get("last"), r.get("code")) for r in j["FormattedQuoteResult"]["FormattedQuote"]]
except Exception as e: out["cnbc"] = repr(e)
for s in [".TOPX", "JPY=", "JP10Y-JP", "JP2Y-JP"]:
    try:
        j = json.loads(get(f"https://ts-api.cnbc.com/harmony/app/charts/1Y.json?symbol={urllib.parse.quote(s)}"))
        b = j.get("barData", {}).get("priceBars") or []
        out["hist_" + s] = len(b)
    except Exception as e: out["hist_" + s] = repr(e)[:100]
corte = datetime.now(timezone.utc) - timedelta(hours=48)
def fecha(t):
    t=(t or "").strip()
    try: d=parsedate_to_datetime(t)
    except Exception:
        try: d=datetime.fromisoformat(t.replace("Z","+00:00"))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
for k, u in {
 "nhk_es": "https://www3.nhk.or.jp/nhkworld/es/news/rss/",
 "nhk_es2": "https://www3.nhk.or.jp/rss/news/cat5.xml",
 "nhk_es3": "https://www3.nhk.or.jp/nhkworld/data/es/news/all.json",
 "efe_asia": "https://efe.com/asia/feed/",
 "efe_eco": "https://efe.com/economia/feed/",
 "europapress_asia": "https://www.europapress.es/rss/rss.aspx?ch=00068",
 "europapress_eco": "https://www.europapress.es/rss/rss.aspx?ch=00136",
 "xinhua_es": "https://spanish.news.cn/rss/economia.xml",
 "elpais_asia": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
 "japantimes_biz": "https://www.japantimes.co.jp/news_category/business/feed/",
}.items():
    try:
        root = ET.fromstring(get(u)); tit = []; tot = 0
        for it in root.iter():
            if it.tag.split("}")[-1] not in ("item", "entry"): continue
            h = {c.tag.split("}")[-1]: c for c in it}; tot += 1
            d = fecha(next((h[x].text for x in ("pubDate", "published", "updated", "date") if x in h), ""))
            if d and d >= corte and (k.startswith("japan") or "jap" in ((h["title"].text or "").lower() if "title" in h else "") or k.startswith("nhk")): tit.append((h["title"].text or "").strip() if "title" in h else "")
        out["rss_" + k] = {"total": tot, "48h": len(tit), "ej": tit[:12]}
    except Exception as e: out["rss_" + k] = repr(e)[:150]
    time.sleep(0.4)
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
