"""Base común para secciones de país armadas con fuentes internacionales (BIS, OCDE y Banco Mundial), sin clave.

La usan scripts/india.py y scripts/arabia.py. Nunca inventa datos: si una serie falla queda la anterior y se anota en
"errores"; si viene atrasada, se saca en vez de mostrarla como actual.
"""

import csv
import io
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
OECD = "https://sdmx.oecd.org/public/rest/data/"


def get(url, accept="*/*", tries=3, timeout=90):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            # 404 (serie que no existe) o 429 (la OCDE corta por pedir mucho): no tiene sentido insistir
            if "404" in str(e) or "429" in str(e):
                break
            time.sleep(3 * (i + 1))
    raise last


def filas(txt):
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
    pts = sorted(p for p in pts if "-Q" in p[0] or p[0] <= hoy)
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


OECD_CORTADA = False  # si la OCDE da 429, no se le pide más en esta corrida (si no, el workflow se pasa de tiempo)


def oecd(flujo, clave, desde):
    global OECD_CORTADA
    if OECD_CORTADA:
        raise ValueError("la OCDE cortó por exceso de pedidos (429); queda el dato anterior")
    try:
        return filas(get(f"{OECD}{flujo}/{clave}?startPeriod={desde}&format=csvfile", "text/csv"))
    except Exception as e:  # noqa: BLE001
        if "429" in str(e):
            OECD_CORTADA = True
        raise


def banco_mundial(pais, indicador, desde=2000):
    j = json.loads(get(f"https://api.worldbank.org/v2/country/{pais}/indicator/{indicador}?format=json&per_page=200&date={desde}:{date.today().year}", "application/json"))
    pts = sorted([r["date"], round(float(r["value"]), 3)] for r in (j[1] if isinstance(j, list) and len(j) > 1 else []) or [] if r.get("value") is not None)
    if not pts:
        raise ValueError("sin datos")
    return pts


def fresco(pts, meses):
    hoy = date.today()
    ult = pts[-1][0]
    if "-Q" in ult:
        fin = date(int(ult[:4]), int(ult[-1]) * 3, 28)
        return (hoy - fin).days <= 31 * meses
    if len(ult) == 4:
        return (hoy - date(int(ult), 12, 31)).days <= 31 * meses
    lim = (hoy - timedelta(days=31 * meses)).isoformat()
    return ult[:7] >= lim[:7] if len(ult) == 7 else ult >= lim


def armar(out_path, bis2, moneda, oecd3, wb3, extra=None):
    """Arma el JSON de un país: tasa, moneda, inflación (BIS), desempleo y PBI (OCDE; si no, Banco Mundial anual)."""
    errores = []
    prev = {}
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    data = dict(prev)
    hoy = date.today()
    oecd_ok = bool(oecd3)  # países que no están en la OCDE: se pasa None y no se le pide nada
    tareas = {
        "tasa": (lambda: solo_cambios(bis("WS_CBPOL", f"D.{bis2}", f"{hoy.year - 8}-01-01")), 1),
        "usd": (lambda: bis("WS_XRU", f"D.{bis2}.{moneda}.A", (hoy - timedelta(days=760)).isoformat()), 1),
        "infl": (lambda: bis("WS_LONG_CPI", f"M.{bis2}.771", f"{hoy.year - 6}-01"), 4),
        "ipc_ind": (lambda: bis("WS_LONG_CPI", f"M.{bis2}.628", f"{hoy.year - 4}-01"), 4),
        "desemp": (lambda: oecd("OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0", f"{oecd3}..._Z.Y._T.Y_GE15..M", f"{hoy.year - 6}-01"), 4),
        "pbi_tri": (lambda: oecd("OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1", f"Q..{oecd3}.S1..B1GQ......G1.", f"{hoy.year - 5}-Q1"), 8),
        "pbi_anual": (lambda: oecd("OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1", f"Q..{oecd3}.S1..B1GQ......GY.", f"{hoy.year - 5}-Q1"), 8),
        # anuales del Banco Mundial (respaldo cuando la OCDE no tiene el dato mensual o trimestral)
        "desemp_anual": (lambda: banco_mundial(wb3, "SL.UEM.TOTL.ZS"), 30),
        "crec_anual": (lambda: banco_mundial(wb3, "NY.GDP.MKTP.KD.ZG"), 30),
    }
    if not oecd_ok:
        for k in ("desemp", "pbi_tri", "pbi_anual"):
            tareas.pop(k, None)
    tareas.update(extra or {})
    for k, (fn, meses) in tareas.items():
        try:
            v = fn()
            if not fresco(v, meses):
                raise ValueError(f"los datos están atrasados (último: {v[-1][0]})")
            data[k] = v
        except Exception as e:  # noqa: BLE001
            errores.append(f"{k}: {e}")
            if "atrasados" in str(e):
                data.pop(k, None)
        time.sleep(0.5)
    data["actualizado"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    data["errores"] = errores[:30]
    out_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print({k: f"{len(v)} hasta {v[-1][0]}" for k, v in data.items() if isinstance(v, list) and v and k != "errores"})
    for e in errores:
        print("ERROR", e)
