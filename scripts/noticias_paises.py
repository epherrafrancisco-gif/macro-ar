"""Arma noticias_paises.json: titulares de economía de las últimas 48 horas para las secciones Estados Unidos, Brasil,
Europa y México de Pulso Macro.

Cada medio se baja una sola vez y sus titulares se reparten por país:
  - medios propios del país (por ejemplo El Economista de México o Cinco Días): entran todos o, si el medio es
    general, solo los de economía;
  - medios generales o de otros países: entran solo si el titular nombra al país y es de economía.
Solo titular, link, medio y hora (como en las noticias de Argentina). Nunca se guardan noticias de más de 48 horas.

Uso: python scripts/noticias_paises.py
"""

import html
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "noticias_paises.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"

ECON = (r"econom|mercad|bolsa|wall street|inflaci|tasas?\b|tipos? de inter|inter[eé]s|banco central|reserva federal|\bfed\b|"
        r"\bbce\b|banxico|copom|selic|d[oó]lar|\beuros?\b|\breales\b|\bpeso\b|petr[oó]le|arancel|comercio|export|import|deuda|"
        r"\bpib\b|\bpbi\b|recesi[oó]n|empleo|desempleo|salari|precio|acciones|empresa|inversi|bancos?\b|fiscal|impuest|"
        r"presupuesto|remesas|crecimiento|industria|petrobras|pemex|nasdaq|s&p|dow jones|bono|financ|ventas|consumo|vivienda")
PAIS = {
    "eeuu": r"ee\.? ?uu|\beu\b|estados unidos|estadounidense|norteamerican|\bfed\b|reserva federal|powell|wall street|"
            r"washington|nueva york|nasdaq|dow jones|s&p 500|trump|casa blanca|tesoro de ee",
    "brasil": r"brasil|brasile|lula|bovespa|petrobras|s[aã]o paulo|r[ií]o de janeiro|copom|selic|haddad|bolsonaro|itamaraty",
    "europa": r"europ|\bbce\b|lagarde|zona euro|eurozona|\bue\b|bruselas|alemania|alem[aá]n|francia|franc[eé]s|italia|"
              r"italian|espa[nñ]a|español|reino unido|brit[aá]nic|\bdax\b|\bibex\b|\beuros?\b",
    "mexico": r"m[eé]xic|banxico|sheinbaum|pemex|\bt-?mec\b|usmca|monterrey|guadalajara|\bbmv\b",
}
# (medio, url, {país: "todo" | "econ" | "pais"})
#   todo = entra todo (medio de economía del país) · econ = solo titulares de economía (medio general del país)
#   pais = solo si nombra al país y es de economía (medio de otro lado)
FEEDS = [
    ("El Economista (México)", "https://www.eleconomista.com.mx/rss/ultimas-noticias", {"mexico": "todo"}),
    ("El Financiero", "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml", {"mexico": "econ"}),
    ("La Jornada", "https://www.jornada.com.mx/rss/economia.xml", {"mexico": "todo"}),
    ("Expansión México", "https://expansion.mx/rss", {"mexico": "econ"}),
    ("El Universal", "https://www.eluniversal.com.mx/arc/outboundfeeds/rss/category/cartera/?outputType=xml", {"mexico": "todo"}),
    ("Cinco Días", "https://feeds.elpais.com/mrss-s/pages/ep/site/cincodias.elpais.com/portada", {"europa": "todo", "eeuu": "pais", "brasil": "pais", "mexico": "pais"}),
    ("Expansión", "https://e00-expansion.uecdn.es/rss/mercados.xml", {"europa": "todo", "eeuu": "pais", "brasil": "pais", "mexico": "pais"}),
    ("Euronews", "https://es.euronews.com/rss?level=vertical&name=business", {"europa": "todo", "eeuu": "pais", "brasil": "pais", "mexico": "pais"}),
    ("El País", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada", {"europa": "pais", "eeuu": "pais", "brasil": "pais", "mexico": "pais"}),
    ("El País América", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/america/portada", {"brasil": "pais", "mexico": "pais"}),
    ("El País EE.UU.", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/us/portada", {"eeuu": "econ"}),
    ("DW", "https://rss.dw.com/xml/rss-sp-eco", {"europa": "pais", "eeuu": "pais", "brasil": "pais", "mexico": "pais"}),
    ("France 24", "https://www.france24.com/es/econom%C3%ADa/rss", {"europa": "pais", "eeuu": "pais", "brasil": "pais", "mexico": "pais"}),
    ("France 24", "https://www.france24.com/es/am%C3%A9rica-latina/rss", {"brasil": "pais", "mexico": "pais"}),
    ("BBC Mundo", "https://feeds.bbci.co.uk/mundo/rss.xml", {"europa": "pais", "eeuu": "pais", "brasil": "pais", "mexico": "pais"}),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/estados-unidos/", {"eeuu": "econ"}),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/", {"eeuu": "pais", "brasil": "pais", "mexico": "pais", "europa": "pais"}),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/america/", {"brasil": "pais", "mexico": "pais"}),
    ("Ámbito", "https://www.ambito.com/rss/pages/economia.xml", {"eeuu": "pais", "brasil": "pais", "mexico": "pais", "europa": "pais"}),
    ("Ámbito", "https://www.ambito.com/rss/pages/mundo.xml", {"eeuu": "pais", "brasil": "pais", "mexico": "pais", "europa": "pais"}),
]
# títulos que no son noticias (secciones, columnas fijas)
BASURA = re.compile(r"^(pol[ií]tica|econom[ií]a|mercados|guerra en .+|opini[oó]n|tendencias y señales|para tomar en cuenta)$", re.I)


def get(url, tries=2, timeout=30):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, */*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise last


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


def main():
    ahora = datetime.now(timezone.utc)
    corte = ahora - timedelta(hours=48)
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    por_pais = {p: [] for p in PAIS}
    fuentes, errores = {}, []
    for medio, url, reglas in FEEDS:
        clave_f = f"{medio} · {url.split('/')[2]}"
        try:
            raiz = ET.fromstring(get(url))
            n = 0
            for it in raiz.iter():
                if it.tag.split("}")[-1] not in ("item", "entry"):
                    continue
                h = {c.tag.split("}")[-1]: c for c in it}
                t = limpiar(h["title"].text if "title" in h else "")
                link = ((h["link"].text or h["link"].get("href") or "").strip()) if "link" in h else ""
                d = fecha(next((h[k].text for k in ("pubDate", "published", "updated", "date") if k in h), ""))
                if not t or BASURA.match(t) or len(t) < 25 or not link.startswith("http") or not d or d < corte or d > ahora + timedelta(hours=1):
                    continue
                es_econ = bool(re.search(ECON, t, re.I))
                for pais, regla in reglas.items():
                    nombra = bool(re.search(PAIS[pais], t, re.I))
                    if regla == "todo" or (regla == "econ" and es_econ) or (regla == "pais" and nombra and es_econ):
                        por_pais[pais].append({"t": t, "u": link, "f": medio, "h": d.isoformat(timespec="minutes")})
                        n += 1
            fuentes[clave_f] = f"ok ({n})"
        except Exception as e:  # noqa: BLE001
            fuentes[clave_f] = f"error: {str(e)[:80]}"
            errores.append(f"{clave_f}: {e}")
        time.sleep(0.3)
    data = {"actualizado": ahora.isoformat(timespec="minutes"), "fuentes": fuentes, "errores": errores[:30]}
    for pais, items in por_pais.items():
        vistos, unicos = set(), []
        for x in sorted(items, key=lambda x: x["h"], reverse=True):
            k = re.sub(r"\W+", "", x["t"].lower())[:60]
            if k not in vistos:
                vistos.add(k)
                unicos.append(x)
        if not unicos:  # si todo falló, quedan las anteriores que sigan dentro de las 48 horas
            unicos = [x for x in (prev.get(pais) or []) if x.get("h", "") >= corte.isoformat(timespec="minutes")]
        data[pais] = unicos[:40]
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print({p: len(data[p]) for p in PAIS})
    for p in PAIS:
        for x in data[p][:12]:
            print(p, "|", x["f"], "|", x["t"][:100])
    for e in errores:
        print("ERROR", e)


if __name__ == "__main__":
    main()
