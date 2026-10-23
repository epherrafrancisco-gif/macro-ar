// Pulso Macro: "ayudante" mínimo para que el sitio se pueda instalar como app.
// NO guarda nada: todo se pide siempre a la red, así nunca se muestran datos viejos.
// Solo si no hay conexión al abrir la página, muestra un aviso en vez de la pantalla de error del navegador.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.mode !== 'navigate') return;
  e.respondWith(fetch(e.request).catch(() => new Response(
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>Pulso Macro</title><body style="margin:0;background:#0e1319;color:#e6edf3;font:16px system-ui;display:grid;place-items:center;min-height:100vh;text-align:center;padding:24px">' +
    '<div><h1 style="font-size:22px">Pulso Macro</h1><p>No hay conexión a internet.<br>Los datos se cargan en vivo: volvé a intentar cuando tengas señal.</p>' +
    '<button onclick="location.reload()" style="margin-top:12px;padding:10px 18px;border-radius:999px;border:0;background:#6ea8dc;color:#0e1319;font-weight:600">Reintentar</button></div>',
    {headers: {'Content-Type': 'text/html; charset=utf-8'}})));
});
