import urllib.request, io, zipfile, re
UA={"User-Agent":"Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar)"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=180).read()
pag=get("https://comex.indec.gob.ar/").decode('utf-8','replace')
srcs=re.findall(r'src="([^"]+)"',pag); print(srcs)
for s in srcs:
    u=s if s.startswith('http') else "https://comex.indec.gob.ar/"+s.lstrip('/')
    try: t=get(u).decode('utf-8','replace')
    except Exception as e: print(u,e); continue
    for m in set(re.findall(r'["\'`](/?(?:api|files|data|json|assets)[^"\'`\s]{2,120})["\'`]',t)): print('URL',u[-20:],m)
    for m in re.finditer(r'Alemania',t): print('PAIS',u[-20:],t[max(0,m.start()-400):m.start()+200].replace('\n',' ')); break
z=zipfile.ZipFile(io.BytesIO(get("https://comex.indec.gob.ar/files/zips/imports_2026_M.zip")))
d=z.read('Leame importaciones.docx'); x=zipfile.ZipFile(io.BytesIO(d)).read('word/document.xml').decode('utf-8','replace')
print('LEAME', re.sub(r'<[^>]+>',' ',x)[:4000])
