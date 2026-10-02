# Macro AR

Tablero diario de la economía argentina: dólares y brechas, riesgo país, reservas, compras del BCRA, inflación, tasas, dinero en términos reales, resultado fiscal y comercio exterior.

**Ver el tablero:** https://epherrafrancisco-gif.github.io/macro-ar/

Se actualiza solo cada día hábil después del cierre. Las tarjetas de dólares se refrescan en vivo cada minuto. Fuentes: BCRA, INDEC y Hacienda (datos.gob.ar), Ámbito y DolarApi.

- `index.html`: la página.
- `data.json`: los datos (una fila por día hábil y una por mes).
- `scripts/update.py`: el programa que trae los datos nuevos.
- `.github/workflows/actualizar-datos.yml`: lo corre solo con GitHub Actions, de lunes a viernes a las 10:15, 11:30 y 18:47 (hora argentina). También se puede correr a mano desde la pestaña Actions.

Datos con fines informativos, no constituyen recomendación de inversión.
