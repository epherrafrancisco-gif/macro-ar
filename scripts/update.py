"""Actualiza data.json de Macro AR con los datos más recientes.

Fuentes:
  - Ámbito (históricos de dólares y riesgo país)
  - BCRA, API de estadísticas monetarias v4.0 (reservas, mayorista, base,
    tasas, depósitos, inflación, expectativas y compras de divisas del BCRA;
    estas últimas se piden siempre desde el 1 de enero para los acumulados)
  - DolarApi (cripto y tarjeta del día)

Uso: python scripts/update.py [--dias N]
Revisa los últimos N días (10 por defecto), así se completan solos los días
que el BCRA publica con atraso o que una corrida anterior no pudo traer.
Nunca inventa datos: si una fuente falla, ese campo queda como estaba.
"""

import argparse
import json
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data.json"
TZ_AR = timezone(timedelta(hours=-3))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 MacroAR/1.0"

AMBITO = {
    # campo: (ruta, tipo)  tipo "cv" = compra/venta, "v" = un solo valor
    "blue": ("dolar/informal", "cv"),
    "oficial": ("dolar/oficial", "cv"),
    "mep": ("dolarrava/mep", "v"),
    "ccl": ("dolarrava/cl", "v"),
    "riesgo": ("riesgopais", "n"),
}
BCRA_DIARIO = {1: "reservas", 5: "mayorista", 15: "base", 7: "badlar", 44: "tamar", 12: "pf", 108: "depusd"}
BCRA_MENSUAL = {27: "infl", 28: "inflYoY", 29: "expect"}
# Series diarias que se piden desde el 1 de enero del año en curso (para los
# acumulados anuales). 78 = variación de reservas por compra de divisas en el
# MULC, en millones de USD (negativo = el BCRA vendió).
BCRA_ANUAL = {78: "compras"}

log_ok, log_err = [], []


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/plain,*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def num_ar(s):
    """'1.545,12' -> 1545.12"""
    return float(str(s).strip().replace(".", "").replace(",", "."))


def fecha_ambito(s):
    s = s.replace("\\/", "/").replace("-", "/")
    d, m, y = s.split("/")
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"


def es_habil(f):
    return date.fromisoformat(f).weekday() < 5


def ambito(desde, hasta):
    out = {}
    for campo, (ruta, tipo) in AMBITO.items():
        url = f"https://mercados.ambito.com//{ruta}/historico-general/{desde}/{hasta}"
        try:
            rows = get_json(url)
            n = 0
            for row in rows[1:]:  # la primera fila es el encabezado
                f = fecha_ambito(row[0])
                if f in out.get(campo, {}):
                    continue  # fecha repetida: quedarse con la primera (la más reciente)
                if tipo == "cv":
                    val = {"c": num_ar(row[1]), "v": num_ar(row[2])}
                elif tipo == "v":
                    val = {"v": num_ar(row[1])}
                else:
                    val = num_ar(row[1])
                out.setdefault(campo, {})[f] = val
                n += 1
            log_ok.append(f"Ámbito {campo}: {n} días")
        except Exception as e:  # noqa: BLE001
            log_err.append(f"Ámbito {campo}: {e}")
    return out


def bcra_puntos(var_id, desde, hasta):
    url = f"https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{var_id}?desde={desde}&hasta={hasta}&limit=1000"
    j = get_json(url)
    pts = {}
    for res in j.get("results", []):
        for p in res.get("detalle", []):
            pts[p["fecha"][:10]] = float(p["valor"])
    return pts


def bcra(desde, hasta, mensual_desde, anual_desde):
    diario, mensual = {}, {}
    for vid, campo in BCRA_ANUAL.items():
        try:
            pts = bcra_puntos(vid, anual_desde, hasta)
            for f, v in pts.items():
                diario.setdefault(campo, {})[f] = round(v, 2)
            log_ok.append(f"BCRA {campo}: {len(pts)} días desde {anual_desde}")
        except Exception as e:  # noqa: BLE001
            log_err.append(f"BCRA {campo} (id {vid}): {e}")
    for vid, campo in BCRA_DIARIO.items():
        try:
            pts = bcra_puntos(vid, desde, hasta)
            for f, v in pts.items():
                diario.setdefault(campo, {})[f] = {"v": round(v, 2)} if campo == "mayorista" else v
            log_ok.append(f"BCRA {campo}: {len(pts)} días")
        except Exception as e:  # noqa: BLE001
            log_err.append(f"BCRA {campo} (id {vid}): {e}")
    for vid, campo in BCRA_MENSUAL.items():
        try:
            pts = bcra_puntos(vid, mensual_desde, hasta)
            for f, v in pts.items():
                mensual.setdefault(f[:7], {})[campo] = v
            log_ok.append(f"BCRA {campo}: {len(pts)} meses")
        except Exception as e:  # noqa: BLE001
            log_err.append(f"BCRA {campo} (id {vid}): {e}")
    return diario, mensual


def dolarapi():
    out = {}
    try:
        for d in get_json("https://dolarapi.com/v1/dolares"):
            if d.get("casa") not in ("cripto", "tarjeta"):
                continue
            ts = datetime.fromisoformat(d["fechaActualizacion"].replace("Z", "+00:00")).astimezone(TZ_AR)
            f = ts.date().isoformat()
            if not es_habil(f):
                continue
            out.setdefault(d["casa"], {})[f] = {"c": float(d["compra"]), "v": float(d["venta"])}
        log_ok.append(f"DolarApi: {', '.join(f'{k} {list(v)}' for k, v in out.items()) or 'sin datos de día hábil'}")
    except Exception as e:  # noqa: BLE001
        log_err.append(f"DolarApi: {e}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=10)
    args = ap.parse_args()

    hoy = datetime.now(TZ_AR).date()
    desde = (hoy - timedelta(days=args.dias)).isoformat()
    hasta = hoy.isoformat()
    mensual_desde = (hoy - timedelta(days=120)).isoformat()
    anual_desde = min(date(hoy.year, 1, 1), hoy - timedelta(days=args.dias)).isoformat()
    print(f"Ventana: {desde} a {hasta}")

    nuevos = {}  # fecha -> {campo: valor}
    amb = ambito(desde, hasta)
    bd, bm = bcra(desde, hasta, mensual_desde, anual_desde)
    dapi = dolarapi()

    # Días hábiles con dato oficial: sirven para descartar valores que Ámbito
    # repite en feriados para el MEP y el CCL.
    dias_mercado = set(amb.get("oficial", {})) | set(bd.get("mayorista", {}))

    for fuente in (amb, bd, dapi):
        for campo, porfecha in fuente.items():
            for f, val in porfecha.items():
                if not es_habil(f):
                    continue
                if campo in ("mep", "ccl") and dias_mercado and f not in dias_mercado:
                    continue
                nuevos.setdefault(f, {})[campo] = val

    if not log_ok:
        print("Todas las fuentes fallaron:\n  " + "\n  ".join(log_err))
        sys.exit(1)

    data = json.loads(DATA.read_text(encoding="utf-8"))
    diario = {d["fecha"]: d for d in data.get("diario", [])}
    mensual = {m["mes"]: m for m in data.get("mensual", [])}

    agregados, actualizados = [], []
    for f, campos in sorted(nuevos.items()):
        if f in diario:
            antes = dict(diario[f])
            diario[f].update(campos)
            if diario[f] != antes:
                actualizados.append(f)
        else:
            diario[f] = {"fecha": f, **campos}
            agregados.append(f)
    for mes, campos in bm.items():
        if mes in mensual:
            mensual[mes].update(campos)
        else:
            mensual[mes] = {"mes": mes, **campos}

    data["diario"] = [diario[k] for k in sorted(diario)]
    data["mensual"] = [mensual[k] for k in sorted(mensual)]
    data["actualizado"] = data["diario"][-1]["fecha"]
    DATA.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    json.loads(DATA.read_text(encoding="utf-8"))  # verificar que quedó un JSON válido

    print("Fuentes OK:\n  " + "\n  ".join(log_ok))
    if log_err:
        print("Fuentes con error:\n  " + "\n  ".join(log_err))
    resumen = lambda l: (f"{len(l)} ({l[0]} a {l[-1]})" if len(l) > 5 else str(l)) if l else "ninguno"
    print(f"Días agregados: {resumen(agregados)}")
    print(f"Días actualizados: {resumen(actualizados)}")
    print(f"Último dato: {data['actualizado']}")


if __name__ == "__main__":
    main()
