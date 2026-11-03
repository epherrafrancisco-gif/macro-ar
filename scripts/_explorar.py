import urllib.request, re, json
UA={"User-Agent":"Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar)","Accept":"application/json"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=180).read()
pag=get("https://comex.indec.gob.ar/").decode()
t=get("https://comex.indec.gob.ar"+[s for s in re.findall(r'src="([^"]+)"',pag) if 'c714bc7b' in s][0]).decode('utf-8','replace')
for key in ['public-api/search','public-api/businessPartners/','public-api/rankings/','public-api/report/','countries','Countries']:
    for m in list(re.finditer(re.escape(key),t))[:2]: print('CTX',key, t[m.start():m.start()+700].replace('\n',' '))
