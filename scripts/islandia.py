"""Arma islandia.json para la sección Islandia de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py)."""
from pathlib import Path

from pais_bis import armar

if __name__ == "__main__":
    armar(Path(__file__).resolve().parent.parent / "islandia.json", "IS", "ISK", "ISL", "ISL")
