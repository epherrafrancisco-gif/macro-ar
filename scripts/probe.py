"""Probe temporal 2: formulario del Mercado Agroganadero y precios medios del INDEC. Se borra después."""
import json, re, urllib.request, urllib.parse
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, data=None):
    try:
        req = urllib.request.Request(u, data=data, headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=40); return r.read().decode("latin-1", "replace")
    except Exception as e:
        return "ERR " + str(e)[:200]
out = {}
h = get("https://www.mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo000002")
out["form"] = re.findall(r"<form.*?</form>", h, re.S | re.I)[:3]
out["inputs"] = re.findall(r"<(?:input|select)[^>]*>", h, re.I)[:40]
for n in ["000001", "000003", "000011", "000012", "000013", "000020"]:
    t = get(f"https://www.mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo{n}")
    pl = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    i = pl.find("Mercado Agroganadero S.A.", 200)
    out["p" + n] = pl[i:i + 1500] if i > 0 else pl[:800]
# probar con fechas por GET y POST
for nm, u, d in [
  ("get1", "https://www.mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo000002?txtFechaIni=16/10/2026&txtFechaFin=16/10/2026", None),
  ("get2", "https://www.mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo000002?txtFECHAINI=16/10/2026&txtFECHAFIN=16/10/2026&CP=&LISTADO=SI", None),
]:
    t = get(u, d); pl = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)); i = pl.find("PRECIOS POR CATEGORIA"); out[nm] = pl[i:i + 2500]
s = get("https://apis.datos.gob.ar/series/api/search/?limit=60&q=" + urllib.parse.quote("IPC-GBA Precios mensual"))
try:
    out["indec"] = [(x["field"]["id"], x["field"].get("description"), x["field"].get("time_index_end")) for x in json.loads(s)["data"]]
except Exception as e:
    out["indec"] = str(e) + s[:300]
for q in ["nalga", "carne picada", "cuadril", "paleta", "bife", "pollo", "Precios. "]:
    s = get("https://apis.datos.gob.ar/series/api/search/?limit=10&q=" + urllib.parse.quote(q))
    try: out["q_" + q] = [(x["field"]["id"], x["field"].get("description"), x["field"].get("time_index_end")) for x in json.loads(s)["data"]]
    except Exception as e: out["q_" + q] = str(e)
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
