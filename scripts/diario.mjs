// Genera la imagen diaria para redes (diario/hoy.png, 1080x1350) y el texto del
// posteo (diario/texto.txt) a partir de scripts/diario.html y data.json.
// Uso: node scripts/diario.mjs   (necesita playwright-core y un Chrome/Chromium;
// la ruta se toma de CHROME_PATH o se busca en las ubicaciones habituales).
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const TIPOS = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.png': 'image/png' };

const chrome = [process.env.CHROME_PATH, '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium', '/usr/bin/chromium-browser', '/opt/pw-browsers/chromium'].find(p => p && existsSync(p));
if (!chrome) { console.error('No encontré Chrome/Chromium (definí CHROME_PATH).'); process.exit(1); }

// Servidor mínimo para que la plantilla pueda leer ../data.json con fetch.
const server = createServer(async (req, res) => {
  const ruta = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const archivo = join(ROOT, ruta);
  if (!archivo.startsWith(ROOT)) { res.writeHead(403).end(); return; }
  try {
    const body = await readFile(archivo);
    res.writeHead(200, { 'Content-Type': TIPOS[extname(archivo)] || 'application/octet-stream' }).end(body);
  } catch { res.writeHead(404).end(); }
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/scripts/diario.html`;

const browser = await chromium.launch({ executablePath: chrome });
try {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, locale: 'es-AR', timezoneId: 'America/Argentina/Buenos_Aires' });
  page.on('pageerror', e => console.error('Error en la plantilla:', e.message));
  await page.goto(url);
  await page.waitForSelector('body[data-listo], body[data-error]', { timeout: 30000 });
  const error = await page.getAttribute('body', 'data-error');
  if (error) throw new Error(error);
  await page.waitForTimeout(300);
  await mkdir(join(ROOT, 'diario'), { recursive: true });
  await page.screenshot({ path: join(ROOT, 'diario', 'hoy.png') });
  const texto = await page.evaluate(() => window.TEXTO);
  await writeFile(join(ROOT, 'diario', 'texto.txt'), texto + '\n', 'utf8');
  console.log('Imagen y texto generados:\n' + texto);
} finally {
  await browser.close();
  server.close();
}
