"""Arma arabia.json para la sección Arabia Saudita de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py).
El riyal está atado al dólar (3,75 desde 1986) y el banco central (SAMA) mueve la tasa cuando lo hace la Fed."""
from pathlib import Path

from pais_bis import armar

if __name__ == "__main__":
    armar(Path(__file__).resolve().parent.parent / "arabia.json", "SA", "SAR", "SAU", "SAU")
