import urllib.request, io, zipfile, re, json
UA={"User-Agent":"Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar)"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=180).read()
pag=get("https://comex.indec.gob.ar/").decode('utf-8','replace')
for s in re.findall(r'src="([^"]+)"',pag):
    t=get("https://comex.indec.gob.ar"+s).decode('utf-8','replace')
    for m in re.finditer(r'api/|files/|\.json',t):
        c=t[max(0,m.start()-120):m.start()+160].replace('\n',' ')
        if 'http' in c or 'get(' in c or 'fetch' in c or 'url' in c.lower(): print('CTX',s[12:22],c)
for u in ["https://comex.indec.gob.ar/api/internal/countries","https://comex.indec.gob.ar/api/internal/paises","https://comex.indec.gob.ar/api/internal/ncm","https://comex.indec.gob.ar/files/amendments/"]:
    try: print('GET',u,get(u)[:800])
    except Exception as e: print('GET',u,e)
z=zipfile.ZipFile(io.BytesIO(get("https://comex.indec.gob.ar/files/zips/imports_2026_M.zip")))
d=z.read('Leame importaciones.docx'); x=zipfile.ZipFile(io.BytesIO(d)).read('word/document.xml').decode('utf-8','replace')
print('LEAME', re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',x))[:5000])
