// Chequeo con el motor de Safari (WebKit) en iPhone, iPad y Mac contra el sitio publicado.
// Corre en una Mac de GitHub Actions (workflow chequeo-apple.yml) y deja capturas + informe en la rama `chequeo-apple`.
import { webkit, devices } from 'playwright';
import fs from 'node:fs';

const BASE = (process.argv[2] || 'https://pulsomacro.com.ar').replace(/\/$/, '');
const OUT = 'apple'; fs.mkdirSync(OUT, { recursive: true });
const AJENO = /tradingview|goatcounter|googletagmanager|fonts\.g|tiles|cloudflareinsights|static\.cloudflare/i;
const EQUIPOS = {
  iphone: { ...devices['iPhone 15'] },
  ipad: { ...devices['iPad Pro 11'] },
  mac: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15' },
};
const INFORME = [];
const dormir = ms => new Promise(r => setTimeout(r, ms));

async function abrir(b, eq, init) {
  const ctx = await b.newContext(EQUIPOS[eq]);
  if (init) await ctx.addInitScript(init);
  // no contar estas visitas en GoatCounter
  await ctx.addInitScript(() => { try { localStorage.setItem('skipgc', 't'); localStorage.setItem('pm-yo', '1'); } catch (e) {} });
  const p = await ctx.newPage();
  const r = { errores: [], red: [] };
  p.on('pageerror', e => r.errores.push('JS: ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !AJENO.test(m.text() + (m.location().url || ''))) r.errores.push('consola: ' + m.text().slice(0, 200)); });
  p.on('response', s => { const u = s.url(); if (s.status() >= 400 && /pulsomacro/.test(u)) r.red.push(s.status() + ' ' + u); });
  p.on('requestfailed', q => { const u = q.url(); if (/pulsomacro/.test(u) && !/goatcounter/.test(u)) r.red.push('falló ' + u + ' ' + (q.failure()?.errorText || '')); });
  return { ctx, p, r };
}
async function desborde(p) {
  return p.evaluate(() => {
    const W = innerWidth; if (document.documentElement.scrollWidth <= W + 1) return null;
    const malos = [];
    for (const el of document.querySelectorAll('body *')) {
      const b = el.getBoundingClientRect(); if (b.width === 0 || b.right <= W + 1) continue;
      const cs = getComputedStyle(el); if (cs.position === 'fixed' || cs.visibility === 'hidden') continue;
      let x = el.parentElement, oculto = false;
      while (x && x !== document.body) { const o = getComputedStyle(x).overflowX; if (o === 'hidden' || o === 'auto' || o === 'scroll' || o === 'clip') { oculto = true; break; } x = x.parentElement; }
      if (!oculto) malos.push((el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + [...el.classList].join('.')) + ' → ' + Math.round(b.right) + 'px');
      if (malos.length > 5) break;
    }
    return { ancho: document.documentElement.scrollWidth, pantalla: W, elementos: malos };
  });
}
async function paso(nombre, eq, fn, init) {
  const b = await webkit.launch();
  const { ctx, p, r } = await abrir(b, eq, init);
  const fila = { eq, nombre, ok: true, notas: [] };
  try { await fn(p, fila); }
  catch (e) { fila.ok = false; fila.notas.push('FALLÓ: ' + String(e.message || e).split('\n')[0]); }
  try { const d = await desborde(p); if (d) { fila.ok = false; fila.notas.push('Se sale de la pantalla: ' + JSON.stringify(d)); } } catch (e) {}
  try { await p.screenshot({ path: `${OUT}/${eq}-${nombre}.png`, timeout: 30000 }); } catch (e) {}
  if (r.errores.length) { fila.ok = false; fila.notas.push(...[...new Set(r.errores)].slice(0, 6)); }
  if (r.red.length) { fila.ok = false; fila.notas.push(...[...new Set(r.red)].slice(0, 6).map(x => 'red: ' + x)); }
  INFORME.push(fila); console.log((fila.ok ? 'OK   ' : 'MAL  ') + eq + ' ' + nombre + (fila.notas.length ? '\n     ' + fila.notas.join('\n     ') : ''));
  await ctx.close(); await b.close();
}
const ir = (p, ruta) => p.goto(BASE + ruta, { waitUntil: 'load', timeout: 60000 });
const tema = (t, extra) => new Function(`try{localStorage.setItem('pm-tema','${t}');${extra || ''}}catch(e){}`);

for (const eq of Object.keys(EQUIPOS)) {
  // portada en los cuatro modos
  await paso('inicio-oscuro', eq, async p => { await ir(p, '/'); await dormir(3500); });
  await paso('inicio-claro', eq, async p => { await ir(p, '/'); await dormir(3000); }, tema('claro'));
  await paso('inicio-ciudad', eq, async p => { await ir(p, '/'); await dormir(3000);
    if (await p.evaluate(() => document.documentElement.dataset.tema) !== 'cyber') throw new Error('no quedó en modo Ciudad'); },
    tema('cyber', "localStorage.setItem('pm-ciudad','1');"));
  await paso('inicio-orbita', eq, async (p, f) => { await ir(p, '/');
    if (await p.evaluate(() => document.documentElement.dataset.tema) !== 'orbita') throw new Error('no quedó en modo Órbita');
    await p.waitForSelector('#orFx canvas.tierra.on', { state: 'attached', timeout: 25000 });
    const n = await p.evaluate(() => new Promise(ok => { const g = document.querySelector('#orFx canvas.tierra').getContext('webgl2'); let k = 0; const o = g.drawArrays.bind(g); g.drawArrays = (...a) => { k++; return o(...a); }; setTimeout(() => ok(k), 3000); }));
    f.notas.push(`Tierra: ${n} cuadros en 3 s` + (eq === 'iphone' ? ' (en celular tiene que ser 0)' : ''));
    if (eq === 'iphone' && n > 0) throw new Error('en el iPhone la Tierra gira (tendría que estar quieta)');
    if (eq === 'mac' && n === 0) throw new Error('en la Mac la Tierra no gira');
    await dormir(1500); },
    tema('orbita', "localStorage.setItem('pm-orbita','1');"));
  // volver desde Verdadero o falso con Órbita: que no salte
  await paso('orbita-volver', eq, async (p, f) => { await ir(p, '/'); await p.waitForSelector('#orFx canvas.tierra.on', { state: 'attached', timeout: 25000 }); await dormir(1500);
    await ir(p, '/verdadero-o-falso/'); await dormir(1500);
    const g = await p.evaluate(() => !!sessionStorage.getItem('pm-tierra')); f.notas.push('foto guardada al salir: ' + (g ? 'sí' : 'NO'));
    if (!g) throw new Error('no guardó la foto de la Tierra al salir');
    await p.goBack({ waitUntil: 'commit' }); await dormir(250);
    const fondo = await p.evaluate(() => { const t = document.querySelector('#orFx .tie'); return t && t.style.background.slice(0, 40); });
    f.notas.push('fondo al volver: ' + fondo);
    if (!/data:image/.test(fondo || '')) throw new Error('al volver no mostró la foto (puede saltar)'); },
    tema('orbita', "localStorage.setItem('pm-orbita','1');"));
  // cambio de modo con el botón
  await paso('boton-modo', eq, async (p, f) => { await ir(p, '/'); await dormir(2000);
    const b = p.locator('button[data-tema]:visible').first(); const a = await p.evaluate(() => document.documentElement.dataset.tema || 'oscuro');
    await b.click(); await dormir(600); const d = await p.evaluate(() => document.documentElement.dataset.tema || 'oscuro');
    f.notas.push(`${a} → ${d}`); if (a === d) throw new Error('el botón de modo no cambió nada'); });
  // buscador
  await paso('buscador', eq, async (p, f) => { await ir(p, '/'); await dormir(2500);
    await p.locator('[data-bus]:visible').first().click(); await dormir(400);
    await p.keyboard.type('dolar blu'); await dormir(800);
    const n = await p.evaluate(() => document.querySelectorAll('#bus a, #bus button, #bus li').length);
    f.notas.push('resultados: ' + n); if (n < 2) throw new Error('el buscador no mostró resultados'); });
  // secciones
  for (const [n, h] of [['dolares', '/#dolares'], ['mercado', '/#mercado'], ['noticias', '/#noticias'], ['calculadoras', '/#calculadoras'], ['mundo', '/#global'], ['eeuu', '/#eeuu'], ['polonia', '/#polonia'], ['sobre', '/#sobre']])
    await paso('seccion-' + n, eq, async p => { await ir(p, h); await dormir(4500); });
  for (const [n, u] of [['terminal', '/terminal/'], ['indicador-blue', '/dolar-blue-hoy/'], ['indicadores', '/indicadores/']])
    await paso(n, eq, async p => { await ir(p, u); await dormir(3500); });
  // Verdadero o falso: responder una
  await paso('verdadero-o-falso', eq, async (p, f) => { await ir(p, '/verdadero-o-falso/'); await dormir(2500);
    const btn = p.locator('button:has-text("Verdadero"):visible').first();
    if (!(await btn.count())) { await p.mouse.wheel(0, 900); await dormir(1500); }
    await p.locator('button:has-text("Verdadero")').first().scrollIntoViewIfNeeded(); await dormir(800);
    await p.locator('button:has-text("Verdadero")').first().click(); await dormir(1800);
    const est = await p.evaluate(() => document.querySelector('.reel.gano') ? 'acertó' : document.querySelector('.reel.perdio') ? 'erró' : 'nada');
    f.notas.push('al responder: ' + est); if (est === 'nada') throw new Error('al tocar Verdadero no pasó nada');
    const rail = await p.evaluate(() => document.querySelectorAll('.rail').length); if (rail) throw new Error('siguen los botones Compartir/Ver más'); });
  // Mundo › Espacio: la animación dibuja y no hay nada fuera de las tarjetas
  await paso('mundo-espacio', eq, async (p, f) => { await ir(p, '/#global'); await dormir(3000);
    await p.evaluate(() => document.querySelector('#gSubM [data-s="espacio"]').click()); await dormir(2500);
    await p.evaluate(() => document.getElementById('espOrb')?.scrollIntoView({block: 'center'})); await dormir(2500);
    const r = await p.evaluate(() => { const c = document.getElementById('espOrb'); if (!c) return {err: 'no está la animación'};
      const x = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < x.length; i += 40) if (x[i]) n++;
      const sale = [...document.querySelectorAll('[data-sub="espacio"] .card *')].filter(e => { const card = e.closest('.card'), a = e.getBoundingClientRect(), b = card.getBoundingClientRect(); return a.width && (a.right > b.right + 1 || a.left < b.left - 1) && !e.closest('.tablewrap'); }).length;
      return {pintado: n, sale}; });
    f.notas.push('animación: ' + JSON.stringify(r)); if (r.err) throw new Error(r.err); if (!r.pintado) throw new Error('la animación de Espacio no dibuja'); if (r.sale) throw new Error(r.sale + ' cosas se salen de las tarjetas'); });
  // Monitor en modo claro (solo compu)
  if (eq === 'mac') await paso('monitor-claro', eq, async (p, f) => { await ir(p, '/#global'); await dormir(3000);
    await p.evaluate(() => document.querySelector('#gSubM [data-s="explorar"]')?.click()); await dormir(6000);
    const bg = await p.evaluate(() => getComputedStyle(document.getElementById('xpW')).backgroundImage.slice(0, 60)); f.notas.push('fondo: ' + bg);
    if (!/251, 241, 220|fbf1dc/.test(bg)) throw new Error('el Monitor no quedó dorado en modo claro'); }, tema('claro'));
  // Crucigrama en modo claro: la lista de pistas sigue a la palabra elegida (compu)
  if (eq === 'mac') await paso('crucigrama-lista', eq, async (p, f) => { await ir(p, '/crucigrama/'); await dormir(2500);
    await p.evaluate(() => { const c = window.__cruci._p.filter(q => q.dy).sort((a, b) => b.n - a.n)[0]; window.__cruci._ir(c.x, c.y, 'v'); }); await dormir(1200);
    const v = await p.evaluate(() => { const li = document.querySelector('.pistas li.act'); if (!li) return false; const r = li.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; });
    f.notas.push('pista a la vista: ' + v); if (!v) throw new Error('la lista no bajó hasta la pista elegida'); }, tema('claro'));
  // Crucigrama: escribir una letra
  await paso('crucigrama', eq, async (p, f) => { await ir(p, '/crucigrama/'); await dormir(2500);
    const c = p.locator('#grid input:not([readonly])').first(); await c.click(); await p.keyboard.type('A'); await dormir(400);
    const v = await p.evaluate(() => [...document.querySelectorAll('#grid input')].some(i => i.value === 'A'));
    f.notas.push('escribir una letra: ' + (v ? 'anda' : 'NO anda')); if (!v) throw new Error('no se puede escribir en el crucigrama'); });
}

const malos = INFORME.filter(x => !x.ok);
let md = `# Chequeo con Safari (WebKit) · ${new Date().toISOString().slice(0, 16)} UTC\n\nSitio: ${BASE}\n\n**${INFORME.length - malos.length} de ${INFORME.length} bien**\n\n`;
for (const x of INFORME) md += `- ${x.ok ? '✅' : '❌'} **${x.eq}** ${x.nombre}${x.notas.length ? '\n  - ' + x.notas.join('\n  - ') : ''}\n`;
fs.writeFileSync(`${OUT}/informe.md`, md); fs.writeFileSync(`${OUT}/informe.json`, JSON.stringify(INFORME, null, 1));
console.log(`\n${INFORME.length - malos.length}/${INFORME.length} bien`);
