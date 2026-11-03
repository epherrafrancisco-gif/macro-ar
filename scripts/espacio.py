"""Espacio (apartado de Mundo): lanzamientos, satélites en órbita, la NASA y Argentina → espacio.json.

Fuentes (todas permiten uso comercial):
- Launch Library 2 de The Space Devs (ll.thespacedevs.com): próximos y últimos lanzamientos. Sus términos: "You are free to use
  the data in any way, shape, or form". Sin clave: 15 pedidos por hora → acá 2 por corrida; la página lee espacio.json, nunca la API.
- GCAT de Jonathan McDowell (planet4589.org/space/gcat), CC BY 4.0 citándolo: todos los lanzamientos desde 1957 y todos los
  objetos en órbita (dueño, país, tipo).
- USAspending (api.usaspending.gov, gobierno de EE.UU., dominio público): presupuesto de la NASA (agencia 080) por año fiscal.
Si una fuente falla queda lo que había (nunca se inventa).
"""
import csv, io, json, os, re, time, urllib.request
from collections import Counter, defaultdict

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
LL2 = "https://ll.thespacedevs.com/2.3.0/launches/{}/?limit={}&mode=detailed"
GCAT = "https://planet4589.org/space/gcat/tsv/"
diag = {'errores': []}


def bajar(url, intentos=3, datos=None):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Content-Type': 'application/json'} if datos else {'User-Agent': UA}, data=datos)
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except Exception as e:
            if i == intentos - 1 or '429' in str(e): raise
            time.sleep(6 * (i + 1))


def tsv(ruta):
    """Las tablas de GCAT: TSV con la cabecera en una línea que empieza con '#'; las líneas '#' que siguen son comentarios."""
    txt = bajar(GCAT + ruta).decode('utf-8', errors='replace').splitlines()
    cab = txt[0].lstrip('#').split('\t')
    filas = [dict(zip(cab, l.split('\t'))) for l in txt[1:] if l and not l.startswith('#')]
    diag.setdefault('columnas', {})[ruta] = cab
    return [{k.strip(): (v or '').strip() for k, v in f.items()} for f in filas]


viejo = {}
try: viejo = json.load(open(R + 'espacio.json', encoding='utf-8'))
except Exception: pass
out = {'fuentes': 'The Space Devs (Launch Library 2); GCAT, J. McDowell, planet4589.org/space/gcat (CC BY 4.0); USAspending (NASA)',
       'actualizado': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}


def nombre_org(o, k):
    for c in ('ShortEName', 'EName', 'ShortName', 'Name'):
        v = (o or {}).get(c)
        if v and v != '-': return v
    return k


def lanzamiento(l):
    g = lambda *ks: (lambda x: x)(_dig(l, ks))
    return {'n': l.get('name'), 't': l.get('net'), 'prec': (l.get('net_precision') or {}).get('abbrev'),
            'est': (l.get('status') or {}).get('abbrev'), 'estn': (l.get('status') or {}).get('name'),
            'emp': g('launch_service_provider', 'name'), 'tipo_emp': g('launch_service_provider', 'type', 'name'),
            'pais': g('launch_service_provider', 'country', 0, 'alpha_2_code') or g('launch_service_provider', 'country_code'),
            'cohete': g('rocket', 'configuration', 'full_name') or g('rocket', 'configuration', 'name'),
            'mision': g('mission', 'name'), 'mtipo': g('mission', 'type'), 'orbita': g('mission', 'orbit', 'abbrev'),
            'desc': (g('mission', 'description') or '')[:400], 'base': g('pad', 'location', 'name'),
            'pad_pais': g('pad', 'location', 'country', 'alpha_2_code') or g('pad', 'country_code'),
            'video': next((v.get('url') for v in (l.get('vid_urls') or []) if v.get('url')), None)}


def _dig(x, ks):
    for k in ks:
        if isinstance(k, int): x = x[k] if isinstance(x, list) and len(x) > k else None
        else: x = x.get(k) if isinstance(x, dict) else None
        if x is None: return None
    return x


# 1) próximos y últimos lanzamientos (2 pedidos)
for clave, cual, n in (('proximos', 'upcoming', 40), ('ultimos', 'previous', 25)):
    try:
        d = json.loads(bajar(LL2.format(cual, n)))
        out[clave] = [lanzamiento(l) for l in d.get('results', [])]
    except Exception as e:
        diag['errores'].append(f'LL2 {cual}: {e}'); out[clave] = viejo.get(clave, [])

# 2) GCAT: lanzamientos orbitales por año, por país y por empresa/agencia
try:
    orgs = {o.get('Code'): o for o in tsv('tables/orgs.tsv')}
    L = tsv('launch/launch.tsv')
    diag['ej_launch'] = L[-2:]
    anio = defaultdict(lambda: {'n': 0, 'ok': 0, 'pais': Counter(), 'org': Counter()})
    for f in L:
        code = f.get('LaunchCode') or f.get('Launch_Code') or ''
        if not code.startswith('O'): continue          # solo lanzamientos orbitales (los suborbitales empiezan con otra letra)
        a = (f.get('Launch_Date') or '')[:4]
        if not a.isdigit(): continue
        ag = (f.get('Agency') or '').split('/')[0]
        o = orgs.get(ag, {}); pais = o.get('StateCode') or o.get('State') or '?'
        x = anio[a]; x['n'] += 1; x['ok'] += 1 if 'S' in code[1:] else 0
        x['pais'][pais] += 1; x['org'][ag] += 1
    out['anios'] = {a: {'n': v['n'], 'ok': v['ok'], 'pais': dict(v['pais'].most_common(12)), 'org': dict(v['org'].most_common(12))}
                    for a, v in sorted(anio.items())}
    out['orgs'] = {k: {'n': nombre_org(orgs.get(k), k), 'p': (orgs.get(k) or {}).get('StateCode')}
                   for v in anio.values() for k in v['org']}
except Exception as e:
    diag['errores'].append(f'GCAT lanzamientos: {e}')
    for k in ('anios', 'orgs'): out[k] = viejo.get(k, {})

# 3) GCAT: lo que está en órbita hoy (satélites = payloads 'P')
try:
    C = tsv('derived/currentcat.tsv')
    diag['ej_current'] = C[:2]
    pay = [f for f in C if (f.get('Type') or '').startswith('P')]
    out['orbita'] = {'objetos': len(C), 'satelites': len(pay),
                     'por_dueno': dict(Counter(f.get('Owner') for f in pay).most_common(15)),
                     'por_pais': dict(Counter(f.get('State') for f in pay).most_common(15)),
                     'basura': sum(1 for f in C if (f.get('Type') or '').startswith(('D', 'R')))}
    try: orgs
    except NameError: orgs = {}
    out['orbita']['nombres'] = {k: nombre_org(orgs.get(k.split('/')[0]), k)
                                for k in list(out['orbita']['por_dueno']) + list(out['orbita']['por_pais'])}
    # Argentina: todos sus satélites (activos o no) del catálogo completo
    S = tsv('cat/satcat.tsv')
    ar = [f for f in S if f.get('State') == 'AR' and (f.get('Type') or '').startswith('P')]
    out['argentina'] = [{'n': f.get('Name'), 'f': f.get('LDate'), 'est': f.get('Status'), 'dueno': f.get('Owner'),
                         'fab': f.get('Manufacturer'), 'kg': f.get('Mass')} for f in ar]
    out['argentina_orgs'] = {f.get('Owner'): nombre_org(orgs.get(f.get('Owner')), f.get('Owner')) for f in ar}
except Exception as e:
    diag['errores'].append(f'GCAT órbita: {e}')
    for k in ('orbita', 'argentina', 'argentina_orgs'): out[k] = viejo.get(k, {})

# 4) NASA: presupuesto por año fiscal (USAspending, agencia 080)
try:
    d = json.loads(bajar('https://api.usaspending.gov/api/v2/agency/080/budgetary_resources/'))
    out['nasa'] = sorted([{'fy': r.get('fiscal_year'), 'recursos': r.get('agency_budgetary_resources'),
                           'obligado': r.get('agency_total_obligated')} for r in d.get('agency_data_by_year', [])], key=lambda r: r['fy'])
except Exception as e:
    diag['errores'].append(f'NASA: {e}'); out['nasa'] = viejo.get('nasa', [])

json.dump(out, open(R + 'espacio.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(diag, open(R + 'espacio_diag.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', len(out.get('proximos', [])), 'próximos', len(out.get('anios', {})), 'años', os.path.getsize(R + 'espacio.json') // 1024, 'KB', diag['errores'])
