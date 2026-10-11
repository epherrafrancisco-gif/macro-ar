"""Arma usa.json para la sección Estados Unidos de la pestaña Global.

Fuentes oficiales y gratuitas, sin clave:
  - Tesoro de EE.UU. (fiscaldata): deuda pública total, publicada cada día hábil.
  - Tesoro de EE.UU. (home.treasury.gov): curva de tasas diaria de 1 mes a 30 años.
  - BLS (Oficina de Estadísticas Laborales): inflación, inflación núcleo, desempleo,
    empleos creados, salarios y desempleo por estado. Su API sin clave permite pocas
    consultas por día: se renueva como máximo cada 12 horas.
  - BIS: tasa de la Reserva Federal (diaria), para el historial y las decisiones.
  - CNBC: sectores del S&P 500 (fondos XLK, XLE, ...), las 7 magníficas y las 50 empresas más grandes.
  - Departamento de Trabajo (DOL): pedidos semanales de seguro de desempleo (como máximo cada 12 horas).
  - Freddie Mac: tasa hipotecaria a 30 años (semanal).
  - Nasdaq: calendario de balances de las empresas grandes (como máximo cada 12 horas).
  - BEA: PBI trimestral, solo si existe el secreto BEA_KEY (clave gratis de apps.bea.gov, cargada el 11/10/2026).

Uso: python scripts/usa.py
Nunca inventa datos: si una fuente falla, queda lo que había y se anota en "errores".
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
OUT = ROOT / "usa.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
errores = []

# Reuniones de la Fed (federalreserve.gov/monetarypolicy/fomccalendars.htm): (inicio, fin)
FOMC = [("2025-01-28", "2025-01-29"), ("2025-03-18", "2025-03-19"), ("2025-05-06", "2025-05-07"), ("2025-06-17", "2025-06-18"),
        ("2025-07-29", "2025-07-30"), ("2025-09-16", "2025-09-17"), ("2025-10-28", "2025-10-29"), ("2025-12-09", "2025-12-10"),
        ("2026-01-27", "2026-01-28"), ("2026-03-17", "2026-03-18"), ("2026-04-28", "2026-04-29"), ("2026-06-16", "2026-06-17"),
        ("2026-07-28", "2026-07-29"), ("2026-09-15", "2026-09-16"), ("2026-10-27", "2026-10-28"), ("2026-12-08", "2026-12-09"),
        ("2027-01-26", "2027-01-27"), ("2027-03-16", "2027-03-17"), ("2027-04-27", "2027-04-28"), ("2027-06-08", "2027-06-09"),
        ("2027-07-27", "2027-07-28"), ("2027-09-14", "2027-09-15"), ("2027-10-26", "2027-10-27"), ("2027-12-07", "2027-12-08")]
ESTADOS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
           "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
           "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
           "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
           "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY"}
BLS_NAC = {"CUUR0000SA0": "ipc", "CUUR0000SA0L1E": "nucleo", "LNS14000000": "desemp", "CES0000000001": "empleo", "CES0500000003": "salario",
           # inflación por rubro (índices sin desestacionalizar) y vacantes de empleo (JOLTS, miles)
           "CUUR0000SAH1": "r_vivienda", "CUUR0000SAF1": "r_alimentos", "CUUR0000SA0E": "r_energia", "CUUR0000SAM": "r_salud",
           "CUUR0000SETA01": "r_autos0", "CUUR0000SETA02": "r_autosu", "CUUR0000SAA": "r_ropa", "CUUR0000SAT": "r_transporte",
           "CUUR0000SAS": "r_servicios", "JTS000000000000000JOL": "jolts"}
# Las 50 empresas más grandes del S&P 500, con su sector (para el mapa de calor)
HEAT50 = {"Tecnología": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "AMD", "ADBE", "CSCO", "ACN", "IBM", "QCOM", "INTU", "TXN", "NOW"],
          "Comunicaciones": ["GOOGL", "META", "NFLX", "DIS", "VZ"],
          "Consumo": ["AMZN", "TSLA", "COST", "HD", "WMT", "PG", "KO", "PEP", "MCD", "PM"],
          "Finanzas": ["BRK.B", "JPM", "V", "MA", "BAC", "WFC", "GS"],
          "Salud": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "AMGN"],
          "Energía e industria": ["XOM", "CVX", "GE", "CAT", "LIN"]}
SECTORES = [("XLK", "Tecnología"), ("XLC", "Comunicaciones"), ("XLY", "Consumo discrecional"), ("XLF", "Finanzas"),
            ("XLI", "Industria"), ("XLV", "Salud"), ("XLB", "Materiales"), ("XLP", "Consumo básico"), ("XLRE", "Inmobiliario"),
            ("XLU", "Servicios públicos"), ("XLE", "Energía")]
MAG7 = [("NVDA", "Nvidia"), ("MSFT", "Microsoft"), ("AAPL", "Apple"), ("AMZN", "Amazon"), ("GOOGL", "Alphabet (Google)"),
        ("META", "Meta"), ("TSLA", "Tesla")]


def get(url, tries=3, timeout=60, data=None, headers=None):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Accept": "*/*", **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise last


def deuda():
    base = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    j = json.loads(get(f"{base}?fields=record_date,tot_pub_debt_out_amt&sort=-record_date&page[size]=40"))
    rows = [(r["record_date"], float(r["tot_pub_debt_out_amt"])) for r in j["data"]]
    hace = (date.fromisoformat(rows[0][0]) - timedelta(days=365)).isoformat()
    j2 = json.loads(get(f"{base}?fields=record_date,tot_pub_debt_out_amt&filter=record_date:lte:{hace}&sort=-record_date&page[size]=1"))
    a = rows[0]
    b = rows[-1]  # ~40 días hábiles antes: ritmo de crecimiento reciente
    seg = (date.fromisoformat(a[0]) - date.fromisoformat(b[0])).days * 86400
    return {"fecha": a[0], "monto": a[1], "por_seg": round((a[1] - b[1]) / seg, 2) if seg else None,
            "hace_un_anio": float(j2["data"][0]["tot_pub_debt_out_amt"]) if j2.get("data") else None,
            "fecha_anio": j2["data"][0]["record_date"] if j2.get("data") else None}


def curva():
    def anio(y):
        txt = get(f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all"
                  f"?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv")
        return list(csv.DictReader(io.StringIO(txt)))
    hoy = date.today()
    filas = anio(hoy.year)
    if not filas:
        raise ValueError("sin datos")
    plazos = ["1 Mo", "3 Mo", "6 Mo", "1 Yr", "2 Yr", "3 Yr", "5 Yr", "7 Yr", "10 Yr", "20 Yr", "30 Yr"]
    etiq = ["1M", "3M", "6M", "1A", "2A", "3A", "5A", "7A", "10A", "20A", "30A"]
    f2d = lambda s: datetime.strptime(s, "%m/%d/%Y").date()
    ult = max(filas, key=lambda r: f2d(r["Date"]))
    objetivo = f2d(ult["Date"]) - timedelta(days=365)
    previas = [r for r in anio(objetivo.year) if f2d(r["Date"]) <= objetivo]
    ant = max(previas, key=lambda r: f2d(r["Date"])) if previas else None
    val = lambda r: [float(r[p]) if r.get(p) not in (None, "") else None for p in plazos]
    return {"plazos": etiq, "hoy": val(ult), "fecha": f2d(ult["Date"]).isoformat(),
            "ant": val(ant) if ant else None, "fecha_ant": f2d(ant["Date"]).isoformat() if ant else None}


def bls(series, desde):
    body = json.dumps({"seriesid": series, "startyear": str(desde), "endyear": str(date.today().year)}).encode()
    j = json.loads(get("https://api.bls.gov/publicAPI/v1/timeseries/data/", data=body, headers={"Content-type": "application/json"}))
    if j.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(f"{j.get('status')}: {' '.join(j.get('message') or [])[:200]}")
    out = {}
    for s in j["Results"]["series"]:
        pts = []
        for d in s["data"]:
            if d["period"].startswith("M") and d["period"] != "M13" and d["value"] not in ("-", ""):
                pts.append([f"{d['year']}-{d['period'][1:]}", float(d["value"])])
        out[s["seriesID"]] = sorted(pts)
    return out


def bis_fed():
    txt = get(f"https://stats.bis.org/api/v1/data/WS_CBPOL/D.US/all?startPeriod={date.today().year - 6}-01-01&format=csv", timeout=90)
    pts = sorted((r["TIME_PERIOD"], float(r["OBS_VALUE"])) for r in csv.DictReader(io.StringIO(txt))
                 if r.get("OBS_VALUE") not in (None, "", "NaN"))
    if not pts:
        raise ValueError("sin datos")
    mensual = {}
    for f, v in pts:
        mensual[f[:7]] = v
    def tasa_al(dia):
        v = None
        for f, x in pts:
            if f <= dia:
                v = x
        return v
    decisiones = []
    hoy = date.today().isoformat()
    for ini, fin in FOMC:
        despues = (date.fromisoformat(fin) + timedelta(days=3)).isoformat()
        if despues > pts[-1][0] or fin > hoy:
            continue
        a, b = tasa_al((date.fromisoformat(ini) - timedelta(days=1)).isoformat()), tasa_al(despues)
        if a is not None and b is not None:
            decisiones.append({"fecha": fin, "antes": a, "despues": b})
    proxima = next(({"inicio": i, "fin": f} for i, f in FOMC if f >= hoy), None)
    return {"actual": pts[-1][1], "al": pts[-1][0], "mensual": sorted(mensual.items()), "decisiones": decisiones[-8:][::-1], "proxima": proxima}


def cnbc(symbols):
    num = lambda x: float(str(x).replace(",", "").replace("%", "").strip())
    j = json.loads(get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols="
                       + urllib.request.quote("|".join(symbols), safe="") + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1",
                       tries=2, headers={"Accept": "application/json", "Referer": "https://www.cnbc.com/"}))
    out = {}
    for r in ((j.get("FormattedQuoteResult") or {}).get("FormattedQuote")) or []:
        try:
            out[r["symbol"]] = {"v": num(r["last"]), "prev": num(r["previous_day_closing"]), "t": str(r.get("last_time") or ""),
                                "mcap": r.get("mktcapView") or r.get("mktcap") or None}
        except Exception:  # noqa: BLE001
            continue
    return out


def claims():
    """Pedidos semanales de seguro de desempleo (DOL, suma de los estados, sin desestacionalizar)."""
    txt = get("https://oui.doleta.gov/unemploy/csv/ar539.csv", timeout=120)
    ini, cont = {}, {}
    desde = (date.today() - timedelta(days=760)).isoformat()
    for r in csv.DictReader(io.StringIO(txt)):
        f = r.get("rptdate") or ""
        if f < desde:
            continue
        try:
            ini[f] = ini.get(f, 0) + float(r.get("c3") or 0)
            cont[f] = cont.get(f, 0) + float(r.get("c8") or 0)
        except ValueError:
            continue
    fechas = sorted(ini)
    if len(fechas) < 10:
        raise ValueError("sin datos")
    return {"iniciales": [[f, ini[f]] for f in fechas], "continuos": [[f, cont[f]] for f in fechas]}


def hipotecaria():
    """Tasa hipotecaria fija a 30 años (Freddie Mac, encuesta semanal)."""
    txt = get("https://www.freddiemac.com/pmms/docs/PMMS_history.csv")
    pts = []
    for r in csv.DictReader(io.StringIO(txt)):
        try:
            m, d, y = r["date"].strip().split("/")
            if r.get("pmms30", "").strip():
                pts.append([f"{y}-{int(m):02d}-{int(d):02d}", float(r["pmms30"])])
        except (KeyError, ValueError):
            continue
    pts.sort()
    if not pts:
        raise ValueError("sin datos")
    return pts[-260:]


def balances():
    """Próximos balances de empresas grandes (Nasdaq), para los próximos 14 días."""
    out = []
    for i in range(0, 15):
        dia = date.today() + timedelta(days=i)
        if dia.weekday() >= 5:
            continue
        try:
            j = json.loads(get(f"https://api.nasdaq.com/api/calendar/earnings?date={dia.isoformat()}", tries=2, timeout=30,
                               headers={"Accept": "application/json", "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"}))
        except Exception as e:  # noqa: BLE001
            errores.append(f"Nasdaq {dia}: {e}")
            continue
        for r in ((j.get("data") or {}).get("rows")) or []:
            try:
                mcap = float(str(r.get("marketCap") or "0").replace("$", "").replace(",", "") or 0)
            except ValueError:
                mcap = 0
            if mcap >= 50e9:
                out.append({"f": dia.isoformat(), "s": r.get("symbol"), "n": r.get("name"), "mcap": mcap,
                            "h": {"time-pre-market": "antes de la apertura", "time-after-hours": "después del cierre"}.get(r.get("time"), ""),
                            "eps": r.get("epsForecast") or "", "q": r.get("fiscalQuarterEnding") or ""})
        time.sleep(0.5)
    return sorted(out, key=lambda x: (x["f"], -x["mcap"]))


def pbi():
    """PBI real de EE.UU.: variación trimestral anualizada (BEA, tabla NIPA T10101). Necesita BEA_KEY."""
    key = os.environ.get("BEA_KEY", "").strip()
    if not key:
        return None
    anios = ",".join(str(y) for y in range(date.today().year - 6, date.today().year + 1))
    j = json.loads(get(f"https://apps.bea.gov/api/data?UserID={key}&method=GetData&DataSetName=NIPA&TableName=T10101"
                       f"&Frequency=Q&Year={anios}&ResultFormat=JSON", timeout=90))
    res = (j.get("BEAAPI") or {}).get("Results") or {}
    if res.get("Error"):
        raise ValueError(str(res["Error"])[:200])
    pts = sorted((d["TimePeriod"], float(d["DataValue"].replace(",", ""))) for d in res.get("Data", []) if str(d.get("LineNumber")) == "1")
    if not pts:
        raise ValueError("sin datos")
    return [[t, v] for t, v in pts]


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    data = dict(prev)
    for clave, fn in (("deuda", deuda), ("curva", curva), ("fed", bis_fed)):
        try:
            data[clave] = fn()
        except Exception as e:  # noqa: BLE001
            errores.append(f"{clave}: {e}")
    # BLS: como máximo cada 12 horas (la API sin clave tiene un límite diario)
    try:
        al = datetime.fromisoformat(prev.get("bls_al", "2000-01-01T00:00+00:00"))
        viejo = (datetime.now(timezone.utc) - al).total_seconds() > 12 * 3600
    except Exception:  # noqa: BLE001
        viejo = True
    if viejo or not prev.get("bls") or "jolts" not in (prev.get("bls") or {}):
        try:
            nac = bls(list(BLS_NAC), date.today().year - 6)
            b = {campo: nac.get(sid, []) for sid, campo in BLS_NAC.items()}
            if not b["ipc"]:
                raise ValueError("sin inflación")
            ids = {f"LASST{f}0000000000003": ab for f, ab in ESTADOS.items()}
            est = {}
            claves = list(ids)
            for i in range(0, len(claves), 25):
                r = bls(claves[i:i + 25], date.today().year - 1)
                for sid, pts in r.items():
                    if pts:
                        est[ids[sid]] = pts[-1]
                time.sleep(1)
            data["bls"] = b
            if est:
                data["estados"] = est
            data["bls_al"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
        except Exception as e:  # noqa: BLE001
            errores.append(f"BLS: {e}")
    try:
        q = cnbc([s for s, _ in SECTORES] + [s for s, _ in MAG7])
        if q:
            data["sectores"] = [{"s": s, "n": n, **q[s]} for s, n in SECTORES if s in q]
            data["mag7"] = [{"s": s, "n": n, **q[s]} for s, n in MAG7 if s in q]
    except Exception as e:  # noqa: BLE001
        errores.append(f"CNBC: {e}")
    try:
        todos = [x for l in HEAT50.values() for x in l]
        q = {}
        for i in range(0, len(todos), 25):
            q.update(cnbc(todos[i:i + 25]))
        if q:
            data["heat"] = [{"g": g, "s": x, **q[x]} for g, l in HEAT50.items() for x in l if x in q]
    except Exception as e:  # noqa: BLE001
        errores.append(f"CNBC 50: {e}")
    for clave, fn in (("hipotecaria", hipotecaria), ("pbi", pbi)):
        try:
            r = fn()
            if r:
                data[clave] = r
        except Exception as e:  # noqa: BLE001
            errores.append(f"{clave}: {e}")
    # DOL y Nasdaq: como máximo cada 12 horas
    for clave, fn in (("pedidos", claims), ("balances", balances)):
        try:
            al = datetime.fromisoformat((data.get(clave + "_al") or "2000-01-01T00:00+00:00"))
            if (datetime.now(timezone.utc) - al).total_seconds() < 12 * 3600 and data.get(clave):
                continue
        except Exception:  # noqa: BLE001
            pass
        try:
            r = fn()
            if r:
                data[clave] = r
                data[clave + "_al"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
        except Exception as e:  # noqa: BLE001
            errores.append(f"{clave}: {e}")
    data["actualizado"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    data["errores"] = errores[:30]
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("deuda", bool(data.get("deuda")), "curva", bool(data.get("curva")), "fed", bool(data.get("fed")),
          "bls", bool(data.get("bls")), "estados", len(data.get("estados") or {}), "sectores", len(data.get("sectores") or []),
          "heat", len(data.get("heat") or []), "pedidos", bool(data.get("pedidos")), "hipotecaria", bool(data.get("hipotecaria")),
          "balances", len(data.get("balances") or []), "pbi", bool(data.get("pbi")))
    for e in errores:
        print("ERROR", e)


if __name__ == "__main__":
    main()
