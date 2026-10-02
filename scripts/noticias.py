"""Junta los titulares de economía de varios medios (RSS) en noticias.json.

Solo guarda título, link, medio y hora: la nota se lee en el sitio de cada medio.
Uso: python scripts/noticias.py
Lo corre .github/workflows/noticias.yml cada hora. Si un medio falla, se conservan
sus titulares anteriores y se registra el error.
"""

import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "noticias.json"
TZ_AR = timezone(timedelta(hours=-3))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 MacroAR/1.0"
HORAS = 48      # se muestran las últimas 48 horas
MAXIMO = 150

FUENTES = {
    "Ámbito": "https://www.ambito.com/rss/pages/economia.xml",
    "Infobae": "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/",
    "La Nación": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/economia/",
    "iProfesional": "https://www.iprofesional.com/rss/economia",
    "Perfil": "https://www.perfil.com/feed/economia",
}

# Temas para filtrar en la página (se buscan en el título, sin distinguir mayúsculas).
TEMAS = {
    "dolar": r"d[oó]lar|cambiari|brecha|\bmep\b|\bccl\b|\bblue\b|devalu",
    "bcra": r"\bbcra\b|banco central|reservas|tasas?\b|plazo fijo|encaje|bopreal|lecap|licitaci",
    "inflacion": r"inflaci|\bipc\b|precios|canasta|tarifa|aumento",
    "mercados": r"merval|acciones|bonos|riesgo pa[ií]s|wall street|mercados?\b|bolsa|cedear|cripto|bitcoin|\bfed\b",
    "fiscal": r"fiscal|super[aá]vit|d[eé]ficit|recaudaci|impuesto|arca|presupuesto|deuda|\bfmi\b|gasto",
    "actividad": r"actividad|industria|empleo|desempleo|salari|consumo|ventas|construcci|\bpbi\b|exportaci|importaci|vaca muerta|rigi|campo|cosecha",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml,application/xml,text/xml,*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def limpiar(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()
    return re.sub(r"\s+", " ", t)


def fecha(txt):
    """RFC 822 (pubDate) o ISO 8601 (Atom) → datetime con zona."""
    txt = (txt or "").strip()
    if not txt:
        return None
    try:
        d = parsedate_to_datetime(txt)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def leer(medio, url):
    raiz = ET.fromstring(get(url))
    items = []
    for it in raiz.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        hijos = {c.tag.split("}")[-1]: c for c in it}
        titulo = limpiar(hijos["title"].text if "title" in hijos else "")
        link = ""
        if "link" in hijos:
            link = (hijos["link"].text or hijos["link"].get("href") or "").strip()
        d = fecha(next((hijos[k].text for k in ("pubDate", "published", "updated", "date") if k in hijos), ""))
        if titulo and link.startswith("http") and d:
            temas = [k for k, rx in TEMAS.items() if re.search(rx, titulo, re.I)]
            items.append({"t": titulo, "u": link, "f": medio, "h": d.astimezone(TZ_AR).isoformat(timespec="minutes"), "k": temas})
    if not items:
        raise ValueError("el feed no trajo titulares")
    return items


def main():
    ahora = datetime.now(TZ_AR)
    previo = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"items": []}
    todos, estado = {}, {}
    nuevos_por_medio = {}
    for medio, url in FUENTES.items():
        try:
            nuevos_por_medio[medio] = leer(medio, url)
            estado[medio] = f"ok ({len(nuevos_por_medio[medio])})"
        except Exception as e:  # noqa: BLE001
            estado[medio] = f"error: {e}"
    # Medios que fallaron: quedan sus titulares anteriores.
    for it in previo.get("items", []):
        if it["f"] not in nuevos_por_medio:
            todos[it["u"]] = it
    for items in nuevos_por_medio.values():
        for it in items:
            todos[it["u"]] = it
    limite = ahora - timedelta(hours=HORAS)
    lista = [it for it in todos.values() if datetime.fromisoformat(it["h"]) >= limite and datetime.fromisoformat(it["h"]) <= ahora + timedelta(minutes=10)]
    # Mismo título en dos links del mismo medio: quedarse con uno.
    vistos, final = set(), []
    for it in sorted(lista, key=lambda x: x["h"], reverse=True):
        clave = (it["f"], it["t"].lower())
        if clave not in vistos:
            vistos.add(clave)
            final.append(it)
    final = final[:MAXIMO]
    if not nuevos_por_medio:
        print("Todos los medios fallaron:", estado)
        raise SystemExit(1)
    salida = {"actualizado": ahora.isoformat(timespec="minutes"), "fuentes": estado, "items": final}
    if [x["u"] for x in final] == [x["u"] for x in previo.get("items", [])] and previo.get("fuentes") == estado:
        print("Sin titulares nuevos.")
        return
    DATA.write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(final)} titulares. Medios: {estado}")


if __name__ == "__main__":
    main()
