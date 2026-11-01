"""Vinos y uvas: arma vinos.json con datos abiertos del INV (Instituto Nacional de Vitivinicultura) publicados en
datos.gob.ar / datos.magyp.gob.ar (CSV, licencia abierta) y series de la API de Series de Tiempo (datos.gob.ar).

Ojo: los informes mensuales del INV en argentina.gob.ar son PDF y su robots.txt prohíbe bajar PDF (Disallow /*.pdf$):
no se usan. Lo mensual sale de la API de series; lo anual (cosecha, superficie, elaboración, exportaciones, mercado
interno por envase y variedad) de los CSV. Si una fuente falla, queda lo que había en vinos.json (nunca se inventa).
"""
import csv, io, json, os, re, time, urllib.request
from collections import defaultdict

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
CKAN = "https://datos.gob.ar/api/3/action/package_show?id={}"
API = "https://apis.datos.gob.ar/series/api/series/?ids={}&limit=1000&format=json"
SERIES = {
    'precio': '105.1_I2VC_2016_M_19',      # IPC-GBA, precio medio del vino común ($ por litro), mensual
}
diag = {'errores': [], 'fuentes': {}}


def bajar(url, intentos=3):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:
            if i == intentos - 1: raise
            time.sleep(4 * (i + 1))


def paquete(nombre):
    d = json.loads(bajar(CKAN.format(nombre)))
    return d['result']['resources']


def csv_filas(url):
    txt = bajar(url).decode('utf-8-sig', errors='replace')
    return list(csv.DictReader(io.StringIO(txt)))


def recurso(recs, patron, fmt='CSV'):
    """El recurso cuyo nombre matchea el patrón; si tiene un año, el más nuevo."""
    cand = []
    for r in recs:
        nm = r.get('name') or ''
        if (r.get('format') or '').upper() != fmt or not re.search(patron, nm, re.I): continue
        anios = [int(a) for a in re.findall(r'(20\d\d)', nm)]
        cand.append((max(anios) if anios else 0, nm, r['url']))
    return sorted(cand)[-1] if cand else None


num = lambda v: float(str(v).replace(',', '.')) if v not in (None, '', '-') else 0.0
viejo = {}
try: viejo = json.load(open(R + 'vinos.json', encoding='utf-8'))
except Exception: pass
out = {'fuente': 'Instituto Nacional de Vitivinicultura (INV), datos abiertos; INDEC vía datos.gob.ar'}


def tramo(nombre, fn):
    try:
        fn(); diag['fuentes'][nombre] = 'ok'
    except Exception as e:
        diag['errores'].append(f'{nombre}: {e}')
        diag['fuentes'][nombre] = 'error'
        if nombre in viejo: out[nombre] = viejo[nombre]


# ---------- series mensuales (API de Series de Tiempo) ----------
def series():
    d = json.loads(bajar(API.format(','.join(SERIES.values()))))
    claves = list(SERIES)
    s = {k: [] for k in claves}
    for fila in d['data']:
        for i, k in enumerate(claves):
            v = fila[i + 1]
            if v is not None: s[k].append([fila[0][:7], round(v, 2)])
    out['series'] = s
tramo('series', series)


# ---------- cosecha de uva (quintales) por provincia, 2012 en adelante ----------
def cosecha():
    recs = paquete('agroindustria-inv---produccion-uvas')
    _, nm, url = recurso(recs, r'Serie 20\d\d')
    por = defaultdict(lambda: defaultdict(float))
    for f in csv_filas(url):
        por[int(f['anio'])][f['provincia']] += num(f['quintales'])
    anios = sorted(por)
    out['cosecha'] = {'anios': anios, 'prov': {}, 'total': [round(sum(por[a].values())) for a in anios], 'fuente': nm}
    provs = sorted({p for a in anios for p in por[a]}, key=lambda p: -por[anios[-1]].get(p, 0))
    for p in provs[:6]: out['cosecha']['prov'][p] = [round(por[a].get(p, 0)) for a in anios]
    out['cosecha']['otras'] = [round(sum(v for p, v in por[a].items() if p not in provs[:6])) for a in anios]
    # la última vendimia por variedad y color
    ult = recurso(recs, r'Producci.n de uvas 20\d\d$')
    if ult:
        var, col = defaultdict(float), defaultdict(float)
        filas = csv_filas(ult[2])
        campo = next((c for c in filas[0] if c.lower() in ('quintales', 'quintales_uva', 'cantidad')), list(filas[0])[-1])
        for f in filas:
            q = num(f[campo]); var[f.get('variedad', '?')] += q; col[f.get('color', '?')] += q
        tot = sum(var.values())
        out['cosecha']['ultima'] = {'anio': ult[0], 'total': round(tot),
                                    'variedades': [[k, round(v)] for k, v in sorted(var.items(), key=lambda x: -x[1])[:12]],
                                    'color': {k: round(v) for k, v in col.items()}}
tramo('cosecha', cosecha)


# ---------- superficie con viñedos (ha) ----------
def superficie():
    recs = paquete('agroindustria-inv---superficie-implantada-con-vinedos')
    _, nm, url = recurso(recs, r'Superficie implantada')
    por = defaultdict(lambda: defaultdict(float))
    for f in csv_filas(url): por[int(f['anio'])][f['provincia']] += num(f['superficie_ha'])
    anios = sorted(por)
    out['superficie'] = {'anios': anios, 'total': [round(sum(por[a].values())) for a in anios]}
    ult = recurso(recs, r'Superficie con vi.edos 20\d\d')
    if ult:
        var, prov, col, edad = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
        for f in csv_filas(ult[2]):
            ha = num(f['superficie_plantada'])
            var[f['variedad']] += ha; prov[f['provincia']] += ha; col[f.get('color', '?')] += ha
            try:
                a = int(f.get('anio_plantacion') or 0)
                if a > 1800: edad['antes de 1980' if a < 1980 else '1980-1999' if a < 2000 else '2000-2009' if a < 2010 else '2010 en adelante'] += ha
            except ValueError: pass
        tot = sum(var.values())
        out['superficie']['ultima'] = {'anio': ult[0], 'total': round(tot),
                                       'variedades': [[k, round(v)] for k, v in sorted(var.items(), key=lambda x: -x[1])[:15]],
                                       'provincias': [[k, round(v)] for k, v in sorted(prov.items(), key=lambda x: -x[1])],
                                       'color': {k: round(v) for k, v in col.items()},
                                       'edad': {k: round(v) for k, v in edad.items()},
                                       'n_variedades': len(var)}
tramo('superficie', superficie)


# ---------- elaboración de vino y mosto (litros) ----------
def elaboracion():
    recs = paquete('agroindustria-inv---elaboracion-mostos-vino')
    ult = recurso(recs, r'Elaboraci.n de mostos y vinos 20\d\d')
    tipo, color, prov = defaultdict(float), defaultdict(float), defaultdict(float)
    for f in csv_filas(ult[2]):
        l = num(f['litros']); tipo[f['tipo_producto']] += l; prov[f['provincia']] += l
        if f['tipo_producto'] == 'vino': color[f.get('color', '?')] += l
    out['elaboracion'] = {'anio': ult[0], 'tipo': {k: round(v) for k, v in tipo.items()},
                          'color_vino': {k: round(v) for k, v in color.items()},
                          'provincias': [[k, round(v)] for k, v in sorted(prov.items(), key=lambda x: -x[1])[:8]]}
tramo('elaboracion', elaboracion)


# ---------- mercado interno (último año con CSV): envase, tipo, variedad, mes ----------
def mercado():
    recs = paquete('agroindustria-inv---actividad-vitivinicola')
    ult = recurso(recs, r'Mercado interno 20\d\d')
    env, grupo, var, mes = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
    for f in csv_filas(ult[2]):
        l = num(f['consumo'])  # litros
        env[f['envase']] += l; grupo[f['grupo']] += l; mes[int(f['mes'])] += l
        v = f.get('variedad_1') or '-'
        if v not in ('-', '', 'sin variedad'): var[v] += l
    tot = sum(env.values())
    out['mercado'] = {'anio': ult[0], 'litros': round(tot), 'meses': [round(mes[m]) for m in range(1, 13) if m in mes],
                      'envase': [[k, round(v)] for k, v in sorted(env.items(), key=lambda x: -x[1])],
                      'grupo': [[k, round(v)] for k, v in sorted(grupo.items(), key=lambda x: -x[1])],
                      'variedades': [[k, round(v)] for k, v in sorted(var.items(), key=lambda x: -x[1])[:10]]}
    try:  # litros por habitante con la población del Banco Mundial (paises_extra.json, mismo año)
        pob = dict(json.load(open(R + 'paises_extra.json', encoding='utf-8'))['wb']['pop']['ARG'])
        if str(ult[0]) in pob: out['mercado']['por_hab'] = round(tot / pob[str(ult[0])], 1)
    except Exception: pass
tramo('mercado', mercado)


# ---------- exportaciones (último CSV): destinos, variedades, precio por litro ----------
def exportaciones():
    recs = paquete('agroindustria-inv---actividad-vitivinicola')
    ult = recurso(recs, r'Exportaciones 20\d\d')
    pais, var, prod = defaultdict(lambda: [0.0, 0.0]), defaultdict(lambda: [0.0, 0.0]), defaultdict(lambda: [0.0, 0.0])
    meses = []
    for f in csv_filas(ult[2]):
        l, fob = num(f['litros_exportados']), num(f['valor_fob_miles']) * 1000
        pais[f['pais']][0] += l; pais[f['pais']][1] += fob
        if f.get('variedad_1') not in (None, '', 'sin variedad'): var[f['variedad_1']][0] += l; var[f['variedad_1']][1] += fob
        prod[f.get('modalidad_envio', '?')][0] += l; prod[f.get('modalidad_envio', '?')][1] += fob
        if f['mes'] not in meses: meses.append(f['mes'])
    lt = sum(v[0] for v in pais.values()); fb = sum(v[1] for v in pais.values())
    top = lambda d, n: [[k, round(v[0]), round(v[1]), round(v[1] / v[0], 2) if v[0] else None] for k, v in sorted(d.items(), key=lambda x: -x[1][1])[:n]]
    out['exportaciones'] = {'periodo': ult[1], 'meses': meses, 'litros': round(lt), 'fob': round(fob_total := fb),
                            'precio_litro': round(fb / lt, 2) if lt else None, 'paises': top(pais, 12), 'variedades': top(var, 8),
                            'modalidad': top(prod, 4), 'n_paises': len(pais)}
tramo('exportaciones', exportaciones)


# ---------- bodegas y viñedos por provincia ----------
def establecimientos():
    recs = paquete('agroindustria-inv---actividad-vitivinicola')
    ult = recurso(recs, r'Establecimientos')
    b, v = defaultdict(int), defaultdict(int)
    for f in csv_filas(ult[2]):
        b[f['provincia'].title()] += int(num(f['cant_bodegas'])); v[f['provincia'].title()] += int(num(f['cant_vinedos']))
    out['establecimientos'] = {'bodegas': sum(b.values()), 'vinedos': sum(v.values()),
                               'provincias': [[k, b[k], v[k]] for k in sorted(b, key=lambda k: -b[k]) if b[k] or v[k]][:12]}
tramo('establecimientos', establecimientos)

out['diag'] = diag
out['actualizado'] = time.strftime('%Y-%m-%d')
txt = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
vtxt = json.dumps({k: v for k, v in viejo.items() if k not in ('actualizado', 'diag')}, ensure_ascii=False, separators=(',', ':')) if viejo else ''
nuevo = json.dumps({k: v for k, v in out.items() if k not in ('actualizado', 'diag')}, ensure_ascii=False, separators=(',', ':'))
if nuevo != vtxt:
    open(R + 'vinos.json', 'w', encoding='utf-8').write(txt)
    print('vinos.json actualizado')
else:
    print('sin cambios')
print(json.dumps(diag, ensure_ascii=False))
