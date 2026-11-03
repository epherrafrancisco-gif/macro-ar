"""Insumos químicos: precio al que entra cada producto al país → insumos.json.

Fuente: INDEC, base de comercio exterior de bienes (comex.indec.gob.ar, archivos públicos imports_AAAA_M.zip; columnas
Año;mes;NCM;Porg;Pnet(kg);FOB(USD);Flete(USD);Seguro(USD);CIF(USD)). Precio = valor total / kilos del mes (promedio
ponderado de todas las operaciones), en dólares por tonelada, sin aranceles ni impuestos. Nombres oficiales de cada NCM y
de cada país: API pública del mismo sitio (comexbe.indec.gob.ar/public-api/search). Un producto cuyo código no figure en el
nomenclador se descarta (diag). Años cerrados se guardan resumidos en insumos_cache/AAAA.json (VERSION: subirla si cambia
la lista de productos o la forma de contar, y se rehacen).
"""
import csv, io, json, os, sys, time, urllib.parse, urllib.request, zipfile
from datetime import date, datetime, timezone

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
CACHE = R + 'insumos_cache/'
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
ZIP = "https://comex.indec.gob.ar/files/zips/imports_{}_M.zip"
API = "https://comexbe.indec.gob.ar/public-api/search/"
DESDE = 2019
VERSION = 1

# clave, nombre en criollo, grupo, códigos NCM (se suman)
PROD = [
    ('soda_s', 'Soda cáustica en escamas', 'limpieza', ['28151100']),
    ('soda_l', 'Soda cáustica líquida', 'limpieza', ['28151200']),
    ('labsa', 'Ácido sulfónico (LABSA)', 'limpieza', ['34023100']),
    ('anion', 'Lauril éter sulfato y otros aniónicos', 'limpieza', ['34023990']),
    ('noion', 'Tensioactivos no iónicos', 'limpieza', ['34024200']),
    ('hipo_na', 'Hipoclorito de sodio', 'limpieza', ['28289011']),
    ('hipo_ca', 'Hipoclorito de calcio (cloro granulado)', 'limpieza', ['28281000']),
    ('carbonato', 'Carbonato de sodio', 'limpieza', ['28362010']),
    ('sulfurico', 'Ácido sulfúrico', 'limpieza', ['28070010']),
    ('citrico', 'Ácido cítrico', 'limpieza', ['29181400']),
    ('glicerina', 'Glicerina', 'limpieza', ['29054500']),
    ('formol', 'Formol (formaldehído)', 'conservantes', ['29121100']),
    ('benzoato', 'Benzoato de sodio', 'conservantes', ['29163121']),
    ('sorbato', 'Sorbato de potasio', 'conservantes', ['29161911']),
    ('pebd', 'Polietileno de baja densidad', 'plasticos', ['39011030', '39011020']),
    ('pebdl', 'Polietileno lineal de baja densidad', 'plasticos', ['39014000']),
    ('pead', 'Polietileno de alta densidad', 'plasticos', ['39012029', '39012019']),
    ('pp', 'Polipropileno', 'plasticos', ['39021020', '39021010']),
    ('pet', 'PET (botellas y envases)', 'plasticos', ['39076100', '39076900']),
]
diag = {'errores': [], 'sin_codigo': [], 'anios': {}}


def get(url, accept='*/*', intentos=3, timeout=240):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if '404' in str(e) or i == intentos - 1: raise
            time.sleep(5 * (i + 1))


def nombres_ncm():
    """Descripción oficial de cada código (y se descartan los que no existen)."""
    out = {}
    for _, _, _, cods in PROD:
        for c in cods:
            try:
                j = json.loads(get(API + 'products?' + urllib.parse.urlencode({'i18n': 'es', 'term': c, 'year': date.today().year}), 'application/json'))
                d = next((x for x in j if str(x.get('code')) == c), None)
                if d: out[c] = (d.get('description') or {}).get('es', '').strip()
                else: diag['sin_codigo'].append(c)
            except Exception as e:  # noqa: BLE001
                diag['errores'].append(f'nomenclador {c}: {e}')
    return out


def paises():
    out = {}
    for t in 'aeiou':
        try:
            for c in json.loads(get(API + 'countries?i18n=es&term=' + t, 'application/json')):
                out[str(c['_id'])] = (c.get('name') or '').strip()
        except Exception as e:  # noqa: BLE001
            diag['errores'].append(f'países: {e}')
    return out


def anio(y, codigos):
    """{codigo: {mes: [kg, fob, cif], 'p': {pais: {mes: [kg, cif]}}}} de un año."""
    z = zipfile.ZipFile(io.BytesIO(get(ZIP.format(y))))
    nom = next(n for n in z.namelist() if n.lower().startswith('impom') and n.lower().endswith('.csv'))
    txt = z.read(nom).decode('latin-1')
    f = lambda s: float((s or '0').replace(',', '.')) if s not in ('', 's') else 0.0
    out, filas = {}, 0
    for r in csv.reader(io.StringIO(txt), delimiter=';'):
        if len(r) < 9 or r[2] not in codigos: continue
        filas += 1
        m = f'{r[0]}-{int(r[1]):02d}'
        kg, fob, cif = f(r[4]), f(r[5]), f(r[8])
        d = out.setdefault(r[2], {'m': {}, 'p': {}})
        a = d['m'].setdefault(m, [0, 0, 0]); a[0] += kg; a[1] += fob; a[2] += cif
        b = d['p'].setdefault(r[3], {}).setdefault(m, [0, 0]); b[0] += kg; b[1] += cif
    diag['anios'][y] = filas
    return out


def main():
    viejo = {}
    try: viejo = json.load(open(R + 'insumos.json', encoding='utf-8'))
    except Exception: pass
    desc = nombres_ncm()
    if not desc:
        print('sin nomenclador: queda lo anterior'); return
    codigos = {c for _, _, _, cs in PROD for c in cs if c in desc}
    os.makedirs(CACHE, exist_ok=True)
    hoy = date.today().year
    datos = {}
    for y in range(DESDE, hoy + 1):
        fc = f'{CACHE}{y}.json'
        if y < hoy - 0 and os.path.exists(fc):
            c = json.load(open(fc, encoding='utf-8'))
            if c.get('v') == VERSION and y < hoy - 1:  # el año anterior se rehace (el INDEC corrige)
                datos[y] = c['d']; continue
        try:
            datos[y] = anio(y, codigos)
            if y < hoy:
                json.dump({'v': VERSION, 'd': datos[y]}, open(fc, 'w', encoding='utf-8'), separators=(',', ':'))
        except Exception as e:  # noqa: BLE001
            diag['errores'].append(f'{y}: {e}')
            if os.path.exists(fc): datos[y] = json.load(open(fc, encoding='utf-8'))['d']
    if not datos.get(hoy) and not datos.get(hoy - 1):
        print('sin datos recientes: queda lo anterior'); return
    nompais = paises() or viejo.get('paises', {})
    prods, usados = [], set()
    for k, n, g, cods in PROD:
        cs = [c for c in cods if c in desc]
        if not cs: continue
        mes, porig = {}, {}
        for y, d in datos.items():
            for c in cs:
                for m, v in (d.get(c) or {}).get('m', {}).items():
                    a = mes.setdefault(m, [0, 0, 0]); a[0] += v[0]; a[1] += v[1]; a[2] += v[2]
                for p, ms in (d.get(c) or {}).get('p', {}).items():
                    for m, v in ms.items():
                        a = porig.setdefault(p, {}).setdefault(m, [0, 0]); a[0] += v[0]; a[1] += v[1]
        if not mes: continue
        serie = [[m, round(v[0]), round(v[1]), round(v[2])] for m, v in sorted(mes.items())]
        ult = serie[-1][0]
        y12 = sorted(mes)[-12:]
        orig = []
        for p, ms in porig.items():
            kg = sum(ms.get(m, [0, 0])[0] for m in y12); cif = sum(ms.get(m, [0, 0])[1] for m in y12)
            if kg > 0: orig.append([p, round(kg), round(cif)])
        orig.sort(key=lambda x: -x[1])
        usados.update(p for p, _, _ in orig[:12])
        prods.append({'k': k, 'n': n, 'g': g, 'ncm': [[c, desc[c]] for c in cs], 'serie': serie, 'ult': ult,
                      'orig': orig[:12], 'orig_n': len(orig)})
    out = {'fuente': 'INDEC, base de comercio exterior de bienes (importaciones)', 'productos': prods,
           'paises': {p: nompais.get(p, p) for p in sorted(usados)},
           'ultimo_mes': max(p['ult'] for p in prods), 'diag': diag,
           'actualizado': datetime.now(timezone.utc).isoformat(timespec='minutes')}
    json.dump(out, open(R + 'insumos.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(json.dumps(diag, ensure_ascii=False))
    for p in prods:
        s = p['serie'][-1]
        print(p['k'], p['ult'], f"{s[1]/1000:.0f} t", f"US$ {s[3]/s[1]*1000 if s[1] else 0:.0f}/t", [nompais.get(o[0], o[0]) for o in p['orig'][:3]])


if __name__ == '__main__':
    main()
