"""Arma actividad.json para la sección "Actividad y empleo" de Argentina y la inflación por rubro.

Fuente oficial y gratuita, sin clave: la API de series de tiempo de datos.gob.ar (series del INDEC):
  - EMAE (actividad económica mensual), original y desestacionalizado.
  - Índice de salarios: total, registrado privado, público y no registrado.
  - Tasa de desocupación (EPH, trimestral).
  - Canasta básica total y alimentaria (por adulto equivalente).
  - IPC nacional por rubro (12 divisiones) y por categoría (núcleo, regulados, estacionales), con el nivel general.

Se renueva como máximo cada 6 horas (son datos mensuales). Uso: python scripts/actividad.py
Nunca inventa datos: si una tanda falla, queda la que había. Las series atrasadas se sacan en vez de mostrarse.
"""

import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "actividad.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 PulsoMacro/1.0"
API = "https://apis.datos.gob.ar/series/api/series/?ids={ids}&start_date={desde}&limit=1000&format=json"
# tanda: (series {id: clave}, desde, meses de atraso tolerados)
TANDAS = {
    "emae": ({"143.3_NO_PR_2004_A_31": "emae_d", "143.3_NO_PR_2004_A_21": "emae"}, "2016-01-01", 5),
    "salarios": ({"149.1_TL_INDIIOS_OCTU_0_21": "sal_total", "149.1_SOR_PRIADO_OCTU_0_25": "sal_priv", "149.1_SOR_PUBICO_OCTU_0_14": "sal_pub",
                  "149.1_SOR_PRIADO_OCTU_0_28": "sal_noreg"}, "2016-10-01", 6),
    "desocupacion": ({"42.3_EPH_PUNTUAL_0_M_30": "desoc"}, "2016-01-01", 9),
    "canasta": ({"150.1_CSTA_BATAL_0_D_20": "cbt", "150.1_CSTA_BARIA_0_D_26": "cba"}, "2016-04-01", 5),
    "rubros": ({"145.3_INGNACNAL_DICI_M_15": "general", "146.3_IALIMENNAL_DICI_M_45": "alimentos", "146.3_IBEBIDANAL_DICI_M_39": "bebidas",
                "146.3_IPRENDANAL_DICI_M_35": "prendas", "146.3_IVIVIENNAL_DICI_M_52": "vivienda", "146.3_IEQUIPANAL_DICI_M_46": "equipamiento",
                "146.3_ISALUDNAL_DICI_M_18": "salud", "146.3_ITRANSPNAL_DICI_M_23": "transporte", "146.3_ICOMUNINAL_DICI_M_27": "comunicacion",
                "146.3_IRECREANAL_DICI_M_31": "recreacion", "146.3_IEDUCACNAL_DICI_M_22": "educacion", "146.3_IRESTAUNAL_DICI_M_33": "restaurantes",
                "146.3_IBIENESNAL_DICI_M_36": "varios", "148.3_INUCLEONAL_DICI_M_19": "nucleo", "148.3_IREGULANAL_DICI_M_22": "regulados",
                "148.3_IESTACINAL_DICI_M_25": "estacionales"}, "2022-01-01", 4),
}


def get(url, tries=3, timeout=90):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(4 * (i + 1))
    raise last


def tanda(series, desde):
    ids = list(series)
    j = get(API.format(ids=",".join(ids), desde=desde))
    out = {series[s]: [] for s in ids}
    for row in j.get("data", []):
        f = row[0][:7]
        for i, sid in enumerate(ids, start=1):
            if i < len(row) and row[i] is not None:
                out[series[sid]].append([f, round(float(row[i]), 4)])
    return {k: v for k, v in out.items() if v}


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    try:
        al = datetime.fromisoformat(prev.get("actualizado", "2000-01-01T00:00+00:00"))
        if (datetime.now(timezone.utc) - al) < timedelta(hours=6) and not prev.get("errores"):
            print("actividad.json reciente: no se renueva")
            return
    except ValueError:
        pass
    data, errores, hoy = dict(prev), [], date.today()
    for nombre, (series, desde, meses) in TANDAS.items():
        try:
            res = tanda(series, desde)
            if not res:
                raise ValueError("sin datos")
            lim = (hoy - timedelta(days=31 * meses)).isoformat()[:7]
            for k, pts in res.items():
                if pts[-1][0] < lim:
                    errores.append(f"{k}: atrasada (último {pts[-1][0]}), se saca")
                    data.pop(k, None)
                else:
                    data[k] = pts
        except Exception as e:  # noqa: BLE001
            errores.append(f"{nombre}: {e}")
        time.sleep(1)
    data["actualizado"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    data["errores"] = errores[:30]
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print({k: f"{len(v)} hasta {v[-1][0]}" for k, v in data.items() if isinstance(v, list) and v and isinstance(v[0], list)})
    for e in errores:
        print("ERROR", e)


if __name__ == "__main__":
    main()
