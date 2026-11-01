import requests, json, re
UA = {'User-Agent': 'Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)'}
out = {}
def j(u):
    try:
        r = requests.get(u, headers=UA, timeout=60); return r.json() if r.status_code == 200 else {'status': r.status_code}
    except Exception as e: return {'err': str(e)}
def t(u):
    try:
        r = requests.get(u, headers=UA, timeout=60); return {'status': r.status_code, 'txt': r.text[:4000]}
    except Exception as e: return {'err': str(e)}
for q in ['vino', 'mosto', 'uva', 'vitivinicola', 'vitivinícola', 'espumante', 'exportaciones vino']:
    d = j('https://apis.datos.gob.ar/series/api/search/?q=' + q + '&limit=40')
    out['q_' + q] = [[x['field']['id'], x['field'].get('description'), x['field'].get('frequency'), x['field'].get('time_index_start'), x['field'].get('time_index_end'), x['dataset'].get('title')] for x in d.get('data', [])] if 'data' in d else d
ids = '41.3_DAVMI_0_A_42,453.2_VINOINO_0_0_4_89,105.1_I2VC_2016_M_19'
out['series'] = j('https://apis.datos.gob.ar/series/api/series/?ids=' + ids + '&last=14&format=json')
out['ckan_uvas'] = j('https://datos.gob.ar/api/3/action/package_show?id=agroindustria-inv---produccion-uvas')
out['ckan_search'] = j('https://datos.gob.ar/api/3/action/package_search?q=vitivinicultura&rows=20')
if isinstance(out['ckan_search'], dict) and out['ckan_search'].get('result'):
    out['ckan_search'] = [[p['name'], p['title'], p.get('metadata_modified'), [[r.get('name'), r.get('format'), r.get('url')] for r in p.get('resources', [])][:6]] for p in out['ckan_search']['result']['results']]
if isinstance(out['ckan_uvas'], dict) and out['ckan_uvas'].get('result'):
    p = out['ckan_uvas']['result']; out['ckan_uvas'] = [p['title'], p.get('metadata_modified'), [[r.get('name'), r.get('format'), r.get('url'), r.get('last_modified')] for r in p.get('resources', [])]]
out['bcm_robots'] = t('https://www.bolsamza.com.ar/robots.txt')
out['oiv_robots'] = t('https://www.oiv.int/robots.txt')
out['inv_gov_robots'] = t('https://www.inv.gov.ar/robots.txt')
json.dump(out, open('prueba/resumen2.json', 'w'), ensure_ascii=False, indent=1)
