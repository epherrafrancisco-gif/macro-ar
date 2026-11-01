"""Surtidores: precios de nafta, gasoil y GNC en todas las estaciones del país → surtidores.json + surtidores_est.json.

Fuente: Secretaría de Energía, "Precios en surtidor - Resolución 314/2016" (datos abiertos, cada estación informa sus
precios; publicado en datos.gob.ar / datos.energia.gob.ar). Se usan solo los precios informados en los últimos DIAS días
(muchas estaciones informan poco: un precio viejo no es el de hoy). La historia se arma guardando la mediana de cada día
(como la pizarra de Rosario) y, si se puede leer, se completa con el archivo de precios históricos.
Nunca inventa: si la fuente falla, queda lo que había.
"""
import csv, io, json, os, re, statistics, time, urllib.request, urllib.robotparser
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
CKANS = ["https://datos.gob.ar/api/3/action/package_show?id={}", "http://datos.energia.gob.ar/api/3/action/package_show?id={}"]
PAQ = "energia-precios-surtidor---resolucion-3142016"
DIAS = 45
ESPEJO = "https://datos.pulsomacro.com.ar/surtidores/vigentes.csv"
HOY = datetime.now(timezone(timedelta(hours=-3))).date()
diag = {'errores': [], 'fuentes': {}}

# productos: clave corta ← patrón del nombre que usa la Secretaría
PROD = [('super', r'n?afta.*s[uú]per'), ('premium', r'n?afta.*premium'), ('gasoil', r'gas ?oil.*grado 2'),
        ('gasoil3', r'gas ?oil.*grado 3'), ('gnc', r'^gnc'), ('kerosene', r'kerosene')]
PNOM = {'super': 'Nafta súper', 'premium': 'Nafta premium', 'gasoil': 'Gasoil común', 'gasoil3': 'Gasoil premium',
        'gnc': 'GNC', 'kerosene': 'Querosén'}
RANGO = {'super': (300, 6000), 'premium': (300, 7000), 'gasoil': (300, 6000), 'gasoil3': (300, 7000), 'gnc': (100, 3000),
         'kerosene': (300, 8000)}


def abrir(url, timeout=180):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=timeout)


def bajar(url, intentos=3):
    for i in range(intentos):
        try:
            with abrir(url) as r: return r.read()
        except Exception:
            if i == intentos - 1: raise
            time.sleep(5 * (i + 1))


def permitido(url):
    try:
        base = re.match(r'(https?://[^/]+)', url).group(1)
        rp = urllib.robotparser.RobotFileParser(); rp.set_url(base + '/robots.txt'); rp.read()
        return rp.can_fetch('PulsoMacro', url)
    except Exception:
        return True


def prod_de(nombre):
    n = (nombre or '').lower()
    for k, p in PROD:
        if re.search(p, n): return k
    return None


def fecha(s):
    s = (s or '').strip()
    m = re.match(r'(\d{4})-(\d\d)-(\d\d)', s)
    if m: return date(int(m[1]), int(m[2]), int(m[3]))
    m = re.match(r'(\d\d?)/(\d\d?)/(\d{4})', s)
    return date(int(m[3]), int(m[2]), int(m[1])) if m else None


def num(v):
    try: return float(str(v).replace(',', '.'))
    except Exception: return None


med = lambda a: round(statistics.median(a), 1) if a else None
viejo = {}
try: viejo = json.load(open(R + 'surtidores.json', encoding='utf-8'))
except Exception: pass
out = {'fuente': 'Secretaría de Energía de la Nación, precios en surtidor (Resolución 314/2016), datos abiertos',
       'dias': DIAS}

# ---------- recursos del paquete ----------
recs = None
for c in CKANS:
    try:
        recs = json.loads(bajar(c.format(PAQ)))['result']['resources']; diag['ckan'] = c.split('/api')[0]; break
    except Exception as e:
        diag['errores'].append(f'ckan {c.split("/api")[0]}: {e}')
diag['recursos'] = [[r.get('name'), r.get('format'), r.get('url'), r.get('last_modified') or r.get('created')] for r in (recs or [])]


def recurso(patron):
    for r in recs or []:
        if (r.get('format') or '').upper() == 'CSV' and re.search(patron, (r.get('name') or '') + ' ' + (r.get('url') or ''), re.I):
            return r
    return None


def candidatos(r):
    """El mismo archivo por varios caminos: desde Actions datos.energia.gob.ar a veces no responde (timeout)."""
    u = r['url']; out = []
    if 'precios-en-surtidor' in u: out.append(ESPEJO)   # copia que deja el Worker pulso-vivo en R2
    out += [u.replace('http://', 'https://'), u]
    return out


def abrir_alguno(r, timeout):
    errs = []
    for u in candidatos(r):
        try:
            if not permitido(u): errs.append('robots ' + u); continue
            x = abrir(u, timeout if u == ESPEJO else 20); diag.setdefault('url_ok', []).append([u, x.headers.get('Last-Modified'), x.headers.get('Content-Length')]); return x
        except Exception as e:
            errs.append(f'{u}: {e}')
    raise Exception(' | '.join(errs))


# ---------- precios vigentes: todas las estaciones ----------
est = {}
try:
    rec = recurso(r'vigente')
    if not rec: raise Exception('sin recurso de precios vigentes')
    with abrir_alguno(rec, 90) as r:
        txt = io.TextIOWrapper(r, encoding='utf-8-sig', errors='replace', newline='')
        rd = csv.DictReader(txt)
        diag['columnas'] = rd.fieldnames
        nprod, n = defaultdict(int), 0
        for f in rd:
            n += 1
            nprod[f.get('producto', '')] += 1
            k = prod_de(f.get('producto'))
            if not k: continue
            if 'diurno' not in (f.get('tipohorario') or 'diurno').lower(): continue  # el precio de día (el nocturno es casi igual y lo informan pocas)
            p, fv = num(f.get('precio')), fecha(f.get('fecha_vigencia') or f.get('indice_tiempo'))
            if p is None or not (RANGO[k][0] <= p <= RANGO[k][1]) or not fv: continue
            eid = f.get('idempresa') or (f.get('cuit', '') + f.get('direccion', ''))
            e = est.setdefault(eid, {'e': (f.get('empresa') or '').strip().title(), 'b': (f.get('empresabandera') or '').strip(),
                                     'd': (f.get('direccion') or '').strip().title(), 'l': (f.get('localidad') or '').strip().title(),
                                     'p': (f.get('provincia') or '').strip().title(), 'la': num(f.get('latitud')), 'lo': num(f.get('longitud')), 'x': {}})
            if k not in e['x'] or fv > e['x'][k][1]: e['x'][k] = (p, fv)
        diag['filas'] = n
        diag['productos_crudos'] = dict(sorted(nprod.items(), key=lambda x: -x[1]))
    diag['fuentes']['vigentes'] = 'ok'
except Exception as e:
    diag['errores'].append(f'vigentes: {e}'); diag['fuentes']['vigentes'] = 'error'

PROV_FIX = {'Capital Federal': 'CABA', 'Ciudad Autonoma De Buenos Aires': 'CABA', 'Ciudad Autónoma De Buenos Aires': 'CABA',
            'Tierra Del Fuego': 'Tierra del Fuego', 'Santiago Del Estero': 'Santiago del Estero', 'Entre Rios': 'Entre Ríos',
            'Rio Negro': 'Río Negro', 'Neuquen': 'Neuquén', 'Cordoba': 'Córdoba', 'Tucuman': 'Tucumán'}
BAND = lambda b: ('Sin bandera' if not b or re.search(r'blanca|sin empresa|^-$', b, re.I) else
                  'YPF' if re.search(r'ypf', b, re.I) else 'Shell' if re.search(r'shell|raizen', b, re.I) else
                  'Axion' if re.search(r'axion|esso', b, re.I) else 'Puma' if re.search(r'puma', b, re.I) else
                  'Gulf' if re.search(r'gulf', b, re.I) else 'Dapsa' if re.search(r'dapsa', b, re.I) else 'Otras')

if est:
    lim = HOY - timedelta(days=DIAS)
    fresh = defaultdict(list)          # producto → [(precio, estación)]
    for eid, e in est.items():
        e['p'] = PROV_FIX.get(e['p'], e['p']); e['B'] = BAND(e['b'])
        for k, (p, fv) in e['x'].items():
            if fv >= lim: fresh[k].append((p, e))
    resumen = {}
    for k, lst in fresh.items():
        ps = sorted(p for p, _ in lst)
        if len(ps) < 20: continue
        q = lambda a, x: a[min(len(a) - 1, int(len(a) * x))]
        resumen[k] = {'n': PNOM[k], 'med': med(ps), 'prom': round(sum(ps) / len(ps), 1), 'p10': q(ps, .1), 'p90': q(ps, .9),
                      'min': ps[0], 'max': ps[-1], 'est': len(ps)}
        prov, band, provband = defaultdict(list), defaultdict(list), defaultdict(list)
        for p, e in lst:
            prov[e['p']].append(p); band[e['B']].append(p)
        resumen[k]['prov'] = sorted([[pv, med(v), len(v)] for pv, v in prov.items() if len(v) >= 3], key=lambda x: x[1])
        resumen[k]['band'] = sorted([[b, med(v), len(v)] for b, v in band.items() if len(v) >= 5], key=lambda x: -x[2])
        # localidades más caras y más baratas (con al menos 4 estaciones)
        loc = defaultdict(list)
        for p, e in lst: loc[(e['l'], e['p'])].append(p)
        lc = sorted([[l, pv, med(v), len(v)] for (l, pv), v in loc.items() if len(v) >= 4], key=lambda x: x[2])
        resumen[k]['loc_bar'], resumen[k]['loc_car'] = lc[:10], lc[-10:][::-1]
    out['productos'] = resumen
    out['estaciones'] = len(est)
    out['fecha'] = str(max((fv for e in est.values() for _, fv in e['x'].values() if fv <= HOY), default=HOY))
    # historia propia: la mediana de cada producto, una por día
    hist = (viejo.get('hist') or {})
    hist[str(HOY)] = {k: v['med'] for k, v in resumen.items()}
    out['hist'] = dict(sorted(hist.items())[-1500:])
    # estaciones para el buscador (archivo aparte: la página lo baja solo al buscar)
    lst = []
    for e in est.values():
        x = {k: [p, str(fv)] for k, (p, fv) in e['x'].items() if fv >= HOY - timedelta(days=180)}
        if not x: continue
        lst.append([e['B'], e['b'] if e['B'] == 'Otras' else '', e['e'][:60], e['d'][:70], e['l'], e['p'], x,
                    round(e['la'], 4) if e['la'] else None, round(e['lo'], 4) if e['lo'] else None])
    with open(R + 'surtidores_est.json', 'w', encoding='utf-8') as f:
        json.dump({'f': out['fecha'], 'e': lst}, f, ensure_ascii=False, separators=(',', ':'))
else:
    for k in ('productos', 'estaciones', 'fecha', 'hist'):
        if k in viejo: out[k] = viejo[k]

# ---------- historia mensual: precios históricos (si el archivo se puede leer en un tiempo razonable) ----------
try:
    rec = recurso(r'hist[oó]ric')
    if rec:
        t0, men, n = time.time(), defaultdict(lambda: defaultdict(list)), 0
        with abrir_alguno(rec, 90) as r:
            diag['hist_bytes'] = r.headers.get('Content-Length')
            rd = csv.DictReader(io.TextIOWrapper(r, encoding='utf-8-sig', errors='replace', newline=''))
            diag['hist_columnas'] = rd.fieldnames
            for f in rd:
                n += 1
                if time.time() - t0 > 600: diag['errores'].append('historicos: cortado por tiempo'); break
                k = prod_de(f.get('producto'))
                if not k or 'diurno' not in (f.get('tipohorario') or 'diurno').lower(): continue
                p = num(f.get('precio')); fv = f.get('indice_tiempo') or f.get('fecha_vigencia') or ''
                m = re.match(r'(\d{4})-(\d\d)', fv)
                if p is None or not m or not (RANGO[k][0] * .01 <= p <= RANGO[k][1]): continue
                men[k][m[1] + '-' + m[2]].append(p)
        diag['hist_filas'] = n
        out['mensual'] = {k: [[mm, med(v), len(v)] for mm, v in sorted(d.items()) if len(v) >= 30] for k, d in men.items()}
        diag['fuentes']['historicos'] = 'ok'
except Exception as e:
    diag['errores'].append(f'historicos: {e}'); diag['fuentes']['historicos'] = 'error'
if not out.get('mensual') and viejo.get('mensual'): out['mensual'] = viejo['mensual']

# ---------- ventas mensuales al mercado interno (miles de m³; Secretaría de Energía vía la API de series) ----------
VENTAS = {'super': '38.3_NS_1994_M_11', 'premium': '38.3_NU_1994_M_11', 'gasoil': '41.3_GO_0_A_7', 'gnc': '364.3_GNCGNC__3'}
try:
    d = json.loads(bajar('https://apis.datos.gob.ar/series/api/series/?ids=' + ','.join(VENTAS.values()) + '&limit=1000&format=json'))
    out['ventas'] = {k: [[r[0][:7], round(r[i + 1], 1)] for r in d['data'] if r[i + 1] is not None] for i, k in enumerate(VENTAS)}
    diag['fuentes']['ventas'] = 'ok'
except Exception as e:
    diag['errores'].append(f'ventas: {e}'); diag['fuentes']['ventas'] = 'error'
    if viejo.get('ventas'): out['ventas'] = viejo['ventas']

out['diag'] = diag
out['actualizado'] = str(HOY)
with open(R + 'surtidores.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
print(json.dumps(diag, ensure_ascii=False)[:4000])
