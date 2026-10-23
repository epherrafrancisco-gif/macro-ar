"""Arma suecia.json para la sección Suecia de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py)."""
from pathlib import Path

from pais_bis import armar

if __name__ == "__main__":
    armar(Path(__file__).resolve().parent.parent / "suecia.json", "SE", "SEK", "SWE", "SWE")
