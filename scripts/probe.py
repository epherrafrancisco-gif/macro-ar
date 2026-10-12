import json, urllib.request, time
UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
U = {
 "banxico_sin_token": "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF61745/datos/oportuno",
 "bis_cbpol_mx": "https://stats.bis.org/api/v1/data/WS_CBPOL/D.MX/all?startPeriod=2026-01-01&format=csv",
 "bis_xru_mx": "https://stats.bis.org/api/v1/data/WS_XRU/D.MX.MXN.A/all?startPeriod=2026-08-01&format=csv",
 "bis_cpi_mx": "https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.MX.771/all?startPeriod=2025-06&format=csv",
 "oecd_cpi_mx": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/MEX.M.N.CPI.PA._T.N.GY?startPeriod=2025-06&format=csvfile",
 "oecd_core_mx": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/MEX.M.N.CPI.PA._TXCP01_NRG.N.GY?startPeriod=2025-06&format=csvfile",
 "oecd_une_mx": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/MEX..._Z.Y._T.Y_GE15..M?startPeriod=2025-06&format=csvfile",
 "oecd_gdp_mx": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/Q..MEX.S1..B1GQ......G1.?startPeriod=2024-Q1&format=csvfile",
 "dbn_providers": "https://api.db.nomics.world/v22/providers?limit=500",
 "dbn_banxico": "https://api.db.nomics.world/v22/datasets/BANXICO?limit=50",
 "dbn_inegi": "https://api.db.nomics.world/v22/datasets/INEGI?limit=50",
 "fred_mx": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXMXUS",
 "inegi_bie_pub": "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/444612/es/0700/false/BIE/2.0/?type=json",
 "banxico_cal": "https://www.banxico.org.mx/publicaciones-y-prensa/anuncios-de-las-decisiones-de-politica-monetaria/anuncios-politica-monetaria-t.html",
}
out = {}
for k, u in U.items():
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=40) as r:
            t = r.read().decode("utf-8", "replace")
        if k == "dbn_providers":
            j = json.loads(t); t = json.dumps([p["code"] for p in j["providers"]["docs"]])
        elif k.startswith("dbn_"):
            j = json.loads(t); t = json.dumps([(d["code"], d.get("name")) for d in j["datasets"]["docs"]], ensure_ascii=False)
        elif k == "banxico_cal":
            import re; t = " | ".join(sorted(set(re.findall(r"20(?:26|27)[^<]{0,80}", t)))[:60])
        out[k] = {"ok": True, "len": len(t), "head": t[:1500], "tail": t[-800:]}
    except Exception as e:
        out[k] = {"ok": False, "err": repr(e)[:300]}
    time.sleep(1)
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
