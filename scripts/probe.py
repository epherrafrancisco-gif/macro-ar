import json, urllib.request, urllib.parse, time, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, h=None):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*", **(h or {})})
    with urllib.request.urlopen(req, timeout=40) as r: return r.read()
out = {}
for k, u in {
 "bis_cbpol": "https://stats.bis.org/api/v1/data/WS_CBPOL/D.CA/all?startPeriod=2024-01-01&format=csv",
 "bis_xru": "https://stats.bis.org/api/v1/data/WS_XRU/D.CA.CAD.A/all?startPeriod=2026-09-20&format=csv",
 "bis_cpi": "https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.CA.771/all?startPeriod=2026-01&format=csv",
 "oecd_une": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/CAN..._Z.Y._T.Y_GE15..M?startPeriod=2026-01&format=csvfile",
 "oecd_gdp": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..CAN.S1..B1GQ......G1.?startPeriod=2025-Q1&format=csvfile",
}.items():
    try:
        t = get(u).decode(); rows = [l.split(",") for l in t.strip().split("\n")]
        hdr = rows[0]; i, j = hdr.index("TIME_PERIOD"), hdr.index("OBS_VALUE")
        out[k] = sorted((r[i], r[j]) for r in rows[1:] if len(r) > j)[-4:]
    except Exception as e: out[k] = repr(e)[:200]
syms = [".GSPTSE", "CAD=", "CA10Y", "CA2Y", "CA30Y", "CA5Y", "SHOP", "RY", "TD", "ENB", "CNQ", "CP", "CNI", "BMO", "BNS", "SU", "BAM", "TRI", "CM", "NTR", "B", "GOLD", "EWC", "CVE", "MFC"]
try:
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=" + urllib.parse.quote("|".join(syms), safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1", {"Referer": "https://www.cnbc.com/"}))
    out["cnbc"] = [(r.get("symbol"), r.get("name"), r.get("last"), r.get("code")) for r in j["FormattedQuoteResult"]["FormattedQuote"]]
except Exception as e: out["cnbc"] = repr(e)
for s in [".GSPTSE", "CAD=", "CA10Y", "CA2Y"]:
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
 "bbc": "https://feeds.bbci.co.uk/mundo/rss.xml",
 "elpais_us": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/us/portada",
 "infobae_eeuu": "https://www.infobae.com/arc/outboundfeeds/rss/category/estados-unidos/",
 "europapress_int": "https://www.europapress.es/rss/rss.aspx?ch=00069",
 "france24": "https://www.france24.com/es/econom%C3%ADa/rss",
 "rcinet_es": "https://ici.radio-canada.ca/rci/es/rss",
 "rci2": "https://www.rcinet.ca/es/feed/",
 "laprensa_ca": "https://www.lapresse.ca/actualites/rss",
}.items():
    try:
        root = ET.fromstring(get(u)); tit = []; tot = 0
        for it in root.iter():
            if it.tag.split("}")[-1] not in ("item", "entry"): continue
            h = {c.tag.split("}")[-1]: c for c in it}; tot += 1
            d = fecha(next((h[x].text for x in ("pubDate", "published", "updated", "date") if x in h), ""))
            if d and d >= corte and (k.startswith("rc") or __import__("re").search(r"canad|ottawa|toronto|carney|quebec|montreal|vancouver", (h["title"].text or "") if "title" in h else "", __import__("re").I)): tit.append((h["title"].text or "").strip() if "title" in h else "")
        out["rss_" + k] = {"total": tot, "48h": len(tit), "ej": tit[:12]}
    except Exception as e: out["rss_" + k] = repr(e)[:150]
    time.sleep(0.4)
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
