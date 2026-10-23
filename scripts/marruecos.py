"""Arma marruecos.json para la sección Marruecos de Pulso Macro (BIS, OCDE y Banco Mundial; ver scripts/pais_bis.py).
El BIS publica la tasa y el dirham de Marruecos con más atraso: se aceptan hasta 3 meses."""
from datetime import date, timedelta
from pathlib import Path

from pais_bis import armar, bis, solo_cambios

if __name__ == "__main__":
    hoy = date.today()
    armar(Path(__file__).resolve().parent.parent / "marruecos.json", "MA", "MAD", None, "MAR",
          extra={"tasa": (lambda: solo_cambios(bis("WS_CBPOL", "D.MA", f"{hoy.year - 8}-01-01")), 3),
                 "usd": (lambda: bis("WS_XRU", "D.MA.MAD.A", (hoy - timedelta(days=760)).isoformat()), 3)})
