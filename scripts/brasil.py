"""Arma brasil.json para la sección Brasil de Pulso Macro.

Fuentes oficiales y gratuitas, sin clave (Banco Central de Brasil):
  - SGS (series temporales): Selic meta (432), dólar PTAX venta (1), IPCA mensual (433) y de 12 meses (13522),
    IBC-Br sin desestacionalizar (24363, "PBI mensual"), desempleo PNAD (24369) y reservas internacionales (13621).
  - Olinda / Focus: lo que esperan los analistas (mediana) para IPCA, Selic, dólar y PBI de cada año.

Uso: python scripts/brasil.py
Nunca inventa datos: si una serie falla, queda la que había y se anota en "errores".
"""

import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "brasil.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
errores = []

# clave: (código SGS, años de historia, solo guardar cambios)
SGS = {"selic": (432, 6, True), "ptax": (1, 2, False), "ipca_m": (433, 6, False), "ipca_12": (13522, 6, False),
       "ibc": (24363, 7, False), "desemp": (24369, 6, False), "reservas": (13621, 2, False)}
FOCUS = {"ipca": "IPCA", "selic": "Selic", "cambio": "Câmbio", "pib": "PIB Total"}


def get(url, tries=4, timeout=40):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                txt = r.read().decode("utf-8", "replace")
            return json.loads(txt)
        except Exception as e:  # noqa: BLE001 (el BCB a veces da 502 o respuesta vacía: se reintenta)
            last = e
            time.sleep(3 * (i + 1))
    raise last


def sgs(codigo, anios, cambios):
    desde = (date.today() - timedelta(days=365 * anios)).strftime("%d/%m/%Y")
    j = get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial={desde}")
    pts = []
    for r in j:
        d, m, y = r["data"].split("/")
        try:
            pts.append([f"{y}-{m}-{d}", float(r["valor"])])
        except (TypeError, ValueError):
            continue
    pts.sort()
    if not pts:
        raise ValueError("sin datos")
    if cambios:  # series diarias que casi no cambian (Selic): solo los días en que cambia + el último
        out = [pts[0]]
        for p in pts[1:]:
            if p[1] != out[-1][1]:
                out.append(p)
        if out[-1] != pts[-1]:
            out.append(pts[-1])
        return out
    return pts


def focus():
    """Mediana de la encuesta Focus para este año y los dos siguientes, hoy y 4 semanas atrás."""
    out = {}
    anios = [str(date.today().year + i) for i in range(3)]
    for k, ind in FOCUS.items():
        f = urllib.parse.quote(f"Indicador eq '{ind}' and baseCalculo eq 0")
        j = get("https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"
                f"?$filter={f}&$orderby=Data%20desc&$top=200&$format=json&$select=Data,DataReferencia,Mediana")
        filas = j.get("value") or []
        if not filas:
            raise ValueError(f"{ind}: sin datos")
        ult = filas[0]["Data"]
        objetivo = (date.fromisoformat(ult) - timedelta(days=28)).isoformat()
        ant = next((r["Data"] for r in filas if r["Data"] <= objetivo), None)
        out[k] = {"fecha": ult, "fecha_ant": ant,
                  "anios": {a: {"v": next((r["Mediana"] for r in filas if r["Data"] == ult and r["DataReferencia"] == a), None),
                                "ant": next((r["Mediana"] for r in filas if r["Data"] == ant and r["DataReferencia"] == a), None)}
                            for a in anios}}
    return out


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    data = dict(prev)
    for k, (cod, anios, cambios) in SGS.items():
        try:
            data[k] = sgs(cod, anios, cambios)
        except Exception as e:  # noqa: BLE001
            errores.append(f"SGS {cod} ({k}): {e}")
        time.sleep(0.5)
    try:
        data["focus"] = focus()
    except Exception as e:  # noqa: BLE001
        errores.append(f"Focus: {e}")
    data["actualizado"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    data["errores"] = errores[:30]
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print({k: (len(v) if isinstance(v, list) else bool(v)) for k, v in data.items() if k not in ("actualizado", "errores")})
    for e in errores:
        print("ERROR", e)


if __name__ == "__main__":
    main()
