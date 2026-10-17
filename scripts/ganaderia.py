"""Arma ganaderia.json para la sección Ganadería de Pulso Macro.

Fuentes gratuitas, sin clave:
  - Mercado Agroganadero de Cañuelas (ex Liniers): "Precios por categoría" de cada día de operación
    (mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo000002 con txtFechaIni y txtFechaFin, dd/mm/aaaa).
    Por categoría: precio mínimo, máximo, promedio y mediana en $ por kilo vivo, cabezas, importe, kilos y kilos por cabeza.
  - Cámara Arbitral de Cereales de la Bolsa de Comercio de Rosario: precios pizarra del día (trigo, maíz, girasol,
    soja y sorgo), en $ y US$ por tonelada. La página solo muestra el día: la historia se arma guardando cada día.

Uso: python scripts/ganaderia.py
Nunca inventa datos: si una fuente falla, deja lo que había y lo anota en "errores".
"""

import json
import re
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ganaderia.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
MAG = "https://www.mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo000002?txtFechaIni={f}&txtFechaFin={f}"
CAC = "https://www.cac.bcr.com.ar/es/precios-de-pizarra"
DIAS_HISTORIA = 400       # cuánto hacia atrás se reconstruye la hacienda
MAX_POR_VUELTA = 260      # días nuevos que se piden por corrida (el resto en la próxima)
GRUPOS = ["NOVILLOS", "NOVILLITOS", "VAQUILLONAS", "VACAS", "TOROS", "MEJ"]
NUM = r"(\d[\d\.]*,\d+)"
FILA = re.compile(r"([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ\.\+/ 0-9]*?)\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM
                  + r"\s+([\d\.]+)\s+\$([\d\.]+,\d+)\s+([\d\.]+)\s+(\d+)")
TOTAL = re.compile(r"-{3,}[\s-]*" + NUM + r"\s+([\d\.]+)\s+\$([\d\.]+,\d+)\s+([\d\.]+)\s+(\d+)")
errores = []


def get(url, tries=3, timeout=60):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                cs = r.headers.get_content_charset() or "latin-1"   # Cañuelas: latin-1; Rosario: UTF-8
                return r.read().decode(cs, "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise last


def plano(html):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t).replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t)


def n(s):
    return float(s.replace(".", "").replace(",", "."))


def hacienda_dia(d):
    """Precios de un día. None si ese día no hubo operaciones."""
    t = plano(get(MAG.format(f=d.strftime("%d/%m/%Y"))))
    i = t.find("PRECIOS POR CATEGORIA")
    if i < 0:
        raise ValueError("no apareció la tabla de precios")
    t = t[i:]
    definitivo = "DEFINITIVOS" in t[:200]
    j = t.find("Kgs Kgs")
    cuerpo = t[j + 7:] if j > 0 else t
    fin = cuerpo.find("NOTA:")
    if fin > 0:
        cuerpo = cuerpo[:fin]
    filas, grupos, grupo = [], {}, None
    pos = 0
    while True:
        mf, mt = FILA.search(cuerpo, pos), TOTAL.search(cuerpo, pos)
        if not mf and not mt:
            break
        if mt and (not mf or mt.start() < mf.start()):
            if grupo:
                grupos[grupo] = {"prom": n(mt.group(1)), "cab": int(mt.group(2).replace(".", "")),
                                 "imp": n(mt.group(3)), "kg": int(mt.group(4).replace(".", "")), "kgc": int(mt.group(5))}
            pos = mt.end()
            continue
        nombre = mf.group(1).strip()
        g = nombre.split()[0].upper()
        if g in GRUPOS:
            grupo = g
        filas.append({"cat": nombre, "g": grupo or g, "min": n(mf.group(2)), "max": n(mf.group(3)), "prom": n(mf.group(4)),
                      "med": n(mf.group(5)), "cab": int(mf.group(6).replace(".", "")), "imp": n(mf.group(7)),
                      "kg": int(mf.group(8).replace(".", "")), "kgc": int(mf.group(9))})
        pos = mf.end()
    if not filas:
        return None
    # si un grupo de una sola fila no trae total, se arma con su fila
    for f in filas:
        if f["g"] not in grupos:
            gs = [x for x in filas if x["g"] == f["g"]]
            kg = sum(x["kg"] for x in gs)
            grupos[f["g"]] = {"prom": round(sum(x["imp"] for x in gs) / kg, 3) if kg else None, "cab": sum(x["cab"] for x in gs),
                              "imp": sum(x["imp"] for x in gs), "kg": kg, "kgc": round(kg / max(1, sum(x["cab"] for x in gs)))}
    kg = sum(f["kg"] for f in filas)
    total = {"prom": round(sum(f["imp"] for f in filas) / kg, 3) if kg else None, "cab": sum(f["cab"] for f in filas),
             "imp": round(sum(f["imp"] for f in filas), 2), "kg": kg}
    return {"def": definitivo, "grupos": grupos, "total": total, "filas": filas}


def pizarra():
    t = plano(get(CAC))
    m = re.search(r"Precios Pizarra del d[ií]a (\d{2})/(\d{2})/(\d{4})", t)
    if not m:
        raise ValueError("no apareció la fecha de la pizarra")
    f = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    out = {}
    for g, k in [("Trigo", "trigo"), ("Ma[ií]z", "maiz"), ("Girasol", "girasol"), ("Soja", "soja"), ("Sorgo", "sorgo")]:
        mg = re.search(g + r"\s*(S/C)?\s*(\(E\))?\s*\$\s*([\d\.]+,\d+)\s*US\$\s*(\(E\))?\s*([\d\.]+,\d+)", t[m.end():m.end() + 900])
        if mg:
            out[k] = {"ars": n(mg.group(3)), "usd": n(mg.group(5)), "est": bool(mg.group(1) or mg.group(2) or mg.group(4))}
    if not out:
        raise ValueError("no se pudieron leer los precios")
    return f, out


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    hac = prev.get("hacienda", {})          # {"aaaa-mm-dd": {...}}
    sin_op = set(prev.get("sin_operaciones", []))
    hoy = datetime.now(timezone(timedelta(hours=-3))).date()
    # días a pedir: los últimos 4 siempre (provisorios → definitivos), después los que falten, de lo nuevo a lo viejo
    pedir = []
    for k in range(DIAS_HISTORIA):
        d = hoy - timedelta(days=k)
        if d.weekday() >= 5:
            continue
        iso = d.isoformat()
        reciente = k <= 4
        ya = iso in hac and hac[iso].get("def")
        if reciente and not ya:
            pedir.append(d)
        elif not reciente and iso not in hac and iso not in sin_op:
            pedir.append(d)
    pedidos = 0
    fallas = 0
    for d in pedir:
        if pedidos >= MAX_POR_VUELTA:
            break
        iso = d.isoformat()
        try:
            r = hacienda_dia(d)
            pedidos += 1
            if r is None:
                if d < hoy - timedelta(days=4):
                    sin_op.add(iso)   # feriado o día sin remates: no se vuelve a pedir
            else:
                hac[iso] = r
            fallas = 0
        except Exception as e:  # noqa: BLE001
            fallas += 1
            errores.append(f"hacienda {iso}: {e}")
            if fallas >= 6:
                errores.append("hacienda: demasiadas fallas seguidas, sigo en la próxima vuelta")
                break
        time.sleep(0.6)
    corte = (hoy - timedelta(days=DIAS_HISTORIA + 10)).isoformat()
    hac = {k: v for k, v in sorted(hac.items()) if k >= corte}
    for v in hac.values():
        v.pop("_cola", None)
    piz = prev.get("pizarra", {})
    try:
        f, p = pizarra()
        piz[f] = p
    except Exception as e:  # noqa: BLE001
        errores.append(f"pizarra: {e}")
    data = {"hacienda": hac, "sin_operaciones": sorted(x for x in sin_op if x >= corte), "pizarra": dict(sorted(piz.items())),
            "actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"), "errores": errores[:30],
            "pendientes": max(0, len(pedir) - pedidos)}
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    ult = max(hac) if hac else None
    print(f"hacienda: {len(hac)} días (último {ult}), pedidos {pedidos}, pendientes {data['pendientes']}; pizarra: {len(piz)} días")
    for e in errores:
        print("ERROR", e)


if __name__ == "__main__":
    main()
