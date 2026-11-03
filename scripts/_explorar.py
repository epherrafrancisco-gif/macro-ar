import urllib.request, json
UA={"User-Agent":"Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar)","Accept":"application/json"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=180).read()
b=get("https://comexbe.indec.gob.ar/public-api/staticData"); print('SIZE',len(b))
j=json.loads(b); print('KEYS', list(j) if isinstance(j,dict) else type(j))
def walk(o,p='',d=0):
    if d>3: return
    if isinstance(o,dict):
        for k,v in list(o.items())[:12]: print('K',p+'/'+k, type(v).__name__, (len(v) if hasattr(v,'__len__') else v) if not isinstance(v,str) else v[:80]); walk(v,p+'/'+k,d+1)
    elif isinstance(o,list) and o: print('L0',p, json.dumps(o[0],ensure_ascii=False)[:400]); walk(o[0],p+'[0]',d+1)
walk(j)
s=json.dumps(j,ensure_ascii=False)
for code in ['28151100','28151200','28289011','34023100','34023990','39011030','39011020','39012029','39012019','39014000','29121100','29163121','29161911','34024200','28070010','28362010','29181400','29054500','29341090','38089419']:
    i=s.find(code); print('NCM',code, s[max(0,i-20):i+260] if i>=0 else None)
for c in ['"203"','"212"','"310"','"438"','"222"','"315"','"406"','"225"','"204"','"113"','"320"']:
    i=s.find(c); print('PAIS',c, s[max(0,i-150):i+150] if i>=0 else None)
