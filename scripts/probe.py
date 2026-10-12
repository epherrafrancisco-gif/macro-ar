"""Prueba temporal de fuentes de Europa (se borra después)."""
import json, urllib.request
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
def get(u, t=40, acc="*/*"):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": acc})
    return urllib.request.urlopen(r, timeout=t).read().decode("utf-8", "replace")
out = {}
E = "https://data-api.ecb.europa.eu/service/data/"
keys = {"dfr": "FM/D.U2.EUR.4F.KR.DFR.LEV", "mro": "FM/D.U2.EUR.4F.KR.MRR_FR.LEV", "hicp": "ICP/M.U2.N.000000.4.ANR",
        "hicp_core": "ICP/M.U2.N.XEF000.4.ANR", "hicp_de": "ICP/M.DE.N.000000.4.ANR", "hicp_it": "ICP/M.IT.N.000000.4.ANR",
        "hicp_es": "ICP/M.ES.N.000000.4.ANR", "hicp_fr": "ICP/M.FR.N.000000.4.ANR", "hicp_mom": "ICP/M.U2.N.000000.4.MOR",
        "eurusd": "EXR/D.USD.EUR.SP00.A", "unemp": "LFSI/M.I9.S.UNEHRT.TOTAL0.15_74.T", "unemp_de": "LFSI/M.DE.S.UNEHRT.TOTAL0.15_74.T",
        "unemp_es": "LFSI/M.ES.S.UNEHRT.TOTAL0.15_74.T", "gdp": "MNA/Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.GY",
        "gdp_qoq": "MNA/Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.GQ", "y10_it": "IRS/M.IT.L.L40.CI.0000.EUR.N.Z"}
for k, key in keys.items():
    try:
        t = get(E + key + "?format=csvdata&lastNObservations=3", acc="text/csv")
        lines = t.strip().split("\n")
        hdr = lines[0].split(",")
        i, j = hdr.index("TIME_PERIOD"), hdr.index("OBS_VALUE")
        out[k] = [(l.split(",")[i], l.split(",")[j]) for l in lines[1:]]
    except Exception as e:
        out[k] = str(e)[:150]
for k, u in {"eurostat_gdp": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?geo=EA20&unit=CLV_PCH_PRE&s_adj=SCA&na_item=B1GQ&lastTimePeriod=3",
             "eurostat_unemp": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=EA20&geo=DE&geo=FR&geo=IT&geo=ES&age=TOTAL&sex=T&unit=PC_ACT&s_adj=SA&lastTimePeriod=2"}.items():
    try:
        out[k] = get(u, acc="application/json")[:1500]
    except Exception as e:
        out[k] = str(e)[:150]
try:
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=.STOXX50E%7C.STOXX%7C.IBEX%7C.FTMIB%7CGB10Y-GB&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1"))
    out["cnbc"] = [(r.get("symbol"), r.get("last"), r.get("name")) for r in j["FormattedQuoteResult"]["FormattedQuote"]]
except Exception as e:
    out["cnbc"] = str(e)[:150]
try:
    out["hist_sx5e"] = get("https://ts-api.cnbc.com/harmony/app/charts/1Y.json?symbol=.STOXX50E")[:200]
except Exception as e:
    out["hist_sx5e"] = str(e)[:150]
json.dump(out, open("probe.json", "w"), ensure_ascii=False, indent=1)
