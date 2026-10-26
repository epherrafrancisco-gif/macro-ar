// Worker "pulso-vivo": una vez por minuto trae el dólar (DolarApi) y acciones y bonos (data912), y guarda todo en R2 como vivo.json. La página lo lee desde datos.pulsomacro.com.ar con la
// marca del minuto (?t=VER()), así Cloudflare lo sirve de su caché y las fuentes reciben 1 pedido por minuto
// en total, no uno por cada visitante. Si una fuente falla, se conserva el último dato bueno.
// Acciones y bonos se publican con 20 minutos de demora (como el acceso gratuito de BYMA, Open BYMADATA): cada minuto
// se guarda una foto en un casillero (mkt/0..29.json) y en vivo.json va la foto de hace 20 minutos. Nunca más nueva.
// Bindings: R2 bucket "DATOS". Cron: "* * * * *".

const DOLAR = 'https://dolarapi.com/v1/dolares';
const MKT = 'https://data912.com/live/';
const UA = {headers: {'user-agent': 'pulsomacro.com.ar (contacto@pulsomacro.com.ar)'}};
const DEMORA = 20 * 60000, CASILLEROS = 30;
const JSON_META = {httpMetadata: {contentType: 'application/json; charset=utf-8', cacheControl: 'public, max-age=60'}};

async function traer(url){
  const r = await fetch(url, UA);
  if(!r.ok) throw new Error(url + ' ' + r.status);
  return r.json();
}
const casillero = min => 'mkt/' + (((min % CASILLEROS) + CASILLEROS) % CASILLEROS) + '.json';

async function actualizar(env, ahora){
  let prev = {};
  try{ const o = await env.DATOS.get('vivo.json'); if(o) prev = await o.json(); }catch(e){}
  const out = {t: ahora, dolares: prev.dolares || null, tDol: prev.tDol || 0,
               stocks: prev.stocks || null, bonds: prev.bonds || null, tMkt: prev.tMkt || 0, demora: DEMORA, err: []};
  // nunca publicar precios de mercado con menos de 20 minutos (por ejemplo, los que quedaron de la versión anterior)
  if(out.tMkt > ahora - DEMORA){ out.stocks = null; out.bonds = null; out.tMkt = 0; }
  try{
    const d = await traer(DOLAR);
    if(Array.isArray(d) && d.length){ out.dolares = d; out.tDol = ahora; }
  }catch(e){ out.err.push('dolar'); }
  const min = Math.floor(ahora / 60000);
  // 1) foto de este minuto, a su casillero
  try{
    const [s, b] = await Promise.all([traer(MKT + 'arg_stocks'), traer(MKT + 'arg_bonds')]);
    if(Array.isArray(s) && s.length) await env.DATOS.put(casillero(min), JSON.stringify({t: ahora, stocks: s, bonds: Array.isArray(b) ? b : null}));
  }catch(e){ out.err.push('mercado'); }
  // 2) se publica la foto de hace 20 minutos (si falta, queda la anterior, que es más vieja)
  try{
    const o = await env.DATOS.get(casillero(min - DEMORA / 60000));
    if(o){ const f = await o.json();
      if(f && Array.isArray(f.stocks) && f.t <= ahora - DEMORA + 30000 && f.t > ahora - DEMORA - 5 * 60000 && f.t > out.tMkt){
        out.stocks = f.stocks; out.bonds = f.bonds || out.bonds; out.tMkt = f.t; } }
  }catch(e){ out.err.push('demora'); }
  await env.DATOS.put('vivo.json', JSON.stringify(out), JSON_META);
  return out;
}

export default {
  async scheduled(ev, env, ctx){ ctx.waitUntil(actualizar(env, ev.scheduledTime || Date.now())); },
  // Visitar la dirección del Worker muestra el estado (sin datos), para revisar que corre.
  async fetch(req, env){
    let o = null; try{ const x = await env.DATOS.get('vivo.json'); if(x) o = await x.json(); }catch(e){}
    const s = o ? {t: new Date(o.t).toISOString(), dolar: new Date(o.tDol).toISOString(), mercado: o.tMkt ? new Date(o.tMkt).toISOString() : null,
                   demora_min: o.tMkt ? Math.round((o.t - o.tMkt) / 60000) : null, err: o.err} : {vacio: true};
    return new Response(JSON.stringify(s, null, 1), {headers: {'content-type': 'application/json'}});
  }
};
