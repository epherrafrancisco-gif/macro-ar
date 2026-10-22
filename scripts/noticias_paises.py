"""Arma noticias_paises.json: titulares de economía de las últimas 48 horas para las secciones Estados Unidos, Brasil,
Europa, México, Chile, Japón, Reino Unido, Canadá, Colombia, Turquía, Perú y Polonia de Pulso Macro.

Cada medio se baja una sola vez y sus titulares se reparten por país:
  - medios propios del país (por ejemplo El Economista de México o Cinco Días): entran todos o, si el medio es
    general, solo los de economía;
  - medios generales o de otros países: entran solo si el titular nombra al país y es de economía.
Solo titular, link, medio y hora (como en las noticias de Argentina). Nunca se guardan noticias de más de 48 horas.
Primero van los titulares en español. Si un país tiene menos de MIN_ES, se completa con medios en inglés (marcados
con "l": "en"), con las mismas reglas pero filtros en inglés.

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

ECON = (r"econom|\bmercados?\b|\bbolsas?\b|wall street|inflaci|\btasas?\b|tipos? de inter|banco central|reserva federal|\bfed\b|"
        r"\bbce\b|banxico|copom|selic|d[oó]lar|\beuros?\b|\breales\b|\bpesos\b|petr[oó]leo\b|\bcrudo\b|arancel|comerci|exportaci|"
        r"importaci|exportador|importador|deuda|\bpib\b|\bpbi\b|recesi[oó]n|empleo|desempleo|salari|precios?\b|acciones|inversi|"
        r"\bbancos?\b|bancari|d[eé]ficit|super[aá]vit|pol[ií]tica fiscal|impuest|presupuesto|remesas|industria|nasdaq|s&p|"
        r"dow jones|\bbonos?\b|financier|bitcoin|cripto|\boro\b|hipotec|\bopa\b|ganancias|ingresos|mil millones|"
        r"millones de (d[oó]lares|pesos|euros|reales)|\bmdp\b|\bmdd\b|empresa|econ[oó]mic|negocio|riesgo pa[ií]s|\btlc\b|t-mec")
# otros países: en los medios propios se saltean los titulares que hablan de otro país y no del propio
OTROS = (r"argentin|milei|colombia|chile|per[uú]\b|venezuel|ecuador|uruguay|paraguay|bolivia|china|chin[oa]s\b|jap[oó]n|india|"
         r"rusia|ucrani|ir[aá]n\b|israel|gaza|arabia|turqu[ií]a|corea|canad[aá]|reino unido|brit[aá]nic|alemania|francia|"
         r"espa[nñ]a|italia|europ|\bue\b|estados unidos|ee\.? ?uu|\beu\b|trump|wall street|brasil|m[eé]xic")
PAIS = {
    "eeuu": r"ee\.? ?uu|\beu\b|estados unidos|estadounidense|norteamerican|\bfed\b|reserva federal|powell|wall street|"
            r"washington|nueva york|nasdaq|dow jones|s&p 500|trump|casa blanca|tesoro de ee",
    "brasil": r"brasil|brasile|lula|bovespa|petrobras|s[aã]o paulo|r[ií]o de janeiro|copom|selic|haddad|bolsonaro|itamaraty",
    "europa": r"europ|\bbce\b|lagarde|zona euro|eurozona|\bue\b|bruselas|alemania|alem[aá]n|francia|franc[eé]s|italia|"
              r"italian|espa[nñ]a|español|reino unido|brit[aá]nic|\bdax\b|\bibex\b|\beuros?\b",
    "mexico": r"m[eé]xic|banxico|sheinbaum|pemex|\bt-?mec\b|usmca|monterrey|guadalajara|\bbmv\b",
    "chile": r"chile|chilen|codelco|\bipsa\b|santiago de chile|\btpm\b|\bboric\b|\bkast\b|valpara[ií]so|antofagasta",
    "japon": r"jap[oó]n|japones|tokio|nikkei|topix|banco de jap|\bboj\b|\byen(es)?\b|toyota|sony|honda|takaichi|ishiba|osaka",
    "reino": r"reino unido|brit[aá]nic|londres|inglaterra|ingl[eé]s(a|es)?\b|banco de inglaterra|\blibras?( esterlinas?)?\b|starmer|reeves|\bftse\b|escocia|brexit|\bcity de londres",
    "canada": r"canad[aá]|canadiense|ottawa|toronto|montreal|quebec|vancouver|carney|banco de canad|\btsx\b",
    "colombia": r"colombi|bogot[aá]|medell[ií]n|\bcali\b|barranquilla|petro\b|banco de la rep[uú]blica|ecopetrol|\bdane\b|colcap",
    "turquia": r"turqu[ií]a|turc[oa]s?\b|ankara|estambul|erdo[gğ]an|lira turca|\bbist\b",
    "peru": r"per[uú]\b|peruan|lima\b|bcrp|velarde|\bsoles?\b|sunat|arequipa|\bbvl\b",
    "polonia": r"polonia|polac[oa]s?\b|varsovia|cracovia|\bzlotys?\b|złoty|tusk|nawrocki|glapi[nń]ski|banco nacional de polonia",
}
MIN_ES = 15  # con menos titulares en español que esto, se suman los de medios en inglés
ECON_EN = (r"econom|\bmarkets?\b|stocks?\b|\bshares\b|inflation|interest rates?|\brates?\b|central bank|\bfed\b|\becb\b|currenc|"
           r"dollar|\beuros?\b|zloty|\blira\b|\byen\b|sterling|\bpounds?\b|\breal\b|\boil\b|crude|tariff|\btrade\b|export|import|"
           r"\bdebt\b|\bgdp\b|recession|\bjobs?\b|unemploy|employ|wages?\b|prices?\b|invest|\bbanks?\b|banking|budget|deficit|"
           r"surplus|\btax|\bbonds?\b|yields?\b|financ|bitcoin|crypto|\bgold\b|mortgage|earnings|profit|revenue|billion|"
           r"million|compan|business|industr|growth|\bimf\b|manufactur|consumer|retail|housing|energy|subsid|fiscal|monetary")
OTROS_EN = (r"argentin|milei|china|chinese|india\b|indian\b|russia|ukrain|\biran|israel|gaza|saudi|turk(ey|ish)|t[uü]rkiye|korea|"
            r"canad|britain|british|\buk\b|germany|german\b|france|french|ital(y|ian)|spain|spanish|europe|\beu\b|"
            r"united states|u\.s\.|american|washington|trump|wall street|brazil|mexic|japan|poland|polish|colombia|chile|peru")
PAIS_EN = {
    "eeuu": r"united states|u\.s\.|\bus (economy|stocks|treasur|tariff|inflation|jobs)|american|wall street|\bfed\b|federal reserve|"
            r"powell|trump|washington|nasdaq|dow jones|s&p 500",
    "brasil": r"brazil|lula\b|petrobras|s[aã]o paulo|bovespa|selic|haddad|\bbrazilian real",
    "europa": r"europe|eurozone|euro zone|\becb\b|lagarde|\beu\b|germany|german\b|france|french|ital(y|ian)|spain|spanish|\bdax\b",
    "mexico": r"mexic|banxico|sheinbaum|pemex|usmca",
    "chile": r"chile|codelco",
    "japon": r"japan|tokyo|nikkei|topix|bank of japan|\bboj\b|\byen\b|toyota|sony|takaichi|osaka",
    "reino": r"britain|british|\buk\b|u\.k\.|england|london|bank of england|\bboe\b|sterling|starmer|reeves|ftse|scotland|brexit",
    "canada": r"canad|ottawa|toronto|montreal|quebec|alberta|vancouver|bank of canada|carney|\btsx\b",
    "colombia": r"colombia|bogot[aá]|ecopetrol|petro\b",
    "turquia": r"turk(ey|ish)|t[uü]rkiye|ankara|istanbul|erdo[gğ]an|\blira\b|[şs]im[şs]ek|karahan|\bbist\b",
    "peru": r"\bperu|lima\b",
    "polonia": r"poland|polish|warsaw|zloty|złoty|tusk|nawrocki|krak[oó]w|gda[nń]sk|\bnbp\b|glapi[nń]ski|\bwig(20)?\b",
}
RUIDO_EN = re.compile(r"football|soccer|\bnba\b|\bnfl\b|murder|shooting|\bkilled\b|\bdies\b|\bdead\b|actor|actress|\bfilm\b|movie|"
                      r"weather|earthquake|hurricane|horoscope|celebrit|abortion|espionage|\bspy\b|court acquits", re.I)
# (medio, url, {país: "todo" | "econ" | "pais"})
#   todo = entra todo · econ = solo titulares de economía (medio del país; se saltean los que hablan de otro país)
#   pais = solo si nombra al país y es de economía (medio de otro lado)
FEEDS = [
    ("El Economista (México)", "https://www.eleconomista.com.mx/rss/ultimas-noticias", {"mexico": "econ"}),
    ("El Financiero", "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml", {"mexico": "econ"}),
    ("La Jornada", "https://www.jornada.com.mx/rss/economia.xml", {"mexico": "econ"}),
    ("Expansión México", "https://expansion.mx/rss", {"mexico": "econ"}),
    ("El Universal", "https://www.eluniversal.com.mx/arc/outboundfeeds/rss/category/cartera/?outputType=xml", {"mexico": "econ"}),
    ("Cinco Días", "https://feeds.elpais.com/mrss-s/pages/ep/site/cincodias.elpais.com/portada", {"europa": "econ", "eeuu": "pais", "brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("Expansión", "https://e00-expansion.uecdn.es/rss/mercados.xml", {"europa": "econ", "eeuu": "pais", "brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("Euronews", "https://es.euronews.com/rss?level=vertical&name=business", {"europa": "econ", "eeuu": "pais", "brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("El País", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada", {"europa": "pais", "eeuu": "pais", "brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("El País América", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/america/portada", {"brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("El País EE.UU.", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/us/portada", {"eeuu": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("DW", "https://rss.dw.com/xml/rss-sp-eco", {"europa": "pais", "eeuu": "pais", "brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("France 24", "https://www.france24.com/es/econom%C3%ADa/rss", {"europa": "pais", "eeuu": "pais", "brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("France 24", "https://www.france24.com/es/am%C3%A9rica-latina/rss", {"brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("BBC Mundo", "https://feeds.bbci.co.uk/mundo/rss.xml", {"europa": "pais", "eeuu": "pais", "brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/estados-unidos/", {"eeuu": "econ", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/", {"eeuu": "pais", "brasil": "pais", "mexico": "pais", "europa": "pais"}),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/america/", {"brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("Ámbito", "https://www.ambito.com/rss/pages/economia.xml", {"eeuu": "pais", "brasil": "pais", "mexico": "pais", "europa": "pais"}),
    ("NHK World", "https://www3.nhk.or.jp/nhkworld/data/es/news/all.json", {"japon": "econ"}),
    ("Europa Press", "https://www.europapress.es/rss/rss.aspx?ch=00069", {"reino": "pais", "europa": "pais", "eeuu": "pais"}),
    ("El Tiempo", "https://www.eltiempo.com/rss/economia.xml", {"colombia": "econ"}),
    ("Portafolio", "https://www.portafolio.co/rss/economia.xml", {"colombia": "econ"}),
    ("La República", "https://www.larepublica.co/rss/economia", {"colombia": "econ"}),
    ("Semana", "https://www.semana.com/arc/outboundfeeds/rss/category/economia/?outputType=xml", {"colombia": "econ"}),
    ("Valora Analitik", "https://www.valoraanalitik.com/feed/", {"colombia": "econ"}),
    ("Gestión", "https://gestion.pe/arc/outboundfeeds/rss/category/economia/?outputType=xml", {"peru": "econ"}),
    ("El Comercio", "https://elcomercio.pe/arc/outboundfeeds/rss/category/economia/?outputType=xml", {"peru": "econ"}),
    ("La República (Perú)", "https://larepublica.pe/rss/economia.xml", {"peru": "econ"}),
    ("Andina", "https://andina.pe/agencia/rss/3.xml", {"peru": "econ"}),
    ("RPP", "https://rpp.pe/feed/economia", {"peru": "econ"}),
    ("La Tercera", "https://www.latercera.com/arc/outboundfeeds/rss/category/pulso/?outputType=xml", {"chile": "econ"}),
    ("Diario Financiero", "https://www.df.cl/noticias/site/list/port/rss.xml", {"chile": "econ"}),
    ("Cooperativa", "https://www.cooperativa.cl/noticias/site/tax/port/all/rss_6___1.xml", {"chile": "econ"}),
    ("Ex-Ante", "https://www.ex-ante.cl/feed/", {"chile": "econ"}),
    ("Agência Brasil", "https://agenciabrasil.ebc.com.br/es/rss/ultimasnoticias/feed.xml", {"brasil": "econ"}),
    ("Agência Brasil", "https://agenciabrasil.ebc.com.br/es/rss/economia/feed.xml", {"brasil": "econ"}),
    ("MercoPress", "https://es.mercopress.com/rss/", {"brasil": "pais", "mexico": "pais", "chile": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "colombia": "pais", "turquia": "pais", "peru": "pais", "polonia": "pais"}),
    ("La Nación", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/economia/", {"eeuu": "pais", "brasil": "pais", "mexico": "pais", "europa": "pais"}),
    ("EFE", "https://efe.com/economia/feed/", {"europa": "pais", "brasil": "pais", "japon": "pais", "reino": "pais", "canada": "pais", "turquia": "pais", "polonia": "pais"}),
    ("iProfesional", "https://www.iprofesional.com/rss/economia", {"eeuu": "pais", "brasil": "pais", "mexico": "pais", "europa": "pais"}),
    ("Ámbito", "https://www.ambito.com/rss/pages/mundo.xml", {"eeuu": "pais", "brasil": "pais", "mexico": "pais", "europa": "pais"}),
]
# Medios en inglés: solo completan a los países con pocos titulares en español (MIN_ES)
INT_EN = {"polonia": "pais", "turquia": "pais", "reino": "pais", "canada": "pais", "brasil": "pais", "japon": "pais", "chile": "pais", "peru": "pais", "colombia": "pais", "mexico": "pais"}
FEEDS_EN = [
    ("Notes from Poland", "https://notesfrompoland.com/feed/", {"polonia": "econ"}),
    ("TVP World", "https://tvpworld.com/rss", {"polonia": "econ"}),
    ("Polskie Radio", "https://www.polskieradio.pl/395/7784/Rss", {"polonia": "econ"}),
    ("Daily Sabah", "https://www.dailysabah.com/rss/business", {"turquia": "econ"}),
    ("Hürriyet Daily News", "https://www.hurriyetdailynews.com/rss/economy", {"turquia": "econ"}),
    ("Anadolu Agency", "https://www.aa.com.tr/en/rss/default?cat=economy", {"turquia": "econ"}),
    ("BBC", "https://feeds.bbci.co.uk/news/business/rss.xml", {**INT_EN, "reino": "econ"}),
    ("The Guardian", "https://www.theguardian.com/uk/business/rss", {**INT_EN, "reino": "econ"}),
    ("CBC", "https://www.cbc.ca/webfeed/rss/rss-business", {"canada": "econ"}),
    ("Global News", "https://globalnews.ca/money/feed/", {"canada": "econ"}),
    ("Financial Post", "https://financialpost.com/feed", {"canada": "econ"}),
    ("NHK World", "https://www3.nhk.or.jp/nhkworld/data/en/news/all.json", {"japon": "econ"}),
    ("The Japan Times", "https://www.japantimes.co.jp/business/feed/", {"japon": "econ"}),
    ("Agência Brasil", "https://agenciabrasil.ebc.com.br/en/rss/economia/feed.xml", {"brasil": "econ"}),
    ("Agência Brasil", "https://agenciabrasil.ebc.com.br/en/rss/ultimasnoticias/feed.xml", {"brasil": "econ"}),
    ("MercoPress", "https://en.mercopress.com/rss/", INT_EN),
    ("Euronews", "https://www.euronews.com/rss?level=vertical&name=business", INT_EN),
    ("DW", "https://rss.dw.com/rdf/rss-en-bus", INT_EN),
    ("CNBC", "https://www.cnbc.com/id/100727362/device/rss/rss.html", INT_EN),
]
# temas que no son de economía aunque nombren plata (deportes, policiales, espectáculos, clima)
RUIDO = re.compile(r"golea|\bgol(es)?\b|f[uú]tbol|\bliga\b|partido de|campeonato|\bnba\b|\bnfl\b|secuestr|asesin|homicid|"
                   r"tiroteo|\bmuere\b|\bmuerto|cantante|\bactor\b|actriz|pel[ií]cula|taquilla|hurac[aá]n|sismo|terremoto|"
                   r"mercado negro|celular|hor[oó]scopo", re.I)
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


def entradas(url):
    """(título, link, fecha, es de la sección economía) de un RSS/Atom o del JSON de NHK World."""
    raw = get(url)
    if url.endswith(".json"):  # NHK World en español: {"data": [{title, page_url, public_at (ms), categories{name}}]}
        for x in json.loads(raw.decode("utf-8", "replace")).get("data") or []:
            try:
                d = datetime.fromtimestamp(int(x.get("public_at") or x.get("updated_at")) / 1000, timezone.utc)
            except (TypeError, ValueError):
                continue
            cat = str((x.get("categories") or {}).get("name") or "").upper()
            yield limpiar(x.get("title")), "https://www3.nhk.or.jp" + str(x.get("page_url") or ""), d, cat == "BUSINESS"
        return
    for it in ET.fromstring(raw).iter():
        if it.tag.split("}")[-1] not in ("item", "entry"):
            continue
        h = {c.tag.split("}")[-1]: c for c in it}
        t = limpiar(h["title"].text if "title" in h else "")
        link = ((h["link"].text or h["link"].get("href") or "").strip()) if "link" in h else ""
        yield t, link, fecha(next((h[k].text for k in ("pubDate", "published", "updated", "date") if k in h), "")), False


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
    por_pais_en = {p: [] for p in PAIS}
    fuentes, errores = {}, []
    for medio, url, reglas, en in [(*f, False) for f in FEEDS] + [(*f, True) for f in FEEDS_EN]:
        clave_f = f"{medio} · {url.split('/')[2]}"
        try:
            n = 0
            for t, link, d, cat_econ in entradas(url):
                if not t or BASURA.match(t) or (RUIDO_EN if en else RUIDO).search(t) or len(t) < 25 or not link.startswith("http") or not d or d < corte or d > ahora + timedelta(hours=1):
                    continue
                es_econ = cat_econ or bool(re.search(ECON_EN if en else ECON, t, re.I))
                for pais, regla in reglas.items():
                    nombra = bool(re.search((PAIS_EN if en else PAIS)[pais], t, re.I))
                    otro = not nombra and bool(re.search(OTROS_EN if en else OTROS, t, re.I))
                    if (regla == "todo" and not otro) or (regla == "econ" and es_econ and not otro) or (regla == "pais" and nombra and es_econ):
                        x = {"t": t, "u": link, "f": medio, "h": d.isoformat(timespec="minutes")}
                        if en:
                            x["l"] = "en"
                        (por_pais_en if en else por_pais)[pais].append(x)
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
        if len(unicos) < MIN_ES:  # pocos en español: se completa con titulares en inglés, después de los de español
            for x in sorted(por_pais_en[pais], key=lambda x: x["h"], reverse=True):
                k = re.sub(r"\W+", "", x["t"].lower())[:60]
                if k not in vistos and len(unicos) < 30:
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
