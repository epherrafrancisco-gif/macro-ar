import requests, pdfplumber, io, re, json, os
UA = {'User-Agent': 'Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)'}
out = {}
def get(u):
    try:
        r = requests.get(u, headers=UA, timeout=60); return r
    except Exception as e: return str(e)
r = get('https://www.argentina.gob.ar/robots.txt'); out['robots'] = r.text if hasattr(r, 'text') else r
for nombre, pag in [('mi', 'https://www.argentina.gob.ar/inv/vinos/estadisticas/mercado-interno/informes'),
                    ('me', 'https://www.argentina.gob.ar/inv/estadisticas-vitivinicolas/mercado-externo/informes-mensuales'),
                    ('cos', 'https://www.argentina.gob.ar/inv/estadisticas-vitivinicolas/cosecha/anuarios'),
                    ('cpc', 'https://www.argentina.gob.ar/inv/estadisticas-vitivinicolas/consumo-capita'),
                    ('exist', 'https://www.argentina.gob.ar/inv/vinos/estadisticas/existencias')]:
    r = get(pag)
    if hasattr(r, 'text'):
        out[nombre + '_status'] = r.status_code
        out[nombre + '_links'] = sorted(set(re.findall(r'href="([^"]+\.(?:pdf|xlsx?|csv))"', r.text)))[:40]
    else: out[nombre + '_err'] = r
def pdf(u, tag, pages=6):
    r = get(u)
    if not hasattr(r, 'content') or r.status_code != 200: out[tag + '_err'] = getattr(r, 'status_code', r); return
    with pdfplumber.open(io.BytesIO(r.content)) as d:
        out[tag + '_pags'] = len(d.pages)
        txt = []
        for i, p in enumerate(d.pages[:pages]):
            txt.append(f'--- página {i+1} ---\n' + (p.extract_text() or ''))
            for t in p.extract_tables()[:4]: txt.append('TABLA: ' + json.dumps(t, ensure_ascii=False)[:3000])
        open(f'prueba/{tag}.txt', 'w').write('\n'.join(txt))
pdf('https://www.argentina.gob.ar/sites/default/files/2018/10/informe_mensual_merc._interno_de_vinos_-_sep26.pdf', 'mi_sep26', 8)
pdf('https://www.argentina.gob.ar/sites/default/files/2018/10/comercializacion_mercado_externo_septiembre_2026.pdf', 'me_sep26', 8)
pdf('https://www.argentina.gob.ar/sites/default/files/2018/10/consumo_per_capita_1963-2024.pdf', 'cpc', 3)
# INDEC precios medios: vino común (datos.gob.ar)
r = get('https://apis.datos.gob.ar/series/api/search/?q=vino&limit=30')
out['series_vino'] = r.json() if hasattr(r, 'json') and r.status_code == 200 else str(getattr(r, 'status_code', r))
json.dump(out, open('prueba/resumen.json', 'w'), ensure_ascii=False, indent=1)
