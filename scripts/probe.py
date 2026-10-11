"""Prueba temporal de fuentes nuevas desde GitHub Actions (se borra después)."""
import json, re, urllib.request, importlib.util
spec = importlib.util.spec_from_file_location("g", "scripts/global.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
out = {}
def tryget(k, url, n=600, **kw):
    try:
        t = g.get(url, tries=1, timeout=30, **kw); out[k] = {"ok": True, "len": len(t), "muestra": t[:n]}
    except Exception as e:
        out[k] = {"ok": False, "err": str(e)[:200]}
bonos = ["US10Y", "DE10Y-DE", "GB10Y-GB", "JP10Y-JP", "FR10Y-FR", "IT10Y-IT", "ES10Y-ES", "BR10Y-BR", "BR10Y", "MX10Y-MX", "MX10Y",
         "CA10Y", "CA10Y-CA", "AU10Y-AU", "AU10Y", "CN10Y-CN", "CN10Y", "IN10Y-IN", "IN10Y", "CL10Y-CL", "CO10Y-CO", "ZA10Y-ZA", "TR10Y-TR", "CH10Y-CH", "KR10Y-KR"]
com = ["@S.1", "@C.1", "@W.1", "@CL.1", "@LCO.1", "@NG.1", "@GC.1", "@SI.1", "@HG.1", "@PL.1", "@KC.1", "@SB.1"]
heat = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","AVGO","TSLA","BRK.B","LLY","JPM","V","UNH","XOM","MA","COST","HD","PG","JNJ","WMT","NFLX","ABBV","BAC","CRM","KO","ORCL","CVX","MRK","AMD","PEP","ADBE","TMO","LIN","ACN","MCD","CSCO","WFC","ABT","IBM","GE","QCOM","DIS","CAT","INTU","VZ","TXN","AMGN","PM","NOW","GS"]
q = g.cnbc_raw(bonos + com + heat)
out["cnbc"] = {s: q.get(s) for s in bonos + com}
out["cnbc_heat_ok"] = [s for s in heat if s in q]
try:
    t = g.get("https://ts-api.cnbc.com/harmony/app/charts/1Y.json?symbol=" + urllib.request.quote("DE10Y-DE", safe=""), tries=1)
    out["hist_de10"] = t[:300]
except Exception as e: out["hist_de10"] = str(e)
try:
    t = g.get("https://ts-api.cnbc.com/harmony/app/charts/1Y.json?symbol=" + urllib.request.quote("@NG.1", safe=""), tries=1)
    out["hist_ng"] = t[:300]
except Exception as e: out["hist_ng"] = str(e)
tryget("coingecko", "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=12&page=1&price_change_percentage=24h,7d,1y", 900)
for k, u in {"rss_elpais": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada",
             "rss_bbc": "https://feeds.bbci.co.uk/mundo/rss.xml",
             "rss_dw": "https://rss.dw.com/xml/rss-sp-eco",
             "rss_expansion": "https://e00-expansion.uecdn.es/rss/mercados.xml",
             "rss_eleconomista": "https://www.eleconomista.es/rss/rss-mercados.php",
             "rss_france24": "https://www.france24.com/es/econom%C3%ADa/rss",
             "rss_cnnes": "https://cnnespanol.cnn.com/category/economia/feed/",
             "rss_euronews": "https://es.euronews.com/rss?level=vertical&name=business",
             "rss_infobae_eco": "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/",
             "rss_elfinanciero": "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml",
             "dol_claims": "https://oui.doleta.gov/unemploy/csv/ar539.csv",
             "freddie": "https://www.freddiemac.com/pmms/docs/PMMS_history.csv",
             "nasdaq_earn": "https://api.nasdaq.com/api/calendar/earnings?date=2026-10-14",
             "fred_icsa": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ICSA",
             "fred_mort": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US",
             "bea": "https://apps.bea.gov/api/data?&UserID=x&method=GETDATASETLIST&ResultFormat=JSON"}.items():
    tryget(k, u, 400)
# BLS: rubros del IPC y JOLTS (una sola consulta)
try:
    body = json.dumps({"seriesid": ["CUUR0000SAH1", "CUUR0000SA0E", "CUUR0000SAF1", "CUUR0000SETA02", "CUUR0000SETA01", "CUUR0000SAM",
                                    "CUUR0000SAS", "CUUR0000SAA", "CUUR0000SAT", "JTS000000000000000JOL", "LNS14000000"], "startyear": "2025", "endyear": "2026"}).encode()
    req = urllib.request.Request("https://api.bls.gov/publicAPI/v1/timeseries/data/", data=body, headers={"Content-type": "application/json", "User-Agent": g.UA})
    j = json.loads(urllib.request.urlopen(req, timeout=60).read())
    out["bls"] = {"status": j.get("status"), "msg": j.get("message"), "series": {s["seriesID"]: (s["data"][:2] if s.get("data") else None) for s in j.get("Results", {}).get("series", [])}}
except Exception as e: out["bls"] = str(e)
json.dump(out, open("probe.json", "w"), ensure_ascii=False, indent=1)
