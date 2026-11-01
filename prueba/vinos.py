import requests, json, csv, io
UA = {'User-Agent': 'Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)'}
out = {}
def j(u):
    try:
        r = requests.get(u, headers=UA, timeout=60); return r.json() if r.status_code == 200 else {'status': r.status_code}
    except Exception as e: return {'err': str(e)}
def muestra(u, n=6):
    try:
        r = requests.get(u, headers=UA, timeout=90)
        if r.status_code != 200: return {'status': r.status_code}
        txt = r.content.decode('utf-8-sig', errors='replace'); lines = txt.splitlines()
        return {'filas': len(lines), 'cab': lines[:n], 'fin': lines[-4:]}
    except Exception as e: return {'err': str(e)}
for q in ['vitivinicultura', 'vino', 'INV']:
    d = j('https://datos.gob.ar/api/3/action/package_search?q=' + q + '&rows=40')
    if d.get('result'):
        for p in d['result']['results']:
            if p['name'] in out: continue
            if not any(w in (p['title'] + p['name']).lower() for w in ['inv', 'vin', 'viti', 'uva', 'sectoriales']): continue
            out[p['name']] = {'title': p['title'], 'mod': p.get('metadata_modified'), 'res': [[r.get('name'), r.get('format'), r.get('url')] for r in p.get('resources', [])]}
# muestras de los CSV de INV y del sectorial vitivinícola
for k, v in list(out.items()):
    for nm, fmt, url in v['res']:
        if fmt and fmt.upper() == 'CSV' and ('inv' in k or 'viti' in (nm or '').lower() or 'vin' in (nm or '').lower()):
            v.setdefault('muestras', {})[nm] = muestra(url)
json.dump(out, open('prueba/resumen3.json', 'w'), ensure_ascii=False, indent=1)
