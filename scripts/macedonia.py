"""Arma macedonia.json para la sección Macedonia del Norte de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py)."""
from datetime import date, timedelta
from pathlib import Path

from pais_bis import armar, bis, solo_cambios

if __name__ == "__main__":
    hoy = date.today()
    armar(Path(__file__).resolve().parent.parent / "macedonia.json", "MK", "MKD", None, "MKD")
