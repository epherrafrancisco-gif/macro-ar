"""Arma peru.json para la sección Perú de Pulso Macro.

Fuente oficial y gratuita, sin clave: la API de estadísticas del Banco Central de Reserva del Perú (BCRP,
estadisticas.bcrp.gob.pe): tasa de referencia, inflación de Lima (12 meses y del mes), PBI mensual (variación
interanual), desempleo de Lima Metropolitana y tipo de cambio diario (soles por dólar).

Uso: python scripts/peru.py
Nunca inventa datos: si una serie falla, queda la que había y se anota en "errores". Si una serie viene atrasada,
se saca en vez de mostrarla como actual.
"""

import json
import re
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "peru.json"
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/"
MES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12}
errores = []


def get(url, tries=3, timeout=60):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise last


def periodo(txt):
    """'Sep.2026' → '2026-09'; '01.Oct.26' → '2026-10-01'."""
    t = txt.strip().lower().replace(" ", "")
    m = re.fullmatch(r"([a-z]{3})\.(\d{4})", t)
    if m:
        return f"{m.group(2)}-{MES[m.group(1)]:02d}"
    m = re.fullmatch(r"(\d{1,2})\.([a-z]{3})\.(\d{2})", t)
    if m:
        return f"20{m.group(3)}-{MES[m.group(2)]:02d}-{int(m.group(1)):02d}"
    raise ValueError(f"período raro: {txt}")


def bcrp(serie, desde, hasta):
    j = json.loads(get(f"{API}{serie}/json/{desde}/{hasta}"))
    pts = []
    for p in j.get("periods") or []:
        v = (p.get("values") or [None])[0]
        try:
            pts.append([periodo(p["name"]), float(v)])
        except (TypeError, ValueError, KeyError):
            continue  # "n.d." = sin dato todavía
    hoy = date.today().isoformat()
    pts = sorted(p for p in pts if p[0] <= hoy)
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


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    data = dict(prev)
    hoy = date.today()
    m6, m3 = f"{hoy.year - 6}-1", f"{hoy.year - 3}-1"
    mh = f"{hoy.year}-{hoy.month}"
    d2 = (hoy - timedelta(days=760)).isoformat()
    tareas = {
        "tasa": (lambda: solo_cambios(bcrp("PD04722MM", m6, mh)), 2),
        "infl": (lambda: bcrp("PN01273PM", m6, mh), 3),
        "infl_mes": (lambda: bcrp("PN01271PM", m3, mh), 3),
        "pbi": (lambda: bcrp("PN01728AM", m6, mh), 5),
        "desemp": (lambda: bcrp("PN38063GM", m6, mh), 4),
        "usdpen": (lambda: bcrp("PD04640PD", d2, hoy.isoformat()), 1),
    }

    def fresco(pts, meses):
        ult = pts[-1][0]
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
