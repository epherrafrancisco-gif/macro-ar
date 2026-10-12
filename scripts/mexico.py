"""Arma mexico.json para la sección México de Pulso Macro.

Fuentes oficiales y gratuitas, sin clave:
  - BIS (stats.bis.org): tasa objetivo de Banxico (diaria), peso mexicano contra el dólar (diario) e inflación
    (precios al consumidor del INEGI: variación en 12 meses e índice para la del mes).
  - OCDE (sdmx.oecd.org): desempleo mensual y PBI trimestral (contra el trimestre anterior y contra un año atrás).
Si existe la variable BANXICO_TOKEN (clave gratis del SIE de Banxico), suma reservas, remesas y dólar FIX.

Uso: python scripts/mexico.py
Nunca inventa datos: si una serie falla, queda la que había y se anota en "errores". Si una serie viene atrasada,
se saca en vez de mostrarla como actual.
"""

import csv
import io
import json
import os
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mexico.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
OECD = "https://sdmx.oecd.org/public/rest/data/"
errores = []


def get(url, accept="*/*", tries=3, timeout=90):
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


def filas(txt):
    """CSV (BIS u OCDE) → [[periodo, valor], ...] ordenado, sin fechas futuras."""
    hoy = date.today().isoformat()
    pts = []
    for r in csv.DictReader(io.StringIO(txt)):
        t, v = r.get("TIME_PERIOD"), r.get("OBS_VALUE")
        if not t or v in (None, "", "NaN"):
            continue
        try:
            pts.append([t, float(v)])
        except ValueError:
            continue
    pts = sorted(p for p in pts if "-Q" in p[0] or p[0] <= hoy)  # los trimestres ("2026-Q2") no se comparan con fechas
    if not pts:
        raise ValueError("sin datos")
    return pts


def solo_cambios(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if p[1] != out[-1][1]:
            out.append(p)
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def bis(flujo, clave, desde):
    return filas(get(f"https://stats.bis.org/api/v1/data/{flujo}/{clave}/all?startPeriod={desde}&format=csv", "text/csv"))


def oecd(flujo, clave, desde):
    return filas(get(f"{OECD}{flujo}/{clave}?startPeriod={desde}&format=csvfile", "text/csv"))


def banxico(serie, desde, token):
    """Serie del SIE de Banxico (necesita clave). Fechas dd/mm/aaaa → aaaa-mm-dd."""
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/{desde}/{date.today().isoformat()}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Bmx-Token": token})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.loads(r.read().decode("utf-8"))
    pts = []
    for d in j["bmx"]["series"][0].get("datos") or []:
        try:
            dd, mm, yy = d["fecha"].split("/")
            pts.append([f"{yy}-{mm}-{dd}", float(d["dato"].replace(",", ""))])
        except (ValueError, KeyError):
            continue
    if not pts:
        raise ValueError("sin datos")
    return sorted(pts)


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
        "tasa": (lambda: solo_cambios(bis("WS_CBPOL", "D.MX", f"{hoy.year - 6}-01-01")), 1),
        "usdmxn": (lambda: bis("WS_XRU", "D.MX.MXN.A", (hoy - timedelta(days=760)).isoformat()), 1),
        "infl": (lambda: bis("WS_LONG_CPI", "M.MX.771", f"{hoy.year - 6}-01"), 4),
        "ipc_ind": (lambda: bis("WS_LONG_CPI", "M.MX.628", f"{hoy.year - 4}-01"), 4),
        "desemp": (lambda: oecd("OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0", "MEX..._Z.Y._T.Y_GE15..M", f"{hoy.year - 6}-01"), 4),
        "pbi_tri": (lambda: oecd("OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1", "Q..MEX.S1..B1GQ......G1.", f"{hoy.year - 5}-Q1"), 8),
        "pbi_anual": (lambda: oecd("OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1", "Q..MEX.S1..B1GQ......GY.", f"{hoy.year - 5}-Q1"), 8),
    }
    token = os.environ.get("BANXICO_TOKEN", "").strip()
    if token:
        d4 = f"{hoy.year - 4}-01-01"
        tareas.update({
            "fix": (lambda: banxico("SF43718", (hoy - timedelta(days=760)).isoformat(), token), 1),
            "reservas": (lambda: banxico("SF43707", d4, token), 1),
            "remesas": (lambda: banxico("SE27803", f"{hoy.year - 6}-01-01", token), 4),
        })

    def fresco(pts, meses):
        ult = pts[-1][0]
        if "-Q" in ult:  # trimestral: aceptar hasta `meses` meses después del fin del trimestre
            y, q = int(ult[:4]), int(ult[-1])
            fin = date(y, q * 3, 28)
            return (hoy - fin).days <= 31 * meses
        lim = (hoy - timedelta(days=31 * meses)).isoformat()
        return ult[:7] >= lim[:7] if len(ult) == 7 else ult >= lim

    for k, (fn, meses) in tareas.items():
        try:
            v = fn()
            if not fresco(v, meses):
                raise ValueError(f"los datos están atrasados (último: {v[-1][0]})")
            data[k] = v
        except Exception as e:  # noqa: BLE001
            errores.append(f"{k}: {e}")
            if "atrasados" in str(e):
                data.pop(k, None)  # nunca mostrar datos viejos como actuales
        time.sleep(0.5)
    data["actualizado"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    data["errores"] = errores[:30]
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print({k: f"{len(v)} hasta {v[-1][0]}" for k, v in data.items() if isinstance(v, list) and v and k != "errores"})
    for e in errores:
        print("ERROR", e)


if __name__ == "__main__":
    main()
