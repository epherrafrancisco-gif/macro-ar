"""Arma espana.json para la sección España de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py).
España no tiene tasa propia: usa la del Banco Central Europeo (BIS, zona euro "XM")."""
from datetime import date, timedelta
from pathlib import Path

from pais_bis import armar, bis, solo_cambios

if __name__ == "__main__":
    hoy = date.today()
    armar(Path(__file__).resolve().parent.parent / "espana.json", "ES", "EUR", "ESP", "ESP",
          extra={"tasa": (lambda: solo_cambios(bis("WS_CBPOL", "D.XM", f"{hoy.year - 8}-01-01")), 1)})
