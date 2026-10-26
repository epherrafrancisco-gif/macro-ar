"""Genera una página estática por indicador (para que Google las encuentre) + /indicadores/, sitemap.xml y robots.txt.

Cada página tiene el dato escrito como texto, un gráfico SVG, una tabla con los últimos valores, qué es el indicador
y un botón a la sección del tablero. Sale solo de los JSON que ya arman los otros robots: no pide nada a internet.
Solo reescribe un archivo si cambió su contenido, así no hay commits vacíos.
"""
import json
import html
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://pulsomacro.com.ar"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def cargar(nombre):
    try:
        return json.loads((ROOT / nombre).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def nf(v, dec=2):
    s = f"{abs(v):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if v < 0 and round(abs(v), dec) != 0 else "") + s


def sg(v, dec=2):
    return ("+" if round(v, dec) > 0 else "") + nf(v, dec)


def fecha_larga(iso):
    d = date.fromisoformat(iso[:10])
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_corta(iso):
    d = date.fromisoformat(iso[:10])
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def mes_txt(ym):
    return f"{MESES[int(ym[5:7]) - 1]} de {ym[:4]}"


def esc(s):
    return html.escape(str(s), quote=True)


# ---------- series ----------
D = cargar("data.json")
DIARIO = D.get("diario", [])
MENSUAL = D.get("mensual", [])


def diaria(clave, sub=None):
    out = []
    for x in DIARIO:
        v = x.get(clave)
        if isinstance(v, dict):
            v = v.get(sub or "v")
        if v is not None:
            out.append((x["fecha"], float(v)))
    return out


def mensual(clave):
    return [(m["mes"], float(m[clave])) for m in MENSUAL if m.get(clave) is not None]


def cruzar(a, b, f):
    mb = dict(b)
    return [(d, f(v, mb[d])) for d, v in a if d in mb and mb[d]]


def en(serie, dias, desde=None):
    """Valor de la serie más cercano (hacia atrás) a `dias` antes del último."""
    if not serie:
        return None
    obj = (date.fromisoformat((desde or serie[-1][0])[:10]) - timedelta(days=dias)).isoformat()
    previos = [p for p in serie if p[0] <= obj]
    return previos[-1] if previos else None


# ---------- gráfico ----------
def svg_linea(serie, color, fmt, mensual_=False):
    if len(serie) < 2:
        return ""
    W, H, L, R, T, B = 600, 280, 60, 14, 14, 32
    vals = [v for _, v in serie]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.08 or abs(hi) * 0.05 or 1
    lo, hi = lo - pad, hi + pad
    x = lambda i: L + i * (W - L - R) / (len(serie) - 1)
    y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B)
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(serie))
    area = f"M{x(0):.1f},{H - B} L" + " L".join(f"{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(serie)) + f" L{x(len(serie) - 1):.1f},{H - B} Z"
    grid = ""
    for k in range(4):
        v = lo + (hi - lo) * (k + .5) / 4
        grid += f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#1f2831"/><text x="{L - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{esc(fmt(v))}</text>'
    # marcas de meses
    marcas, visto = "", set()
    for i, (d, _) in enumerate(serie):
        k = d[:4] if mensual_ and len(serie) > 30 else d[:7]
        if k in visto:
            continue
        visto.add(k)
        if mensual_ and len(serie) > 30 and d[5:7] != "01":
            continue
        lab = d[:4] if (mensual_ and len(serie) > 30) else MESES[int(d[5:7]) - 1][:3].upper()
        if x(i) < W - R - 20:
            marcas += f'<text x="{x(i):.1f}" y="{H - 10}">{lab}</text>'
    if len(visto) > 14:  # demasiadas: una cada dos
        marcas = "".join(m for j, m in enumerate(re.findall(r"<text.*?</text>", marcas)) if j % 2 == 0)
    ult = serie[-1][1]
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Gráfico"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity=".28"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
            f'<g class="ax">{grid}{marcas}</g><path d="{area}" fill="url(#g)"/><polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round"/>'
            f'<circle cx="{x(len(serie) - 1):.1f}" cy="{y(ult):.1f}" r="4.5" fill="{color}"/></svg>')


# ---------- plantilla ----------
CSS = """:root{color-scheme:dark;--bg:#0e1319;--sf:#161d25;--ink:#e6edf3;--ink2:#a9b6c3;--mu:#7c8a98;--ln:#28323d;--ac:#6aa8d8;--up:#2fb383;--dn:#e0663a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 "Instrument Sans",system-ui,sans-serif}
a{color:var(--ac)}.w{max-width:860px;margin:0 auto;padding:22px 16px 40px}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;border-bottom:1px solid var(--ln);padding-bottom:14px}
.lg{font-weight:700;font-size:22px;letter-spacing:-.02em;color:var(--ink);text-decoration:none}.lg span{font-family:"JetBrains Mono",monospace;font-weight:500;color:var(--ac);font-size:.8em;margin-left:4px}
.crumb{font-size:13px;color:var(--mu);margin:18px 0 4px}.crumb a{color:var(--mu)}
h1{font-size:clamp(28px,6vw,40px);line-height:1.1;letter-spacing:-.02em;margin:6px 0 10px}
.big{font-family:"JetBrains Mono",monospace;font-size:clamp(40px,10vw,60px);font-weight:600;line-height:1}.big small{font-size:.4em;color:var(--ink2);margin-left:8px;font-weight:500}
.cuando{color:var(--mu);font-size:14px;margin:8px 0 18px}
.lead{font-size:18px;color:var(--ink2)}.lead b{color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.kpi{background:var(--sf);border:1px solid var(--ln);border-radius:10px;padding:10px 12px}.kpi span{display:block;font-size:13px;color:var(--mu)}.kpi b{font-family:"JetBrains Mono",monospace;font-size:19px;font-weight:500}
.card{background:var(--sf);border:1px solid var(--ln);border-radius:12px;padding:14px;margin:18px 0}
.card h2{font-size:17px;margin:0 0 10px}
svg{width:100%;height:auto;display:block}.ax text{fill:var(--mu);font:13px "JetBrains Mono",monospace}
table{width:100%;border-collapse:collapse;font-size:15px}td,th{padding:7px 4px;border-bottom:1px solid var(--ln);text-align:right}td:first-child,th:first-child{text-align:left}th{color:var(--mu);font-weight:500;font-size:13px}
td{font-family:"JetBrains Mono",monospace;font-size:14px}td:first-child{font-family:inherit}
.up{color:var(--up)}.dn{color:var(--dn)}
.btn{display:inline-block;background:var(--ac);color:#0e1319;font-weight:700;padding:12px 18px;border-radius:10px;text-decoration:none;margin:6px 0}
.prose p{color:var(--ink2)}.prose h2{font-size:20px;margin:26px 0 6px}
.rel{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}.rel a{border:1px solid var(--ln);border-radius:999px;padding:6px 12px;font-size:14px;text-decoration:none;color:var(--ink2)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}.grid a{display:block;background:var(--sf);border:1px solid var(--ln);border-radius:10px;padding:12px;text-decoration:none;color:var(--ink)}
.grid a span{display:block;font-size:13px;color:var(--mu)}.grid a b{font-family:"JetBrains Mono",monospace;font-weight:500}
footer{border-top:1px solid var(--ln);margin-top:30px;padding-top:14px;font-size:13px;color:var(--mu)}"""

ICON = "/icons/anillo.svg"

PAGINAS = []   # (slug, nombre corto, valor corto, grupo)


def pagina(slug, titulo_seo, desc, cuerpo, crumb, extra_head=""):
    url = f"{SITE}/{slug}/" if slug else f"{SITE}/indicadores/"
    return f"""<!doctype html>
<html lang="es-AR"><head><meta charset="utf-8"><meta name="color-scheme" content="dark"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(titulo_seo)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}"><link rel="icon" href="{ICON}">
<meta property="og:title" content="{esc(titulo_seo)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article"><meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/preview.png?v=6">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600;700&family=JetBrains+Mono:wght@500;600&display=swap">
<style>{CSS}</style>{extra_head}
<script data-goatcounter="https://macroar.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head><body><div class="w">
<header><a class="lg" href="/">Pulso<span>Macro</span></a><a href="/indicadores/">Todos los indicadores</a></header>
<div class="crumb"><a href="/">Inicio</a> › {crumb}</div>
{cuerpo}
<footer>Pulso Macro es un tablero gratuito de la economía argentina y del mundo, que se actualiza solo cada día hábil.
Los datos son informativos y no constituyen una recomendación de inversión. <a href="/#sobre">Sobre Pulso Macro</a></footer>
</div></body></html>
"""


def kpis(items):
    return '<div class="kpis">' + "".join(f'<div class="kpi"><span>{esc(a)}</span><b class="{c}">{esc(b)}</b></div>' for a, b, c in items) + "</div>"


def tabla(filas, cab):
    return "<table><tr>" + "".join(f"<th>{esc(c)}</th>" for c in cab) + "</tr>" + "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas) + "</table>"


def cls(v, sube_bien=True):
    if v is None or round(v, 2) == 0:
        return ""
    return "up" if (v > 0) == sube_bien else "dn"


def relacionadas(slug):
    return '<div class="card"><h2>Otros indicadores</h2><div class="rel">' + "".join(
        f'<a href="/{s}/">{esc(n)}</a>' for s, n, _, _ in PAGINAS if s != slug) + "</div></div>"


SALIDA = {}   # slug -> (html sin relacionadas, marca)


def pag_diaria(slug, nombre, h1, serie, fmt, unidad, color, que_es, tab, fuente, sube_bien=True, pref="", dec=2, grupo="Argentina",
               titulo_seo=None, extra="", etq=None):
    if len(serie) < 5:
        return
    uu = lambda z: f"{pref}{fmt(z)}" + ("%" if unidad == "%" else (" " + unidad) if unidad else "")
    f, v = serie[-1]
    ant = serie[-2]
    sem, mes = en(serie, 7), en(serie, 30)
    ano = [p for p in serie if p[0][:4] == f[:4]]
    ini = [p for p in serie if p[0] < f[:4] + "-01-01"]
    base_ano = ini[-1] if ini else None
    mx = max(ano, key=lambda p: p[1]) if ano else None
    mn = min(ano, key=lambda p: p[1]) if ano else None
    d1 = v - ant[1]
    pct = lambda a: (v / a[1] - 1) * 100 if a and a[1] else None
    es_pct = unidad in ("pb",) or "%" in unidad
    var = (lambda a: v - a[1]) if es_pct or unidad == "pb" else pct
    vtxt = (lambda x: f"{sg(x, 0 if unidad == 'pb' else 2)} {'pb' if unidad == 'pb' else 'puntos'}") if (es_pct or unidad == "pb") else (lambda x: f"{sg(x)}%")
    frases = [f"<b>{esc(nombre)}</b>: <b>{uu(v)}</b> el {fecha_larga(f)}."]
    dd = var(ant)
    if dd is not None:
        frases.append(f"Contra el dato anterior ({fecha_corta(ant[0])}), {('subió ' + vtxt(dd).lstrip('+')) if round(dd, 2) > 0 else ('bajó ' + vtxt(dd).lstrip('+')) if round(dd, 2) < 0 else 'quedó igual'}.")
    if mx and mn and len(ano) > 20:
        if mx[0] == f:
            frases.append(f"Es el valor <b>más alto de {f[:4]}</b>.")
        elif mn[0] == f:
            frases.append(f"Es el valor <b>más bajo de {f[:4]}</b>.")
        else:
            frases.append(f"En {f[:4]}, el máximo fue {pref}{fmt(mx[1])} ({fecha_corta(mx[0])}) y el mínimo, {pref}{fmt(mn[1])} ({fecha_corta(mn[0])}).")
    k = [("Último dato", uu(v), ""), ("Día anterior", vtxt(dd) if dd is not None else "—", cls(dd, sube_bien))]
    for etq, a in (("En una semana", sem), ("En un mes", mes), (f"En {f[:4]}", base_ano)):
        x = var(a) if a else None
        k.append((etq, vtxt(x) if x is not None else "—", cls(x, sube_bien)))
    ult = serie[-10:][::-1]
    filas = []
    for i, (d, val) in enumerate(ult):
        prev = serie[len(serie) - 2 - i] if len(serie) - 2 - i >= 0 else None
        x = (val - prev[1]) if prev and (es_pct or unidad == "pb") else ((val / prev[1] - 1) * 100 if prev and prev[1] else None)
        filas.append([fecha_corta(d), uu(val), f'<span class="{cls(x, sube_bien)}">{vtxt(x) if x is not None else "—"}</span>'])
    cuerpo = (f'<h1>{esc(h1)}</h1><div class="big">{pref}{fmt(v)}<small>{esc(unidad)}</small></div>'
              f'<div class="cuando">Dato del {fecha_larga(f)} · Fuente: {esc(fuente)}</div>'
              f'<p class="lead">{" ".join(frases)}</p>{kpis(k)}{extra}'
              f'<div class="card"><h2>Evolución</h2>{svg_linea(serie[-260:], color, lambda z: pref + fmt(z))}</div>'
              f'<a class="btn" href="/#{tab}">Ver todo en el tablero →</a>'
              f'<div class="card"><h2>Últimos datos</h2>{tabla(filas, ["Fecha", nombre, "Cambio"])}</div>'
              f'<div class="prose">{que_es}</div>')
    ts = titulo_seo or f"{h1}: {uu(v)} ({fecha_corta(f)})"
    desc = re.sub("<[^>]+>", "", " ".join(frases[:2]))[:300]
    PAGINAS.append((slug, etq or nombre, uu(v), grupo))
    SALIDA[slug] = (ts + " | Pulso Macro", desc, cuerpo, esc(nombre))


def pag_mensual(slug, nombre, h1, serie, fmt, unidad, color, que_es, tab, fuente, frases_extra="", k_extra=None, grupo="Argentina",
                sube_bien=False, yoy=None, etq=None):
    if len(serie) < 3:
        return
    m, v = serie[-1]
    p = serie[-2]
    frases = [f"<b>{esc(nombre)}</b> de {mes_txt(m)}: <b>{fmt(v)}{unidad}</b>.",
              f"El mes anterior ({mes_txt(p[0])}) había sido {fmt(p[1])}{unidad}."]
    if frases_extra:
        frases.append(frases_extra)
    k = [("Último dato", f"{fmt(v)}{unidad}", ""), ("Mes anterior", f"{fmt(p[1])}{unidad}", "")]
    k += k_extra or []
    filas = []
    for i, (mm, val) in enumerate(serie[-12:][::-1]):
        fila = [mes_txt(mm).capitalize(), f"{fmt(val)}{unidad}"]
        if yoy:
            yy = dict(yoy).get(mm)
            fila.append(f"{nf(yy, 1)}%" if yy is not None else "—")
        filas.append(fila)
    cab = ["Mes", nombre] + (["Interanual"] if yoy else [])
    cuerpo = (f'<h1>{esc(h1)}</h1><div class="big">{fmt(v)}{esc(unidad)}<small>{mes_txt(m)}</small></div>'
              f'<div class="cuando">Último dato publicado: {mes_txt(m)} · Fuente: {esc(fuente)}</div>'
              f'<p class="lead">{" ".join(frases)}</p>{kpis(k)}'
              f'<div class="card"><h2>Evolución</h2>{svg_linea(serie[-60:], color, lambda z: fmt(z) + unidad, mensual_=True)}</div>'
              f'<a class="btn" href="/#{tab}">Ver todo en el tablero →</a>'
              f'<div class="card"><h2>Últimos 12 meses</h2>{tabla(filas, cab)}</div><div class="prose">{que_es}</div>')
    ts = f"{h1}: {fmt(v)}{unidad} en {mes_txt(m)}"
    desc = re.sub("<[^>]+>", "", " ".join(frases[:2]))[:300]
    PAGINAS.append((slug, etq or nombre, f"{fmt(v)}{unidad}", grupo))
    SALIDA[slug] = (ts + " | Pulso Macro", desc, cuerpo, esc(nombre))


def P(*ps):
    return "".join(f"<h2>{esc(h)}</h2><p>{t}</p>" for h, t in ps)


# ---------- Argentina ----------
peso = lambda z: nf(z, 2)
for slug, clave, nombre, h1, color, txt in [
    ("dolar-blue-hoy", "blue", "Dólar blue", "Dólar blue hoy", "#c98500",
     P(("¿Qué es el dólar blue?", "Es el dólar que se compra y vende en el mercado informal (las \"cuevas\" y arbolitos). No está regulado: su precio sale de la oferta y la demanda del día. Se usa como termómetro de cuánto vale el peso para quien no puede o no quiere operar en el mercado oficial."),
       ("¿De dónde sale el dato?", "Cotización de venta informada por los medios que relevan el mercado informal. En el tablero se actualiza cada minuto durante el día."))),
    ("dolar-mep-hoy", "mep", "Dólar MEP", "Dólar MEP hoy", "#d95926",
     P(("¿Qué es el dólar MEP?", "El dólar MEP (Mercado Electrónico de Pagos), o dólar bolsa, se consigue comprando un bono en pesos y vendiéndolo en dólares. Es una forma legal de comprar dólares sin límite de monto, desde cualquier cuenta comitente."),
       ("¿Cuál es la diferencia con el CCL?", "Con el MEP los dólares quedan en una cuenta en Argentina; con el contado con liquidación (CCL) quedan en una cuenta del exterior. Por eso el CCL suele cotizar un poco más caro."))),
    ("dolar-ccl-hoy", "ccl", "Dólar CCL", "Dólar contado con liqui (CCL) hoy", "#199e70",
     P(("¿Qué es el contado con liquidación?", "Es el tipo de cambio que surge de comprar una acción o un bono en pesos en Argentina y venderlo en dólares en el exterior. Es la vía que usan las empresas y los inversores para sacar dólares del país de forma legal."),
       ("¿Por qué importa?", "Es la referencia del dólar \"financiero\". La diferencia con el oficial, la brecha, muestra cuánta presión hay sobre el peso."))),
    ("dolar-oficial-hoy", "oficial", "Dólar oficial", "Dólar oficial hoy", "#3987e5",
     P(("¿Qué es el dólar oficial?", "Es la cotización minorista que cobran los bancos al público (precio de venta del Banco Nación). Se mueve casi igual que el dólar mayorista, que es el que usan las empresas y el BCRA."),)),
    ("dolar-tarjeta-hoy", "tarjeta", "Dólar tarjeta", "Dólar tarjeta hoy", "#8fa3b5",
     P(("¿Qué es el dólar tarjeta?", "Es lo que termina costando cada dólar cuando pagás con tarjeta en el exterior o en servicios del exterior: el dólar oficial más las percepciones de impuestos que se cobran a cuenta de Ganancias y Bienes Personales."),)),
]:
    s = diaria(clave)
    pag_diaria(slug, nombre, h1, s, peso, "", color, txt, "dolares", "DolarApi y Ámbito", pref="$ ", titulo_seo=None)

ofi, ccl, may = diaria("oficial"), diaria("ccl"), diaria("mayorista")
brecha = cruzar(ccl, ofi, lambda a, b: (a / b - 1) * 100)
pag_diaria("brecha-cambiaria", "Brecha CCL", "Brecha cambiaria hoy (CCL vs. oficial)", brecha, lambda z: nf(z, 1), "%", "#c98500",
           P(("¿Qué es la brecha cambiaria?", "Es cuánto más caro está el dólar contado con liquidación (CCL) que el dólar oficial, en porcentaje. Una brecha alta indica que el mercado cree que el peso oficial está sobrevaluado o que hay restricciones para comprar dólares."),
             ("¿Cómo se calcula?", "Brecha = (dólar CCL ÷ dólar oficial − 1) × 100, con los valores de venta del mismo día.")),
           "dolares", "cálculo de Pulso Macro con datos de Ámbito y DolarApi", sube_bien=False)
pag_diaria("riesgo-pais", "Riesgo país", "Riesgo país hoy", diaria("riesgo"), lambda z: nf(z, 0), "pb", "#e0663a",
           P(("¿Qué es el riesgo país?", "Es la tasa extra que pagan los bonos argentinos en dólares por encima de los bonos del Tesoro de Estados Unidos, medida en puntos básicos (100 puntos básicos = 1 punto porcentual). Lo calcula JP Morgan con el índice EMBI."),
             ("¿Por qué importa?", "Cuanto más alto, más caro le sale al país (y a las empresas) conseguir financiamiento, y más riesgo de que no pueda pagar ve el mercado. Por debajo de 500 puntos suele considerarse que se abre la puerta para volver a emitir deuda.")),
           "macro", "Ámbito (JP Morgan EMBI)", sube_bien=False)
pag_diaria("reservas-bcra", "Reservas del BCRA", "Reservas del Banco Central hoy", diaria("reservas"), lambda z: nf(z, 0), "M US$", "#199e70",
           P(("¿Qué son las reservas?", "Son los activos en moneda extranjera y oro que tiene el Banco Central: dólares, otras monedas, oro, posiciones en el FMI. Respaldan al peso y sirven para pagar deuda e intervenir en el mercado de cambios."),
             ("Brutas y netas", "El dato que publica el BCRA cada día son las reservas brutas. Las netas descuentan lo que no es realmente propio (encajes de depósitos en dólares, swaps, préstamos de corto plazo) y son bastante más bajas.")),
           "macro", "BCRA (con uno o dos días de atraso)", grupo="Argentina")
pag_diaria("merval-hoy", "Merval", "Merval hoy", diaria("merval"), lambda z: nf(z, 0), "puntos", "#6aa8d8",
           P(("¿Qué es el Merval?", "El Merval es el principal índice de la Bolsa de Buenos Aires: sigue el precio de las acciones argentinas más negociadas (bancos, energéticas, servicios). Desde el 19/10/2026 lo calcula MSCI (antes S&P) y arrancó en 100.000 puntos al cierre del 16/10/2026; los datos anteriores están pasados a esa base, con las mismas subas y bajas."),
             ("En pesos y en dólares", "Como el peso pierde valor, una suba del Merval en pesos puede ser una baja en dólares. En el tablero también lo mostramos convertido a dólares contado con liqui.")),
           "mercado", "Ámbito")
pag_diaria("tasa-plazo-fijo", "Tasa de plazo fijo", "Tasa de plazo fijo hoy", diaria("pf"), lambda z: nf(z, 2), "%", "#3987e5",
           P(("¿Qué tasa es?", "Es la tasa nominal anual promedio que pagan los bancos por plazos fijos a 30 días de personas (dato del BCRA). Para comparar con la inflación mensual, dividila por 12: es lo que gana por mes."),
             ("¿Le gana a la inflación?", "En el tablero comparamos todos los meses lo que rinde el plazo fijo contra la inflación del INDEC, y te decimos si ganó o perdió.")),
           "dinero", "BCRA")

# compras del BCRA: suma del año
cp = diaria("compras")
if cp:
    anio = cp[-1][0][:4]
    tot = sum(v for d, v in cp if d[:4] == anio)
    pag_diaria("compras-dolares-bcra", "Compras del BCRA", "Compras de dólares del BCRA hoy", cp, lambda z: nf(z, 0), "M US$", "#199e70",
               P(("¿Qué son las compras del BCRA?", "Es lo que el Banco Central compra (o vende, si da negativo) en el mercado oficial de cambios cada día, en millones de dólares. Cuando compra, suma reservas; cuando vende, las usa."),),
               "macro", "BCRA", extra=kpis([(f"Acumulado {anio}", f"{sg(tot, 0)} M US$", cls(tot))]))

# inflación
infl, inya = mensual("infl"), mensual("inflYoY")
if infl:
    ex = [m for m in MENSUAL if m.get("expect") is not None]
    pag_mensual("inflacion-argentina", "Inflación mensual", "Inflación en Argentina", infl, lambda z: nf(z, 1), "%", "#e0663a",
                P(("¿Qué mide?", "La inflación es cuánto subieron en promedio los precios de lo que consume una familia, según el Índice de Precios al Consumidor (IPC) del INDEC. Se publica a mediados de cada mes con el dato del mes anterior."),
                  ("Mensual e interanual", "La mensual compara con el mes anterior; la interanual, con el mismo mes del año pasado (los últimos 12 meses).")),
                "macro", "INDEC", frases_extra=(f"En los últimos 12 meses, la inflación fue de <b>{nf(inya[-1][1], 1)}%</b>." if inya else ""),
                k_extra=([("Últimos 12 meses", f"{nf(inya[-1][1], 1)}%", "")] if inya else []) + ([("Esperada próximos 12 meses (REM)", f"{nf(ex[-1]['expect'], 1)}%", "")] if ex else []),
                yoy=inya, etq="Inflación Argentina")

# balanza comercial
sal = mensual("saldo")
if sal:
    ex_, im_ = dict(mensual("expo")), dict(mensual("impo"))
    m = sal[-1][0]
    ano = [v for mm, v in sal if mm[:4] == m[:4]]
    pag_mensual("balanza-comercial", "Saldo comercial", "Balanza comercial de Argentina", sal, lambda z: nf(z, 0), " M US$", "#2fb383",
                P(("¿Qué es la balanza comercial?", "Es la diferencia entre lo que el país exporta y lo que importa en bienes, en millones de dólares. Si da positivo hay superávit: entran más dólares por comercio de los que salen."),),
                "fiscal", "INDEC", etq="Balanza comercial", frases_extra=f"Exportaciones: US$ {nf(ex_.get(m, 0), 0)} M; importaciones: US$ {nf(im_.get(m, 0), 0)} M. En lo que va de {m[:4]}, el saldo suma US$ {nf(sum(ano), 0)} M.",
                k_extra=[("Exportaciones", f"{nf(ex_.get(m, 0), 0)} M US$", ""), ("Importaciones", f"{nf(im_.get(m, 0), 0)} M US$", ""),
                         (f"Acumulado {m[:4]}", f"{nf(sum(ano), 0)} M US$", "")], sube_bien=True)

# ganadería
G = cargar("ganaderia.json")
hac = G.get("hacienda", {})
nov = [(d, v["grupos"]["NOVILLOS"]["prom"]) for d, v in sorted(hac.items()) if v.get("grupos", {}).get("NOVILLOS", {}).get("prom")]
if nov:
    k = max(hac)
    gr = hac[k]["grupos"]
    fil = "".join(f"<tr><td>{esc(g.capitalize() if g != 'MEJ' else 'Mestizos (MEJ)')}</td><td>$ {nf(x['prom'], 2)}</td><td>{nf(x['cab'], 0)}</td></tr>" for g, x in gr.items() if x.get("prom"))
    extra = f'<div class="card"><h2>Todas las categorías, {fecha_corta(k)}</h2><table><tr><th>Categoría</th><th>$/kg vivo</th><th>Cabezas</th></tr>{fil}</table></div>'
    pag_diaria("precio-novillo-hoy", "Novillo", "Precio del novillo hoy en Cañuelas (ex Liniers)", nov, lambda z: nf(z, 2), "por kg", "#c98500",
               P(("¿De dónde sale?", "Es el precio promedio por kilo vivo de los novillos vendidos en el Mercado Agroganadero de Cañuelas, que reemplazó al histórico Mercado de Liniers. Es la referencia de precios de la hacienda en Argentina."),
                 ("¿Cuándo hay remate?", "El mercado opera casi siempre martes, miércoles y viernes. Los precios del día son provisorios hasta la tarde.")),
               "ganaderia", "Mercado Agroganadero de Cañuelas", extra=extra, pref="$ ", etq="Precio del novillo")

piz = G.get("pizarra", {})
if piz:
    f = max(piz)
    p = piz[f]
    fil = []
    for k_, n_ in (("soja", "Soja"), ("trigo", "Trigo"), ("maiz", "Maíz"), ("girasol", "Girasol"), ("sorgo", "Sorgo")):
        if k_ in p:
            fil.append([n_ + (" (estimado)" if p[k_].get("est") else ""), f"$ {nf(p[k_]['ars'], 0)}", f"US$ {nf(p[k_]['usd'], 2)}"])
    soja = p.get("soja", {})
    cuerpo = (f'<h1>Precios pizarra de Rosario hoy</h1><div class="big">US$ {nf(soja.get("usd", 0), 0)}<small>soja, por tonelada</small></div>'
              f'<div class="cuando">Pizarra del {fecha_larga(f)} · Fuente: Cámara Arbitral de Cereales, Bolsa de Comercio de Rosario</div>'
              f'<p class="lead">Precios pizarra del {fecha_larga(f)} en Rosario: soja <b>$ {nf(soja.get("ars", 0), 0)}</b> por tonelada'
              f'{", trigo $ " + nf(p["trigo"]["ars"], 0) if "trigo" in p else ""}{" y maíz $ " + nf(p["maiz"]["ars"], 0) if "maiz" in p else ""}.</p>'
              f'<div class="card"><h2>Precios por tonelada</h2>{tabla(fil, ["Grano", "Pesos", "Dólares"])}</div>'
              f'<a class="btn" href="/#ganaderia">Ver todo en el tablero →</a>'
              + P(("¿Qué es el precio pizarra?", "Es el precio de referencia que fija cada día la Cámara Arbitral de Cereales de la Bolsa de Comercio de Rosario, con las operaciones del día en el mercado físico. Se usa para liquidar contratos y como referencia para todo el campo."),
                  ("¿Cuándo se publica?", "La pizarra de cada día hábil se publica a la mañana del día hábil siguiente. Los valores marcados como estimados no tuvieron operaciones suficientes ese día.")))
    PAGINAS.append(("precios-pizarra-rosario", "Pizarra de Rosario", f"Soja US$ {nf(soja.get('usd', 0), 0)}", "Argentina"))
    SALIDA["precios-pizarra-rosario"] = (f"Precios pizarra Rosario hoy: soja $ {nf(soja.get('ars', 0), 0)} ({fecha_corta(f)}) | Pulso Macro",
                                          f"Precios pizarra de la Bolsa de Comercio de Rosario del {fecha_larga(f)}: soja, trigo, maíz, girasol y sorgo en pesos y dólares por tonelada.",
                                          cuerpo, "Pizarra de Rosario")

# ---------- El mundo ----------
B = cargar("brasil.json")
ptax = [(d, v) for d, v in B.get("ptax", [])]
real = cruzar(may, ptax, lambda a, b: a / b)
pag_diaria("real-en-pesos", "Real en pesos", "Cuánto vale un real en pesos hoy", real, lambda z: nf(z, 2), "", "#199e70",
           P(("¿Cómo se calcula?", "Dividimos el dólar mayorista argentino por el dólar PTAX de Brasil del mismo día (cuántos reales vale un dólar). El resultado es cuántos pesos vale un real brasileño al tipo de cambio oficial."),
             ("Para viajar", "Si pagás con tarjeta o con dólar MEP, el real te sale más caro que este valor. En la calculadora de viaje del tablero podés ver cuánto te cuesta según cómo pagues.")),
           "brasil", "BCRA y Banco Central de Brasil (PTAX)", pref="$ ", grupo="El mundo", sube_bien=False)
E = cargar("europa.json")
eur = cruzar(may, [(d, v) for d, v in E.get("eurusd", [])], lambda a, b: a * b)
pag_diaria("euro-en-pesos", "Euro en pesos", "Cuánto vale un euro en pesos hoy", eur, lambda z: nf(z, 2), "", "#3987e5",
           P(("¿Cómo se calcula?", "Multiplicamos el dólar mayorista argentino por la cotización del euro en dólares del Banco Central Europeo del mismo día. Es el valor del euro al tipo de cambio oficial."),),
           "europa", "BCRA y Banco Central Europeo", pref="$ ", grupo="El mundo", sube_bien=False)
PL = cargar("polonia.json")
pln = cruzar(may, [(d, v) for d, v in PL.get("usdpln", [])], lambda a, b: a / b)
if pln:
    pag_diaria("zloty-en-pesos", "Zloty en pesos", "Cuánto vale un zloty polaco en pesos hoy", pln, lambda z: nf(z, 2), "", "#d55181",
               P(("¿Cómo se calcula?", "Dividimos el dólar mayorista argentino por la cotización oficial del dólar en zlotys del Banco Nacional de Polonia del mismo día. El resultado es cuántos pesos vale un zloty al tipo de cambio oficial."),
                 ("Polonia y el euro", "Polonia está en la Unión Europea pero no usa el euro: mantiene el zloty y su propio banco central. En el tablero está su tasa de interés, la inflación y la comparación con Argentina desde 1990.")),
               "polonia", "BCRA y Banco Nacional de Polonia", pref="$ ", grupo="El mundo", sube_bien=False)
sel = [(d, v) for d, v in B.get("selic", [])]
if sel:
    pag_diaria("tasa-selic", "Tasa Selic", "Tasa Selic hoy (Brasil)", sel, lambda z: nf(z, 2), "%", "#d95926",
               P(("¿Qué es la Selic?", "Es la tasa de interés de referencia de Brasil, que fija el Comité de Política Monetaria (Copom) del Banco Central de Brasil cada 45 días aproximadamente. Es una de las tasas reales más altas del mundo."),),
               "brasil", "Banco Central de Brasil", grupo="El mundo")
U = cargar("usa.json")
ipc = U.get("bls", {}).get("ipc", [])
if len(ipc) > 13:
    yy = []
    m_ = dict(ipc)
    for mm, v in ipc:
        a = f"{int(mm[:4]) - 1}{mm[4:]}"
        if a in m_:
            yy.append((mm, (v / m_[a] - 1) * 100))
    fed = U.get("fed", {})
    pag_mensual("inflacion-estados-unidos", "Inflación interanual", "Inflación en Estados Unidos", yy, lambda z: nf(z, 1), "%", "#e0663a",
                P(("¿Qué mide?", "Es la suba de precios al consumidor en Estados Unidos en los últimos 12 meses (índice CPI-U del Bureau of Labor Statistics). La Reserva Federal busca que se acerque al 2%."),),
                "eeuu", "BLS", grupo="El mundo", etq="Inflación EE.UU.",
                frases_extra=(f"La tasa de la Reserva Federal está en {nf(fed['actual'], 2)}%." if fed.get("actual") else ""))
T = cargar("turquia.json")
ti = [(m, v) for m, v in T.get("infl", [])]
if ti and inya:
    ar = dict(inya)
    comp = f"En Argentina, la inflación de {mes_txt(ti[-1][0])} fue {nf(ar[ti[-1][0]], 1)}% interanual." if ti[-1][0] in ar else ""
    pag_mensual("inflacion-turquia", "Inflación interanual", "Inflación en Turquía", ti, lambda z: nf(z, 1), "%", "#e0663a",
                P(("Turquía y Argentina", "Turquía es uno de los pocos países con una inflación comparable a la argentina. En el tablero las comparamos mes a mes, junto con la tasa del Banco Central de Turquía y la lira contra el peso."),),
                "turquia", "BIS y OCDE", grupo="El mundo", frases_extra=comp, etq="Inflación Turquía")


# ---------- escribir ----------
def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if not ruta.exists() or ruta.read_text(encoding="utf-8") != texto:
        ruta.write_text(texto, encoding="utf-8")
        return 1
    return 0


cambios = 0
for slug, (ts, desc, cuerpo, crumb) in SALIDA.items():
    cambios += escribir(ROOT / slug / "index.html", pagina(slug, ts, desc, cuerpo + relacionadas(slug), crumb))

grupos = {}
for s, n, v, g in PAGINAS:
    grupos.setdefault(g, []).append((s, n, v))
hub = '<h1>Todos los indicadores</h1><p class="lead">Los datos más buscados de la economía argentina y del mundo, cada uno con su gráfico, su historia y qué significa. Se actualizan solos cada día hábil.</p>'
for g, items in grupos.items():
    hub += f'<div class="card"><h2>{esc(g)}</h2><div class="grid">' + "".join(f'<a href="/{s}/"><span>{esc(n)}</span><b>{esc(v)}</b></a>' for s, n, v in items) + "</div></div>"
hub += '<a class="btn" href="/">Ir al tablero completo →</a>'
cambios += escribir(ROOT / "indicadores" / "index.html", pagina("", "Indicadores de la economía argentina y del mundo, hoy | Pulso Macro",
                                                              "Dólar blue, MEP y CCL, riesgo país, inflación, reservas, Merval, balanza comercial, novillo, granos y más: todos los indicadores de Pulso Macro con su gráfico.",
                                                              hub, "Indicadores"))

urls = [f"{SITE}/", f"{SITE}/indicadores/"] + [f"{SITE}/{s}/" for s in SALIDA]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n"
cambios += escribir(ROOT / "sitemap.xml", sm)
cambios += escribir(ROOT / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
print(f"páginas: {len(SALIDA)} + índice; archivos cambiados: {cambios}")
