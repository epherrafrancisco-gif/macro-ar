# Verdadero o falso (/verdadero-o-falso/): arma verdadero-o-falso/datos.json con los datos de las preguntas.
# Solo lee los JSON que ya generan los otros robots del repo; no baja nada de afuera.
import json, os
from math import log10, floor

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
J = lambda f: json.load(open(R + f, encoding='utf-8'))
D, G, GH, H, U, PX = J('data.json'), J('global.json'), J('global_hist.json'), J('historia.json'), J('usa.json'), J('paises_extra.json')
S = GH['series']
r4 = lambda x: None if x is None else round(x, 4)
sig5 = lambda v: None if not v else round(v, max(0, 4 - int(floor(log10(abs(v))))))
sig = lambda v: None if not v else round(v, max(0, 3 - int(floor(log10(abs(v))))))

# país: archivo, nombre, bandera, iso3, serie fx, moneda, factor, invertida (1 = la serie es USD por unidad)
PA = [
 ('polonia','Polonia','pl','POL','fx_pln','un zloty',1,0), ('brasil','Brasil','br','BRA','fx_brl','un real',1,0),
 ('europa','Zona euro','eu','EA20','fx_eur','un euro',1,1), ('mexico','México','mx','MEX','fx_mxn','un peso mexicano',1,0),
 ('chile','Chile','cl','CHL','fx_clp','mil pesos chilenos',1000,0), ('japon','Japón','jp','JPN','fx_jpy','cien yenes',100,0),
 ('reinounido','Reino Unido','gb','GBR','fx_gbp','una libra',1,1), ('canada','Canadá','ca','CAN','fx_cad','un dólar canadiense',1,0),
 ('colombia','Colombia','co','COL','fx_cop','mil pesos colombianos',1000,0), ('turquia','Turquía','tr','TUR','fx_try','una lira',1,0),
 ('peru','Perú','pe','PER','fx_pen','un sol',1,0), ('india','India','in','IND','fx_inr','cien rupias',100,0),
 ('arabia','Arabia Saudita','sa','SAU','fx_sar','un riyal',1,0), ('suiza','Suiza','ch','CHE','fx_chf','un franco suizo',1,0),
 ('australia','Australia','au','AUS','fx_aud','un dólar australiano',1,1), ('corea','Corea del Sur','kr','KOR','fx_krw','mil wones',1000,0),
 ('sudafrica','Sudáfrica','za','ZAF','fx_zar','un rand',1,0), ('zelanda','Nueva Zelanda','nz','NZL','fx_nzd','un dólar neozelandés',1,1),
 ('indonesia','Indonesia','id','IDN','fx_idr','mil rupias',1000,0), ('noruega','Noruega','no','NOR','fx_nok','una corona noruega',1,0),
 ('suecia','Suecia','se','SWE','fx_sek','una corona sueca',1,0), ('tailandia','Tailandia','th','THA','fx_thb','un baht',1,0),
 ('malasia','Malasia','my','MYS','fx_myr','un ringgit',1,0), ('filipinas','Filipinas','ph','PHL','fx_php','un peso filipino',1,0),
 ('islandia','Islandia','is','ISL','fx_isk','cien coronas islandesas',100,0), ('hungria','Hungría','hu','HUN','fx_huf','cien forintos',100,0),
 ('hongkong','Hong Kong','hk','HKG','fx_hkd','un dólar de Hong Kong',1,0), ('chequia','Chequia','cz','CZE','fx_czk','una corona checa',1,0),
 ('dinamarca','Dinamarca','dk','DNK','fx_dkk','una corona danesa',1,0), ('rumania','Rumania','ro','ROU','fx_ron','un leu',1,0),
 ('israel','Israel','il','ISR','fx_ils','un séquel',1,0), ('serbia','Serbia','rs','SRB','fx_rsd','cien dinares',100,0),
 ('china','China','cn','CHN','fx_cny','un yuan',1,0), ('rusia','Rusia','ru','RUS','fx_rub','cien rublos',100,0),
 ('espana','España','es','ESP',None,None,1,0), ('macedonia','Macedonia del Norte','mk','MKD','fx_mkd','cien denares',100,0),
 ('singapur','Singapur','sg','SGP','fx_sgd','un dólar de Singapur',1,0), ('marruecos','Marruecos','ma','MAR','fx_mad','un dirham',1,0),
]
HOY = D['actualizado'][:10]


def meses_atras(m):
    y, mo = map(int, m[:7].split('-')); hy, hm = map(int, HOY[:7].split('-'))
    return (hy - y) * 12 + (hm - mo)


def seguro(fn, *a):
    try:
        return fn(*a)
    except Exception as e:  # un país roto no tira abajo todo
        print('  aviso:', a[0] if a else '', e)
        return None


def armar_pais(k, n, fl, iso, fx, mon, fac, inv):
    d = J(k + '.json')
    tasa = d.get('tasa') or d.get('selic') or d.get('bce')
    infl, desemp = d.get('infl'), d.get('desemp')
    if k == 'brasil': infl = d.get('ipca_12')
    if k == 'europa':
        infl = (d.get('infl') or {}).get('EA'); desemp = (d.get('desemp') or {}).get('EA')
    o = {'n': n, 'fl': fl, 'iso': iso, 'k': k}
    if isinstance(tasa, list) and tasa: o['tasa'] = tasa[-1][1]
    if isinstance(infl, list) and infl:
        f, v = infl[-1]
        if meses_atras(f) <= 5: o['infl'] = [f[:7], r4(v)]
    if isinstance(desemp, list) and desemp:
        f, v = desemp[-1]
        if meses_atras(f) <= 6: o['desemp'] = [f[:7], r4(v)]
    if fx and fx in S and S[fx]:
        ser = S[fx][-380:]
        ser = ser[::-2][::-1]  # un día sí y otro no (alcanza para el gráfico), siempre con el último
        o['fx'] = [[a, sig5(b)] for a, b in ser]; o['mon'] = mon; o['fac'] = fac; o['inv'] = inv
    return o


paises = {}
for row in PA:
    o = seguro(armar_pais, *row)
    if o: paises[row[0]] = o
fed = U.get('fed') or {}
paises['eeuu'] = {'n': 'Estados Unidos', 'fl': 'us', 'iso': 'USA', 'k': 'eeuu', 'tasa': fed.get('actual') if isinstance(fed, dict) else None}

wb = PX.get('wb', {})
ppa = {iso: [[int(a), round(b)] for a, b in v if b] for iso, v in wb.get('ppa', {}).items()}
crec = {iso: [[int(a), r4(b)] for a, b in v if b is not None] for iso, v in wb.get('crec', {}).items()}
bm = PX.get('bigmac', {})
bigmac = {iso: {'usd': v['usd'], 'local': v['local'], 'mon': v['moneda']} for iso, v in bm.get('paises', {}).items()}
bm_fecha = bm.get('fecha') or bm.get('f') or ''
bolsas = {k: {'idx': v.get('idx'), 'iso': v.get('iso'), 'm': v.get('m'), 'vm': v.get('vm'), 'va': v.get('va'), 'v12': v.get('v12')}
          for k, v in G.get('bolsas', {}).items() if v.get('va') is not None and v.get('m') and meses_atras(v['m']) <= 3}
bonos = {k: {'n': v['n'], 'v': v['v'], 'prev': v.get('prev'), 't': v['t'][:10], 'mens': bool(v.get('mensual'))}
         for k, v in G.get('bonos', {}).items() if v.get('v') is not None}
com = {}
for c in G.get('commodities', []):
    k = c['k']; ser = S.get(k, [])
    com[k] = {'n': c['n'], 'v': c['v'], 'u': c.get('u', ''), 'f': c['f'], 'mens': bool(c.get('mensual')),
              's': [[a, r4(b)] for a, b in ser[-260:]]}

# Argentina
dia = D['diario']


def serie(campo):
    out = []
    for r in dia:
        x = r.get(campo)
        if isinstance(x, dict): x = x.get('v')
        if x is not None: out.append([r['fecha'], x])
    return out


arg = {k: serie(k) for k in ['oficial', 'blue', 'mep', 'ccl', 'mayorista', 'cripto', 'tarjeta', 'riesgo', 'merval']}
arg['hist'] = [[r['mes'], r.get('ofi'), r.get('blue'), r.get('mep'), r.get('ccl'), r.get('cer')] for r in D['historico']]
arg['infl'] = [[r['mes'], r['infl'], r.get('inflYoY')] for r in D['mensual'] if r.get('infl') is not None and r.get('inflYoY') is not None]
mx = S.get('ars_mayorista') or [[a, b] for a, b in arg['mayorista']]
arg['fx'] = [[a, r4(b)] for a, b in arg['mayorista'][-400:]]

# Acciones y CEDEARs: solo las que se operan seguido y sin saltos raros (un precio roto da un "si ponías…" falso)
F = H['fechas']; pos = {f: i for i, f in enumerate(F)}; n = len(F)
acc, fuera = {}, {'sin_nombre': 0, 'poco_operada': 0, 'saltos': 0, 'poco_conocida': 0}
# solo empresas conocidas (pedido del dueño 01/11/2026); la misma lista que FAMOSAS en verdadero-o-falso/juego.js
FAMOSAS = set(('GGAL YPFD PAMP BMA TXAR ALUA MELI AAPL MSFT GOOGL AMZN TSLA NVDA META KO DIS NFLX MCD WMT NKE SPY BABA PFE XOM SBUX PEP MERVAL').split())
for tk, inf in H['info'].items():
    if inf['t'] == 'bon': continue
    if tk not in FAMOSAS: fuera['poco_conocida'] += 1; continue
    if not inf.get('n'): fuera['sin_nombre'] += 1; continue
    p = R + 'historia/%s.json' % tk
    if not os.path.exists(p): continue
    a = json.load(open(p)); c = [None] * n
    for d_, v in zip(a['d'], a['c']):
        if d_ in pos and v: c[pos[d_]] = sig(v)
    ult60 = c[-60:]
    if sum(1 for v in ult60 if v) < 0.85 * len(ult60) or not any(c[-3:]) or sum(1 for v in c if v) < 150:   # el último día puede faltar si la corrida de historia se cortó
        fuera['poco_operada'] += 1; continue
    prev, raro = None, False
    for v in c:
        if v and prev and (v / prev > 1.45 or v / prev < 0.6): raro = True; break
        if v: prev = v
    if raro: fuera['saltos'] += 1; continue
    acc[tk] = {'n': inf['n'], 't': inf['t'], 'c': c}
his = {'f': F, 'mep': [sig(x) if x else None for x in H['mep']], 'acc': acc}

cal, nots = [], []  # agenda y noticias se sacaron de los reels (pedido del dueño 01/11/2026: poco llamativos)

pack = {'hoy': HOY, 'gen': D['actualizado'], 'arg': arg, 'paises': paises, 'ppa': ppa, 'crec': crec, 'bigmac': bigmac, 'bmf': bm_fecha,
        'bolsas': bolsas, 'bonos': bonos, 'com': com, 'his': his, 'cal': cal, 'nots': nots}
os.makedirs(R + 'verdadero-o-falso', exist_ok=True)
txt = json.dumps(pack, ensure_ascii=False, separators=(',', ':'))
viejo = open(R + 'verdadero-o-falso/datos.json', encoding='utf-8').read() if os.path.exists(R + 'verdadero-o-falso/datos.json') else ''
if txt != viejo:
    open(R + 'verdadero-o-falso/datos.json', 'w', encoding='utf-8').write(txt)
print('verdadero-o-falso/datos.json', len(txt.encode()) // 1024, 'KB · acciones', len(acc), 'afuera', fuera,
      '· países con inflación', sum('infl' in o for o in paises.values()), '· bolsas', len(bolsas), '· commodities', len(com))

# Miniaturas de la entrada en Inicio (live/portada.json, chiquito: la portada no baja los datos enteros)
def spark(vals, n=10):
    vals = [v for v in vals if v]
    if len(vals) < 2: return ''
    paso = max(1, len(vals) // n); pts = vals[::paso][-n:] + ([vals[-1]] if vals[::paso][-1] != vals[-1] else [])
    lo, hi = min(pts), max(pts); rg = (hi - lo) or 1
    return ' '.join(('M' if i == 0 else 'L') + '%d %d' % (round(i * 90 / (len(pts) - 1)), round(32 - (v - lo) / rg * 28)) for i, v in enumerate(pts))

fmt = lambda v, d=0: ('{:,.%df}' % d).format(v).replace(',', 'X').replace('.', ',').replace('X', '.')
th = []  # afirmaciones de verdadero o falso para la franja de Inicio (la página les pone ¿ ?)
nom = {o['iso']: o['n'] for o in paises.values()}
try:
    ok = [o for o in paises.values() if 'infl' in o]; o = max(ok, key=lambda o: o['infl'][1])
    th.append({'t': '%s tiene más inflación que Argentina' % o['n']})
    o = max([o for o in ok if o['infl'][1] > 0], key=lambda o: arg['infl'][-1][2] / o['infl'][1])
    k2 = arg['infl'][-1][2] / o['infl'][1]
    th.append({'t': 'La inflación de Argentina es más de %d veces la de %s' % (int(k2 // 5 * 5) if k2 >= 10 else int(k2), o['n'])})
except Exception as e: print('  aviso portada infl', e)
try:
    ar = dict(ppa['ARG'])
    for iso in ['CHL', 'POL', 'KOR', 'ESP']:
        s_ = ppa.get(iso)
        if s_ and ar.get(s_[0][0]) and ar[s_[0][0]] > s_[0][1]:
            th.append({'t': 'En %d Argentina era más rica que %s' % (s_[0][0], nom.get(iso, iso))}); break
except Exception as e: print('  aviso portada ppa', e)
try:
    a_ = bigmac.get('ARG'); iso = max((i for i in bigmac if i in nom), key=lambda i: bigmac[i]['usd'])
    if a_: th.append({'t': 'Un Big Mac es más caro en %s que en Argentina' % nom[iso]})
except Exception as e: print('  aviso portada bm', e)
try:
    i0 = max(0, n - 1 - 250); best = None
    for tk, a in acc.items():
        c0, c1, m0, m1 = a['c'][i0], a['c'][-1], his['mep'][i0], his['mep'][-1]
        if a['t'] in ('acc', 'ced') and c0 and c1 and m0 and m1:
            r = (c1 / m1) / (c0 / m0)
            if best is None or r > best[1]: best = (tk, r)
    if best:
        u = int(1000 * best[1] // 500 * 500)
        th.append({'t': 'Si ponías US$ 1.000 en %s hace un año, hoy tendrías más de US$ %s' % (acc[best[0]]['n'], fmt(u))})
except Exception as e: print('  aviso portada sim', e)
txt = json.dumps({'gen': D['actualizado'], 'th': th}, ensure_ascii=False, separators=(',', ':'))
viejo = open(R + 'verdadero-o-falso/portada.json', encoding='utf-8').read() if os.path.exists(R + 'verdadero-o-falso/portada.json') else ''
if txt != viejo: open(R + 'verdadero-o-falso/portada.json', 'w', encoding='utf-8').write(txt)
print('verdadero-o-falso/portada.json', len(th), 'miniaturas')
