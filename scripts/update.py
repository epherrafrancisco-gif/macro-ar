"""Actualiza data.json de Macro AR con los datos más recientes.

Fuentes:
  - Ámbito (históricos de dólares y riesgo país)
  - BCRA, API de estadísticas monetarias v4.0 (reservas, mayorista, base,
    tasas, depósitos, inflación, expectativas y compras de divisas del BCRA;
    estas últimas se piden siempre desde el 1 de enero para los acumulados)
  - DolarApi (cripto y tarjeta del día)
  - FRED (inflación de EE.UU., para el dólar a precios de hoy)

Uso: python scripts/update.py [--dias N] [--historia]
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
    "merval": ("indice/.merv", "idx"),  # columnas: Fecha, Apertura, Último, ...; se pide desde el 1/1
}
AMBITO_LARGO = {"merval"}
BCRA_DIARIO = {1: "reservas", 5: "mayorista", 15: "base", 7: "badlar", 44: "tamar", 12: "pf", 108: "depusd"}
BCRA_MENSUAL = {27: "infl", 28: "inflYoY", 29: "expect"}
# Series diarias que se piden desde el 1 de enero del año en curso (para los
# acumulados anuales). 78 = variación de reservas por compra de divisas en el
# MULC, en millones de USD (negativo = el BCRA vendió).
BCRA_ANUAL = {78: "compras", 158: "bopreal"}
# Series del BCRA que se guardan por mes (desde HISTORIA): "prom" = promedio del
# mes, "fin" = último dato del mes. Sirven para los agregados en términos reales
# y en % del PBI, y para la historia de los pasivos remunerados del BCRA.
HISTORIA = "2023-01-01"
BCRA_MENSUALIZAR = {
    15: ("base", "prom"), 109: ("m2", "prom"), 197: ("m2t", "prom"), 30: ("cer", "prom"),
    155: ("leliq", "fin"), 152: ("pases", "fin"), 196: ("lefi", "fin"),
}
# API de series de datos.gob.ar (INDEC y Hacienda).
DATOSGOB_MENSUAL = {
    "452.3_RESULTADO_RIO_0_M_18_54": "prim",   # resultado primario SPN, millones $
    "452.3_RESULTADO_ERO_0_M_20_25": "fin",    # resultado financiero SPN, millones $
    "74.3_IET_0_M_16": "expo",                 # exportaciones, MUSD
    "74.3_IIT_0_M_25": "impo",                 # importaciones, MUSD
    "74.3_ISC_0_M_19": "saldo",                # saldo comercial, MUSD
}
DATOSGOB_TRIM = {"166.2_PPIB_0_0_3": "pib"}  # PBI a precios corrientes, millones $ (valor anualizado)
# Historia larga de dólares para "Dólar a precios de hoy" (clave "historico" de
# data.json, una fila por mes con promedios). Arranca en 2017 porque antes el IPC
# oficial (y por lo tanto el CER) estaba manipulado. La primera vez (o con
# --historia) se baja todo desde HIST_DOLAR; después, solo desde el mes anterior.
HIST_DOLAR = "2017-01-01"
HIST_AMBITO = {"ofi": "dolar/oficial", "blue": "dolar/informal", "mep": "dolarrava/mep", "ccl": "dolarrava/cl"}
HIST_BCRA = {5: "may", 30: "cer"}
# Inflación de EE.UU. (CPI-U sin desestacionalizar, BLS vía FRED, CSV sin clave).
FRED_CPI = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS&cosd=2016-12-01"

log_ok, log_err = [], []


def get_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/csv,text/plain,*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def get_json(url):
    return json.loads(get_text(url))


def num_ar(s):
    """'1.545,12' -> 1545.12"""
    return float(str(s).strip().replace(".", "").replace(",", "."))


def fecha_ambito(s):
    s = s.replace("\\/", "/").replace("-", "/")
    d, m, y = s.split("/")
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"


def es_habil(f):
    return date.fromisoformat(f).weekday() < 5


def ambito(desde, hasta, desde_largo):
    out = {}
    for campo, (ruta, tipo) in AMBITO.items():
        d0 = desde_largo if campo in AMBITO_LARGO else desde
        url = f"https://mercados.ambito.com//{ruta}/historico-general/{d0}/{hasta}"
        try:
            rows = get_json(url)
            n = 0
            for row in rows[1:]:  # la primera fila es el encabezado
                try:
                    f = fecha_ambito(row[0])
                except ValueError:
                    continue
                if f in out.get(campo, {}):
                    continue  # fecha repetida: quedarse con la primera (la más reciente)
                if tipo == "cv":
                    val = {"c": num_ar(row[1]), "v": num_ar(row[2])}
                elif tipo == "v":
                    val = {"v": num_ar(row[1])}
                elif tipo == "idx":
                    val = num_ar(row[2])
                else:
                    val = num_ar(row[1])
                out.setdefault(campo, {})[f] = val
                n += 1
            log_ok.append(f"Ámbito {campo}: {n} días")
        except Exception as e:  # noqa: BLE001
            log_err.append(f"Ámbito {campo}: {e}")
    return out


def bcra_puntos(var_id, desde, hasta):
    url = f"https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{var_id}?desde={desde}&hasta={hasta}&limit=3000"
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
    for vid, (campo, modo) in BCRA_MENSUALIZAR.items():
        try:
            pts = bcra_puntos(vid, HISTORIA, hasta)
            pormes = {}
            for f in sorted(pts):
                pormes.setdefault(f[:7], []).append(pts[f])
            for mes, vals in pormes.items():
                v = sum(vals) / len(vals) if modo == "prom" else vals[-1]
                mensual.setdefault(mes, {})[campo] = round(v, 4 if campo == "cer" else 1)
            log_ok.append(f"BCRA {campo} mensual: {len(pormes)} meses")
        except Exception as e:  # noqa: BLE001
            log_err.append(f"BCRA {campo} mensual (id {vid}): {e}")
    return diario, mensual


def datosgob(series, desde):
    """Devuelve {fecha: {campo: valor}} para varias series de la misma frecuencia."""
    ids = list(series)
    url = (f"https://apis.datos.gob.ar/series/api/series/?ids={','.join(ids)}"
           f"&start_date={desde}&limit=1000&format=json")
    j = get_json(url)
    out = {}
    for row in j.get("data", []):
        f = row[0][:10]
        for i, sid in enumerate(ids, start=1):
            if i < len(row) and row[i] is not None:
                out.setdefault(f, {})[series[sid]] = round(float(row[i]), 1)
    return out


def datos_gob_ar():
    mensual, trimestral = {}, {}
    try:
        for f, campos in datosgob(DATOSGOB_MENSUAL, HISTORIA).items():
            mensual.setdefault(f[:7], {}).update(campos)
        log_ok.append(f"datos.gob.ar fiscal y comercio: {len(mensual)} meses")
    except Exception as e:  # noqa: BLE001
        log_err.append(f"datos.gob.ar fiscal y comercio: {e}")
    try:
        for f, campos in datosgob(DATOSGOB_TRIM, "2022-01-01").items():
            trimestral.setdefault(f[:7], {}).update(campos)
        log_ok.append(f"datos.gob.ar PBI: {len(trimestral)} trimestres")
    except Exception as e:  # noqa: BLE001
        log_err.append(f"datos.gob.ar PBI: {e}")
    return mensual, trimestral


def tramos(desde, hasta):
    """Parte [desde, hasta] en tramos de a un año (las APIs cortan las respuestas largas)."""
    d0, fin = date.fromisoformat(desde), date.fromisoformat(hasta)
    while d0 <= fin:
        d1 = min(date(d0.year, 12, 31), fin)
        yield d0, d1
        d0 = d1 + timedelta(days=1)


def historico(previo, hoy, forzar=False):
    """Promedios mensuales de dólares, CER y CPI de EE.UU. desde HIST_DOLAR.

    Devuelve la lista nueva para data["historico"]. Si una fuente falla, sus
    campos quedan como estaban."""
    meses = {h["mes"]: dict(h) for h in previo}
    hasta = hoy.isoformat()
    # Desde el 1° del mes anterior: así se recalculan enteros este mes y el anterior.
    reciente = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1).isoformat()

    def desde_de(campo):
        """Historia completa si el campo todavía no tiene datos de antes de 2019."""
        tiene = any(campo in h for m, h in meses.items() if m < "2019-01")
        return reciente if (tiene and not forzar) else HIST_DOLAR

    diario, desdes = {}, {}
    for campo, ruta in HIST_AMBITO.items():
        desde = desdes[campo] = desde_de(campo)
        try:
            pts = {}
            for d0, d1 in tramos(desde, hasta):
                url = f"https://mercados.ambito.com//{ruta}/historico-general/{d0.isoformat()}/{d1.isoformat()}"
                for row in get_json(url)[1:]:
                    try:
                        f = fecha_ambito(row[0])
                        v = num_ar(row[2] if campo in ("ofi", "blue") else row[1])
                    except (ValueError, IndexError):
                        continue
                    if es_habil(f) and f not in pts and v > 0:
                        pts[f] = v
            diario[campo] = pts
            log_ok.append(f"Historia {campo}: {len(pts)} días desde {desde}")
        except Exception as e:  # noqa: BLE001
            log_err.append(f"Historia {campo}: {e}")
    for vid, campo in HIST_BCRA.items():
        desde = desdes[campo] = desde_de(campo)
        try:
            pts = {}
            for d0, d1 in tramos(desde, hasta):
                pts.update(bcra_puntos(vid, d0.isoformat(), d1.isoformat()))
            if campo == "may":
                pts = {f: v for f, v in pts.items() if es_habil(f)}
            diario[campo] = pts
            log_ok.append(f"Historia {campo}: {len(pts)} días desde {desde}")
        except Exception as e:  # noqa: BLE001
            log_err.append(f"Historia {campo} (id {vid}): {e}")
    # Feriados: Ámbito repite el último valor del MEP, CCL y blue; quedarse con
    # los días en que hubo oficial o mayorista.
    habiles = set(diario.get("ofi", {})) | set(diario.get("may", {}))
    for campo in ("mep", "ccl", "blue"):
        if campo in diario and habiles:
            diario[campo] = {f: v for f, v in diario[campo].items() if f in habiles}
    for campo, pts in diario.items():
        pormes = {}
        for f, v in pts.items():
            if f >= desdes[campo]:
                pormes.setdefault(f[:7], []).append(v)
        for mes, vals in pormes.items():
            meses.setdefault(mes, {"mes": mes})[campo] = round(sum(vals) / len(vals), 4 if campo == "cer" else 2)
    try:
        n = 0
        for linea in get_text(FRED_CPI).strip().splitlines()[1:]:
            partes = linea.strip().split(",")
            if len(partes) < 2:
                continue
            try:
                v = float(partes[1])
            except ValueError:  # FRED marca con "." los meses sin dato
                continue
            mes = partes[0][:7]
            if mes >= HIST_DOLAR[:7]:
                meses.setdefault(mes, {"mes": mes})["cpi"] = round(v, 3)
                n += 1
        if not n:
            raise ValueError("CSV sin datos")
        log_ok.append(f"CPI EE.UU. (FRED): {n} meses")
    except Exception as e:  # noqa: BLE001
        log_err.append(f"CPI EE.UU. (FRED): {e}")
    return [meses[k] for k in sorted(meses) if k <= hasta[:7]]


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
    ap.add_argument("--historia", action="store_true", help="volver a bajar toda la historia de dólares desde 2017")
    args = ap.parse_args()

    hoy = datetime.now(TZ_AR).date()
    desde = (hoy - timedelta(days=args.dias)).isoformat()
    hasta = hoy.isoformat()
    mensual_desde = (hoy - timedelta(days=120)).isoformat()
    anual_desde = min(date(hoy.year, 1, 1), hoy - timedelta(days=args.dias)).isoformat()
    print(f"Ventana: {desde} a {hasta}")

    nuevos = {}  # fecha -> {campo: valor}
    amb = ambito(desde, hasta, anual_desde)
    bd, bm = bcra(desde, hasta, mensual_desde, anual_desde)
    dapi = dolarapi()
    gm, gt = datos_gob_ar()
    for mes, campos in gm.items():
        bm.setdefault(mes, {}).update(campos)

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
    hist = historico(data.get("historico", []), hoy, args.historia)
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

    trimestral = {t["trim"]: t for t in data.get("trimestral", [])}
    for trim, campos in gt.items():
        trimestral.setdefault(trim, {"trim": trim}).update(campos)

    data["diario"] = [diario[k] for k in sorted(diario)]
    data["mensual"] = [mensual[k] for k in sorted(mensual)]
    data["trimestral"] = [trimestral[k] for k in sorted(trimestral)]
    data["historico"] = hist
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
