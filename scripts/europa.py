"""Arma europa.json para la sección Europa (zona euro) de Pulso Macro.

Fuentes oficiales y gratuitas, sin clave:
  - Banco Central Europeo (data-api.ecb.europa.eu): tasa de depósito del BCE (la tasa de referencia), euro contra dólar
    (diario) y tasa de los bonos a 10 años de Alemania, Francia, Italia y España (mensual).
  - Eurostat (ec.europa.eu/eurostat/api): inflación (HICP) general y núcleo, desempleo y PBI trimestral, de la zona euro
    y de los 4 países grandes.

Uso: python scripts/europa.py
Nunca inventa datos: si una serie falla, queda la que había y se anota en "errores".
"""

import csv
import io
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "europa.json"
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
PAISES = ["EA", "DE", "FR", "IT", "ES"]  # EA = zona euro (composición vigente)
errores = []


def get(url, accept="*/*", tries=3, timeout=60):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise last


def ecb(key, desde, cambios=False):
    txt = get(f"https://data-api.ecb.europa.eu/service/data/{key}?format=csvdata&startPeriod={desde}", "text/csv")
    pts = sorted((r["TIME_PERIOD"], float(r["OBS_VALUE"])) for r in csv.DictReader(io.StringIO(txt)) if r.get("OBS_VALUE") not in (None, "", "NaN"))
    hoy = date.today().isoformat()
    pts = [[t, v] for t, v in pts if t <= hoy]
    if not pts:
        raise ValueError("sin datos")
    if cambios:
        out = [pts[0]]
        for p in pts[1:]:
            if p[1] != out[-1][1]:
                out.append(p)
        if out[-1] != pts[-1]:
            out.append(pts[-1])
        return out
    return pts


def eurostat(dataset, params, por="geo"):
    """Lee un dataset de Eurostat (JSON-stat) y devuelve {valor de la dimensión `por`: [[periodo, valor], ...]}."""
    q = "&".join(f"{k}={v}" for k, vs in params.items() for v in (vs if isinstance(vs, list) else [vs]))
    j = json.loads(get(f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}?{q}", "application/json"))
    ids, sizes, vals = j["id"], j["size"], j.get("value") or {}
    idx = {d: {i: k for k, i in j["dimension"][d]["category"]["index"].items()} for d in ids}
    out = {}
    for flat, v in vals.items():
        n, coord = int(flat), {}
        for d, s in zip(reversed(ids), reversed(sizes)):
            coord[d] = idx[d][n % s]
            n //= s
        out.setdefault(coord[por], []).append([coord["time"], float(v)])
    for k in out:
        out[k].sort()
    if not out:
        raise ValueError("sin datos")
    return out


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    data = dict(prev)
    hoy = date.today()
    tareas = {
        "bce": lambda: ecb("FM/D.U2.EUR.4F.KR.DFR.LEV", f"{hoy.year - 6}-01-01", cambios=True),
        "eurusd": lambda: ecb("EXR/D.USD.EUR.SP00.A", (hoy - timedelta(days=760)).isoformat()),
        "bonos": lambda: {p: ecb(f"IRS/M.{p}.L.L40.CI.0000.EUR.N.Z", f"{hoy.year - 6}-01") for p in ["DE", "FR", "IT", "ES"]},
        # desde 2026 el HICP se publica con la clasificación ECOICOP 2 (dataset prc_hicp_minr; el viejo prc_hicp_manr quedó en 12/2025)
        "infl": lambda: eurostat("prc_hicp_minr", {"geo": PAISES, "coicop18": "TOTAL", "unit": "RCH_A", "sinceTimePeriod": f"{hoy.year - 6}-01"}),
        "infl_nucleo": lambda: eurostat("prc_hicp_minr", {"geo": "EA", "coicop18": "TOT_X_NRG_FOOD", "unit": "RCH_A", "sinceTimePeriod": f"{hoy.year - 6}-01"}),
        "infl_mes": lambda: eurostat("prc_hicp_minr", {"geo": "EA", "coicop18": "TOTAL", "unit": "RCH_M", "sinceTimePeriod": f"{hoy.year - 3}-01"}),
        # desempleo: zona euro del BCE (I9 = composición vigente), países de Eurostat
        "desemp": lambda: {"EA": ecb("LFSI/M.I9.S.UNEHRT.TOTAL0.15_74.T", f"{hoy.year - 6}-01"),
                           **eurostat("une_rt_m", {"geo": ["DE", "FR", "IT", "ES"], "age": "TOTAL", "sex": "T", "unit": "PC_ACT", "s_adj": "SA", "sinceTimePeriod": f"{hoy.year - 6}-01"})},
        "pbi_tri": lambda: eurostat("namq_10_gdp", {"geo": PAISES, "unit": "CLV_PCH_PRE", "s_adj": "SCA", "na_item": "B1GQ", "sinceTimePeriod": f"{hoy.year - 5}-Q1"}),
        "pbi_anual": lambda: eurostat("namq_10_gdp", {"geo": PAISES, "unit": "CLV_PCH_SM", "s_adj": "SCA", "na_item": "B1GQ", "sinceTimePeriod": f"{hoy.year - 5}-Q1"}),
    }
    def fresco(v, meses=5):
        ult = max((s[-1][0] for s in (v.values() if isinstance(v, dict) else [v]) if s), default="")
        lim = (hoy - timedelta(days=31 * meses)).isoformat()[:7]
        return ult[:7] >= lim if "-Q" not in ult else ult[:4] >= str(hoy.year - 1)
    for k, fn in tareas.items():
        try:
            v = fn()
            if not fresco(v, 8 if k.startswith("pbi") else 5):
                raise ValueError("los datos están atrasados (último: %s)" % max(s[-1][0] for s in (v.values() if isinstance(v, dict) else [v]) if s))
            data[k] = v
        except Exception as e:  # noqa: BLE001
            errores.append(f"{k}: {e}")
            if "atrasados" in str(e):
                data.pop(k, None)  # nunca mostrar datos viejos como actuales
        time.sleep(0.5)
    data["actualizado"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    data["errores"] = errores[:30]
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    resumen = {}
    for k, v in data.items():
        if isinstance(v, list):
            resumen[k] = f"{len(v)} hasta {v[-1][0]}"
        elif isinstance(v, dict) and k not in ("errores",):
            resumen[k] = {g: (s[-1][0] if s else None) for g, s in v.items()}
    print(resumen)
    for e in errores:
        print("ERROR", e)


if __name__ == "__main__":
    main()
