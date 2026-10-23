"""Arma singapur.json para la sección Singapur de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py).
Singapur no tiene tasa de política: la MAS maneja el dólar de Singapur dentro de una banda (no hay "tasa" en el BIS)."""
from datetime import date, timedelta
from pathlib import Path

from pais_bis import armar, bis, solo_cambios

if __name__ == "__main__":
    hoy = date.today()
    armar(Path(__file__).resolve().parent.parent / "singapur.json", "SG", "SGD", None, "SGP")
