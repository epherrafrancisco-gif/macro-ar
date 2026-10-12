import json, urllib.request, time
UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
U = {
 "oecd_cpi_w": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/MEX.M..CPI.....?startPeriod=2026-05&format=csvfile",
 "oecd_cpi_w2": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,/MEX.M.?startPeriod=2026-06&format=csvfile",
 "oecd_gdp_gy": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..MEX.S1..B1GQ......GY.?startPeriod=2025-Q1&format=csvfile",
 "frank_mxn": "https://api.frankfurter.app/2026-10-01..?from=USD&to=MXN",
 "dbn_inegi_series": "https://api.db.nomics.world/v22/series/INEGI/DF_STEI?limit=40&observations=false",
}
out = {}
for k, u in U.items():
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=40) as r:
            t = r.read().decode("utf-8", "replace")
        if k == "dbn_providers":
            j = json.loads(t); t = json.dumps([p["code"] for p in j["providers"]["docs"]])
        elif k=="dbn_inegi_series":
            j = json.loads(t); t = json.dumps([(d["series_code"], d.get("series_name")) for d in j["series"]["docs"]], ensure_ascii=False)
        elif k.startswith("dbn_"):
            j = json.loads(t); t = json.dumps([(d["code"], d.get("name")) for d in j["datasets"]["docs"]], ensure_ascii=False)
        elif k == "banxico_cal":
            import re; t = " | ".join(sorted(set(re.findall(r"20(?:26|27)[^<]{0,80}", t)))[:60])
        out[k] = {"ok": True, "len": len(t), "head": t[:3000], "tail": t[-1500:]}
    except Exception as e:
        out[k] = {"ok": False, "err": repr(e)[:300]}
    time.sleep(1)
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
