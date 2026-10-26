import json, sys, urllib.request
sys.path.insert(0, "scripts"); import propios
UA = {"User-Agent": "pulsomacro.com.ar (contacto@pulsomacro.com.ar)"}
b = json.loads(urllib.request.urlopen(urllib.request.Request("https://data912.com/live/arg_bonds", headers=UA), timeout=40).read())
syms = {x["symbol"]: x for x in b if isinstance(x, dict)}
for s in ["AL30","AL30D","AL30C","GD30","GD30D","GD30C","GD29D","GD35D","GD38D","GD41D","GD46D"]:
    x = syms.get(s); print(s, {k: x.get(k) for k in ("c","px_bid","px_ask","v","pct_change")} if x else None)
print("campos:", list(b[0].keys()) if b else None)
c = json.load(open("usa.json"))["curva"]
r = propios.calcular(b, c)
print("PROPIOS:", json.dumps(r, ensure_ascii=False))
d = json.load(open("data.json"))["diario"]
for row in d[-3:]:
    print("AMBITO", row["fecha"], "mep", (row.get("mep") or {}).get("v"), "ccl", (row.get("ccl") or {}).get("v"), "riesgo", row.get("riesgo"))
