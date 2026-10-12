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
- Encabezado: selector `#modo` (Inicio `#modoH` | Argentina | El mundo | Sobre Pulso Macro `#modoS`; en celular grilla 2x2);
  el logo (`#brandH`) vuelve a la portada. Botón flotante "Volver al inicio" (`#flHome`) en todas las vistas menos la portada.
- Adentro: migas (`#crumb`), pestañas como píldoras (`#tabsNav a[data-g]`, en celular grilla de 2 columnas), recuadro
  `#here` con qué es cada sección, y selector de período `#segRange` (1M/3M/6M/1A/Todo; los mensuales no lo usan).
- Hashes (no cambiarlos): Argentina = `#dolares`, `#macro` ("Inflación y reservas"), `#dinero` ("Tasas y pesos"),
  `#fiscal` ("Cuentas del Estado"), `#actividad` ("Actividad y empleo"), `#mercado` ("Bolsa y bonos"), `#noticias`, `#calculadoras`;
  El mundo = `#global` (Mundo), `#eeuu` (Estados Unidos; `setTab('eeuu')` pone `G.vista='usa'`), `#brasil`, `#europa`
  `#mexico`, `#chile`, `#japon`, `#reinounido`, `#canada`, `#colombia`, `#turquia` y `#peru`; `#sobre`.
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
- Actividad y empleo (`#actividad`, `vA`, `renderActividad`; datos `actividad.json` de scripts/actividad.py en `global.yml`,
  máx. cada 6 h): EMAE desestacionalizado e interanual, salarios reales (÷ IPC nacional, nov-2023 = 100; no registrados
  corridos 5 meses atrás por el rezago del INDEC), desocupación EPH trimestral, canasta básica total y alimentaria × 3,09
  (familia tipo). En Macro, "Inflación por rubro" (`renderRubros`, `RUB`: 12 divisiones + núcleo/regulados/estacionales).
  La API de datos.gob.ar devuelve meses vacíos al azar: el script pide cada serie sola, reintenta y junta con lo guardado.
- Mercado: ranking "¿Qué le ganó a la inflación?", Merval en $ y US$ CCL, mapa de calor de 21 líderes (`LIDERES`,
  data912 desde el navegador cada 10 min), AL30/GD30 con TIR y paridad.
- Noticias: `noticias.json` (scripts/noticias.py, RSS de Ámbito, Infobae, La Nación, iProfesional y Perfil, 48 h).
- Calculadoras: plazo fijo vs dólar, inflación (CER), sueldo en dólares y de viaje (`calcVia`, `VIA`: 12 monedas con
  cotización de `global.json`/`global_hist.json`; tarjeta, MEP, blue y cripto; "hace un año" con MEP mensual y CER).
- Sobre Pulso Macro: contenido estático en el HTML (`vS`). No cambiar su texto sin que lo pida el dueño.

### Apartados dentro de Mundo y Estados Unidos
- Barra `.subtabs` (`#gSubM`, `#gSubU`) y bloques `.gsub[data-sub]`; `SUBS`, `aplicarSub`, `setSub` (se recuerda en
  localStorage `sub-M` / `sub-U`). Pedido del dueño: los menos apartados posibles, lo coherente junto.
- Mundo: arriba SIEMPRE los dos globos (no sacarlos de ahí). Apartados: Bolsas y acciones (reloj, bolsas, termómetro,
  Argentinas en WS, Líderes, gráficos, ¿qué rindió más?, cripto) · Economías y tasas (ficha del país, ¿dónde está
  Argentina?, agenda y tasas de bancos centrales, bonos) · Commodities y monedas · Noticias · Explorador (solo compu). Tocar un país del globo
  lleva a Economías y tasas, a la ficha. Tocar un commodity lleva a Bolsas y acciones, al gráfico.
- Estados Unidos: arriba SIEMPRE mapa, deuda, Fed y los 6 indicadores. Apartados: Economía (semáforo, rubros, próximos
  datos, empleos, mercado laboral, PBI) · Tasas y deuda (Fed vs inflación, curva, decisiones, hipotecaria) · Wall Street
  (50 empresas, sectores, 7 magníficas, balances).

### Brasil (`#brasil`, sección `vB`, `renderBrasil`, datos `brasil.json` de scripts/brasil.py en `global.yml`)
- Arriba siempre 6 indicadores: real por dólar (PTAX), un real en pesos (mayorista de data.json ÷ PTAX del mismo día),
  Selic con cuenta regresiva al Copom (`BCAL` BRA), IPCA 12 meses, desempleo y Bovespa. Apartados (`#gSubB`, `SUBS.B`):
  Economía (IPCA mensual, IBC-Br interanual, desempleo, reservas) · Tasas y expectativas (Selic vs IPCA, decisiones del
  Copom sacadas de los cambios de la Selic, encuesta Focus) · Mercados y el real (PTAX, real en pesos, Bovespa, acciones).
- Fuentes: BCB SGS `api.bcb.gov.br/dados/serie/bcdata.sgs.{código}/dados` (432 Selic meta: viene cargada hasta la próxima
  reunión, se cortan fechas futuras; 1 PTAX; 433/13522 IPCA; 24363 IBC-Br sin desestacionalizar, el 24364 falla; 24369
  desempleo; 13621 reservas) y Focus (`olinda.bcb.gov.br/.../ExpectativasMercadoAnuais`). El BCB a veces da 502: se reintenta.

### Europa (`#europa`, sección `vE`, `renderEuropa`, datos `europa.json` de scripts/europa.py en `global.yml`)
- Arriba siempre: euro en dólares (BCE), un euro en pesos (mayorista × euro del BCE del mismo día), tasa del BCE con
  cuenta regresiva (`BCAL` DEU), inflación, desempleo y Euro Stoxx 50. Apartados (`#gSubE`, `SUBS.E`): Economía
  (inflación general y núcleo, por país, PBI trimestral, desempleo) · Tasas y bonos (BCE vs inflación, decisiones, bonos
  del día y prima de riesgo Italia/España/Francia vs Alemania) · Mercados y el euro (euro/dólar, euro en pesos, bolsas
  europeas `global.json → europa`, empresas europeas).
- Fuentes: BCE `data-api.ecb.europa.eu` (FM tasa de depósito, EXR euro, IRS bonos 10 años mensual, LFSI I9 desempleo
  zona euro) y Eurostat (`prc_hicp_minr`: desde 2026 el HICP usa ECOICOP 2 y el viejo `prc_hicp_manr` quedó en 12/2025;
  `une_rt_m` países; `namq_10_gdp`). europa.py descarta series atrasadas (más de 5 meses; PBI 8) en vez de mostrarlas.

### México (`#mexico`, sección `vX`, `renderMexico`, datos `mexico.json` de scripts/mexico.py en `global.yml`)
- Pedido del dueño: cada país con su propia sección (Brasil, Europa, México, ...), NO agrupar en "Latinoamérica".
- Arriba siempre: peso mexicano por dólar (BIS completado con CNBC `fx_mxn`/`monedas.MXN`; con clave, FIX), un peso mexicano
  en pesos (mayorista ÷ dólar en México del mismo día), tasa de Banxico con cuenta regresiva (`BCAL` MEX), inflación,
  desempleo e IPC México. Apartados (`#gSubX`, `SUBS.X`): Economía (inflación 12 meses y del mes, PBI trimestral,
  desempleo; remesas y reservas solo con clave) · Tasas y bonos (Banxico vs inflación, decisiones sacadas de los cambios,
  bono a 10 años vs EE.UU. con `mx10`/`t10`) · Mercados y el peso (peso/dólar, peso en pesos, IPC `mxx`, ADR `acciones.mex`).
- Fuentes sin clave: BIS (WS_CBPOL D.MX, WS_XRU D.MX.MXN.A, WS_LONG_CPI M.MX.771 y .628; viene con ~1 mes de atraso) y
  OCDE (`sdmx.oecd.org`: DF_IALFS_UNE_M desempleo, DF_QNA_EXPENDITURE_GROWTH_OECD PBI G1/GY; los períodos "2026-Q2" no se
  comparan con fechas). Banxico SIE pide clave (secreto opcional `BANXICO_TOKEN`: FIX SF43718, reservas SF43707,
  remesas SE27803). INEGI pide clave; Frankfurter y FRED dan timeout desde Actions.
- Todas las secciones de país tienen un cuarto apartado "Noticias" (ver noticias_paises.json).

### Chile (`#chile`, sección `vCl`, `renderChile`, datos `chile.json` de scripts/chile.py en `global.yml`)
- Mismo formato que México, sin clave: BIS (WS_CBPOL D.CL, WS_XRU D.CL.CLP.A, WS_LONG_CPI M.CL.771/.628) y OCDE (CHL).
  Arriba: peso chileno por dólar, mil pesos chilenos en pesos (mayorista ÷ dólar en Chile), tasa del Banco Central
  (`BCAL` CHL), inflación, desempleo y bolsa chilena. CNBC no tiene el IPSA: se usa el ETF ECH (`global.json → chile.ech`,
  historia `ech`). Apartados (`#gSubC`, `SUBS.C`): Economía (+ cobre, `cobre` en US$/t) · Tasas y bonos (`cl10` vs `t10`)
  · Mercados y el peso (ADR `acciones.chl`) · Noticias (La Tercera Pulso, Diario Financiero, Cooperativa, Ex-Ante).

### Japón (`#japon`, sección `vJp`, `renderJapon`, datos `japon.json` de scripts/japon.py en `global.yml`)
- Mismo formato que Chile (BIS D.JP / D.JP.JPY.A / M.JP.771 y .628; OCDE JPN). Arriba: yen por dólar, cien yenes en
  pesos, tasa del Banco de Japón (`BCAL` JPN), inflación, desempleo y Nikkei (`bolsas.TSE`). `global.json → japon`
  (TOPIX, yen, bonos a 2 y 30 años) e historia `fx_jpy`, `topix`, `jp10`, `jp2`. Apartados (`#gSubJ`, `SUBS.J`):
  Economía · Tasas y bonos (con la explicación del carry trade) · Mercados y el yen (ADR `acciones.jpn`) · Noticias
  (NHK World en español: JSON `nhkworld/data/es/news/all.json`, categoría BUSINESS cuenta como economía).
- La historia de CNBC en `global_hist.json` cubre unos 2 años (los textos dicen "últimos dos años").

### Reino Unido (`#reinounido`, sección `vUk`, `renderReino`, datos `reinounido.json` de scripts/reinounido.py en `global.yml`)
- Mismo formato que Japón (BIS D.GB / D.GB.GBP.A, que viene en libras por dólar y se invierte / M.GB.771 y .628; OCDE GBR,
  el desempleo llega con ~3 meses de atraso). Arriba: libra en dólares, una libra en pesos (mayorista × dólares por libra),
  tasa del Banco de Inglaterra (`BCAL` GBR), inflación, desempleo y FTSE 100 (`bolsas.LSE`). `global.json → reino`
  (FTSE 250, libra, gilts a 2 y 30 años) e historia `fx_gbp`, `ftmc`, `gb10`, `gb2`. Apartados (`#gSubR`, `SUBS.R`):
  Economía · Tasas y bonos (con la explicación de la crisis de los gilts de 2022) · Mercados y la libra (ADR
  `acciones.gbr`) · Noticias (`reino` en noticias_paises.py: en español hay pocas; los findes puede quedar vacío).

### Canadá (`#canada`, sección `vCa`, `renderCanada`, datos `canada.json` de scripts/canada.py en `global.yml`)
- Mismo formato que Japón (BIS D.CA / D.CA.CAD.A en C$ por dólar / M.CA.771 y .628; OCDE CAN). Arriba: dólar canadiense
  por dólar, un dólar canadiense en pesos (mayorista ÷ C$ por dólar), tasa del Banco de Canadá (`BCAL` CAN, fechas hasta
  dic-2027), inflación, desempleo y S&P/TSX (`bolsas.TSX`). `global.json → canada` (C$, bonos a 2 y 30 años) e historia
  `fx_cad`, `tsx`, `ca10`, `ca2`. Apartados (`#gSubK`, `SUBS.K`): Economía · Tasas y bonos · Mercados y el dólar canadiense
  (petróleo WTI con la explicación de la "petrodivisa", TSX, ADR `acciones.can`) · Noticias (en español casi no hay).

### Colombia y Turquía (`#colombia` `vCo` `renderColombia` `SUBS.O`; `#turquia` `vTr` `renderTurquia` `SUBS.T`)
- Mismo formato que Japón, datos `colombia.json`/`turquia.json` (scripts/colombia.py y turquia.py: BIS D.CO/D.TR, XRU COP/TRY,
  CPI 771/628; OCDE COL/TUR). `BCAL` COL y TUR solo con fechas de 2026: cargar 2027 cuando las publiquen.
- Colombia: mil pesos colombianos en pesos, MSCI COLCAP (`global.json → colombia.colcap`, historia `colcap`), ADR
  `acciones.col` (EC, CIB, AVAL, TGLS); sin bono a 10 años (CNBC no lo tiene), por eso el apartado se llama "Tasas".
  Noticias de El Tiempo, Portafolio, La República, Semana y Valora Analitik.
- Turquía: una lira en pesos, BIST 100 (`turquia.xu100`, historia `xu100`), bonos 2 y 10 años (`tr2`, `tr10`), ETF TUR
  y Turkcell; tarjetas "Inflación: Turquía contra Argentina" y "Lira contra peso" (base 100 con `fx_try` y `fx_ars`).
  En español casi no hay noticias de Turquía.

### Perú (`#peru`, sección `vPe`, `renderPeru`, `SUBS.P`, datos `peru.json` de scripts/peru.py en `global.yml`)
- Fuente: API del BCRP sin clave (`estadisticas.bcrp.gob.pe/estadisticas/series/api/{serie}/json/{desde}/{hasta}`; períodos
  "Sep.2026" y "01.Oct.26", "n.d." = sin dato): PD04722MM tasa, PN01273PM inflación 12 meses (Lima), PN01271PM del mes,
  PN01728AM PBI mensual interanual, PN38063GM desempleo Lima, PD04640PD soles por dólar. Sin bono (CNBC no lo tiene) y sin
  `BCAL` (el BCRP no publica un calendario fácil de verificar). CNBC dejó de actualizar el S&P/BVL: se usa el ETF EPU
  (`global.json → peru.epu`, historia `epu`). ADR `acciones.per` (BAP, SCCO, BVN, IFS). Noticias de Gestión, El Comercio,
  La República (Perú), Andina y RPP.
- Probados y descartados por falta de datos gratis al día: India (BIS no tiene su tasa, no hay desempleo ni noticias en
  español) y Uruguay (BIS no tiene tasa ni inflación; el BCU y el INE no responden desde Actions).

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

### Global › Mundo › Monitor (`data-sub="explorar"`, botón "Monitor ✦", objeto `XP`, `xpStart`/`xpDraw`)
- Pedido del dueño: NO interactivo, para dejar prendido de ambiente (el Explorador interactivo se descartó: "no se entiende").
  Nunca escribir "escaneando" ni textos que finjan procesos. Solo computadora: `xpDesk()` = `(min-width:1024px) and
  (pointer:fine)`; en celular/tablet el botón se oculta. Se arranca desde `aplicarSub('M')`.
- Globo gigante en canvas (d3 orthographic) con anillos de radar, barrido que muestra el dato de cada país al pasar, noche
  real (`xpSun`), luces de `GEX`, arcos del carry trade y destellos de titulares (`xpNews`). Escenas automáticas
  `XP_SCN` cada `XP_DUR` (22 s): bolsas, monedas, tasas, inflación (se acerca a Argentina) y bonos; vuela al destacado y
  muestra un recuadro con su serie de global_hist (`XP_BK`, `XP_MK`, `XP_BO`). Paneles: relojes `XP_CLK`, VIX, Argentina
  (`live`, `series`), flujo de datos (`xpRain`) y consola (`xpLog`).
- "Modo monitor" (`xpModo`): clase `body.mon` (deja visibles las cintas y fija el monitor debajo con `--monTop`),
  pantalla completa, Wake Lock para que no se apague; Esc o clic para salir. Rendimiento: DPR máx. 1,25, 30 cuadros por
  segundo, países agrupados por color y solo la cara visible; los globos de arriba se pausan si no están en pantalla.

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
- `noticias_paises.json` (scripts/noticias_paises.py, mismo workflow `noticias.yml`): titulares de 48 h para el apartado
  "Noticias" de todas las secciones de país (`renderNP`, `NP_PAIS`; se dispara solo desde `aplicarSub`). Reglas por
  medio: "econ" (medio del país: solo economía y sin titulares de otro país, `OTROS`) o "pais" (medio de afuera: tiene que
  nombrar al país, `PAIS`, y ser de economía, `ECON`); `RUIDO` saca deportes, policiales y espectáculos. Brasil tiene
  pocos titulares: en español casi no hay medios brasileños (Agência Brasil en español publica poco de economía).
  Medios que dan 403 desde Actions: El Economista México por sección, Forbes México, elEconomista.es.
- Chequeo diario del sitio publicado (`chequeo-sitio.yml` + `scripts/chequeo.mjs`, L a V 19:43 ART): si hay problemas
  graves abre un issue (avisa por mail al dueño) y lo cierra solo cuando se arregla. Revisa también la portada.
- Secretos del repo: `BEA_KEY` (clave gratis del BEA para el PBI de EE.UU.; si falta, la tarjeta de PBI no aparece) y
  `BANXICO_TOKEN` (opcional, SIE de Banxico; si falta, México no muestra remesas, reservas ni FIX).
- `global.yml` tiene 20 min de límite: cuando se suman claves a `HIST`, global.py vuelve a bajar toda la historia (~6 min).

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
