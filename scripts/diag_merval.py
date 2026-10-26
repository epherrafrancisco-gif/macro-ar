import json, http.cookiejar, urllib.request, ssl, time
ctx = ssl.create_default_context()
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ctx))
H = {"Accept": "application/json, text/plain, */*", "Content-Type": "application/json", "Origin": "https://open.bymadata.com.ar",
     "Referer": "https://open.bymadata.com.ar/", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
B = "https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/"
def req(url, data=None):
    try:
        r = op.open(urllib.request.Request(url, data=data.encode() if data is not None else None, headers=H, method="POST" if data is not None else "GET"), timeout=40)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR", str(e)
print("home", req("https://open.bymadata.com.ar/#/dashboard")[0])
for path, body in [("index-price", '{"Content-Type":"application/json"}'), ("market-time", "{}")]:
    s, t = req(B + path, body); print("==", path, s, t[:1500])
s, t = req(B + "public-bonds", '{"excludeZeroPxAndQty":true,"T2":true,"T1":false,"T0":false,"Content-Type":"application/json"}')
print("== public-bonds", s, len(t))
try:
    j = json.loads(t); d = j.get("data", j) if isinstance(j, dict) else j
    print(" n", len(d), "keys", list(d[0].keys()) if d else None)
    for x in d:
        if x.get("symbol") in ("AL30","AL30D","GD30D","GD35D"): print("  ", {k: x.get(k) for k in ("symbol","settlementType","trade","closingPrice","previousClosingPrice","imbalance","denominationCcy","tradeHour")})
except Exception as e: print(" parse", e, t[:300])
now = int(time.time())
for sym in ("M", "MERVAL", "IMV", "M.MERV", "MERV"):
    s, t = req(B + f"chart/historical-series/history?symbol={sym}&resolution=D&from={now-20*86400}&to={now}")
    print("== hist", sym, s, t[:400])
s, t = req(B + "chart/historical-series/history?symbol=AL30%2048HS&resolution=D&from=%d&to=%d" % (now-10*86400, now)); print("== hist AL30", s, t[:300])
s, t = req("https://open.bymadata.com.ar/robots.txt"); print("== robots", s, t[:300])
