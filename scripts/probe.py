import json, urllib.request, urllib.parse, time, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, h=None):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*", **(h or {})})
    with urllib.request.urlopen(req, timeout=40) as r: return r.read()
out = {}
for k, u in {
 "bis_cbpol": "https://stats.bis.org/api/v1/data/WS_CBPOL/D.CL/all?startPeriod=2026-06-01&format=csv",
 "bis_xru": "https://stats.bis.org/api/v1/data/WS_XRU/D.CL.CLP.A/all?startPeriod=2026-09-20&format=csv",
 "bis_cpi": "https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.CL.771/all?startPeriod=2026-01&format=csv",
 "oecd_une": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/CHL..._Z.Y._T.Y_GE15..M?startPeriod=2026-01&format=csvfile",
 "oecd_gdp": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..CHL.S1..B1GQ......G1.?startPeriod=2025-Q1&format=csvfile",
}.items():
    try:
        t = get(u).decode(); rows = [l.split(",") for l in t.strip().split("\n")]
        hdr = rows[0]; i, j = hdr.index("TIME_PERIOD"), hdr.index("OBS_VALUE")
        out[k] = sorted((r[i], r[j]) for r in rows[1:] if len(r) > j)[-4:]
    except Exception as e: out[k] = repr(e)[:200]
syms = [".SPIPSA", ".IPSA", "SPIPSA", ".SPCLXIPSA", "SQM", "LTM", "BCH", "BSAC", "ENIC", "CCU", "AKO.B", "AKO/B", "CL10Y-CL", "CLP="]
try:
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=" + urllib.parse.quote("|".join(syms), safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1", {"Referer": "https://www.cnbc.com/"}))
    out["cnbc"] = [(r.get("symbol"), r.get("name"), r.get("last"), r.get("code")) for r in j["FormattedQuoteResult"]["FormattedQuote"]]
except Exception as e: out["cnbc"] = repr(e)
for s in [".SPIPSA", ".IPSA", "SPIPSA"]:
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
 "latercera": "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml",
 "latercera_pulso": "https://www.latercera.com/arc/outboundfeeds/rss/category/pulso/?outputType=xml",
 "df": "https://www.df.cl/noticias/site/list/port/rss.xml",
 "df2": "https://www.df.cl/rss",
 "biobio_eco": "https://www.biobiochile.cl/static/rss/economia.xml",
 "biobio": "https://www.biobiochile.cl/static/rss/portada.xml",
 "emol_eco": "https://www.emol.com/rss/economia.xml",
 "elmostrador": "https://www.elmostrador.cl/feed/",
 "elmostrador_mercados": "https://www.elmostrador.cl/mercados/feed/",
 "cooperativa_eco": "https://www.cooperativa.cl/noticias/site/tax/port/all/rss_6___1.xml",
 "t13": "https://www.t13.cl/rss",
 "cnnchile": "https://www.cnnchile.com/feed/",
 "ex_ante": "https://www.ex-ante.cl/feed/",
 "eldinamo": "https://www.eldinamo.cl/feed/",
}.items():
    try:
        root = ET.fromstring(get(u)); tit = []; tot = 0
        for it in root.iter():
            if it.tag.split("}")[-1] not in ("item", "entry"): continue
            h = {c.tag.split("}")[-1]: c for c in it}; tot += 1
            d = fecha(next((h[x].text for x in ("pubDate", "published", "updated", "date") if x in h), ""))
            if d and d >= corte: tit.append((h["title"].text or "").strip() if "title" in h else "")
        out["rss_" + k] = {"total": tot, "48h": len(tit), "ej": tit[:12]}
    except Exception as e: out["rss_" + k] = repr(e)[:150]
    time.sleep(0.4)
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
