"""Arma grecia.json para la sección Grecia de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py).
Grecia no tiene tasa propia: usa la del Banco Central Europeo (BIS, zona euro "XM"). Mismo armado que España."""
from datetime import date
from pathlib import Path

from pais_bis import armar, bis, solo_cambios

if __name__ == "__main__":
    hoy = date.today()
    armar(Path(__file__).resolve().parent.parent / "grecia.json", "GR", "EUR", "GRC", "GRC",
          extra={"tasa": (lambda: solo_cambios(bis("WS_CBPOL", "D.XM", f"{hoy.year - 8}-01-01")), 1)})
