"""Arma tailandia.json para la sección Tailandia de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py)."""
from pathlib import Path

from pais_bis import armar

if __name__ == "__main__":
    armar(Path(__file__).resolve().parent.parent / "tailandia.json", "TH", "THB", "THA", "THA")
