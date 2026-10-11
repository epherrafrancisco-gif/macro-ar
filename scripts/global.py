"""Arma global.json para la pestaña Global de Pulso Macro.

Fuentes (gratuitas, sin clave):
  - FMI, World Economic Outlook vía DataMapper (o Banco Mundial de respaldo): inflación, crecimiento,
    desempleo, PBI en dólares y PBI per cápita por país (estimación del año en curso).
  - BIS (Banco de Pagos Internacionales): tasas de política monetaria diarias de
    unos 40 bancos centrales, con la fecha de la última decisión.
  - Yahoo Finance (y Stooq como respaldo): índices bursátiles, monedas, bonos de
    EE.UU., commodities y bitcoin, con el cierre anterior para la variación.

Uso: python scripts/global.py
Nunca inventa datos: si una fuente falla, deja lo que había en global.json
y lo anota en "errores".
"""

import csv
import io
import json
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "global.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"

IMF = {  # indicador del FMI: campo
    "PCPIPCH": "infl",        # inflación promedio anual, %
    "NGDP_RPCH": "crec",      # crecimiento real del PBI, %
    "LUR": "desemp",          # desempleo, %
    "NGDPD": "pbi",           # PBI, miles de millones de US$
    "NGDPDPC": "pbipc",       # PBI per cápita, US$
}
EURO = ["AUT", "BEL", "HRV", "CYP", "EST", "FIN", "FRA", "DEU", "GRC", "IRL", "ITA", "LVA",
        "LTU", "LUX", "MLT", "NLD", "PRT", "SVK", "SVN", "ESP", "BGR"]
# BIS usa códigos ISO de 2 letras; XM = zona euro.
A2A3 = {"AR": "ARG", "AU": "AUS", "BR": "BRA", "CA": "CAN", "CH": "CHE", "CL": "CHL", "CN": "CHN",
        "CO": "COL", "CZ": "CZE", "DK": "DNK", "GB": "GBR", "HK": "HKG", "HU": "HUN", "ID": "IDN",
        "IL": "ISR", "IN": "IND", "IS": "ISL", "JP": "JPN", "KR": "KOR", "MK": "MKD", "MX": "MEX",
        "MY": "MYS", "NO": "NOR", "NZ": "NZL", "PE": "PER", "PH": "PHL", "PL": "POL", "RO": "ROU",
        "RS": "SRB", "RU": "RUS", "SA": "SAU", "SE": "SWE", "TH": "THA", "TR": "TUR", "US": "USA",
        "ZA": "ZAF", "UY": "URY", "PY": "PRY", "VN": "VNM", "KE": "KEN", "NG": "NGA", "EG": "EGY",
        "MA": "MAR", "BG": "BGR", "HR": "HRV", "CR": "CRI", "DO": "DOM", "GT": "GTM", "AE": "ARE"}
# Mercados: clave, nombre, grupo, símbolo Yahoo, símbolo Stooq, unidad, conversión
MERCADOS = [
    ("spx", "S&P 500", "indice", "^GSPC", "^spx", "pts", 1),
    ("ndx", "Nasdaq", "indice", "^IXIC", "^ndq", "pts", 1),
    ("dji", "Dow Jones", "indice", "^DJI", "^dji", "pts", 1),
    ("bvsp", "Bovespa", "indice", "^BVSP", "^bvp", "pts", 1),
    ("dax", "DAX", "indice", "^GDAXI", "^dax", "pts", 1),
    ("ftse", "FTSE 100", "indice", "^FTSE", "^ukx", "pts", 1),
    ("nikkei", "Nikkei", "indice", "^N225", "^nkx", "pts", 1),
    ("shanghai", "Shanghái", "indice", "000001.SS", "^shc", "pts", 1),
    ("t10", "Tasa 10 años EE.UU.", "tasa", "^TNX", "10usy.b", "%", 1),
    ("dxy", "Índice dólar (DXY)", "moneda", "DX-Y.NYB", "dx.f", "pts", 1),
    ("eurusd", "Euro", "moneda", "EURUSD=X", "eurusd", "US$", 1),
    ("usdbrl", "Real brasileño", "moneda", "BRL=X", "usdbrl", "por US$", 1),
    ("usdcny", "Yuan", "moneda", "CNY=X", "usdcny", "por US$", 1),
    ("oro", "Oro", "commodity", "GC=F", "gc.f", "US$/onza", 1),
    ("brent", "Petróleo Brent", "commodity", "BZ=F", "cb.f", "US$/barril", 1),
    ("wti", "Petróleo WTI", "commodity", "CL=F", "cl.f", "US$/barril", 1),
    ("soja", "Soja", "commodity", "ZS=F", "zs.f", "US$/t", 0.3674371),   # centavos/bushel → US$/t
    ("maiz", "Maíz", "commodity", "ZC=F", "zc.f", "US$/t", 0.3936825),
    ("trigo", "Trigo", "commodity", "ZW=F", "zw.f", "US$/t", 0.3674371),
    ("cobre", "Cobre", "commodity", "HG=F", "hg.f", "US$/t", 2204.623),  # US$/libra → US$/t
    ("btc", "Bitcoin", "cripto", "BTC-USD", "btcusd", "US$", 1),
]

errores = []


def get(url, tries=3, timeout=40, headers=None):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise last


WB = {  # respaldo del Banco Mundial (último año disponible) si el FMI no responde
    "infl": "FP.CPI.TOTL.ZG", "crec": "NY.GDP.MKTP.KD.ZG", "desemp": "SL.UEM.TOTL.ZS",
    "pbi": "NY.GDP.MKTP.CD", "pbipc": "NY.GDP.PCAP.CD",
}


def imf(prev):
    """Devuelve (paises, indicadores_ok, fuentes por campo)."""
    year = str(date.today().year)
    out = {k: dict(v) for k, v in (prev.get("paises") or {}).items()}
    for d in out.values():  # campos que ya no se usan
        d.pop("deuda", None)
    fuentes = dict(prev.get("fuentes") or {})
    fuentes.pop("deuda", None)
    ok = 0
    for ind, campo in IMF.items():
        try:
            j = json.loads(get(f"https://www.imf.org/external/datamapper/api/v1/{ind}", tries=2,
                               headers={"Accept": "application/json", "Referer": "https://www.imf.org/external/datamapper/"}))
            n = 0
            for iso, serie in (j.get("values", {}).get(ind) or {}).items():
                if len(iso) != 3 or not isinstance(serie, dict):
                    continue
                v = serie.get(year)
                if v is None:  # si el año en curso no está, el último disponible
                    ys = sorted(y for y, x in serie.items() if x is not None and y <= year)
                    if not ys:
                        continue
                    v = serie[ys[-1]]
                out.setdefault(iso, {})[campo] = round(float(v), 2)
                n += 1
            if n:
                ok += 1
                fuentes[campo] = {"f": "FMI", "anio": int(year)}
                continue
        except Exception as e:  # noqa: BLE001
            errores.append(f"FMI {ind}: {e}")
        if campo not in WB:
            continue
        try:  # respaldo: Banco Mundial
            j = json.loads(get(f"https://api.worldbank.org/v2/country/all/indicator/{WB[campo]}?format=json&per_page=20000&date={int(year)-4}:{year}"))
            mejor = {}
            for r in (j[1] if len(j) > 1 and j[1] else []):
                iso, v, y = r.get("countryiso3code"), r.get("value"), r.get("date")
                if not iso or v is None:
                    continue
                if iso not in mejor or y > mejor[iso][0]:
                    mejor[iso] = (y, v)
            if mejor:
                for iso, (y, v) in mejor.items():
                    out.setdefault(iso, {})[campo] = round(float(v) / (1e9 if campo == "pbi" else 1), 2)
                anios = sorted(y for y, _ in mejor.values())
                fuentes[campo] = {"f": "Banco Mundial", "anio": int(anios[len(anios) // 2])}
                ok += 1
        except Exception as e:  # noqa: BLE001
            errores.append(f"Banco Mundial {WB[campo]}: {e}")
    return out, ok, fuentes


def bis(paises):
    try:
        desde = f"{date.today().year - 2}-01-01"
        txt = get(f"https://stats.bis.org/api/v1/data/WS_CBPOL/D./all?startPeriod={desde}&format=csv", timeout=90)
    except Exception as e:  # noqa: BLE001
        errores.append(f"BIS: {e}")
        return 0
    series = {}
    for row in csv.DictReader(io.StringIO(txt)):
        a, f, v = row.get("REF_AREA"), row.get("TIME_PERIOD"), row.get("OBS_VALUE")
        if not a or not f or v in (None, "", "NaN"):
            continue
        try:
            series.setdefault(a, []).append((f, float(v)))
        except ValueError:
            continue
    if series:  # sacar las tasas viejas antes de cargar las nuevas
        for d in paises.values():
            for k in ("tasa", "tasa_al", "tasa_prev", "tasa_cambio"):
                d.pop(k, None)
    n = 0
    for a, pts in series.items():
        pts.sort()
        tasa, fecha = pts[-1][1], pts[-1][0]
        prev, cambio = None, None
        for f, v in reversed(pts):  # última decisión: el último día en que cambió la tasa
            if abs(v - tasa) > 1e-9:
                prev = v
                break
            cambio = f
        if (date.today() - date.fromisoformat(fecha[:10])).days > 120:  # serie discontinuada (ej. BCRA desde 2025)
            continue
        info = {"tasa": tasa, "tasa_al": fecha, "tasa_prev": prev, "tasa_cambio": cambio if prev is not None else None}
        destinos = EURO if a == "XM" else [A2A3.get(a)] if A2A3.get(a) else []
        for iso in destinos:
            paises.setdefault(iso, {}).update(info)
            n += 1
    return n


def yahoo(sym):
    j = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(sym)}?range=10d&interval=1d", tries=1))
    r = j["chart"]["result"][0]
    ts, cl = r.get("timestamp") or [], r["indicators"]["quote"][0].get("close") or []
    pts = [(t, c) for t, c in zip(ts, cl) if c is not None]
    if len(pts) < 2:
        raise ValueError("sin datos")
    meta = r.get("meta", {})
    precio = meta.get("regularMarketPrice") or pts[-1][1]
    t = meta.get("regularMarketTime") or pts[-1][0]
    # cierre anterior: el último cierre de un día distinto al del precio actual
    dia = datetime.fromtimestamp(t, timezone.utc).date()
    prev = next((c for tt, c in reversed(pts) if datetime.fromtimestamp(tt, timezone.utc).date() < dia), pts[-2][1])
    return float(precio), float(prev), datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="minutes")


def stooq(sym):
    txt = get(f"https://stooq.com/q/d/l/?s={urllib.request.quote(sym)}&i=d", tries=1)
    rows = [r for r in csv.reader(io.StringIO(txt)) if r and r[0][:1].isdigit()]
    if len(rows) < 2:
        raise ValueError("sin datos")
    return float(rows[-1][4]), float(rows[-2][4]), rows[-1][0] + "T21:00+00:00"


def yahoo_spark(syms):
    """Un solo pedido para todos los símbolos (menos chances de que Yahoo limite)."""
    out = {}
    for host in ("query2", "query1"):
        try:
            q = ",".join(urllib.request.quote(x) for x in syms)
            j = json.loads(get(f"https://{host}.finance.yahoo.com/v7/finance/spark?symbols={q}&range=5d&interval=1d", tries=1))
            for r in (j.get("spark") or {}).get("result") or []:
                resp = (r.get("response") or [{}])[0]
                meta = resp.get("meta", {})
                cl = [c for c in ((resp.get("indicators") or {}).get("quote") or [{}])[0].get("close") or [] if c is not None]
                precio = meta.get("regularMarketPrice") or (cl[-1] if cl else None)
                prevc = cl[-2] if len(cl) >= 2 else meta.get("chartPreviousClose")
                if precio and prevc:
                    t = meta.get("regularMarketTime")
                    out[r.get("symbol")] = (float(precio), float(prevc), datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="minutes") if t else "")
            if out:
                return out
        except Exception as e:  # noqa: BLE001
            errores.append(f"Yahoo spark {host}: {e}")
    return out


CNBC = {"spx": ".SPX", "ndx": ".IXIC", "dji": ".DJI", "bvsp": ".BVSP", "dax": ".GDAXI", "ftse": ".FTSE",
        "nikkei": ".N225", "shanghai": ".SSEC", "t10": "US10Y", "dxy": ".DXY", "oro": "@GC.1", "brent": "@LCO.1",
        "wti": "@CL.1", "soja": "@S.1", "maiz": "@C.1", "trigo": "@W.1", "cobre": "@HG.1"}


def cnbc():
    """Cotizaciones públicas de CNBC (un solo pedido, sin clave)."""
    syms = "|".join(CNBC.values())
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols="
                       + urllib.request.quote(syms, safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1",
                       tries=2, headers={"Accept": "application/json", "Referer": "https://www.cnbc.com/"}))
    q = ((j.get("FormattedQuoteResult") or {}).get("FormattedQuote")) or []
    num = lambda x: float(str(x).replace(",", "").replace("%", "").strip())
    por = {r.get("symbol"): r for r in q}
    out = {}
    for k, sym in CNBC.items():
        r = por.get(sym)
        try:
            out[k] = (num(r["last"]), num(r["previous_day_closing"]), str(r.get("last_time") or ""))
        except Exception:  # noqa: BLE001
            continue
    if not out:
        raise ValueError("sin cotizaciones")
    return out


def cnbc_raw(symbols):
    """Cotizaciones crudas de CNBC para una lista de símbolos (en tandas de 40)."""
    num = lambda x: float(str(x).replace(",", "").replace("%", "").strip())
    out = {}
    for i in range(0, len(symbols), 40):
        tanda = "|".join(symbols[i:i + 40])
        try:
            j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols="
                               + urllib.request.quote(tanda, safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1",
                               tries=2, headers={"Accept": "application/json", "Referer": "https://www.cnbc.com/"}))
        except Exception as e:  # noqa: BLE001
            errores.append(f"CNBC tanda {i // 40}: {e}")
            continue
        for r in ((j.get("FormattedQuoteResult") or {}).get("FormattedQuote")) or []:
            try:
                out[r["symbol"]] = {"n": r.get("name") or r.get("shortName") or r["symbol"], "v": num(r["last"]),
                                    "prev": num(r["previous_day_closing"]), "t": str(r.get("last_time") or ""),
                                    "estado": str(r.get("curmktstatus") or "")}
            except Exception:  # noqa: BLE001
                continue
    return out


# Índice principal de cada bolsa (clave de la bolsa en la página → símbolo CNBC, nombre del índice)
BOLSAS = {"NYSE": (".SPX", "S&P 500"), "BYMA": (".MERV", "S&P Merval"), "B3": (".BVSP", "Bovespa"),
          "BMV": (".MXX", "IPC México"), "TSX": (".GSPTSE", "S&P/TSX"), "LSE": (".FTSE", "FTSE 100"),
          "Xetra": (".GDAXI", "DAX"), "Euronext": (".FCHI", "CAC 40"), "JSE": ((".JALSH", ".JTOPI", ".J203"), "JSE"),
          "Tadawul": ((".TASI", "TASI", ".TASI.SE", ".TASIX"), "Tadawul"), "NSE": (".NSEI", "Nifty 50"), "SSE": (".SSEC", "Shanghái"),
          "HKEX": (".HSI", "Hang Seng"), "TSE": (".N225", "Nikkei 225"), "ASX": (".AXJO", "S&P/ASX 200")}
# Acciones por grupo (todas cotizan en Wall Street, en US$)
ACCIONES = {
    "arg": ["YPF", "GGAL", "BMA", "BBAR", "SUPV", "PAM", "CEPU", "TGS", "EDN", "TEO", "VIST", "LOMA", "CRESY", "IRS",
            "TX", "MELI", "GLOB", "DESP", "BIOX", "ARCO"],
    "usa": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "BRK.B", "JPM", "LLY", "V", "XOM",
            "WMT", "MA", "NFLX", "KO", "DIS"],
    "bra": ["PBR", "VALE", "ITUB", "BBD", "NU", "ABEV", "ERJ", "SBS", "GGB", "XP"],
    "eur": ["ASML", "SAP", "NVO", "AZN", "SHEL", "TTE", "UL", "HSBC", "SAN", "BP", "DEO", "SNY"],
    "asia": ["TSM", "BABA", "TM", "SONY", "PDD", "HDB", "INFY", "BIDU", "JD", "MUFG"],
}
TERMO = {"vix": ".VIX", "us2y": "US2Y", "us10y": "US10Y", "us30y": "US30Y"}
MONEDAS = {"ARS": "ARS=", "BRL": "BRL=", "CLP": "CLP=", "MXN": "MXN=", "COP": "COP=", "PEN": "PEN=", "UYU": "UYU=", "CNY": "CNY=", "EUR": "EUR="}
# Series con historia diaria (gráficos y "¿qué rindió más en el año?")
HIST = {"spx": ".SPX", "ndx": ".IXIC", "dji": ".DJI", "merv": ".MERV", "bvsp": ".BVSP", "dax": ".GDAXI",
        "ftse": ".FTSE", "nikkei": ".N225", "shanghai": ".SSEC", "oro": "@GC.1", "brent": "@LCO.1", "soja": "@S.1",
        "cobre": "@HG.1", "dxy": ".DXY", "t10": "US10Y", "vix": ".VIX",
        "fx_brl": "BRL=", "fx_mxn": "MXN=", "fx_clp": "CLP=", "fx_cop": "COP=", "fx_ars": "ARS="}


def extras():
    alt = lambda s: s if isinstance(s, tuple) else (s,)
    syms = [x for v in BOLSAS.values() for x in alt(v[0])] + [x for l in ACCIONES.values() for x in l] + list(TERMO.values()) + list(MONEDAS.values())
    q = cnbc_raw(syms)
    bolsas = {}
    for k, (s, n) in BOLSAS.items():
        varios = isinstance(s, tuple)
        s = next((x for x in alt(s) if x in q), None)
        if s:
            bolsas[k] = {"idx": q[s]["n"] if varios else n, **q[s]}
    acciones = {g: [{"s": x, **q[x]} for x in l if x in q] for g, l in ACCIONES.items()}
    termo = {k: q[s] for k, s in TERMO.items() if s in q}
    monedas = {k: q[s] for k, s in MONEDAS.items() if s in q}
    return {"bolsas": bolsas, "acciones": acciones, "termo": termo, "monedas": monedas}


def historia(prev_h):
    """Cierres diarios de 1 año (CNBC). Se renueva cada 3 horas como máximo."""
    try:
        al = datetime.fromisoformat(prev_h.get("actualizado", "2000-01-01T00:00+00:00"))
        if (datetime.now(timezone.utc) - al).total_seconds() < 3 * 3600 and prev_h.get("series"):
            return prev_h
    except Exception:  # noqa: BLE001
        pass
    series = dict(prev_h.get("series") or {})
    ok = 0
    for k, sym in HIST.items():
        try:
            j = json.loads(get(f"https://ts-api.cnbc.com/harmony/app/charts/1Y.json?symbol={urllib.request.quote(sym, safe='')}",
                               tries=2, headers={"Accept": "application/json", "Referer": "https://www.cnbc.com/"}))
            pts = []
            for b in (j.get("barData") or {}).get("priceBars") or []:
                t, c = str(b.get("tradeTime") or ""), b.get("close")
                if len(t) >= 8 and c not in (None, ""):
                    pts.append([f"{t[:4]}-{t[4:6]}-{t[6:8]}", round(float(c), 4)])
            if len(pts) > 20:
                series[k] = pts
                ok += 1
            else:
                errores.append(f"CNBC historia {sym}: {len(pts)} puntos")
        except Exception as e:  # noqa: BLE001
            errores.append(f"CNBC historia {sym}: {e}")
        time.sleep(0.4)
    try:  # bitcoin: CoinGecko
        j = json.loads(get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365&interval=daily"))
        series["btc"] = [[datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat(), round(v, 2)] for t, v in j.get("prices", [])]
        ok += 1
    except Exception as e:  # noqa: BLE001
        errores.append(f"CoinGecko historia: {e}")
    if not ok:
        return prev_h
    return {"actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"), "series": series}


def frankfurter():
    """Monedas del BCE (Frankfurter): EUR, BRL y CNY contra el dólar, último y anterior."""
    hoy = date.today()
    j = json.loads(get(f"https://api.frankfurter.app/{(hoy - timedelta(days=10)).isoformat()}..?from=USD&to=EUR,BRL,CNY"))
    fechas = sorted(j.get("rates") or {})
    if len(fechas) < 2:
        raise ValueError("sin datos")
    u, a = j["rates"][fechas[-1]], j["rates"][fechas[-2]]
    t = fechas[-1] + "T16:00+00:00"
    return {"eurusd": (1 / u["EUR"], 1 / a["EUR"], t), "usdbrl": (u["BRL"], a["BRL"], t), "usdcny": (u["CNY"], a["CNY"], t)}


def coingecko():
    j = json.loads(get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_last_updated_at=true"))
    b = j["bitcoin"]
    v, ch = float(b["usd"]), float(b.get("usd_24h_change") or 0)
    return {"btc": (v, v / (1 + ch / 100), datetime.fromtimestamp(b.get("last_updated_at", time.time()), timezone.utc).isoformat(timespec="minutes"))}


def mercados(prev):
    viejo = {m["k"]: m for m in prev.get("mercados") or []}
    datos, fuente = {}, {}
    for nombre, fn in (("CNBC", cnbc), ("BCE/Frankfurter", frankfurter), ("CoinGecko", coingecko)):
        try:
            for k, d in fn().items():
                if k not in datos:
                    datos[k], fuente[k] = d, nombre
        except Exception as e:  # noqa: BLE001
            errores.append(f"{nombre}: {e}")
    faltan = [m for m in MERCADOS if m[0] not in datos]
    if faltan:
        spark = yahoo_spark([m[3] for m in faltan])
        for k, _, _, ys, *_ in faltan:
            if ys in spark:
                datos[k], fuente[k] = spark[ys], "Yahoo"
    for k, _, _, ys, ss, *_ in MERCADOS:  # respaldo uno por uno
        if k in datos:
            continue
        for f, fn, sym in (("Yahoo", yahoo, ys), ("Stooq", stooq, ss)):
            try:
                datos[k], fuente[k] = fn(sym), f
                break
            except Exception as e:  # noqa: BLE001
                errores.append(f"{f} {sym}: {e}")
            time.sleep(1)
    out = []
    for k, n, g, ys, ss, u, conv in MERCADOS:
        if k in datos:
            p, pv, t = datos[k]
            c = 1 if fuente[k] in ("BCE/Frankfurter", "CoinGecko") else conv
            out.append({"k": k, "n": n, "g": g, "u": u, "v": round(p * c, 4), "prev": round(pv * c, 4), "t": t, "f": fuente[k]})
        elif k in viejo:
            out.append(viejo[k])
    return out


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    paises, ok_imf, fuentes = imf(prev)
    n_bis = bis(paises)
    try:
        ex = extras()
    except Exception as e:  # noqa: BLE001
        errores.append(f"extras: {e}")
        ex = {}
    for k in ("bolsas", "acciones", "termo", "monedas"):  # si una sección vino vacía, queda la anterior
        if not ex.get(k) or (k == "acciones" and not any(ex[k].values())):
            ex[k] = prev.get(k) or {}
    HISTF = ROOT / "global_hist.json"
    prev_h = {}
    if HISTF.exists():
        try:
            prev_h = json.loads(HISTF.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev_h = {}
    h = historia(prev_h)
    if h is not prev_h:
        HISTF.write_text(json.dumps(h, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    data = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        **ex,
        "anio_fmi": date.today().year,
        "paises": dict(sorted(paises.items())),
        "fuentes": fuentes,
        "mercados": mercados(prev),
        "errores": errores[:60],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"FMI {ok_imf}/{len(IMF)} indicadores, {len(paises)} países; BIS {n_bis} países con tasa; "
          f"{len(data['mercados'])}/{len(MERCADOS)} mercados")
    for e in errores:
        print("ERROR", e)
    # No corta el workflow: los errores quedan en global.json para poder diagnosticarlos.


if __name__ == "__main__":
    main()
