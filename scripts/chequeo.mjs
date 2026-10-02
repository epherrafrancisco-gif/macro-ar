// Chequeo automático del sitio publicado. Lo corre .github/workflows/chequeo-sitio.yml.
// Revisa que los datos estén al día, que las fuentes respondan y que cada pestaña
// dibuje sus gráficos sin errores. Escribe el informe en chequeo.md y sale con
// código 1 si encontró un problema grave (el workflow abre entonces un aviso).
// Uso: node scripts/chequeo.mjs [URL]   (necesita playwright-core y Chrome).
import { writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { chromium } from 'playwright-core';

const URL_SITIO = (process.argv[2] || 'https://epherrafrancisco-gif.github.io/macro-ar/').replace(/\/?$/, '/');
const chrome = [process.env.CHROME_PATH, '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium', '/opt/pw-browsers/chromium'].find(p => p && existsSync(p));
const errores = [], avisos = [], ok = [];
const ahora = new Date();
const hoyAR = ahora.toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' });
const horaAR = +ahora.toLocaleString('en-US', { timeZone: 'America/Argentina/Buenos_Aires', hour: '2-digit', hour12: false });
const dias = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 864e5);

async function json(ruta) {
  const r = await fetch(URL_SITIO + ruta + '?chequeo=' + Date.now(), { cache: 'no-store' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

// 1) Datos al día
try {
  const d = await json('data.json');
  const atraso = dias(d.actualizado, hoyAR);
  const habil = new Date(hoyAR + 'T12:00:00Z').getUTCDay() % 6 !== 0;
  if (atraso > 4) errores.push(`Los datos tienen ${atraso} días de atraso (último dato: ${d.actualizado}). La actualización automática no está funcionando.`);
  else if (habil && horaAR >= 19 && atraso > 0) avisos.push(`Hoy es día hábil y después del cierre, pero el último dato es del ${d.actualizado} (puede ser feriado).`);
  else ok.push(`Datos al día (último dato: ${d.actualizado}).`);
  const ult = d.diario[d.diario.length - 1] || {};
  const faltan = ['oficial', 'mep', 'ccl', 'blue', 'riesgo'].filter(k => ult[k] == null);
  if (faltan.length) avisos.push(`En el último día faltan: ${faltan.join(', ')}.`);
  const res = [...d.diario].reverse().find(x => x.reservas != null);
  if (!res || dias(res.fecha, hoyAR) > 7) avisos.push(`Las reservas del BCRA no se actualizan desde ${res ? res.fecha : 'nunca'}.`);
  const hist = d.historico || [];
  if (!hist.length) avisos.push('Falta la historia de dólares (Dólar a precios de hoy).');
} catch (e) { errores.push(`No se pudo leer data.json del sitio: ${e.message}`); }

// 2) Fuentes con error en la última actualización
try {
  const e = await json('estado.json');
  if (e.errores?.length) avisos.push('Fuentes con error en la última actualización:\n' + e.errores.map(x => `  - ${x}`).join('\n'));
  else ok.push('Todas las fuentes respondieron en la última actualización.');
} catch (e) { avisos.push(`No se pudo leer estado.json: ${e.message}`); }

// 3) Calendario de publicaciones
try {
  const c = await json('calendario.json');
  const resta = dias(hoyAR, c.vigente_hasta);
  if (resta < 0) avisos.push(`El calendario de publicaciones venció el ${c.vigente_hasta}: hay que cargar el del semestre siguiente.`);
  else if (resta <= 21) avisos.push(`El calendario de publicaciones vence el ${c.vigente_hasta}: cargar el del semestre siguiente.`);
} catch (e) { avisos.push(`No se pudo leer calendario.json: ${e.message}`); }

// 4) La página: cada pestaña, sin errores y con sus gráficos dibujados
if (!chrome) errores.push('No hay Chrome para revisar la página.');
else {
  const browser = await chromium.launch({ executablePath: chrome });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, locale: 'es-AR', timezoneId: 'America/Argentina/Buenos_Aires' });
    const jsErr = [];
    page.on('pageerror', e => jsErr.push(e.message));
    await page.goto(URL_SITIO + '?chequeo=' + Date.now() + '#dolares', { waitUntil: 'load', timeout: 60000 });
    await page.waitForFunction(() => !document.getElementById('stamp')?.textContent.includes('Cargando'), null, { timeout: 30000 }).catch(() => {});
    for (const tab of ['dolares', 'macro', 'dinero', 'fiscal', 'mercado', 'calculadoras']) {
      await page.evaluate(t => { location.hash = t; }, tab);
      await page.waitForTimeout(tab === 'mercado' ? 6000 : 1500);
      const r = await page.evaluate(() => {
        const v = document.querySelector('section.view:not([hidden])');
        const charts = [...v.querySelectorAll('.chart[id]')];
        const vacios = charts.filter(c => !c.querySelector('svg')).map(c => (c.closest('.card')?.querySelector('h2')?.firstChild?.textContent || c.id).trim());
        return { charts: charts.length, vacios, kpis: v.querySelectorAll('.k').length, heat: v.querySelectorAll('#heat button').length, bonos: v.querySelectorAll('#tBonos tr td:nth-child(5)').length };
      });
      if (r.vacios.length) avisos.push(`Pestaña ${tab}: gráficos sin datos: ${r.vacios.join(', ')}.`);
      if (r.charts && r.vacios.length === r.charts) errores.push(`Pestaña ${tab}: ningún gráfico se dibujó.`);
      if (tab === 'mercado' && !r.heat) avisos.push('Mercado: no cargaron los precios de acciones (data912).');
      if (tab === 'calculadoras') {
        const calc = await page.evaluate(() => /equilibrio/i.test(document.getElementById('pfR')?.textContent || ''));
        calc ? ok.push('Calculadoras: funcionan.') : avisos.push('Calculadoras: la de plazo fijo no muestra resultado.');
      } else ok.push(`Pestaña ${tab}: ${r.charts - r.vacios.length}/${r.charts} gráficos, ${r.kpis} indicadores.`);
    }
    await page.evaluate(() => { location.hash = 'dolares'; });
    await page.waitForTimeout(3000);
    const vivo = await page.evaluate(() => document.getElementById('live')?.classList.contains('on'));
    if (!vivo) avisos.push('Las cotizaciones en vivo (DolarApi) no cargaron.');
    if (jsErr.length) errores.push('Errores de JavaScript en la página:\n' + [...new Set(jsErr)].map(x => `  - ${x}`).join('\n'));
    const r = await fetch(URL_SITIO + 'diario/texto.txt?chequeo=' + Date.now());
    const txt = r.ok ? await r.text() : '';
    const m = txt.match(/(\d{2})\/(\d{2})\/(\d{4})/);
    if (!m) avisos.push('No se encontró el texto de la imagen del día.');
    else if (dias(`${m[3]}-${m[2]}-${m[1]}`, hoyAR) > 4) avisos.push(`La imagen del día es vieja (${m[0]}).`);
  } catch (e) { errores.push(`No se pudo revisar la página: ${e.message}`); }
  finally { await browser.close(); }
}

const estado = errores.length ? '🔴 Hay problemas' : avisos.length ? '🟡 Funciona, con avisos' : '🟢 Todo bien';
const lista = (t, xs) => xs.length ? `\n### ${t}\n${xs.map(x => `- ${x}`).join('\n')}\n` : '';
const md = `## ${estado}\n\nChequeo del ${hoyAR} a las ${String(horaAR).padStart(2, '0')} h (hora argentina) de ${URL_SITIO}\n`
  + lista('Problemas', errores) + lista('Avisos', avisos) + lista('Bien', ok);
await writeFile('chequeo.md', md, 'utf8');
console.log(md);
process.exit(errores.length ? 1 : 0);
