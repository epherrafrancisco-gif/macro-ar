"""Probe temporal: fuentes para una sección de carnes/campo. Se borra después."""
import json, re, urllib.request, urllib.parse
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40)
        b = r.read(); ct = r.headers.get("Content-Type", "")
        return {"ok": r.status, "ct": ct, "len": len(b), "body": b}
    except Exception as e:
        return {"err": str(e)[:200]}
def txt(b):
    t = b.decode("utf-8", "replace")
    links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', t)))
    plain = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    plain = re.sub(r"<[^>]+>", " ", plain); plain = re.sub(r"\s+", " ", plain)
    return plain[:2500], [l for l in links if re.search(r"preci|haci|pizarra|informe|cotiz|novill|dll|carne|ganad|indice|inmag", l, re.I)][:80]
out = {}
U = {
 "mag_home": "https://www.mercadoagroganadero.com.ar/",
 "mag_dll2": "https://www.mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo000002",
 "mag_dll502": "https://www.mercadoagroganadero.com.ar/dll/hacienda6.dll/haciinfo000502",
 "cac_pizarra": "https://www.cac.bcr.com.ar/es/precios-de-pizarra",
 "bcr_home": "https://www.bcr.com.ar/es",
 "ipcva": "https://www.ipcva.com.ar/",
 "rosgan": "https://www.rosgan.com.ar/",
 "siocarnes_pdf": "https://www.magyp.gob.ar/sitio/areas/ss_mercados_agropecuarios/sistemas-de-informacion-de-operaciones-sio/sio-carnes/informes/_archivo/000001_%C3%9Altimo%20Informe%20Siocarnes.pdf",
}
for k, u in U.items():
    r = get(u)
    if "body" in r:
        if "pdf" in r["ct"]:
            r["body"] = None
        else:
            r["text"], r["links"] = txt(r.pop("body"))
    r.pop("body", None); out[k] = r
for q in ["novillo", "hacienda", "asado", "carne vacuna", "precio carne", "pizarra soja", "soja precio", "faena bovina"]:
    r = get("https://apis.datos.gob.ar/series/api/search/?limit=12&q=" + urllib.parse.quote(q))
    if "body" in r:
        try:
            j = json.loads(r["body"]); r = [{"id": x["field"]["id"], "t": x["field"].get("description"), "f": x["field"].get("frequency"), "end": x["field"].get("time_index_end"), "ds": x["dataset"].get("title")} for x in j.get("data", [])]
        except Exception as e:
            r = {"err": str(e)}
    out["dg_" + q] = r
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
