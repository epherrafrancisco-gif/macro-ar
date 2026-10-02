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
  Cinco pestañas: **Dólares** (`#dolares`), **Macro** (`#macro`), **Dinero** (`#dinero`),
  **Fiscal** (`#fiscal`), **Mercado** (`#mercado`), **Noticias** (`#noticias`), **Calculadoras** (`#calculadoras`) y **Sobre Macro AR** (`#sobre`), en ese orden, selector de rango 1M/3M/6M/1A/Todo (los gráficos mensuales
  no lo usan). Funciones de gráfico: `lineChart`, `barChart`, `dailyBars`. Tema claro y oscuro con tokens CSS en `:root`.
  Fuentes: Instrument Sans + JetBrains Mono (Google Fonts).
  Paleta de series (claro/oscuro): s1 azul #2a78d6/#3987e5, s2 naranja #eb6834/#d95926,
  s3 aqua #1baf7a/#199e70, s4 amarillo #eda100/#c98500, s5 magenta #e87ba4/#d55181.
  Colores por entidad: Oficial s1, MEP s2, CCL s3, Blue s4, Mayorista s5.
- `data.json`: `{"actualizado": "YYYY-MM-DD", "diario": [...], "mensual": [...], "trimestral": [...]}`.
  - Diario (una fila por día hábil, todos los campos opcionales): `fecha`,
    `oficial {c,v}`, `blue {c,v}`, `mep {v}`, `ccl {v}`, `mayorista {v}`,
    `cripto {c,v}`, `tarjeta {c,v}`, `riesgo` (pb), `reservas` (MUSD),
    `base` (millones $), `badlar`, `tamar`, `pf` (% TNA), `depusd` (MUSD),
    `compras` (BCRA id 78, MUSD/día; negativo = vendió) y `bopreal` (id 158, MUSD);
    estas dos se piden siempre desde el 1/1. `merval` (S&P Merval, puntos, Ámbito
    `indice/.merv`, columna Último; también desde el 1/1).
  - Mensual: `mes` (YYYY-MM), `infl`, `inflYoY`, `expect` (REM 12m); desde 2023-01:
    `base`, `m2`, `m2t`, `cer` (promedio del mes; millones $ / índice), `leliq`, `pases`,
    `lefi` (fin de mes, millones $), `prim`, `fin` (resultado fiscal SPN, millones $),
    `expo`, `impo`, `saldo` (MUSD).
  - Trimestral: `trim` (YYYY-MM del 1er mes), `pib` (PBI corriente, millones $, valor
    ANUALIZADO del trimestre: el promedio de los 4 trimestres = PBI del año).
    En la página, meses sin trimestre publicado: PBI estimado con la suba del CER.
  - Historico (`historico`, mensual desde 2017-01, para "Dólar a precios de hoy"): `mes`,
    `ofi`, `blue`, `mep`, `ccl` (Ámbito, promedio de la venta), `may` (BCRA id 5), `cer`
    (BCRA id 30, promedio) y `cpi` (CPI-U de EE.UU. sin desestacionalizar: intenta FRED
    `fredgraph.csv?id=CPIAUCNS` y, si falla, la API v1 del BLS por POST, serie CUUR0000SA0;
    desde Actions FRED da timeout y anda el BLS). Primera corrida baja todo por tramos
    anuales; después solo los años con huecos + desde el mes anterior (`--historia` fuerza
    todo). Si un año falla en Ámbito, baja mes por mes y, si falla el mes, día por día.
    Arranca en 2017 porque antes el IPC (y el CER) estaba manipulado. El MEP de Ámbito
    (`dolarrava/mep`) empieza recién en 03/2020; el CCL sí tiene 2017. Ámbito devuelve 500
    para el 13/08/2025 de MEP y CCL (día roto de la fuente, queda sin dato).
  - Historia desde 27/03/2026 (diario; `compras` desde 01/2026) y 08/2024 (mensual).
- `scripts/update.py`: trae datos y mezcla en `data.json` (solo librería estándar).
  Revisa los últimos N días (default 10). Nunca inventa datos: si una fuente falla,
  lo registra y deja el campo como estaba.
- `.github/workflows/actualizar-datos.yml`: corre `update.py` L a V a las
  10:15, 11:30 y 18:47 ART (13:15, 14:30 y 21:47 UTC) y a mano (`workflow_dispatch`), y
  commitea `data.json` y `estado.json` si cambió data.json. **Funciona** (primera corrida OK el 02/10/2026).
  `estado.json` guarda las fuentes OK y con error de la última corrida que cambió datos:
  mirarlo para diagnosticar (los logs de Actions no se pueden bajar desde el entorno de Claude).
  Claude puede lanzar el workflow solo: `gh workflow run actualizar-datos.yml -R
  epherrafrancisco-gif/macro-ar --ref main` y esperar con `gh run watch ID --exit-status`.
- `preview.png`: imagen para la vista previa de LinkedIn (og:image, con `?v=N` para
  romper la caché: subir N cada vez que cambie). Se genera con `scripts/preview.html`
  (lee data.json, sin cifras ni fechas para que no envejezca) y captura de 1200x630 con
  Playwright (`executablePath:'/opt/pw-browsers/chromium'`; las fuentes de Google no
  cargan en el entorno de Claude: usar @fontsource de npm con `page.route`).

## Fuentes (todas verificadas, aceptan consultas desde GitHub Actions)
- **Ámbito** `https://mercados.ambito.com//<ruta>/historico-general/DESDE/HASTA`
  → JSON `[["Fecha","Compra","Venta"],["30/09/2026","1540,00","1560,00"],...]`
  (fechas DD/MM/YYYY o DD-MM-YYYY, coma decimal, más reciente primero). OJO: el rango
  EXCLUYE el día HASTA (se pide hasta el día siguiente; corregido el 02/10/2026).
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
- **datos.gob.ar** (en uso): `452.3_RESULTADO_RIO_0_M_18_54` primario, `452.3_RESULTADO_ERO_0_M_20_25`
  financiero, `74.3_IET_0_M_16` expo, `74.3_IIT_0_M_25` impo, `74.3_ISC_0_M_19` saldo,
  `166.2_PPIB_0_0_3` PBI corriente trimestral. BCRA ids nuevos en uso: 109, 197, 30, 155
  (LELIQ), 152, 196, 158. La API del BCRA acepta `limit=3000`.
- Deuda del Tesoro en pesos (LECAP/BONCAP): NO hay serie pública gratuita por API
  (solo el boletín mensual de Finanzas en Excel). Pendiente, ver con Francisco.
- Para buscar más: **API de series de datos.gob.ar** (`https://apis.datos.gob.ar/series/api/series/?ids=...`)
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
balanza cambiaria, liquidación del agro (CIARA-CEC) y gráfico histórico por acción
(descartados el 02/10/2026). Todo lo demás va, con los agregados de cada punto.

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

### Bloque 2 (HECHO y verificado el 02/10/2026 con datos reales, salvo la deuda
LECAP/BONCAP, que no tiene fuente gratuita por API; datos.gob.ar responde desde Actions)
6. **Agregados en términos reales**: base, M2 (y M2 transaccional privado)
   deflactados con CER (o IPC), y en % del PBI, para medir la remonetización.
7. **Resultado fiscal mensual** (datos.gob.ar): primario y financiero en barras,
   acumulado del año y en % del PBI.
8. **Balanza comercial** (INDEC vía datos.gob.ar): exportaciones, importaciones, saldo.
9. **Pasivos/deuda en pesos**: stock de BOPREAL (id 158), deuda del Tesoro en
   pesos (LECAP/BONCAP), y gráfico histórico de la migración LELIQ → pases →
   LEFI → LECAP. LEFI y pases están en 0 desde 07/2025: no mostrarlos como si
   fueran actuales.

### Bloque 3 (HECHO el 02/10/2026; agro e histórico por acción descartados)
- Paso (a) fuentes, HECHO: Merval histórico = Ámbito; precios del día de acciones y
  bonos = data912 (`https://data912.com/live/arg_stocks`, `/live/arg_bonds`; campos
  symbol, c, pct_change, v, px_bid, px_ask; sin timestamp; 120 req/min; su historia
  de bonos está cortada en 2023, no usarla). CORS OK: verificado en el sitio publicado el 02/10.
- Paso (b) HECHO: pestaña Mercado con Merval en $ y en US$ CCL, riesgo país y tabla de
  AL30/GD30 (precio D y $, TIR y paridad calculadas en la página con el cronograma
  2030; se consulta data912 cada 10 min desde el navegador).
- Paso (c) HECHO en parte: mapa de calor de 21 acciones líderes (lista `LIDERES` en
  index.html), resumen suben/bajan y detalle al tocar (puntas, monto, operaciones).
  SIN gráfico histórico por acción: no hay fuente gratuita (la historia de data912 está
  cortada). DESCARTADO: liquidación del agro (CIARA-CEC): no hay API; publican un Excel
  mensual en ciaracec.com.ar/ciara/estadisticas/ con nombre que cambia (ej.
  `.../descargar/01102026_30092026liquidacion-de-divisas-ciara-cec-base-oficial.xlsx`).
  Opciones: leer ese Excel desde el workflow (sin librerías: zipfile + xml) o cargar
  el dato a mano una vez por mes. Septiembre 2026: US$ 3.228 M (comunicado del 01/10).
10. **Pestaña Mercado**: S&P Merval en pesos y en dólares CCL (histórico),
    tablero de las empresas del índice (precio, variación del día, mapa de calor,
    gráfico al tocar), bonos AL30/GD30 con rendimiento y riesgo país. Datos
    gratuitos con 15-20 min de demora (BYMA demorado u otra fuente; verificar
    disponibilidad), actualizados cada 10-15 min. Aclarar en la página que son
    demorados. Ojo: si el sitio pasa a generar ingresos, redistribuir precios de
    BYMA puede requerir licencia.
11. **Liquidación del agro (CIARA-CEC)**: mensual (no hay dato diario público),
    barras con comparación interanual. Como proxy semanal, las compras del BCRA.

### Bloque 4 (menú propuesto el 02/10/2026; hechos A, B, C, D y E)
Al arrancar una sesión nueva, mostrale lo que falta de este menú en criollo y que elija.
- A. HECHO (02/10/2026): nueva `preview.png` (oscura, 5 pestañas con mini gráficos) y
  meta description/og actualizadas. Para que LinkedIn la tome: Post Inspector.
- B. HECHO (02/10/2026): tarjeta "Dólar a precios de hoy" en Dólares (`renderUsdReal`):
  promedio mensual × CER hoy/CER mes × CPI mes/CPI hoy; último punto = cotización de hoy;
  tabla con hoy, promedio desde 2017, desvío, percentil, mínimo y máximo.
- C. HECHO (02/10/2026): barra "Datos de esta pestaña en CSV" al final de cada pestaña
  (objeto `CSV` en index.html: una función por archivo). Formato Excel en español: `;`,
  coma decimal, BOM UTF-8. Nombre `macro-ar_<clave>_<fecha>.csv`.
- D. HECHO (02/10/2026): tarjeta "Próximas publicaciones" en Macro (`renderCal`), con
  cuenta regresiva a la próxima y lista de las 7 siguientes. Datos en `calendario.json`
  (`eventos`: f, org, n, p, h, est; `vigente_hasta`). Cargado: INDEC 2º semestre 2026
  (calendario_2sem2026.pdf, publica a las 16 h) + REM estimado (4º día hábil; el BCRA no
  publica calendario: ago-2026 salió el 6/8 y sep el 4/9). PENDIENTE cada diciembre/junio:
  cargar el calendario del semestre siguiente
  (indec.gob.ar/ftp/cuadros/publicaciones/calendario_1sem2027.pdf) y actualizar
  `vigente_hasta`; si no, la tarjeta muestra "No hay fechas cargadas".
- E. HECHO (02/10/2026): imagen diaria 1080x1350 para @macroar_diario. Plantilla
  `scripts/diario.html` (lee data.json; expone `window.TEXTO` con el texto del posteo),
  generador `scripts/diario.mjs` (servidor http propio + playwright-core + Chrome del runner,
  `CHROME_PATH` opcional). El workflow la genera cuando cambia data.json (paso con
  `continue-on-error`) y commitea `diario/hoy.png` y `diario/texto.txt`. Página para
  bajarla y copiar el texto: `/diario/` (link en el pie). Antes de las 17 h dice
  "parcial, HH:MM h"; la de las 18:47 es la de cierre. Probar local:
  `ln -s <scratch>/node_modules node_modules && node scripts/diario.mjs` (sin Google Fonts).
- F. **Dominio propio `macroar.com.ar`**: POSTERGADO AL FINAL por decisión de Francisco
  (02/10/2026): el sitio está "en mantenimiento", nadie usa el link todavía, y el trámite
  en NIC Argentina pide clave fiscal de ARCA que no recuerda. Hacerlo después de G y H.
  Orden obligatorio: comprar → DNS (NIC.ar no aloja DNS: delegar a Cloudflare gratis, A a
  las IPs de GitHub Pages, CNAME www, nube gris) → recién ahí CNAME en el repo + Settings
  → Pages; si se agrega el CNAME antes, el link github.io redirige a un dominio muerto.
  Al pasar: cambiar las menciones de la URL en index.html (og:url), scripts/preview.html,
  scripts/diario.html (pie y texto del posteo) y README.
- G y H DESCARTADOS por Francisco (02/10/2026): deuda del Tesoro en pesos (LECAP/BONCAP),
  newsletter e inflación semanal de alimentos propia. No volver a proponerlos.

### Bloque 5 (lista de Francisco del 02/10/2026)
- HECHO: íconos (i) con glosario en criollo. Objeto `GLOS` (clave → [título, texto]) y
  `GLOS_REGLAS` ([regex sobre el texto, clave, dónde: q = tarjetas de dólar, g = h2/h3/
  etiquetas de KPI y stats, th = encabezados]). `decorar()` los agrega solo después de cada
  dibujo (MutationObserver sobre .wrap). Para sumar un término: agregar a GLOS y una regla.
  Popover único `#tipbox`: hover con mouse, tap en celular, foco con teclado, Esc cierra.
- HECHO: en cada gráfico (`.card .chart[id]`) tres íconos: compartir, PNG y CSV
  (`herramientas()`). Cada función de gráfico guarda `el._exp = {fn, a, o}`; el PNG
  redibuja el gráfico a 760 px, copia los colores calculados y arma un canvas 2x con
  título, subtítulo, leyenda, marca de agua "Macro AR", logo, URL y @macroar_diario.
  Compartir: en celular usa navigator.share con el archivo (no se pudo probar acá:
  Chromium de Linux no lo soporta); en compu copia la imagen al portapapeles y abre
  twitter.com/intent/tweet con texto y link (si no puede copiar, la descarga).
- HECHO: pestaña **Calculadoras** (`#calculadoras`, `renderCalc`), con selector y la última
  elegida en localStorage: (1) ¿Plazo fijo o dólar? → dólar de equilibrio = precio × (1 +
  TNA × días/365), TNA precargada con `pf` del BCRA, precio en vivo (editable), tasa real
  contra REM y cuánto se movió ese dólar en los últimos N días; (2) Inflación → monto × CER
  hoy / CER del mes (historico desde 2017) y comparación con haber comprado blue;
  (3) Sueldo en dólares → sueldo ÷ cada dólar hoy y, opcional, comparación con un sueldo
  anterior (poder de compra por CER y en dólares). Francisco eligió 1, 2 y 5 de las ideas
  (descartadas por ahora: tarjeta vs MEP y calculadora de bonos). Números con `parseAR`.
- HECHO: ranking "¿Qué le ganó a la inflación en <año>?" arriba de Mercado (`renderRanking`,
  barras horizontales `hBars`, con compartir/PNG/CSV). Desde el último cierre del año
  anterior: dólares oficial/MEP/CCL/blue, S&P Merval y plazo fijo 30 días renovado con la
  TNA vigente. Inflación: IPC publicado + REM para lo que falta ("Hasta hoy") o solo IPC
  ("Hasta <último mes con IPC>"). Para esto update.py ahora pide Ámbito (todos), mayorista
  y plazo fijo desde el 1/12 del año anterior (`AMBITO_LARGO`, `BCRA_LARGO`).
- HECHO: chequeo automático diario del sitio publicado (`.github/workflows/chequeo-sitio.yml`
  + `scripts/chequeo.mjs`, L a V 19:43 ART). Revisa atraso de datos, estado.json,
  calendario por vencer, errores de JS y gráficos vacíos por pestaña, DolarApi, data912 e
  imagen del día. Si hay un problema grave abre el issue "Chequeo del sitio: hay problemas"
  (le llega por mail a Francisco) y lo cierra solo cuando vuelve a andar; los avisos
  menores quedan en el resumen de la corrida. A mano: Run workflow, opcional `url`.
  Probado el 02/10 (issue #1 abierto con URL rota y cerrado solo). gh: usar REST
  (`gh api repos/...`), GraphQL está bloqueado en el entorno de Claude.
- HECHO: contador de visitas privado con GoatCounter, cuenta `macroar` de Francisco (panel en
  macroar.goatcounter.com, solo con su usuario). Script en el head de index.html con
  `no_onload`: la función `gc()` cuenta cada pestaña como `/macro-ar/#pestaña` y eventos:
  `calculadora-<pf|inf|sue>`, `glosario-<clave>` (una vez por visita), `compartir|png|csv-<id
  del gráfico>`, `csv-pestaña-<clave>`. No cuenta navegadores automatizados
  (navigator.webdriver, o sea el chequeo diario). La página /diario/ cuenta sola.
  Para no contar sus propias visitas: abrir el sitio con `#toggle-goatcounter` en cada
  navegador/celular.
- DESCARTADOS (02/10/2026): "el día en 30 segundos", dólar contra la banda cambiaria y
  curva de tasas en pesos. No volver a proponerlos.
- HECHO: pestaña **Noticias** (`#noticias`, `renderNoticias`). `scripts/noticias.py` junta
  titulares (solo título, link, medio, hora y temas por palabras clave) de los RSS de
  economía de Ámbito, Infobae, La Nación, iProfesional y Perfil (verificados 02/10/2026;
  El Cronista y Clarín no se pudieron leer) en `noticias.json`, últimas 48 h.
  Workflow `noticias.yml`: L a V cada hora de 6 a 22 ART, fines de semana cada 3 h.
  Filtros por tema y medio, marca "NUEVA" desde la última visita (localStorage), evento
  `noticia-<medio>` en GoatCounter al tocar un titular. El chequeo revisa que esté al día.
- HECHO: última pestaña **Sobre Macro AR** (`#sobre`, sección `vS`, contenido estático en el
  HTML): presentación en primera persona (estudiante de Economía Empresarial en UTDT, Técnico
  en Administración de las Organizaciones, invierte desde los 17; NO está en el Finance
  Club; NO mencionar el negocio familiar ni IG/X por ahora), por qué hizo Macro AR, para
  quién es, "lo que me mueve", cómo funciona, fuentes y aclaraciones. Contacto: LinkedIn
  www.linkedin.com/in/francisco-epherra-8509513b4 y epherrafrancisco@gmail.com (eventos
  `contacto-linkedin|mail`). Foto: `foto.jpg` (480x480, la foto original sin retocar; Francisco no quiso el fondo azul). Título: solo "Francisco Epherra".
- El dominio (F) queda para después.

### Próxima sesión: jueves 08/10/2026, dominio `macroar.com.ar`
El sitio está TERMINADO para Francisco (02/10/2026) y NO se lanza hasta tener el dominio.
Él trae la clave fiscal de ARCA (se blanquea desde el home banking). Pasos, guiándolo uno
por uno: (1) verificar en nic.ar que `macroar.com.ar` esté libre y comprarlo (alta $8.500,
renovación anual $8.500 según nic.ar al 02/10/2026; que active renovación o se agende el
vencimiento); (2) cuenta gratis en Cloudflare, agregar el dominio, copiar los 2 nameservers
y cargarlos en NIC.ar → Delegaciones; (3) en Cloudflare: A @ → 185.199.108.153,
185.199.109.153, 185.199.110.153, 185.199.111.153 y CNAME www → epherrafrancisco-gif.github.io,
todos con nube GRIS (DNS only); verificar las IPs en la doc de GitHub Pages ese día;
(4) recién con el DNS respondiendo: archivo `CNAME` en el repo + Settings → Pages →
Custom domain + Enforce HTTPS; (5) cambiar las menciones de la URL (index.html og:url y
SITE, scripts/preview.html, scripts/diario.html, diario/, chequeo.mjs, README) y subir
`?v=` de preview.png; (6) verificar que el link viejo redirija; (7) recién ahí lanzarlo.

## Otras cosas del proyecto
- El tablero viejo dentro de Claude (artifact) quedó congelado al 25/09/2026;
  ya no se usa. Las tareas programadas de Claude están desactivadas.
- El tracker del QQQ de Francisco es privado (artifact de Claude, no va a GitHub)
  y su tarea automática también está desactivada.
- Ideas futuras ya conversadas: dólar ajustado por inflación ("a precios de hoy"),
  calendario de publicaciones (INDEC/BCRA), inflación semanal de alimentos propia,
  datos descargables, newsletter, gráfico diario para X/IG.
