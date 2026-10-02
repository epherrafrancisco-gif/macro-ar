# Pulso Macro

Tablero diario de la economía argentina: dólares y brechas, riesgo país, reservas, compras del BCRA, inflación, tasas, dinero en términos reales, resultado fiscal, comercio exterior, Merval y bonos, el dólar a precios de hoy, noticias económicas y calculadoras.

**Ver el tablero:** https://epherrafrancisco-gif.github.io/macro-ar/

Se actualiza solo cada día hábil después del cierre. Las tarjetas de dólares se refrescan en vivo cada minuto. Fuentes: BCRA, INDEC y Hacienda (datos.gob.ar), Ámbito, DolarApi, data912 y FRED (inflación de EE.UU.).

- `index.html`: la página.
- `data.json`: los datos (una fila por día hábil y una por mes).
- `calendario.json`: próximas publicaciones del INDEC y el BCRA (se carga a mano cada semestre).
- `scripts/update.py`: el programa que trae los datos nuevos.
- `scripts/diario.html` y `scripts/diario.mjs`: la imagen del día para redes (`diario/hoy.png`, se ve en `/diario/`).
- `scripts/preview.html`: la plantilla de `preview.png`, la imagen que aparece al compartir el link.
- `.github/workflows/actualizar-datos.yml`: lo corre solo con GitHub Actions, de lunes a viernes a las 10:15, 11:30 y 18:47 (hora argentina). También se puede correr a mano desde la pestaña Actions.

Datos con fines informativos, no constituyen recomendación de inversión.
