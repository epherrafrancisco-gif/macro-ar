"""Indicadores calculados por Pulso Macro con precios de bonos (método publicado en el sitio).

- MEP Pulso Macro  = precio del AL30 en pesos ÷ precio del AL30D (en dólares MEP), por cada 100 nominales.
- CCL Pulso Macro  = precio del AL30 en pesos ÷ precio del AL30C (en dólares cable).
  (Si falta el AL30, se usa el GD30 con la misma cuenta.)
- Riesgo país Pulso Macro = promedio simple, en puntos básicos, de (TIR de cada Global en dólares − rendimiento del bono
  del Tesoro de EE.UU. al mismo plazo), para los Globales con más de 3 años de duración (hoy GD35, GD38, GD41 y GD46;
  los más cortos, GD29 y GD30, se dejan afuera porque a menos de 2 años el diferencial se distorsiona). La TIR se calcula con el cronograma de
  pagos de cada bono (mismo cálculo que la página, validado contra PPI ±0,1 pp) y el Tesoro se interpola en la curva del
  Tesoro de EE.UU. a la duración del bono.

No es el EMBI de J.P. Morgan (que usa su propia canasta y ponderaciones): sigue el mismo movimiento pero puede diferir
en decenas de puntos. Por eso se publica con su nombre propio.
"""
from datetime import date, timedelta


def _bq(n, desde, hasta, pct=None):
    out, (y, m) = {}, map(int, desde.split("-"))
    while True:
        f = f"{y}-{m:02d}-09"
        out[f] = pct if pct is not None else 100 / n
        if f[:7] == hasta:
            return out
        if m == 1:
            m = 7
        else:
            m, y = 1, y + 1


BDEF = {
    "29": {"am": _bq(10, "2025-01", "2029-07"), "cup": [["9999", 1]]},
    "30": {"am": {"2024-07-09": 4, **_bq(12, "2025-01", "2030-07", 8)},
           "cup": [["2021-07-09", 0.125], ["2023-07-09", 0.5], ["2027-07-09", 0.75], ["9999", 1.75]]},
    "35": {"am": _bq(10, "2031-01", "2035-07"),
           "cup": [["2021-07-09", 0.125], ["2022-07-09", 1.125], ["2023-07-09", 1.5], ["2024-07-09", 3.625], ["2027-07-09", 4.125], ["2028-07-09", 4.75], ["9999", 5]]},
    "38": {"am": _bq(22, "2027-07", "2038-01"),
           "cup": [["2021-07-09", 0.125], ["2022-07-09", 2], ["2023-07-09", 3.875], ["2024-07-09", 4.25], ["9999", 5]]},
    "41": {"am": _bq(28, "2028-01", "2041-07"),
           "cup": [["2021-07-09", 0.125], ["2022-07-09", 2.5], ["2029-07-09", 3.5], ["9999", 4.875]]},
    "46": {"am": _bq(44, "2025-01", "2046-07"),
           "cup": [["2021-07-09", 0.125], ["2022-07-09", 1.125], ["2023-07-09", 1.5], ["2024-07-09", 3.625], ["2027-07-09", 4.125], ["2028-07-09", 4.75], ["9999", 5]]},
}


def _flujos(k):
    d, f, res, prev = BDEF[k], [], 100.0, "2020-09-04"
    fin = max(d["am"])
    y = 2021
    while True:
        for m in ("01", "07"):
            dd = f"{y}-{m}-09"
            if dd > fin:
                return f
            r = next(t for lim, t in d["cup"] if prev < lim)
            am = d["am"].get(dd, 0)
            f.append({"d": dd, "cup": res * r / 100 / 2, "am": am, "res": res, "r": r, "prev": prev})
            res -= am
            prev = dd
        y += 1


BFLUJO = {k: _flujos(k) for k in BDEF}


def _dias(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def tir(px, settle, k):
    """TIR anual (%) y duración (años) de un bono por cada 100 nominales originales, precio en dólares."""
    fut = [p for p in BFLUJO[k] if p["d"] > settle]
    if not fut or not px or px <= 0:
        return None
    cf = [(_dias(settle, p["d"]) / 365, p["cup"] + p["am"]) for p in fut]
    pv = lambda y: sum(v / (1 + y) ** t for t, v in cf)
    lo, hi = -0.5, 2.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if pv(mid) > px else (lo, mid)
    y = (lo + hi) / 2
    tot = pv(y)
    dur = sum(t * v / (1 + y) ** t for t, v in cf) / tot if tot else None
    return {"tir": y * 100, "dur": dur}


DUR_MIN = 3  # años de duración mínima para entrar al riesgo país
PLAZOS = {"1M": 1 / 12, "3M": 0.25, "6M": 0.5, "1A": 1, "2A": 2, "3A": 3, "5A": 5, "7A": 7, "10A": 10, "20A": 20, "30A": 30}


def tesoro(curva, anios):
    """Rendimiento del Tesoro de EE.UU. interpolado linealmente al plazo pedido (curva de usa.json)."""
    pts = sorted((PLAZOS[p], v) for p, v in zip(curva.get("plazos", []), curva.get("hoy", [])) if p in PLAZOS and v is not None)
    if not pts:
        return None
    if anios <= pts[0][0]:
        return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if a <= anios <= b:
            return va + (vb - va) * (anios - a) / (b - a)
    return pts[-1][1]


def _settle(hoy):
    """Liquidación a 24 h hábiles (contado 24 h)."""
    d = hoy + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.isoformat()


def calcular(bonos, curva, hoy=None):
    """bonos: lista de Open BYMADATA ({symbol, c}, ver byma_bonos en update.py). Devuelve {mep, ccl, riesgo, detalle} o lo que se pueda."""
    hoy = hoy or date.today()
    px = {b["symbol"]: float(b["c"]) for b in bonos if isinstance(b, dict) and b.get("symbol") and (b.get("c") or 0) > 0}
    out = {}
    for base in ("AL30", "GD30"):
        if "mep" not in out and px.get(base) and px.get(base + "D"):
            out["mep"], out["mep_bono"] = round(px[base] / px[base + "D"], 2), base
        if "ccl" not in out and px.get(base) and px.get(base + "C"):
            out["ccl"], out["ccl_bono"] = round(px[base] / px[base + "C"], 2), base
    settle, spreads, det = _settle(hoy), [], {}
    if curva:
        for k in ("29", "30", "35", "38", "41", "46"):
            p = px.get(f"GD{k}D")
            r = tir(p, settle, k) if p else None
            if not r or r["dur"] is None:
                continue
            ust = tesoro(curva, r["dur"])
            if ust is None:
                continue
            sp = (r["tir"] - ust) * 100
            det[f"GD{k}"] = {"tir": round(r["tir"], 2), "dur": round(r["dur"], 2), "ust": round(ust, 2), "spread": round(sp), "usa": r["dur"] >= DUR_MIN}
            if r["dur"] >= DUR_MIN:
                spreads.append(sp)
    if len(spreads) >= 3:  # con menos de 3 bonos el promedio no es confiable
        out["riesgo"] = round(sum(spreads) / len(spreads))
    out["detalle"] = det
    return out
