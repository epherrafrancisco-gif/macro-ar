"""Historia diaria de precios para el Simulador de inversión histórica → historia.json.

Fuentes:
  - Open BYMADATA (acceso gratuito y público de BYMA, la dueña del dato): cierres diarios de acciones, bonos y CEDEARs
    (GET .../chart/historical-series/history?symbol=GGAL%2024HS&resolution=D&from=&to=) y del índice Merval
    (.../chart/index-historical-series/history?symbol=M). Solo se guarda el cierre del día.
  - Merval: hasta el 16/10/2026 es el S&P Merval de BYMA re-expresado a la base del MSCI Merval (100.000 al 16/10/2026,
    mismo factor que update.py); desde el 19/10/2026, el MSCI Merval de data.json.
  - Dólar MEP del día: calculado por Pulso Macro con los cierres de BYMA (AL30 en pesos ÷ AL30D; si falta, GD30).
  - CER diario: BCRA (API de Estadísticas, serie 30), para ajustar por inflación.
Una serie con un salto de más de 45 % en un día (cambio de ratio de un CEDEAR, split) se descarta y queda en diag.
"""
import json
import ssl
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "historia.json"
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
BYMA = "https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/"
DESDE = date(2019, 1, 1)
MERVAL_BASE_FECHA = "2026-10-16"
MERVAL_FACTOR = 100000 / 2843310.56

# [ticker, nombre, tipo]
ACTIVOS = [
    ["GGAL", "Grupo Galicia", "acc"], ["YPFD", "YPF", "acc"], ["PAMP", "Pampa Energía", "acc"], ["BMA", "Banco Macro", "acc"],
    ["TXAR", "Ternium Argentina", "acc"], ["ALUA", "Aluar", "acc"], ["CEPU", "Central Puerto", "acc"], ["COME", "Comercial del Plata", "acc"],
    ["CRES", "Cresud", "acc"], ["EDN", "Edenor", "acc"], ["LOMA", "Loma Negra", "acc"], ["MIRG", "Mirgor", "acc"],
    ["SUPV", "Supervielle", "acc"], ["TECO2", "Telecom", "acc"], ["TGNO4", "TGN", "acc"], ["TGSU2", "TGS", "acc"],
    ["TRAN", "Transener", "acc"], ["VALO", "Grupo Valores", "acc"], ["BYMA", "BYMA", "acc"], ["METR", "Metrogas", "acc"],
    ["BBAR", "BBVA Argentina", "acc"],
    ["AL29", "Bonar 2029", "bon"], ["AL30", "Bonar 2030", "bon"], ["AL35", "Bonar 2035", "bon"], ["AE38", "Bonar 2038", "bon"],
    ["AL41", "Bonar 2041", "bon"], ["GD29", "Global 2029", "bon"], ["GD30", "Global 2030", "bon"], ["GD35", "Global 2035", "bon"],
    ["GD38", "Global 2038", "bon"], ["GD41", "Global 2041", "bon"], ["GD46", "Global 2046", "bon"],
    ["SPY", "S&P 500 (CEDEAR SPY)", "ced"], ["QQQ", "Nasdaq 100 (CEDEAR QQQ)", "ced"], ["AAPL", "Apple", "ced"],
    ["MSFT", "Microsoft", "ced"], ["NVDA", "Nvidia", "ced"], ["GOOGL", "Alphabet (Google)", "ced"], ["AMZN", "Amazon", "ced"],
    ["MELI", "Mercado Libre", "ced"], ["KO", "Coca-Cola", "ced"], ["TSLA", "Tesla", "ced"],
]

CTX = ssl.create_default_context()
CTX_LAXO = ssl.create_default_context()
CTX_LAXO.check_hostname = False
CTX_LAXO.verify_mode = ssl.CERT_NONE
diag = {"ok": [], "errores": [], "descartados": []}


def get_json(url, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
                return json.loads(r.read().decode("utf-8"))
        except ssl.SSLError:
            # el certificado de BYMA a veces no trae la cadena completa: la data es pública, se reintenta sin verificar
            with urllib.request.urlopen(req, timeout=60, context=CTX_LAXO) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            if i == 2:
                raise
            time.sleep(3 * (i + 1))


def byma_hist(path, symbol):
    t0 = int(datetime(DESDE.year, DESDE.month, DESDE.day, tzinfo=timezone.utc).timestamp())
    t1 = int(time.time()) + 86400
    q = urllib.parse.urlencode({"symbol": symbol, "resolution": "D", "from": t0, "to": t1})
    j = get_json(f"{BYMA}{path}?{q}", {"Origin": "https://open.bymadata.com.ar", "Referer": "https://open.bymadata.com.ar/"})
    if j.get("s") != "ok":
        raise ValueError(f"s={j.get('s')}")
    out = {}
    for t, c in zip(j.get("t") or [], j.get("c") or []):
        if c and c > 0:
            # los timestamps vienen a medianoche/mediodía de Buenos Aires: se pasa a la fecha argentina
            f = (datetime.fromtimestamp(t, timezone.utc) - timedelta(hours=3)).date()
            if f.weekday() < 5:
                out[f.isoformat()] = round(float(c), 4 if c < 100 else 2)
    return out


def saltos(serie):
    ks = sorted(serie)
    malos = []
    for a, b in zip(ks, ks[1:]):
        r = serie[b] / serie[a]
        if r > 1.8 or r < 0.55:
            malos.append(f"{a}→{b} ×{r:.2f}")
    return malos


def bcra_cer():
    j = get_json(f"https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30?desde={DESDE.isoformat()}&hasta={date.today().isoformat()}&limit=3000")
    out = {}
    for res in j.get("results", []):
        for p in res.get("detalle", []):
            out[p["fecha"][:10]] = float(p["valor"])
    return out


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    series, info = {}, {}
    for tk, nom, tipo in ACTIVOS:
        try:
            s = byma_hist("chart/historical-series/history", f"{tk} 24HS")
            if len(s) < 20:
                raise ValueError(f"solo {len(s)} días")
            m = saltos(s)
            if m:
                diag["descartados"].append(f"{tk}: {', '.join(m[:3])}")
                continue
            series[tk] = s
            info[tk] = {"n": nom, "t": tipo}
            diag["ok"].append(f"{tk}: {len(s)} días desde {min(s)}")
        except Exception as e:  # noqa: BLE001
            diag["errores"].append(f"{tk}: {e}")
        time.sleep(0.4)
    # dólar (para el MEP): AL30D y GD30D
    usd = {}
    for tk in ("AL30D", "GD30D"):
        try:
            usd[tk] = byma_hist("chart/historical-series/history", f"{tk} 24HS")
            diag["ok"].append(f"{tk}: {len(usd[tk])} días")
        except Exception as e:  # noqa: BLE001
            diag["errores"].append(f"{tk}: {e}")
        time.sleep(0.4)
    # Merval
    merval = {}
    try:
        m = byma_hist("chart/index-historical-series/history", "M")
        for f, v in m.items():
            if f <= MERVAL_BASE_FECHA:
                merval[f] = round(v * MERVAL_FACTOR, 2) if v > 500000 else v
        diag["ok"].append(f"Merval BYMA: {len(merval)} días desde {min(merval) if merval else '-'}")
    except Exception as e:  # noqa: BLE001
        diag["errores"].append(f"Merval BYMA: {e}")
    try:
        dj = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        for x in dj.get("diario", []):
            if x.get("merval") and x["fecha"] > MERVAL_BASE_FECHA:
                merval[x["fecha"]] = x["merval"]
    except Exception as e:  # noqa: BLE001
        diag["errores"].append(f"Merval data.json: {e}")
    if merval:
        series["MERVAL"] = merval
        info["MERVAL"] = {"n": "Merval (índice)", "t": "idx"}
    # CER
    try:
        cer = bcra_cer()
        diag["ok"].append(f"CER: {len(cer)} días")
    except Exception as e:  # noqa: BLE001
        diag["errores"].append(f"CER: {e}")
        cer = {}

    if len(series) < 10:
        print("Muy pocas series: no se reemplaza historia.json", json.dumps(diag, ensure_ascii=False, indent=1))
        if prev:
            prev["diag"] = diag
            OUT.write_text(json.dumps(prev, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        else:
            OUT.write_text(json.dumps({"diag": diag}, ensure_ascii=False), encoding="utf-8")
        return

    fechas = sorted(set().union(*[set(s) for s in series.values()]))
    # MEP de cada día: AL30 ÷ AL30D (si falta, GD30 ÷ GD30D)
    mep = []
    for f in fechas:
        v = None
        for p, d in (("AL30", "AL30D"), ("GD30", "GD30D")):
            a, b = series.get(p, {}).get(f), usd.get(d, {}).get(f)
            if a and b:
                v = round(a / b, 2)
                break
        mep.append(v)
    # CER del día (o el último anterior)
    cer_al = []
    ks = sorted(cer)
    j, ult = 0, None
    for f in fechas:
        while j < len(ks) and ks[j] <= f:
            ult = cer[ks[j]]
            j += 1
        cer_al.append(ult)
    out = {
        "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00"),
        "fechas": fechas,
        "info": info,
        "p": {k: [s.get(f) for f in fechas] for k, s in series.items()},
        "mep": mep,
        "cer": cer_al,
        "diag": diag,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"historia.json: {len(series)} series, {len(fechas)} días ({fechas[0]} a {fechas[-1]})")
    print(json.dumps(diag, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
