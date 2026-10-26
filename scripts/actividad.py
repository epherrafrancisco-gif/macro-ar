"""Arma actividad.json para la sección "Actividad y empleo" de Argentina y la inflación por rubro.

Fuente oficial y gratuita, sin clave: la API de series de tiempo de datos.gob.ar (series del INDEC):
  - EMAE (actividad económica mensual), original y desestacionalizado.
  - Índice de salarios: total, registrado privado, público y no registrado.
  - Tasa de desocupación (EPH, trimestral).
  - Canasta básica total y alimentaria (por adulto equivalente).
  - IPC nacional por rubro (12 divisiones) y por categoría (núcleo, regulados, estacionales), con el nivel general.
  - Carne al consumidor (precios medios del INDEC en GBA y carne picada por región) y faena de vacunos por mes.

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
UA = "Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)"
TRIM = {"desoc", "faena_t"}   # series trimestrales
API = "https://apis.datos.gob.ar/series/api/series/?ids={ids}&start_date={desde}&limit=1000&format=json"
# tanda: (series {id: clave}, desde, meses de atraso tolerados)
TANDAS = {
    "emae": ({"143.3_NO_PR_2004_A_31": "emae_d", "143.3_NO_PR_2004_A_21": "emae"}, "2016-01-01", 5),
    "salarios": ({"149.1_TL_INDIIOS_OCTU_0_21": "sal_total", "149.1_SOR_PRIADO_OCTU_0_25": "sal_priv", "149.1_SOR_PUBICO_OCTU_0_14": "sal_pub",
                  "149.1_SOR_PRIADO_OCTU_0_28": "sal_noreg"}, "2016-10-01", 6),
    "desocupacion": ({"45.2_ECTDT_0_T_33": "desoc"}, "2016-01-01", 9),
    "canasta": ({"150.1_CSTA_BATAL_0_D_20": "cbt", "150.1_CSTA_BARIA_0_D_26": "cba"}, "2016-04-01", 5),
    "carnes": ({"105.1_I2A_2016_M_14": "c_asado", "105.1_I2N_2016_M_14": "c_nalga", "105.1_I2C_2016_M_16": "c_cuadril",
                "105.1_I2P_2016_M_15": "c_paleta", "105.1_I2CPC_2016_M_27": "c_picada", "105.1_I2PE_2016_M_21": "c_pollo",
                "348.1_GBA_CARNE_KG__25": "rp_gba", "348.1_PAMPEANA_C_KG__30": "rp_pampeana", "348.1_NOA_CARNE_KG__25": "rp_noa",
                "348.1_NEA_CARNE_KG__25": "rp_nea", "348.1_CUYO_CARNE_KG__26": "rp_cuyo", "348.1_PATAGONIA_KG__31": "rp_patagonia",
                }, "2019-01-01", 4),
    # la faena mensual (41.3_FCV) viene vacía en la API: se usa la trimestral y el IPI de carne vacuna (mensual)
    "faena": ({"41.2_FCV_0_T_18": "faena_t", "453.2_CARNE_VACUUNA_0_0_12_53": "ipi_carne"}, "2021-01-01", 9),
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


def huecos(pts, paso):
    """Cuántos meses faltan entre el primero y el último (paso 1 = mensual, 3 = trimestral)."""
    if not pts:
        return 99
    y, m = map(int, pts[0][0].split("-"))
    y2, m2 = map(int, pts[-1][0].split("-"))
    esperados = ((y2 - y) * 12 + (m2 - m)) // paso + 1
    return esperados - len(pts)


def una(sid, clave, desde):
    j = get(API.format(ids=sid, desde=desde))
    pts = {}
    for row in j.get("data", []):
        if len(row) > 1 and row[1] is not None:
            v = float(row[1])
            if clave == "desoc" and v < 1:
                v *= 100  # viene como fracción (0,079)
            pts[row[0][:7]] = round(v, 4)
    return pts


def tanda(series, desde, prev):
    """Una consulta por serie. La API a veces devuelve meses vacíos al azar: se pide hasta 4 veces,
    se juntan los resultados y se completa con lo que ya estaba guardado (los datos publicados no cambian)."""
    out = {}
    for sid, clave in series.items():
        paso = 3 if clave in TRIM else 1
        junt = {p[0]: p[1] for p in prev.get(clave, []) if p[0] >= desde[:7]}
        nuevos = {}
        for intento in range(5):
            try:
                # la API cachea por dirección: cada intento pide desde un año distinto para no recibir el mismo hueco
                d = desde if intento == 0 else f"{int(desde[:4]) - intento}{desde[4:]}"
                nuevos.update({k: v for k, v in una(sid, clave, d).items() if k >= desde[:7]})
            except Exception as e:  # noqa: BLE001
                if intento == 4 and not nuevos:
                    raise
            pts = sorted({**junt, **nuevos}.items())
            if nuevos and huecos([list(p) for p in pts], paso) == 0:
                break
            time.sleep(2)
        if nuevos:
            out[clave] = [list(p) for p in sorted({**junt, **nuevos}.items())]
    return out


def main():
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    try:
        al = datetime.fromisoformat(prev.get("actualizado", "2000-01-01T00:00+00:00"))
        completo = all(huecos(v, 3 if k in TRIM else 1) == 0 for k, v in prev.items() if isinstance(v, list) and v and isinstance(v[0], list))
        if (datetime.now(timezone.utc) - al) < timedelta(hours=6) and not prev.get("errores") and completo:
            print("actividad.json reciente: no se renueva")
            return
    except ValueError:
        pass
    data, errores, hoy = dict(prev), [], date.today()
    for nombre, (series, desde, meses) in TANDAS.items():
        try:
            res = tanda(series, desde, prev)
            if not res:
                raise ValueError("sin datos")
            lim = (hoy - timedelta(days=31 * meses)).isoformat()[:7]
            for k, pts in res.items():
                if pts[-1][0] < lim:
                    errores.append(f"{k}: atrasada (último {pts[-1][0]}), se saca")
                    data.pop(k, None)
                else:
                    data[k] = pts
                    h = huecos(pts, 3 if k in TRIM else 1)
                    if h:
                        errores.append(f"{k}: faltan {h} meses (la API los devolvió vacíos; se completa en la próxima vuelta)")
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
