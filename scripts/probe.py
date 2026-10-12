import json, urllib.request, urllib.parse, time, csv, io, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, h=None):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*", **(h or {})})
    with urllib.request.urlopen(req, timeout=40) as r: return r.read()
out = {}
def sd(k, u):
    try:
        rr = list(csv.DictReader(io.StringIO(get(u).decode())))
        out[k] = sorted((r["TIME_PERIOD"], r["OBS_VALUE"]) for r in rr)[-3:]
    except Exception as e: out[k] = repr(e)[:150]
for c, o in [("PE","PER"),("IN","IND"),("UY","URY")]:
    sd("bis_cbpol_"+c, f"https://stats.bis.org/api/v1/data/WS_CBPOL/D.{c}/all?startPeriod=2026-09-01&format=csv")
    sd("bis_cpi_"+c, f"https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.{c}.771/all?startPeriod=2026-01&format=csv")
    sd("oecd_une_"+o, f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/{o}..._Z.Y._T.Y_GE15..M?startPeriod=2025-06&format=csvfile")
    sd("oecd_gdp_"+o, f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..{o}.S1..B1GQ......G1.?startPeriod=2025-Q1&format=csvfile")
sd("bis_xru_PE", "https://stats.bis.org/api/v1/data/WS_XRU/D.PE.PEN.A/all?startPeriod=2026-09-25&format=csv")
sd("bis_xru_IN", "https://stats.bis.org/api/v1/data/WS_XRU/D.IN.INR.A/all?startPeriod=2026-09-25&format=csv")
sd("bis_xru_UY", "https://stats.bis.org/api/v1/data/WS_XRU/D.UY.UYU.A/all?startPeriod=2026-09-25&format=csv")
# BCRP (Perú), sin clave
for k, s in {"pe_tasa":"PD04722MM","pe_infl12":"PN01273PM","pe_tc":"PD04640PD","pe_pbi":"PN01728AM","pe_desemp":"PN38063GM","pe_reservas":"PN00026MM"}.items():
    try:
        j = json.loads(get(f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{s}/json/2025-1/2026-12").decode("utf-8","replace"))
        out[k] = [j.get("config",{}).get("series",[{}])[0].get("name"), j.get("periods",[])[-2:]]
    except Exception as e: out[k] = repr(e)[:150]
# Uruguay: INE y BCU
for k, u in {"uy_bcu_tpm": "https://www.bcu.gub.uy/Politica-Economica-y-Mercados/Paginas/Tasa-de-Politica-Monetaria.aspx",
             "uy_ine_ipc": "https://www.gub.uy/instituto-nacional-estadistica/datos-y-estadisticas/estadisticas/ipc"}.items():
    try: t = get(u).decode("utf-8","replace"); out[k] = f"ok {len(t)}"
    except Exception as e: out[k] = repr(e)[:150]
syms = [".NSEI", ".BSESN", "INR=", "IN10Y", "IN2Y", "INFY", "HDB", "IBN", "WIT", "RDY", "MMYT", "INDA", "PEN=", ".SPBLPGPT", "EPU", "BAP", "SCCO", "BVN", "IFS", "UYU=", "PE10Y", "PE10Y-PE", "UY10Y"]
try:
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=" + urllib.parse.quote("|".join(syms), safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1", {"Referer": "https://www.cnbc.com/"}))
    out["cnbc"] = [(r.get("symbol"), r.get("name"), r.get("last")) for r in j["FormattedQuoteResult"]["FormattedQuote"]]
except Exception as e: out["cnbc"] = repr(e)
for s in [".NSEI", "INR=", "IN10Y", ".SPBLPGPT", "EPU", "PEN="]:
    try:
        j = json.loads(get(f"https://ts-api.cnbc.com/harmony/app/charts/1Y.json?symbol={urllib.parse.quote(s)}"))
        out["hist_" + s] = len(j.get("barData", {}).get("priceBars") or [])
    except Exception as e: out["hist_" + s] = repr(e)[:100]
corte = datetime.now(timezone.utc) - timedelta(hours=48)
def fecha(t):
    t=(t or "").strip()
    try: d=parsedate_to_datetime(t)
    except Exception:
        try: d=datetime.fromisoformat(t.replace("Z","+00:00"))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
for k, u in {"gestion": "https://gestion.pe/arcio/rss/category/economia/?outputType=xml", "gestion2": "https://gestion.pe/arc/outboundfeeds/rss/category/economia/?outputType=xml",
             "elcomercio_eco": "https://elcomercio.pe/arc/outboundfeeds/rss/category/economia/?outputType=xml", "larepublica_pe": "https://larepublica.pe/rss/economia.xml",
             "andina": "https://andina.pe/agencia/rss/3.xml", "rpp_eco": "https://rpp.pe/feed/economia",
             "elobservador": "https://www.elobservador.com.uy/rss/elobservador/economia-y-empresas.xml", "elpais_uy": "https://www.elpais.com.uy/rss/negocios/", "elpais_uy2": "https://www.elpais.com.uy/rss",
             "montevideo": "https://www.montevideo.com.uy/anxml.aspx?59", "ladiaria": "https://ladiaria.com.uy/feeds/articulos/"}.items():
    try:
        root = ET.fromstring(get(u)); tit = []; tot = 0
        for it in root.iter():
            if it.tag.split("}")[-1] not in ("item", "entry"): continue
            h = {c.tag.split("}")[-1]: c for c in it}; tot += 1
            d = fecha(next((h[x].text for x in ("pubDate", "published", "updated", "date") if x in h), ""))
            if d and d >= corte: tit.append((h["title"].text or "").strip() if "title" in h else "")
        out["rss_" + k] = {"total": tot, "48h": len(tit), "ej": tit[:5]}
    except Exception as e: out["rss_" + k] = repr(e)[:150]
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
