import json, urllib.request
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
out = {}
for k, u in {"all": "https://www3.nhk.or.jp/nhkworld/data/es/news/all.json",
             "biz": "https://www3.nhk.or.jp/nhkworld/data/es/news/business.json",
             "rss_es": "https://www3.nhk.or.jp/nhkworld/es/news/feeds/",
             "rss_es2": "https://www3.nhk.or.jp/nhkworld/rss/es/news.xml"}.items():
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=40) as r: t = r.read().decode("utf-8", "replace")
        out[k] = t[:3000]
    except Exception as e: out[k] = repr(e)[:200]
open("probe.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))
