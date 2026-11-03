import urllib.request, io, zipfile, re
UA={"User-Agent":"Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar)"}
def get(u, n=None):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=120); return r.read() if n is None else r.read(n)
for u in ["https://comex.indec.gob.ar/robots.txt","https://comex.indec.gob.ar/","https://comex.indec.gob.ar/#/database"]:
    try: t=get(u).decode('utf-8','replace'); print("==",u,len(t)); print(t[:1500]); print(sorted(set(re.findall(r'[\w./-]*\.(?:zip|csv|js)\b',t)))[:60])
    except Exception as e: print("ERR",u,e)
for y in [2025,2026]:
  for k in ["imports","exports"]:
    for f in ["M","A"]:
      u=f"https://comex.indec.gob.ar/files/zips/{k}_{y}_{f}.zip"
      try:
        b=get(u); z=zipfile.ZipFile(io.BytesIO(b)); print("OK",u,len(b),z.namelist())
        for n in z.namelist()[:3]:
          lines=z.read(n).decode('latin-1').splitlines(); print(n,len(lines)); print("\n".join(lines[:4])); print(lines[-1])
          import collections
          for codigo in ["28151100","28151200","28289011","28289019","34021190","34021110","29041000","39011000","39012019","39014000"]:
            m=[l for l in lines if codigo in l][:3]; print(codigo, m)
      except Exception as e: print("ERR",u,e)
