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

UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
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


# ---- Bonos del gobierno: cada banco central o ministerio publica su curva diaria, gratis y con reuso citando la fuente ----
BONOS_FUENTE = {"DE10Y-DE": "Bundesbank", "GB10Y-GB": "Banco de Inglaterra", "CA2Y": "Banco de Canadá", "CA10Y": "Banco de Canadá",
                "CA30Y": "Banco de Canadá", "JP2Y-JP": "Ministerio de Finanzas de Japón", "JP10Y-JP": "Ministerio de Finanzas de Japón",
                "JP30Y-JP": "Ministerio de Finanzas de Japón", "SE10Y-SE": "Riksbank", "NO10Y-NO": "Norges Bank"}


def _num(x):
    try:
        return float(str(x).replace(",", ".").strip())
    except Exception:  # noqa: BLE001
        return None


def bonos_hist(dias=800):
    """{símbolo CNBC: [[fecha, tasa %], ...]} de fuentes oficiales. Cada fuente por separado: si una falla, las otras siguen."""
    desde_d = date.today() - timedelta(days=dias)
    desde, hoy = desde_d.isoformat(), date.today().isoformat()
    out = {}

    def poner(sym, t, v):
        if v is not None and desde <= t <= hoy:
            out.setdefault(sym, {})[t] = round(v, 4)

    try:  # Bundesbank: rendimiento a 10 años (curva Svensson), CSV con ; y coma decimal
        for r in get(f"https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A?format=csv&startPeriod={desde}").decode("utf-8-sig", "replace").splitlines():
            p = r.split(";")
            if len(p) > 1 and len(p[0]) == 10 and p[0][4] == "-":
                poner("DE10Y-DE", p[0], _num(p[1]) if p[1] not in (".", "") else None)
    except Exception as e:  # noqa: BLE001
        errores.append(f"Bundesbank: {e}")
    try:  # Banco de Inglaterra: gilt a 10 años (par yield nominal)
        for r in get("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom="
                     + desde_d.strftime("%d/%b/%Y") + "&Dateto=now&SeriesCodes=IUDMNPY&CSVF=TN&UsingCodes=Y").decode("utf-8", "replace").splitlines()[1:]:
            p = r.split(",")
            try:
                poner("GB10Y-GB", datetime.strptime(p[0].strip(), "%d %b %Y").date().isoformat(), _num(p[1]))
            except Exception:  # noqa: BLE001
                continue
    except Exception as e:  # noqa: BLE001
        errores.append(f"Banco de Inglaterra: {e}")
    try:  # Banco de Canadá (Valet)
        sers = {"BD.CDN.2YR.DQ.YLD": "CA2Y", "BD.CDN.10YR.DQ.YLD": "CA10Y", "BD.CDN.LONG.DQ.YLD": "CA30Y"}
        j = json.loads(get(f"https://www.bankofcanada.ca/valet/observations/{','.join(sers)}/json?start_date={desde}", "application/json"))
        for o in j.get("observations", []):
            for s, sym in sers.items():
                poner(sym, o.get("d", ""), _num((o.get(s) or {}).get("v")))
    except Exception as e:  # noqa: BLE001
        errores.append(f"Banco de Canadá: {e}")
    try:  # Ministerio de Finanzas de Japón: histórico (hasta el mes pasado) + mes en curso
        for url in ("https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv",
                    "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv"):
            filas = get(url).decode("utf-8", "replace").splitlines()
            cab = next((r.split(",") for r in filas if r.startswith("Date,")), None)
            if not cab:
                continue
            col = {c: cab.index(c) for c in ("2Y", "10Y", "30Y") if c in cab}
            for r in filas:
                p = r.split(",")
                try:
                    t = datetime.strptime(p[0], "%Y/%m/%d").date().isoformat()
                except Exception:  # noqa: BLE001
                    continue
                for c, sym in (("2Y", "JP2Y-JP"), ("10Y", "JP10Y-JP"), ("30Y", "JP30Y-JP")):
                    if c in col and p[col[c]] not in ("-", ""):
                        poner(sym, t, _num(p[col[c]]))
    except Exception as e:  # noqa: BLE001
        errores.append(f"Ministerio de Finanzas de Japón: {e}")
    try:  # Riksbank (Suecia): bono del gobierno a 10 años
        for o in json.loads(get(f"https://api.riksbank.se/swea/v1/Observations/SEGVB10YC/{desde}", "application/json")):
            poner("SE10Y-SE", o.get("date", ""), _num(o.get("value")))
    except Exception as e:  # noqa: BLE001
        errores.append(f"Riksbank: {e}")
    try:  # Norges Bank: bono genérico a 10 años
        for r in get(f"https://data.norges-bank.no/api/data/GOVT_GENERIC_RATES/B.10Y.GBON?format=csv&startPeriod={desde}").decode("utf-8-sig", "replace").splitlines():
            p = r.split(";")
            if len(p) >= 2 and len(p[-2]) == 10 and p[-2][4] == "-":
                poner("NO10Y-NO", p[-2], _num(p[-1]))
    except Exception as e:  # noqa: BLE001
        errores.append(f"Norges Bank: {e}")
    return {s: sorted([t, v] for t, v in d.items()) for s, d in out.items() if len(d) > 20}


NOMBRES_SYM = {"DE10Y-DE": "Bund a 10 años", "GB10Y-GB": "Gilt a 10 años", "CA2Y": "Bono a 2 años", "CA10Y": "Bono a 10 años",
               "CA30Y": "Bono a 30 años", "JP2Y-JP": "Bono a 2 años", "JP10Y-JP": "Bono a 10 años", "JP30Y-JP": "Bono a 30 años",
               "SE10Y-SE": "Bono a 10 años", "NO10Y-NO": "Bono a 10 años",
               "US2Y": "Bono del Tesoro a 2 años", "US10Y": "Bono del Tesoro a 10 años", "US30Y": "Bono del Tesoro a 30 años",
               ".DXY": "Índice dólar (6 monedas, BCE)", "@CL.1": "Petróleo WTI (spot, EIA)", "@LCO.1": "Petróleo Brent (spot, EIA)", "@NG.1": "Gas natural Henry Hub (spot, EIA)"}


def sym_cotizaciones(hist):
    """Símbolo CNBC → {n, v, prev, t, estado, f} con el último y el anterior dato."""
    q = {}
    for sym, pts in hist.items():
        x = a_cotizacion(pts, NOMBRES_SYM.get(sym, sym))
        if x:
            x["f"] = (BONOS_FUENTE.get(sym) or ("Tesoro de EE.UU." if sym.startswith("US") else
                      "Pulso Macro con el BCE" if sym == ".DXY" else "EIA"))
            q[sym] = x
    return q


# ---- Plan legal, segunda etapa (26/10/2026): sin CNBC ----
# Bolsas y bonos de cada país: OCDE (Main Economic Indicators, promedios mensuales; uso libre, también comercial, citando).
OCDE_FIN = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/.M.SHARE+IRLT......"
            "?startPeriod={}&format=csvfile")


def ocde_mercados(anios=6):
    """{'SHARE': {ISO3: [[AAAA-MM-01, índice 2015=100], ...]}, 'IRLT': {ISO3: [[AAAA-MM-01, tasa %], ...]}}.
    SHARE = índice de precios de las acciones; IRLT = bono del gobierno a 10 años. Los dos son promedios del mes."""
    out = {"SHARE": {}, "IRLT": {}}
    try:
        for r in _csv(get(OCDE_FIN.format(f"{date.today().year - anios}-01"), "text/csv")):
            m, a, t, v = r.get("MEASURE"), r.get("REF_AREA"), r.get("TIME_PERIOD") or "", r.get("OBS_VALUE")
            if m in out and a and len(t) == 7 and v not in (None, "", "NaN"):
                out[m].setdefault(a, []).append([t + "-01", round(float(v), 4)])
    except Exception as e:  # noqa: BLE001
        errores.append(f"OCDE bolsas y bonos: {e}")
    corte = (date.today() - timedelta(days=150)).isoformat()  # más de ~5 meses sin dato: serie cortada, no se muestra
    def viva(p):
        p.sort()
        return len(p) > 2 and p[-1][0] >= corte and len({v for _, v in p[-6:]}) > 1  # (Rusia: la OCDE la dejó fija)
    return {m: {a: p for a, p in d.items() if viva(p)} for m, d in out.items()}


# Materias primas: Banco Mundial, "Pink Sheet" (precios promedio de cada mes; CC BY 4.0).
PINK = {"soja": "Soybeans", "maiz": "Maize", "trigo": "Wheat, US SRW", "oro": "Gold", "plata": "Silver", "cobre": "Copper"}


def banco_mundial_commodities(anios=6):
    """{clave: [[AAAA-MM-01, precio], ...]} en US$/t (soja, maíz, trigo, cobre) y US$/onza (oro, plata). Necesita openpyxl."""
    import re
    try:
        import openpyxl
        pag = get("https://www.worldbank.org/en/research/commodity-markets").decode("utf-8", "replace")
        m = re.search(r"https://thedocs\.worldbank\.org/[^\"'\s]+CMO-Historical-Data-Monthly\.xlsx", pag)
        if not m:
            raise ValueError("no encontré el link de la planilla mensual")
        wb = openpyxl.load_workbook(io.BytesIO(get(m.group(0))), read_only=True, data_only=True)
        filas = list(wb["Monthly Prices"].iter_rows(values_only=True))
        cab_i = next(i for i, r in enumerate(filas) if r and any(str(c or "").strip() == "Soybeans" for c in r))
        cab = [str(c or "").strip() for c in filas[cab_i]]
        cols = {k: cab.index(n) for k, n in PINK.items() if n in cab}
        desde, out = date.today().year - anios, {}
        for r in filas[cab_i + 1:]:
            mm = re.fullmatch(r"(\d{4})M(\d{2})", str(r[0] or "").strip())
            if not mm or int(mm.group(1)) < desde:
                continue
            for k, i in cols.items():
                if isinstance(r[i], (int, float)):
                    out.setdefault(k, []).append([f"{mm.group(1)}-{mm.group(2)}-01", round(float(r[i]), 2)])
        if not out:
            raise ValueError("planilla sin datos")
        return out
    except Exception as e:  # noqa: BLE001
        errores.append(f"Banco Mundial (materias primas): {e}")
        return {}


def ofr_estres(dias=800):
    """Índice de estrés financiero de la Oficina de Investigación Financiera de EE.UU. (OFR, Tesoro; dominio público).
    Diario. 0 = estrés promedio; positivo = más estrés que lo normal. Reemplaza al VIX (de Cboe, con licencia)."""
    try:
        desde = (date.today() - timedelta(days=dias)).isoformat()
        pts = [[r["Date"], round(float(r["OFR FSI"]), 3)] for r in _csv(get(
            "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv", "text/csv"))
            if r.get("Date", "") >= desde and r.get("OFR FSI") not in (None, "")]
        return sorted(pts)
    except Exception as e:  # noqa: BLE001
        errores.append(f"OFR estrés financiero: {e}")
        return []


def cot_mensual(pts, nombre, fuente):
    """Último mes y el anterior: {n, v, prev, t (AAAA-MM), mensual, f}. La página muestra el mes en vez de 'hoy'."""
    if not pts or len(pts) < 2:
        return None
    return {"n": nombre, "v": pts[-1][1], "prev": pts[-2][1], "t": pts[-1][0][:7], "mensual": True, "f": fuente}


def var_mensual(pts):
    """Para una bolsa con el índice mensual de la OCDE: mes, % contra el mes anterior, % en el año y % en 12 meses."""
    if not pts or len(pts) < 2:
        return {}
    (t, v), pv = pts[-1], pts[-2][1]
    dic = next((p[1] for p in reversed(pts) if p[0] < t[:4] + "-01-01"), None)
    hace = next((p[1] for p in pts if p[0] == f"{int(t[:4]) - 1}{t[4:]}"), None)
    r = lambda a, b: round((a / b - 1) * 100, 2) if a and b else None
    return {"m": t[:7], "vm": r(v, pv), "va": r(v, dic), "v12": r(v, hace), "fm": "OCDE (promedio del mes)"}


# ---- Símbolos para los widgets de TradingView (la página los muestra desde los servidores de TradingView, que tiene
# las licencias de las bolsas; Pulso Macro no guarda ni redistribuye esos precios). Probados uno por uno el 26/10/2026:
# los índices que TradingView no deja mostrar en widgets (S&P 500, Dow, Nikkei, FTSE...) van con el CFD que lo sigue. ----
TV = {
    # índices (o el instrumento que los sigue)
    ".SPX": ("FOREXCOM:SPXUSD", "S&P 500"), ".IXIC": ("FOREXCOM:NSXUSD", "Nasdaq 100"), ".DJI": ("FOREXCOM:DJI", "Dow Jones"),
    ".BVSP": ("BMFBOVESPA:IBOV", "Bovespa"), ".GSPTSE": ("TSX:TSX", "S&P/TSX"), ".FTSE": ("FOREXCOM:UKXGBP", "FTSE 100"),
    ".GDAXI": ("XETR:DAX", "DAX"), ".FCHI": ("EURONEXT:PX1", "CAC 40"), ".SSMI": ("SIX:SMI", "SMI"), ".SSEC": ("SSE:000001", "Shanghái"),
    ".HSI": ("HSI:HSI", "Hang Seng"), ".N225": ("FOREXCOM:JPXJPY", "Nikkei 225"), ".AXJO": ("FOREXCOM:AUXAUD", "S&P/ASX 200"),
    ".JKSE": ("IDX:COMPOSITE", "Jakarta Composite"), ".OSEBX": ("OSL:OSEBX", "OSEBX"), ".OMXS30": ("OMXSTO:OMXS30", "OMX Stockholm 30"),
    ".OMXI15": ("OMXICE:OMXI15", "OMX Iceland 15"), ".BUX": ("BET:BUX", "BUX"), ".PX": ("PSECZ:PX", "PX"),
    ".OMXC25": ("OMXCOP:OMXC25", "OMX Copenhagen 25"), ".BETI": ("BVB:BET", "BET"), ".IBEX": ("BME:IBC", "IBEX 35"),
    ".WIG20": ("GPW:WIG20", "WIG20"), ".STOXX50E": ("CAPITALCOM:EU50", "Euro Stoxx 50"), ".FTMIB": ("CAPITALCOM:IT40", "FTSE MIB"),
    ".VIX": ("CAPITALCOM:VIX", "VIX"), "IPSA": ("BCS:SP_IPSA", "S&P IPSA"),
    # índices sin widget: fondo de acciones del país que cotiza en Nueva York
    ".MXX": ("AMEX:EWW", "iShares MSCI Mexico (EWW)"), ".JALSH": ("AMEX:EZA", "iShares MSCI South Africa (EZA)"),
    ".TASI": ("AMEX:KSA", "iShares MSCI Saudi Arabia (KSA)"), ".NSEI": ("CBOE:INDA", "iShares MSCI India (INDA)"),
    ".KS11": ("AMEX:EWY", "iShares MSCI South Korea (EWY)"), ".NZ50": ("NASDAQ:ENZL", "iShares MSCI New Zealand (ENZL)"),
    ".SETI": ("AMEX:THD", "iShares MSCI Thailand (THD)"), ".KLSE": ("AMEX:EWM", "iShares MSCI Malaysia (EWM)"),
    ".PSI": ("AMEX:EPHE", "iShares MSCI Philippines (EPHE)"), ".TA35": ("AMEX:EIS", "iShares MSCI Israel (EIS)"),
    ".STI": ("AMEX:EWS", "iShares MSCI Singapore (EWS)"), ".TOPX": ("AMEX:EWJ", "iShares MSCI Japan (EWJ)"),
    ".XU100": ("NASDAQ:TUR", "iShares MSCI Turkey (TUR)"), ".COLCAP": ("AMEX:COLO", "Global X MSCI Colombia (COLO)"),
    # fondos y acciones que cotizan en Nueva York
    "ECH": ("CBOE:ECH", None), "EPU": ("AMEX:EPU", None), "EPOL": ("AMEX:EPOL", None), "INDA": ("CBOE:INDA", None),
    "KSA": ("AMEX:KSA", None), "EWL": ("AMEX:EWL", None), "EWA": ("AMEX:EWA", None), "EWY": ("AMEX:EWY", None),
    "EZA": ("AMEX:EZA", None), "ENZL": ("NASDAQ:ENZL", None), "EIDO": ("AMEX:EIDO", None), "NORW": ("AMEX:NORW", None),
    "EWD": ("AMEX:EWD", None), "THD": ("AMEX:THD", None), "EWM": ("AMEX:EWM", None), "EPHE": ("AMEX:EPHE", None),
    "EWH": ("AMEX:EWH", None), "EDEN": ("CBOE:EDEN", None), "EIS": ("AMEX:EIS", None), "FXI": ("AMEX:FXI", None),
    "EWS": ("AMEX:EWS", None), "EWP": ("AMEX:EWP", None), "TUR": ("NASDAQ:TUR", None), "ITA": ("CBOE:ITA", None),
    "RHM-DE": ("XETR:RHM", None), "BA.-GB": ("OTC:BAESY", "BAE Systems (ADR)"),
}
# Bolsa de Nueva York o Nasdaq de cada acción (para el widget). Las que no están acá van a NYSE.
NASDAQ = {"GGAL", "CRESY", "MELI", "BIOX", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "NFLX", "WMT", "XP",
          "ASML", "SNY", "VOD", "ARM", "SHOP", "TRI", "MMYT", "LOGI", "TEAM", "OMAB", "PDD", "BIDU", "JD", "CHKP",
          "ERIC", "GRAB", "ADBE", "AMD", "CSCO", "INTU", "QCOM", "TXN", "COST", "PEP", "AMGN", "LIN"}
OTC = {"CAJPY", "ABBNY", "NSRGY", "RHHBY", "BAESY"}


def tv_sym(sym):
    """Símbolo CNBC o ticker de Nueva York → (símbolo de TradingView, nombre a mostrar o None)."""
    if sym in TV:
        return TV[sym]
    import re
    if sym.startswith((".", "@")) or sym.endswith("=") or re.fullmatch(r"[A-Z]{2}\d+Y(-[A-Z]{2})?", sym):
        return (None, None)  # índice sin widget, moneda o bono: sin símbolo de TradingView
    ex = ("NASDAQ" if sym in NASDAQ else "OTC" if sym in OTC else
          "AMEX" if re.fullmatch(r"XL[A-Z]{1,2}", sym) else "NYSE")  # fondos de sectores (NYSE Arca) = AMEX en TradingView
    return (f"{ex}:{sym}", None)
