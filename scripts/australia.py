"""Arma australia.json para la sección Australia de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py).
El BIS da dólares australianos por dólar estadounidense (al revés de como se cotiza en Australia)."""
from pathlib import Path

from pais_bis import armar

if __name__ == "__main__":
    armar(Path(__file__).resolve().parent.parent / "australia.json", "AU", "AUD", "AUS", "AUS")
