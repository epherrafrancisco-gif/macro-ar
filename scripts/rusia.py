"""Arma rusia.json para la sección Rusia de Pulso Macro (BIS y Banco Mundial; ver scripts/pais_bis.py)."""
from pathlib import Path

from pais_bis import armar

if __name__ == "__main__":
    armar(Path(__file__).resolve().parent.parent / "rusia.json", "RU", "RUB", None, "RUS")
