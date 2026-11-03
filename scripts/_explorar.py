import urllib.request, io, zipfile, re, collections
UA={"User-Agent":"Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar)"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=180).read()
z=zipfile.ZipFile(io.BytesIO(get("https://comex.indec.gob.ar/files/zips/imports_2026_M.zip")))
L=z.read('impom26.csv').decode('latin-1').splitlines()[1:]
f=lambda s: float(s.replace(',','.'))
agg=collections.defaultdict(lambda:[0,0,0,set()])
for l in L:
    a=l.split(';')
    if a[2][:4] in ('2815','2828','3402','2904','2916','2918','2922','2933','2934','2836','3901','3902','3907','2905','2811','2807','3808'):
        g=agg[a[2]]; g[0]+=f(a[4]); g[1]+=f(a[5]); g[2]+=f(a[8]); g[3].add(a[1])
for k in sorted(agg):
    kg,fob,cif,ms=agg[k]
    if kg>20000: print(k, f"{kg/1000:.0f} t", f"US$ {cif/kg*1000:.0f}/t CIF", len(ms),"meses")
ze=zipfile.ZipFile(io.BytesIO(get("https://comex.indec.gob.ar/files/zips/exports_2026_M.zip")))
for n in ['exponm26.csv','expopm26.csv']:
    E=ze.read(n).decode('latin-1').splitlines(); print(n,E[0],E[1],E[-1])
    for code in ['39011000','39012019','39014000','28151100','28151200','34023110','34023190']:
        print(code,[l for l in E if ';'+code+';' in l][:2])
# países
pag=get("https://comex.indec.gob.ar/").decode('utf-8','replace')
for js in sorted(set(re.findall(r'[\w]+\.bundle\.js',pag))):
    try:
        t=get("https://comex.indec.gob.ar/"+js).decode('utf-8','replace')
        for m in re.finditer(r'Brasil|BRASIL',t):
            print(js, t[max(0,m.start()-300):m.start()+300].replace('\n',' ')); break
        for m in re.finditer(r'files/[\w/.-]+',t): print(js,'FILE',m.group(0))
    except Exception as e: print(js,e)
