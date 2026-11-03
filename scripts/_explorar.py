import urllib.request, urllib.parse, json
UA={"User-Agent":"Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar)","Accept":"application/json"}
def get(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=120).read())
B="https://comexbe.indec.gob.ar/public-api/search/"
for term in ['a','e','i','o','u']:
    try:
        j=get(B+"countries?i18n=es&term="+term); print('C',term,len(j), json.dumps(j[:3],ensure_ascii=False)[:500])
    except Exception as e: print('C',term,e)
seen={}
for term in ['a','e','i','o','u','r','n']:
    try:
        for c in get(B+"countries?i18n=es&term="+term): seen[str(c.get('_id'))]=c
    except Exception: pass
print('PAISES', json.dumps({k:(v.get('name') or v.get('description') or v) for k,v in sorted(seen.items())},ensure_ascii=False))
for term in ['28151100','28151200','2828901','34023100','34023990','39011020','39011030','39012019','39012029','39014000','29121100','29163121','28070010','28362010','29181400','29054500','34024200','29341090','29161911','38089419','sodio','polietileno','sulfonico','formaldehido','benzoato','sorbato','isotiazol','hipoclorito']:
    try: j=get(B+"products?"+urllib.parse.urlencode({'i18n':'es','term':term,'year':2026})); print('P',term, json.dumps(j[:6] if isinstance(j,list) else j,ensure_ascii=False)[:900])
    except Exception as e: print('P',term,e)
