"""0km: patentamientos (inscripciones iniciales) de autos de la DNRPA → autos.json.

Fuente: Portal de Datos de la Justicia Argentina (datos.jus.gob.ar), "DNRPA. Inscripciones iniciales de autos", licencia
CC BY 4.0 (permite uso comercial citando la fuente). Un ZIP por año (2018 en adelante) + un CSV del último mes.
Historia larga (desde 2000, por provincia, todos los automotores): "Estadística de trámites de automotores".

Cada fila es una inscripción con datos del primer titular: acá SOLO se cuentan totales (marca, modelo, tipo, origen,
provincia, persona física o empresa). Nunca se guarda nada de una persona. Si un auto tiene varios titulares, cada fila pesa
su porcentaje de titularidad (así cada auto suma 1).

Los años cerrados se resumen una vez y quedan en autos_cache/AAAA.json; cada corrida solo baja el año en curso y el mes.
"""
import csv, io, json, os, re, sys, time, urllib.request, zipfile
from collections import Counter, defaultdict

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
CACHE = R + 'autos_cache/'
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
CKAN = "https://datos.jus.gob.ar/api/3/action/package_show?id={}"
PAQ = 'inscripciones-iniciales-de-autos'
PAQ_HIST = 'estadistica-de-tramites-de-automotores'
HOY = time.strftime('%Y-%m-%d')
diag = {'errores': [], 'archivos': []}
VERSION = 2   # subir si cambia la forma de contar (rehace autos_cache/)
csv.field_size_limit(10 ** 8)


def bajar(url, intentos=3):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception as e:
            if i == intentos - 1: raise
            time.sleep(5 * (i + 1))


def recursos(paq):
    return json.loads(bajar(CKAN.format(paq)))['result']['resources']


def texto(b):
    for enc in ('utf-8-sig', 'latin-1'):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode('utf-8', errors='replace')


def lector(txt):
    primera = txt[:4000].split('\n')[0]
    sep = ';' if primera.count(';') > primera.count(',') else ','
    return csv.DictReader(io.StringIO(txt), delimiter=sep)


def col(cab, *claves, no=()):
    """La primera columna cuyo nombre tiene todas las claves (y ninguna de `no`)."""
    for c in cab:
        k = c.lower()
        if all(x in k for x in claves) and not any(x in k for x in no): return c
    return None


def mes_de(v):
    v = (v or '').strip()
    m = re.match(r'(\d{4})-(\d{2})', v)
    if m: return f'{m[1]}-{m[2]}'
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', v)
    if m: return f'{m[3]}-{int(m[2]):02d}'
    return None


def categoria(t):
    """Tipo de la DNRPA → auto, suv, pickup, util (livianos: lo que la gente llama "0km") o pesado / otro."""
    t = t or ''
    if re.search(r'CAMION|TRACTOR|CHASIS|REMOLQUE|ACOPLADO|TRAILER|CARRETON|VOLQUETE|BUS|PASAJEROS|UNIMOG|BOMBER|AMBULANCIA|'
                 r'CASA RODANTE|COMPENSADOR|HORMIGON|GRUA|CISTERNA', t): return 'pesado'
    if 'PICK' in t: return 'pickup'
    if re.search(r'RURAL|TODO TERRENO|JEEP|SUV|STATION|CAMIONETA', t): return 'suv'
    if re.search(r'FURGON|UTILITARIO|PANEL', t): return 'util'
    if re.search(r'SEDAN|COUPE|COUPÉ|CONVERTIBLE|DESCAPOTABLE|CABRIOLET|ROADSTER|FAMILIAR|AUTOMOVIL|AUTOMÓVIL|HATCH|LIMUSINA', t): return 'auto'
    return 'otro'


LIVIANOS = ('auto', 'suv', 'pickup', 'util')
ORIGEN = {'NACIONAL': 'Nacional', 'PROTOCOLO 21': 'Brasil', 'IMPORTADO': 'Importado'}   # Protocolo 21 = Mercosur con Brasil

limpio = lambda s: re.sub(r'\s+', ' ', (s or '').strip().upper())
nuevo_mes = lambda: {'tot': 0.0, 'org': Counter(), 'mar': Counter(), 'mod': Counter(), 'prov': Counter(), 'tip': Counter(),
                     'per': Counter(), 'cat': Counter(), 'mo': Counter(), 'mt': Counter(), 'morg': Counter()}


def resumir(txt, meses, nombre):
    rd = lector(txt); cab = rd.fieldnames or []
    c_fecha = col(cab, 'fecha_inscripcion') or col(cab, 'inscripcion', 'fecha') or col(cab, 'tramite_fecha') or col(cab, 'fecha')
    c_mar = col(cab, 'marca', 'desc') or col(cab, 'marca', no=('codigo', 'cod'))
    c_mod = col(cab, 'modelo', 'desc') or col(cab, 'modelo', no=('codigo', 'cod', 'anio', 'año'))
    c_tip = col(cab, 'tipo', 'desc', no=('persona', 'tramite')) or col(cab, 'automotor_tipo', no=('cod',))
    c_org = col(cab, 'origen')
    c_prov = col(cab, 'registro', 'provincia', no=('id', 'cod')) or col(cab, 'provincia', no=('id', 'cod', 'titular'))
    c_per = col(cab, 'tipo_persona') or col(cab, 'persona')
    c_pct = col(cab, 'porcentaje')
    c_anio = col(cab, 'anio_modelo') or col(cab, 'modelo', 'anio')
    diag['archivos'].append({'archivo': nombre, 'columnas': cab, 'usadas': {'fecha': c_fecha, 'marca': c_mar, 'modelo': c_mod,
                             'tipo': c_tip, 'origen': c_org, 'provincia': c_prov, 'persona': c_per, 'porcentaje': c_pct, 'anio_modelo': c_anio}})
    filas = 0; peso_tot = 0.0; ej = []; usados = 0
    for f in rd:
        filas += 1
        m = mes_de(f.get(c_fecha))
        if not m: continue
        w = 1.0
        if c_pct:
            try:
                p = float(str(f.get(c_pct) or '').replace(',', '.'))
                if 0 < p <= 100: w = p / 100
            except ValueError: pass
        # 0km: año de modelo igual al del patentamiento o el anterior (afuera los usados importados: camiones viejos, clásicos)
        try:
            if c_anio and int(str(f.get(c_anio) or '0')[:4]) < int(m[:4]) - 1: usados += w; continue
        except ValueError: pass
        mar, mod = limpio(f.get(c_mar)), limpio(f.get(c_mod))
        tip, org, prov = limpio(f.get(c_tip)), limpio(f.get(c_org)), limpio(f.get(c_prov))
        org = ORIGEN.get(org, org.title())
        per = limpio(f.get(c_per))[:1] if c_per else ''
        cat = categoria(tip)
        x = meses[m]
        x['cat'][cat] += w
        if cat not in LIVIANOS: continue      # el resto de los conteos es solo de livianos
        peso_tot += w
        x['tot'] += w; x['org'][org] += w; x['mar'][mar] += w; x['mod'][mar + '|' + mod] += w; x['prov'][prov] += w
        x['tip'][tip] += w
        if per: x['per'][per] += w
        x['mt'][mar + '|' + mod + '|' + tip] += w; x['morg'][mar + '|' + org] += w
        if len(ej) < 4:  # ejemplo para revisar, SIN ninguna columna del titular
            ej.append({k: v for k, v in f.items() if k and 'titular' not in k.lower()})
    diag['archivos'][-1].update({'filas': filas, 'livianos_0km': round(peso_tot), 'usados': round(usados), 'ejemplo': ej[:2]})


def a_json(x):
    r2 = lambda c: {k: round(v, 1) for k, v in c.most_common() if v >= .5}
    return {'tot': round(x['tot']), 'org': r2(x['org']), 'mar': r2(x['mar']), 'mod': r2(x['mod']), 'prov': r2(x['prov']),
            'tip': r2(x['tip']), 'per': r2(x['per']), 'cat': r2(x['cat']), 'mt': r2(x['mt']), 'morg': r2(x['morg'])}


def leer_zip(b, meses, nombre):
    z = zipfile.ZipFile(io.BytesIO(b))
    for n in z.namelist():
        if n.lower().endswith('.csv'):
            resumir(texto(z.read(n)), meses, nombre + ':' + n)


def principal():
    os.makedirs(CACHE, exist_ok=True)
    recs = recursos(PAQ)
    anuales, mensual = {}, None
    for r in recs:
        u = r.get('url') or ''
        m = re.search(r'(20\d\d)\.zip$', u)
        if m: anuales[int(m[1])] = u
        m = re.search(r'(20\d\d)(\d\d)\.csv$', u)
        if m: mensual = (f'{m[1]}-{m[2]}', u)
    diag['recursos'] = {'anuales': sorted(anuales), 'mensual': mensual[0] if mensual else None}
    anio_hoy = int(HOY[:4])
    todos = {}
    for a in sorted(anuales):
        f = CACHE + f'{a}.json'
        cerrado = a < anio_hoy and a < max(anuales)
        if cerrado and os.path.exists(f):
            c = json.load(open(f, encoding='utf-8'))
            if c.pop('_v', None) == VERSION: todos.update(c); continue
        meses = defaultdict(nuevo_mes)
        try: leer_zip(bajar(anuales[a]), meses, f'{a}.zip')
        except Exception as e: diag['errores'].append(f'{a}.zip: {e}'); continue
        res = {m: a_json(x) for m, x in sorted(meses.items()) if m.startswith(str(a))}
        if cerrado: json.dump({'_v': VERSION, **res}, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        todos.update(res)
    if mensual and mensual[0] not in todos:
        meses = defaultdict(nuevo_mes)
        try:
            resumir(texto(bajar(mensual[1])), meses, mensual[0] + '.csv')
            if mensual[0] in meses: todos[mensual[0]] = a_json(meses[mensual[0]])
        except Exception as e: diag['errores'].append(f'mensual: {e}')
    return todos


def historia():
    """Inscripciones iniciales de todos los automotores por mes desde 2000 (suma de provincias)."""
    try:
        recs = recursos(PAQ_HIST)
        cand = [r for r in recs if re.search(r'inscripciones.iniciales', (r.get('name') or '') + (r.get('url') or ''), re.I)
                and (r.get('url') or '').lower().endswith('.csv')]
        if not cand: diag['errores'].append('historia: no está el recurso'); return {}
        u = sorted(cand, key=lambda r: r.get('url'))[-1]['url']
        rd = lector(texto(bajar(u))); cab = rd.fieldnames or []
        ca, cm, cc, ct = col(cab, 'anio'), col(cab, 'mes'), col(cab, 'cantidad'), col(cab, 'tipo_vehiculo')
        cp = col(cab, 'provincia_inscripcion')
        diag['historia'] = {'url': u, 'columnas': cab}
        h = defaultdict(Counter); prov = defaultdict(Counter)
        for f in rd:
            try:
                m = f'{int(f[ca])}-{int(f[cm]):02d}'; t = limpio(f.get(ct)) if ct else 'TOTAL'; n = int(float(f[cc]))
            except (ValueError, TypeError, KeyError): continue
            h[t][m] += n
            if cp: prov[t + '|' + m][limpio(f.get(cp))] += n
        diag['historia']['tipos'] = {t: sum(c.values()) for t, c in h.items()}
        out = {t: dict(sorted(c.items())) for t, c in h.items()}
        # provincias del último mes de cada tipo (para tener un mes más fresco que el detalle)
        out['_prov'] = {t: dict(prov[t + '|' + max(c)].most_common()) for t, c in h.items()}
        return out
    except Exception as e:
        diag['errores'].append(f'historia: {e}'); return {}


todos = principal()
hist = historia()
viejo = {}
try: viejo = json.load(open(R + 'autos.json', encoding='utf-8'))
except Exception: pass
if not todos:
    print('Sin datos nuevos; queda lo que había', diag['errores']); json.dump(diag, open(R + 'autos_diag.json', 'w'), ensure_ascii=False, indent=1); sys.exit(0)

meses = sorted(todos)
ult = meses[-1]
# serie mensual liviana (todo el período) + detalle de los últimos 25 meses y por año
serie = [{'m': m, 't': todos[m]['tot'], 'org': {k: round(v) for k, v in todos[m]['org'].items()},
          'cat': {k: round(v) for k, v in todos[m].get('cat', {}).items()}, 'per': {k: round(v) for k, v in todos[m]['per'].items()}}
         for m in meses]
det = {}
for m in meses[-25:]:
    x = todos[m]
    det[m] = {'mar': {k: round(v) for k, v in x['mar'].items()}, 'mod': {k: round(v) for k, v in list(x['mod'].items())[:400]},
              'prov': {k: round(v) for k, v in x['prov'].items()}}
anios = defaultdict(lambda: {'tot': 0, 'mar': Counter(), 'mod': Counter()})
for m in meses:
    a = anios[m[:4]]; x = todos[m]; a['tot'] += x['tot']
    for k, v in x['mar'].items(): a['mar'][k] += v
    for k, v in x['mod'].items(): a['mod'][k] += v
anio_out = {a: {'tot': round(v['tot']), 'n': sum(1 for m in meses if m[:4] == a),
                'mar': {k: round(n) for k, n in v['mar'].most_common()},
                'mod': {k: round(n) for k, n in v['mod'].most_common(300)}} for a, v in sorted(anios.items())}
# ficha de modelo: tipo y origen más comunes (últimos 12 meses)
mt, morg = Counter(), Counter()
for m in meses[-12:]:
    for k, v in todos[m]['mt'].items(): mt[k] += v
    for k, v in todos[m]['morg'].items(): morg[k] += v
tipo_de = {}
for k, v in mt.most_common():
    mar, mod, tip = k.split('|', 2)
    tipo_de.setdefault(mar + '|' + mod, tip)
org_marca = defaultdict(dict)
for k, v in morg.items():
    mar, org = k.split('|', 1); org_marca[mar][org] = round(v)
out = {'fuente': 'DNRPA (Ministerio de Justicia), datos abiertos: inscripciones iniciales de autos. Licencia CC BY 4.0.',
       'actualizado': HOY, 'ultimo_mes': ult, 'serie': serie, 'det': det, 'anios': anio_out,
       'tipo_modelo': tipo_de, 'origen_marca': org_marca, 'hist': hist or viejo.get('hist', {})}
json.dump(out, open(R + 'autos.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(diag, open(R + 'autos_diag.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', ult, len(meses), 'meses', os.path.getsize(R + 'autos.json') // 1024, 'KB', diag['errores'])
