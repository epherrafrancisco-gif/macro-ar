"""Junta los titulares de economía de varios medios (RSS) en noticias.json.

Solo guarda título, link, medio y hora: la nota se lee en el sitio de cada medio.
Uso: python scripts/noticias.py
Lo corre .github/workflows/noticias.yml cada hora. Los titulares se acumulan durante
48 horas; si un medio falla, se conservan los anteriores y se registra el error.
"""

import html
import json
import re
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "noticias.json"
TZ_AR = timezone(timedelta(hours=-3))
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
HORAS = 72      # se muestran las últimas 72 horas
MAXIMO = 900

# Cada medio: una lista de secciones; cada sección, una o varias direcciones (se usa la primera que ande). Pedido del dueño
# 02/11/2026: muchas más noticias, de economía y alrededor (negocios, finanzas, política económica), sin irse por las ramas.
FUENTES = {
    "Ámbito": [["https://www.ambito.com/rss/pages/economia.xml"], ["https://www.ambito.com/rss/pages/finanzas.xml"],
               ["https://www.ambito.com/rss/pages/negocios.xml"], ["https://www.ambito.com/rss/pages/politica.xml"]],
    "Infobae": [["https://www.infobae.com/arc/outboundfeeds/rss/category/economia/"],
                ["https://www.infobae.com/arc/outboundfeeds/rss/category/politica/"]],
    "La Nación": [["https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/economia/"],
                  ["https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/politica/"]],
    "iProfesional": [["https://www.iprofesional.com/rss/economia"], ["https://www.iprofesional.com/rss/finanzas"],
                     ["https://www.iprofesional.com/rss/negocios"]],
    # Perfil: desde 10/2026 /feed/economia da 404; Reperfilar es su sección de economía
    "Perfil": [["https://www.perfil.com/feed/economia/", "https://www.perfil.com/feed/reperfilar"]],
    "Clarín": [["https://www.clarin.com/rss/economia/"], ["https://www.clarin.com/rss/politica/"]],
    "Página/12": [["https://www.pagina12.com.ar/rss/secciones/economia/notas"]],
    "El Cronista": [["https://www.cronista.com/files/rss/economia.xml", "https://www.cronista.com/rss/economia/", "https://www.cronista.com/rss/"]],
    "El Economista": [["https://eleconomista.com.ar/rss/", "https://eleconomista.com.ar/feed/"]],
    "TN": [["https://tn.com.ar/rss/economia/", "https://tn.com.ar/rss.xml"]],
}

# Temas para filtrar en la página (se buscan en el título, sin distinguir mayúsculas).
TEMAS = {
    "dolar": r"d[oó]lar|cambiari|brecha|\bmep\b|\bccl\b|\bblue\b|devalu",
    "bcra": r"\bbcra\b|banco central|reservas|tasas?\b|plazo fijo|encaje|bopreal|lecap|licitaci",
    "inflacion": r"inflaci|\bipc\b|precios|canasta|tarifa|aumento",
    "mercados": r"merval|acciones|bonos|riesgo pa[ií]s|wall street|mercados?\b|bolsa|cedear|cripto|bitcoin|\bfed\b",
    "fiscal": r"fiscal|super[aá]vit|d[eé]ficit|recaudaci|impuest|tributari|retenciones|\barca\b|presupuesto|deuda|\bfmi\b|gasto|jubilaci",
    "politica": r"milei|gobierno|congreso|diputados|senado|ministr|caputo|gobernador|elecci|ley\b|reforma|oposici|peronis|libertari|casa rosada",
    "actividad": r"actividad|industria|empleo|desempleo|salari|consumo|ventas|construcci|\bpbi\b|exportaci|importaci|vaca muerta|rigi|inversi|campo|cosecha|petr[oó]le|miner",
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


IMG_RX = re.compile(r"\.(jpe?g|png|webp|gif|avif)(\?|$)", re.I)


def imagen(it):
    """La foto de la nota que trae el propio feed (media:content, media:thumbnail, enclosure o la primera <img>)."""
    for c in it.iter():
        tag = c.tag.split("}")[-1]
        u = c.get("url") or ""
        if tag in ("content", "thumbnail") and u.startswith("http") and (c.get("medium") in (None, "image") or IMG_RX.search(u)):
            if not (c.get("type") or "image").startswith(("image", "")) and not IMG_RX.search(u): continue
            return u
        if tag == "enclosure" and u.startswith("http") and ((c.get("type") or "").startswith("image") or IMG_RX.search(u)):
            return u
    for c in it.iter():
        tag = c.tag.split("}")[-1]
        if tag in ("description", "encoded", "content", "summary") and c.text:
            m = re.search(r'<img[^>]+src=["\'](https?://[^"\']+)', c.text)
            if m: return html.unescape(m.group(1))
    return None


def achicar(u):
    """Las fotos de Infobae y La Nación vienen a 2000 px: el resizer de Arc acepta otro ancho."""
    if "/resizer/v2/" in u and "width=" in u:
        return re.sub(r"&height=\d+", "", re.sub(r"width=\d+", "width=560", u))
    return u


def anda(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA}, method="GET")
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200 and (r.headers.get("Content-Type") or "").startswith("image")
    except Exception:
        return False


def og_image(url):
    """Foto de la nota sacada de su página (og:image), para los medios cuyo feed no trae foto (Ámbito)."""
    try:
        rp = urllib.robotparser.RobotFileParser(); rp.set_url(re.match(r"https?://[^/]+", url).group(0) + "/robots.txt"); rp.read()
        if not rp.can_fetch("PulsoMacro", url): return None
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=15) as r:
            h = r.read(200000).decode("utf-8", "replace")
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', h) or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', h)
        return html.unescape(m.group(1)) if m and m.group(1).startswith("https://") else None
    except Exception:
        return None


# fuera lo que no tiene que ver (las secciones de política y los feeds generales traen de todo)
RUIDO = re.compile(r"f[uú]tbol|boca juniors|river plate|selecci[oó]n argentina|messi|mundial 20|partido de|gol\b|tenis|f[oó]rmula 1|"
                   r"hor[oó]scopo|far[aá]ndula|novela|actriz|actor\b|cantante|gran hermano|asesin|homicid|femicid|polic[ií]a|choque|accidente|"
                   r"clima|pron[oó]stico del tiempo|lluvias|tormenta|receta|celebridad|famos", re.I)


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
        if titulo and link.startswith("http") and d and not RUIDO.search(titulo):
            temas = [k for k, rx in TEMAS.items() if re.search(rx, titulo, re.I)]
            x = {"t": titulo, "u": link, "f": medio, "h": d.astimezone(TZ_AR).isoformat(timespec="minutes"), "k": temas}
            im = imagen(it)
            if im and im.startswith("https://"): x["i"] = im  # solo https (en la página se ve con http bloqueado)
            items.append(x)
    if not items:
        raise ValueError("el feed no trajo titulares")
    return items


def main():
    ahora = datetime.now(TZ_AR)
    previo = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"items": []}
    todos, estado = {}, {}
    nuevos_por_medio = {}
    for medio, secciones in FUENTES.items():
        juntos, errs, n_ok = {}, [], 0
        for alternativas in secciones:
            for u in alternativas:
                try:
                    for x in leer(medio, u): juntos.setdefault(x["u"], x)
                    n_ok += 1; break
                except Exception as e:  # noqa: BLE001
                    errs.append(f"{u.split('/')[2]}{u.split(u.split('/')[2])[1][:30]}: {e}")
        if juntos:
            nuevos_por_medio[medio] = list(juntos.values())
            estado[medio] = f"ok ({len(juntos)}, {sum(1 for x in juntos.values() if x.get('i'))} con foto, {n_ok}/{len(secciones)} secciones)"
        else:
            estado[medio] = "error: " + " | ".join(errs)[:300]
    # Se acumulan: los titulares anteriores quedan hasta cumplir 48 horas (algunos feeds,
    # como el de Ámbito, traen solo los últimos 20) y los de un medio que falló, también.
    for it in previo.get("items", []):
        todos[it["u"]] = it
    for items in nuevos_por_medio.values():
        for it in items:
            todos[it["u"]] = it
    # fotos: las del feed achicadas (si el medio lo acepta: se prueba con una), y las que faltan, de la página de la nota
    for medio, items in nuevos_por_medio.items():
        con = [x for x in items if x.get("i")]
        if con and achicar(con[0]["i"]) != con[0]["i"] and anda(achicar(con[0]["i"])):
            for x in con: x["i"] = achicar(x["i"])
    previas = {it["u"]: it.get("i") for it in previo.get("items", []) if it.get("i")}
    pedidas = 0
    for items in nuevos_por_medio.values():
        for x in items:
            if x.get("i"): continue
            if x["u"] in previas: x["i"] = previas[x["u"]]; continue
            if pedidas < 40 and datetime.fromisoformat(x["h"]) >= ahora - timedelta(hours=HORAS):
                pedidas += 1; im = og_image(x["u"])
                if im: x["i"] = im
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
    if final == previo.get("items", []) and previo.get("fuentes") == estado:
        print("Sin titulares nuevos.")
        return
    DATA.write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(final)} titulares. Medios: {estado}")


if __name__ == "__main__":
    main()
