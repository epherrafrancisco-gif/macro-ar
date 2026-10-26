import urllib.request, re
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30); return r.status, r.read().decode("utf-8","replace")
    except Exception as e: return "ERR", str(e)
for d in ["2026/10/","2026/10/26/","2025/12/30/","2025/12/01/","2026/01/02/","2026/06/15/","2026/10/01/"]:
    s, t = get(f"https://www.rava.com/cotizaciones/historico/merval/{d}")
    txt = re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",t)); j = txt.find("Cotizacion del MERVAL")
    print("RAVA", d, s, len(t), txt[j:j+520] if j>=0 else txt[:400])
    if d == "2026/10/": print("  HREFS", re.findall(r'href="([^"]*merval[^"]*)"', t)[:30])
