"""Arma geovivo.json para el Monitor y el Monitor de geopolítica de Pulso Macro (pulsomacro.com.ar/monitor/).

Tres fuentes, todas con uso comercial permitido citándolas:
  - GDELT 2.0 (gdeltproject.org): eventos de conflicto codificados por máquina a partir de noticias de todo el mundo,
    un archivo cada 15 minutos. Se toman las últimas 2 horas, solo combates (códigos CAMEO 19x), violencia masiva (20x)
    y atentados con bomba (183), y solo en países con guerras o conflictos en curso (geopolitica.json). Son REPORTES DE
    PRENSA: pueden tener errores de la codificación automática; la página lo aclara.
  - NASA FIRMS: focos de calor detectados por el satélite NOAA-20 (VIIRS) en las últimas 24 horas, archivo público sin
    clave. Solo se guardan los que caen en zonas de guerra (ZONAS). El satélite no distingue un incendio, una quema
    agrícola o una explosión: la página lo dice.
  - FMI PortWatch: buques por día que cruzan cada paso marítimo clave (de datos AIS satelitales de la ONU). Viene con
    unos días de atraso y se publica una vez por semana: se muestra con su fecha. Se renueva cada 6 horas.

Si una fuente falla, queda lo de la corrida anterior (con su fecha). Nunca se inventa nada.
Uso: python scripts/geovivo.py
"""

import csv
import io
import json
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "geovivo.json"
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"


def get(url, timeout=60, tries=2):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + 3 * i)
    raise last


# ---------------------------------------------------------------- países
# FIPS 10-4 (lo que usa GDELT) -> ISO3, para los países que aparecen en la lista de conflictos.
FIPS = {"AF": "AFG", "AO": "AGO", "AE": "ARE", "AR": "ARG", "AM": "ARM", "AJ": "AZE", "BY": "BDI", "BN": "BEN", "UV": "BFA",
        "BG": "BGD", "BA": "BHR", "BO": "BLR", "BH": "BLZ", "BL": "BOL", "BR": "BRA", "BT": "BTN", "CT": "CAF", "CH": "CHN",
        "IV": "CIV", "CM": "CMR", "CG": "COD", "CO": "COL", "AG": "DZA", "EC": "ECU", "EG": "EGY", "ER": "ERI", "ET": "ETH",
        "FR": "FRA", "GG": "GEO", "GA": "GMB", "GT": "GTM", "HO": "HND", "HA": "HTI", "ID": "IDN", "IN": "IND", "IR": "IRN",
        "IZ": "IRQ", "IS": "ISR", "JM": "JAM", "JO": "JOR", "KE": "KEN", "KU": "KWT", "LA": "LAO", "LE": "LBN", "LY": "LBY",
        "CE": "LKA", "MO": "MAR", "MX": "MEX", "ML": "MLI", "BM": "MMR", "MZ": "MOZ", "MR": "MRT", "MY": "MYS", "NG": "NER",
        "NI": "NGA", "NU": "NIC", "MU": "OMN", "PK": "PAK", "PE": "PER", "RP": "PHL", "PP": "PNG", "PA": "PRY", "WE": "PSE",
        "GZ": "PSE", "QA": "QAT", "RS": "RUS", "RW": "RWA", "SA": "SAU", "SU": "SDN", "SG": "SEN", "ES": "SLV", "SO": "SOM",
        "OD": "SSD", "SY": "SYR", "CD": "TCD", "TO": "TGO", "TH": "THA", "TI": "TJK", "TS": "TUN", "TU": "TUR", "TZ": "TZA",
        "UG": "UGA", "UP": "UKR", "US": "USA", "VE": "VEN", "YM": "YEM"}
NOMBRE = {"AFG": "Afganistán", "AGO": "Angola", "ARE": "Emiratos Árabes", "ARG": "Argentina", "ARM": "Armenia", "AZE": "Azerbaiyán",
          "BDI": "Burundi", "BEN": "Benín", "BFA": "Burkina Faso", "BGD": "Bangladés", "BHR": "Baréin", "BLR": "Bielorrusia",
          "BLZ": "Belice", "BOL": "Bolivia", "BRA": "Brasil", "BTN": "Bután", "CAF": "Rep. Centroafricana", "CHN": "China",
          "CIV": "Costa de Marfil", "CMR": "Camerún", "COD": "Congo", "COL": "Colombia", "DZA": "Argelia", "ECU": "Ecuador",
          "EGY": "Egipto", "ERI": "Eritrea", "ETH": "Etiopía", "FRA": "Francia", "GEO": "Georgia", "GMB": "Gambia",
          "GTM": "Guatemala", "HND": "Honduras", "HTI": "Haití", "IDN": "Indonesia", "IND": "India", "IRN": "Irán", "IRQ": "Irak",
          "ISR": "Israel", "JAM": "Jamaica", "JOR": "Jordania", "KEN": "Kenia", "KWT": "Kuwait", "LAO": "Laos", "LBN": "Líbano",
          "LBY": "Libia", "LKA": "Sri Lanka", "MAR": "Marruecos", "MEX": "México", "MLI": "Malí", "MMR": "Myanmar",
          "MOZ": "Mozambique", "MRT": "Mauritania", "MYS": "Malasia", "NER": "Níger", "NGA": "Nigeria", "NIC": "Nicaragua",
          "OMN": "Omán", "PAK": "Pakistán", "PER": "Perú", "PHL": "Filipinas", "PNG": "Papúa Nueva Guinea", "PRY": "Paraguay",
          "PSE": "Palestina", "QAT": "Catar", "RUS": "Rusia", "RWA": "Ruanda", "SAU": "Arabia Saudita", "SDN": "Sudán",
          "SEN": "Senegal", "SLV": "El Salvador", "SOM": "Somalia", "SSD": "Sudán del Sur", "SYR": "Siria", "TCD": "Chad",
          "TGO": "Togo", "THA": "Tailandia", "TJK": "Tayikistán", "TUN": "Túnez", "TUR": "Turquía", "TZA": "Tanzania",
          "UGA": "Uganda", "UKR": "Ucrania", "USA": "Estados Unidos", "VEN": "Venezuela", "YEM": "Yemen"}
# Países que participan de guerras lejos de casa (o en las que solo hay choques chicos): ahí un "combate" de GDELT
# casi siempre es otra cosa (policía, política), así que no se cuentan aunque estén en la lista.
NO_TEATRO = {"USA", "FRA", "CHN", "IND", "BRA", "ARG", "BLZ", "GBR", "ARE", "QAT", "KWT", "BHR", "OMN", "JOR", "MYS", "TUN"}

# Tipo de evento CAMEO -> texto corto en español
CAMEO = {"183": "Atentado con bomba", "190": "Combates", "191": "Bloqueo militar", "192": "Ocupación de territorio",
         "193": "Combates con armas livianas", "194": "Artillería y tanques", "195": "Ataque aéreo", "196": "Violación de la tregua",
         "200": "Violencia masiva", "201": "Expulsión masiva", "202": "Matanza", "203": "Limpieza étnica",
         "204": "Armas de destrucción masiva"}


def teatros():
    """ISO3 de los países donde hay guerra o conflicto armado según geopolitica.json."""
    try:
        g = json.loads((ROOT / "geopolitica.json").read_text())
        out = set()
        for c in g["conflictos"]["lista"]:
            if not c.get("iso"):
                continue
            if c.get("nivel") in ("mayor", "menor", "conflicto"):
                out.add(c["iso"][0])
            if c.get("nivel") == "mayor":
                out.update(c["iso"])
        return out - NO_TEATRO
    except Exception:  # noqa: BLE001
        return set()


# ---------------------------------------------------------------- GDELT
GDELT = "http://data.gdeltproject.org/gdeltv2/"


def gdelt(prev):
    ok = teatros()
    if not ok:
        raise RuntimeError("sin lista de países en guerra")
    last = get(GDELT + "lastupdate.txt", timeout=30).decode().split()
    url = next(x for x in last if x.endswith(".export.CSV.zip"))
    stamp = url.rsplit("/", 1)[1][:14]
    t0 = datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    ev, vistos, bajados = {}, set(), 0
    for k in range(8):                      # últimas 2 horas (8 archivos de 15 minutos)
        ts = (t0 - timedelta(minutes=15 * k)).strftime("%Y%m%d%H%M%S")
        try:
            z = zipfile.ZipFile(io.BytesIO(get(f"{GDELT}{ts}.export.CSV.zip", timeout=60)))
        except Exception:  # noqa: BLE001
            continue
        bajados += 1
        txt = z.read(z.namelist()[0]).decode("utf-8", "replace")
        for row in csv.reader(io.StringIO(txt), delimiter="\t"):
            if len(row) < 61:
                continue
            code, root = row[26], row[28]
            if not (root in ("19", "20") or code == "183") or row[25] != "1":   # solo el hecho principal de cada nota
                continue
            iso = FIPS.get(row[53])
            if iso not in ok or row[51] not in ("3", "4", "2"):   # ciudad o provincia (no "todo el país")
                continue
            try:
                lat, lon = float(row[56]), float(row[57])
            except ValueError:
                continue
            url_n = row[60]
            if url_n in vistos:
                continue
            vistos.add(url_n)
            dom = urllib.parse.urlparse(url_n).netloc.lower().removeprefix("www.")
            lugar = row[52].split(",")[0].strip()
            tipo = CAMEO.get(code) or CAMEO.get(root + "0") or "Combates"
            clave = (tipo, row[58] or lugar)
            when = int(datetime.strptime(row[59], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp())
            e = ev.get(clave)
            if e:
                e[8] += 1
                if when > e[0]:
                    e[0] = when
                continue
            ev[clave] = [when, tipo, round(lat, 3), round(lon, 3), lugar, iso, NOMBRE.get(iso, iso), dom, 1]
    if not bajados:
        raise RuntimeError("no bajó ningún archivo")
    lista = sorted(ev.values(), key=lambda e: -e[0])[:400]
    # [cuándo (unix), tipo, lat, lon, lugar, ISO3, país, medio, cuántas notas]
    return {"t": int(t0.timestamp()), "archivos": bajados, "ev": lista,
            "fuente": "GDELT Project (gdeltproject.org)"}


# ---------------------------------------------------------------- NASA FIRMS
FIRMS = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv"
# [clave, nombre, [[oeste, sur, este, norte], ...]]. Solo frentes donde un foco de calor suele ser combate o bombardeo:
# en noviembre-abril el Sahel, Sudán rural, el Congo y Somalia arden por quemas de pastizales y los números se dispararían
# sin decir nada de la guerra (probado 11/11/2026: Sudán entero daba 8.298 focos y el frente ucraniano 1). Por eso en Sudán
# solo las ciudades sitiadas o en disputa.
ZONAS = [
    ["ucr", "Frente Rusia-Ucrania", [[31.0, 46.0, 40.5, 51.5]]],
    ["gaz", "Gaza y sur del Líbano", [[34.2, 31.2, 34.6, 31.65], [35.1, 33.0, 35.9, 33.5]]],
    ["sdn", "Sudán: El Fasher, Jartum y El Obeid", [[25.15, 13.5, 25.55, 13.8], [32.35, 15.4, 32.75, 15.8], [30.05, 13.05, 30.35, 13.3]]],
    ["mmr", "Myanmar", [[92.0, 16.0, 101.0, 28.0]]],
]


def firms():
    txt = get(FIRMS, timeout=120).decode("utf-8", "replace")
    rd = csv.DictReader(io.StringIO(txt))
    cnt = [0] * len(ZONAS)
    pts = []
    total = 0
    for r in rd:
        total += 1
        try:
            la, lo = float(r["latitude"]), float(r["longitude"])
        except (KeyError, ValueError):
            continue
        for i, (_, _, cajas) in enumerate(ZONAS):
            if any(w <= lo <= e and s <= la <= n for (w, s, e, n) in cajas):
                if r.get("confidence", "n").lower() in ("l", "low"):
                    break
                cnt[i] += 1
                hh = (r.get("acq_time") or "").zfill(4)
                pts.append([round(la, 3), round(lo, 3), i, f"{r.get('acq_date', '')} {hh[:2]}:{hh[2:]}"])
                break
    if total < 100:
        raise RuntimeError(f"archivo casi vacío ({total} filas)")
    pts.sort(key=lambda p: p[3], reverse=True)
    return {"t": int(time.time()), "zonas": [[z[0], z[1], z[2], cnt[i]] for i, z in enumerate(ZONAS)],
            "p": pts[:2500], "global": total,
            "fuente": "NASA FIRMS, satélite NOAA-20 (VIIRS), últimas 24 horas"}


# ---------------------------------------------------------------- FMI PortWatch
PW = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
PASOS = [["ormuz", "Estrecho de Ormuz", ("hormuz",)], ["bab", "Bab el-Mandeb", ("mandeb",)], ["suez", "Canal de Suez", ("suez",)],
         ["malaca", "Estrecho de Malaca", ("malacca",)], ["panama", "Canal de Panamá", ("panama",)],
         ["bosforo", "Bósforo", ("bosporus", "bosphorus")], ["cabo", "Cabo de Buena Esperanza", ("good hope",)],
         ["gib", "Gibraltar", ("gibraltar",)]]


def arcgis(capa, where, campos="*", orden=None):
    out, off = [], 0
    while True:
        q = {"where": where, "outFields": campos, "f": "json", "resultOffset": off, "resultRecordCount": 1000}
        if orden:
            q["orderByFields"] = orden
        j = json.loads(get(PW + capa + "/FeatureServer/0/query?" + urllib.parse.urlencode(q), timeout=90))
        if "error" in j:
            raise RuntimeError(str(j["error"])[:200])
        f = [x["attributes"] for x in j.get("features", [])]
        out += f
        if not j.get("exceededTransferLimit") or not f:
            return out
        off += len(f)


def fecha(v):
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    return str(v)[:10]


def portwatch():
    db = arcgis("PortWatch_chokepoints_database", "1=1", "portid,portname")
    ids = {}
    for k, n, claves in PASOS:
        for r in db:
            if any(c in str(r.get("portname", "")).lower() for c in claves):
                ids[k] = r["portid"]
                break
    if not ids:
        raise RuntimeError("no encontró los pasos")
    desde = "2025-01-01"
    where = "(" + " OR ".join(f"portid='{v}'" for v in ids.values()) + f") AND date >= DATE '{desde}'"
    filas = arcgis("Daily_Chokepoints_Data", where, "portid,date,n_tanker,n_total", "date")
    por = {}
    for r in filas:
        por.setdefault(r["portid"], []).append((fecha(r["date"]), r.get("n_tanker") or 0, r.get("n_total") or 0))
    out, ult = [], ""
    for k, n, _ in PASOS:
        s = sorted(por.get(ids.get(k), []))
        if not s:
            continue
        a25 = [x[1] for x in s if x[0].startswith("2025")]
        u = s[-1]
        ult = max(ult, u[0])
        out.append({"k": k, "n": n, "f": u[0], "v": u[1], "tot": u[2], "p": round(sum(a25) / len(a25), 1) if a25 else None,
                    "s": [[x[0], x[1]] for x in s[-90:]]})
    return {"t": int(time.time()), "ult": ult, "p": out,
            "fuente": "FMI PortWatch (portwatch.imf.org), con datos AIS de la Plataforma Global de la ONU"}


# ---------------------------------------------------------------- armado
def main():
    try:
        prev = json.loads(OUT.read_text())
    except Exception:  # noqa: BLE001
        prev = {}
    out = {"t": int(time.time()), "err": {}}
    for k, fn, cada in (("gdelt", gdelt, 0), ("firms", firms, 0), ("pasos", portwatch, 6 * 3600)):
        p = prev.get(k)
        if p and cada and time.time() - p.get("t", 0) < cada:
            out[k] = p
            continue
        try:
            out[k] = fn(prev) if fn is gdelt else fn()
        except Exception as e:  # noqa: BLE001
            out["err"][k] = str(e)[:300]
            if p:
                out[k] = p
    for k in ("gdelt", "firms", "pasos"):
        v = out.get(k)
        n = len(v.get("ev", v.get("p", []))) if v else 0
        print(k, "ok" if k not in out["err"] else "ERROR " + out["err"][k], n)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
