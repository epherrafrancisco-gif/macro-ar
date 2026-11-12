// Worker "pulso-vivo": una vez por minuto trae el dólar (DolarApi) y acciones y bonos (Open BYMADATA) y guarda todo en R2 como
// vivo.json. La página lo lee desde datos.pulsomacro.com.ar con la marca del minuto (?t=VER()), así Cloudflare lo sirve de su
// caché y las fuentes reciben 1 pedido por minuto en total, no uno por cada visitante. Si una fuente falla, queda el último dato bueno.
// Acciones y bonos: Open BYMADATA, el acceso gratuito y público de BYMA (dueña del dato), que ya viene con 20 minutos de
// demora. Desde el 26/10/2026 no se usa data912 (API anónima sin licencia). Se publican los mismos precios que BYMA
// muestra gratis al público, citando a BYMA. Plazo 24 hs (T1), como se opera normalmente.
// Bindings: R2 bucket "DATOS". Cron: "* * * * *". Secreto opcional AISSTREAM_KEY (barcos en vivo, ver ais()).

const DOLAR = 'https://dolarapi.com/v1/dolares';
const BYMA = 'https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/';
const UA = 'Mozilla/5.0 (compatible; PulsoMacro/1.0; +https://pulsomacro.com.ar; contacto@pulsomacro.com.ar)';
const DEMORA = 20 * 60000;  // la demora con la que Open BYMADATA publica los precios
const JSON_META = {httpMetadata: {contentType: 'application/json; charset=utf-8', cacheControl: 'public, max-age=60'}};

async function traer(url){
  const r = await fetch(url, {headers: {'user-agent': UA}});
  if(!r.ok) throw new Error(url + ' ' + r.status);
  return r.json();
}

// Un pedido a Open BYMADATA (todas las especies en una página, plazo 24 hs).
async function byma(ep){
  const r = await fetch(BYMA + ep, {method: 'POST', headers: {
      'user-agent': UA, 'content-type': 'application/json', 'accept': 'application/json, text/plain, */*',
      'origin': 'https://open.bymadata.com.ar', 'referer': 'https://open.bymadata.com.ar/'},
    body: JSON.stringify({excludeZeroPxAndQty: false, T2: false, T1: true, T0: false, page_size: 3000, 'Content-Type': 'application/json'})});
  if(!r.ok) throw new Error(ep + ' ' + r.status);
  const j = await r.json();
  return Array.isArray(j && j.data) ? j.data : [];
}

// Formato que usa la página (el mismo de antes): c precio, pct_change en %, v cantidad, q_op operaciones, puntas y moneda.
// Solo pesos (ARS) y dólar MEP (USD); el cable (EXT) no se usa en la página.
function slim(a){
  return a.filter(x => x && x.symbol && (x.denominationCcy === 'ARS' || x.denominationCcy === 'USD')).map(x => {
    const c = x.trade > 0 ? x.trade : x.closingPrice > 0 ? x.closingPrice : x.previousClosingPrice || 0;
    return {symbol: x.symbol, m: x.denominationCcy, c, pct_change: x.trade > 0 ? Math.round((x.imbalance || 0) * 1e6) / 1e4 : 0,
            v: x.volume || 0, q_op: x.numberOfOrders || 0, px_bid: x.bidPrice || 0, px_ask: x.offerPrice || 0, h: x.tradeHour || ''};
  });
}

async function actualizar(env, ahora){
  let prev = {};
  try{ const o = await env.DATOS.get('vivo.json'); if(o) prev = await o.json(); }catch(e){}
  const out = {t: ahora, dolares: prev.dolares || null, tDol: prev.tDol || 0, fuente: 'Open BYMADATA (BYMA)',
               stocks: prev.fuente ? prev.stocks : null, bonds: prev.fuente ? prev.bonds : null,  // nada de lo que venía de data912
               tMkt: prev.fuente ? prev.tMkt : 0, demora: DEMORA, err: []};
  try{
    const d = await traer(DOLAR);
    if(Array.isArray(d) && d.length){ out.dolares = d; out.tDol = ahora; }
  }catch(e){ out.err.push('dolar'); }
  try{
    const [le, ge, pb, lt] = await Promise.all(['leading-equity', 'general-equity', 'public-bonds', 'lebacs'].map(byma));
    const stocks = slim([...le, ...ge]), bonds = slim([...pb, ...lt]);
    if(stocks.length > 30){ out.stocks = stocks; out.bonds = bonds.length ? bonds : out.bonds; out.tMkt = ahora - DEMORA; }
    else out.err.push('byma vacío');
  }catch(e){ out.err.push('byma: ' + e.message); }
  await env.DATOS.put('vivo.json', JSON.stringify(out), JSON_META);
  return out;
}

// ---------- Verdadero o falso: récord de racha entre todos los jugadores (pulsomacro.com.ar/api/racha) ----------
// Cada acierto el navegador manda la ficha que recibió en el acierto anterior; el Worker la firma (HMAC) y solo deja sumar
// de a uno y con al menos RACHA_GAP entre respuestas. Sin guardar nada por jugador: en R2 solo el récord y la clave.
const RACHA_GAP = 2500, RACHA_CORTE = 10 * 60000, RACHA_TOPE = 1000;
let RACHA_KEY = null;
const b64 = u8 => btoa(String.fromCharCode(...u8)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
async function rachaClave(env){
  if (RACHA_KEY) return RACHA_KEY;
  let raw = null; try{ const o = await env.DATOS.get('racha/clave'); if (o) raw = new Uint8Array(await o.arrayBuffer()); }catch(e){}
  if (!raw || raw.length < 32){ raw = crypto.getRandomValues(new Uint8Array(32)); await env.DATOS.put('racha/clave', raw); }
  RACHA_KEY = await crypto.subtle.importKey('raw', raw, {name: 'HMAC', hash: 'SHA-256'}, false, ['sign']);
  return RACHA_KEY;
}
async function firmar(env, txt){ return b64(new Uint8Array(await crypto.subtle.sign('HMAC', await rachaClave(env), new TextEncoder().encode(txt)))).slice(0, 32); }
// récord base de 81 (pedido del dueño 08/11/2026, antes 62: es el suyo, el del único que tiene el modo secreto): el récord que se
// muestra nunca es menor, y solo cambia cuando alguien hace 82 o más
const RACHA_PISO = 81;
async function rachaRecord(env){ let r = {n: 0, t: 0}; try{ const o = await env.DATOS.get('racha/record.json'); if (o) r = await o.json(); }catch(e){}
  return r.n >= RACHA_PISO ? r : {n: RACHA_PISO, t: r.t || 0}; }
async function racha(req, env){
  const H = {'content-type': 'application/json', 'cache-control': 'no-store'};
  if (req.method === 'GET') return new Response(JSON.stringify(await rachaRecord(env)), {headers: {...H, 'cache-control': 'public, max-age=20'}});
  if (req.method !== 'POST') return new Response('{}', {status: 405, headers: H});
  const ahora = Date.now(); let tk = '';
  try{ tk = String((await req.json()).tk || ''); }catch(e){}
  let n = 1;
  const [nn, t, sig] = tk.split('.');
  if (sig && sig === await firmar(env, nn + '.' + t)){
    const dt = ahora - +t;
    if (dt < RACHA_GAP) return new Response(JSON.stringify({err: 'rapido'}), {status: 429, headers: H});
    if (dt < RACHA_CORTE) n = Math.min(RACHA_TOPE, +nn + 1);
  }
  let rec = await rachaRecord(env), nuevo = false;
  if (n > rec.n){ rec = {n, t: ahora}; nuevo = true; await env.DATOS.put('racha/record.json', JSON.stringify(rec), {httpMetadata: {contentType: 'application/json'}}); }
  const base = n + '.' + ahora;
  return new Response(JSON.stringify({tk: base + '.' + await firmar(env, base), n, record: rec.n, nuevo}), {headers: H});
}

// ---------- Modo Bóveda: cuántas personas lo desbloquearon (pulsomacro.com.ar/api/boveda; pedido del dueño 02/11/2026) ----------
// Arranca en 1 (el dueño). Solo suma con una ficha firmada por /api/racha de 60 o más seguidas, y cada ficha cuenta una vez.
// Desde el 08/11/2026 es el modo Órbita, el ÚNICO modo secreto, con 40 seguidas (antes 60; Ciudad y Coder se sacaron).
const BOV_META = 40, BOV_BASE = 1;
async function bovCuenta(env){ try{ const o = await env.DATOS.get('boveda/cuenta.json'); if (o) return await o.json(); }catch(e){} return {n: BOV_BASE}; }
async function boveda(req, env){
  const H = {'content-type': 'application/json', 'cache-control': 'no-store'};
  if (req.method === 'GET') return new Response(JSON.stringify(await bovCuenta(env)), {headers: {...H, 'cache-control': 'public, max-age=30'}});
  if (req.method !== 'POST') return new Response('{}', {status: 405, headers: H});
  let tk = ''; try{ tk = String((await req.json()).tk || ''); }catch(e){}
  const [nn, t, sig] = tk.split('.'); let c = await bovCuenta(env);
  if (sig && +nn >= BOV_META && sig === await firmar(env, nn + '.' + t) && !(await env.DATOS.head('boveda/usadas/' + sig))){
    await env.DATOS.put('boveda/usadas/' + sig, '1');
    c = {n: c.n + 1, t: Date.now()};
    await env.DATOS.put('boveda/cuenta.json', JSON.stringify(c), {httpMetadata: {contentType: 'application/json'}});
  }
  return new Response(JSON.stringify(c), {headers: H});
}

// ---------- Surtidores: copia del CSV de precios en surtidor (Secretaría de Energía, datos abiertos) ----------
// datos.energia.gob.ar no responde desde GitHub Actions: el Worker baja el archivo tal cual y lo guarda en R2
// (surtidores/vigentes.csv); el robot de GitHub lo procesa desde datos.pulsomacro.com.ar. Cada 6 horas como mucho.
const SURT_URL = 'http://datos.energia.gob.ar/dataset/1c181390-5045-475e-94dc-410429be4b17/resource/80ac25de-a44a-4445-9215-090cf55cfda5/download/precios-en-surtidor-resolucin-3142016.csv';
const SURT_KEY = 'surtidores/vigentes.csv', SURT_CADA = 6 * 3600e3;
async function robotsOk(url){
  try{ const u = new URL(url), r = await fetch(u.origin + '/robots.txt', {headers: {'user-agent': UA}}); if(!r.ok) return true;
    let todos = false, no = [];
    for(const l of (await r.text()).split('\n')){ const [k, ...v] = l.split(':'), val = v.join(':').trim(), kk = k.trim().toLowerCase();
      if(kk === 'user-agent') todos = val === '*'; else if(kk === 'disallow' && todos && val) no.push(val); }
    return !no.some(d => u.pathname.startsWith(d.replace(/\*.*$/, '')));
  }catch(e){ return true; }
}
async function surtidores(env){
  try{
    const h = await env.DATOS.head(SURT_KEY);
    if(h && Date.now() - h.uploaded.getTime() < SURT_CADA) return;
    let est = null; try{ const o = await env.DATOS.get('surtidores/estado.json'); if(o) est = await o.json(); }catch(e){}
    if(est && Date.now() - est.t < (est.corriendo ? 15 : 30) * 60e3 && !est.ok) return;   // bajando ahora, o falló hace poco
    await env.DATOS.put('surtidores/estado.json', JSON.stringify({t: Date.now(), corriendo: true}));
    if(!(await robotsOk(SURT_URL))){ await env.DATOS.put('surtidores/estado.json', JSON.stringify({t: Date.now(), err: 'robots.txt no lo permite'})); return; }
    const r = await fetch(SURT_URL, {headers: {'user-agent': UA}});
    if(!r.ok) throw new Error('energia ' + r.status);
    const meta = {httpMetadata: {contentType: 'text/csv; charset=utf-8', cacheControl: 'public, max-age=600'}};
    const len = +r.headers.get('content-length');
    if(len > 0){ const {readable, writable} = new FixedLengthStream(len); r.body.pipeTo(writable); await env.DATOS.put(SURT_KEY, readable, meta); }
    else await env.DATOS.put(SURT_KEY, await r.arrayBuffer(), meta);
    await env.DATOS.put('surtidores/estado.json', JSON.stringify({t: Date.now(), ok: true, bytes: len || null}));
  }catch(e){ try{ await env.DATOS.put('surtidores/estado.json', JSON.stringify({t: Date.now(), err: String(e.message || e)})); }catch(e2){} }
}


// ---------- Barcos en vivo: petroleros por AIS (AISStream.io, clave en el secreto AISSTREAM_KEY) ----------
// Cada minuto, DESPUÉS de guardar vivo.json (así, si esto falla o se corta, el dólar no se entera), se escucha AIS_SEG
// milisegundos una región (van rotando) y se guardan las posiciones de los petroleros (tipo AIS 80-89). El tipo de barco
// viene en otro mensaje (ShipStaticData, cada ~6 min por barco): el registro de petroleros se va llenando solo en las primeras
// horas. Para gastar poco, los reportes de posición se miran sin abrir el JSON y solo se abren los de petroleros conocidos.
// Las antenas de AISStream están en la costa: en alta mar casi no hay datos. Publica barcos.json (cache 60 s) en R2.
const AIS_SEG = 20000;   // AISStream tarda varios segundos en empezar a mandar (11/11/2026: con 7 s llegaban 12 mensajes del Mar de China)
const AIS_REG = [   // [nombre, cajas [[lat sur, lon oeste], [lat norte, lon este]]]
  ['Golfo Pérsico y Ormuz', [[[22, 47], [30.5, 60]]]],
  ['Mar Rojo, Bab el-Mandeb y Suez', [[[11, 32], [31.8, 46]]]],
  ['Malaca y Singapur', [[[-1.5, 95], [7, 106]]]],
  ['Mediterráneo y Gibraltar', [[[30, -7], [42, 30]]]],
  ['Mar Negro y Bósforo', [[[40, 26], [47.5, 42]]]],
  ['Mar del Norte y Báltico', [[[48, -6], [61, 30]]]],
  ['Golfo de México, Caribe y Panamá', [[[7, -98], [31, -60]]]],
  ['Mar de China y Japón', [[[7, 106], [38, 142]]]],
  ['Mar Arábigo e India', [[[5, 55], [25, 78]]]],
  ['Atlántico sur y Cabo', [[[-38, -50], [-18, -35]], [[-38, 10], [-25, 35]]]],
];
const AIS_VIVO = 45 * 60000, AIS_QUIETO = 3 * 3600000;   // cuánto se muestra un barco sin reporte nuevo (navegando / fondeado)

const RE_MMSI = /"(?:MMSI|UserID)"\s*:\s*(\d+)/, RE_STAT = /"MessageType"\s*:\s*"ShipStaticData"/;
async function ais(env, ahora){
  if(!env.AISSTREAM_KEY) return;
  let E = {i: 0, reg: {}, pos: {}, rep: [], vis: {}, cnt: {}};
  try{ const o = await env.DATOS.get('barcos/estado.json'); if(o) E = Object.assign(E, await o.json()); }catch(e){}
  // Desde el 11/11/2026 se escuchan TODAS las zonas juntas cada minuto: medido en 20 s, Mar del Norte 832 mensajes, Mediterráneo 89,
  // Golfo de México 45, China 35, Malaca 15 y Golfo Pérsico / Mar Rojo / Arábigo 1 (AISStream casi no tiene antenas ahí). Con tan
  // poco volumen no hace falta rotar, y el registro de petroleros se llena 10 veces más rápido.
  const k = 0; E.i = 0;
  const diag = {region: 'todas las zonas', msgs: 0, pos: 0, estat: 0, err: null, ms: 0, primero: null, ultimos5s: 0};
  const t0 = Date.now(), nuevos = [];
  try{
    const r = await fetch('https://stream.aisstream.io/v0/stream', {headers: {Upgrade: 'websocket', 'user-agent': UA}});
    const ws = r.webSocket; if(!ws) throw new Error('sin websocket (' + r.status + ')');
    ws.accept();
    ws.send(JSON.stringify({APIKey: env.AISSTREAM_KEY, BoundingBoxes: AIS_REG.flatMap(r => r[1]), FilterMessageTypes: ['PositionReport', 'ShipStaticData']}));
    const dec = new TextDecoder();
    await new Promise(res => {
      let listo = false;
      const fin = () => { if(listo) return; listo = true; try{ ws.close(1000, 'fin'); }catch(e){} res(); };
      const timer = setTimeout(fin, AIS_SEG);
      ws.addEventListener('close', () => { clearTimeout(timer); fin(); });
      ws.addEventListener('error', () => { clearTimeout(timer); fin(); });
      ws.addEventListener('message', ev => {
        try{
          diag.msgs++;
          const dt = Date.now() - t0; if(diag.primero == null) diag.primero = dt; if(dt > AIS_SEG - 5000) diag.ultimos5s++;
          const s = typeof ev.data === 'string' ? ev.data : dec.decode(ev.data);
          if(diag.muestra == null) diag.muestra = s.slice(0, 300);
          // 12/11/2026: AISStream manda el JSON con espacios ("MMSI": 123): buscar con indexOf '"MMSI":' no encontraba nada y no se
          // registraba ningún barco (msgs ~1000, pos y estat 0). Ahora se busca con una expresión que acepta espacios.
          const mM = RE_MMSI.exec(s);
          if(!mM){ diag.sinMmsi = (diag.sinMmsi || 0) + 1; if(s.length < 400) diag.err = s.slice(0, 200); return; }
          const mmsi = parseInt(mM[1], 10);
          if(RE_STAT.test(s)){
            diag.estat++;
            const m = JSON.parse(s).Message.ShipStaticData, ty = m.Type | 0;
            if(ty >= 80 && ty <= 89){ const d = m.Dimension || {}; E.reg[mmsi] = [(d.A | 0) + (d.B | 0), ty - 80, String(m.Name || '').trim().slice(0, 24)]; }
            else if(E.reg[mmsi]) delete E.reg[mmsi];
            return;
          }
          if(!E.reg[mmsi]) return;
          const j = JSON.parse(s), p = j.Message && j.Message.PositionReport; if(!p) return;
          const la = p.Latitude, lo = p.Longitude;
          if(!(Math.abs(la) <= 90 && Math.abs(lo) <= 180) || (la === 0 && lo === 0)) return;   // 91/181 = sin dato
          const sog = p.Sog >= 102.2 ? null : Math.round(p.Sog * 10) / 10, cog = p.Cog >= 360 ? null : Math.round(p.Cog);
          const tu = String((j.MetaData || {}).time_utc || '').slice(0, 19);
          const t = Date.parse(tu.replace(' ', 'T') + 'Z') || Date.now();
          const x = [Math.round(la * 1e4) / 1e4, Math.round(lo * 1e4) / 1e4, sog, cog, t];
          E.pos[mmsi] = x; nuevos.push([t, mmsi, x[0], x[1], sog, cog]); diag.pos++;
        }catch(e){}
      });
    });
  }catch(e){ diag.err = String(e.message || e).slice(0, 200); }
  diag.ms = Date.now() - t0;
  for(let i = 0; i < AIS_REG.length; i++) E.vis[i] = ahora; E.cnt = {};
  for(const m in E.pos){ const p = E.pos[m], q = p[2] != null && p[2] < 1; if(ahora - p[4] > (q ? AIS_QUIETO : AIS_VIVO) || !E.reg[m]) delete E.pos[m]; }
  const regs = Object.keys(E.reg); if(regs.length > 25000) for(const m of regs.slice(0, regs.length - 25000)) delete E.reg[m];
  nuevos.sort((a, b) => a[0] - b[0]);
  E.rep = E.rep.concat(nuevos).filter(r => ahora - r[0] < 20 * 60000).slice(-600);
  await env.DATOS.put('barcos/estado.json', JSON.stringify(E));
  const b = Object.entries(E.pos).map(([m, p]) => { const g = E.reg[m]; return [+m, p[0], p[1], p[2], p[3], p[4], g[0], g[1], g[2]]; });
  const nombre = {}; for(const r of E.rep) if(E.reg[r[1]]) nombre[r[1]] = [E.reg[r[1]][0], E.reg[r[1]][2]];
  await env.DATOS.put('barcos.json', JSON.stringify({t: ahora, b, rep: E.rep.slice(-300), nombre, petroleros: regs.length,
    regiones: AIS_REG.map((r, i) => [r[0], E.vis[i] || 0]), diag, fuente: 'AISStream.io (AIS de antenas costeras)'}), JSON_META);
}

export default {
  async scheduled(ev, env, ctx){
    const t = ev.scheduledTime || Date.now();
    ctx.waitUntil((async () => { await actualizar(env, t); try{ await ais(env, Date.now()); }catch(e){} })());
    ctx.waitUntil(surtidores(env));
  },
  // Visitar la dirección del Worker muestra el estado (sin datos), para revisar que corre.
  async fetch(req, env){
    if (new URL(req.url).pathname === '/api/racha') return racha(req, env);
    if (new URL(req.url).pathname === '/api/boveda') return boveda(req, env);
    let o = null; try{ const x = await env.DATOS.get('vivo.json'); if(x) o = await x.json(); }catch(e){}
    const s = o ? {t: new Date(o.t).toISOString(), dolar: new Date(o.tDol).toISOString(), mercado: o.tMkt ? new Date(o.tMkt).toISOString() : null,
                   fuente: o.fuente || 'data912 (versión vieja)', acciones: o.stocks ? o.stocks.length : 0, bonos: o.bonds ? o.bonds.length : 0, err: o.err} : {vacio: true};
    return new Response(JSON.stringify(s, null, 1), {headers: {'content-type': 'application/json'}});
  }
};
