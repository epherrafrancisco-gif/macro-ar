"""Arma geopolitica.json para el apartado "Geopolítica" de Mundo en Pulso Macro.

- Conflictos armados en curso: Wikipedia, "List of ongoing armed conflicts" (CC BY-SA 4.0). Cuatro niveles según las muertes
  del último año (guerras mayores 10.000+, guerras menores 1.000-9.999, conflictos 100-999, enfrentamientos 1-99). Se
  traducen los nombres con los enlaces al artículo en español cuando existe.
- Índice de riesgo geopolítico (Caldara e Iacoviello, Fed): diario (se actualiza los lunes) y mensual con 44 países.
  Los archivos son .xls: se leen con xlrd (pip install xlrd en el workflow).
- Gasto militar (Banco Mundial, datos del SIPRI): % del PBI y en dólares, último año de cada país.
Nunca inventa: si una fuente falla, queda lo que había y el error va a "errores".
"""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "geopolitica.json"
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
errores, diag = [], {}


def get(url, tries=3, timeout=90, binary=False):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
                return b if binary else b.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            if "404" in str(e) or "403" in str(e) or "429" in str(e):
                break
            time.sleep(3 * (i + 1))
    raise last


# ---------------- Wikipedia: tablas de conflictos ----------------
class Tablas(HTMLParser):
    """Junta las tablas 'wikitable' con celdas (texto, enlaces, rowspan) y el último título h2/h3 antes de cada una."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tablas, self.titulo, self.enh, self.prof = [], "", None, 0
        self.fila = self.celda = None
        self.skip = 0

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ("h2", "h3"):
            self.enh = ""
        if tag == "table":
            if self.prof == 0 and "wikitable" in (a.get("class") or ""):
                self.tablas.append({"titulo": self.titulo, "filas": []})
                self.prof = 1
            elif self.prof:
                self.prof += 1
        if not self.prof:
            return
        if tag in ("sup", "style") or "display:none" in (a.get("style") or "").replace(" ", ""):
            self.skip += 1
        if tag == "tr" and self.prof == 1:
            self.fila = []
            self.tablas[-1]["filas"].append(self.fila)
        if tag in ("td", "th") and self.prof == 1 and self.fila is not None:
            self.celda = {"th": tag == "th", "t": "", "links": [], "rs": int(re.sub(r"\D", "", a.get("rowspan") or "1") or 1), "li": []}
            self.fila.append(self.celda)
        if self.celda is not None and tag == "a" and not self.skip:
            href = a.get("href") or ""
            if href.startswith("/wiki/") and ":" not in href[6:]:
                self.celda["links"].append([urllib.parse.unquote(href[6:]).replace("_", " "), ""])
        if self.celda is not None and tag == "li":
            self.celda["li"].append("")
        if self.celda is not None and tag == "br":
            self.celda["t"] += "\n"

    def handle_endtag(self, tag):
        if tag in ("h2", "h3") and self.enh is not None:
            self.titulo, self.enh = self.enh.strip(), None
        if not self.prof:
            return
        if tag in ("sup", "style") and self.skip:
            self.skip -= 1
        if tag == "table":
            self.prof -= 1
        if tag in ("td", "th") and self.prof == 1:
            self.celda = None

    def handle_data(self, d):
        if self.enh is not None:
            self.enh += d
        if self.celda is not None and not self.skip:
            self.celda["t"] += d
            if self.celda["links"] and self.celda["links"][-1][1] == "" and d.strip():
                self.celda["links"][-1][1] = d.strip()
            if self.celda["li"]:
                self.celda["li"][-1] += d


def grilla(filas):
    """Expande los rowspan: devuelve filas completas de celdas."""
    out, pend = [], {}
    for f in filas:
        fila, i, cols = [], 0, list(f)
        while cols or i in pend:
            if i in pend:
                c, n = pend[i]
                fila.append(c)
                if n > 1:
                    pend[i] = (c, n - 1)
                else:
                    del pend[i]
            else:
                c = cols.pop(0)
                fila.append(c)
                if c["rs"] > 1:
                    pend[i] = (c, c["rs"] - 1)
            i += 1
        out.append(fila)
    return out


def num(t):
    m = re.search(r"\d[\d,\.]*", t or "")
    if not m:
        return None
    try:
        return int(m.group(0).replace(",", "").split(".")[0])
    except ValueError:
        return None


def limpio(t):
    t = re.sub(r"\[[^\]]*\]", "", t or "")
    return re.sub(r"\s+", " ", t).strip(" ;,")


def paises_wb():
    """Nombre en inglés → ISO3 (lista del Banco Mundial + alias de Wikipedia)."""
    j = json.loads(get("https://api.worldbank.org/v2/country?format=json&per_page=400"))
    m = {}
    for r in j[1]:
        if (r.get("region") or {}).get("value") != "Aggregates":
            m[r["name"].lower()] = r["id"]
    alias = {
        "democratic republic of the congo": "COD", "dr congo": "COD", "republic of the congo": "COG", "congo": "COG",
        "egypt": "EGY", "iran": "IRN", "syria": "SYR", "yemen": "YEM", "russia": "RUS", "venezuela": "VEN", "south korea": "KOR",
        "north korea": "PRK", "laos": "LAO", "turkey": "TUR", "türkiye": "TUR", "gambia": "GMB", "the gambia": "GMB",
        "ivory coast": "CIV", "côte d'ivoire": "CIV", "palestine": "PSE", "state of palestine": "PSE", "gaza strip": "PSE",
        "west bank": "PSE", "kyrgyzstan": "KGZ", "slovakia": "SVK", "czech republic": "CZE", "myanmar": "MMR", "burma": "MMR",
        "taiwan": "TWN", "kosovo": "XKX", "somaliland": "SOM", "western sahara": "ESH", "micronesia": "FSM", "bahamas": "BHS",
        "cape verde": "CPV", "eswatini": "SWZ", "brunei": "BRN", "vietnam": "VNM", "hong kong": "HKG", "macau": "MAC",
        "united states": "USA", "united kingdom": "GBR", "saint lucia": "LCA", "sudan": "SDN", "south sudan": "SSD",
        "central african republic": "CAF", "northern cyprus": "CYP", "transnistria": "MDA", "abkhazia": "GEO",
        "south ossetia": "GEO", "nagorno-karabakh": "AZE", "kashmir": "IND", "balochistan": "PAK", "tibet": "CHN",
        "xinjiang": "CHN", "iraqi kurdistan": "IRQ", "rojava": "SYR", "haiti": "HTI", "ecuador": "ECU",
    }
    m.update(alias)
    return m


def conflictos(prev):
    html = json.loads(get("https://en.wikipedia.org/w/api.php?action=parse&page=List_of_ongoing_armed_conflicts&prop=text|revid&format=json&formatversion=2"))
    rev = html.get("parse", {}).get("revid")
    p = Tablas()
    p.feed(html["parse"]["text"])
    niveles = [("mayor", r"major wars"), ("menor", r"minor wars"), ("conflicto", r"^conflicts"), ("choque", r"skirmish")]
    iso = paises_wb()
    out, usados = [], set()
    diag["wiki_tablas"] = [t["titulo"][:40] for t in p.tablas][:12]
    for nivel, rx in niveles:
        tab = next((t for t in p.tablas if re.search(rx, t["titulo"], re.I) and id(t) not in usados), None)
        if not tab:
            errores.append(f"Wikipedia: no encontré la tabla de {nivel}")
            continue
        usados.add(id(tab))
        filas = grilla(tab["filas"])
        enc = next((f for f in filas if f and all(c["th"] for c in f)), None)
        cols = [limpio(c["t"]).lower() for c in enc] if enc else []
        def col(rx, d):
            return next((i for i, c in enumerate(cols) if re.search(rx, c)), d)
        ci = {"ini": col(r"start", 0), "con": col(r"^conflict", 1), "cont": col(r"continent", 2), "loc": col(r"location", 3),
              "acum": col(r"cumulative", 4)}
        anios = [(i, re.search(r"(20\d\d)", c).group(1)) for i, c in enumerate(cols) if re.search(r"20\d\d", c) and "cumulative" not in c]
        diag.setdefault("wiki_cols", {})[nivel] = cols
        vistos = {}
        for f in filas:
            if not f or all(c["th"] for c in f) or len(f) <= ci["loc"]:
                continue
            cc = f[ci["con"]]
            if id(cc) in vistos:  # misma celda por rowspan: se suman los países de esta fila
                for t, txt in f[ci["loc"]]["links"]:
                    k = iso.get(t.lower()) or iso.get((txt or "").lower())
                    if k and k not in vistos[id(cc)]["iso"]:
                        vistos[id(cc)]["iso"].append(k)
                continue
            links = [x for x in cc["links"] if x[1]]
            cab = cc["t"]
            for li in cc["li"]:  # el nombre es lo que va antes de la lista de sub-conflictos
                if li.strip():
                    cab = cab.replace(li, "\n", 1)
            nombre = limpio(cab.strip().split("\n")[0]) or limpio(links[0][1] if links else "")
            if not nombre:
                continue
            subs = [limpio(x) for x in cc["li"] if limpio(x)][:8]
            loc = f[ci["loc"]]
            isos = []
            for t, txt in loc["links"]:
                k = iso.get(t.lower()) or iso.get((txt or "").lower())
                if k and k not in isos:
                    isos.append(k)
            item = {"n": nombre, "w": links[0][0] if links else None, "nivel": nivel, "ini": num(f[ci["ini"]]["t"]),
                    "cont": limpio(f[ci["cont"]]["t"]) if len(f) > ci["cont"] else "", "lugar": limpio(loc["t"]), "iso": isos,
                    "acum": limpio(f[ci["acum"]]["t"]) if len(f) > ci["acum"] else "", "sub": subs,
                    "muertes": {a: limpio(f[i]["t"]) for i, a in anios if i < len(f)}}
            vistos[id(cc)] = item
            out.append(item)
    if len(out) < 15:
        raise ValueError(f"muy pocos conflictos ({len(out)}): cambió la página")
    # nombres en español (artículo de Wikipedia en español, si existe)
    titulos = [x["w"] for x in out if x["w"]]
    es = {}
    for i in range(0, len(titulos), 40):
        q = "|".join(titulos[i:i + 40])
        try:
            j = json.loads(get("https://en.wikipedia.org/w/api.php?action=query&prop=langlinks&lllang=es&redirects=1&format=json&formatversion=2&titles=" + urllib.parse.quote(q)))
            red = {r["from"]: r["to"] for r in j.get("query", {}).get("redirects", [])}
            nor = {r["from"]: r["to"] for r in j.get("query", {}).get("normalized", [])}
            pag = {pg["title"]: (pg.get("langlinks") or [{}])[0].get("title") for pg in j.get("query", {}).get("pages", [])}
            for t in titulos[i:i + 40]:
                t2 = nor.get(t, t)
                t2 = red.get(t2, t2)
                if pag.get(t2):
                    es[t] = pag[t2]
        except Exception as e:  # noqa: BLE001
            errores.append(f"Wikipedia en español: {e}")
        time.sleep(0.5)
    for x in out:
        if x["w"] in es and not es[x["w"]].startswith("Anexo:"):
            x["wes"] = es[x["w"]]
        k = clave(x["n"])
        if k in TRAD:
            x["es"] = TRAD[k]
        elif x["w"] in es and not es[x["w"]].startswith("Anexo:"):
            x["es"] = es[x["w"]]
        else:
            diag.setdefault("sin_traducir", []).append(x["n"])
    return {"lista": out, "revid": rev, "al": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")}


def clave(t):
    t = re.sub(r"\([^)]*\)", "", t or "").replace("–", "-").replace("—", "-").lower()
    return re.sub(r"\s+", " ", t).strip()


# Nombres en español (a mano; si aparece un conflicto nuevo, queda el título de Wikipedia en español o el inglés y va a diag.sin_traducir)
TRAD = {clave(k): v for k, v in {
    "Arab-Israeli/Iran-Israel proxy wars": "Conflicto árabe-israelí y guerras de Israel con Irán y sus aliados",
    "Myanmar civil war": "Guerra civil de Myanmar", "Sudanese civil wars": "Guerras civiles de Sudán", "Congolese conflicts": "Conflictos del Congo",
    "Somali Civil War": "Guerra civil de Somalia", "Islamist insurgencies in the Maghreb/Sahel": "Insurgencias islamistas en el Magreb y el Sahel",
    "Mexican drug war": "Guerra contra el narcotráfico en México", "Russo-Ukrainian war": "Guerra entre Rusia y Ucrania",
    "Insurgencies in Iran": "Insurgencias en Irán", "Insurgencies in Pakistan": "Insurgencias en Pakistán", "Ethiopian civil wars": "Guerras civiles de Etiopía",
    "Colombian conflict": "Conflicto armado de Colombia", "Afghanistan conflicts": "Conflictos de Afganistán", "Ecuadorian conflict": "Conflicto interno de Ecuador",
    "Civil conflicts in Nigeria": "Conflictos internos de Nigeria", "Venezuelan conflict": "Conflicto de Venezuela", "Yemeni civil war": "Guerra civil de Yemen",
    "Aftermath/Spillover of the Syrian civil war": "Secuelas de la guerra civil siria", "Cameroonian conflicts": "Conflictos de Camerún",
    "Central African Republic Civil War": "Guerra civil de la República Centroafricana", "Haitian conflict": "Conflicto de Haití (pandillas)",
    "Kurdish nationalist conflicts": "Conflictos del nacionalismo kurdo", "Insurgencies in Turkey": "Insurgencias en Turquía",
    "Jamaican political conflict": "Conflicto político en Jamaica", "Kashmir conflict": "Conflicto de Cachemira", "Insurgencies in India": "Insurgencias en la India",
    "Papua conflict": "Conflicto de Papúa", "Civil conflict in the Philippines": "Conflicto interno de Filipinas", "Insurgencies in Bangladesh": "Insurgencias en Bangladés",
    "Cabinda War": "Guerra de Cabinda (Angola)", "Ethnic violence in Papua New Guinea": "Violencia étnica en Papúa Nueva Guinea",
    "Brazilian drug war": "Guerra contra el narcotráfico en Brasil", "Iraqi conflict": "Conflicto de Irak", "Libyan crisis": "Crisis de Libia",
    "Insurgency in Cabo Delgado": "Insurgencia en Cabo Delgado (Mozambique)", "Honduran gang crackdown": "Ofensiva contra las pandillas en Honduras",
    "Cross border attacks in Sabah/Drug trafficking in Malaysia": "Ataques en Sabah y narcotráfico en Malasia", "Western Sahara conflict": "Conflicto del Sahara Occidental",
    "Insurgency in Laos": "Insurgencia en Laos", "Peruvian conflict": "Conflicto interno de Perú", "Casamance conflict": "Conflicto de Casamanza (Senegal)",
    "Nagorno-Karabakh conflict": "Conflicto de Nagorno Karabaj", "North Caucasus conflict": "Conflicto del Cáucaso Norte",
    "South Thailand insurgency": "Insurgencia en el sur de Tailandia", "Insurgency in Paraguay": "Insurgencia en Paraguay",
    "Islamic insurgency in Egypt": "Insurgencia islamista en Egipto", "Salvadoran gang crackdown": "Guerra contra las pandillas en El Salvador",
    "Sri Lankan drug war": "Guerra contra el narcotráfico en Sri Lanka",
    # la celda a veces trae solo la primera parte del nombre
    "Arab-Israeli": "Conflicto árabe-israelí y guerras de Israel con Irán y sus aliados",
    "Islamist insurgencies in the Maghreb": "Insurgencias islamistas en el Magreb y el Sahel",
    "Aftermath": "Secuelas de la guerra civil siria", "Cross border attacks in Sabah": "Ataques en Sabah y narcotráfico en Malasia",
}.items()}


# ---------------- Índice de riesgo geopolítico (Caldara e Iacoviello) ----------------
def xls_tabla(b):
    import xlrd  # noqa: PLC0415
    wb = xlrd.open_workbook(file_contents=b)
    sh = wb.sheet_by_index(0)
    enc = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
    filas = [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(1, sh.nrows)]
    return wb, enc, filas


def fecha_xls(v, wb):
    import xlrd  # noqa: PLC0415
    if isinstance(v, float) and v > 1000:
        return xlrd.xldate_as_datetime(v, wb.datemode).date()
    s = str(v).strip()
    for f in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%Y-%m"):
        try:
            return datetime.strptime(s[:10], f).date()
        except ValueError:
            pass
    return None


def gpr(prev):
    base = "https://www.matteoiacoviello.com/"
    html = get(base + "gpr.htm")
    hrefs = re.findall(r'href=["\']([^"\']+\.xls)["\']', html, re.I)
    diag["gpr_links"] = hrefs[:10]
    dia = next((h for h in hrefs if "daily" in h.lower()), None)
    mes = next((h for h in hrefs if "export" in h.lower() and "daily" not in h.lower()), None)
    res = {}
    if dia:
        wb, enc, filas = xls_tabla(get(urllib.parse.urljoin(base, dia), binary=True))
        diag["gpr_dia_cols"] = enc[:20]
        cf = next((i for i, c in enumerate(enc) if c.lower() in ("date", "day")), 0)
        cg = next((i for i, c in enumerate(enc) if c.upper() == "GPRD"), None)
        cm = next((i for i, c in enumerate(enc) if c.upper() in ("GPRD_MA7", "GPRD_MA30")), None)
        ca = next((i for i, c in enumerate(enc) if c.upper() == "GPRD_ACT"), None)
        ct = next((i for i, c in enumerate(enc) if c.upper() == "GPRD_THREAT"), None)
        if cg is None:
            raise ValueError("GPR diario: no encontré la columna GPRD")
        serie = []
        for f in filas:
            d = fecha_xls(f[cf], wb)
            if d and isinstance(f[cg], float):
                serie.append([d.isoformat(), round(f[cg], 1), round(f[cm], 1) if cm is not None and isinstance(f[cm], float) else None,
                              round(f[ca], 1) if ca is not None and isinstance(f[ca], float) else None,
                              round(f[ct], 1) if ct is not None and isinstance(f[ct], float) else None])
        serie.sort()
        res["diario"] = serie[-1100:]
    else:
        errores.append("GPR: no encontré el archivo diario")
    if mes:
        wb, enc, filas = xls_tabla(get(urllib.parse.urljoin(base, mes), binary=True))
        diag["gpr_mes_cols"] = enc[:12] + [c for c in enc if c.upper().startswith("GPRC_")][:3]
        cf = next((i for i, c in enumerate(enc) if c.lower() in ("month", "date")), 0)
        idx = {c.upper(): i for i, c in enumerate(enc)}
        mens, hist, paises = [], [], {}
        for f in filas:
            d = fecha_xls(f[cf], wb)
            if not d:
                continue
            m = d.strftime("%Y-%m")
            if "GPR" in idx and isinstance(f[idx["GPR"]], float):
                mens.append([m, round(f[idx["GPR"]], 1), round(f[idx["GPRT"]], 1) if "GPRT" in idx and isinstance(f[idx["GPRT"]], float) else None,
                             round(f[idx["GPRA"]], 1) if "GPRA" in idx and isinstance(f[idx["GPRA"]], float) else None])
            if "GPRH" in idx and isinstance(f[idx["GPRH"]], float):
                hist.append([m, round(f[idx["GPRH"]], 1)])
            for c, i in idx.items():
                if c.startswith("GPRC_") and isinstance(f[i], float) and d.year >= 2015:
                    paises.setdefault(c[5:], []).append([m, round(f[i], 3)])
        res["mensual"] = sorted(mens)
        res["historico"] = sorted(hist)
        res["paises"] = {k: sorted(v)[-36:] for k, v in paises.items()}
    else:
        errores.append("GPR: no encontré el archivo mensual")
    if not res:
        raise ValueError("sin datos")
    res["al"] = date.today().isoformat()
    return res


# ---------------- Gasto militar (Banco Mundial / SIPRI) ----------------
def gasto_militar(prev):
    out = {}
    for k, ind in (("pbi", "MS.MIL.XPND.GD.ZS"), ("usd", "MS.MIL.XPND.CD")):
        j = json.loads(get(f"https://api.worldbank.org/v2/country/all/indicator/{ind}?format=json&mrv=1&per_page=400"))
        for r in j[1] or []:
            c, v = r.get("countryiso3code"), r.get("value")
            if c and v is not None and len(c) == 3:
                out.setdefault(c, {})[k] = round(float(v), 3 if k == "pbi" else 0)
                out[c]["a"] = r["date"]
                out[c]["n"] = (r.get("country") or {}).get("value")
        time.sleep(0.5)
    if len(out) < 50:
        raise ValueError("pocos países")
    return {"paises": out, "al": date.today().isoformat()}


def main():
    try:
        prev = json.loads(OUT.read_text())
    except Exception:  # noqa: BLE001
        prev = {}
    data = {k: prev[k] for k in ("conflictos", "gpr", "militar") if k in prev}
    for k, fn, cada in (("conflictos", conflictos, 0), ("gpr", gpr, 0), ("militar", gasto_militar, 7)):
        try:
            al = (prev.get(k) or {}).get("al", "2000-01-01")[:10]
            if cada and (date.today() - date.fromisoformat(al)).days < cada:
                continue
            data[k] = fn(prev.get(k) or {})
        except Exception as e:  # noqa: BLE001
            errores.append(f"{k}: {e}")
    data["actualizado"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")
    data["errores"] = errores
    data["diag"] = diag
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print("conflictos:", len((data.get("conflictos") or {}).get("lista", [])), "| gpr diario:", len((data.get("gpr") or {}).get("diario", [])),
          "| paises gpr:", len((data.get("gpr") or {}).get("paises", {})), "| errores:", errores)


if __name__ == "__main__":
    main()
