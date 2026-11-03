import json, urllib.request, urllib.parse, io, re, sys
def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 PulsoMacro"})
    return urllib.request.urlopen(r, timeout=60).read()
vistos=set()
for q in ["quimicos","sustancias quimicas","quimica","petroquimica","fertilizantes","agroquimicos","farmaceuticos","medicamentos","plasticos","caucho","detergentes","jabones","pinturas","gases industriales","productos quimicos basicos","materias primas plasticas","IPI manufacturero","precios mayoristas quimicos","IPIB quimicos","IPIM sustancias","exportaciones quimica","empleo quimica","utilizacion capacidad instalada quimica","fibras sinteticas","urea","cloro soda"]:
    try:
        j=json.loads(get("https://apis.datos.gob.ar/series/api/search/?"+urllib.parse.urlencode({"q":q,"limit":60})))
    except Exception as e:
        print("ERR",q,e); continue
    for d in j.get("data",[]):
        f=d.get("field",{}); ds=d.get("dataset",{})
        i=f.get("id")
        if i in vistos: continue
        vistos.add(i)
        print(f"{i} | {f.get('title')} | {f.get('description')} | {ds.get('title')} | {f.get('frequency')} | {f.get('time_index_start')}..{f.get('time_index_end')} | {f.get('units')}")
print("=== PINK")
try:
    import openpyxl
    pag=get("https://www.worldbank.org/en/research/commodity-markets").decode("utf-8","replace")
    m=re.search(r"https://thedocs\.worldbank\.org/[^\"'\s]+CMO-Historical-Data-Monthly\.xlsx",pag)
    wb=openpyxl.load_workbook(io.BytesIO(get(m.group(0))),read_only=True,data_only=True)
    print(wb.sheetnames)
    for sh in ["Monthly Prices","Monthly Indices"]:
        rows=list(wb[sh].iter_rows(values_only=True))
        for r in rows[:8]: print(sh, r)
        print(sh,"LAST",rows[-1][:3], rows[-1])
except Exception as e: print("PINK ERR",e)
print("=== FRED")
for s in ["IPG325S","IPG3251S","IPG3253S","IPG3254S","PCU325325"]:
    try: t=get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}&cosd=2025-01-01").decode(); print(s, t.splitlines()[:2], t.splitlines()[-1])
    except Exception as e: print(s,"ERR",e)
print("=== EUROSTAT")
for geo in ["EU27_2020","DE","FR","IT","ES"]:
    try:
        u=f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_inpr_m?geo={geo}&nace_r2=C20&s_adj=SCA&unit=I21&indic_bt=PRD&sinceTimePeriod=2025-01"
        j=json.loads(get(u)); tm=j["dimension"]["time"]["category"]["index"]; print(geo, len(j["value"]), sorted(tm)[-1], list(j["value"].items())[-1])
    except Exception as e: print(geo,"ERR",e)
