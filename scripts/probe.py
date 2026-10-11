"""Prueba temporal de fuentes de Brasil (se borra después)."""
import json, urllib.request, urllib.parse
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
def get(u, t=40):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "application/json,*/*"})
    return urllib.request.urlopen(r, timeout=t).read().decode("utf-8", "replace")
out = {}
for c in [432, 433, 13522, 1, 24364, 24363, 13621, 3546, 24369, 4380, 22099, 11, 4390, 20542, 189, 22707, 7326]:
    try:
        j = json.loads(get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{c}/dados/ultimos/3?formato=json"))
        out[f"sgs{c}"] = j
    except Exception as e:
        out[f"sgs{c}"] = str(e)[:150]
try:
    j = json.loads(get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=01/01/2020"))
    out["sgs433_len"] = len(j)
except Exception as e: out["sgs433_len"] = str(e)[:150]
for ind in ["IPCA", "Selic", "Câmbio", "PIB Total"]:
    f = urllib.parse.quote(f"Indicador eq '{ind}'")
    try:
        j = json.loads(get(f"https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?$filter={f}&$orderby=Data%20desc&$top=6&$format=json&$select=Indicador,Data,DataReferencia,Mediana,baseCalculo"))
        out["focus_" + ind] = j.get("value")
    except Exception as e:
        out["focus_" + ind] = str(e)[:150]
for k, u in {"sidra_desemp": "https://apisidra.ibge.gov.br/values/t/4099/n1/all/v/4099/p/last%203",
             "gob_search1": "https://apis.datos.gob.ar/series/api/search/?q=exportaciones%20brasil&limit=15",
             "gob_search2": "https://apis.datos.gob.ar/series/api/search/?q=intercambio%20comercial%20brasil&limit=15",
             "gob_search3": "https://apis.datos.gob.ar/series/api/search/?q=importaciones%20brasil&limit=15"}.items():
    try:
        out[k] = get(u)[:3000]
    except Exception as e:
        out[k] = str(e)[:150]
json.dump(out, open("probe.json", "w"), ensure_ascii=False, indent=1)
