"""Arma global.json para la pestaña Global de Pulso Macro.

Fuentes (gratuitas, sin clave):
  - FMI, World Economic Outlook vía DataMapper (o Banco Mundial de respaldo): inflación, crecimiento,
    desempleo, PBI en dólares y PBI per cápita por país (estimación del año en curso).
  - BIS (Banco de Pagos Internacionales): tasas de política monetaria diarias de
    unos 40 bancos centrales, con la fecha de la última decisión.
  - (antes Yahoo Finance y Stooq como respaldo: sacados en 10/2026 por sus términos) índices bursátiles, monedas, bonos de
    EE.UU., commodities y bitcoin, con el cierre anterior para la variación.

Uso: python scripts/global.py
Nunca inventa datos: si una fuente falla, deja lo que había en global.json
y lo anota en "errores".
"""

import csv
import html
import io
import json
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
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
# Mercados: clave, nombre, grupo, símbolo Yahoo (ya no se usa), símbolo Stooq (ya no se usa), unidad, conversión
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


# Yahoo Finance y Stooq se sacaron (10/2026): sus términos prohíben redistribuir los datos.



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
          "Tadawul": ((".TASI", "TASI", ".TASI.SE", ".TASIX"), "Tadawul"), "NSE": (".NSEI", "Nifty 50"), "SIX": (".SSMI", "SMI"), "SSE": (".SSEC", "Shanghái"),
          "HKEX": (".HSI", "Hang Seng"), "TSE": (".N225", "Nikkei 225"), "ASX": (".AXJO", "S&P/ASX 200"), "KRX": (".KS11", "KOSPI"), "NZX": (".NZ50", "NZX 50"), "IDX": (".JKSE", "Jakarta Composite"), "OSE": ((".OSEBX", ".OSEAX",), "OSEBX"), "OMX": ((".OMXS30",), "OMX Stockholm 30"), "SET": ((".SETI",), "SET"), "KLSE": ((".KLSE",), "FTSE Bursa Malaysia KLCI"), "PSE": ((".PSI",), "PSEi"), "ICEX": ((".OMXI15", ".OMXIPI",), "OMX Iceland 15"), "BUX": ((".BUX",), "BUX"), "PSE_CZ": ((".PX",), "PX"), "CPH": ((".OMXC25", ".OMXC20",), "OMX Copenhagen 25"), "BVB": ((".BETI", ".BET",), "BET"), "TASE": ((".TA35", ".TA125",), "TA-35"), "BELEX": ((".BELEX15", ".BELEXLINE",), "BELEX15"), "MOEX": ((".IMOEX", ".MOEX", ".IRTS"), "MOEX Russia"), "BME": ((".IBEX",), "IBEX 35"), "SGX": ((".STI", ".FTSTI"), "STI"), "CSE": ((".MASI", ".MADEX"), "MASI"), "MSE": ((".MBI10",), "MBI10"),
          "GPW": ((".WIG20", "WIG20", ".WIG20.WA"), "WIG20")}
# Acciones por grupo (todas cotizan en Wall Street, en US$)
ACCIONES = {
    "arg": ["YPF", "GGAL", "BMA", "BBAR", "SUPV", "PAM", "CEPU", "TGS", "EDN", "TEO", "VIST", "LOMA", "CRESY", "IRS",
            "TX", "MELI", "GLOB", "DESP", "BIOX", "ARCO"],
    "usa": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "BRK.B", "JPM", "LLY", "V", "XOM",
            "WMT", "MA", "NFLX", "KO", "DIS"],
    "bra": ["PBR", "VALE", "ITUB", "BBD", "NU", "ABEV", "ERJ", "SBS", "GGB", "XP"],
    "eur": ["ASML", "SAP", "NVO", "AZN", "SHEL", "TTE", "UL", "HSBC", "SAN", "BP", "DEO", "SNY"],
    "chl": ["SQM", "LTM", "BCH", "BSAC", "ENIC", "CCU", "AKO.B"],
    "jpn": ["TM", "SONY", "MUFG", "SMFG", "MFG", "HMC", "NMR", "IX", "TAK", "CAJPY"],
    "gbr": ["SHEL", "AZN", "HSBC", "UL", "BP", "DEO", "GSK", "BTI", "RIO", "BCS", "LYG", "NWG", "VOD", "RELX", "ARM"],
    "can": ["SHOP", "RY", "TD", "ENB", "CNQ", "CP", "CNI", "BMO", "BNS", "SU", "BAM", "TRI", "CM", "NTR", "B", "CVE", "MFC"],
    "col": ["EC", "CIB", "AVAL", "TGLS"],
    "per": ["BAP", "SCCO", "BVN", "IFS"],
    "ind": ["INFY", "HDB", "IBN", "WIT", "RDY", "MMYT"],
    "che": ["NVS", "UBS", "ALC", "LOGI", "ABBNY", "NSRGY", "RHHBY", "GRMN"],
    "aus": ["BHP", "RIO", "WDS", "JHX", "TEAM"],
    "kor": ["KB", "SHG", "PKX", "KEP", "SKM", "LPL", "WF"],
    "zaf": ["GFI", "AU", "SBSW", "HMY", "SSL", "DRD"],
    "mex": ["AMX", "FMX", "KOF", "CX", "ASR", "PAC", "OMAB", "TV", "VLRS", "SCCO"],
    "asia": ["TSM", "BABA", "TM", "SONY", "PDD", "HDB", "INFY", "BIDU", "JD", "MUFG"],
}
# Bono del gobierno a 10 años de cada país (ISO3 → símbolo CNBC). Argentina va con el riesgo país (data.json).
BONOS = {"USA": "US10Y", "DEU": "DE10Y-DE", "GBR": "GB10Y-GB", "JPN": "JP10Y-JP", "FRA": "FR10Y-FR", "ITA": "IT10Y-IT",
         "ESP": "ES10Y-ES", "CHE": "CH10Y-CH", "CAN": "CA10Y", "AUS": "AU10Y", "CHN": "CN10Y", "IND": "IN10Y", "KOR": "KR10Y-KR", "NZL": "NZ10Y", "IDN": "ID10Y", "NOR": "NO10Y-NO", "SWE": "SE10Y-SE", "THA": "TH10Y", "MYS": "MY10Y", "PHL": "PH10Y", "ISL": "IS10Y", "HUN": "HU10Y", "HKG": "HK10Y", "CZE": "CZ10Y", "DNK": "DK10Y", "ROU": "RO10Y", "ISR": "IL10Y", "SRB": "RS10Y", "RUS": "RU10Y", "SGP": "SG10Y", "MAR": "MA10Y",
         "BRA": "BR10Y", "MEX": "MX10Y", "CHL": "CL10Y-CL", "ZAF": "ZA10Y-ZA", "TUR": "TR10Y-TR"}
# Commodities (clave, nombre, símbolo CNBC, conversión a la unidad mostrada, unidad)
COMS = [("soja", "Soja", "@S.1", 0.3674371, "US$/t"), ("maiz", "Maíz", "@C.1", 0.3936825, "US$/t"),
        ("trigo", "Trigo", "@W.1", 0.3674371, "US$/t"), ("wti", "Petróleo WTI", "@CL.1", 1, "US$/barril"),
        ("brent", "Petróleo Brent", "@LCO.1", 1, "US$/barril"), ("gas", "Gas natural (EE.UU.)", "@NG.1", 1, "US$/MMBtu"),
        ("oro", "Oro", "@GC.1", 1, "US$/onza"), ("plata", "Plata", "@SI.1", 1, "US$/onza"), ("cobre", "Cobre", "@HG.1", 2204.623, "US$/t")]
COM_CONV = {k: c for k, _, _, c, _ in COMS}
TERMO = {"vix": ".VIX", "us2y": "US2Y", "us10y": "US10Y", "us30y": "US30Y"}
MONEDAS = {"ARS": "ARS=", "BRL": "BRL=", "CLP": "CLP=", "MXN": "MXN=", "COP": "COP=", "PEN": "PEN=", "UYU": "UYU=", "CNY": "CNY=", "EUR": "EUR=", "PLN": "PLN=", "INR": "INR=", "SAR": "SAR=", "CHF": "CHF=", "AUD": "AUD=", "KRW": "KRW=", "ZAR": "ZAR=", "NZD": "NZD=", "IDR": "IDR=", "NOK": "NOK=", "SEK": "SEK=", "THB": "THB=", "MYR": "MYR=", "PHP": "PHP=", "ISK": "ISK=", "HUF": "HUF=", "HKD": "HKD=", "CZK": "CZK=", "DKK": "DKK=", "RON": "RON=", "ILS": "ILS=", "RSD": "RSD=", "RUB": "RUB=", "SGD": "SGD=", "MAD": "MAD=", "MKD": "MKD="}
# Series con historia diaria (gráficos y "¿qué rindió más en el año?")
HIST = {"spx": ".SPX", "ndx": ".IXIC", "dji": ".DJI", "merv": ".MERV", "bvsp": ".BVSP", "dax": ".GDAXI",
        "ftse": ".FTSE", "nikkei": ".N225", "shanghai": ".SSEC", "oro": "@GC.1", "brent": "@LCO.1", "soja": "@S.1",
        "cobre": "@HG.1", "dxy": ".DXY", "t10": "US10Y", "vix": ".VIX",
        "fx_brl": "BRL=", "fx_mxn": "MXN=", "fx_clp": "CLP=", "fx_cop": "COP=", "fx_ars": "ARS=",
        "maiz": "@C.1", "trigo": "@W.1", "wti": "@CL.1", "gas": "@NG.1", "plata": "@SI.1",
        "fx_pen": "PEN=", "fx_uyu": "UYU=", "fx_cny": "CNY=", "fx_eur": "EUR=",
        "cac": ".FCHI", "ibex": ".IBEX", "ftmib": ".FTMIB", "sx5e": ".STOXX50E", "de10": "DE10Y-DE", "it10": "IT10Y-IT", "fr10": "FR10Y-FR", "es10": "ES10Y-ES",
        "mxx": ".MXX", "mx10": "MX10Y", "ech": "ECH", "cl10": "CL10Y-CL",
        "fx_jpy": "JPY=", "topix": ".TOPX", "jp10": "JP10Y-JP", "jp2": "JP2Y-JP",
        "fx_gbp": "GBP=", "ftmc": ".FTMC", "gb10": "GB10Y-GB", "gb2": "GB2Y-GB",
        "fx_cad": "CAD=", "tsx": ".GSPTSE", "ca10": "CA10Y", "ca2": "CA2Y",
        "colcap": ".COLCAP", "xu100": ".XU100", "fx_try": "TRY=", "tr10": "TR10Y-TR", "tr2": "TR2Y-TR",
        "epu": "EPU", "fx_pln": "PLN=", "wig20": ".WIG20", "epol": "EPOL", "fx_inr": "INR=", "in10": "IN10Y", "inda": "INDA", "ksa": "KSA", "nifty": ".NSEI", "tasi": ".TASI", "fx_chf": "CHF=", "smi": ".SSMI", "ch10": "CH10Y-CH", "ewl": "EWL", "fx_aud": "AUD=", "asx": ".AXJO", "au10": "AU10Y", "ewa": "EWA", "fx_krw": "KRW=", "kospi": ".KS11", "kr10": "KR10Y-KR", "ewy": "EWY", "fx_zar": "ZAR=", "jse": ".JTOPI", "za10": "ZA10Y-ZA", "eza": "EZA", "fx_nzd": "NZD=", "nzx": ".NZ50", "nz10": "NZ10Y", "enzl": "ENZL", "fx_idr": "IDR=", "jkse": ".JKSE", "id10": "ID10Y", "eido": "EIDO", "fx_nok": "NOK=", "osebx": ".OSEBX", "no10": "NO10Y-NO", "norw": "NORW", "fx_sek": "SEK=", "omxs30": ".OMXS30", "se10": "SE10Y-SE", "ewd": "EWD", "fx_thb": "THB=", "seti": ".SETI", "th10": "TH10Y", "thd": "THD", "fx_myr": "MYR=", "klci": ".KLSE", "my10": "MY10Y", "ewm": "EWM", "fx_php": "PHP=", "psei": ".PSI", "ph10": "PH10Y", "ephe": "EPHE", "fx_isk": "ISK=", "omxi": ".OMXI15", "is10": "IS10Y", "fx_huf": "HUF=", "bux": ".BUX", "hu10": "HU10Y", "fx_hkd": "HKD=", "hsi": ".HSI", "hk10": "HK10Y", "ewh": "EWH", "fx_czk": "CZK=", "pxi": ".PX", "cz10": "CZ10Y", "fx_dkk": "DKK=", "omxc": ".OMXC20", "dk10": "DK10Y", "eden": "EDEN", "fx_ron": "RON=", "bet": ".BETI", "ro10": "RO10Y", "fx_ils": "ILS=", "ta35": ".TA35", "il10": "IL10Y", "eis": "EIS", "fx_rsd": "RSD=", "belex": ".BELEX15", "cn10": "CN10Y", "fxi": "FXI", "fx_rub": "RUB=", "imoex": ".IMOEX", "ru10": "RU10Y", "ita": "ITA", "fx_sgd": "SGD=", "sti": ".STI", "sg10": "SG10Y", "ews": "EWS", "fx_mad": "MAD=", "masi": ".MASI", "fx_mkd": "MKD=", "mbi10": ".MBI10", "ewp": "EWP"}
# Bolsas europeas para la sección Europa
# Bolsa chilena: CNBC no tiene el IPSA; se usa el fondo iShares MSCI Chile (ECH, en dólares)
CHILE = {"ech": ("ECH", "iShares MSCI Chile")}
# Japón: TOPIX, yen y bonos a 2 y 30 años (el de 10 está en BONOS)
JAPON = {"topix": (".TOPX", "TOPIX"), "jpy": ("JPY=", "Yen por dólar"), "jp2": ("JP2Y-JP", "Bono a 2 años"), "jp30": ("JP30Y-JP", "Bono a 30 años")}
# Reino Unido: FTSE 250, libra (dólares por libra) y gilts a 2 y 30 años (el de 10 está en BONOS)
REINO = {"ftmc": (".FTMC", "FTSE 250"), "gbp": ("GBP=", "Dólares por libra"), "gb2": ("GB2Y-GB", "Gilt a 2 años"), "gb30": ("GB30Y-GB", "Gilt a 30 años")}
# Canadá: dólar canadiense (por dólar) y bonos a 2 y 30 años (el de 10 está en BONOS; el TSX en BOLSAS)
CANADA = {"cad": ("CAD=", "Dólares canadienses por dólar"), "ca2": ("CA2Y", "Bono a 2 años"), "ca30": ("CA30Y", "Bono a 30 años")}
# Colombia: índice MSCI COLCAP (el peso colombiano está en MONEDAS)
COLOMBIA = {"colcap": (".COLCAP", "MSCI COLCAP")}
# Turquía: BIST 100, lira, bono a 2 años (el de 10 está en BONOS), ETF y Turkcell
TURQUIA = {"xu100": (".XU100", "BIST 100"), "try": ("TRY=", "Liras por dólar"), "tr2": ("TR2Y-TR", "Bono a 2 años"), "tur": ("TUR", "iShares MSCI Turkey"), "tkc": ("TKC", "Turkcell")}
# Polonia: zloty contra el dólar y el euro y el fondo de acciones polacas que cotiza en Nueva York. CNBC no tiene los bonos
# polacos (el de 10 años sale del BCE en polonia.py) y su cotización del WIG20 viene vacía: el índice sale de la historia.
POLONIA = {"pln": ("PLN=", "Zlotys por dólar"), "eurpln": ("EURPLN=", "Zlotys por euro"), "epol": ("EPOL", "iShares MSCI Poland")}
# India (el Nifty está en BOLSAS y el bono a 10 años en BONOS) y Arabia Saudita (CNBC no tiene el Tadawul: se usa el
# fondo iShares MSCI Saudi Arabia, KSA)
INDIA = {"inr": ("INR=", "Rupias por dólar"), "inda": ("INDA", "iShares MSCI India")}
ISLANDIA = {"isk": ("ISK=", "Islandia")}
HUNGRIA = {"huf": ("HUF=", "Hungría")}
HONGKONG = {"hkd": ("HKD=", "Hong Kong"), "ewh": ("EWH", "iShares MSCI Hong Kong")}
CHEQUIA = {"czk": ("CZK=", "Chequia")}
DINAMARCA = {"dkk": ("DKK=", "Dinamarca"), "eden": ("EDEN", "iShares MSCI Denmark"), "nvo": ("NVO", "NVO")}
RUMANIA = {"ron": ("RON=", "Rumania")}
ISRAEL = {"ils": ("ILS=", "Israel"), "eis": ("EIS", "iShares MSCI Israel"), "teva": ("TEVA", "TEVA"), "chkp": ("CHKP", "CHKP")}
SERBIA = {"rsd": ("RSD=", "Serbia")}
CHINA = {"cny": ("CNY=", "China"), "fxi": ("FXI", "iShares China Large-Cap"), "baba": ("BABA", "BABA"), "pdd": ("PDD", "PDD"), "bidu": ("BIDU", "BIDU")}
RUSIA = {"rub": ("RUB=", "Rusia")}
ESPANA = {"eur": ("EUR=", "España"), "ewp": ("EWP", "iShares MSCI Spain"), "san": ("SAN", "SAN"), "bbva": ("BBVA", "BBVA"), "tef": ("TEF", "TEF")}
SINGAPUR = {"sgd": ("SGD=", "Singapur"), "ews": ("EWS", "iShares MSCI Singapore"), "se": ("SE", "SE"), "grab": ("GRAB", "GRAB")}
MARRUECOS = {"mad": ("MAD=", "Marruecos")}
MACEDONIA = {"mkd": ("MKD=", "Macedonia del Norte")}
DEFENSA = {"ita": ("ITA", "iShares U.S. Aerospace & Defense"), "lmt": ("LMT", "Lockheed Martin"), "noc": ("NOC", "Northrop Grumman"), "rtx": ("RTX", "RTX (Raytheon)"), "gd": ("GD", "General Dynamics"), "lhx": ("LHX", "L3Harris"), "rhm": ("RHM-DE", "Rheinmetall"), "ba_": ("BA.-GB", "BAE Systems")}
NORUEGA = {"nok": ("NOK=", "Noruega"), "norw": ("NORW", "Global X MSCI Norway"), "eqnr": ("EQNR", "EQNR")}
SUECIA = {"sek": ("SEK=", "Suecia"), "ewd": ("EWD", "iShares MSCI Sweden"), "eric": ("ERIC", "ERIC"), "spot": ("SPOT", "SPOT")}
TAILANDIA = {"thb": ("THB=", "Tailandia"), "thd": ("THD", "iShares MSCI Thailand")}
MALASIA = {"myr": ("MYR=", "Malasia"), "ewm": ("EWM", "iShares MSCI Malaysia")}
FILIPINAS = {"php": ("PHP=", "Filipinas"), "ephe": ("EPHE", "iShares MSCI Philippines"), "phi": ("PHI", "PHI")}
ZELANDA = {"nzd": ("NZD=", "Dólar neozelandés"), "enzl": ("ENZL", "iShares MSCI New Zealand")}
INDONESIA = {"idr": ("IDR=", "Rupias por dólar"), "eido": ("EIDO", "iShares MSCI Indonesia"), "tlk": ("TLK", "Telkom Indonesia")}
COREA = {"krw": ("KRW=", "Wones por dólar"), "ewy": ("EWY", "iShares MSCI South Korea")}
SUDAFRICA = {"zar": ("ZAR=", "Rands por dólar"), "eza": ("EZA", "iShares MSCI South Africa")}
AUSTRALIA = {"aud": ("AUD=", "Dólar australiano"), "ewa": ("EWA", "iShares MSCI Australia")}
SUIZA = {"chf": ("CHF=", "Francos por dólar"), "eurchf": ("EURCHF=", "Francos por euro"), "ewl": ("EWL", "iShares MSCI Switzerland")}
ARABIA = {"sar": ("SAR=", "Riyales por dólar"), "ksa": ("KSA", "iShares MSCI Saudi Arabia")}
# Perú: CNBC no actualiza el S&P/BVL; se usa el fondo iShares MSCI Peru (EPU, en dólares)
PERU = {"epu": ("EPU", "iShares MSCI Peru")}
EUROPA = {"sx5e": (".STOXX50E", "Euro Stoxx 50"), "stoxx600": (".STOXX", "Stoxx Europe 600"), "dax": (".GDAXI", "DAX"), "cac": (".FCHI", "CAC 40"), "ibex": (".IBEX", "IBEX 35"), "ftmib": (".FTMIB", "FTSE MIB")}


def extras():
    alt = lambda s: s if isinstance(s, tuple) else (s,)
    syms = ([x for v in BOLSAS.values() for x in alt(v[0])] + [x for l in ACCIONES.values() for x in l] + list(TERMO.values())
            + list(MONEDAS.values()) + list(BONOS.values()) + [c[2] for c in COMS] + [v[0] for v in EUROPA.values()] + [v[0] for v in CHILE.values()] + [v[0] for v in JAPON.values()] + [v[0] for v in REINO.values()] + [v[0] for v in CANADA.values()] + [v[0] for v in COLOMBIA.values()] + [v[0] for v in TURQUIA.values()] + [v[0] for v in PERU.values()] + [v[0] for v in POLONIA.values()] + [v[0] for v in INDIA.values()] + [v[0] for v in ARABIA.values()] + [v[0] for v in SUIZA.values()] + [v[0] for v in AUSTRALIA.values()] + [v[0] for v in COREA.values()] + [v[0] for v in SUDAFRICA.values()] + [v[0] for v in ZELANDA.values()] + [v[0] for v in INDONESIA.values()] + [v[0] for v in NORUEGA.values()] + [v[0] for v in SUECIA.values()] + [v[0] for v in TAILANDIA.values()] + [v[0] for v in MALASIA.values()] + [v[0] for v in FILIPINAS.values()] + [v[0] for v in ISLANDIA.values()] + [v[0] for v in HUNGRIA.values()] + [v[0] for v in HONGKONG.values()] + [v[0] for v in CHEQUIA.values()] + [v[0] for v in DINAMARCA.values()] + [v[0] for v in RUMANIA.values()] + [v[0] for v in ISRAEL.values()] + [v[0] for v in SERBIA.values()] + [v[0] for v in CHINA.values()] + [v[0] for v in RUSIA.values()] + [v[0] for v in ESPANA.values()] + [v[0] for v in SINGAPUR.values()] + [v[0] for v in MARRUECOS.values()] + [v[0] for v in MACEDONIA.values()] + [v[0] for v in DEFENSA.values()])
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
    bonos = {k: q[s] for k, s in BONOS.items() if s in q}
    coms = [{**q[s], "k": k, "n": n, "u": u, "contrato": q[s]["n"], "v": round(q[s]["v"] * c, 4), "prev": round(q[s]["prev"] * c, 4)}
            for k, n, s, c, u in COMS if s in q]
    europa = {k: {"idx": n, **q[s]} for k, (s, n) in EUROPA.items() if s in q}
    chile = {k: {"idx": n, **q[s]} for k, (s, n) in CHILE.items() if s in q}
    japon = {k: {"idx": n, **q[s]} for k, (s, n) in JAPON.items() if s in q}
    reino = {k: {"idx": n, **q[s]} for k, (s, n) in REINO.items() if s in q}
    canada = {k: {"idx": n, **q[s]} for k, (s, n) in CANADA.items() if s in q}
    colombia = {k: {"idx": n, **q[s]} for k, (s, n) in COLOMBIA.items() if s in q}
    turquia = {k: {"idx": n, **q[s]} for k, (s, n) in TURQUIA.items() if s in q}
    peru = {k: {"idx": n, **q[s]} for k, (s, n) in PERU.items() if s in q}
    polonia = {k: {"idx": n, **q[s]} for k, (s, n) in POLONIA.items() if s in q}
    india = {k: {"idx": n, **q[s]} for k, (s, n) in INDIA.items() if s in q}
    arabia = {k: {"idx": n, **q[s]} for k, (s, n) in ARABIA.items() if s in q}
    suiza = {k: {"idx": n, **q[s]} for k, (s, n) in SUIZA.items() if s in q}
    australia = {k: {"idx": n, **q[s]} for k, (s, n) in AUSTRALIA.items() if s in q}
    corea = {k: {"idx": n, **q[s]} for k, (s, n) in COREA.items() if s in q}
    sudafrica = {k: {"idx": n, **q[s]} for k, (s, n) in SUDAFRICA.items() if s in q}
    zelanda = {k: {"idx": n, **q[s]} for k, (s, n) in ZELANDA.items() if s in q}
    indonesia = {k: {"idx": n, **q[s]} for k, (s, n) in INDONESIA.items() if s in q}
    noruega = {k: {"idx": n, **q[s]} for k, (s, n) in NORUEGA.items() if s in q}
    suecia = {k: {"idx": n, **q[s]} for k, (s, n) in SUECIA.items() if s in q}
    tailandia = {k: {"idx": n, **q[s]} for k, (s, n) in TAILANDIA.items() if s in q}
    malasia = {k: {"idx": n, **q[s]} for k, (s, n) in MALASIA.items() if s in q}
    filipinas = {k: {"idx": n, **q[s]} for k, (s, n) in FILIPINAS.items() if s in q}
    islandia = {k: {"idx": n, **q[s]} for k, (s, n) in ISLANDIA.items() if s in q}
    hungria = {k: {"idx": n, **q[s]} for k, (s, n) in HUNGRIA.items() if s in q}
    hongkong = {k: {"idx": n, **q[s]} for k, (s, n) in HONGKONG.items() if s in q}
    chequia = {k: {"idx": n, **q[s]} for k, (s, n) in CHEQUIA.items() if s in q}
    dinamarca = {k: {"idx": n, **q[s]} for k, (s, n) in DINAMARCA.items() if s in q}
    rumania = {k: {"idx": n, **q[s]} for k, (s, n) in RUMANIA.items() if s in q}
    israel = {k: {"idx": n, **q[s]} for k, (s, n) in ISRAEL.items() if s in q}
    serbia = {k: {"idx": n, **q[s]} for k, (s, n) in SERBIA.items() if s in q}
    china = {k: {"idx": n, **q[s]} for k, (s, n) in CHINA.items() if s in q}
    rusia = {k: {"idx": n, **q[s]} for k, (s, n) in RUSIA.items() if s in q}
    espana = {k: {"idx": n, **q[s]} for k, (s, n) in ESPANA.items() if s in q}
    singapur = {k: {"idx": n, **q[s]} for k, (s, n) in SINGAPUR.items() if s in q}
    marruecos = {k: {"idx": n, **q[s]} for k, (s, n) in MARRUECOS.items() if s in q}
    macedonia = {k: {"idx": n, **q[s]} for k, (s, n) in MACEDONIA.items() if s in q}
    defensa = {k: {"idx": n, **q[s]} for k, (s, n) in DEFENSA.items() if s in q}
    return {"polonia": polonia, "india": india, "arabia": arabia, "suiza": suiza, "australia": australia, "corea": corea, "sudafrica": sudafrica, "zelanda": zelanda, "indonesia": indonesia, "noruega": noruega, "suecia": suecia, "tailandia": tailandia, "malasia": malasia, "filipinas": filipinas, "islandia": islandia, "hungria": hungria, "hongkong": hongkong, "chequia": chequia, "dinamarca": dinamarca, "rumania": rumania, "israel": israel, "serbia": serbia, "china": china, "rusia": rusia, "espana": espana, "singapur": singapur, "marruecos": marruecos, "macedonia": macedonia, "defensa": defensa, "bolsas": bolsas, "acciones": acciones, "termo": termo, "monedas": monedas, "bonos": bonos, "commodities": coms, "europa": europa, "chile": chile, "japon": japon, "reino": reino, "canada": canada, "colombia": colombia, "turquia": turquia, "peru": peru}


def cripto():
    """Las 10 criptomonedas más grandes por valor de mercado (CoinGecko)."""
    j = json.loads(get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
                       "&price_change_percentage=24h,7d,1y"))
    out = []
    for c in j:
        out.append({"s": str(c.get("symbol", "")).upper(), "n": c.get("name"), "v": c.get("current_price"), "mcap": c.get("market_cap"),
                    "d1": c.get("price_change_percentage_24h_in_currency"), "d7": c.get("price_change_percentage_7d_in_currency"),
                    "a1": c.get("price_change_percentage_1y_in_currency"), "t": c.get("last_updated")})
    if not out:
        raise ValueError("sin datos")
    return out


# Titulares de economía internacional (RSS en español). BBC Mundo es general: se filtra por palabras de economía.
FEEDS_MUNDO = [("El País", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada", False),
               ("DW", "https://rss.dw.com/xml/rss-sp-eco", False),
               ("Expansión", "https://e00-expansion.uecdn.es/rss/mercados.xml", False),
               ("France 24", "https://www.france24.com/es/econom%C3%ADa/rss", False),
               ("Euronews", "https://es.euronews.com/rss?level=vertical&name=business", False),
               ("BBC Mundo", "https://feeds.bbci.co.uk/mundo/rss.xml", True)]
ECON = r"econom|mercad|bolsa|wall street|inflaci|tasa|inter[eé]s|banco central|reserva federal|\bfed\b|\bbce\b|d[oó]lar|euro\b|petr[oó]le|arancel|comercio|exporta|importa|deuda|pib|recesi[oó]n|empleo|desempleo|precio|bitcoin|cripto|oro\b|acciones|empresa"
TEMAS_M = {"mercados": r"bolsa|wall street|acciones|[ií]ndice|mercado|nasdaq|s&p|dow jones|ibex|dax|bitcoin|cripto",
           "bancos": r"banco central|reserva federal|\bfed\b|\bbce\b|tasas? de inter[eé]s|tipos de inter[eé]s|powell|lagarde",
           "eeuu": r"estados unidos|ee\.? ?uu|trump|washington|wall street|\bfed\b|reserva federal",
           "europa": r"europ|\bbce\b|alemania|francia|espa[nñ]a|italia|reino unido|bruselas",
           "china": r"china|chin[oa]s|pek[ií]n|xi jinping|asia|jap[oó]n",
           "energia": r"petr[oó]le|gas\b|energ[ií]a|opep|crudo|brent",
           "comercio": r"arancel|comercio|exporta|importa|aduana|guerra comercial"}


def noticias_mundo(prev):
    def limpiar(t):
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip())
    def fecha(txt):
        txt = (txt or "").strip()
        try:
            d = parsedate_to_datetime(txt)
        except (TypeError, ValueError):
            try:
                d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
            except ValueError:
                return None
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    corte = datetime.now(timezone.utc) - timedelta(hours=48)
    items, fuentes = [], {}
    for medio, url, filtrar in FEEDS_MUNDO:
        try:
            raiz = ET.fromstring(get(url, tries=2, timeout=30).encode("utf-8"))
            n = 0
            for it in raiz.iter():
                if it.tag.split("}")[-1] not in ("item", "entry"):
                    continue
                h = {c.tag.split("}")[-1]: c for c in it}
                t = limpiar(h["title"].text if "title" in h else "")
                link = ((h["link"].text or h["link"].get("href") or "").strip()) if "link" in h else ""
                d = fecha(next((h[k].text for k in ("pubDate", "published", "updated", "date") if k in h), ""))
                if not t or not link.startswith("http") or not d or d < corte:
                    continue
                if filtrar and not re.search(ECON, t, re.I):
                    continue
                items.append({"t": t, "u": link, "f": medio, "h": d.isoformat(timespec="minutes"),
                              "k": [k for k, rx in TEMAS_M.items() if re.search(rx, t, re.I)]})
                n += 1
            fuentes[medio] = f"ok ({n})"
        except Exception as e:  # noqa: BLE001
            fuentes[medio] = f"error: {str(e)[:80]}"
            errores.append(f"Noticias {medio}: {e}")
    if not items:
        return prev.get("noticias") or {}
    vistos, unicos = set(), []
    for x in sorted(items, key=lambda x: x["h"], reverse=True):
        clave = re.sub(r"\W+", "", x["t"].lower())[:60]
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(x)
    return {"actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"), "fuentes": fuentes, "items": unicos[:60]}


def historia(prev_h):
    """Cierres diarios de 1 año (CNBC). Se renueva cada 3 horas como máximo."""
    try:
        al = datetime.fromisoformat(prev_h.get("actualizado", "2000-01-01T00:00+00:00"))
        if (datetime.now(timezone.utc) - al).total_seconds() < 3 * 3600 and prev_h.get("series") and prev_h.get("conv") and set(HIST) <= set(prev_h.get("claves") or []):
            return prev_h
    except Exception:  # noqa: BLE001
        pass
    series = dict(prev_h.get("series") or {})
    if not prev_h.get("conv"):  # historia vieja guardada en la unidad de CNBC: pasarla a la unidad mostrada
        for k, c in COM_CONV.items():
            if k in series and c != 1:
                series[k] = [[d, round(v * c, 4)] for d, v in series[k]]
    ok = 0
    for k, sym in HIST.items():
        try:
            pts = []
            for intento in range(3):  # a veces CNBC devuelve la serie vacía: se reintenta con una pausa
                j = json.loads(get(f"https://ts-api.cnbc.com/harmony/app/charts/1Y.json?symbol={urllib.request.quote(sym, safe='')}",
                                   tries=2, headers={"Accept": "application/json", "Referer": "https://www.cnbc.com/"}))
                for b in (j.get("barData") or {}).get("priceBars") or []:
                    t, c = str(b.get("tradeTime") or ""), b.get("close")
                    if len(t) >= 8 and c not in (None, ""):
                        pts.append([f"{t[:4]}-{t[4:6]}-{t[6:8]}", round(float(c) * COM_CONV.get(k, 1), 4)])
                if len(pts) > 20:
                    break
                pts = []
                time.sleep(3 + 3 * intento)
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
    return {"actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"), "series": series, "conv": True, "claves": list(HIST)}


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
    out = []
    for k, n, g, ys, ss, u, conv in MERCADOS:
        if k in datos:
            p, pv, t = datos[k]
            c = 1 if fuente[k] in ("BCE/Frankfurter", "CoinGecko") else conv
            out.append({"k": k, "n": n, "g": g, "u": u, "v": round(p * c, 4), "prev": round(pv * c, 4), "t": t, "f": fuente[k]})
        elif k in viejo:
            out.append(viejo[k])
    return out


def cripto_seguro(prev):
    try:
        return cripto()
    except Exception as e:  # noqa: BLE001
        errores.append(f"CoinGecko top 10: {e}")
        return prev.get("cripto") or []


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
    for k in ("bolsas", "acciones", "termo", "monedas", "bonos", "commodities", "europa", "chile", "japon", "reino", "canada", "colombia", "turquia", "peru", "polonia", "india", "arabia", "suiza", "australia", "corea", "sudafrica", "zelanda", "indonesia", "noruega", "suecia", "tailandia", "malasia", "filipinas", "islandia", "hungria", "hongkong", "chequia", "dinamarca", "rumania", "israel", "serbia", "china", "rusia", "defensa", "espana", "singapur", "marruecos", "macedonia"):  # si una sección vino vacía, queda la anterior
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
        "cripto": cripto_seguro(prev),
        "noticias": noticias_mundo(prev),
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
