// Worker "pulso-vivo": una vez por minuto trae el dólar (DolarApi) y acciones y bonos (Open BYMADATA) y guarda todo en R2 como
// vivo.json. La página lo lee desde datos.pulsomacro.com.ar con la marca del minuto (?t=VER()), así Cloudflare lo sirve de su
// caché y las fuentes reciben 1 pedido por minuto en total, no uno por cada visitante. Si una fuente falla, queda el último dato bueno.
// Acciones y bonos: Open BYMADATA, el acceso gratuito y público de BYMA (dueña del dato), que ya viene con 20 minutos de
// demora. Desde el 26/10/2026 no se usa data912 (API anónima sin licencia). Se publican los mismos precios que BYMA
// muestra gratis al público, citando a BYMA. Plazo 24 hs (T1), como se opera normalmente.
// Bindings: R2 bucket "DATOS". Cron: "* * * * *".

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

export default {
  async scheduled(ev, env, ctx){ ctx.waitUntil(actualizar(env, ev.scheduledTime || Date.now())); ctx.waitUntil(surtidores(env)); },
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
