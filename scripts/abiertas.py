"""Datos de mercado de fuentes abiertas, que permiten reutilizarlos (también con fines comerciales) citando la fuente.
Reemplazan a CNBC donde se puede (plan legal del 26/10/2026; ver "Licencias y créditos" en Sobre Pulso Macro).

- Monedas: Banco Central Europeo (tipos de cambio de referencia diarios, ~30 monedas; uso libre citando al BCE) y, para las
  que el BCE no publica, el BIS (tipo de cambio diario de cada banco central; llega con 1 a 3 semanas de atraso).
  Peso argentino, colombiano y sol se completan al día con el BCRA (mayorista de data.json), la TRM de datos.gov.co y el
  BCRP. El resto puede quedar atrasado: la página muestra la fecha en vez de "hoy".
  Las cotizaciones se devuelven con la MISMA convención que usaba CNBC, así la página no cambia: EUR, GBP, AUD y NZD en
  dólares por unidad; el resto en unidades por dólar; EURPLN y EURCHF en monedas por euro.
- Petróleo y gas: EIA de EE.UU. (precios spot diarios, dominio público; se publican con unos días de atraso).
- Tasas de EE.UU.: Departamento del Tesoro (curva diaria, dominio público).
"""
import csv
import io
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

UA = "pulsomacro.com.ar (contacto@pulsomacro.com.ar)"
errores = []

# Monedas del BCE (código → se cotiza en dólares por unidad, como CNBC)
BCE = ["USD", "JPY", "CZK", "DKK", "GBP", "HUF", "PLN", "RON", "SEK", "CHF", "ISK", "NOK", "TRY", "AUD", "BRL", "CAD",
       "CNY", "HKD", "IDR", "ILS", "INR", "KRW", "MXN", "MYR", "NZD", "PHP", "SGD", "THB", "ZAR"]
USD_POR_UNIDAD = {"EUR", "GBP", "AUD", "NZD"}
# Monedas que el BCE no publica: tipo de cambio diario del BIS (código de país del BIS)
BIS_FX = {"ARS": "AR", "CLP": "CL", "COP": "CO", "PEN": "PE", "UYU": "UY", "RSD": "RS", "RUB": "RU", "MAD": "MA", "MKD": "MK", "SAR": "SA"}
FUENTE_AL_DIA = {}  # moneda → fuente oficial con la que se completó lo que el BIS todavía no tiene
NOMBRES = {"EUR": "Euro", "GBP": "Libra esterlina", "AUD": "Dólar australiano", "NZD": "Dólar neozelandés"}


def get(url, accept="*/*", tries=3, timeout=60):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            if "404" in str(e):
                break
            time.sleep(3 * (i + 1))
    raise last


def _csv(txt):
    return list(csv.DictReader(io.StringIO(txt.decode("utf-8", "replace") if isinstance(txt, bytes) else txt)))


def fx_hist(dias=800):
    """{moneda: [[fecha, valor], ...]} con la convención de CNBC. Un solo pedido al BCE para todas sus monedas."""
    desde = (date.today() - timedelta(days=dias)).isoformat()
    hoy = date.today().isoformat()
    out = {}
    try:
        filas = _csv(get(f"https://data-api.ecb.europa.eu/service/data/EXR/D.{'+'.join(BCE)}.EUR.SP00.A?format=csvdata&startPeriod={desde}", "text/csv"))
        por = {}  # fecha → {moneda: unidades por euro}
        for r in filas:
            v, t, c = r.get("OBS_VALUE"), r.get("TIME_PERIOD"), r.get("CURRENCY")
            if v in (None, "", "NaN") or not t or t > hoy:
                continue
            por.setdefault(t, {})[c] = float(v)
        for t in sorted(por):
            x = por[t]
            usd = x.get("USD")
            if not usd:
                continue
            out.setdefault("EUR", []).append([t, round(usd, 6)])           # dólares por euro
            out.setdefault("EURPLN", []).append([t, round(x["PLN"], 6)]) if "PLN" in x else None
            out.setdefault("EURCHF", []).append([t, round(x["CHF"], 6)]) if "CHF" in x else None
            for c, v in x.items():
                if c == "USD":
                    continue
                val = usd / v if c in USD_POR_UNIDAD else v / usd       # dólares por unidad, o unidades por dólar
                out.setdefault(c, []).append([t, round(val, 6)])
    except Exception as e:  # noqa: BLE001
        errores.append(f"BCE monedas: {e}")
    for c, pais in BIS_FX.items():
        try:
            filas = _csv(get(f"https://stats.bis.org/api/v1/data/WS_XRU/D.{pais}.{c}.A/all?startPeriod={desde}&format=csv", "text/csv"))
            pts = sorted([r["TIME_PERIOD"], round(float(r["OBS_VALUE"]), 6)] for r in filas
                         if r.get("OBS_VALUE") not in (None, "", "NaN") and r.get("TIME_PERIOD", "") <= hoy)
            if pts:
                out[c] = pts
        except Exception as e:  # noqa: BLE001
            errores.append(f"BIS moneda {c}: {e}")
        time.sleep(0.3)
    # El BIS llega con 1 a 3 semanas de atraso: donde hay una fuente oficial abierta al día, se completa con ella
    for c, fn in (("ARS", _ars_bcra), ("COP", _cop_trm), ("PEN", _pen_bcrp)):
        try:
            nuevos = fn(desde, hoy)
            if nuevos:
                FUENTE_AL_DIA[c] = {"ARS": "BCRA", "COP": "Superfinanciera de Colombia", "PEN": "BCRP"}[c]
                m = dict(out.get(c, []))
                m.update(nuevos)
                out[c] = sorted([t, v] for t, v in m.items())
        except Exception as e:  # noqa: BLE001
            errores.append(f"moneda {c} al día: {e}")
    return out


def _ars_bcra(desde, hoy):
    """Mayorista del BCRA (Comunicación A 3500) que ya guarda data.json (scripts/update.py)."""
    d = json.loads((Path(__file__).resolve().parent.parent / "data.json").read_text(encoding="utf-8"))
    return {r["fecha"]: float(r["mayorista"]["v"]) for r in d.get("diario", [])
            if desde <= r.get("fecha", "") <= hoy and (r.get("mayorista") or {}).get("v")}


def _cop_trm(desde, hoy):
    """TRM de la Superintendencia Financiera de Colombia (datos.gov.co, datos abiertos). La del finde vale desde el sábado."""
    filas = json.loads(get("https://www.datos.gov.co/resource/32sa-8pi3.json?$order=vigenciadesde%20DESC&$limit=60", "application/json"))
    return {r["vigenciadesde"][:10]: round(float(r["valor"]), 2) for r in filas
            if r.get("valor") and desde <= r.get("vigenciadesde", "")[:10] <= hoy}


MESES_BCRP = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6, "Jul": 7, "Ago": 8, "Set": 9, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12}


def _pen_bcrp(desde, hoy):
    """Soles por dólar del BCRP (venta, sistema bancario; períodos "22.Oct.26", "n.d." = sin dato). Últimos 60 días."""
    ini = max(desde, (date.today() - timedelta(days=60)).isoformat())
    d = json.loads(get(f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04640PD/json/{ini}/{hoy}", "application/json"))
    out = {}
    for p in d.get("periods", []):
        try:
            dd, mm, aa = p["name"].split(".")
            v = p["values"][0]
            if v != "n.d.":
                out[date(2000 + int(aa), MESES_BCRP[mm], int(dd)).isoformat()] = float(v)
        except Exception:  # noqa: BLE001
            continue
    return out


DXY_PESOS = {"EUR": -0.576, "JPY": 0.136, "GBP": -0.119, "CAD": 0.091, "SEK": 0.042, "CHF": 0.036}


def dolar_indice(hist):
    """Índice dólar calculado por Pulso Macro con la fórmula pública del DXY (6 monedas, pesos fijos) y las monedas del BCE.
    EUR y GBP vienen en dólares por unidad (exponente negativo); el resto en unidades por dólar. Da ±0,3 del DXY de ICE
    (el BCE toma las monedas a las 14:15 de Fráncfort, no al cierre de Nueva York)."""
    m = {c: dict(hist.get(c, [])) for c in DXY_PESOS}
    out = []
    for t in sorted(set.intersection(*(set(x) for x in m.values()))):
        v = 50.14348112
        for c, w in DXY_PESOS.items():
            v *= m[c][t] ** w
        out.append([t, round(v, 3)])
    return out


def a_cotizacion(pts, nombre):
    """Último y anterior, en el formato que usaba CNBC: {n, v, prev, t, estado}."""
    if not pts or len(pts) < 2:
        return None
    (t0, v0), (t1, v1) = pts[-2], pts[-1]
    return {"n": nombre, "v": v1, "prev": v0, "t": t1 + "T16:00:00+00:00", "estado": "", "f": "BCE" if nombre else ""}


def fx_cotizaciones(hist):
    """Mapa símbolo de CNBC → cotización, para reemplazar lo que antes venía de CNBC sin tocar la página."""
    q = {}
    for c, pts in hist.items():
        sym = c + "=" if c not in ("EURPLN", "EURCHF") else c + "="
        fuente = FUENTE_AL_DIA.get(c) or ("BIS" if c in BIS_FX else "BCE")
        x = a_cotizacion(pts, NOMBRES.get(c, c))
        if x:
            x["f"] = fuente
            q[sym] = x
    return q


def fx_series_hist(hist):
    """Claves fx_xxx de global_hist.json (minúsculas), 2 años."""
    return {f"fx_{c.lower()}": pts[-520:] for c, pts in hist.items() if c not in ("EURPLN", "EURCHF") and len(pts) > 20}


# ---- Tasas de EE.UU.: Departamento del Tesoro (dominio público) ----
TESORO = {"US2Y": "2 Yr", "US10Y": "10 Yr", "US30Y": "30 Yr"}


def tesoro_hist(dias=800):
    """{símbolo CNBC (US2Y, US10Y, US30Y): [[fecha, tasa %], ...]} de la curva diaria del Tesoro."""
    hoy = date.today()
    filas = []
    for y in range(hoy.year - dias // 365 - 1, hoy.year + 1):
        try:
            txt = get(f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all"
                      f"?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv", "text/csv")
            filas += _csv(txt)
        except Exception as e:  # noqa: BLE001
            errores.append(f"Tesoro {y}: {e}")
    out = {}
    desde = (hoy - timedelta(days=dias)).isoformat()
    for r in filas:
        try:
            t = datetime.strptime(r["Date"], "%m/%d/%Y").date().isoformat()
        except Exception:  # noqa: BLE001
            continue
        if t < desde:
            continue
        for sym, col in TESORO.items():
            if r.get(col) not in (None, ""):
                out.setdefault(sym, {})[t] = float(r[col])
    return {s: sorted([t, v] for t, v in d.items()) for s, d in out.items()}


# ---- Petróleo y gas: EIA de EE.UU. (precios spot diarios, dominio público; se publican con unos días de atraso) ----
EIA = {"@CL.1": "https://www.eia.gov/dnav/pet/hist_xls/RWTCd.xls",      # WTI Cushing, US$/barril
       "@LCO.1": "https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls",    # Brent Europa, US$/barril
       "@NG.1": "https://www.eia.gov/dnav/ng/hist_xls/RNGWHHDd.xls"}    # Henry Hub, US$/MMBtu


def eia_hist(dias=800):
    """{símbolo CNBC: [[fecha, precio], ...]}. Necesita xlrd (las planillas de la EIA son .xls)."""
    try:
        import xlrd
    except Exception as e:  # noqa: BLE001
        errores.append(f"EIA: falta xlrd ({e})")
        return {}
    desde = (date.today() - timedelta(days=dias)).isoformat()
    out = {}
    for sym, url in EIA.items():
        try:
            wb = xlrd.open_workbook(file_contents=get(url))
            sh = wb.sheet_by_name("Data 1")
            pts = []
            for i in range(3, sh.nrows):
                f, v = sh.cell_value(i, 0), sh.cell_value(i, 1)
                if not isinstance(f, float) or v in ("", None):
                    continue
                t = xlrd.xldate.xldate_as_datetime(f, wb.datemode).date().isoformat()
                if t >= desde:
                    pts.append([t, round(float(v), 4)])
            if len(pts) > 20:
                out[sym] = sorted(pts)
        except Exception as e:  # noqa: BLE001
            errores.append(f"EIA {sym}: {e}")
    return out


NOMBRES_SYM = {"US2Y": "Bono del Tesoro a 2 años", "US10Y": "Bono del Tesoro a 10 años", "US30Y": "Bono del Tesoro a 30 años",
               ".DXY": "Índice dólar (6 monedas, BCE)", "@CL.1": "Petróleo WTI (spot, EIA)", "@LCO.1": "Petróleo Brent (spot, EIA)", "@NG.1": "Gas natural Henry Hub (spot, EIA)"}


def sym_cotizaciones(hist):
    """Símbolo CNBC → {n, v, prev, t, estado, f} con el último y el anterior dato."""
    q = {}
    for sym, pts in hist.items():
        x = a_cotizacion(pts, NOMBRES_SYM.get(sym, sym))
        if x:
            x["f"] = "Tesoro de EE.UU." if sym.startswith("US") else "Pulso Macro con el BCE" if sym == ".DXY" else "EIA"
            q[sym] = x
    return q
