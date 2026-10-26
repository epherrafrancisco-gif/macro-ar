"""Arma reinounido.json para la sección Reino Unido de Pulso Macro.

Fuentes oficiales y gratuitas, sin clave:
  - BIS (stats.bis.org): tasa del Banco de Inglaterra (diaria), libras por dólar (diario) e inflación
    (IPC de la ONS: variación en 12 meses e índice para la del mes).
  - OCDE (sdmx.oecd.org): desempleo mensual y PBI trimestral (contra el trimestre anterior y contra un año atrás).

Uso: python scripts/reinounido.py
Nunca inventa datos: si una serie falla, queda la que había y se anota en "errores". Si una serie viene atrasada,
se saca en vez de mostrarla como actual.
"""

import csv
import io
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reinounido.json"
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
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
        "tasa": (lambda: solo_cambios(bis("WS_CBPOL", "D.GB", f"{hoy.year - 6}-01-01")), 1),
        "usdgbp": (lambda: bis("WS_XRU", "D.GB.GBP.A", (hoy - timedelta(days=760)).isoformat()), 1),
        "infl": (lambda: bis("WS_LONG_CPI", "M.GB.771", f"{hoy.year - 6}-01"), 4),
        "ipc_ind": (lambda: bis("WS_LONG_CPI", "M.GB.628", f"{hoy.year - 4}-01"), 4),
        "desemp": (lambda: oecd("OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0", "GBR..._Z.Y._T.Y_GE15..M", f"{hoy.year - 6}-01"), 4),
        "pbi_tri": (lambda: oecd("OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1", "Q..GBR.S1..B1GQ......G1.", f"{hoy.year - 5}-Q1"), 8),
        "pbi_anual": (lambda: oecd("OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1", "Q..GBR.S1..B1GQ......GY.", f"{hoy.year - 5}-Q1"), 8),
    }
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
