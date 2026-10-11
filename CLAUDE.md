# Pulso Macro: notas técnicas del proyecto

Leé este archivo antes de tocar nada. Este repositorio es PÚBLICO: acá van solo notas técnicas.
Nada de datos personales, trámites, claves, mails ni preferencias privadas del dueño.

## Cómo trabajar
- El dueño no es programador: hablale en español rioplatense, de "vos", conciso, en criollo.
  Cuando tenga que hacer algo él (GitHub, configuraciones), de a un paso por mensaje, explicando lo que esté en inglés.
- Trabajá por bloques y verificá cada bloque antes de seguir. Para cambios visuales grandes, primero una maqueta.
- Nunca mostrar datos viejos como si fueran actuales: si una fuente está atrasada, se saca o se aclara la fecha.
- Commits: terminar con las líneas de atribución que indique el sistema.

## Nombre, estética y URLs
- Sitio: **Pulso Macro** en **https://pulsomacro.com.ar/** (GitHub Pages, rama `main`, carpeta raíz, archivo `CNAME`;
  DNS en Cloudflare con nube gris; el link viejo epherrafrancisco-gif.github.io/macro-ar redirige solo).
  El repo sigue llamándose `macro-ar`: no renombrar (rompe la redirección). Nunca usar "Macro AR" en nada visible.
- Logo: `Pulso<span>Macro</span>` ("Macro" en mono y color de acento). Archivos descargados: `pulso-macro_<...>`.
- Siempre tema oscuro (`:root` con colores fijos y `color-scheme:dark`), también en /diario/.
- Fuentes: Instrument Sans + JetBrains Mono. Series: s1 azul #3987e5, s2 naranja #d95926, s3 aqua #199e70,
  s4 amarillo #c98500, s5 magenta #d55181. Oficial s1, MEP s2, CCL s3, Blue s4, Mayorista s5.
- Contador de visitas: GoatCounter (cuenta interna `macroar`), función `gc()` en index.html; no cuenta navegadores
  automatizados. Para no contar las visitas propias: abrir el sitio con `#toggle-goatcounter`.

## Estructura de la página (`index.html`, todo en un archivo, sin librerías salvo d3/topojson en Global)
- Arriba: tres cintas (`#tape` dólares/brecha/riesgo/Merval; `#tape2` mercados del mundo; `#tape3` reloj de mercados)
  y los 7 dólares (`#dolHoy`/`#quotes`, `renderQuotes()`): siempre en la portada y en todo Argentina (requisito no
  negociable); NO en Mundo, Estados Unidos ni Sobre Pulso Macro (pedido del dueño).
  Dólar en vivo: DolarApi desde el navegador cada 60 s.
- Sin hash: portada (`#vP`, `renderPortada()`): "¿Qué querés ver?" con dos puertas (Argentina / El mundo), tarjetas por
  sección (`SECC` + `ICO`: nombre claro, ícono y una línea), "Hoy en números" (`#pHoy`) y globo de puntos con resumen.
- Encabezado: selector `#modo` (Argentina | El mundo | Sobre Pulso Macro `#modoS`); el logo (`#brandH`) vuelve a la portada.
- Adentro: migas (`#crumb`), pestañas como píldoras (`#tabsNav a[data-g]`, en celular grilla de 2 columnas), recuadro
  `#here` con qué es cada sección, y selector de período `#segRange` (1M/3M/6M/1A/Todo; los mensuales no lo usan).
- Hashes (no cambiarlos): Argentina = `#dolares`, `#macro` ("Inflación y reservas"), `#dinero` ("Tasas y pesos"),
  `#fiscal` ("Cuentas del Estado"), `#mercado` ("Bolsa y bonos"), `#noticias`, `#calculadoras`;
  El mundo = `#global` (Mundo) y `#eeuu` (Estados Unidos; `setTab('eeuu')` pone `G.vista='usa'`); `#sobre`.
- Funciones de gráfico: `lineChart`, `barChart`, `dailyBars`, `hBars` (barras horizontales; opciones `vfmt`, `rh`,
  `ref`, filas con `hl` para resaltar). Cada gráfico guarda `el._exp` para compartir/PNG/CSV (`herramientas()`).
- Glosario (i): objetos `GLOS` y `GLOS_REGLAS`, `decorar()` los agrega solo. Popover `#tipbox`.
- CSV por pestaña: objeto `CSV` (`;`, coma decimal, BOM UTF-8).

### Argentina
- Dólares: cotizaciones, brechas, canje CCL/MEP con banda, "Dólar a precios de hoy" (`renderUsdReal`), últimos días.
- Macro: inflación, REM, reservas, compras del BCRA en el MULC, riesgo país, "Próximas publicaciones" (`renderCal`,
  datos en `calendario.json`; PENDIENTE cada diciembre/junio: cargar el calendario del INDEC del semestre siguiente
  y actualizar `vigente_hasta`).
- Dinero: base, M2, M2 transaccional en términos reales y % del PBI, tasas, pasivos (LELIQ → pases → LEFI → LECAP;
  LEFI y pases en 0 desde 07/2025: no mostrarlos como actuales), BOPREAL.
- Fiscal: resultado primario y financiero, acumulado y % del PBI, balanza comercial.
- Mercado: ranking "¿Qué le ganó a la inflación?", Merval en $ y US$ CCL, mapa de calor de 21 líderes (`LIDERES`,
  data912 desde el navegador cada 10 min), AL30/GD30 con TIR y paridad.
- Noticias: `noticias.json` (scripts/noticias.py, RSS de Ámbito, Infobae, La Nación, iProfesional y Perfil, 48 h).
- Calculadoras: plazo fijo vs dólar, inflación (CER), sueldo en dólares.
- Sobre Pulso Macro: contenido estático en el HTML (`vS`). No cambiar su texto sin que lo pida el dueño.

### Global › Mundo
- Dos globos: países (`gInit/gDraw`, capas inflación/crecimiento/tasa/desempleo, ficha vs Argentina; mapa plano si
  `innerWidth<560`) y "Mundo hoy" de puntos (`dgStart/dgDraw/dgDots/dgItems`; capas bolsas hoy, monedas hoy, monedas en
  el año, bonos a 10 años). d3 7.8.5 y topojson 3.0.2 de cdnjs, solo al abrir la pestaña. Mapa `world.json`.
- Reloj de mercados 24 h (`renderReloj`, `gEstado`, `gProx`, lista `GEX` sin feriados).
- `gMundoExtra`: ¿Dónde está Argentina? (`DPA`, países `DPA_P`), agenda de bancos centrales (`BCAL`, fechas de anuncio
  cargadas a mano hasta dic-2027; Banxico solo 2026: agregar 2027 cuando lo publique), bonos a 10 años vs EE.UU.
  (Argentina = riesgo país), cripto top 10, noticias del mundo.
- `gExtras`: bolsas, bancos centrales (BIS), commodities (9, con variación en el año y clic al gráfico), Argentinas en
  Wall Street, Líderes del mundo, gráficos 1M-2A (`GCH`), "¿Qué rindió más en el año?", monedas, termómetro (VIX, 10-2).

### Global › Estados Unidos (`renderUsa`, `usaExtra`)
- Mapa de desempleo por estado (sin animación decorativa), reloj de la deuda, cuenta regresiva a la Fed, 6 indicadores,
  Fed vs inflación, curva del Tesoro, empleos por mes, sectores, 7 magníficas, decisiones de la Fed.
- Semáforo de recesión (regla de Sahm, curva 10-2, VIX, pedidos de desempleo vs un año), inflación por rubro,
  próximos datos (`CAL_US`, fechas BLS/BEA a mano hasta 2027; PBI/PCE solo hasta dic-2026: cargar 2027 cuando salgan),
  mapa de 50 empresas por sector, mercado laboral, hipotecaria 30 años, próximos balances y PBI.

## Datos y robots (GitHub Actions)
- `data.json` (scripts/update.py, workflow `actualizar-datos.yml`, L a V 10:15, 11:30 y 18:47 ART + a mano):
  - `diario`: `fecha`, `oficial {c,v}`, `blue {c,v}`, `mep {v}`, `ccl {v}`, `mayorista {v}`, `cripto {c,v}`,
    `tarjeta {c,v}`, `riesgo`, `reservas`, `base`, `badlar`, `tamar`, `pf`, `depusd`, `compras` (BCRA 78), `bopreal`
    (158), `merval`. Historia desde 27/03/2026 (`compras`, `bopreal`, `merval` desde el 1/1; Ámbito, mayorista y plazo
    fijo desde el 1/12 del año anterior: `AMBITO_LARGO`, `BCRA_LARGO`).
  - `mensual`: `mes`, `infl`, `inflYoY`, `expect`; desde 2023-01 `base`, `m2`, `m2t`, `cer`, `leliq`, `pases`, `lefi`,
    `prim`, `fin`, `expo`, `impo`, `saldo`.
  - `trimestral`: `trim`, `pib` (corriente, anualizado). Meses sin trimestre: PBI estimado con el CER.
  - `historico` (mensual desde 2017-01): `ofi`, `blue`, `mep`, `ccl`, `may`, `cer`, `cpi` (CPI-U de EE.UU.: FRED da
    timeout desde Actions, se usa la API v1 del BLS).
  - Nunca inventa datos: si una fuente falla, deja lo que había. `estado.json` guarda fuentes OK y con error.
  - Genera también la imagen diaria (`scripts/diario.html` + `diario.mjs` → `diario/hoy.png`, `diario/texto.txt`).
- `global.json` + `global_hist.json` (scripts/global.py) y `usa.json` (scripts/usa.py), workflow `global.yml`:
  L a V cada hora 08:23-19:23 ART, findes cada 6 h y en cada push de esos scripts. Errores en el campo `errores`.
- `noticias.json` (workflow `noticias.yml`, L a V cada hora 6 a 22 ART, findes cada 3 h).
- Chequeo diario del sitio publicado (`chequeo-sitio.yml` + `scripts/chequeo.mjs`, L a V 19:43 ART): si hay problemas
  graves abre un issue (avisa por mail al dueño) y lo cierra solo cuando se arregla. Revisa también la portada.
- Secreto del repo: `BEA_KEY` (clave gratis del BEA para el PBI de EE.UU.). Si falta, la tarjeta de PBI no aparece.

## Fuentes (verificadas desde Actions)
- Ámbito `https://mercados.ambito.com//<ruta>/historico-general/DESDE/HASTA` (el rango EXCLUYE HASTA; rutas
  `dolar/informal`, `dolar/oficial`, `dolarrava/mep`, `dolarrava/cl`, `riesgopais`, `indice/.merv`). En feriados repite
  MEP/CCL: se filtran con los días de oficial/mayorista. El 13/08/2025 de MEP y CCL da error (queda sin dato).
- BCRA `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{id}` (acepta `limit=3000`). IDs: 1 reservas, 5 mayorista,
  15 base, 7 BADLAR, 44 TAMAR, 12 PF 30d, 108 depósitos USD, 27/28 IPC, 29 REM, 78 compras, 158 BOPREAL, 109 M2,
  197 M2 transaccional, 30 CER, 155 LELIQ, 152 pases, 196 LEFI.
- datos.gob.ar: `452.3_RESULTADO_RIO_0_M_18_54`, `452.3_RESULTADO_ERO_0_M_20_25`, `74.3_IET_0_M_16`,
  `74.3_IIT_0_M_25`, `74.3_ISC_0_M_19`, `166.2_PPIB_0_0_3`.
- DolarApi `https://dolarapi.com/v1/dolares` y data912 `https://data912.com/live/arg_stocks|arg_bonds` (desde el navegador).
- Mundo: CNBC (`quote.cnbc.com/...restQuote` y `ts-api.cnbc.com/harmony/app/charts/1Y.json`; a veces devuelve historia
  vacía: se reintenta), Banco Mundial (el FMI da 403), BIS WS_CBPOL, Frankfurter, CoinGecko, RSS (El País, DW,
  Expansión, France 24, Euronews, BBC Mundo filtrado). Yahoo da 429 y Stooq no responde.
- EE.UU.: Tesoro (deuda y curva), BLS v1 sin clave (máximo cada 12 h; series nacionales, rubros `r_*`, JOLTS y 51
  estados), BIS (Fed), CNBC, DOL `oui.doleta.gov/unemploy/csv/ar539.csv` (c3 iniciales, c8 continuos, suma de estados,
  sin desestacionalizar), Freddie Mac `PMMS_history.csv`, Nasdaq `api.nasdaq.com/api/calendar/earnings`, BEA (con clave).
- Sin fuente gratuita: deuda del Tesoro en pesos (LECAP/BONCAP), historia por acción argentina, liquidación del agro.

## Entorno de Claude
- La terminal no tiene internet salvo GitHub: las fuentes se miran con WebFetch y la prueba real es correr el workflow
  (un push a los scripts dispara `global.yml`). `env -u GH_TOKEN gh api repos/...` sirve para leer (repo público).
- Para probar la página: servidor local en el repo y Playwright con Chromium de `/opt/pw-browsers`; d3/topojson y
  fuentes no cargan desde la red: servirlos locales con `page.route`.

## Decisiones del dueño (no volver a proponer)
- Descartados: calendario de vencimientos de deuda, "BSTEP", balanza cambiaria, liquidación del agro, gráfico histórico
  por acción, deuda del Tesoro en pesos, newsletter, inflación semanal de alimentos propia, "el día en 30 segundos",
  dólar contra la banda cambiaria, curva de tasas en pesos, capas del globo con datos viejos (exportaciones por destino,
  deuda/PBI), sección China, rediseño "sala de situación".
