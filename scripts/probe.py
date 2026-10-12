import json, urllib.request, urllib.parse, time, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, h=None):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*", **(h or {})})
    with urllib.request.urlopen(req, timeout=40) as r: return r.read()
out = {}
for k, u in {
 "bis_cbpol_co": "https://stats.bis.org/api/v1/data/WS_CBPOL/D.CO/all?startPeriod=2026-09-01&format=csv",
 "bis_cbpol_tr": "https://stats.bis.org/api/v1/data/WS_CBPOL/D.TR/all?startPeriod=2026-09-01&format=csv",
 "bis_xru_co": "https://stats.bis.org/api/v1/data/WS_XRU/D.CO.COP.A/all?startPeriod=2026-09-25&format=csv",
 "bis_xru_tr": "https://stats.bis.org/api/v1/data/WS_XRU/D.TR.TRY.A/all?startPeriod=2026-09-25&format=csv",
 "bis_cpi_co": "https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.CO.771/all?startPeriod=2026-01&format=csv",
 "bis_cpi_tr": "https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.TR.771/all?startPeriod=2026-01&format=csv",
 "oecd_une_co": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/COL..._Z.Y._T.Y_GE15..M?startPeriod=2026-01&format=csvfile",
 "oecd_une_tr": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/TUR..._Z.Y._T.Y_GE15..M?startPeriod=2026-01&format=csvfile",
 "oecd_gdp_co": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..COL.S1..B1GQ......G1.?startPeriod=2025-Q1&format=csvfile",
 "oecd_gdp_tr": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..TUR.S1..B1GQ......G1.?startPeriod=2025-Q1&format=csvfile",
}.items():
    try:
        import csv, io; rr = list(csv.DictReader(io.StringIO(get(u).decode())))
        out[k] = sorted((r["TIME_PERIOD"], r["OBS_VALUE"]) for r in rr)[-3:]
    except Exception as e: out[k] = repr(e)[:200]
syms = [".COLCAP", "COLCAP", ".COLCAP.CO", "GXG", "COLO", "CO10Y-CO", "CO10Y", "COP=", "EC", "CIB", "AVAL", "TGLS", ".XU100", "XU100", "TUR", "TR10Y-TR", "TR2Y-TR", "TRY=", "TKC", "TRYUSD="]
try:
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=" + urllib.parse.quote("|".join(syms), safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1", {"Referer": "https://www.cnbc.com/"}))
    out["cnbc"] = [(r.get("symbol"), r.get("name"), r.get("last"), r.get("code")) for r in j["FormattedQuoteResult"]["FormattedQuote"]]
except Exception as e: out["cnbc"] = repr(e)
for s in [".XU100", "COP=", "TRY=", "TR10Y-TR", ".COLCAP", "GXG", "CO10Y-CO", "TUR"]:
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
 "eltiempo_eco": "https://www.eltiempo.com/rss/economia.xml",
 "portafolio": "https://www.portafolio.co/rss/economia.xml",
 "portafolio2": "https://www.portafolio.co/rss",
 "larepublica": "https://www.larepublica.co/rss/economia",
 "elespectador_eco": "https://www.elespectador.com/arc/outboundfeeds/rss/category/economia/?outputType=xml",
 "semana_eco": "https://www.semana.com/arc/outboundfeeds/rss/category/economia/?outputType=xml",
 "valora": "https://www.valoraanalitik.com/feed/",
 "aa_es": "https://www.aa.com.tr/es/rss/default?cat=economia",
 "aa_es2": "https://www.aa.com.tr/es/rss/default?cat=guncel",
 "trt_es": "https://www.trtespanol.com/rss",
 "trt_es2": "https://www.trtespanol.com/rss/economia",
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
