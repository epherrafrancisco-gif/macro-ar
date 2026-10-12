import json, urllib.request, urllib.parse, time, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, h=None):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*", **(h or {})})
    with urllib.request.urlopen(req, timeout=40) as r: return r.read()
out = {}
for k, u in {
 "bis_cbpol": "https://stats.bis.org/api/v1/data/WS_CBPOL/D.GB/all?startPeriod=2024-01-01&format=csv",
 "bis_xru": "https://stats.bis.org/api/v1/data/WS_XRU/D.GB.GBP.A/all?startPeriod=2026-09-20&format=csv",
 "bis_cpi": "https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.GB.771/all?startPeriod=2026-01&format=csv",
 "oecd_une": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/GBR..._Z.Y._T.Y_GE15..M?startPeriod=2026-01&format=csvfile",
 "oecd_gdp": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..GBR.S1..B1GQ......G1.?startPeriod=2025-Q1&format=csvfile",
}.items():
    try:
        t = get(u).decode(); rows = [l.split(",") for l in t.strip().split("\n")]
        hdr = rows[0]; i, j = hdr.index("TIME_PERIOD"), hdr.index("OBS_VALUE")
        out[k] = sorted((r[i], r[j]) for r in rows[1:] if len(r) > j)[-4:]
    except Exception as e: out[k] = repr(e)[:200]
syms = [".FTSE", ".FTMC", ".FTLC", "GBP=", "GB2Y-GB", "GB10Y-GB", "GB30Y-GB", "SHEL", "AZN", "HSBC", "UL", "BP", "DEO", "GSK", "BTI", "RIO", "BCS", "LYG", "NWG", "VOD", "RELX", "ARM", "EWU"]
try:
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=" + urllib.parse.quote("|".join(syms), safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1", {"Referer": "https://www.cnbc.com/"}))
    out["cnbc"] = [(r.get("symbol"), r.get("name"), r.get("last"), r.get("code")) for r in j["FormattedQuoteResult"]["FormattedQuote"]]
except Exception as e: out["cnbc"] = repr(e)
for s in [".FTMC", "GBP=", "GB10Y-GB", "GB2Y-GB"]:
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
 "elpais_eco": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada",
 "expansion_eco": "https://e00-expansion.uecdn.es/rss/economia.xml",
 "cincodias": "https://feeds.elpais.com/mrss-s/pages/ep/site/cincodias.elpais.com/portada",
 "europapress_int": "https://www.europapress.es/rss/rss.aspx?ch=00069",
 "elmundo_int": "https://e00-elmundo.uecdn.es/elmundo/rss/internacional.xml",
 "abc_eco": "https://www.abc.es/rss/2.0/economia/",
 "20min_eco": "https://www.20minutos.es/rss/economia/",
}.items():
    try:
        root = ET.fromstring(get(u)); tit = []; tot = 0
        for it in root.iter():
            if it.tag.split("}")[-1] not in ("item", "entry"): continue
            h = {c.tag.split("}")[-1]: c for c in it}; tot += 1
            d = fecha(next((h[x].text for x in ("pubDate", "published", "updated", "date") if x in h), ""))
            if d and d >= corte and __import__("re").search(r"reino unido|brit|londres|inglaterra|libra|starmer|reeves|ftse|escocia|brexit", (h["title"].text or "") if "title" in h else "", __import__("re").I): tit.append((h["title"].text or "").strip() if "title" in h else "")
        out["rss_" + k] = {"total": tot, "48h": len(tit), "ej": tit[:12]}
    except Exception as e: out["rss_" + k] = repr(e)[:150]
    time.sleep(0.4)
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
