import json, urllib.request, re
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30); return r.status, r.read().decode("utf-8","replace")
    except Exception as e: return "ERR", str(e)
for ruta in ["indice/.merv","indice/merval","indice/.mervm","indice/msci-merval","indice/.msmerv","indice/.mmerv","indice/.merv-msci","indice/.bymagen","indice/.mar"]:
    s, t = get(f"https://mercados.ambito.com//{ruta}/historico-general/2026-10-14/2026-10-27"); print("AMBITO", ruta, s, t[:300].replace("\n"," "))
for sym in [".MERV",".MSCIMERV",".MMERV",".MERVM",".MSMERV","MERVAL",".MERVAL"]:
    s, t = get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols="+urllib.request.quote(sym)+"&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1")
    m = re.findall(r'"(last|last_time|name|code)":"?([^",]*)', t); print("CNBC", sym, s, m[:8])
for d in ["2026/10/23","2026/10/22"]:
    s, t = get(f"https://www.rava.com/cotizaciones/historico/merval/{d}/"); i = t.find("98"); print("RAVA", d, s, len(t), re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",t))[:1]); 
    txt = re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",t)); j = txt.find("Cierre"); print("   ", txt[max(0,j-300):j+500])
for p in ["arg_stocks","arg_indices","arg_index","indices"]:
    s, t = get("https://data912.com/live/"+p)
    try:
        js = json.loads(t); hits = [x for x in js if "MERV" in json.dumps(x).upper()][:3]; print("D912", p, s, len(js), hits)
    except Exception: print("D912", p, s, t[:150])
