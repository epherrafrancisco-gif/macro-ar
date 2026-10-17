import json,urllib.request
out={}
for sid in ["41.3_FCV_0_A_18","41.2_FCV_0_T_18","453.2_CARNE_VACUUNA_0_0_12_53"]:
    for d in ["2019-01-01","2024-01-01"]:
        u=f"https://apis.datos.gob.ar/series/api/series/?ids={sid}&start_date={d}&limit=1000&format=json"
        try:
            j=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=60))
            out[sid+"_"+d]={"n":len(j.get("data",[])),"head":j.get("data",[])[:3],"tail":j.get("data",[])[-3:],"meta":j.get("meta",[None,None])[1]}
        except Exception as e: out[sid+"_"+d]=str(e)
json.dump(out,open("probe.json","w"),ensure_ascii=False,indent=1)
