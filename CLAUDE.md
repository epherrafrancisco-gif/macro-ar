# Macro AR: notas del proyecto para Claude

Leé este archivo completo antes de tocar nada. Resume todo lo decidido con Francisco
hasta el 02/10/2026.

## Quién y cómo
- Dueño: **Francisco Epherra**, estudiante de Economía Empresarial (UTDT), inversor.
- Hablale en español rioplatense, de "vos", conciso y directo, sin relleno ni
  preguntas retóricas. Explicale en criollo; no es programador.
- Su uso de Claude es limitado: trabajá por bloques, verificá cada bloque antes
  de seguir y no repitas trabajo.

## Qué es
Tablero público y gratuito de la macro argentina:
**https://epherrafrancisco-gif.github.io/macro-ar/**
(GitHub Pages desde la rama `main`, carpeta raíz). Publicado en LinkedIn.
Plan futuro: dominio propio `macroar.com.ar` (no tocar el nombre del usuario ni
del repo: rompería la redirección del link viejo). Redes: @macroar_diario (IG y X).

## Archivos
- `index.html`: toda la página (HTML + CSS + JS en un solo archivo, sin librerías).
  Lee `data.json` con `fetch` y dibuja gráficos SVG propios (`lineChart`, `barChart`).
  Dos pestañas: **Dólares** (`#dolares`) y **Macro** (`#macro`), selector de rango
  1M/3M/6M/1A/Todo. Tema claro y oscuro con tokens CSS en `:root`.
  Fuentes: Instrument Sans + JetBrains Mono (Google Fonts).
  Paleta de series (claro/oscuro): s1 azul #2a78d6/#3987e5, s2 naranja #eb6834/#d95926,
  s3 aqua #1baf7a/#199e70, s4 amarillo #eda100/#c98500, s5 magenta #e87ba4/#d55181.
  Colores por entidad: Oficial s1, MEP s2, CCL s3, Blue s4, Mayorista s5.
- `data.json`: `{"actualizado": "YYYY-MM-DD", "diario": [...], "mensual": [...]}`.
  - Diario (una fila por día hábil, todos los campos opcionales): `fecha`,
    `oficial {c,v}`, `blue {c,v}`, `mep {v}`, `ccl {v}`, `mayorista {v}`,
    `cripto {c,v}`, `tarjeta {c,v}`, `riesgo` (pb), `reservas` (MUSD),
    `base` (millones $), `badlar`, `tamar`, `pf` (% TNA), `depusd` (MUSD),
    `compras` (BCRA id 78, MUSD/día; negativo = vendió; se pide siempre desde el 1/1).
  - Mensual: `mes` (YYYY-MM), `infl`, `inflYoY`, `expect` (REM 12m).
  - Historia desde 27/03/2026 (diario; `compras` desde 01/2026) y 08/2024 (mensual).
- `scripts/update.py`: trae datos y mezcla en `data.json` (solo librería estándar).
  Revisa los últimos N días (default 10). Nunca inventa datos: si una fuente falla,
  lo registra y deja el campo como estaba.
- `.github/workflows/actualizar-datos.yml`: corre `update.py` L a V a las
  10:15, 11:30 y 18:47 ART (13:15, 14:30 y 21:47 UTC) y a mano (`workflow_dispatch`), y
  commitea `data.json` si cambió. **Funciona** (primera corrida OK el 02/10/2026).
- `preview.png`: imagen para la vista previa de LinkedIn (og:image).

## Fuentes (todas verificadas, aceptan consultas desde GitHub Actions)
- **Ámbito** `https://mercados.ambito.com//<ruta>/historico-general/DESDE/HASTA`
  → JSON `[["Fecha","Compra","Venta"],["30/09/2026","1540,00","1560,00"],...]`
  (fechas DD/MM/YYYY o DD-MM-YYYY, coma decimal, más reciente primero).
  Rutas: `dolar/informal` (blue), `dolar/oficial`, `dolarrava/mep`, `dolarrava/cl`,
  `riesgopais`. En feriados repite MEP/CCL: se filtran con los días de oficial/mayorista.
- **BCRA** `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{id}?desde=&hasta=&limit=1000`
  → `{"results":[{"idVariable":1,"detalle":[{"fecha":"2026-09-29","valor":47482.0}]}]}`.
  La v3.0 ya no existe (410). Listado de variables: `.../v4.0/monetarias`.
  IDs en uso: 1 reservas, 5 mayorista, 15 base, 7 BADLAR, 44 TAMAR, 12 PF 30d,
  108 depósitos privados USD, 27 IPC mensual, 28 IPC interanual, 29 REM 12m.
  IDs útiles para lo que viene: 78 variación de reservas por compra de divisas
  (MUSD, = compras/ventas del BCRA en el MULC), 158 LEBAC/LEDIV/BOPREAL USD,
  109 M2, 197 M2 transaccional privado, 25 var. i.a. M2 privado, 30 CER, 31 UVA,
  196 LEFI (en 0 desde 07/2025), 152 pases pasivos (en 0).
- **DolarApi** `https://dolarapi.com/v1/dolares` (cripto, tarjeta; también oficial,
  blue, bolsa=MEP, contadoconliqui=CCL, mayorista con `fechaActualizacion`).
- Para lo nuevo: **API de series de datos.gob.ar** (`https://apis.datos.gob.ar/series/api/series/?ids=...`)
  para resultado fiscal, balanza comercial (INDEC) y PBI. Buscar los IDs en
  `https://apis.datos.gob.ar/series/api/search/?q=...`.

## Entorno de trabajo de Claude (importante)
- La terminal del entorno de Claude NO tiene internet salvo GitHub: no se puede
  probar `update.py` contra las fuentes desde acá. Usá WebFetch para mirar el
  formato de una fuente y probá el script con respuestas simuladas (mock de
  `get_json`). La prueba real es correr el workflow.
- Para correr el workflow, Francisco entra a
  `github.com/epherrafrancisco-gif/macro-ar/actions/workflows/actualizar-datos.yml`
  → **Run workflow**. Guialo paso a paso (no usa la app de escritorio de GitHub;
  si le aparece "Authorize your device", es esa app: que la cierre).
- Push a `main` funciona (app de Claude instalada en el repo).
- Commits: terminar con las líneas de atribución que indique el sistema.

## Hoja de ruta aprobada (02/10/2026)
Descartado por Francisco: calendario de vencimientos de deuda, "BSTEP",
balanza cambiaria. Todo lo demás va, con los agregados de cada punto.

### Bloque 1 (HECHO y verificado el 02/10/2026: `compras` cargó 180 días desde 02/01;
DolarApi responde desde el navegador, CORS OK)
1. **Firma**: "Diseñado y operado por Francisco Epherra" junto al nombre del sitio,
   en chico, debajo del título.
2. **Canje histórico**: gráfico de la prima CCL/MEP − 1 en %, con su promedio
   como referencia (banda o línea) para ver cuándo se dispara. Ya hay datos.
3. **Compras/ventas del BCRA en el MULC** (BCRA id 78, MUSD/día): barras diarias
   verde/rojo, acumulado del mes y del año, contador grande "Compras en 2026".
   Agregar al `update.py`, cargar historia (al menos desde 27/03/2026 o el año).
4. **Dólar en vivo**: la página consulta DolarApi desde el navegador **cada 60 s**
   (no menos: la fuente no cambia tan rápido y es gratis) y actualiza las tarjetas
   sin recargar; cartel "En vivo · hace N s" con punto verde y parpadeo verde/rojo
   al cambiar. Verificar que DolarApi permita CORS. Los gráficos siguen usando el
   cierre de `data.json`.
5. **Corrida extra a las 11:30 ART** (14:30 UTC), media hora después de la apertura.
   Explicarle que los datos del BCRA no cambian intradía; lo que cambia son dólares
   y riesgo país. GitHub puede atrasar el cron 5-30 min.

### Bloque 2 (el próximo)
6. **Agregados en términos reales**: base, M2 (y M2 transaccional privado)
   deflactados con CER (o IPC), y en % del PBI, para medir la remonetización.
7. **Resultado fiscal mensual** (datos.gob.ar): primario y financiero en barras,
   acumulado del año y en % del PBI.
8. **Balanza comercial** (INDEC vía datos.gob.ar): exportaciones, importaciones, saldo.
9. **Pasivos/deuda en pesos**: stock de BOPREAL (id 158), deuda del Tesoro en
   pesos (LECAP/BONCAP), y gráfico histórico de la migración LELIQ → pases →
   LEFI → LECAP. LEFI y pases están en 0 desde 07/2025: no mostrarlos como si
   fueran actuales.

### Bloque 3
10. **Pestaña Mercado**: S&P Merval en pesos y en dólares CCL (histórico),
    tablero de las empresas del índice (precio, variación del día, mapa de calor,
    gráfico al tocar), bonos AL30/GD30 con rendimiento y riesgo país. Datos
    gratuitos con 15-20 min de demora (BYMA demorado u otra fuente; verificar
    disponibilidad), actualizados cada 10-15 min. Aclarar en la página que son
    demorados. Ojo: si el sitio pasa a generar ingresos, redistribuir precios de
    BYMA puede requerir licencia.
11. **Liquidación del agro (CIARA-CEC)**: mensual (no hay dato diario público),
    barras con comparación interanual. Como proxy semanal, las compras del BCRA.

## Otras cosas del proyecto
- El tablero viejo dentro de Claude (artifact) quedó congelado al 25/09/2026;
  ya no se usa. Las tareas programadas de Claude están desactivadas.
- El tracker del QQQ de Francisco es privado (artifact de Claude, no va a GitHub)
  y su tarea automática también está desactivada.
- Ideas futuras ya conversadas: dólar ajustado por inflación ("a precios de hoy"),
  calendario de publicaciones (INDEC/BCRA), inflación semanal de alimentos propia,
  datos descargables, newsletter, gráfico diario para X/IG.
