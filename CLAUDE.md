# Pulso Macro: notas técnicas del proyecto

Leé este archivo antes de tocar nada. Este repositorio es PÚBLICO: acá van solo notas técnicas.
Nada de datos personales, trámites, claves, mails ni preferencias privadas del dueño.

## Cómo trabajar
- El dueño no es programador: hablale en español rioplatense, de "vos", conciso, en criollo.
  Cuando tenga que hacer algo él (GitHub, Cloudflare, configuraciones): TODOS los pasos juntos en un solo mensaje, numerados
  y cortos (pedido del dueño 01/11/2026: menos idas y vueltas), explicando lo que esté en inglés. Su notebook es chica y no
  tiene tecla Supr: para reemplazar texto, Ctrl+A y después Ctrl+V (pega encima, no hace falta borrar).
- Trabajá por bloques y verificá cada bloque antes de seguir. Para cambios visuales grandes, primero una maqueta.
- Nunca mostrar datos viejos como si fueran actuales: si una fuente está atrasada, se saca o se aclara la fecha.
- Commits: terminar con las líneas de atribución que indique el sistema.

## Nombre, estética y URLs
- Sitio: **Pulso Macro** en **https://pulsomacro.com.ar/** (GitHub Pages, rama `main`, carpeta raíz, archivo `CNAME`;
  DNS en Cloudflare con nube naranja (proxy); el link viejo epherrafrancisco-gif.github.io/macro-ar redirige solo).
- Cloudflare (plan gratis): SSL Full (strict); Cache Rule "Cachear todo 1 min" (todo elegible, Edge TTL = cache-control
  de origen; GitHub manda 10 min); Browser Cache TTL = "Respect Existing Headers"; Smart Tiered Cache activo; rate limit
  1000 pedidos / 10 s por IP (bloqueo 10 s); Web Analytics automático. Para forzar un cambio ya: Caching → Configuration
  → Purge Everything (después de que termine el deploy de Pages, no antes).
- Datos en vivo (worker/vivo.js, Worker `pulso-vivo`, cron cada minuto, binding R2 `DATOS` = bucket `pulso-datos`):
  trae DolarApi y Open BYMADATA (acciones y bonos, acceso gratuito de BYMA) cada minuto y guarda `vivo.json` (cache-control 60 s) en R2, publicado en
  `https://datos.pulsomacro.com.ar/vivo.json` (dominio propio del bucket, CORS solo pulsomacro.com.ar). Cache Rule
  "Datos en vivo: ignorar query" en ese host: ignora la query para que nadie fuerce lecturas de R2 con URLs inventadas.
  La página (`vivo()` en index.html) lo usa si tiene menos de 5 min (dólar) / 10 min (mercado); si no, va directo a
  DolarApi (solo el dólar; acciones y bonos salen únicamente del Worker). El editor del panel de Cloudflare no deja editar por script: el código se pega a mano en
  "Edit code" (si se cambia worker/vivo.js, hay que volver a pegarlo).
  El repo sigue llamándose `macro-ar`: no renombrar (rompe la redirección). Nunca usar "Macro AR" en nada visible.
- Logo: "pulso en anillo" (anillo celeste #6aa8d8 con un latido blanco adentro, sobre #0e1319; elegido por el dueño el
  25/10/2026 después de descartar la "P del pulso": "parece la P de un contacto", "sin letras") + `Pulso<span>Macro</span>`
  ("Macro" en mono y color de acento). En `#brandH` y `.mlogo` va la marca sola (`svg.lg`, sin cuadrado de fondo).
  Archivos: `icons/anillo.svg` (favicon de todas las páginas, también `ICON` en paginas.py y /diario/), `anillo-48/192/512.png`,
  `anillo-maskable-512.png`, `anillo-apple-180.png`. Si se cambia el logo, usar nombres de archivo NUEVOS (así nadie queda con
  el viejo en caché). `<meta name="color-scheme" content="dark">` en todas las páginas: sin eso, el modo oscuro forzado de
  Samsung Internet/Chrome recolorea la página (aclaraba el logo y los colores). Archivos descargados: `pulso-macro_<...>`.
- Tema oscuro por defecto para todos (`:root` con colores fijos y `color-scheme:dark`), también en /diario/. Modo claro beige whisky con detalles dorados (02/11/2026: "que no se vea apagado")
  opcional (pedido del dueño 01/11/2026), solo en index.html: botón `button[data-tema]` (`.temabtn`) al lado de "¿Cómo se usa?"
  en `.hello` y en `#mHero` (`.mhb`), dice "Modo claro" u "Modo oscuro" según el que esté puesto (`temaPintar`). Pone
  `html[data-tema="claro"]` (redefine las variables de `:root` + unos pocos fondos fijos) y lo guarda en localStorage `pm-tema`;
  un script en el `<head>` lo aplica antes de pintar. OJO: el selector del botón es `button[data-tema]` (el `<html>` también
  tiene `data-tema`). Los recuadros de TradingView quedan como islas oscuras. Globos de Mundo y portada (`gDraw`, `dgDraw`): en modo claro
  se pintan claros (esfera crema/dorada, verde y rojo más oscuros, etiquetas con fondo crema; `esClaro()`, pedido del dueño
  02/11/2026). Crucigrama y páginas de indicadores (paginas.py) también leen `pm-tema` = 'claro' con un script en el `<head>` y
  tienen su bloque `html[data-tema="claro"]` (pedido del dueño 03/11/2026); Terminal y Verdadero o falso quedan oscuros a propósito. El Monitor en modo claro es una terminal dorada whisky (pedido del dueño 03/11/2026): variables de `.xpw` redefinidas en el
  bloque CSS "Monitor en modo claro" y colores del lienzo en el objeto `K` de `xpDraw` (según `esClaro()`).
- Modo Ciudad (cyberpunk con una ciudad de neón tipo Chongqing de fondo; pedido del dueño 02/11/2026): PREMIO SECRETO, nunca el
  modo por defecto. Se desbloquea con 30 seguidas en Verdadero o falso (`CIU_META` en juego.js; también si `PT.max` ya era ≥30):
  marca `pm-ciudad` = '1' en localStorage, cartel `#ciu` (imagen = el render `fondos/ciudad3-1200`, encuadre en la torre de 宏观脉搏, desde el 02/11/2026; antes el dibujo `ciudad.svg`; "Desbloqueaste el modo Ciudad", "Probarlo ahora" pone `pm-tema` =
  'cyber' y va al inicio), aviso `.lockr` en cada pregunta arriba de la fuente ("30 seguidas desbloquean un modo secreto"; desaparece al ganarlo), el medidor
  dice "· modo secreto" camino a 30. Evento GoatCounter `ciudad-desbloqueado`. En index.html: `html[data-tema="cyber"]` (bloque
  CSS "Modo Ciudad") y capa fija `#cyFx`: ciudad cyberpunk vista desde lo alto RENDERIZADA por código (02/11/2026, el dueño
  pidió algo realista y no le gustó ni la foto ni el dibujo SVG): `scripts/ciudad_render.py` (12 capas de edificios en perspectiva
  con terrazas, ventanas, neblina y desenfoque por distancia, calles con luces, bloom y grano; ~22 carteles de neón en chino y una
  torre protagonista con 宏观脉搏 = "Pulso Macro") → `fondos/ciudad3-2400.webp/.jpg` y `-1200` (≤900px, encuadre 66%); solo se baja
  en ese modo. Quedaron sin uso `fondos/chongqing-*` (foto) y `fondos/ciudad2*.svg`. Cartel cian con el nombre del dueño en chino (弗朗西斯科 / 埃佩拉 = "Francisco Epherra", en dos renglones para que entre en el
  recorte del celular). Dos jets privados `.jet` (pedido del dueño 02/11/2026: realistas, de diseño propio, "como nuestra aerolínea": logo del anillo en la cola y franja celeste, sin texto porque a ese tamaño no se lee; NO en
  línea recta; reemplazan a los autos voladores, que no le gustaron): `jetVuelo` al final de index.html los mueve por una
  curva de Bézier al azar en cada pasada, con inclinación según la dirección, balanceo leve y tamaño que cambia (se acerca o
  se aleja); luces de navegación que titilan (`.jbl`, `.jst`); solo corre en modo Ciudad con la pestaña visible; ocultos con
  reducir movimiento. UN solo
  botón `button[data-tema]` que va pasando oscuro → claro → Ciudad (solo con la marca) → oscuro (`temaSig`, pedido del dueño
  02/11/2026) y dice a qué modo pasa. El script del `<head>` solo aplica 'cyber' si está `pm-ciudad`. Es por dispositivo.
- Modo Órbita (la Tierra desde la órbita sobre Argentina, con la nave de Pulso Macro cruzando; pedido del dueño 02/11/2026, reemplazó
  a una "Bóveda" que no le gustó): premio LEGENDARIO, 60 seguidas en Verdadero o falso (`BOV_META` en juego.js; también si `PT.max`
  ≥60), marca `pm-orbita` (se acepta la vieja `pm-boveda`), `pm-tema` = 'orbita' (la vieja 'oro' también entra). SECRETO hasta ganar
  Ciudad: el cartel `#ciu` lo cuenta (`.leg`) con cuántos lo tienen; desde ahí `.lockr` dice "60 seguidas desbloquean el modo legendario
  · lo tiene N persona(s) en el mundo" (`BOV_N`), el medidor "· modo legendario" y en la 59 "Una más…". Cartel `#bov` con la nave sobre la
  Tierra. Contador: `/api/boveda` en el Worker (GET = cuenta, arranca en 1 = el dueño; POST {tk} suma solo con una ficha firmada de
  /api/racha de ≥60, una vez por ficha). Evento GoatCounter `orbita-desbloqueado`. En el juego, "Récord de todos" muestra el mayor
  entre el del servidor y el propio (si no, en los dispositivos del dueño no coincide). Imágenes 3D con Blender (`pip install bpy`,
  Cycles en CPU): `scripts/espacio_blender.py` (texturas 8K de Solar System Scope, CC BY 4.0, basadas en la NASA: día y luces de noche;
  nubes y océanos de la NASA vía three.js; no están en el repo, se bajan de GitHub) + `scripts/espacio_post.py` (estrellas, brillo,
  grano) → `fondos/espacio-2400` y `-1200`; `scripts/nave_blender.py` + `scripts/nave_fuego.py` → `fondos/nave.webp/.png` (avión
  espacial propio: blanco, panza negra, franja celeste, anillo del logo en las derivas, "PULSO MACRO" en el costado, fuego celeste).
  La Tierra GIRA (pedido del dueño 02/11/2026: "que esté girando y se vea más real"): `fondos/tierra.js`, shader propio de WebGL 2
  (rayo por píxel contra la esfera; sin librerías): texturas `fondos/tierra/dia|noche|aux-{2048,4096}.webp` (aux: R = océanos para el
  reflejo del sol, G = nubes reales de 8K de Solar System Scope), luces de las ciudades del lado de noche, atmósfera, estrellas; una
  vuelta cada 15 min (`GIRO`), 30 cuadros por segundo, solo con el modo puesto y la pestaña visible; misma toma que el render de Blender
  (cámara a 1.700 km sobre el Atlántico Sur). Sin WebGL 2 queda la imagen fija (`.tie`). El nombre de la nave es una calcomanía
  (Inter Bold proyectada en el material del fuselaje, solo del lado que se ve). Crédito en Sobre → Licencias.
  En index.html: `html[data-tema="orbita"]` (bloque "Modo Órbita"), capa `#orFx` (`.tie`, `.velo`, `.nave`) y `naveVuelo` al final
  (cruza de izquierda a derecha por una curva suave, 27-54 s, cada 22-50 s; nunca dada vuelta porque se leería el nombre al revés).
  La Tierra en vivo (`fondos/tierra.js`): la imagen fija `espacio-*` es SOLO respaldo sin WebGL y tiene otro encuadre; con WebGL se
  tapa (negro, o la foto del último cuadro guardada en sessionStorage `pm-tierra` al salir, con el punto del giro) para que al volver
  a la página la Tierra no "salte" de arriba hacia abajo (bug reportado 02/11/2026). Un script en línea tras `#orFx` la pone antes del
  primer pintado.
  En celulares (`QUIETO`: puntero táctil y pantalla < 820 px de lado corto) la Tierra NO gira: un solo cuadro (`fijo()`), redibujado
  solo al cambiar el tamaño, y texturas de 2048 (pedido del dueño 02/11/2026: no saturar celulares lentos).
  Los dispositivos del dueño se marcan con un link secreto (`#<clave>` en /verdadero-o-falso/; en el código solo los SHA-256 del link
  viejo y del nuevo del 08/11/2026): récord 81 y los tres modos (Ciudad, Órbita, Coder); abre el cartel `#cod`.
- Modo Coder (pedido del dueño 08/11/2026: "códigos y cables coloridos llevando y trayendo data todo el tiempo en toda la pantalla,
  como si estuvieras viendo el software de una potente IA en tiempo real"): premio SECRETO de 80 seguidas en Verdadero o falso
  (`COD_META` en juego.js; también si `PT.max` ≥80), marca `pm-coder`, `pm-tema` = 'coder'. Nadie sabe que existe hasta ganar Órbita:
  el cartel `#bov` lo cuenta (`.sig`), desde ahí `.lockr` (clase `cod`, verde) dice "80 seguidas desbloquean el modo Coder · lo tiene N
  persona(s) en el mundo" (`COD_N`, `enMundo`), el medidor "· modo Coder" y en la 79 "Una más…". Cartel `#cod` con la animación en vivo
  en chico (`CoderFx.start(canvas, {lite:true})`, se frena al cerrar). Contador `/api/coder` en el Worker (igual que `/api/boveda`:
  arranca en 1 = el dueño, suma solo con ficha firmada de ≥80, `coder/cuenta.json` y `coder/usadas/<firma>` en R2). Piso del récord
  de todos `RACHA_PISO` = 81. Evento GoatCounter `coder-desbloqueado`.
  Animación: `fondos/coder.js` (lienzo 2D propio, sin librerías; en index.html se prende sola con `html[data-tema="coder"]` por un
  MutationObserver, capa `#cdFx` con `canvas` y `.velo`). Capas: fondo fijo con grilla de puntos → columnas de código coloreado que
  suben (pre-dibujadas en lienzos aparte; código propio en `CODE`) → editor abajo a la izquierda donde el código se escribe letra
  por letra → cables como tubos (pre-dibujados: Bézier con caída, muestreados cada 4 px) → paquetes con estela y punto de luz
  (`lighter`, ida y vuelta, alguno rápido y largo) → chips (`NOMBRES`, leds y medidores; se iluminan al llegarles un paquete) y en el
  medio el anillo de Pulso Macro latiendo con ondas. Cada chip va al núcleo y a 1-2 vecinos; unos cables entran desde afuera.
  30 cuadros/s en compu (DPR máx. 1,25, tope 190 paquetes); celular (`pointer:coarse` o pantalla < 600) 24 cuadros, DPR 1, 70
  paquetes; se frena con la pestaña oculta; con reducir movimiento un cuadro fijo. Bloque CSS "Modo Coder" en index.html (cian
  #22d3ee, verde #a3e635, títulos de tarjeta en mono). Ciclo del botón: oscuro → claro → Ciudad → Órbita → Coder.
- Pantalla de carga (pedido del dueño 02/11/2026: al cargar se veía un instante el jet del modo Ciudad, porque `#cyFx` va antes del
  `<style>` grande): en el `<style>` del `<head>` van `#cyFx{display:none}` y `#pmCarga` (primer elemento del body: el anillo con
  los colores del modo puesto, oscuro/claro/Ciudad), que se va con un fundido en DOMContentLoaded (tope 4 s).
- Fuentes: Instrument Sans + JetBrains Mono. Series: s1 azul #3987e5, s2 naranja #d95926, s3 aqua #199e70,
  s4 amarillo #c98500, s5 magenta #d55181. Oficial s1, MEP s2, CCL s3, Blue s4, Mayorista s5.
- Contador de visitas: GoatCounter (cuenta interna `macroar`), función `gc()` en index.html; no cuenta navegadores
  automatizados. Dispositivos del dueño (pedido 26/10/2026): entrar UNA vez por navegador a `pulsomacro.com.ar/#no-contarme`
  (`yo`, `yoHash`; marca `pm-yo` + `skipgc` en localStorage; se deshace con `#contarme`); al pie aparece `#yoNota`.
  En Android y en la compu la app instalada comparte esa memoria con el navegador. Cloudflare Web Analytics (automático,
  plan gratis sin reglas) NO se puede filtrar así: el número oficial es el de GoatCounter.
- Usuarios con la app: eventos GoatCounter `app-nueva-{ios|android|compu}` una vez por dispositivo (la primera vez que se
  abre como app, `pm-app-n`) y `app-abierta-{tipo}` una vez por día de uso (`pm-app-d`). Sumar los `app-nueva-*` de todo
  el período = dispositivos que la tienen (no se puede saber quién la desinstala). `app-instalada` (solo Chrome/Edge) sigue.

## Estructura de la página (`index.html`, todo en un archivo, sin librerías salvo d3/topojson en Global)
- Arriba: dos cintas (`#tape` dólares/brecha/riesgo/Merval; `#tape2` mercados del mundo, PROPIA desde el 28/10/2026 (pedido del dueño: no le gustaba la de TradingView): `renderTape2` con índice dólar, monedas (BCE), tasas 2 y 10 años de EE.UU., bonos alemán y japonés, petróleo (EIA; si tiene más de ~4 días dice "al dd/mm") y lo mensual con su mes (oro, soja, cobre del Banco Mundial; bolsas de la OCDE "S&P 500 en sep"). Nada de TradingView en la cinta). Tarjetas de dólares en el mismo
  orden en compu y celular (`QORD` en `renderQuotes`: Oficial, Blue, MEP, Mayorista, CCL, Cripto, Tarjeta; pedido del dueño). La tercera (reloj de mercados)
  se sacó el 26/10/2026 (pedido del dueño: ocupaban mucho en la compu): ahora es la ficha fija `#tChip` a la izquierda de
  `#tape` ("Bolsas 12 de 41 abiertas", `renderTape3`; solo ≥641px), que lleva al reloj de Mundo
  y los 7 dólares (`#dolHoy`/`#quotes`, `renderQuotes()`): siempre en la portada y en todo Argentina (requisito no
  negociable); NO en Mundo, Estados Unidos ni Sobre Pulso Macro (pedido del dueño).
  Dólar en vivo: cada 60 s (+0-10 s al azar) desde `vivo.json` del Worker, con respaldo a DolarApi directo (si todo
  falla, espera 1, 2, 4, 8 min, tope 10: `liveFallas`; mientras tanto muestra el último cierre).
- Caché (para aguantar mucho tráfico): los JSON se piden con `?t='+VER()` (`VER` = minuto actual), NO con `Date.now()`:
  así todos los que entran en el mismo minuto piden la misma dirección y el CDN la sirve de su copia. No volver a usar
  `Date.now()` en las direcciones de los fetch.
- Orden de Argentina en la portada, la hoja y la grilla del celular (`ARG_T`, pedido del dueño): Dólares, Noticias, Bolsa y bonos,
  Inflación y reservas, Tasas y pesos, Cuentas del Estado, Actividad y empleo, Autos 0km, Ganadería, Vinos y uvas, Surtidores, Industria química, Calculadoras.
- Sin hash: portada (`#vP`, `renderPortada()`): "¿Qué querés ver?" con dos puertas (Argentina / El mundo), tarjetas por
  sección (`SECC` + `ICO`: nombre claro, ícono y una línea). Los países usan bandera en vez de ícono (`FLAG` clave→código, `flag(k)`, `ico(k)`
  la devuelve sola; SVG de flag-icons 7.2.3, MIT, en `vendor/flags/`): fichas, panel Países, hoja del celular, `#mWhere`,
  botón "Países · X" y título de `#here`; además `#here` lleva la bandera grande a la derecha, esfumada hacia
  la izquierda (`.here.conb` + `.hflag`, máscara con degradé; pedido del dueño: "un poquito más nacionalista"). No usar emojis de banderas (en Windows no se ven). País nuevo: sumarlo a `FLAG` y
  copiar su SVG, "Hoy en números" (`#pHoy`) y globo de puntos con resumen.
- Portada en la compu (≥901px): Argentina un tercio y El mundo dos tercios (`.split` 1fr/2fr; países en 3 columnas, todas
  las fichas a la vista: pedido del dueño, "que se aprecie la cantidad"). Al final de Argentina, "Argentina en vivo"
  (`#pVivo`, `pvStart`/`pvTick`, `PV`): cuenta regresiva al próximo dato oficial (`calendario.json`; sin hora = 16:00
  estimada) y los 3 siguientes, hora de Buenos Aires con BYMA, habitantes y PBI mientras mirás (Banco Mundial, `wb` ARG) y
  mini gráficos del último mes (MEP, riesgo, Merval, reservas) que se dibujan al aparecer. No va en celular ni ≤900px.
- Encabezado: selector `#modo` (pedido del dueño 02/11/2026: Inicio `#modoH` | Argentina | Noticias `#modoN` | El mundo | Terminal `#modoT`; Sobre Pulso Macro
  salió de ahí y queda en el pie y en la hoja del celular; en celular el encabezado no se ve). Sin la firma "Diseñado y operado por…" (`.by`/`.mby`, sacada el 02/11/2026);
  el logo (`#brandH`) vuelve a la portada. Botón flotante "Volver al inicio" (`#flHome`) en todas las vistas menos la portada.
- Adentro: migas (`#crumb`), pestañas como píldoras (`#tabsNav a[data-g]`, en celular grilla de 2 columnas). En El mundo
  solo Mundo y el botón "Países" (`#tabPaises`), que abre el panel `#paisPanel` con Estados Unidos y los 44 países
  (`data-g="pais"`; orden pedido por el dueño, igual en el panel, la hoja del celular y la portada: EE.UU., Polonia, Japón, China,
  Turquía, Zona euro, Suiza, Reino Unido, Brasil, Hong Kong, Arabia Saudita, Israel, Corea del Sur, después Alemania, Francia, Italia, Países Bajos y Grecia (sumados el 08/11/2026) y el resto).
  `PAISES_T` son las pestañas de país; `PAISES_M` = `['eeuu', ...PAISES_T]` es el orden del menú (EE.UU. sigue siendo la
  vista `usa` de la pestaña global). Un país nuevo se agrega en el panel y en `PAISES_T`. Recuadro
  `#here` con qué es cada sección, y selector de período `#segRange` (1M/3M/6M/1A/Todo; los mensuales no lo usan).
- Hashes (no cambiarlos): Argentina = `#dolares`, `#macro` ("Inflación y reservas"), `#dinero` ("Tasas y pesos"),
  `#fiscal` ("Cuentas del Estado"), `#actividad` ("Actividad y empleo"), `#autos` ("Autos 0km"), `#ganaderia`, `#mercado` ("Bolsa y bonos"), `#noticias`, `#calculadoras`;
  El mundo = `#global` (Mundo), `#eeuu` (Estados Unidos; `setTab('eeuu')` pone `G.vista='usa'`), `#brasil`, `#europa`
  `#mexico`, `#chile`, `#japon`, `#reinounido`, `#canada`, `#colombia`, `#turquia`, `#peru` y `#polonia`; `#sobre`.
- Celular (≤640px, `body.insec` siempre y `body.mporta` en la portada; en la compu no cambia nada). Pedido del dueño:
  que el que entra por primera vez entienda qué es, dónde está y cómo moverse.
  - Barra de abajo `#mNav` (Inicio · Argentina · El mundo · Noticias, pedido del dueño 02/11/2026; antes el cuarto era Calculadoras, que sigue en la hoja de Argentina; `mNavMarcar`): Argentina y El mundo abren la
    hoja `#mSheet` con la lista de esa parte y una línea por sección (`mSheetArmar(grp)`). Arriba, `#mbar` con flecha
    para volver (`#mLogo`) y dónde estás (`#mWhere`). Se ocultan header, `#tChip`, migas, pestañas y `#mBtn`. Arriba queda una cinta (pedido del dueño): `#tape` (dólares) en portada y Argentina, `#tape2` (mercados) en El mundo y países (`body.mglo`, en `mActualizar`). En la portada no va `#mbar`.
  - Portada: `#mHero` (logo Pulso Macro, la firma y una bajada corta; nada de eslogan, pedido del dueño) (antes: qué es Pulso Macro y la firma "Diseñado y operado por…", `.mby`, como `.by` en la compu), los dólares (pedido del dueño 26/10/2026: SIN "Los datos del día"; `#mHoy` queda oculto, como en la compu) y un selector Argentina / El mundo (`#mTg`, `body[data-door]`) con las secciones en grilla
    compacta. El cartel de primera visita `#mTip` se sacó el 02/11/2026 (pedido del dueño): queda en el HTML, siempre oculto.
  - Secciones: "En resumen" en criollo (`#mRes`, `mResumen`/`mResTxt`: dólares, macro, dinero, mercado, ganadería; si no
    hay, queda `#here`), 4 indicadores y botón "Ver los N indicadores" (`.mmas`), y tarjetas plegables (`mAcordeon`,
    clases `.macc`/`.mk`/`.mc`): pedido del dueño, al entrar a una sección o cambiar de apartado TODAS cerradas (`mAb` se
    vacía) y la página arriba de todo (`scrollTo(0,0)` en `setTab`, `history.scrollRestoration="manual"` en celular); al cambiar de apartado, la barra de apartados queda pegada abajo de `#mbar` (`mSubArriba`); al volver para atrás (botón del navegador o la flecha `#mLogo`, que hace `history.back()` si hay a dónde
    volver dentro del sitio), la página vuelve a la altura donde estaba (`NAV`: id por entrada en `history.state` para
    distinguir "atrás" de un link #algo, que en Chrome también dispara popstate; la altura se guarda al scrollear;
    las navegaciones propias usan `navPush`), para que se vean juntas y el usuario elija; al abrir se llama a `render()`. No se pliegan: portada, Sobre, Calculadoras, Noticias, tarjetas con canvas (globos) ni lo que está arriba
    de los apartados en Mundo, EE.UU. y países. Los dólares van en fila compacta (`.quotes.compact`, menos en `#dolares`)
    con Oficial, Blue y MEP primeros (pedido del dueño). `mActualizar()` corre al final de `setTab`.
- Instalar como app (pedido del dueño): `manifest.webmanifest`, íconos en `icons/` (`anillo-*`: 192, 512, maskable, apple-touch 180;
  mismo dibujo que el favicon) y `sw.js`, que NO guarda nada (todo va a la red; solo muestra un aviso si no hay conexión).
  Botón `[data-inst]` en la portada (`.hello` en la compu, `#mHero` en el celular): en Chrome/Edge (`chromium`) aparece SOLO con
  `beforeinstallprompt` (que no llega si ya está instalada; pedido del dueño: no ofrecerla a quien ya la tiene) y abre el cartel del navegador; en iPhone/iPad abre `#iosInst` con los 3 pasos (Apple no permite
  hacerlo solo; pasos lo más cortos posible, pedido del dueño: Safari 26+ = ••• → Compartir; Safari ≤18 = Compartir abajo; Chrome/iPad = Compartir arriba); si el navegador no manda su aviso (pasa después de desinstalar), el botón igual aparece y abre los pasos para ese
  navegador (`pasos()`: Edge, Chrome, Android, Samsung, Safari de Mac; evento `instalar-pasos`); en Firefox de compu no aparece. Si ya está instalada tampoco: marca `pm-app` en localStorage (al instalar o abrir como
  app) + `getInstalledRelatedApps` (`related_applications` en el manifest); `beforeinstallprompt` borra la marca. Eventos GoatCounter `instalar-click`, `instalar-ios`,
  `app-instalada`. La app abre `/?app=1`.
- Avisos de novedades (pedido del dueño): cartel chico `#nove` (`noveIni`), una sola vez (se cierra con la X y no vuelve:
  `pm-nove-1027`), SOLO a quien ya usaba el sitio (tenía alguna marca vieja en localStorage) y hasta `FIN` (29/10/2026 01:10).
  `pm-visita` = desde cuándo se conoce a ese navegador ('0' = de antes del 27/10/2026): para un próximo aviso, mostrarlo a
  quien tenga `pm-visita` anterior a la fecha del cambio, con clave y fecha de fin nuevas. A los nuevos no se les muestra.
- Manual de uso (pedido del dueño, "que no sea molesto"): botón `[data-man]` "¿Cómo se usa?" en `.hello` (compu), `#mHero`
  (celular) y arriba de Aclaraciones en Sobre; abre `#manual` (8 bloques cortos). Nunca se abre solo. Evento GoatCounter `manual`.
- Buscador (pedido del dueño: "que encuentre todo", "que perdone bastante" y que con una palabra vaga muestre todas las
  opciones, como Google): ventana `#bus` (`busAbrir`/`busPintar`/`busIr`), se abre con cualquier `[data-bus]` (caja `.bfake`
  en la portada del celular y de la compu, lupa `.mbus` en `#mbar`, botón `.hbus` en el encabezado, oculto en Inicio con `body.mporta`
  porque ya está la caja; pedido del dueño 01/11/2026, junto con menos espacio arriba en la portada de la compu) o con "/" y Ctrl+K.
  El índice (`busArmar`) se arma solo al abrir: secciones (`SECC`), cotizaciones, calculadoras, apartados (`SUBS`), cada
  `.card > .head > h2` (con su nota y el comienzo de `p.sub`) y `GLOS`. Perdona errores (`bLev`, letras cambiadas = 1 error),
  plurales y tildes; sinónimos de la gente en `BSIN` (los de varias palabras se buscan enteros). Primero lo de Argentina.
  Al tocar un gráfico: va a la sección y al apartado, lo abre (`mAb`), baja hasta él y lo marca (`.bflash`); `NAV.salto`
  evita que `setTab` lo vuelva a subir. Eventos GoatCounter `buscar` y `buscar-ir`.
- Celular: el botón de volver de `#mbar` (`#mLogo`) dice "Volver" (o "Inicio" si se entró por link directo); el selector
  Argentina / El mundo de la portada (`#mTg`) son dos botones separados con ícono, el elegido en celeste (pedido del dueño:
  "que se entienda que son dos botones").
- Rendimiento en equipos lentos (26/10/2026, medido con la CPU 6 veces más lenta): widgets de TradingView con carga
  diferida (`tvIO`: el script se agrega recién cuando el recuadro está a ≤400 px de la pantalla; los apartados ocultos no
  cargan nada); glosario y botones de gráficos en tandas de 8 ms (`enTandas`, `decorar1`, `herramienta1`, primero lo
  visible; antes ~1 s de bloqueo); globos con cuadros adaptativos (`cuadroOk`/`cuadroCosto`: si un cuadro tarda >30 ms en compu o >16 en celular (`LIM_CUADRO`, `pesado` con margen; con 12 ms las compus comunes saltaban cuadros y se veía trabado)
  dibuja menos seguido y sin brillo; >40 ms deja de girar y se redibuja al tocar o cada 2 s; texto del globo 4 veces por
  segundo); `#mbar` y `#mNav` sin `backdrop-filter`. Resultado: portada del celular 3,1 s → 0,5 s de bloqueo; Mundo de
  6 a 58 cuadros por segundo. No volver a montar widgets de TradingView sin pasar por `tvw`.
- Rendimiento (10/2026, en celular medio la portada trababa 3-4,5 s): los puntos del globo "Mundo hoy" están precalculados en
  `vendor/dots.json` (si se cambia `world.json` o la grilla de `dgDots`, regenerarlo); el globo de la portada solo arranca si
  se ve (`pCv` con ancho); `herramientas()` marca cada gráfico con `data-tl` (antes buscaba en todo el documento por cada uno).
  Manifest con `launch_handler` `navigate-existing`: los links abren en la ventana de la app que ya está abierta.
- Funciones de gráfico: `lineChart`, `barChart`, `dailyBars`, `hBars` (barras horizontales; opciones `vfmt`, `rh`,
  `ref`, filas con `hl` para resaltar). Cada gráfico guarda `el._exp` para compartir/PNG/CSV (`herramientas()`).
- Glosario (i): objetos `GLOS` y `GLOS_REGLAS`, `decorar()` los agrega solo. Popover `#tipbox`.
- CSV por pestaña: objeto `CSV` (`;`, coma decimal, BOM UTF-8).

### Argentina
- Dólares: cotizaciones, brechas, canje CCL/MEP con banda, "Dólar a precios de hoy" (`renderUsdReal`), últimos días.
- Macro: inflación, REM, reservas, compras del BCRA en el MULC, "Lo que vende Argentina al mundo" (`renderExpo`, `EXPO`:
  soja, maíz, trigo y Brent de global.json/global_hist.json, base 100 a fin del año pasado; Commodities sigue en El mundo), riesgo país, "Próximas publicaciones" (`renderCal`,
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
- Ganadería (`#ganaderia`, `vGa`, `renderGanaderia`, `loadGan`; datos `ganaderia.json` de scripts/ganaderia.py, workflow
  `ganaderia.yml` L a V 13:40, 16:40 y 19:40 ART): Mercado Agroganadero de Cañuelas (ex Liniers; `haciinfo000002` con
  txtFechaIni/Fin, latin-1; opera casi siempre martes, miércoles y viernes; días sin remate en `sin_operaciones`; provisorio
  hasta la tarde, `def`), ~400 días; pizarra de la CAC Rosario (UTF-8, solo el día: la historia se arma guardando, desde
  15/10/2026). Carne al consumidor (`c_*` GBA, `rp_*` picada por región), faena trimestral `faena_t` (la mensual 41.3_FCV
  viene vacía en la API) e IPI carne vacuna `ipi_carne` vienen de actividad.json. Novillo/maíz = novillo $/kg ÷ maíz $/kg.
- Autos 0km (`#autos`, `vOk`, pestaña `tabOk`, `renderAutos`, `loadOk`; pedido del dueño 03/11/2026: "con todas las marcas que se
  venden en el país"; datos `autos.json` de scripts/autos.py, workflow `autos.yml` lunes y jueves 8:20 ART): patentamientos de la DNRPA
  (datos abiertos de datos.jus.gob.ar, "Inscripciones iniciales de autos", CC BY 4.0: ZIP por año desde 2018 + CSV del último mes,
  ~1 mes de atraso). Cada fila trae datos del primer titular: el robot SOLO cuenta totales (nunca guarda nada de una persona) y pesa
  cada fila por `titular_porcentaje_titularidad` (un auto con dos titulares suma 1). 0km = año de modelo ≥ año del patentamiento − 1
  (el archivo trae usados importados: camiones viejos, clásicos). `categoria()`: livianos = auto/suv/pickup/util (lo que se muestra);
  pesados (camiones, acoplados, colectivos) solo en `cat`. Origen: NACIONAL, PROTOCOLO 21 (= Brasil, acuerdo automotor del Mercosur)
  e IMPORTADO (resto del mundo). Años cerrados resumidos en `autos_cache/AAAA.json` (`VERSION`: subirla si cambia la forma de contar
  y se rehacen). `autos.json`: `serie` (mes a mes desde 2018: total, origen, categoría, persona física/jurídica), `det` (últimos 25
  meses: marcas, 400 modelos con versión, provincias), `anios`, `tipo_modelo`, `origen_marca` y `hist` (serie desde 2000 de TODOS los
  automotores, de "Estadística de trámites de automotores": viene un mes antes que el detalle → casillero "Adelanto de <mes>").
  Página: casilleros, mes a mes, ranking de marcas y modelos (período mes/año/12 meses `okPer`, filtro por tipo `okCat`; los modelos
  suman versiones con `okBase`: primer palabra + CROSS/TRACK/MINI/número), tabla de TODAS las marcas que vendieron en los últimos 12
  meses ("sin ventas" si no vendieron en el período; 20 y botón `#okMas`), ficha de la marca al tocarla (modelos, versiones tal como
  las registra la DNRPA, origen), origen y tipo en el tiempo, provincias e historia por año. Precios: PENDIENTE (la DNRPA solo publica
  la tabla de valuación en PDF o formulario; ACARA tiene derechos: no usar).
- Vinos y uvas (`#vinos`, `vVi`, `renderVinos`, `loadVin`; pedido del dueño 01/11/2026, "como MacroLibre pero mejor"; datos
  `vinos.json` de scripts/vinos.py, workflow `vinos.yml` los lunes 9:17 ART): precio del vino común $/litro GBA (INDEC, serie
  `105.1_I2VC_2016_M_19` de la API de series, en pesos o pesos de hoy con `act.ipc`) y datos abiertos del INV en datos.gob.ar
  (CKAN `package_show` → CSV de datos.magyp.gob.ar): cosecha por provincia y variedad (quintales; 1 qq = 100 kg), superficie
  (total, variedades, color, edad, provincias), elaboración (vino/mosto, color), mercado interno (envase, variedad, mes; litros
  por habitante con `wb.pop.ARG` de paises_extra.json), exportaciones (países, variedades, fraccionado/granel) y bodegas/viñedos.
  Los informes mensuales del INV son PDF y robots.txt de argentina.gob.ar prohíbe `/*.pdf$`: NO usarlos. Lo abierto va atrasado
  (consumo de un año entero, exportaciones parciales): cada número muestra su período. La serie IPI vino viene vacía (sacada).
- Surtidores (`#surtidores`, `vSu`, `renderSurtidores`, `loadSur`; pedido del dueño 01/11/2026). Desde el 02/11/2026 SOLO ventas
  (pedido del dueño): la Resolución 314/2016, que obligaba a cada estación a informar sus precios, se derogó en 06/2025 (Res.
  717/2025), así que la base de precios por estación ya no está completa ni al día; además datos.energia.gob.ar no responde ni
  desde Actions ni desde el Worker (522). Se sacaron buscador, provincias, marcas, localidades e historia de precios. Quedan:
  casilleros del último mes (súper, premium, gasoil, con la variación contra un año) y "Nafta en lo que va del año", ventas
  mensuales de los últimos 5 años, nafta vendida por año y parte premium (desde 2010: antes también había nafta común, que no
  está en estas series) y la nota de la derogación. Series de la API de series (miles de m³ = millones de litros):
  `38.3_NS_1994_M_11` súper, `38.3_NU_1994_M_11` premium, `41.3_GO_0_A_7` gasoil (solo desde 06/2025); `364.3_GNCGNC__3` GNC sin
  unidad confirmada: no se muestra. scripts/surtidores.py (workflow `surtidores.yml`) y `surtidores()` del Worker siguen
  intentando bajar los precios (cada 6 h, inofensivo); la página ya no los usa (`surtidores_est.json` quedó sin uso).
- Industria química (`#quimica`, `vQu`, pestaña `tabQu`, `renderQuimica`, `loadQu`; pedido del dueño 03/11/2026, "es un gran rubro"; datos
  `quimica.json` de scripts/quimica.py, workflow `quimica.yml` martes y viernes 9:41 ART): IPI manufacturero del INDEC por subclase
  (`453.2_*`: sustancias y productos químicos, básicos, agroquímicos, farmacéuticos, detergentes/jabones/cosmética, pinturas, gases,
  otros, materias primas plásticas y caucho sintético; nivel general `453.1_SERIE_ORIGNAL_0_0_14_46`), capacidad instalada química
  `31.3_USPQ_2004_M_34` vs general `31.3_UNG_2004_M_18`, Pink Sheet del Banco Mundial (urea, DAP, TSP, KCl, roca fosfórica, gas de EE.UU.
  y Europa, caucho) y Eurostat `sts_inpr_m` NACE C20 (química) y C21 (farma), 2021 = 100. Página: casilleros, química vs industria
  (promedio de 12 meses, 100 = 2016), ranking de rubros en lo que va del año, un rubro elegido (`quRub`, `#quSel`) con su interanual,
  capacidad, fertilizantes, gas y Europa. Descartado: producción física 41.3 de urea y caucho sintético (vacía en los últimos años,
  secreto estadístico), pinturas y jabones (unidad que no cierra con el IPI), caucho y plástico total y manufacturas de plástico (cortadas),
  IPIM químico (no está en la API), FRED (timeout desde Actions). Series de más de 7 meses no se publican.
  Insumos (pedido del dueño 03/11/2026: un amigo que trabaja en una química quería precios de hipoclorito, sulfónico, conservantes,
  soda cáustica y polietileno "por marca, proveedor y provincia": eso NO existe público (los proveedores cotizan por WhatsApp) y
  bajar MercadoLibre viola sus términos: el dueño quería hacerlo igual y se le dijo que no, por el plan legal del 26/10). Se hizo el
  precio de importación: scripts/insumos.py (mismo workflow `quimica.yml`) → `insumos.json` + `insumos_cache/AAAA.json` (años cerrados;
  `VERSION`). Fuente: zips públicos `comex.indec.gob.ar/files/zips/imports_AAAA_M.zip` (impomAA.csv: Año;mes;NCM;Porg;Pnet(kg);FOB;
  Flete;Seguro;CIF en US$), desde 2019; nombres oficiales de NCM y países de `comexbe.indec.gob.ar/public-api/search/{products,countries}`
  (un código que no aparece se descarta, `diag.sin_codigo`). Las exportaciones por NCM vienen con secreto ("s") en la petroquímica:
  no se usan. `PROD` = 19 insumos (limpieza, conservantes, plásticos). Precio = CIF total / kilos del mes; meses con < 10 t
  (`QI_MIN`) = "poco volumen" (hipoclorito de sodio casi no se importa: se hace acá). En la página, arriba de todo en Industria
  química: tabla "Cuánto cuesta traer cada insumo" (`renderInsumos`, filtro `qiGrupo`, en pesos al mayorista de hoy con `qiMay`)
  y ficha al tocar uno (`qiSel`, `#quFicha` con `display:contents`): precio desde 2019, toneladas 3 años, orígenes con precio por país.
  Agua blanda: no se compra (se hace en planta con resinas), la nota lo dice.
  Que nada se salga de las tarjetas (pedido del dueño 03/11/2026): en el ranking de rubros nombres cortos (`QU_CORTO`; hBars corta las
  etiquetas largas a la izquierda), "De dónde viene" es una lista propia `.qio` (no hBars: el texto de la barra más larga se salía a la
  derecha), en ≤640px la tabla `.qit` muestra solo insumo, US$/t y contra un año (lo demás en la ficha), unidades cortas (/t, t) y el
  interanual de "Un rubro" va en su propia tarjeta. Control: Playwright buscando elementos que pasen el borde de su `.card` en 360-1366 px.
- Mercado: ranking "¿Qué le ganó a la inflación?", Merval en $ y US$ CCL. Pedido del dueño ("quiero todas", "2 bonos es
  improvisado"): mapa de calor con TODAS las acciones (`renderStocks`, orden variación / más operadas / A-Z `stkOrd`; monto =
  `v` (CANTIDAD) × `c`), los 11 soberanos en dólares con TIR (`SOB`, `BDEF` → `BFLUJO`, `bondCalc(px, settle, k)`; cronogramas
  validados contra PPI 2/2/2026, ±0,1 pp) y "Todos los bonos y letras" (`renderBondsAll`, buscador `#bondQ`, monto =
  `v` × `c` / 100). Solo especie en pesos: `espPesos`/`enDolares` descarta D, C y .D aunque el nombre no siga la regla
  (BPOA7 → BPA7D, TZXA7 → TXA7D, BDC33 → BC33D) comparando precio × MEP/CCL; BA37D y SA24D sí son en pesos (respaldo: hoy
  cada especie trae `m`, la moneda que informa BYMA, y se usa `m === 'ARS'`). Precios cada minuto vía `vivo.json` del Worker
  (`MKT_MS`), que desde el 26/10/2026 los toma de Open BYMADATA (POST `.../bymadata/free/{leading-equity,general-equity,
  public-bonds,lebacs}` con `T1: true` y `page_size: 3000`; sin cookies; campos trade/closingPrice/imbalance/volume/
  numberOfOrders/bidPrice/offerPrice/denominationCcy) y ya vienen con los **20 minutos de demora** de BYMA: `tMkt` = ahora − 20 min.
  data912 NO se usa más (API anónima sin licencia). La página descarta precios con menos de 19 min. Leyenda: "precios de BYMA
  (Open BYMADATA) de las HH:MM · 20 minutos de demora". Los indicadores propios (`byma_bonos` en update.py) también usan BYMA.
- Merval: desde el 19/10/2026 es el "MSCI Merval" (antes S&P), base 100.000 al cierre del 16/10/2026. Ámbito (`indice/.merv`) y
  CNBC (`.MERV`) se cortaron el 16/10. update.py: fuente principal desde el 26/10 `byma_merval` (Open BYMADATA, acceso gratuito
  de BYMA: POST `.../bymadata/free/index-price`, símbolo `MMSCI`, previousClosingPrice y closingPrice/trade después de las 17 h;
  la historia por símbolo de esa API no trae índices). Respaldo: `rava_merval` saca los cierres desde el 19/10 de Rava
  (`rava.com/cotizaciones/historico/merval/AAAA/MM/` lista los días; cada día trae los últimos 10 cierres) y la historia de
  Ámbito se re-expresa con `MERVAL_FACTOR` (= 100.000 / 2.843.310,56); lo guardado en la base vieja (>500.000) se convierte
  solo. En la página se llama "Merval" (no "S&P Merval"); el gráfico del Mundo usa data.json (`gSerie('merv')`).
  "En el día" solo si el dato tiene ≤ 4 días (`fresco`/`enDia`); si no, se muestra la fecha.
- Indicadores propios (scripts/propios.py, plan legal 26/10/2026): MEP Pulso Macro = AL30 ÷ AL30D, CCL = AL30 ÷ AL30C (si falta,
  GD30), riesgo país Pulso Macro = promedio de (TIR de Globales con duración ≥ 3 años − Tesoro de EE.UU. interpolado a esa
  duración, de usa.json), en pb. Misma TIR que la página (validada idéntica). update.py los guarda SOLO en la corrida de la
  tarde de días hábiles (`propios_cierre`, ≥17 h) como `mep_pm`, `ccl_pm`, `riesgo_pm` en `diario`. Primero se comparan unos
  días contra Ámbito/EMBI (26/10: MEP 1.564 vs 1.562; riesgo 648 vs EMBI ~707) y recién después se muestran en la página.
- Noticias: `noticias.json` (scripts/noticias.py, 72 h, hasta 900). Pedido del dueño 02/11/2026: muchas más, de economía y alrededor
  (negocios, finanzas, política). `FUENTES` = medio → secciones → direcciones alternativas (la primera que ande): Ámbito, Infobae,
  La Nación, iProfesional, Perfil (`/feed/economia` da 404 desde 10/2026: Reperfilar), Clarín, El Economista y TN (Página/12 da 404 y
  el RSS de El Cronista viene roto: sacados); `RUIDO` saca deportes, espectáculos y policiales; tema `politica` en el filtro (`NWT`). Pedido del dueño 02/11/2026: tarjetas
  con foto como la portada de Edge (`.nwg`/`.nwc`, `grid-auto-flow:dense`; `nwTam`: la primera de cada día grande y, desde la 4.ª,
  ~13% grandes 2×2 y ~17% anchas `.wide` (2 columnas, foto al costado), al azar fijo por link; 2 columnas en celular; sin foto,
  las iniciales del medio). Solo en estas noticias generales: las de cada país siguen como lista. Foto `i`: la del feed
  (media:content/thumbnail/enclosure/<img>), achicada a 560 px en el resizer de Arc (Infobae, La Nación; se prueba con una
  antes de cambiarlas) y, si el feed no trae (Ámbito), og:image de la nota (con robots.txt, hasta 40 por corrida, se guardan).
  Las fotos se ven directo desde el medio (`referrerpolicy=no-referrer`); el link lleva a la nota.
- Ajuste por IPC (calculadora `alq`, `#cALQ`, `calcAlq`, pedido del dueño 26/10/2026: inmobiliarias que actualizan alquileres):
  monto inicial, mes de inicio, cada cuántos meses, duración y qué meses toma (`alL`: 2 = últimos publicados al ajustar,
  lo común; 1 = del período). Cociente de índices del IPC nacional nivel general (`act.ipc` desde dic-2016, de la tanda
  `ipc_largo` de actividad.py; si falta, `act.general` desde 2022) completado con `months[].infl` del BCRA para los meses que
  datos.gob.ar todavía no cargó (marcados con *). Tabla con qué meses usa cada ajuste, fila vigente resaltada, ajustes sin
  IPC publicado como "pendiente", botones copiar (tabulado) y descargar CSV. `.card` y `.calc` con columna `minmax(0,1fr)`: sin eso, al girar el celular el contenido quedaba más ancho que la tarjeta.
- Simulador de inversión histórica (pedido del dueño 26/10/2026; en Calculadoras `calc='sim'` → `#cSIM` y en Bolsa y bonos
  debajo del mapa de calor `#kSIM`; una sola lógica `simRender(p)`/`simCalc(p)`, `data-sim` = prefijo de ids): activo
  (TODAS las acciones y CEDEARs en pesos de los paneles de BYMA + 11 soberanos + Merval, con buscador `simBuscador`:
  ticker o nombre, sin tildes; vacío muestra `SIM_POP`), fecha y monto → valor hoy, rendimiento en pesos, contra la inflación
  (CER) y en dólares MEP, comparación con MEP/inflación/Merval/SPY y gráfico. Arranca en dólares (`data-cur`, selector
  `#{p}sCur`, pedido del dueño: "la mayoría no invierte en pesos"): US$ → pesos al MEP del día de compra → activo → dólares al
  MEP de hoy; contra la inflación de EE.UU. (`cpiAt`, BLS de usa.json) y rendimiento por año (si hay ≥180 días). Datos: `historia.json` = índice (fechas, `mep`, `cer`, `info` {t, n, f0}) y
  `historia/<TICKER>.json` = {d, c} por activo, que la página baja al elegirlo (`simSerie`, alineado a `HIS.fechas`); los nombres
  salen de `NOMBRES` en el robot (BYMA no los manda). Robot (scripts/historia.py,
  workflow `historia.yml` L a V 18:35 ART): Open BYMADATA `chart/historical-series/history?symbol=GGAL%2024HS` (solo da ~2
  años: arranca el 28/10/2024; el robot ACUMULA lo viejo de la corrida anterior, escalándolo para empalmar; los que ya
  tienen archivo piden solo 45 días, los nuevos todo; tope 32 min por corrida, lo que falta sigue al otro día), índice
  `chart/index-historical-series/history?symbol=M` (S&P Merval × `MERVAL_FACTOR`; desde el 19/10/2026 el MSCI de
  data.json), MEP propio AL30/AL30D (o GD30) y CER BCRA (serie 30). Variantes de la misma especie (AAPLB, BMA.B, KO..B, MOLA5, ON con F) no se piden ni se muestran (`variante`); orden de pedido: los más buscados, los que ya tienen archivo y los que tienen nombre (así un corte por tiempo deja afuera solo lo raro). Sin buscar, la lista muestra los más buscados y TODOS por tipo (pedido del dueño: "que se vea que están todas"); en el celular se elige con el toque (click), no al apoyar el dedo, para poder deslizar la lista. En Bolsa y bonos el simulador no se recalcula con cada precio en vivo. Con un salto de >45 % en un día (split, cambio de ratio de CEDEAR) se guarda solo desde el salto (`desde_ultimo_salto`). Bonos: la historia de BYMA viene ajustada por ALGUNOS pagos y por otros no (AL30: el de 01/2025 sin
  ajustar, los siguientes ajustados): `simCalc` mira si el precio en dólares cayó en cada fecha de pago (BFLUJO) y solo
  suma lo cobrado (al MEP de ese día, sin reinvertir) cuando cayó. `HIS` se declara arriba de todo (TDZ: renderMercado
  corre al arrancar).
- Calculadoras (pedido del dueño: siempre abre en la primera, `calc='sim'` en `setTab`; no se guarda la última). Orden pedido por el dueño: Simulador, Inflación, De viaje, Sueldo en dólares, Ajuste por IPC, ¿Plazo fijo o dólar?. Plazo fijo vs dólar, inflación (CER), sueldo en dólares y de viaje (`calcVia`, `VIA`: 12 monedas con
  cotización de `global.json`/`global_hist.json`; tarjeta, MEP, blue y cripto; "hace un año" con MEP mensual y CER).
- Términos y aviso legal: DENTRO de Sobre Pulso Macro (pedido del dueño: "que esté todo en Sobre"), debajo de Aclaraciones:
  `h3#legal` + `details.legal` desplegable. El link del pie (`[data-legal]`) abre Sobre, despliega y baja hasta ahí.
  `legal/index.html` solo redirige a `/#sobre` (noindex). Incluye cómo pedir corrección o retiro de un dato.
- Sobre Pulso Macro: contenido estático en el HTML (`vS`). No cambiar su texto sin que lo pida el dueño. Sin foto del dueño (la sacó el 01/11/2026; `foto.jpg` borrado) ni la línea "Invierto en la bolsa desde los 17 años" (sacada el 02/11/2026). Contacto: arriba primero el mail
  y después LinkedIn; en "Aclaraciones" y el resto de los avisos, solo el mail y siempre en tercera persona (nunca "escribime").

### Apartados dentro de Mundo y Estados Unidos
- Barra `.subtabs` (`#gSubM`, `#gSubU`) y bloques `.gsub[data-sub]`; `SUBS`, `aplicarSub`, `setSub`. Pedido del dueño: NO se
  recuerda el último apartado; al entrar a una sección siempre arranca en el primero (`SUBS_DEF`, se resetea en `setTab`). Pedido del dueño: los menos apartados posibles, lo coherente junto.
- Mundo: arriba SIEMPRE los dos globos (no sacarlos de ahí). Apartados: Bolsas y acciones (reloj, bolsas, termómetro,
  Argentinas en WS, Líderes, gráficos, ¿qué rindió más?, cripto) · Economías y tasas (comparador de países `renderComparador`, `CMP_P`:
  12 países con el último dato de cada sección; ficha del país, ¿dónde está
  Argentina?, agenda y tasas de bancos centrales, bonos) · Commodities y monedas · Noticias · Explorador (solo compu). Tocar un país del globo
  lleva a Economías y tasas, a la ficha. Tocar un commodity lleva a Bolsas y acciones, al gráfico.
- Estados Unidos: arriba SIEMPRE mapa, deuda, Fed y los 6 indicadores. Apartados: Economía (semáforo, rubros, próximos
  datos, empleos, mercado laboral, PBI) · Tasas y deuda (Fed vs inflación, curva, decisiones, hipotecaria) · Wall Street
  (mapa del S&P 500, sectores y 7 magníficas: widgets de TradingView; sin balances desde el 26/10/2026).

### Brasil (`#brasil`, sección `vB`, `renderBrasil`, datos `brasil.json` de scripts/brasil.py en `global.yml`)
- Arriba siempre 6 indicadores: real por dólar (PTAX), un real en pesos (mayorista de data.json ÷ PTAX del mismo día),
  Selic con cuenta regresiva al Copom (`BCAL` BRA), IPCA 12 meses, desempleo y Bovespa. Apartados (`#gSubB`, `SUBS.B`):
  Economía (IPCA mensual, IBC-Br interanual, desempleo, reservas) · Tasas y expectativas (Selic vs IPCA, decisiones del
  Copom sacadas de los cambios de la Selic, encuesta Focus) · Mercados y el real (PTAX, real en pesos, Bovespa, acciones).
- Fuentes: BCB SGS `api.bcb.gov.br/dados/serie/bcdata.sgs.{código}/dados` (432 Selic meta: viene cargada hasta la próxima
  reunión, se cortan fechas futuras; 1 PTAX; 433/13522 IPCA; 24363 IBC-Br sin desestacionalizar, el 24364 falla; 24369
  desempleo; 13621 reservas) y Focus (`olinda.bcb.gov.br/.../ExpectativasMercadoAnuais`). El BCB a veces da 502: se reintenta.

### Zona euro (`#europa`, sección `vE`; en el menú se llama "Zona euro" para no confundirse con Polonia y Reino Unido, `renderEuropa`, datos `europa.json` de scripts/europa.py en `global.yml`)
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
  CPI 771/628; OCDE COL/TUR). `BCAL` COL solo con fechas de 2026 (cargar 2027 cuando el BanRep las publique); TUR hasta jun-2027 (el TCMB publica
  el año en curso y el primer semestre del siguiente: cargar jul-dic 2027 cuando salgan).
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
- Probado y descartado por falta de datos gratis al día: Uruguay (BIS no tiene tasa ni inflación; el BCU y el INE no
  responden desde Actions). India sí se pudo (10/2026: el BIS ya tiene su tasa; desempleo anual del Banco Mundial).


### Polonia (`#polonia`, sección `vPl`, `renderPolonia`, `SUBS.L`, datos `polonia.json` de scripts/polonia.py en `global.yml`)
- Pedido del dueño (segunda nacionalidad): sección completa. Fuentes sin clave: BIS (WS_CBPOL D.PL, WS_LONG_CPI M.PL.771/.628),
  NBP `api.nbp.pl/api/exchangerates/rates/a/{usd|eur}/{desde}/{hasta}` (zloty oficial, máximo 367 días por pedido: se pide en
  tramos), OCDE (POL), BCE `IRS/M.PL.L.L40.CI.0000.PLN.N.Z` (bono a 10 años mensual: CNBC NO tiene PL10Y/PL2Y) y Banco Mundial
  (`wb`: PBI por habitante PPA `NY.GDP.PCAP.PP.KD` y crecimiento anual de POL, ARG y EUU desde 1990; se renueva cada 7 días).
- CNBC: `PLN=`, `EURPLN=`, `EPOL` (`global.json → polonia`); la cotización de `.WIG20` viene vacía pero la historia sí
  (`global_hist → wig20`): el indicador de arriba sale de los dos últimos cierres. `BOLSAS.GPW` queda por si CNBC lo agrega.
- Arriba: zloty por dólar, un zloty en pesos, tasa del NBP con cuenta regresiva (`BCAL` POL: decisión el 2.º día de cada
  reunión; PENDIENTE: cargar 2027 cuando el NBP publique el calendario), inflación, desempleo y WIG20.
- Economía abre con "Polonia y Argentina desde 1990" (PBI por habitante PPA con la UE y el año desde el que Polonia quedó
  siempre adelante) y "Crecimiento de cada año". Mercados: zloty/dólar, zloty/euro, zloty en pesos, WIG20 y EPOL.
- También en: comparador (`CMP_*` POL), "¿Dónde está Argentina?", bancos centrales, reloj de mercados (GPW, Varsovia),
  monedas, calculadora de viaje (PLN), Monitor y la página `/zloty-en-pesos/`.

### India y Arabia Saudita (`#india` `vIn` `renderIndia` `SUBS.I`; `#arabia` `vSa` `renderArabia` `SUBS.A`)
- Robots `scripts/india.py` y `scripts/arabia.py` sobre la base común `scripts/pais_bis.py` (`armar`: BIS tasa/moneda/IPC,
  OCDE desempleo/PBI si los hay y, de respaldo, Banco Mundial anual `desemp_anual`/`crec_anual`; descarta lo atrasado).
  En la página, piezas comunes `pb*` (`pbFx`, `pbInfl`, `pbPbi`, `pbDes`, `pbTasa`, `pbDat`, `pbBolsa`) y `PB_D`/`loadPB`.
  Un país nuevo con solo BIS/OCDE/Banco Mundial se arma igual: un .py de 5 líneas con `armar(...)` y estas piezas.
- India: rupia (`INR=`, historia `fx_inr`), cien rupias en pesos, RBI (`BCAL` IND, anuncio 10:00 IST; PENDIENTE: cargar
  las reuniones de 2027-28 cuando el RBI las publique), Nifty 50 (`bolsas.NSE`, historia `nifty`), bono `bonos.IND` (`in10`),
  ADR `acciones.ind`, fondo `india.inda`. Noticias: en español casi no hay; medios indios en inglés (Economic Times, Mint,
  Business Standard, Hindu BusinessLine).
- Arabia Saudita: riyal fijo 3,75 desde 1986; el SAMA mueve la tasa con la Fed (su cuenta regresiva usa `BCAL` USA). Brent
  (`commodities` brent, historia `brent`), fondo KSA (`arabia.ksa`, historia `ksa`); el Tadawul (`.TASI`, historia `tasi`)
  se usa si CNBC lo trae. Noticias: Saudi Gazette, Argaam y Al Jazeera (inglés; Arab News da 403 desde Actions). CNBC no trae historia de IN10Y.

### Suiza (`#suiza` `vSz` `renderSuiza` `SUBS.Z`, datos `suiza.json` de scripts/suiza.py, misma base `pais_bis.py`)
- BIS CH (tasa del BNS, CHF, IPC), OCDE/Banco Mundial CHE. `BCAL` CHE (anuncio 9:30 de Zúrich; fechas oficiales hasta
  dic-2027). CNBC: `CHF=`, `EURCHF=`, `EWL` (`global.json → suiza`), SMI (`bolsas.SIX`, historia `smi`), bono `bonos.CHE`
  (historia `ch10`), ADR `acciones.che`. Noticias en inglés: The Local, Le News y finews.ch; el RSS de Swissinfo da 410. Bolsa SIX en `GEX`.

### Australia (`#australia` `vAu` `renderAustralia` `SUBS.W`, datos `australia.json` de scripts/australia.py, base `pais_bis.py`)
- BIS AU (tasa del RBA, moneda, IPC), OCDE/Banco Mundial AUS. Ojo: el BIS da A$ por dólar y CNBC `AUD=` da US$ por A$; en
  la página se usa siempre US$ por dólar australiano (como se cotiza allá; `CMP_FX` y `monY` con inversión). El IPC del BIS
  es trimestral (repite el valor 3 meses): "Inflación de cada trimestre". `BCAL` AUS (anuncio 14:30 de Sídney; fechas
  oficiales del RBA hasta dic-2027). CNBC: `EWA` (`global.json → australia`), S&P/ASX 200 (`bolsas.ASX`, historia `asx`),
  bono `bonos.AUS` (`au10`), ADR `acciones.aus` (BHP, RIO, WDS, JHX, TEAM). Noticias: ABC, Guardian Australia y The
  Conversation (inglés; SBS da 404).

### Corea del Sur y Sudáfrica (`#corea` `vKr` `renderCorea` `SUBS.Q`; `#sudafrica` `vZa` `renderSudafrica` `SUBS.S`)
- Robots `scripts/corea.py` y `scripts/sudafrica.py` (base `pais_bis.py`). Corea: won (`KRW=`, `fx_krw`), mil wones en pesos,
  KOSPI (`bolsas.KRX` `.KS11`, historia `kospi`; KRX Seúl en `GEX`), bono `kr10`, `EWY`, ADR `acciones.kor`. `BCAL` KOR solo
  2026-11-26 (PENDIENTE: cargar 2027 cuando el Banco de Corea publique el calendario; anuncio ~10:00 de Seúl, aproximada).
- Sudáfrica: rand (`ZAR=`, `fx_zar`), JSE Top 40 (`.JTOPI`: la cotización viene vacía pero la historia `jse` sí; el
  indicador sale de los dos últimos cierres), bono `za10`, `EZA`, ADR `acciones.zaf`. Desempleo: solo anual del Banco
  Mundial (la OCDE no lo tiene). `BCAL` ZAF con fechas oficiales del SARB hasta nov-2027 (anuncio ~15:00, aproximada).
- Noticias en inglés: Korea Herald (`kh_Business`), Korea Times; Moneyweb, Daily Maverick (`/dmrss/`), IOL. Yonhap da 404,
  BusinessTech 403 y JoongAng Daily bloquea. En inglés hay pocas: algunos días quedan menos de 10.

### Nueva Zelanda e Indonesia (`#zelanda` `vNz` `renderZelanda` `SUBS.N`; `#indonesia` `vId` `renderIndonesia` `SUBS.Y`)
- Robots `scripts/zelanda.py` e `scripts/indonesia.py` (base `pais_bis.py`). Nueva Zelanda se armó como Australia: US$ por
  dólar neozelandés (CNBC `NZD=`, `fx_nzd`; el BIS viene al revés) e IPC trimestral. NZX 50 (`bolsas.NZX` `.NZ50`, historia
  `nzx`), bono `nz10`, `ENZL`. `BCAL` NZL solo hasta dic-2026 (PENDIENTE 2027: las fuentes no coinciden; anuncio 14:00 de
  Wellington). Indonesia: rupia (`IDR=`, `fx_idr`), mil rupias en pesos, Jakarta Composite (`bolsas.IDX` `.JKSE`, historia
  `jkse`), bono `id10`, `EIDO` y `TLK`. `BCAL` IDN con el calendario oficial de 2026 (PENDIENTE 2027; anuncio ~14:30 de
  Yakarta, aproximada). Desempleo de los dos: anual del Banco Mundial. NZX y IDX en `GEX`.
- Noticias en inglés: RNZ y NZ Herald; Antara (`business-investment.xml` y `news.xml`). Jakarta Post 404, Jakarta Globe 403.

### Noruega, Suecia, Tailandia, Malasia y Filipinas (`#noruega` `vNo` `SUBS.G`; `#suecia` `vSe` `SUBS.V`; `#tailandia` `vTh` `SUBS.H`; `#malasia` `vMy` `SUBS.F`; `#filipinas` `vPh` `SUBS.D`)
- Robots `scripts/{noruega,suecia,tailandia,malasia,filipinas}.py` (base `pais_bis.py`); en la página, mismo armado que
  Corea (`render{Pais}`), con la lista de fondos y ADR en `#{pre}Ws` en vez del mapa de calor. Bolsas: `bolsas.OSE`
  (`.OSEBX`, historia `osebx`), `OMX` (`.OMXS30`, `omxs30`), `SET` (`.SETI`, `seti`), `KLSE` (`.KLSE`, `klci`), `PSE` (`.PSI`,
  `psei`); fondos NORW, EWD, THD, EWM, EPHE; ADR EQNR, ERIC, SPOT, PHI. Bonos: CNBC trae SE10Y-SE y TH10Y; los de Noruega,
  Malasia y Filipinas no (la tarjeta se oculta sola si no hay bono ni historia).
- `BCAL`: NOR (oficial hasta dic-2027, 10:00 Oslo), SWE (hasta mar-2027, 9:30 Estocolmo), THA (2026, ~14:00 Bangkok),
  MYS (5/11/2026, 15:00 Kuala Lumpur). PENDIENTE: completar 2027 de SWE, THA y MYS cuando se publiquen. Filipinas no tiene:
  `VIVO.D.nocal` muestra el aviso. Bolsas OSE, OMX, SET, KLSE y PSE en `GEX`.
- La OCDE corta con 429 si se le pide mucho seguido. En 10/2026 esperar y reintentar hizo pasar `global.yml` de los 20 min
  y se perdió la corrida entera: ahora `pais_bis` NO reintenta ante 404/429, deja de pedirle a la OCDE en esa corrida
  (`OECD_CORTADA`) y queda el dato anterior. Tailandia, Malasia y Filipinas no están en la OCDE (`armar(..., None, ...)`).
  Cada paso de país tiene `timeout-minutes: 3` y el trabajo entero 25.
- Noticias en inglés: News in English y The Local (Noruega), Radio Sweden (Atom de api.sr.se) y The Local (Suecia),
  Bangkok Post y Khaosod English, Free Malaysia Today y Malay Mail, Inquirer, BusinessWorld y Philstar. The Nation y The Star
  dan 404. Noruega y Suecia tienen pocos titulares de economía en inglés.

### Islandia, Hungría, Hong Kong, Chequia, Dinamarca y Rumania (`#islandia` `vIs` `SUBS.IS`; `#hungria` `vHu` `SUBS.HU`; `#hongkong` `vHk` `SUBS.HK`; `#chequia` `vCz` `SUBS.CZ`; `#dinamarca` `vDk` `SUBS.DK`; `#rumania` `vRo` `SUBS.RO`)
- Robots `scripts/{islandia,hungria,hongkong,chequia,dinamarca,rumania}.py` (base `pais_bis.py`; Hong Kong y Rumania sin OCDE).
  Mismo armado que Noruega (`render{Pais}`); claves de `SUBS` de dos letras. Bolsas: `ICEX` (`.OMXI15`, historia `omxi`),
  `BUX` (`bux`), `PSE_CZ` (`.PX`, `pxi`), `CPH` (`.OMXC20`, `omxc`; la historia de .OMXC25 viene vacía), `BVB` (`.BETI`: la
  cotización viene vacía y sale de la historia `bet`), Hang Seng (`HKEX`, `hsi`). Fondos EWH y EDEN (+ NVO). Bonos: CNBC trae
  HU10Y, HK10Y (sin historia) y la historia de DK10Y; Islandia, Chequia y Rumania no (la tarjeta se oculta).
- `BCAL`: ISL (8:30 Reikiavik), HUN (14:00 Budapest), CZE (oficial, 14:30 Praga), ROU (~15:00 Bucarest), solo lo publicado de
  2026-27 (PENDIENTE: completar 2027). Hong Kong sigue a la Fed (caja de conversión 7,75-7,85) y Dinamarca al BCE (mismo día):
  su cuenta regresiva usa `BCAL` USA y DEU. Bolsas ICEX, BUX, BCPP, CPH y BVB en `GEX`.
- Noticias en inglés: Iceland Monitor y RÚV; Hungary Today y Daily News Hungary; HKFP y RTHK; Prague Morning y Brno Daily;
  The Local y Copenhagen Post; Romania Insider y Brno Daily (a veces 429) y Business Review; Chequia y Rumania quedan con pocos titulares. Dan error desde
  Actions: Iceland Review y BBJ (403), Radio Prague y Expats.cz (404), The Standard HK y Universul (XML roto), Romania Journal (403).

### Israel y Serbia (`#israel` `vIl` `renderIsrael` `SUBS.IL`; `#serbia` `vRs` `renderSerbia` `SUBS.RS`)
- Robots `scripts/israel.py` y `scripts/serbia.py` (base `pais_bis.py`; Serbia sin OCDE). Mismo armado que Noruega.
  Israel: séquel (`ILS=`, `fx_ils`), TA-35 (`bolsas.TASE` `.TA35`, historia `ta35`), `EIS`, TEVA y CHKP (`global.json → israel`).
  El IPC de Israel en el BIS llega con ~4 meses de atraso. `BCAL` ISR con el calendario oficial del Banco de Israel hasta
  nov-2027 (anuncio 16:00 de Jerusalén). TASE opera de lunes a viernes desde 2026.
- Serbia: dinar (`RSD=`, `fx_rsd`), cien dinares en pesos. CNBC no trae el BELEX15 ni bonos de Serbia (ni IL10Y con historia):
  la tarjeta y el casillero de la bolsa no aparecen. `BCAL` SRB solo 12/11 y 10/12/2026 (Trading Economics; anuncio ~11:00
  de Belgrado, aproximada; PENDIENTE 2027). Noticias en inglés: Globes (The Times of Israel da 403); Serbian Monitor, N1 English y
  Balkan Insight.

### China y Rusia (`#china` `vCn` `renderChina` `SUBS.CN`; `#rusia` `vRu` `renderRusia` `SUBS.RU`)
- Pedido del dueño (China estaba descartada y la pidió en 10/2026). Robots `scripts/china.py` y `scripts/rusia.py` (base
  `pais_bis.py`, sin OCDE). China ya estaba en varias tablas del Mundo (BC, DG_*, XP_*, monedas): el generador no la duplicó.
  China: la "tasa" del BIS es la LPR a 1 año (`BCAL` CHN: día 20 de cada mes o el hábil siguiente, 9:00 de Pekín, aproximada,
  cargada hasta dic-2027), Shanghái Compuesto (`bolsas.SSE`, historia `shanghai`), bono `cn10`, FXI, BABA, PDD y BIDU.
- Rusia: rublo (`RUB=`, `fx_rub`), tasa del Banco Central de Rusia (`BCAL` RUS oficial 2026, 13:30 de Moscú; PENDIENTE
  2027). CNBC no trae el MOEX ni bonos rusos: esas tarjetas no aparecen. Noticias: South China Morning Post y CGTN; The
  Moscow Times (además de los medios en español).

### España, Macedonia del Norte, Singapur y Marruecos (`#espana` `vEs` `SUBS.ES`; `#macedonia` `vMk` `SUBS.MK`; `#singapur` `vSg` `SUBS.SG`; `#marruecos` `vMa` `SUBS.MA`)
- Robots `scripts/{espana,macedonia,singapur,marruecos}.py` (base `pais_bis.py`; solo España está en la OCDE). Eran los únicos
  que quedaban con tasa e inflación del BIS al día (el BIS también tiene Kuwait).
- España: tasa del BCE (BIS `XM`, `extra` en el robot); en la página va en dólares por euro (como se cotiza allá: BIS
  invertido + `fx_eur` de CNBC) y "un euro en pesos" = mayorista × dólares por euro; cuenta regresiva con `BCAL` DEU. IBEX 35
  (`bolsas.BME`, historia `ibex`), bono `es10`, EWP, SAN, BBVA y TEF. Noticias en español ("pais" en los medios de España).
- Singapur: la MAS no fija tasa (maneja el S$ en una banda): no hay tasa en el BIS, el casillero dice "Sin tasa" y las
  tarjetas de tasa se ocultan; el apartado se llama "Bonos y crédito". `BCAL` SGP 29/01/2027 (aproximada). STI (`bolsas.SGX`,
  historia `sti`), bono `sg10`, EWS, SE y GRAB. Noticias: CNA, The Straits Times y The Business Times. España: Cinco Días y Expansión como medios propios ("econ"). Morocco World News da 403 y MIA (Macedonia) no responde; Macedonia usa Meta.mk y Balkan Insight.
- Marruecos: el BIS trae tasa y dirham con atraso (se aceptan 3 meses; el dirham de hoy sale de CNBC `fx_mad`). MASI (la
  cotización viene vacía, sale de la historia `masi`). `BCAL` MAR 15/12/2026 (aproximada). Macedonia: denar atado al euro, MBI10
  (historia `mbi10`), `BCAL` MKD 3/11 y 22/12/2026 (aproximadas). PENDIENTE 2027 de MAR, MKD y SGP.

### Alemania, Francia, Italia, Países Bajos y Grecia (`#alemania` `vDe` `SUBS.DE`; `#francia` `vFr` `SUBS.FR`; `#italia` `vIt` `SUBS.IT`; `#paisesbajos` `vNl` `SUBS.NL`; `#grecia` `vGr` `SUBS.GR`)
- Sumados el 08/11/2026 (el dueño pidió "los 5 que mejor vayan a quedar"; se eligieron países del euro porque son los que tienen
  todo al día gratis: BIS, OCDE, bonos y bolsa de la OCDE). Clonados de España: robots `scripts/{alemania,francia,italia,paisesbajos,grecia}.py`
  (base `pais_bis.py`, tasa del BCE con BIS `XM`), `render{Alemania,Francia,Italia,PaisesBajos,Grecia}` con el mismo armado que
  `renderEspana` (dólares por euro, un euro en pesos, cuenta regresiva con `BCAL` DEU). Cada uno con su texto de entrada propio.
- global.json: `alemania` (EWG, SAP, DB), `francia` (EWQ, TTE, SNY), `italia` (EWI, RACE, STLA), `paisesbajos` (EWN, ASML, ING, PHG),
  `grecia` (GREK). Bolsas nuevas en `BOLSAS`/`BOLSA_ISO`/`GEX`: `BIT` (Milán, FTSE MIB con CAPITALCOM:IT40), `AEX` (Ámsterdam,
  EURONEXT:AEX) y `ATHEX` (Atenas, sin símbolo de TradingView: la tarjeta del índice no aparece, el casillero sale de la OCDE).
  Alemania y Francia usan `Xetra` y `Euronext` (DAX, CAC 40). Bonos NLD y GRC de la OCDE (`nl10`, `gr10`).
- Símbolos de TradingView sin probar desde acá (EWG, EWQ, EWI, EWN, GREK, EURONEXT:AEX): si alguno muestra "!", buscar el correcto.
- Noticias: medios en español con regla "pais" + en inglés The Local (de, fr, it), NL Times, DutchNews, Greek Reporter y Euronews por país (tag). Kathimerini da 403 desde Actions.

### "En vivo" en todas las secciones de país (`VIVO`, `vvMount`, `vvTick`; pedido del dueño)
- Franja `.vivo` arriba de los apartados (la arma `aplicarSub`): cuenta regresiva a la próxima decisión del banco central
  (fecha de `BCAL` + hora del anuncio en la zona del banco; las marcadas 1 son aproximadas), hora del país con el estado de
  su bolsa (`GEX`; se sumaron Borsa İstanbul, BCS Santiago, BVC Bogotá y BVL Lima), habitantes estimados ahora y "mientras
  mirás esta página" (PBI en dólares por segundo, contra Argentina). Población y PBI: Banco Mundial (`wb.pop`, `wb.popc`,
  `wb.pbiusd` en paises_extra.json). Un solo `setInterval` de 1 s que se corta si la franja no está a la vista.
  En EE.UU. no va la cuenta regresiva (ya está la de la Fed arriba); Perú no tiene calendario fijo del BCRP.

### Datos que se suman a todos los países (`paises_extra.json` de scripts/paises_extra.py en `global.yml`; `pxRender`, `PX_ISO`)
- Pedido del dueño ("los países se ven vagos al lado de Argentina"). Un solo robot para los 44 países + Argentina; `pxRender(k)` se
  llama desde `aplicarSub` y agrega tarjetas en un `.pxw` al final del apartado (sin tocar el HTML de cada país).
- Economía: "{país} y Argentina desde 1990" y "Crecimiento de cada año" (Banco Mundial, `wb.ppa`/`wb.crec`; Polonia ya
  tiene las suyas), inflación por rubro (OCDE `DF_PRICES_ALL`: CP01 alimentos, CP045_0722 energía, _TXCP01_NRG núcleo;
  no en EE.UU., que tiene la del BLS; en 10/2026 la OCDE solo estaba al día para Reino Unido y Colombia: el resto quedó en
  2021-2025 y se descarta por atrasado, ver `diag.rubros_ult`), industria y comercio (OCDE `DF_KEI`: PRVM y TOVM, GY), termómetro (OCDE `DF_CLI`
  4.1: CCICP, BCICP y LI ajustados por amplitud, 100 = promedio; la versión de `DF_KEI` viene en saldos con escalas
  distintas y NO sirve), precio de las viviendas (BIS `WS_SPP` R/N .771, trimestral) y cuenta corriente (Banco Mundial).
- Tasas: crédito al sector privado % PBI (BIS `WS_TC` P.A.M.770.A; Perú no tiene). Mercados (en EE.UU., Wall Street):
  tipo de cambio real (BIS `WS_EER` M.R.B, 2020 = 100) contra Argentina e índice Big Mac (GitHub TheEconomist/big-mac-data).
- La OCDE no se puede leer con WebFetch (devuelve binario): se prueba desde Actions mirando el campo `diag` del JSON.

### Global › Mundo
- OJO: las notas de cada país más arriba nombran símbolos de CNBC (`bolsas.X`, `.OSEBX`, fondos) de cuando se usaba CNBC.
  Desde el 26/10/2026 eso lo muestran los widgets de TradingView y los números propios salen de la OCDE: ver "Mercados sin
  CNBC" en Fuentes. La capa "bolsas" de los globos, el Monitor y "¿Qué rindió más?" usan la OCDE (mensual).
- Merval en Bolsa y bonos: parte de cierre como noticia (`#merParte` arriba de los indicadores: "El MSCI Merval cerró el ... Fuente: BYMA / MSCI").
- Atribución de los widgets de TradingView: el texto original "Track all markets on TradingView" (sus términos piden no cambiarla).
- Dos globos: países (`gInit/gDraw`, capas inflación/crecimiento/tasa/desempleo, ficha vs Argentina; mapa plano si
  `innerWidth<560`) y "Mundo hoy" de puntos (`dgStart/dgDraw/dgDots/dgItems`; capas bolsas en el mes (mensual de la OCDE: el botón ya no dice "hoy"), monedas hoy, monedas en
  el año, bonos a 10 años; el texto de la capa `#dHud` va arriba del globo, no encima, y las etiquetas que se pisan no se escriben). d3 7.8.5 y topojson 3.0.2 copiados en `vendor/` (no dependen de cdnjs), solo al abrir la pestaña. Mapa `world.json`.
- Reloj de mercados 24 h (`renderReloj`, `gEstado`, `gProx`, lista `GEX` sin feriados).
- `gMundoExtra`: ¿Dónde está Argentina? (`DPA`, países `DPA_P`), agenda de bancos centrales (`BCAL`, fechas de anuncio
  cargadas a mano hasta dic-2027; Banxico y Colombia solo 2026, Turquía hasta jun-2027: completar cuando publiquen), bonos a 10 años vs EE.UU.
  (Argentina = riesgo país), cripto top 10, noticias del mundo.
- `gExtras`: bolsas, bancos centrales (BIS), commodities (9, con variación en el año y clic al gráfico), Argentinas en
  Wall Street, Líderes del mundo, gráficos (widget `GTV`), "¿Qué rindió más en el año?", monedas, termómetro (estrés OFR, 10-2).

### Global › Mundo › Geopolítica (`data-sub="geo"`, `renderGeo`, datos `geopolitica.json` de scripts/geopolitica.py en `global.yml`)
- Pedido del dueño ("que se puedan ver todas las guerras del mundo"), con foco económico. Robot (necesita `pip install xlrd`):
  - Conflictos: Wikipedia "List of ongoing armed conflicts" por la API `action=parse` (CC BY-SA 4.0; parser propio `Tablas` +
    `grilla` para rowspan): 4 niveles (mayor 10.000+, menor 1.000-9.999, conflicto 100-999, choque <100), países (ISO3 con la
    lista del Banco Mundial + alias), muertes por año. Nombres en español a mano (`TRAD`; los nuevos van a `diag.sin_traducir`)
    y enlace a Wikipedia en español si existe (`wes`). La tabla "Deaths by country" de esa página es un ranking viejo: NO usar.
  - Índice de riesgo geopolítico (Caldara e Iacoviello): `gpr_files/data_gpr_daily_recent.xls` (diario, los lunes) y
    `data_gpr_export.xls` (mensual, `GPRH` desde 1900 y `GPRC_xxx` de 44 países, Argentina incluida).
  - Gasto militar del Banco Mundial (SIPRI), % del PBI y dólares, cada 7 días. Defensa en `global.json → defensa` (ITA, LMT,
    NOC, RTX, GD, LHX, Rheinmetall en euros, BAE en peniques) e historia `ita`.
- Página: mapa (d3 Natural Earth sobre `world.json`; color fuerte = escenario principal del conflicto, que es el primer país
  de la lista o uno nombrado en el título; claro = alcanzado), lista por nivel, índice diario e histórico con picos, por país,
  refugios (oro, DXY, franco), petróleo/gas/trigo, empresas de defensa y gasto militar.

### Global › Mundo › Espacio (`data-sub="espacio"`, `renderEspacio`, `loadEsp`; datos `espacio.json` de scripts/espacio.py, workflow `espacio.yml` cada 6 h)
- Pedido del dueño 03/11/2026: "no planetas, sino cosas como NASA, SpaceX": economía del espacio. Fuentes con uso comercial permitido:
  Launch Library 2 de The Space Devs (`ll.thespacedevs.com/2.3.0/launches/{upcoming|previous}`; términos: "free to use the data in any
  way"; sin clave 15 pedidos/hora → 2 por corrida, la página NUNCA llama a la API), GCAT de J. McDowell (CC BY 4.0, hay que citarlo:
  `launch/launch.tsv` columna `LaunchCode` que empieza con O = orbital y S = éxito; `derived/currentcat.tsv` lo que está en órbita, Type
  P = satélite; `cat/satcat.tsv` para los satélites con State AR; `tables/orgs.tsv` nombres) y USAspending (NASA = agencia 080,
  `agency_total_obligated` por año fiscal; el último puede estar incompleto).
- Página: próximo lanzamiento con cuenta regresiva por segundo (`espTick`, se corta fuera del apartado; tarjeta `.nofold` para que no
  se pliegue en el celular), casilleros, próximos 15 (con su cuenta), lanzamientos por año desde 1957 (total, EE.UU., China, Rusia/URSS),
  quién lanza más (las academias de CASC juntas, `ESP_CASC`), satélites por dueño (`ESP_DUE`) y por país (`ESP_PAIS`), empresas en
  bolsa (TradingView `tvLista`), NASA, últimos 10 y los satélites argentinos. Nombres de empresas de LL2 acortados en `ESP_EMP`; las
  descripciones de LL2 vienen en inglés: no se muestran.
  Animación (pedido del dueño 03/11/2026: "algo que llame la atención" y después "más lindo y tecnológico, no una pelota con puntos"):
  lienzo `#espOrb` (440×250 en compu, ancho completo × 190 en celular) con la Tierra de puntos (`vendor/dots.json`, Argentina resaltada,
  la mitad de los puntos en celular) girando una vuelta cada 70 s, vista un poco desde abajo; grilla de meridianos; órbitas reales en
  `EO_ORB` (4 planos de Starlink a 53°, polar, GPS y el anillo geoestacionario que gira con la Tierra) con satélites y estela, la ISS,
  pulso en Buenos Aires, enlace punteado de un Starlink a Buenos Aires y un cohete que sale de una base visible (`EO_BASES`); leyenda
  arriba a la izquierda. Colores en `eoCol()`: oscuro celeste; modo claro dorado whisky con Argentina en azul. Funciones `espOrbita`/
  `espDibujar`/`eoCuadro`, objeto `EO`. UNA sola vuelta de animación (`EO.corre`) que busca el lienzo actual en cada
  cuadro (renderEspacio lo recrea; con varias vueltas o un observador viejo se trababa en el celular); 30 cuadros/s en compu, 20 en
  celular, se frena fuera del apartado, fuera de pantalla o con la pestaña oculta; con reducir movimiento queda un cuadro fijo.
  Las tablas `.esptab` anulan el `min-width:640px` y el `nowrap` globales de `table`/`td`; en celular las filas se apilan.

### Global › Mundo › Monitor (`data-sub="explorar"`, botón "Monitor ✦", objeto `XP`, `xpStart`/`xpDraw`)
- Pedido del dueño: NO interactivo, para dejar prendido de ambiente (el Explorador interactivo se descartó: "no se entiende").
  Nunca escribir "escaneando" ni textos que finjan procesos. Solo computadora: `xpDesk()` = `(min-width:1024px) and
  (pointer:fine)`; en celular/tablet el botón se oculta. Se arranca desde `aplicarSub('M')`.
- Globo gigante en canvas (d3 orthographic) con anillos de radar, barrido que muestra el dato de cada país al pasar, noche
  real (`xpSun`), luces de `GEX`, arcos del carry trade y destellos de titulares (`xpNews`). Escenas automáticas
  `XP_SCN` cada `XP_DUR` (22 s): bolsas, monedas, tasas, inflación (se acerca a Argentina) y bonos; vuela al destacado y
  muestra un recuadro con su serie de global_hist (`XP_BK`, `XP_MK`, `XP_BO`). Sexta escena "Conflictos armados" (`xpGeo`,
  `xpGeoC`: color por nivel de `GEO_NIV`, columnas = muertes del último año completo, recuadro con el riesgo geopolítico) y
  cuadros fijos en las guerras mayores/menores en todas las escenas. Pedido del dueño: cargado tipo terminal. Paneles: franja
  `#mnKpi` (mercados, VIX, riesgo geopolítico, riesgo país, Merval), reloj UTC `#mnUtc`, relojes `XP_CLK` (10), termómetro,
  Argentina, geopolítica `#mnGeo` (conflictos por nivel, GPR 7 días, guerras que rotan cada 6 s), flujo de datos (`xpRain`),
  abajo consola (`xpLog`), mapa de calor de bolsas (`xpHeat`) y próximas decisiones de tasas (`#mnBc`, de `BCAL`). `xpSet` solo
  reescribe si cambió.
- Estética (pedido del dueño, "que parezca una terminal de banco, no un jueguito"): piel de terminal tipo Bloomberg,
  bloque CSS "Monitor: piel de terminal" (fondo azul petróleo muy oscuro, ámbar `--am` y acento por panel `--ac`: cian
  mercados/tasas, rojo geopolítica, celeste Argentina; el dueño no quiere todo negro igual ni el azul "aniñado" de antes; antes: negro plano, ámbar `--am` #ff9e1b, encabezados como barras ámbar, sin bordes
  redondeados). En el canvas NO hay halo, anillo con grados, barrido de radar dibujado (el ángulo sigue moviendo las
  etiquetas), miras ni resplandores; títulos sin efecto de máquina de escribir. No volver a agregar adornos de "película".
- "Modo monitor" (`xpModo`): clase `body.mon` (deja visibles las cintas y fija el monitor debajo con `--monTop`),
  pantalla completa, Wake Lock para que no se apague; Esc o clic para salir. Rendimiento: DPR máx. 1,25, 30 cuadros por
  segundo, países agrupados por color y solo la cara visible; los globos de arriba se pausan si no están en pantalla.

### Global › Estados Unidos (`renderUsa`, `usaExtra`)
- Mapa de desempleo por estado (sin animación decorativa), reloj de la deuda (base = Debt to the Penny del Tesoro, 1 día
  hábil de atraso; el avance por segundo es una proyección al ritmo de ~40 días hábiles: el encabezado lo dice), cuenta regresiva a la Fed, 6 indicadores,
  Fed vs inflación, curva del Tesoro, empleos por mes, sectores, 7 magníficas, decisiones de la Fed.
- Semáforo de recesión (regla de Sahm, curva 10-2, VIX, pedidos de desempleo vs un año), inflación por rubro,
  próximos datos (`CAL_US`, fechas BLS/BEA a mano hasta dic-2027),
  mapa de 50 empresas por sector, mercado laboral, hipotecaria 30 años, próximos balances y PBI.

## Terminal (`/terminal/index.html`, página aparte; pedido del dueño 29/10/2026, inspirada en la de MacroLibre)
- Una pantalla sin scroll en compu (≤900px se apila), negro y ámbar estilo Bloomberg (el dueño la quiere así, distinta al resto).
- Links: `#modoT` en el encabezado (entre Argentina y El mundo), `#tabTerm` en las pestañas de Argentina después de Calculadoras
  (el click de `#tabsNav` deja pasar los href que no empiezan con #) y una fila en la hoja de Argentina del celular.
- Datos: `vivo.json` del Worker cada 60 s (dólares, 14 líderes, 11 soberanos en US$; respaldo DolarApi solo dólar), data.json
  (IPC, REM, riesgo, reservas, TAMAR, plazo fijo, base, Merval con su fecha), calendario.json, global.json (monedas BCE y Tesoro).
  Commodities y bolsas del mundo: widgets market-quotes de TradingView con su atribución. Celdas titilan verde/rojo al cambiar.

## Verdadero o falso (`/verdadero-o-falso/`, ex "Pulso Live"/reels en /live/; pedido del dueño 27/10/2026, publicado 01/11/2026)
- Feed vertical a pantalla completa. `verdadero-o-falso/index.html` + `verdadero-o-falso/juego.js` (`/live/` solo redirige; noindex). Pedido del dueño 01/11/2026: SOLO verdadero o
  falso ("es lo que más atrapa", "que haya un montón") y que se llame "Verdadero o falso", no "reels". Los otros moldes
  (dólares del día, récords, monedas en pesos, agenda, noticias, rankings, trivia, "si ponías" como gráfico) siguen en el
  código pero el filtro deja pasar solo `mold: 'vf'`; no volver a mostrarlos. Hoy ~3.500 preguntas distintas por día:
  acciones (A vs B, "¿tiene más dólares que antes?", "¿le ganó al Merval?", "si ponías US$ 1.000… ¿más de US$ X?" en 5
  períodos), inflación (país vs Argentina, país vs país, país vs umbral, Argentina mes a mes), PBI por habitante y
  crecimiento, Big Mac, dólar a precios de hoy y brecha, tasa real. Afuera: bolsas/commodities mensuales, tasas vs Fed y
  desempleo entre países. `add` descarta ids repetidos. Se mezclan por tema (`r.cat` acc/inf/his/dol/bm/tas, `CUOTA`).
- Colores (pedido del dueño: "que cambien, que genere dopamina como un casino; siempre igual parece un tablero"): cada reel
  con un par de colores vivos de `PAL` (`--c`/`--c2`, degradé animado), nunca el mismo seguido; títulos grandes, número con
  degradé, entrada animada, líneas blancas. La imagen para compartir usa el mismo color.
- Premios al responder (pedido del dueño 01/11/2026: "dopamina como en un casino, que te incite a seguir, sin exagerar"):
  `premio(ok, btn, reel)` en verdadero o falso y trivia. Acierto: +10 × racha (tope ×5), número que sube (`.flota`),
  confeti chico (`confeti`, más con racha ≥3), cartel en 3/5/7/10/15 seguidas (`FRASE_RACHA`), vibración corta. Error:
  temblor del botón y "Se cortó la racha de N". Puntos y racha en la ficha `#pts` del encabezado (localStorage `pl-pts`;
  en ≤440px el chip "PULSO LIVE" queda solo como punto). Después de responder aparece "Seguí la racha" / "Probá con la
  próxima" (`.sigue`, baja al siguiente). Eventos GoatCounter `live-acierto` / `live-error`. Respeta reduced-motion.
- Orden al azar pesado por interés; el primero siempre de Argentina. Pedido del dueño 01/11/2026: que nadie vea la misma dos veces.
  Memoria `pl-vistas2` por TEXTO de la pregunta (hash base 36 → día, 180 días; si se llena localStorage se olvidan las más viejas), se marca
  a los 1,2 s en pantalla o al responder, y las vistas no vuelven nunca (antes `pl-vistos`, 7 días, por id). Para que haya miles nuevas en
  cada visita, el bloque "miles de preguntas nuevas" usa períodos que la gente recuerda (cada año, cada semestre, "desde <mes> hasta
  hoy") sobre `his` (A vs B, subió en dólares, contra el Merval, "si ponías US$ 1.000 a principios de <mes>") y meses lejanos del dólar
  real y la inflación: ~4.800 por visita. Pedido del dueño 01/11/2026: que se puedan SABER: nada de fechas exactas ni datos de un día
  (el MEP del 14/03), y todas con diferencias grandes (acciones ≥25 pp entre sí, inflación entre países ≥1,5 pp, Big Mac ≥US$ 0,6,
  dólar real ≥25 %, etc.): se deducen sabiendo cómo vino la economía, no adivinando. Pedido del dueño 02/11/2026: SIN Big Mac (`FUERA_VF`: "nadie sabe cuánto
  vale una hamburguesa en Malasia"), mayoría de conceptos y el orden por FORMATO, no por tema: `FMT` = [formato, regex del id,
  peso] (con 58, ia 7, dol 7, infar 5, infu 3, ppa 3, acc 3, treal 2, crec 2, si 2, infpp 1,5, pp2 1). Se sortea el formato por
  peso y dentro una pregunta al azar (colas mezcladas, sin `score`); nunca dos del mismo formato seguidas salvo conceptos (hasta 3)
  y sin repetir país/acción en las últimas 8 (`key`). Reemplaza a `CUOTA`. Conceptos: ~477 en `conceptos.js` (tercera tanda del
  02/11/2026 con cuentas rápidas, causa y efecto en Argentina, historia, mundo, finanzas personales, mercados, empresas, conducta).
  Como las vistas no vuelven en 180 días, cuando se gastan los conceptos el resto pesa más: sumar conceptos seguido.
  Temas (pedido del dueño 02/11/2026): `verdadero-o-falso/temas.js`, `TEMAS` = [{t, k, w, q}] (billetes, planes y ministros,
  siglas, mitos, quién cobra cada impuesto, empresas, comercio exterior, Argentina en números, economistas, jerga del mercado,
  cuentas rápidas; ~246). Ids `vf-t-<tema>-<hash>`, cada tema es su propio formato (`fmtDe`) con peso `w`; conceptos bajó a 40
  para que conceptos + temas sean ~2/3. Kick = nombre del tema; cat `con`. Para sumar: filas al tema (t sin guiones). Pedido del dueño 01/11/2026: preguntas de
  CONCEPTOS de primer año (`verdadero-o-falso/conceptos.js`, `CONCEPTOS` [afirmación, verdadera, explicación], ~290; categoría
  `con`, cuota 30 en `CUOTA`) y solo acciones conocidas (`FAMOSAS` en juego.js y la misma lista en scripts/verdadero.py). Sin
  puntos: la ficha `#pts` muestra solo la racha; al errar, el reel queda rojo (`.reel.perdio`). Pedido del dueño 02/11/2026: acciones
  solo súper conocidas (~25 en `FAMOSAS`, cuota 8), sin el total de preguntas ("sensación de infinito"), al pie "Tu récord"
  (`#recYo`, `PT.max`) y "Récord de todos"; la siguiente pregunta recién se dibuja al responder la actual (`pintar(1)` en `premio`)
  y si alguien recarga con una a la vista sin responder (`pl-pend`) la racha se corta; al acertar la pantalla queda verde
  (`.reel.gano`), confeti que cae desde arriba en cada acierto (`lluvia`) más el del botón y número dorado con rayos. Las monedas
  (`monedas`) y el marco de luces (`luces`) se probaron y el dueño los sacó el 02/11/2026 ("queda horrible"): no volver a ponerlos. Los botones
  "Compartir" y "Ver más" de cada pregunta se sacaron el 02/11/2026 (nadie los usaba y llenaban la pantalla): no volver a ponerlos; `compartir()` queda sin uso.
- URL `/verdadero-o-falso/` (pedido del dueño: que aparezca al googlear "verdadero o falso Pulso Macro"; título, descripción, JSON-LD `Quiz`, en `sitemap.xml` vía paginas.py). Datos: `verdadero-o-falso/datos.json` (~950 KB, ~290 KB comprimido) y `verdadero-o-falso/portada.json` de `scripts/verdadero.py` (solo lee los JSON del
  repo). Workflow `verdadero-o-falso.yml`: al terminar Actualizar datos, Global o Historia, y 00:50 ART. Acciones: solo con nombre,
  operadas ≥85 % de las últimas 60 ruedas y sin saltos >45 %/−40 % (un precio roto da un "si ponías…" falso).
- Entrada en Inicio: `.juegos#pLive`, dos botones lado a lado en el lugar de la vieja franja (pedido del dueño 01/11/2026):
  a la izquierda Crucigrama (`/crucigrama/`), a la derecha Verdadero o falso. Chicos, para que en el celular se vea
  "¿Qué querés ver?" abajo. `portada.json` ya no lo usa la portada (queda generado, sin uso). Bandera argentina para los reels: `vendor/flags/ar.svg`.

- Más dopamina (pedido del dueño 01/11/2026, "la mayor dopamina posible" y "pantalla roja si perdés"): al acertar, destello
  verde de pantalla (`fx('bien')`), anillos desde el botón (`onda`), número gigante "+N ×racha" (`grande`), confeti 45-110
  y lluvia desde arriba con racha ≥5 (`lluvia`), medidor de racha `#med` ("faltan N para el próximo hito"). Al errar:
  pantalla roja + temblor del feed (`fx('mal')`, `.sacude`) y, si quedó a ≤3 del récord de todos, cartel "¡Casi!". Sin sonido.
- Récord de racha entre todos (pedido del dueño 01/11/2026): `/api/racha` en el Worker `pulso-vivo` (worker/vivo.js, ruta
  `pulsomacro.com.ar/api/*` en Cloudflare). GET = récord (`racha/record.json` en R2). POST {tk} en cada acierto: devuelve
  una ficha firmada con HMAC (clave al azar guardada en R2 `racha/clave`) con la racha +1; solo suma de a uno, con ≥2,5 s
  entre respuestas (si no, 429), se corta a los 10 min sin jugar, tope 1000. No guarda nada por jugador. Límite honesto:
  no puede saber si la respuesta era correcta (eso lo decide el navegador), solo frena trampas fáciles (mandar "999" o
  muchas seguidas al toque). Para borrar el récord: borrar `racha/record.json` del bucket. Piso `RACHA_PISO` = 62 (pedido del dueño 02/11/2026: el récord público arranca en su 62, coherente con el contador del modo Órbita): el GET nunca devuelve menos y solo se supera con 63. En la página: `#rec` al pie
  ("Récord de todos: N"), cartel "¡Nuevo récord!" con racha ≥3. Si la ruta no responde, no se muestra nada.
- Carteles (`cartel(reel, txt, ms)`, pedido del dueño 02/11/2026: que no se superpongan): van EN la pregunta, en el flujo, antes de
  `.lockr`/la fuente, uno por vez en fila (`COLA`, `sigCartel`), arrancan 950 ms después (cuando se fue el número grande) y se pliegan
  al irse. Duración 2,6 s; "¡Nuevo récord!" de todos, 4,2 s.

## Crucigrama (`/crucigrama/`, pedido del dueño 01/11/2026: "uno por día, estilo crucigrama de La Nación pero de economía")
- `crucigrama/index.html` + `crucigrama.js` + `palabras.js` (banco `PALABRAS` [palabra, pista], ~2.400 desde el 02/11/2026, 3-11 letras sin
  tildes; para sumar, agregar ahí). Todo en el navegador, sin robot: semilla = fecha de Buenos Aires (UTC−3), 30 pruebas
  `armar()` con esa semilla y queda la de más palabras (~15), grilla máx. 13×13 de palabras cruzadas sin pegarse en
  paralelo; numeración clásica, Horizontales/Verticales. Igual para todos el mismo día; N.º 1 = 01/11/2026. Un casillero
  = un `<input>` (anda con el teclado del celular); tocar de nuevo cambia la dirección; flechas, Enter (próxima palabra) y
  borrar. Pedido del dueño (como La Nación): la palabra que estás completando va en rojo (`.act`, la letra actual `.cur` más
  fuerte) y cada palabra que queda bien se pone verde al instante y se bloquea (`verdes()`, `.okw`, readonly; sus letras no se pueden cambiar ni borrar desde una palabra que la cruza (`fija()`, sin readOnly para que el teclado del celular no se cierre); al escribir NO se saltean los casilleros fijos: cualquier tecla en un casillero fijo deja la letra como está y pasa al siguiente, nunca la manda a otro casillero (pedido del dueño 03/11/2026); elegir una palabra (pista, Enter, próxima) arranca SIEMPRE en su primera letra, como La Nación; si al completar una palabra le quedan letras fijas al final, se sigue por ellas y recién después salta a la próxima (`dentro`, `pasarSiguiente`) (02/11/2026: saltearlos hacía que, escribiendo la palabra entera, las letras cayeran corridas y nunca se pusiera verde); las resueltas se guardan en `E.okw` y `reparar()` las repone al cargar; la pista se tacha
  `.hecha`). Reloj, "Una letra de ayuda" (cuenta pistas; va en el casillero donde estás parado y, si ese ya está bien, en uno al azar; "Comprobar" se sacó el 01/11/2026 porque las palabras ya se ponen verdes solas), progreso por día en localStorage
  `pm-cruci-AAAA-MM-DD`, racha de días `pm-cruci-racha`, festejo con tiempo, compartir y cuenta regresiva al próximo.
  Evento GoatCounter `cruci-resuelto`. En `sitemap.xml` y JSON-LD `Game`.
  Resuelto (pedido del dueño 02/11/2026: al tocar sin querer se abría el teclado y cambiaba una letra): `cerrar()` deja todos los
  casilleros de solo lectura (`readOnly`, `tabIndex -1`, `inputmode=none`), tocar uno solo muestra su pista (`ir` sin foco con
  `E.fin`), sin "Una letra de ayuda"; al volver a entrar ya resuelto no tira confeti otra vez (`festejo(n, true)`).
- Revisión a fondo (02/11/2026), cambios desde el N.º 3 (03/11; `V2 = HOY >= '2026-11-03'`, así el del día no cambió a mitad de
  partida): el generador anota la dirección de cada letra (`D`) y un cruce tiene que ser con una palabra de la otra dirección
  (antes una palabra podía quedar metida adentro de otra en la misma fila: pasaba en 1 de cada 365); palabras sin repetir (pedido del dueño 02/11/2026: ninguna palabra antes de 2 meses y dos crucigramas cualesquiera
  con como mucho 4 palabras en común): las candidatas de cada día vienen de `crucigrama/plan.js` (`CRUCI_PLAN`, índices en base 36
  de `PALABRAS`, desde el N.º 3 por ~3 años), que arma `node scripts/crucigrama_plan.js [días]` corriendo el MISMO generador de la
  página (`GAP` = 60 días, `MAXC` = 4, 13 a 15 palabras por día). Lo ya publicado no se cambia (respeta el plan viejo hasta
  `--desde`, por defecto mañana). Si un día no está en el plan, queda de respaldo el sistema anterior (`MAZO`). Banco de ~1.050
  palabras (180 originales + tres tandas del 02/11/2026). Pedido del dueño: nada de economistas que nadie conoce (se sacaron 18;
  quedan en `palabras.js` como `['', '']` para no correr los índices). Agregar SIEMPRE AL FINAL y, para sacar una, dejar `['', '']`;
  después volver a correr el script. PENDIENTE: extender el plan antes de que se termine (ver la fecha final que imprime).
  Página: la pista actual (`#pAct`) va arriba de la grilla y queda pegada arriba (el teclado del celular la tapaba); en celular la
  grilla va de borde a borde (casilleros de ~24 a ~26 px); borrar usa `beforeinput` (en Android el teclado no manda keydown
  Backspace y no se podía volver al casillero anterior); Enter/Tab y terminar una palabra llevan a la próxima sin resolver
  (`siguiente`, `irPalabra`); tocar una pista de la lista sube a la grilla en celular; el reloj se frena con la pestaña oculta;
  después de medianoche el festejo dice que ya salió el nuevo.
- Formato La Nación desde el N.º 3 (pedido del dueño 02/11/2026: "25 a 32 palabras" y casilleros no más chicos que los de La
  Nación en el celular, ~31 px): grilla de 11×11 con casilleros negros, simétrica (giro de 180°), estilo británico: filas y
  columnas pares tienen palabras de 3, 5, 7 u 11 letras y en las impares una letra sí y una no (cada palabra se cruza cada dos
  letras); todo conectado y el centro abierto. 26 palabras por día. Las grillas completas vienen hechas en `crucigrama/grillas.js`
  (`CRUCI_G`, 121 caracteres por día, `#` = negro, desde el N.º 3 hasta 12/2028) que arma `node scripts/crucigrama_grillas.js
  [días]` (búsqueda con vuelta atrás; prefiere las palabras que hace más que no salen). Reglas: ninguna palabra de 5+ letras
  antes de 60 días; las de 3 letras (hay pocas en español) nunca antes de 18; dos días cualesquiera con máx. 4 en común; máx. 3
  siglas/códigos por día. Lo ya publicado no cambia (`--desde`, por defecto mañana). En la página: `G3`, `desdeGrilla` arma
  `P.puestas` con las pistas de `PALABRAS` y `#grid.neg` (gap 1 px; celular `(100vw − 26px)/11` = 30 px en 360 y 33 en 390;
  compu 48 px). `plan.js`/`MAZO`/`armar` quedan de respaldo si un día no está en grillas.js. Banco de ~2.400 palabras
  (tandas del 02/11/2026 de 3, 5 y 7 letras, cosas de todos los días: pedido del dueño, "no mega complejas"). Para sumar
  palabras: al final de `palabras.js` y volver a correr el script.
- SOLO ECONOMÍA desde el 03/11/2026 (el dueño, enojado: "se lo anuncié a todo el mundo como un crucigrama de economía"; el N.º 3
  había salido con "Barco antiguo", "No linda"...). El generador usa solo las palabras de arriba de la marca "FIN DE ECONOMÍA" de
  `palabras.js` y las de abajo que tienen un 1 como tercer dato (`['MES', 'Período que mide el IPC', 1]`: palabra de todos los
  días con pista de economía, o palabra nueva de economía). Las palabras de todos los días sin el 1 NO salen nunca. Nunca volver a
  meter pistas que no sean de economía. Pedido del dueño 03/11/2026: "no me gusta que haya tanto de siglas" → tope `SIGLAS` = 3
  (se afloja hasta 5 si un día no sale; en la práctica 3-4 por día, antes ~11), `SIG3` = siglas de 3 letras cuya pista no lo dice,
  palabras comunes de 3 letras con pista de economía (SIN, POR, UNO, OSO, VEZ...), patrón con más filas de 5+5 y centro abierto en
  ≥2 líneas (antes 4). Banco ~1.480 palabras. Reglas: 5+ letras no antes de 21 días (se afloja; mínimo real 15), 3 letras no antes de
  6, máx. 6 en común entre dos días (variables GAP, GAP3, MAXC, SIGLAS). `grillas.js` llega hasta 12/2028 (se armó con `--desde=2026-11-04`;
  el N.º 3 quedó igual). Para separar más las repeticiones: sumar palabras de economía de 3, 5 y 7 letras y volver a correr
  `node scripts/crucigrama_grillas.js 760` (tarda ~15 min).
  El N.º 3 se cambió a mitad del día: su progreso guardado usa la clave `pm-cruci-2026-11-03-eco`.
- Arreglos del 03/11/2026 (pedido del dueño): la racha se cuenta mirando los días resueltos guardados en el dispositivo (`racha()`,
  `resuelto(d)`, hacia atrás desde hoy) y el cartel dice cuáles son ("3 días seguidos resolviéndolo: 1, 2 y 3 de noviembre",
  `rachaTxt`); `pm-cruci-racha` queda solo por compatibilidad. En la compu (≥880px) la lista de pistas tiene su propio scroll
  (sticky, alto = pantalla − 170 px) y al elegir una palabra la lista se mueve sola hasta su pista (`verPista`; la grilla no se
  mueve). Pista elegida más marcada (caramelo más oscuro y raya a la izquierda); resueltas en verde con fondo, tachado grueso y ✓.
- Celular (pedido del dueño 03/11/2026, "es medio incómodo"; `TACTIL` = pointer:coarse): el casillero se elige con el toque (`click`), no al
  apoyar el dedo (`pointerdown` solo con mouse), así deslizar para subir o bajar no cambia la palabra; tocar un casillero NO mueve la página (la pista ya
  aparece arriba, pedido del dueño); solo tocar una pista de la lista acomoda la página para que se vea entera debajo de `#pAct` y arriba del teclado (`verPalabra`, usa
  `visualViewport`); al completar una palabra se cierra el teclado y queda marcada la siguiente (`irPalabra(q, false)`); tocar `#pAct`
  con el teclado cerrado lo vuelve a abrir.

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
  Pedido del dueño: si un país tiene menos de `MIN_ES` (15) titulares en español, se completa con medios en inglés
  (`FEEDS_EN`, filtros `ECON_EN`/`PAIS_EN`/`OTROS_EN`/`RUIDO_EN`), después de los de español y marcados `"l":"en"` (en la
  página, etiqueta EN). Google Noticias no se usa (su robots.txt lo prohíbe). TVP World, Polskie Radio, WBJ y The Brazilian Report dan 404. En inglés se aceptan titulares de hasta 7 días (`DIAS_EN`; en la página también).
  Medios que dan 403 desde Actions: El Economista México por sección, Forbes México, elEconomista.es.
- Páginas por indicador (para Google; el tablero es un solo archivo con `#` y Google solo ve la portada):
  `scripts/paginas.py` + workflow `paginas.yml` (corre al terminar Actualizar datos, Global y Ganaderia, y a las 00:05).
  Arma ~20 carpetas `/<slug>/index.html` (dato escrito como texto, gráfico SVG, últimos datos, qué es, botón al tablero,
  links entre páginas), `/indicadores/` (índice, enlazado desde el pie del tablero), `sitemap.xml` y `robots.txt`.
  Solo lee los JSON; solo escribe si cambió algo. Una página nueva = un bloque `pag_diaria`/`pag_mensual` en el script.
  No cambiar los slugs (son las URL que indexa Google). Google Search Console verificado con el archivo
  `google1d15c85ea7dfd326.html` en la raíz: NO borrarlo (se pierde la verificación).
- Chequeo diario del sitio publicado (`chequeo-sitio.yml` + `scripts/chequeo.mjs`, L a V 19:43 ART): si hay problemas
  graves abre un issue (avisa por mail al dueño) y lo cierra solo cuando se arregla. Revisa también la portada.
- Chequeo con Safari (`chequeo-apple.yml` + `scripts/chequeo_apple.mjs`, en una Mac de GitHub, a mano o al cambiar esos archivos):
  WebKit de Playwright en iPhone 15, iPad Pro y Mac contra el sitio publicado (modos, Órbita, buscador, secciones, juego,
  crucigrama; errores, desbordes y pedidos fallidos). Deja capturas e `informe.md` en la rama `chequeo-apple` (se pisa cada vez).
  Acá no se puede bajar WebKit: leer el resultado con `git fetch origin chequeo-apple:refs/remotes/origin/chequeo-apple`.
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
- DolarApi `https://dolarapi.com/v1/dolares` (la pide el Worker `pulso-vivo`; el navegador solo si el Worker falla) y Open BYMADATA (solo el Worker y update.py).
- Mundo: SIN CNBC, Yahoo, Stooq, CoinGecko ni Nasdaq desde el 26/10/2026 (plan legal: sus términos prohíben mostrar o
  redistribuir sus datos, o no habilitan uso comercial). Ver "Mercados sin CNBC" abajo. Además: FMI DataMapper (o Banco
  Mundial), BIS WS_CBPOL, Frankfurter (BCE) y RSS (El País, DW, Expansión, France 24, Euronews, BBC Mundo filtrado).
- Mercados sin CNBC (plan legal 26/10/2026; scripts/abiertas.py, global.py, usa.py):
  - Números propios SOLO de fuentes que permiten reuso comercial citando: monedas BCE/BIS (+ BCRA, TRM, BCRP), bonos
    (Tesoro, Bundesbank, BoE, BoC, MOF Japón, Riksbank, Norges Bank; el resto OCDE `DF_FINMARK` IRLT, promedio mensual,
    `mensual: true`, `t` = AAAA-MM), bolsas de cada país (OCDE SHARE mensual: `bolsas[k].vm/va/v12/m`, historia `sh_ISO`;
    bonos `ir_ISO`), granos y metales (Banco Mundial Pink Sheet mensual, CC BY 4.0; `banco_mundial_commodities`, necesita
    openpyxl), petróleo y gas (EIA), estrés financiero OFR (`termo.fsi`, historia `fsi`; reemplaza al VIX). `ocde_mercados`
    descarta series cortadas (> 5 meses) o fijas (Rusia). global.json lleva `"abiertas": true`; sin esa marca, main() no
    reusa nada de mercados del JSON anterior (para no volver a publicar datos de CNBC).
  - Color de los widgets (pedido del dueño: "que parezca todo una misma cosa"): `TV_BASE.backgroundColor` negro + iframe con
    `mix-blend-mode:lighten` sobre `.tvbox` aislado (`isolation:isolate`) con el fondo real del lugar (`tvFondo`): el negro
    toma el color de la tarjeta o la cinta (el ticker-tape ignora backgroundColor: su fondo es rgb(19,19,19), medido 26/10/2026; con lighten queda igual a la cinta). `#tape2In` se recorta a la altura del iframe − 1 px (`renderTape2`) para que no quede la franja vacía de 32 px ni la línea de abajo; la atribución va en una tira de 14 px debajo (`.tape2{padding-bottom:14px}`), sin tapar los datos. NO usar `isTransparent` (Edge pinta blanco el iframe, probado 26/10/2026).
  - Precios del día de bolsas, acciones, ADR, fondos, sectores y cripto: widgets de TradingView (gratis con su marca; la
    data la muestra TradingView desde sus servidores con sus licencias). Los JSON solo llevan el símbolo (`tv`, `tvn`).
    En la página: `tvw` (arma cualquier widget; `.tvbox`, `color-scheme:normal` en el iframe o sale fondo blanco),
    `tvLista` (market-quotes), `tvGrafico` (symbol-overview), `tvBolsa` (tarjeta de bolsa de cada país),
    `kpiTv` (pedido del dueño 03/11/2026: el recuadro de TradingView arriba de cada país desentonaba: ahora el casillero de
    arriba es propio, la bolsa del país en el último mes de la OCDE `bolsas[k].vm/va/m`, y si no está, PBI por habitante del Banco
    Mundial con `kpixFill`/`[data-kpix]`; `data-tvq` single-quote queda solo con cls 'st' en Mercados), `gHeat` (ahora lista), cinta `#tape2`
    (ticker-tape; en el celular solo si `body.mglo`), cripto (`screener` crypto_mkt), S&P 500 (`stock-heatmap` SPX500).
  - TradingView NO deja mostrar en widgets: SP:SPX, DJ:DJI, NASDAQ:NDX, Nikkei, FTSE, VIX, el Merval (BCBA:IMV), futuros de
    CME/CBOT. Se usan CFD (FOREXCOM:SPXUSD, NSXUSD, DJI, UKXGBP, JPXJPY, AUXAUD; CAPITALCOM:EU50, IT40, SOYBEAN, COPPER) o el
    fondo del país en Nueva York (EWW, EZA, KSA, INDA, EWY, ENZL, THD, EWM, EPHE, EIS, EWS, EWJ, TUR, COLO). Mapa en
    `abiertas.TV` y `tv_sym` (bolsa de cada ticker resuelta con la búsqueda de TradingView el 26/10/2026). Símbolos
    probados uno por uno; si uno muestra "!", buscar el correcto en es.tradingview.com.
  - Quitados: "Próximos balances" (endpoint interno de Nasdaq), ADR de Despegar y Telefónica (deslistados), ERJ → EMBJ.
- User-agent de todos los robots: `Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@...)`
  (identificarse, no hacerse pasar por un navegador). robots.txt revisado el 26/10/2026: Rava, Cañuelas y CAC Rosario
  permiten lo que se usa; mercados.ambito.com no tiene robots.txt.
- Monedas (`scripts/abiertas.py`): BCE (EXR diario, ~30 monedas; se guardan con la convención que usaba CNBC, por eso
  los símbolos `XXX=`) y, las que el BCE no tiene, BIS WS_XRU (1 a 3 semanas de atraso);
  ARS, COP y PEN se completan al día con el mayorista de data.json (BCRA), la TRM de datos.gov.co (`32sa-8pi3`) y el BCRP
  (PD04640PD). Campo `f` de cada cotización = fuente. En la página, una moneda con más de ~4 días (`fresco`) muestra
  "último dato dd/mm" en vez de "% hoy" y no se pinta en el globo "Mundo hoy". Tasas US2Y/US10Y/US30Y del Tesoro y
  petróleo/gas spot de la EIA (`.xls`, necesita xlrd; vienen con unos días de atraso).
- EE.UU.: Tesoro (deuda y curva), BLS v1 sin clave (máximo cada 12 h; series nacionales, rubros `r_*`, JOLTS y 51
  estados), BIS (Fed), CNBC, DOL `oui.doleta.gov/unemploy/csv/ar539.csv` (c3 iniciales, c8 continuos, suma de estados,
  sin desestacionalizar), Freddie Mac `PMMS_history.csv`, Nasdaq `api.nasdaq.com/api/calendar/earnings`, BEA (con clave).
- Sin fuente gratuita: deuda del Tesoro en pesos (LECAP/BONCAP), historia por acción argentina, liquidación del agro.

## Buscadores (pedido del dueño 02/11/2026: que Pulso Macro salga con logo y descripción, y que al buscar su nombre aparezca él)
- index.html lleva JSON-LD `@graph` con WebSite, Organization (logo `icons/anillo-512.png`, `sameAs` la cuenta de X) y Person
  (`#francisco`); favicon también en 192 px (Google pide múltiplos de 48). Página `/francisco-epherra/` (ProfilePage + Person,
  en el sitemap); el nombre en Sobre lleva ahí. Solo datos que ya están en Sobre: nada de edad ni otros datos personales.
  Los resúmenes de Copilot/Google y los paneles de "persona famosa" no se pueden forzar: dependen de que otros sitios hablen
  del sitio. Bing Webmaster Tools se da de alta importando desde Google Search Console.

## Entorno de Claude
- La terminal no tiene internet salvo GitHub: las fuentes se miran con WebFetch y la prueba real es correr el workflow
  (un push a los scripts dispara `global.yml`). `env -u GH_TOKEN gh api repos/...` sirve para leer (repo público).
- Para probar la página: servidor local en el repo y Playwright con Chromium de `/opt/pw-browsers`; las fuentes de Google
  no cargan desde la red (d3/topojson ya están en `vendor/`).

## Decisiones del dueño (no volver a proponer)
- Descartados: calendario de vencimientos de deuda, "BSTEP", balanza cambiaria, liquidación del agro, gráfico histórico
  por acción, deuda del Tesoro en pesos, newsletter, inflación semanal de alimentos propia, "el día en 30 segundos",
  dólar contra la banda cambiaria, curva de tasas en pesos, capas del globo con datos viejos (exportaciones por destino,
  deuda/PBI), rediseño "sala de situación", segundo monitor "Terminal Argentina" (tablero o globo de
  Argentina: el Monitor del mundo queda como único), pestaña "Vuelos" (horarios y aviones en vivo),
  versión del sitio en inglés, estética ciberpunk / "modo neón" como cara del sitio (existe solo como premio escondido: modo Ciudad).
