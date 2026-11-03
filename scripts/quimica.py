"""Industria química: arma quimica.json solo con fuentes abiertas.

- INDEC, vía la API de Series de Tiempo de datos.gob.ar (uso libre citando la fuente):
  IPI manufacturero (dataset 453: divisiones y subclases de química y de caucho y plástico, más el nivel general),
  producción física (dataset 41.3: urea, caucho sintético, detergentes, jabones, pinturas) y utilización de la capacidad
  instalada del bloque químico (dataset 31.3).
- Banco Mundial, "Pink Sheet" (CC BY 4.0): fertilizantes (urea, DAP, TSP, cloruro de potasio, roca fosfórica), gas natural
  y caucho, precio promedio de cada mes en dólares.
- Eurostat (uso libre citando la fuente): producción de la industria química (NACE C20) y farmacéutica (C21) de Europa.

La API de datos.gob.ar devuelve meses vacíos al azar: se pide cada serie sola, se reintenta y se junta con lo guardado.
Una serie cuyo último dato tiene más de 7 meses no se publica (nunca mostrar datos viejos como actuales).
"""
import io, json, os, re, sys, time
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import abiertas  # noqa: E402

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
API = "https://apis.datos.gob.ar/series/api/series/?ids={}&start_date=2014-01-01&limit=1000&format=json"

IPI = {  # índice 2004 = 100 (INDEC); "general" es el nivel general de la industria, para comparar
    'general': '453.1_SERIE_ORIGNAL_0_0_14_46',
    'quimica': '453.2_SUSTANCIASCOS_0_0_29_82',
    'basicos': '453.2_PRODUCTOS_COS_0_0_26_42',
    'agro': '453.2_AGROQUIMICCOS_0_0_12_6',
    'farma': '453.2_PRODUCTOS_COS_0_0_23_90',
    'deterg': '453.2_DETERGENTELES_0_0_40_99',
    'pinturas': '453.2_PINTURASRAS_0_0_8_67',
    'gases': '453.2_GASES_INDULES_0_0_18_56',
    'otrosq': '453.2_OTROS_PRODCOS_0_0_24_57',
    'cyp': '453.2_PRODUCTOS_ICO_0_0_25_26',
    'mpp': '453.2_MATERIAS_PICO_0_0_44_25',
    'plast': '453.2_MANUFACTURICO_0_0_21_9',
    'caucho': '453.2_OTROS_PRODCHO_0_0_22_35',
}
FIS = {  # producción física mensual
    'urea': '41.3_U_0_A_4',          # miles de toneladas
    'caucho_s': '41.3_CS_0_A_16',    # toneladas
    'deterg': '41.3_DLIL_0_A_42',    # toneladas
    'jabones': '41.3_JTL_0_A_21',    # toneladas
    'pint_c': '41.3_PP_0_A_24',      # toneladas
    'pint_o': '41.3_PPU_0_A_22',     # toneladas
}
UCI = {'quimica': '31.3_USPQ_2004_M_34', 'general': '31.3_UNG_2004_M_18', 'caucho': '31.3_UCP_2004_M_24'}
PINK = {'urea': 'Urea', 'dap': 'DAP', 'tsp': 'TSP', 'kcl': 'Potassium chloride', 'fosfato': 'Phosphate rock',
        'gas_us': 'Natural gas, US', 'gas_eu': 'Natural gas, Europe', 'caucho': 'Rubber, TSR20'}
EU_GEO = ['EU27_2020', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'PL']
diag = {'errores': [], 'series_vacias': []}

viejo = {}
try: viejo = json.load(open(R + 'quimica.json', encoding='utf-8'))
except Exception: pass


def corte_ok(pts, meses=7):
    if not pts: return False
    y, m = map(int, pts[-1][0][:7].split('-'))
    hoy = date.today()
    return (hoy.year - y) * 12 + hoy.month - m <= meses


def serie(sid, prev):
    """[[AAAA-MM, valor]] de una serie de la API, juntando con lo guardado (la API a veces devuelve meses vacíos)."""
    pts = {}
    for i in range(4):
        try:
            d = json.loads(abiertas.get(API.format(sid), "application/json", tries=2, timeout=90))
            for f, v in d.get('data') or []:
                if v is not None: pts[f[:7]] = round(float(v), 3)
            break
        except Exception as e:  # noqa: BLE001
            if i == 3: diag['errores'].append(f'{sid}: {e}')
            time.sleep(5 * (i + 1))
    for f, v in prev or []:
        pts.setdefault(f, v)
    return sorted([k, v] for k, v in pts.items())


def grupo(nombre, ids):
    prev = (viejo.get(nombre) or {})
    out = {}
    for k, sid in ids.items():
        p = serie(sid, prev.get(k))
        if corte_ok(p): out[k] = p
        else: diag['series_vacias'].append(f'{nombre}.{k} ({sid}): {p[-1][0] if p else "sin datos"}')
    return out


def pink():
    import openpyxl
    pag = abiertas.get("https://www.worldbank.org/en/research/commodity-markets").decode('utf-8', 'replace')
    m = re.search(r"https://thedocs\.worldbank\.org/[^\"'\s]+CMO-Historical-Data-Monthly\.xlsx", pag)
    if not m: raise ValueError('no encontré la planilla mensual')
    wb = openpyxl.load_workbook(io.BytesIO(abiertas.get(m.group(0))), read_only=True, data_only=True)
    filas = list(wb['Monthly Prices'].iter_rows(values_only=True))
    ci = next(i for i, r in enumerate(filas) if r and any(str(c or '').strip() == 'DAP' for c in r))
    cab = [re.sub(r'\s*\*+$', '', str(c or '').strip()) for c in filas[ci]]
    cols = {k: cab.index(n) for k, n in PINK.items() if n in cab}
    out = {}
    for r in filas[ci + 1:]:
        mm = re.fullmatch(r'(\d{4})M(\d{2})', str(r[0] or '').strip())
        if not mm or int(mm.group(1)) < 2014: continue
        for k, i in cols.items():
            if isinstance(r[i], (int, float)):
                out.setdefault(k, []).append([f'{mm.group(1)}-{mm.group(2)}', round(float(r[i]), 2)])
    return {k: v for k, v in out.items() if corte_ok(v, 5)}


def eurostat(nace):
    q = '&'.join([f'geo={g}' for g in EU_GEO] + [f'nace_r2={nace}', 's_adj=SCA', 'unit=I21', 'indic_bt=PRD', 'sinceTimePeriod=2016-01'])
    j = json.loads(abiertas.get(f'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_inpr_m?{q}', 'application/json'))
    ids, sizes, vals = j['id'], j['size'], j.get('value') or {}
    idx = {d: {i: k for k, i in j['dimension'][d]['category']['index'].items()} for d in ids}
    out = {}
    for flat, v in vals.items():
        n, co = int(flat), {}
        for d, s in zip(reversed(ids), reversed(sizes)):
            co[d] = idx[d][n % s]; n //= s
        out.setdefault(co['geo'], []).append([co['time'], round(float(v), 1)])
    return {g: sorted(p) for g, p in out.items() if corte_ok(sorted(p), 5)}


def tramo(nombre, fn, out, clave):
    try:
        r = fn()
        if not r: raise ValueError('vacío')
        out[clave] = r
    except Exception as e:  # noqa: BLE001
        diag['errores'].append(f'{nombre}: {e}')
        if viejo.get(clave): out[clave] = {k: v for k, v in viejo[clave].items() if corte_ok(v)}


out = {'fuente': 'INDEC vía datos.gob.ar; Banco Mundial (Pink Sheet, CC BY 4.0); Eurostat'}
out['ipi'] = grupo('ipi', IPI)
out['fis'] = grupo('fis', FIS)
out['uci'] = grupo('uci', UCI)
mundo = {}
tramo('Banco Mundial', pink, mundo, 'precios')
tramo('Eurostat C20', lambda: eurostat('C20'), mundo, 'eu_quim')
tramo('Eurostat C21', lambda: eurostat('C21'), mundo, 'eu_farma')
out['mundo'] = mundo
out['diag'] = diag
out['actualizado'] = datetime.now(timezone.utc).isoformat(timespec='minutes')
if not out['ipi'].get('quimica') and viejo.get('ipi'):
    print('sin IPI: queda lo anterior'); sys.exit(0)
json.dump(out, open(R + 'quimica.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps(diag, ensure_ascii=False, indent=1))
print({g: {k: (v[-1] if v else None) for k, v in d.items()} for g, d in [('ipi', out['ipi']), ('fis', out['fis']), ('uci', out['uci'])]})
print({k: {g: p[-1] for g, p in v.items()} for k, v in mundo.items()})
