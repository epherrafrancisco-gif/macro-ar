"""Datos de mercado de fuentes abiertas, que permiten reutilizarlos (también con fines comerciales) citando la fuente.
Reemplazan a CNBC donde se puede (plan legal del 26/10/2026; ver "Licencias y créditos" en Sobre Pulso Macro).

- Monedas: Banco Central Europeo (tipos de cambio de referencia diarios, ~30 monedas; uso libre citando al BCE) y, para las
  que el BCE no publica, el BIS (tipo de cambio diario de cada banco central; llega con unos días de atraso).
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

UA = "pulsomacro.com.ar (contacto@pulsomacro.com.ar)"
errores = []

# Monedas del BCE (código → se cotiza en dólares por unidad, como CNBC)
BCE = ["USD", "JPY", "CZK", "DKK", "GBP", "HUF", "PLN", "RON", "SEK", "CHF", "ISK", "NOK", "TRY", "AUD", "BRL", "CAD",
       "CNY", "HKD", "IDR", "ILS", "INR", "KRW", "MXN", "MYR", "NZD", "PHP", "SGD", "THB", "ZAR"]
USD_POR_UNIDAD = {"EUR", "GBP", "AUD", "NZD"}
# Monedas que el BCE no publica: tipo de cambio diario del BIS (código de país del BIS)
BIS_FX = {"ARS": "AR", "CLP": "CL", "COP": "CO", "PEN": "PE", "UYU": "UY", "RSD": "RS", "RUB": "RU", "MAD": "MA", "MKD": "MK", "SAR": "SA"}
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
        fuente = "BIS" if c in BIS_FX else "BCE"
        x = a_cotizacion(pts, NOMBRES.get(c, c))
        if x:
            x["f"] = fuente
            q[sym] = x
    return q


def fx_series_hist(hist):
    """Claves fx_xxx de global_hist.json (minúsculas), 2 años."""
    return {f"fx_{c.lower()}": pts[-520:] for c, pts in hist.items() if c not in ("EURPLN", "EURCHF") and len(pts) > 20}
