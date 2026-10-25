// Worker "pulso-vivo": una vez por minuto trae el dólar (DolarApi) y, cada 5 minutos, acciones y bonos
// (data912), y guarda todo en R2 como vivo.json. La página lo lee desde datos.pulsomacro.com.ar con la
// marca del minuto (?t=VER()), así Cloudflare lo sirve de su caché y las fuentes reciben 1 pedido por minuto
// en total, no uno por cada visitante. Si una fuente falla, se conserva el último dato bueno.
// Bindings: R2 bucket "DATOS". Cron: "* * * * *".

const DOLAR = 'https://dolarapi.com/v1/dolares';
const MKT = 'https://data912.com/live/';
const UA = {headers: {'user-agent': 'pulsomacro.com.ar (contacto@pulsomacro.com.ar)'}};

async function traer(url){
  const r = await fetch(url, UA);
  if(!r.ok) throw new Error(url + ' ' + r.status);
  return r.json();
}

async function actualizar(env, ahora){
  let prev = {};
  try{ const o = await env.DATOS.get('vivo.json'); if(o) prev = await o.json(); }catch(e){}
  const out = {t: ahora, dolares: prev.dolares || null, tDol: prev.tDol || 0,
               stocks: prev.stocks || null, bonds: prev.bonds || null, tMkt: prev.tMkt || 0, err: []};
  try{
    const d = await traer(DOLAR);
    if(Array.isArray(d) && d.length){ out.dolares = d; out.tDol = ahora; }
  }catch(e){ out.err.push('dolar'); }
  if(new Date(ahora).getUTCMinutes() % 5 === 0 || !out.stocks){
    try{
      const [s, b] = await Promise.all([traer(MKT + 'arg_stocks'), traer(MKT + 'arg_bonds')]);
      if(Array.isArray(s) && s.length){ out.stocks = s; out.bonds = Array.isArray(b) ? b : out.bonds; out.tMkt = ahora; }
    }catch(e){ out.err.push('mercado'); }
  }
  await env.DATOS.put('vivo.json', JSON.stringify(out), {
    httpMetadata: {contentType: 'application/json; charset=utf-8', cacheControl: 'public, max-age=60'}
  });
  return out;
}

export default {
  async scheduled(ev, env, ctx){ ctx.waitUntil(actualizar(env, ev.scheduledTime || Date.now())); },
  // Visitar la dirección del Worker muestra el estado (sin datos), para revisar que corre.
  async fetch(req, env){
    let o = null; try{ const x = await env.DATOS.get('vivo.json'); if(x) o = await x.json(); }catch(e){}
    const s = o ? {t: new Date(o.t).toISOString(), dolar: new Date(o.tDol).toISOString(), mercado: new Date(o.tMkt).toISOString(), err: o.err} : {vacio: true};
    return new Response(JSON.stringify(s, null, 1), {headers: {'content-type': 'application/json'}});
  }
};
