"""Historia diaria de precios para el Simulador de inversión histórica.

Salida:
  - historia.json: índice liviano (fechas hábiles, MEP propio, CER, y la lista de activos con nombre y tipo).
  - historia/<TICKER>.json: {"d": [fechas], "c": [cierres]} de cada activo (la página lo baja solo al elegirlo).
Fuentes:
  - Open BYMADATA (acceso gratuito y público de BYMA, la dueña del dato): la lista de acciones y CEDEARs en pesos sale
    de los paneles (leading-equity, general-equity, cedears) y la historia de .../chart/historical-series/history
    (?symbol=GGAL%2024HS&resolution=D&from=&to=). Da ~2 años: lo más viejo se conserva de las corridas anteriores.
  - Merval: .../chart/index-historical-series/history?symbol=M (S&P Merval re-expresado a la base del MSCI Merval);
    desde el 19/10/2026, el MSCI Merval de data.json.
  - Dólar MEP del día: calculado por Pulso Macro con AL30 ÷ AL30D (si falta, GD30 ÷ GD30D), cierres de BYMA.
  - CER diario: BCRA (API de Estadísticas, serie 30), para ajustar por inflación.
Corrida diaria: los activos que ya tienen historia solo piden los últimos 45 días (BYMA re-ajusta su historia por
pagos y splits: lo guardado se escala para empalmar). Los nuevos piden todo. Hay un tope de tiempo: lo que no llegue
se completa en la corrida siguiente.
Si un activo tiene un salto de más de 45 % en un día (cambio de ratio de un CEDEAR, split), se guarda solo desde ahí.
"""
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "historia.json"
DIR = ROOT / "historia"
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
BYMA = "https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/"
H_BYMA = {"Origin": "https://open.bymadata.com.ar", "Referer": "https://open.bymadata.com.ar/"}
DESDE = date(2019, 1, 1)
MERVAL_BASE_FECHA = "2026-10-16"
MERVAL_FACTOR = 100000 / 2843310.56
TOPE_SEG = 32 * 60  # el workflow corta a los 45 min

BONOS = [["AL29", "Bonar 2029"], ["AL30", "Bonar 2030"], ["AL35", "Bonar 2035"], ["AE38", "Bonar 2038"], ["AL41", "Bonar 2041"],
         ["GD29", "Global 2029"], ["GD30", "Global 2030"], ["GD35", "Global 2035"], ["GD38", "Global 2038"], ["GD41", "Global 2041"],
         ["GD46", "Global 2046"]]
# Nombres para el buscador (BYMA no los manda). Lo que no está acá se muestra con el ticker.
NOMBRES = {
    # acciones argentinas
    "GGAL": "Grupo Galicia", "YPFD": "YPF", "PAMP": "Pampa Energía", "BMA": "Banco Macro", "TXAR": "Ternium Argentina",
    "ALUA": "Aluar", "CEPU": "Central Puerto", "COME": "Comercial del Plata", "CRES": "Cresud", "EDN": "Edenor",
    "LOMA": "Loma Negra", "MIRG": "Mirgor", "SUPV": "Supervielle", "TECO2": "Telecom Argentina", "TGNO4": "TGN",
    "TGSU2": "TGS", "TRAN": "Transener", "VALO": "Grupo Valores", "BYMA": "BYMA", "METR": "Metrogas", "BBAR": "BBVA Argentina",
    "ECOG": "Ecogas", "AGRO": "Agrometal", "AUSO": "Autopistas del Sol", "BHIP": "Banco Hipotecario", "BOLT": "Boldt",
    "BPAT": "Banco Patagonia", "CADO": "Carlos Casado", "CAPX": "Capex", "CARC": "Carboclor", "CECO2": "Endesa Costanera",
    "CELU": "Celulosa Argentina", "CGPA2": "Camuzzi Gas Pampeana", "CTIO": "Consultatio", "CVH": "Cablevisión Holding",
    "DGCE": "Distribuidora Gas Centro", "DGCU2": "Distribuidora Gas Cuyana", "DOME": "Domec", "DYCA": "Dycasa",
    "EDLH": "Edelap", "FERR": "Ferrum", "FIPL": "Fiplasto", "GAMI": "Gami", "GARO": "Garovaglio y Zorraquín",
    "GBAN": "Gas Natural Ban", "GCDI": "GCDI (ex TGLT)", "GCLA": "Grupo Clarín", "GRIM": "Grimoldi", "HARG": "Holcim Argentina",
    "HAVA": "Havanna", "INAG": "Insumos Agroquímicos", "INTR": "Compañía Introductora", "INVJ": "Inversora Juramento",
    "IRSA": "IRSA", "LEDE": "Ledesma", "LONG": "Longvie", "MOLA": "Molinos Agro", "MOLI": "Molinos Río de la Plata",
    "MORI": "Morixe", "OEST": "Autopistas del Oeste", "PATA": "Importadora Patagonia", "POLL": "Polledo", "RICH": "Laboratorios Richmond",
    "RIGO": "Rigolleau", "ROSE": "Instituto Rosenbusch", "SAMI": "San Miguel", "SEMI": "Molinos Juan Semino", "VIST": "Vista Energy",
    "ZOOT": "Zoo Logic", "A3": "A3 Mercados", "CAPU": "Caputo", "PGR": "Phoenix Global Resources", "HSAT": "Hispasat",
    "MTR": "Matba Rofex", "ESME": "Esmeralda", "IEB": "IEB Construcciones", "REGE": "García Reguera",
    # CEDEARs
    "SPY": "S&P 500 (SPY)", "QQQ": "Nasdaq 100 (QQQ)", "DIA": "Dow Jones (DIA)", "IWM": "Russell 2000 (IWM)",
    "EEM": "Mercados emergentes (EEM)", "EWZ": "Brasil (EWZ)", "XLE": "Energía de EE.UU. (XLE)", "XLF": "Finanzas de EE.UU. (XLF)",
    "GLD": "Oro (GLD)", "SLV": "Plata (SLV)", "ARKK": "ARK Innovation", "IBIT": "Bitcoin (IBIT)", "ETHA": "Ether (ETHA)",
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "GOOGL": "Alphabet (Google)", "GOOG": "Alphabet (Google)",
    "AMZN": "Amazon", "META": "Meta (Facebook)", "TSLA": "Tesla", "MELI": "Mercado Libre", "KO": "Coca-Cola", "PEP": "PepsiCo",
    "MCD": "McDonald's", "WMT": "Walmart", "COST": "Costco", "DIS": "Disney", "NFLX": "Netflix", "NKE": "Nike", "SBUX": "Starbucks",
    "V": "Visa", "MA": "Mastercard", "PYPL": "PayPal", "JPM": "JPMorgan", "BAC": "Bank of America", "C": "Citigroup",
    "GS": "Goldman Sachs", "MS": "Morgan Stanley", "WFC": "Wells Fargo", "BRKB": "Berkshire Hathaway", "AMD": "AMD",
    "INTC": "Intel", "QCOM": "Qualcomm", "AVGO": "Broadcom", "TSM": "TSMC", "ASML": "ASML", "MU": "Micron", "ARM": "Arm",
    "ORCL": "Oracle", "CRM": "Salesforce", "ADBE": "Adobe", "IBM": "IBM", "CSCO": "Cisco", "PLTR": "Palantir", "SHOP": "Shopify",
    "UBER": "Uber", "ABNB": "Airbnb", "SPOT": "Spotify", "SNAP": "Snap", "COIN": "Coinbase", "MSTR": "MicroStrategy",
    "BABA": "Alibaba", "JD": "JD.com", "PDD": "PDD (Temu)", "BIDU": "Baidu", "NIO": "NIO", "TCEHY": "Tencent", "SONY": "Sony",
    "TM": "Toyota", "XOM": "Exxon Mobil", "CVX": "Chevron", "SHEL": "Shell", "BP": "BP", "PBR": "Petrobras", "VALE": "Vale",
    "RIO": "Rio Tinto", "BHP": "BHP", "GOLD": "Barrick Gold", "NEM": "Newmont", "FCX": "Freeport-McMoRan", "X": "US Steel",
    "JNJ": "Johnson & Johnson", "PFE": "Pfizer", "MRK": "Merck", "ABBV": "AbbVie", "LLY": "Eli Lilly", "NVO": "Novo Nordisk",
    "MRNA": "Moderna", "UNH": "UnitedHealth", "BA": "Boeing", "CAT": "Caterpillar", "DE": "John Deere", "GE": "General Electric",
    "MMM": "3M", "HON": "Honeywell", "LMT": "Lockheed Martin", "F": "Ford", "GM": "General Motors", "T": "AT&T", "VZ": "Verizon",
    "PG": "Procter & Gamble", "HD": "Home Depot", "TGT": "Target", "AXP": "American Express", "BIOX": "Bioceres",
    "GLOB": "Globant", "DESP": "Despegar", "SATL": "Satellogic", "NU": "Nubank", "STNE": "StoneCo",
    "XP": "XP Inc", "ITUB": "Itaú", "BBD": "Bradesco", "ERJ": "Embraer", "EMBJ": "Embraer", "AMX": "América Móvil",
    "SID": "CSN", "GGB": "Gerdau", "HMY": "Harmony Gold", "AU": "AngloGold", "PAAS": "Pan American Silver",
    "TXR": "Ternium", "TEN": "Tenaris", "ADGO": "Adecoagro", "LAC": "Lithium Americas", "ALB": "Albemarle",
    "SQ": "Block (Square)", "XYZ": "Block (Square)", "ZM": "Zoom", "SE": "Sea Ltd", "AMAT": "Applied Materials",
    "TXN": "Texas Instruments", "SMCI": "Super Micro", "DELL": "Dell", "HPQ": "HP", "NOW": "ServiceNow", "SNOW": "Snowflake",
    "RBLX": "Roblox", "EA": "Electronic Arts", "HOG": "Harley-Davidson", "RACE": "Ferrari", "STLA": "Stellantis",
    "MO": "Altria", "PM": "Philip Morris", "BUD": "AB InBev", "DEO": "Diageo", "UL": "Unilever", "SAP": "SAP",
    "SIEGY": "Siemens", "BKNG": "Booking", "LRCX": "Lam Research", "AAL": "American Airlines", "DAL": "Delta",
    "UAL": "United Airlines", "LUV": "Southwest", "ETSY": "Etsy", "EBAY": "eBay", "TWLO": "Twilio", "DOCU": "DocuSign",
    "PINS": "Pinterest", "HUT": "Hut 8", "RIOT": "Riot Platforms", "MARA": "MARA Holdings",
}

CTX = ssl.create_default_context()
CTX_LAXO = ssl.create_default_context()
CTX_LAXO.check_hostname = False
CTX_LAXO.verify_mode = ssl.CERT_NONE
diag = {"ok": [], "errores": [], "cortados": [], "faltan": 0}


def pedir(req):
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
                return json.loads(r.read().decode("utf-8"))
        except ssl.SSLError:
            # el certificado de BYMA a veces no trae la cadena completa: la data es pública, se reintenta sin verificar
            with urllib.request.urlopen(req, timeout=40, context=CTX_LAXO) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            if i == 2:
                raise
            time.sleep(2 * (i + 1))


def get_json(url, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    h.update(headers or {})
    return pedir(urllib.request.Request(url, headers=h))


def post_json(path, body):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*", "Content-Type": "application/json"}
    h.update(H_BYMA)
    return pedir(urllib.request.Request(BYMA + path, data=json.dumps(body).encode(), headers=h, method="POST"))


def tramo(path, symbol, ini, fin):
    q = urllib.parse.urlencode({"symbol": symbol, "resolution": "D", "from": int(ini.timestamp()), "to": int(fin.timestamp())})
    j = get_json(f"{BYMA}{path}?{q}", H_BYMA)
    out = {}
    if j.get("s") == "ok":
        for t, c in zip(j.get("t") or [], j.get("c") or []):
            if c and c > 0:
                # los timestamps son de la jornada en Buenos Aires: se pasan a la fecha argentina
                f = (datetime.fromtimestamp(t, timezone.utc) - timedelta(hours=3)).date()
                if f.weekday() < 5:
                    out.setdefault(f.isoformat(), round(float(c), 4 if c < 100 else 2))
    return out


def byma_hist(path, symbol, corto=False):
    """corto: solo los últimos 45 días. Si no, por tramos de un año hasta que un tramo viene vacío (BYMA da ~2 años)."""
    fin = datetime.now(timezone.utc) + timedelta(days=1)
    if corto:
        return tramo(path, symbol, fin - timedelta(days=45), fin)
    out = {}
    tope = datetime(DESDE.year, DESDE.month, DESDE.day, tzinfo=timezone.utc)
    while fin > tope:
        ini = max(fin - timedelta(days=365), tope)
        t = tramo(path, symbol, ini, fin)
        nuevos = {f: v for f, v in t.items() if f not in out}
        if not nuevos and out:
            break
        if not nuevos and not out and fin < datetime.now(timezone.utc) - timedelta(days=400):
            break  # dos tramos vacíos seguidos: no tiene historia
        out.update(nuevos)
        fin = ini
        time.sleep(0.15)
    return out


def desde_ultimo_salto(serie):
    """Si hay un salto de más de 45 % en un día (cambio de ratio de un CEDEAR, split), se queda con lo posterior."""
    ks = sorted(serie)
    corte = None
    for a, b in zip(ks, ks[1:]):
        r = serie[b] / serie[a]
        if r > 1.8 or r < 0.55:
            corte = b
    if corte:
        return {f: v for f, v in serie.items() if f >= corte}, corte
    return serie, None


def unir(nuevo, viejo, escalar=True):
    """Lo guardado de antes completa lo que BYMA ya no da. BYMA re-ajusta su historia (pagos de bonos, splits), así que
    la parte guardada se escala para empalmar con la nueva en la primera fecha que tienen en común."""
    if not viejo:
        return nuevo
    if not nuevo:
        return viejo
    f0 = min(nuevo)
    ant = {f: v for f, v in viejo.items() if f < f0}
    if not ant:
        return nuevo
    r = nuevo[f0] / viejo[f0] if escalar and viejo.get(f0) else 1
    out = {f: round(v * r, 4 if v * r < 100 else 2) for f, v in ant.items()}
    out.update(nuevo)
    return out


def leer(tk):
    p = DIR / f"{tk}.json"
    if not p.exists():
        return {}
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
        return dict(zip(j["d"], j["c"]))
    except Exception:  # noqa: BLE001
        return {}


def guardar(tk, serie):
    ks = sorted(serie)
    (DIR / f"{tk}.json").write_text(json.dumps({"d": ks, "c": [serie[k] for k in ks]}, separators=(",", ":")), encoding="utf-8")


def bcra_cer():
    j = get_json(f"https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30?desde={DESDE.isoformat()}&hasta={date.today().isoformat()}&limit=3000")
    out = {}
    for res in j.get("results", []):
        for p in res.get("detalle", []):
            out[p["fecha"][:10]] = float(p["valor"])
    return out


def lista_byma():
    """Acciones y CEDEARs en pesos que cotizaron hace poco, de los paneles de Open BYMADATA."""
    acc, ced = set(), set()
    for path, dest in (("leading-equity", acc), ("general-equity", acc), ("cedears", ced)):
        try:
            j = post_json(path, {"excludeZeroPxAndQty": False, "T2": False, "T1": True, "T0": False, "page_size": 5000})
            filas = j if isinstance(j, list) else (j.get("data") or [])
            n = 0
            for x in filas:
                s = x.get("symbol") or ""
                if x.get("denominationCcy") == "ARS" and re.fullmatch(r"[A-Z0-9.]{1,8}", s) and \
                        ((x.get("previousClosingPrice") or 0) > 0 or (x.get("closingPrice") or 0) > 0 or (x.get("trade") or 0) > 0):
                    dest.add(s)
                    n += 1
            diag["ok"].append(f"panel {path}: {n} en pesos")
        except Exception as e:  # noqa: BLE001
            diag["errores"].append(f"panel {path}: {e}")
    return acc, ced - acc


def main():
    t0 = time.time()
    DIR.mkdir(exist_ok=True)
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    info_prev = prev.get("info") or {}
    acc, ced = lista_byma()
    for k, v in info_prev.items():  # lo que ya estaba sigue, aunque hoy no haya cotizado
        if v.get("t") == "acc":
            acc.add(k)
        elif v.get("t") == "ced" and k not in acc:
            ced.add(k)
    pedidos = [(tk, "bon") for tk, _ in BONOS] + [(tk, "acc") for tk in sorted(acc)] + [(tk, "ced") for tk in sorted(ced)]
    # primero los que ya tienen historia (rápidos), después los nuevos
    pedidos.sort(key=lambda x: 0 if (DIR / f"{x[0]}.json").exists() else 1)
    info = {}
    for tk, tipo in pedidos:
        viejo = leer(tk)
        if time.time() - t0 > TOPE_SEG:
            diag["faltan"] += 1
            if viejo:
                info[tk] = info_prev.get(tk) or {"t": tipo}
            continue
        try:
            nuevo = byma_hist("chart/historical-series/history", f"{tk} 24HS", corto=bool(viejo))
            serie = unir(nuevo, viejo)
            if len(serie) < 10:
                continue  # casi sin operaciones
            serie, corte = desde_ultimo_salto(serie)
            if corte:
                diag["cortados"].append(f"{tk} desde {corte}")
            if len(serie) < 10:
                continue
            guardar(tk, serie)
            nom = NOMBRES.get(tk) or dict(BONOS).get(tk) or ""
            info[tk] = {"t": tipo, **({"n": nom} if nom else {}), "f0": min(serie)}
        except Exception as e:  # noqa: BLE001
            diag["errores"].append(f"{tk}: {str(e)[:80]}")
            if viejo:
                info[tk] = info_prev.get(tk) or {"t": tipo}
        time.sleep(0.12)
    diag["ok"].append(f"activos con historia: {len(info)} (pedidos {len(pedidos)}, {time.time() - t0:.0f} s)")
    # dólar (para el MEP): AL30D y GD30D
    usd = {}
    for tk in ("AL30D", "GD30D"):
        try:
            usd[tk] = unir(byma_hist("chart/historical-series/history", f"{tk} 24HS", corto=bool(leer(tk))), leer(tk))
            guardar(tk, usd[tk])
        except Exception as e:  # noqa: BLE001
            diag["errores"].append(f"{tk}: {e}")
            usd[tk] = leer(tk)
    # Merval
    merval = {}
    try:
        m = byma_hist("chart/index-historical-series/history", "M")
        merval = {f: round(v * MERVAL_FACTOR, 2) for f, v in m.items() if f <= MERVAL_BASE_FECHA}  # S&P → base MSCI
    except Exception as e:  # noqa: BLE001
        diag["errores"].append(f"Merval BYMA: {e}")
    try:
        dj = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        for x in dj.get("diario", []):
            if x.get("merval") and x["fecha"] > MERVAL_BASE_FECHA:
                merval[x["fecha"]] = x["merval"]
    except Exception as e:  # noqa: BLE001
        diag["errores"].append(f"Merval data.json: {e}")
    merval = {**leer("MERVAL"), **merval}
    if merval:
        guardar("MERVAL", merval)
        info["MERVAL"] = {"t": "idx", "n": "Merval (índice)", "f0": min(merval)}
    # CER
    try:
        cer = bcra_cer()
    except Exception as e:  # noqa: BLE001
        diag["errores"].append(f"CER: {e}")
        cer = {}
    # fechas hábiles con operaciones (las del AL30, GGAL y el Merval)
    base = set()
    for tk in ("AL30", "GGAL", "MERVAL"):
        base |= set(leer(tk))
    fechas = sorted(base)
    if len(fechas) < 50 or len(info) < 20:
        print("Muy pocos datos: no se reemplaza historia.json", json.dumps(diag, ensure_ascii=False, indent=1))
        return
    al30, gd30 = leer("AL30"), leer("GD30")
    mep_viejo = dict(zip(prev.get("fechas") or [], prev.get("mep") or []))
    mep = []
    for f in fechas:
        v = None
        for a, b in ((al30.get(f), usd["AL30D"].get(f)), (gd30.get(f), usd["GD30D"].get(f))):
            if a and b:
                v = round(a / b, 2)
                break
        mep.append(v if v is not None else mep_viejo.get(f))
    ks, j, ult, cer_al = sorted(cer), 0, None, []
    for f in fechas:
        while j < len(ks) and ks[j] <= f:
            ult = cer[ks[j]]
            j += 1
        cer_al.append(ult)
    out = {"actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00"), "fechas": fechas, "mep": mep,
           "cer": cer_al, "info": dict(sorted(info.items())), "diag": diag}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"historia.json: {len(info)} activos, {len(fechas)} días ({fechas[0]} a {fechas[-1]}), {time.time() - t0:.0f} s")
    print(json.dumps(diag, ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main()
