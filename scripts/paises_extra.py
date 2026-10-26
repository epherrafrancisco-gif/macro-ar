"""Arma paises_extra.json: datos que se suman a todas las secciones de país de Pulso Macro (y Argentina para comparar).

Fuentes gratuitas, sin clave:
  - Banco Mundial (api.worldbank.org): PBI por habitante a paridad de poder de compra, crecimiento anual y cuenta
    corriente (% del PBI). Datos anuales: se renuevan una vez por semana.
  - OCDE (sdmx.oecd.org): inflación por rubro (alimentos, energía y núcleo), producción industrial, ventas minoristas,
    confianza de consumidores y empresas e indicador adelantado (CLI). Mensuales.
  - BIS (stats.bis.org): precio real y nominal de las viviendas (trimestral), tipo de cambio real (mensual) y crédito al
    sector privado como % del PBI (trimestral).
  - The Economist (GitHub, big-mac-data): índice Big Mac, dos veces por año.

Uso: python scripts/paises_extra.py
Nunca inventa datos: si una serie falla, queda la anterior y se anota en "errores". Las series atrasadas se sacan.
En "diag" quedan las combinaciones que devolvió la OCDE, para poder ajustar los filtros.
"""

import csv
import io
import json
import time
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paises_extra.json"
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
OECD = "https://sdmx.oecd.org/public/rest/data/"
errores = []
diag = {}

# clave de la página → códigos de cada fuente (None = la fuente no tiene ese país)
P = {  # página: (BIS, OCDE, Banco Mundial, Big Mac)
    "USA": ("US", "USA", "USA", "USA"), "EUR": ("XM", "EA20", "EMU", "EUZ"), "BRA": ("BR", "BRA", "BRA", "BRA"),
    "MEX": ("MX", "MEX", "MEX", "MEX"), "CHL": ("CL", "CHL", "CHL", "CHL"), "JPN": ("JP", "JPN", "JPN", "JPN"),
    "GBR": ("GB", "GBR", "GBR", "GBR"), "CAN": ("CA", "CAN", "CAN", "CAN"), "COL": ("CO", "COL", "COL", "COL"),
    "TUR": ("TR", "TUR", "TUR", "TUR"), "PER": ("PE", None, "PER", "PER"), "POL": ("PL", "POL", "POL", "POL"),
    "IND": ("IN", "IND", "IND", "IND"), "SAU": ("SA", "SAU", "SAU", "SAU"), "CHE": ("CH", "CHE", "CHE", "CHE"), "AUS": ("AU", "AUS", "AUS", "AUS"), "KOR": ("KR", "KOR", "KOR", "KOR"), "ZAF": ("ZA", "ZAF", "ZAF", "ZAF"), "NZL": ("NZ", "NZL", "NZL", "NZL"), "IDN": ("ID", "IDN", "IDN", "IDN"), "NOR": ("NO", "NOR", "NOR", "NOR"), "SWE": ("SE", "SWE", "SWE", "SWE"), "THA": ("TH", "THA", "THA", "THA"), "MYS": ("MY", "MYS", "MYS", "MYS"), "PHL": ("PH", "PHL", "PHL", "PHL"), "ISL": ("IS", "ISL", "ISL", "ISL"), "HUN": ("HU", "HUN", "HUN", "HUN"), "HKG": ("HK", "HKG", "HKG", "HKG"), "CZE": ("CZ", "CZE", "CZE", "CZE"), "DNK": ("DK", "DNK", "DNK", "DNK"), "ROU": ("RO", "ROU", "ROU", "ROU"), "ISR": ("IL", "ISR", "ISR", "ISR"), "SRB": ("RS", "SRB", "SRB", "SRB"), "CHN": ("CN", "CHN", "CHN", "CHN"), "RUS": ("RU", "RUS", "RUS", "RUS"), "ESP": ("ES", "ESP", "ESP", "ESP"), "MKD": ("MK", "MKD", "MKD", "MKD"), "SGP": ("SG", "SGP", "SGP", "SGP"), "MAR": ("MA", "MAR", "MAR", "MAR"), "ARG": ("AR", "ARG", "ARG", "ARG"),
}
POR = {i: {P[k][i]: k for k in P if P[k][i]} for i in range(4)}


def get(url, accept="*/*", tries=3, timeout=120):
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


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def hoy_iso():
    return date.today().isoformat()


def fresco(ult, meses):
    """¿El último período (YYYY, YYYY-MM, YYYY-Qn o YYYY-MM-DD) tiene menos de `meses` meses?"""
    h = date.today()
    if "-Q" in ult:
        y, q = int(ult[:4]), int(ult[-1])
        fin = date(y, q * 3, 28)
    elif len(ult) == 4:
        fin = date(int(ult), 12, 31)
    else:
        fin = date(int(ult[:4]), int(ult[5:7]), 28)
    return (h - fin).days <= 31 * meses


# ---------------- BIS ----------------
def bis(flujo, clave, desde):
    """CSV del BIS → {código de país: [[período, valor], ...]}."""
    txt = get(f"https://stats.bis.org/api/v1/data/{flujo}/{clave}/all?startPeriod={desde}&format=csv", "text/csv")
    out = defaultdict(list)
    for r in csv.DictReader(io.StringIO(txt)):
        pais = r.get("REF_AREA") or r.get("BORROWERS_CTY")
        v = num(r.get("OBS_VALUE"))
        if pais and v is not None and r.get("TIME_PERIOD"):
            out[pais].append([r["TIME_PERIOD"], round(v, 3)])
    return {k: sorted(v) for k, v in out.items()}


def bis_todo(data):
    paises = "+".join(P[k][0] for k in P)
    h = date.today()
    tareas = {
        "viv_real": ("WS_SPP", f"Q.{paises}.R.771", f"{h.year - 8}-Q1", 9),
        "viv_nom": ("WS_SPP", f"Q.{paises}.N.771", f"{h.year - 8}-Q1", 9),
        "tcr": ("WS_EER", f"M.R.B.{paises}", f"{h.year - 10}-01", 4),
        "credito": ("WS_TC", f"Q.{paises}.P.A.M.770.A", f"{h.year - 15}-Q1", 12),
    }
    for k, (flujo, clave, desde, meses) in tareas.items():
        try:
            res = bis(flujo, clave, desde)
            out = {}
            for cod, pts in res.items():
                pag = POR[0].get(cod)
                if pag and pts and fresco(pts[-1][0], meses):
                    out[pag] = pts
            if not out:
                raise ValueError("sin datos")
            data[k] = out
        except Exception as e:  # noqa: BLE001
            errores.append(f"BIS {k}: {e}")
        time.sleep(0.5)


# ---------------- OCDE ----------------
def oecd_rows(flujo, clave, desde):
    txt = get(f"{OECD}{flujo}/{clave}?startPeriod={desde}&format=csvfile", "text/csv")
    return list(csv.DictReader(io.StringIO(txt)))


def series_por(rows, dims):
    """Agrupa filas por país y por la combinación de `dims` → {(pais, combo): [[t, v], ...]}."""
    out = defaultdict(list)
    for r in rows:
        v = num(r.get("OBS_VALUE"))
        if v is None or not r.get("TIME_PERIOD"):
            continue
        out[(r.get("REF_AREA"), tuple(r.get(d, "") for d in dims))].append([r["TIME_PERIOD"], round(v, 3)])
    return {k: sorted(v) for k, v in out.items()}


def yoy(pts):
    """Variación contra el mismo mes del año anterior a partir de un índice mensual."""
    m = dict(pts)
    out = []
    for t, v in pts:
        y = f"{int(t[:4]) - 1}{t[4:]}"
        if y in m and m[y]:
            out.append([t, round((v / m[y] - 1) * 100, 2)])
    return out


def elegir(cands, prefs):
    """De varias series candidatas para un país, la que mejor cumple las preferencias (lista de funciones combo→bool),
    desempatando por la más reciente."""
    if not cands:
        return None
    def score(item):
        combo, pts = item
        return (sum(1 for f in prefs if f(combo)), pts[-1][0] if pts else "")
    return max(cands.items(), key=score)


def oecd_rubros(data):
    paises = "+".join(P[k][1] for k in P if P[k][1])
    h = date.today()
    dims = ["METHODOLOGY", "MEASURE", "UNIT_MEASURE", "EXPENDITURE", "ADJUSTMENT", "TRANSFORMATION"]
    rows = None
    for clave in (f"{paises}.M..CPI.PA...GY", f"{paises}.M..CPI....GY"):
        try:
            rows = oecd_rows("OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0", clave, f"{h.year - 5}-01")
            if rows:
                break
        except Exception as e:  # noqa: BLE001
            errores.append(f"OCDE rubros ({clave[-30:]}): {e}")
    if not rows:
        return
    S = series_por(rows, dims)
    diag["rubros"] = sorted({"|".join(c) for (_, c) in S})[:80]
    diag["rubros_paises"] = sorted({p for (p, _) in S})
    ult = defaultdict(dict)
    for (p, c), pts in S.items():
        if c[3] in ("CP01", "_TXCP01_NRG", "CP045_0722", "_T"):
            ult[p][f"{c[0]}|{c[3]}|{c[2]}|{c[5]}"] = pts[-1][0]
    diag["rubros_ult"] = ult
    ENERGIA = ("NRG", "CP045_0722", "_NRG", "CP0451_0452_0722", "NRG_X")
    out = {}
    for pais_o, pag in POR[1].items():
        res = {}
        for nombre, exps in (("alim", ("CP01",)), ("energia", ("CP045_0722",) + ENERGIA), ("nucleo", ("_TXCP01_NRG", "_TXNRG_01_02", "TOT_X_NRG_FOOD"))):
            c = {combo: pts for (p, combo), pts in S.items() if p == pais_o and combo[3] in exps}
            best = elegir(c, [lambda x: x[0] == "N", lambda x: x[5] == "GY", lambda x: x[2] == "PA", lambda x: x[3] == exps[0]])
            if best:
                combo, pts = best
                if combo[5] != "GY":
                    pts = yoy(pts)
                if pts and fresco(pts[-1][0], 4):
                    res[nombre] = pts[-48:]
        if res:
            out[pag] = res
    if out:
        data["rubros"] = out
    else:
        errores.append("OCDE rubros: ninguna serie útil")


def oecd_kei(data):
    paises = "+".join(P[k][1] for k in P if P[k][1])
    h = date.today()
    dims = ["MEASURE", "UNIT_MEASURE", "ACTIVITY", "ADJUSTMENT", "TRANSFORMATION"]
    rows = []
    for medidas in ("PRVM+TOVM", "CCICP+BCICP+LI"):
        try:
            rows += oecd_rows("OECD.SDD.STES,DSD_KEI@DF_KEI,4.0", f"{paises}.M.{medidas}....", f"{h.year - 6}-01")
        except Exception as e:  # noqa: BLE001
            errores.append(f"OCDE KEI {medidas}: {e}")
        time.sleep(1)
    if not rows:
        return
    S = series_por(rows, dims)
    diag["kei"] = sorted({"|".join(c) for (_, c) in S})[:60]
    ind, conf = {}, {}
    for pais_o, pag in POR[1].items():
        def serie(medida, prefs, crec):
            c = {combo: pts for (p, combo), pts in S.items() if p == pais_o and combo[0] == medida}
            best = elegir(c, prefs)
            if not best:
                return None
            combo, pts = best
            if crec and combo[4] != "GY":
                pts = yoy(pts)
            return pts if pts and fresco(pts[-1][0], 5) else None
        prod = serie("PRVM", [lambda x: x[4] == "GY", lambda x: x[2] in ("BTE", "B-E", "_T"), lambda x: x[3] in ("Y", "S")], True)
        minor = serie("TOVM", [lambda x: x[4] == "GY", lambda x: x[2] in ("G47", "G-47", "G"), lambda x: x[3] in ("Y", "S")], True)
        cons = serie("CCICP", [lambda x: x[4] in ("_Z", "N", ""), lambda x: x[3] in ("AA", "Y", "S")], False)
        emp = serie("BCICP", [lambda x: x[4] in ("_Z", "N", ""), lambda x: x[3] in ("AA", "Y", "S")], False)
        cli = serie("LI", [lambda x: x[4] in ("_Z", "N", ""), lambda x: x[3] in ("AA",)], False)
        r1 = {k: v[-60:] for k, v in (("prod", prod), ("minor", minor)) if v}
        r2 = {k: v[-60:] for k, v in (("cons", cons), ("emp", emp), ("cli", cli)) if v}
        if r1:
            ind[pag] = r1
        if r2:
            conf[pag] = r2
    try:  # confianza normalizada (100 = promedio de largo plazo) e indicador adelantado
        rows2 = oecd_rows("OECD.SDD.STES,DSD_STES@DF_CLI,4.1", f"{paises}.M.LI+CCICP+BCICP.......", f"{h.year - 6}-01")
        dims2 = ["MEASURE", "UNIT_MEASURE", "ACTIVITY", "ADJUSTMENT", "TRANSFORMATION", "TIME_HORIZ", "METHODOLOGY"]
        S2 = series_por(rows2, dims2)
        diag["cli"] = sorted({"|".join(c) for (_, c) in S2})[:40]
        for pais_o, pag in POR[1].items():
            r = {}
            for nombre, medida in (("cons", "CCICP"), ("emp", "BCICP"), ("cli", "LI")):
                c = {combo: pts for (p, combo), pts in S2.items() if p == pais_o and combo[0] == medida}
                best = elegir(c, [lambda x: x[3] == "AA", lambda x: x[1] == "IX", lambda x: x[4] in ("_Z", "")])
                if best and best[1] and fresco(best[1][-1][0], 5) and best[0][3] == "AA":
                    r[nombre] = best[1][-60:]
            if r:
                conf[pag] = r
            else:
                conf.pop(pag, None)
    except Exception as e:  # noqa: BLE001
        errores.append(f"OCDE CLI: {e}")
        conf = {p: {k: v for k, v in x.items() if k == "cli"} for p, x in conf.items()}
        conf = {p: x for p, x in conf.items() if x}
    if ind:
        data["ind"] = ind
    if conf:
        data["conf"] = conf
    if not ind and not conf:
        errores.append("OCDE KEI: ninguna serie útil")


# ---------------- Banco Mundial ----------------
def banco_mundial(data):
    prev = data.get("wb") or {}
    al = prev.get("al", "2000-01-01")
    if (date.today() - date.fromisoformat(al)).days < 7 and prev.get("ppa") and prev.get("pop") and "MAR" in prev.get("ppa", {}):
        return
    paises = ";".join(P[k][2] for k in P)
    res = {"al": hoy_iso()}
    for k, ind in (("ppa", "NY.GDP.PCAP.PP.KD"), ("crec", "NY.GDP.MKTP.KD.ZG"), ("cc", "BN.CAB.XOKA.GD.ZS"),
                   ("pop", "SP.POP.TOTL"), ("popc", "SP.POP.GROW"), ("pbiusd", "NY.GDP.MKTP.CD")):
        try:
            j = json.loads(get(f"https://api.worldbank.org/v2/country/{paises}/indicator/{ind}?format=json&per_page=2000&date=1990:{date.today().year}", "application/json"))
            out = defaultdict(list)
            for r in (j[1] if isinstance(j, list) and len(j) > 1 else []) or []:
                pag = POR[2].get(r.get("countryiso3code"))
                if pag and r.get("value") is not None:
                    out[pag].append([r["date"], round(float(r["value"]), 3)])
            if not out:
                raise ValueError("sin datos")
            res[k] = {p: sorted(v) for p, v in out.items()}
        except Exception as e:  # noqa: BLE001
            errores.append(f"Banco Mundial {k}: {e}")
            if prev.get(k):
                res[k] = prev[k]
        time.sleep(0.5)
    if any(k in res for k in ("ppa", "crec", "cc")):
        data["wb"] = res


# ---------------- Big Mac ----------------
def big_mac(data):
    txt = get("https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv", "text/csv")
    filas = list(csv.DictReader(io.StringIO(txt)))
    if not filas:
        raise ValueError("sin datos")
    ult = max(r["date"] for r in filas)
    out = {"fecha": ult, "paises": {}, "hist": {}}
    for r in filas:
        pag = POR[3].get(r.get("iso_a3"))
        if not pag:
            continue
        usd = num(r.get("dollar_price"))
        if usd is None:
            continue
        out["hist"].setdefault(pag, []).append([r["date"], round(usd, 2)])
        if r["date"] == ult:
            out["paises"][pag] = {"local": num(r.get("local_price")), "tc": num(r.get("dollar_ex")), "usd": round(usd, 2),
                                  "vs_usa": num(r.get("USD_raw")), "moneda": r.get("currency_code")}
    for k in out["hist"]:
        out["hist"][k].sort()
    if not out["paises"]:
        raise ValueError("sin datos del último relevamiento")
    data["bigmac"] = out


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    data = {k: v for k, v in prev.items() if k not in ("errores", "diag")}
    for fn in (bis_todo, oecd_rubros, oecd_kei, banco_mundial):
        try:
            fn(data)
        except Exception as e:  # noqa: BLE001
            errores.append(f"{fn.__name__}: {e}")
    try:
        big_mac(data)
    except Exception as e:  # noqa: BLE001
        errores.append(f"Big Mac: {e}")
    data["actualizado"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    data["errores"] = errores[:30]
    data["diag"] = diag
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    resumen = {k: sorted(v) if isinstance(v, dict) else v for k, v in data.items() if k in ("viv_real", "tcr", "credito", "rubros", "ind", "conf")}
    print(resumen)
    print("Big Mac:", (data.get("bigmac") or {}).get("fecha"), "Banco Mundial:", sorted((data.get("wb") or {}).get("ppa", {})))
    for e in errores:
        print("ERROR", e)


if __name__ == "__main__":
    main()
