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

export default {
  async scheduled(ev, env, ctx){ ctx.waitUntil(actualizar(env, ev.scheduledTime || Date.now())); },
  // Visitar la dirección del Worker muestra el estado (sin datos), para revisar que corre.
  async fetch(req, env){
    let o = null; try{ const x = await env.DATOS.get('vivo.json'); if(x) o = await x.json(); }catch(e){}
    const s = o ? {t: new Date(o.t).toISOString(), dolar: new Date(o.tDol).toISOString(), mercado: o.tMkt ? new Date(o.tMkt).toISOString() : null,
                   fuente: o.fuente || 'data912 (versión vieja)', acciones: o.stocks ? o.stocks.length : 0, bonos: o.bonds ? o.bonds.length : 0, err: o.err} : {vacio: true};
    return new Response(JSON.stringify(s, null, 1), {headers: {'content-type': 'application/json'}});
  }
};
