import json, urllib.request, urllib.parse
UA = {"User-Agent": "pulsomacro.com.ar (contacto@pulsomacro.com.ar)"}
def get(u):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
    except Exception as e: return {"error": str(e)}
Q = ["reservas internacionales", "tipo de cambio mayorista comunicacion A 3500", "base monetaria", "badlar", "tamar", "plazo fijo 30 dias tasa",
     "depositos en dolares sector privado", "M2", "M2 transaccional", "CER coeficiente", "LELIQ", "pases pasivos BCRA", "LEFI",
     "compra de divisas BCRA", "BOPREAL", "relevamiento de expectativas de mercado REM inflacion", "indice de precios al consumidor nacional"]
for q in Q:
    j = get("https://apis.datos.gob.ar/series/api/search/?" + urllib.parse.urlencode({"q": q, "limit": 8}))
    print("=== " + q)
    for r in j.get("data", []) if isinstance(j, dict) else []:
        f = r.get("field", {}); d = r.get("dataset", {})
        print("  ", f.get("id"), "|", f.get("frequency"), "|", f.get("time_index_end"), "|", (f.get("description") or "")[:90], "|", d.get("source") or d.get("publisher"), "|", d.get("license"))
    if isinstance(j, dict) and j.get("error"): print("  ERR", j["error"])
