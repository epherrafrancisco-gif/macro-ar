/* Modo Coder (pedido del dueño 08/11/2026): premio secreto de 80 seguidas en Verdadero o falso. Código que corre y cables de
   colores que llevan y traen datos por toda la pantalla, como si vieras por dentro el software de una IA. Lienzo 2D sin librerías.
   Capas: fondo fijo → columnas de código que suben (dibujadas una vez en lienzos aparte) → cables fijos (un lienzo) → paquetes de
   datos con estela (cada cuadro) → nodos (luces y medidores, cada cuadro). 30 cuadros/s en compu, 24 en celular (menos de todo),
   se frena con la pestaña oculta; con reducir movimiento queda un cuadro fijo.
   Uso: en index.html se prende solo con html[data-tema="coder"] (capa #cdFx). En el juego: CoderFx.start(canvas, {lite: true}). */
(function () {
  const COL = ['#22d3ee', '#f472b6', '#a3e635', '#fbbf24', '#a78bfa', '#fb7185', '#34d399', '#60a5fa', '#f97316'];
  const CODE = `import math
from pulso import feeds, modelo
from pulso.nn import Transformer, softmax

class Atencion(Modulo):
    def __init__(self, d, cabezas=32):
        self.q = Lineal(d, d)
        self.k = Lineal(d, d)
        self.v = Lineal(d, d)
        self.h = cabezas

    def forward(self, x, mascara=None):
        q, k, v = self.q(x), self.k(x), self.v(x)
        s = q @ k.T / math.sqrt(q.shape[-1])
        if mascara is not None:
            s = s.masked_fill(mascara == 0, -1e9)
        return softmax(s, dim=-1) @ v

async def escuchar(fuente):
    async for tick in feeds.stream(fuente):
        x = embed(tick.serie, dim=4096)
        y = modelo(x)
        await bus.publish("pulso.salida", y)

# 96 capas, 8 GPU, una sola cabeza que mira todo
for capa in range(96):
    h = h + atn[capa](norm(h))
    h = h + mlp[capa](norm(h))
logits = cabeza(h)
token = muestrear(logits, temp=0.7, top_p=0.95)

const series = ["mep", "ccl", "blue", "riesgo", "merval"];
for (const s of series) {
  ws.on(s, (d) => grafo.nodo(s).push(d.v));
}
function enrutar(paquete, ruta = []) {
  const n = grafo.vecinos(paquete.destino);
  return n.sort((a, b) => a.carga - b.carga)[0];
}

def gradiente(w, lote):
    perdida = entropia_cruzada(modelo(lote.x, w), lote.y)
    return perdida.backward()

opt = AdamW(params, lr=3e-4, betas=(0.9, 0.95))
for paso, lote in enumerate(datos):
    g = gradiente(w, lote)
    opt.step(g); opt.zero_grad()
    if paso % 1000 == 0:
        guardar(w, f"ckpt/{paso:07d}.pt")

let cache = new Map();   // kv-cache por capa
export const vector = (txt) => tokens(txt).map(t => E[t]);
while (true) {
  const lote = await cola.tomar(512);
  enviar(gpu[lote.id % 8], lote);
}
def mezcla_expertos(x, k=2):
    pesos = router(x).topk(k)
    return sum(p * expertos[i](x) for i, p in pesos)
`.split('\n');
  const KW = /^(def|class|return|for|in|if|is|not|None|import|from|async|await|while|true|const|let|function|export|new|with|as|self|sum|range|enumerate)$/;
  const NOMBRES = ['tokenizer', 'embed · 4096', 'attn.L12', 'attn.L47', 'attn.L95', 'kv-cache', 'mlp.gate', 'router · MoE', 'softmax',
    'logits', 'sampler', 'GPU 0', 'GPU 3', 'GPU 7', 'vector-db', 'dolar.feed', 'riesgo.pais', 'merval.ws', 'bcra.api', 'optimizer',
    'gradientes', 'shard-03', 'shard-11', 'norm', 'cola · 512', 'bus.pulso'];
  const R = Math.random, rr = (a, b) => a + R() * (b - a);

  function tokColor(w) {
    if (/^#/.test(w)) return '#5b6b80';
    if (/^["'`f]?["'`]/.test(w)) return '#a3e635';
    if (/^\d/.test(w)) return '#fbbf24';
    if (KW.test(w)) return '#f472b6';
    return null;
  }
  // una línea de código con colores: palabras, números, textos y comentarios
  function linea(ctx, txt, x, y, base) {
    const com = txt.indexOf('#') >= 0 && !/["'`]/.test(txt.slice(0, txt.indexOf('#'))) ? txt.indexOf('#') : -1;
    const cuerpo = com >= 0 ? txt.slice(0, com) : txt;
    const partes = cuerpo.match(/("[^"]*"|'[^']*'|`[^`]*`|f"[^"]*"|\d[\d.e-]*|[A-Za-z_][\w]*|\s+|.)/g) || [];
    let cx = x;
    partes.forEach((p, i) => {
      let c = tokColor(p);
      if (!c && /^[A-Za-z_]/.test(p) && partes[i + 1] === '(') c = '#22d3ee';
      if (!c && /^[A-Z]/.test(p)) c = '#a78bfa';
      ctx.fillStyle = c || base; ctx.fillText(p, cx, y); cx += ctx.measureText(p).width;
    });
    if (com >= 0) { ctx.fillStyle = '#5b6b80'; ctx.fillText(txt.slice(com), cx, y); }
  }

  function start(cv, o) {
    o = o || {};
    const lite = !!o.lite, quieto = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ctx = cv.getContext('2d');
    let W = 0, H = 0, D = 1, fondo, capaCab, cols = [], cables = [], nodos = [], nucleo, edit, vivo = true, raf = 0, last = 0, ttRes = 0;
    const FPS = lite ? 24 : 30, MAXP = lite ? 70 : 190;
    const sprite = {};
    function brillo(c) {   // punto de luz pre-dibujado por color
      if (sprite[c]) return sprite[c];
      const s = document.createElement('canvas'); s.width = s.height = 32; const g = s.getContext('2d');
      const gr = g.createRadialGradient(16, 16, 0, 16, 16, 16); gr.addColorStop(0, '#ffffff'); gr.addColorStop(.18, c); gr.addColorStop(.45, c + '66'); gr.addColorStop(1, c + '00');
      g.fillStyle = gr; g.fillRect(0, 0, 32, 32); return (sprite[c] = s);
    }
    function rect(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }

    function armar() {
      const r = cv.getBoundingClientRect(); W = Math.max(1, r.width); H = Math.max(1, r.height);
      D = Math.min(lite ? 1 : 1.25, devicePixelRatio || 1);
      cv.width = Math.round(W * D); cv.height = Math.round(H * D);
      const chico = W < 700;
      // fondo: casi negro con un tinte, grilla de puntos y viñeta
      fondo = document.createElement('canvas'); fondo.width = cv.width; fondo.height = cv.height;
      let g = fondo.getContext('2d'); g.scale(D, D);
      const gr = g.createRadialGradient(W * .5, H * .45, 0, W * .5, H * .45, Math.max(W, H) * .75);
      gr.addColorStop(0, '#071022'); gr.addColorStop(.6, '#04070f'); gr.addColorStop(1, '#020308');
      g.fillStyle = gr; g.fillRect(0, 0, W, H);
      g.fillStyle = 'rgba(120,170,255,.07)';
      for (let y = 12; y < H; y += 24) for (let x = 12; x < W; x += 24) g.fillRect(x, y, 1, 1);
      // columnas de código (cada una en su lienzo, se dibuja dos veces para que el giro no se note)
      cols = [];
      const fs = chico ? 10 : 11.5, lh = Math.round(fs * 1.55), cw = chico ? 190 : 270, gap = chico ? 14 : 34;
      const n = Math.max(2, Math.floor((W + gap) / (cw + gap)));
      const x0 = (W - (n * cw + (n - 1) * gap)) / 2;
      for (let i = 0; i < n; i++) {
        const desde = Math.floor(R() * CODE.length), lineas = [];
        for (let k = 0; k < CODE.length; k++) lineas.push(CODE[(desde + k) % CODE.length]);
        const c = document.createElement('canvas'), hh = lineas.length * lh;
        c.width = Math.round(cw * D); c.height = Math.round(hh * D);
        const cg = c.getContext('2d'); cg.scale(D, D); cg.font = `${fs}px "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace`; cg.textBaseline = 'top';
        lineas.forEach((t, k) => { cg.fillStyle = '#3c4d63'; cg.fillText(String((desde + k) % CODE.length + 1).padStart(3, ' '), 0, k * lh); linea(cg, t, fs * 2.6, k * lh, '#9fb3c8'); });
        cols.push({c, x: x0 + i * (cw + gap), w: cw, h: hh, y: R() * hh, v: rr(10, 34) * (R() < .5 ? 1 : 1.4), a: rr(.16, .3)});
      }
      // un editor donde el código se escribe en vivo, letra por letra
      edit = {x: chico ? 10 : 22, y: H - (chico ? 128 : 176), w: chico ? Math.min(W - 20, 300) : 400, h: chico ? 118 : 160, fs, lh, ln: Math.floor(R() * CODE.length), ch: 0, hecho: [], t: 0};
      // nodos: el núcleo (anillo de Pulso Macro) en el medio y chips alrededor en una grilla con ruido
      nucleo = {x: W * .5, y: H * (chico ? .42 : .46), r: Math.min(W, H) * (chico ? .085 : .075) + 10, fl: 0, ondas: []};
      nodos = [];
      const gc = chico ? 3 : Math.max(4, Math.round(W / 300)), gf = chico ? Math.max(2, Math.round(H / 170)) : Math.max(2, Math.round(H / 220));
      const nombres = NOMBRES.slice().sort(() => R() - .5);
      for (let f = 0; f < gf; f++) for (let c = 0; c < gc; c++) {
        const cx = (c + .5) / gc * W + rr(-.28, .28) * W / gc, cy = (f + .5) / gf * H + rr(-.25, .25) * H / gf;
        if (Math.hypot((cx - nucleo.x) / W, (cy - nucleo.y) / H) < (chico ? .2 : .16)) continue;
        if (R() < (chico ? .12 : .18)) continue;
        const w = chico ? 84 : rr(104, 136), h = chico ? 30 : 40;
        nodos.push({x: Math.max(6, Math.min(W - w - 6, cx - w / 2)), y: Math.max(6, Math.min(H - h - 6, cy - h / 2)), w, h,
          nom: nombres[nodos.length % nombres.length], col: COL[Math.floor(R() * COL.length)], fl: 0, bar: Array.from({length: 7}, R), led: R()});
      }
      nodos.forEach(n => { n.cx = n.x + n.w / 2; n.cy = n.y + n.h / 2; });
      // cables: cada chip al núcleo, a uno o dos vecinos, y algunos que entran desde afuera de la pantalla
      cables = [];
      const punto = (n, hacia) => n === nucleo ? {x: nucleo.x + Math.cos(hacia) * nucleo.r * .82, y: nucleo.y + Math.sin(hacia) * nucleo.r * .82} : {x: n.cx + Math.cos(hacia) * n.w * .45, y: n.cy + Math.sin(hacia) * n.h * .4};
      const cable = (a, b, col, an) => {
        const ax = a.cx != null ? a.cx : a.x, ay = a.cy != null ? a.cy : a.y, bx = b.cx != null ? b.cx : b.x, by = b.cy != null ? b.cy : b.y;
        const ang = Math.atan2(by - ay, bx - ax);
        const p0 = a.w || a === nucleo ? punto(a, ang) : {x: ax, y: ay}, p3 = b.w || b === nucleo ? punto(b, ang + Math.PI) : {x: bx, y: by};
        const d = Math.hypot(p3.x - p0.x, p3.y - p0.y), cae = Math.min(140, d * .22) * (R() < .5 ? 1 : -.6), tw = rr(-.25, .25) * d;
        const p1 = {x: p0.x + (p3.x - p0.x) * .3 - (p3.y - p0.y) / d * tw * .4, y: p0.y + (p3.y - p0.y) * .3 + cae};
        const p2 = {x: p0.x + (p3.x - p0.x) * .7 + (p3.y - p0.y) / d * tw * .4, y: p0.y + (p3.y - p0.y) * .7 + cae};
        // muestreo parejo cada 4 px (así un paquete avanza por índice)
        const fino = []; for (let i = 0; i <= 80; i++) { const u = i / 80, m = 1 - u; fino.push([m * m * m * p0.x + 3 * m * m * u * p1.x + 3 * m * u * u * p2.x + u * u * u * p3.x, m * m * m * p0.y + 3 * m * m * u * p1.y + 3 * m * u * u * p2.y + u * u * u * p3.y]); }
        const pts = [fino[0]]; let acc = 0;
        for (let i = 1; i < fino.length; i++) { const [x1, y1] = fino[i - 1], [x2, y2] = fino[i]; let seg = Math.hypot(x2 - x1, y2 - y1), t = 0;
          while (acc + seg - t >= 4) { t += 4 - acc; acc = 0; const u = t / seg; pts.push([x1 + (x2 - x1) * u, y1 + (y2 - y1) * u]); } acc += seg - t; }
        pts.push(fino[fino.length - 1]);
        cables.push({pts, col: col || COL[Math.floor(R() * COL.length)], ancho: (lite ? rr(1.6, 2.6) : rr(2, 3.6)) * (an || 1), a, b, paq: [], ritmo: rr(.25, 1.1), prox: R() * 1.5});
      };
      nodos.forEach(n => cable(n, nucleo, n.col, 1.15));
      nodos.forEach(n => { const v = nodos.filter(m => m !== n).sort((p, q) => Math.hypot(p.cx - n.cx, p.cy - n.cy) - Math.hypot(q.cx - n.cx, q.cy - n.cy));
        v.slice(0, R() < .5 ? 1 : 2).forEach(m => { if (!cables.some(c => (c.a === m && c.b === n))) cable(n, m); }); });
      const borde = () => { const s = Math.floor(R() * 4); return s === 0 ? {x: -30, y: R() * H} : s === 1 ? {x: W + 30, y: R() * H} : s === 2 ? {x: R() * W, y: -30} : {x: R() * W, y: H + 30}; };
      for (let i = 0; i < (chico ? 5 : 10); i++) cable(borde(), R() < .35 ? nucleo : nodos[Math.floor(R() * nodos.length)] || nucleo, null, R() < .3 ? 1.6 : 1);
      // capa fija: cables como tubos (sombra, color, brillo) y el cuerpo de los chips
      capaCab = document.createElement('canvas'); capaCab.width = cv.width; capaCab.height = cv.height;
      g = capaCab.getContext('2d'); g.scale(D, D); g.lineCap = 'round'; g.lineJoin = 'round';
      const trazo = (c, w, s) => { g.beginPath(); c.pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.lineWidth = w; g.strokeStyle = s; g.stroke(); };
      cables.forEach(c => { trazo(c, c.ancho + 3, 'rgba(0,0,0,.55)'); trazo(c, c.ancho, c.col + '88'); g.save(); g.translate(-.5, -.7); trazo(c, Math.max(.6, c.ancho * .28), 'rgba(255,255,255,.22)'); g.restore(); });
      nodos.forEach(n => {
        rect(g, n.x, n.y, n.w, n.h, 6); g.fillStyle = 'rgba(6,10,20,.92)'; g.fill(); g.lineWidth = 1; g.strokeStyle = n.col + '88'; g.stroke();
        g.fillStyle = n.col; g.fillRect(n.x, n.y + 6, 2, n.h - 12);
        g.font = `600 ${chico ? 9.5 : 11}px "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace`; g.textBaseline = 'top'; g.fillStyle = '#dbe7f5';
        g.fillText(n.nom, n.x + 9, n.y + (chico ? 5 : 7));
        for (let k = 0; k < 4; k++) { g.fillStyle = n.col + '55'; g.fillRect(n.x - 3, n.y + 9 + k * (n.h - 18) / 3, 3, 2); g.fillRect(n.x + n.w, n.y + 9 + k * (n.h - 18) / 3, 3, 2); }
      });
    }

    function lanzar(c, grande) {
      const n = c.pts.length; if (n < 3) return;
      const ida = R() < .62;   // más datos van hacia el núcleo que al revés
      c.paq.push({i: ida ? 0 : n - 1, d: ida ? 1 : -1, v: (grande ? rr(420, 640) : rr(110, 300)) / 4, col: R() < .25 ? '#ffffff' : c.col, tam: grande ? 1.5 : rr(.6, 1.1), cola: grande ? 34 : Math.floor(rr(6, 16))});
    }

    function cuadro(t, dt) {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
      ctx.drawImage(fondo, 0, 0);
      ctx.setTransform(D, 0, 0, D, 0, 0);
      // código que sube
      cols.forEach(c => { c.y = (c.y + c.v * dt) % c.h; ctx.globalAlpha = c.a;
        for (let y = -c.y; y < H; y += c.h) ctx.drawImage(c.c, c.x, y, c.w, c.h); });
      ctx.globalAlpha = 1;
      // editor: se escribe una línea por vez
      const e = edit; e.t += dt;
      while (e.t > .035) { e.t -= .035; const L = CODE[e.ln % CODE.length]; e.ch++; if (e.ch > L.length + 6) { e.hecho.push(L); if (e.hecho.length > Math.floor(e.h / e.lh) - 2) e.hecho.shift(); e.ln++; e.ch = 0; } }
      rect(ctx, e.x, e.y, e.w, e.h, 6); ctx.fillStyle = 'rgba(3,6,13,.86)'; ctx.fill(); ctx.strokeStyle = 'rgba(34,211,238,.35)'; ctx.lineWidth = 1; ctx.stroke();
      ctx.fillStyle = 'rgba(34,211,238,.10)'; ctx.fillRect(e.x + 1, e.y + 1, e.w - 2, 18);
      ['#fb7185', '#fbbf24', '#34d399'].forEach((c, k) => { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(e.x + 11 + k * 11, e.y + 10, 3, 0, 7); ctx.fill(); });
      ctx.font = `${e.fs}px "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace`; ctx.textBaseline = 'top';
      ctx.fillStyle = '#6b7f99'; ctx.fillText('pulso/modelo.py', e.x + 50, e.y + 4);
      ctx.save(); ctx.beginPath(); ctx.rect(e.x + 4, e.y + 20, e.w - 8, e.h - 22); ctx.clip();
      e.hecho.forEach((L, k) => linea(ctx, L, e.x + 10, e.y + 26 + k * e.lh, '#9fb3c8'));
      const act = CODE[e.ln % CODE.length].slice(0, e.ch), ya = e.y + 26 + e.hecho.length * e.lh;
      linea(ctx, act, e.x + 10, ya, '#e6edf3');
      if ((t * 2 | 0) % 2 === 0) { ctx.fillStyle = '#a3e635'; ctx.fillRect(e.x + 10 + ctx.measureText(act).width + 1, ya, Math.max(2, e.fs * .55), e.fs + 2); }
      ctx.restore();
      // cables y chips
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.drawImage(capaCab, 0, 0); ctx.setTransform(D, 0, 0, D, 0, 0);
      // paquetes
      let total = 0; cables.forEach(c => total += c.paq.length);
      ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
      cables.forEach(c => {
        c.prox -= dt;
        if (c.prox <= 0 && total < MAXP) { lanzar(c, R() < .05); total++; c.prox = rr(.15, 1.3) / c.ritmo; }
        const n = c.pts.length;
        for (let j = c.paq.length - 1; j >= 0; j--) {
          const p = c.paq[j]; p.i += p.d * p.v * dt;
          if (p.i < 0 || p.i > n - 1) { c.paq.splice(j, 1); const dest = p.d > 0 ? c.b : c.a; if (dest && dest.fl != null) { dest.fl = 1; if (dest === nucleo && nucleo.ondas.length < 6 && R() < .35) nucleo.ondas.push(0); } continue; }
          const k = p.i | 0, k0 = Math.max(0, Math.min(n - 1, k - p.d * p.cola));
          ctx.beginPath(); ctx.moveTo(c.pts[k0][0], c.pts[k0][1]);
          for (let q = k0; q !== k; q += p.d) ctx.lineTo(c.pts[q][0], c.pts[q][1]);
          ctx.strokeStyle = p.col + '55'; ctx.lineWidth = c.ancho * p.tam * 1.4; ctx.stroke();
          const s = (lite ? 16 : 22) * p.tam, [x, y] = c.pts[k];
          ctx.drawImage(brillo(p.col), x - s / 2, y - s / 2, s, s);
        }
      });
      // núcleo: el anillo de Pulso Macro latiendo, con ondas cuando le llegan datos
      const N = nucleo; N.fl = Math.max(0, N.fl - dt * 2.2);
      const late = .5 + .5 * Math.sin(t * 5.2);
      const ng = ctx.createRadialGradient(N.x, N.y, 0, N.x, N.y, N.r * 2.4); ng.addColorStop(0, `rgba(34,211,238,${.22 + .14 * N.fl})`); ng.addColorStop(1, 'rgba(34,211,238,0)');
      ctx.fillStyle = ng; ctx.fillRect(N.x - N.r * 2.4, N.y - N.r * 2.4, N.r * 4.8, N.r * 4.8);
      N.ondas = N.ondas.map(o => o + dt * .9).filter(o => o < 1);
      N.ondas.forEach(o => { ctx.beginPath(); ctx.arc(N.x, N.y, N.r * (1 + o * 1.8), 0, 7); ctx.strokeStyle = `rgba(167,139,250,${.5 * (1 - o)})`; ctx.lineWidth = 2; ctx.stroke(); });
      ctx.globalCompositeOperation = 'source-over';
      ctx.beginPath(); ctx.arc(N.x, N.y, N.r, 0, 7); ctx.fillStyle = '#060b16'; ctx.fill();
      ctx.save(); ctx.translate(N.x, N.y);
      ctx.rotate(t * .35); ctx.setLineDash([N.r * .18, N.r * .12]); ctx.beginPath(); ctx.arc(0, 0, N.r * 1.12, 0, 7); ctx.strokeStyle = 'rgba(244,114,182,.7)'; ctx.lineWidth = 2; ctx.stroke();
      ctx.rotate(-t * .8); ctx.setLineDash([N.r * .05, N.r * .1]); ctx.beginPath(); ctx.arc(0, 0, N.r * 1.26, 0, 7); ctx.strokeStyle = 'rgba(163,230,53,.55)'; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.restore(); ctx.setLineDash([]);
      ctx.beginPath(); ctx.arc(N.x, N.y, N.r * .69, 0, 7); ctx.strokeStyle = '#6aa8d8'; ctx.lineWidth = N.r * .16; ctx.shadowColor = '#22d3ee'; ctx.shadowBlur = 14 + 10 * late; ctx.stroke();
      const sc = N.r * .69 / 176; ctx.beginPath();
      [[97.6, 270], [205.6, 270], [230.8, 216], [259.6, 342], [288.4, 171], [313.6, 270], [414.4, 270]].forEach(([x, y], i) => { const px = N.x + (x - 256) * sc, py = N.y + (y - 256) * sc; i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
      ctx.strokeStyle = '#eef6ff'; ctx.lineWidth = N.r * .13; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke(); ctx.shadowBlur = 0;
      // chips: luz cuando les llega algo, leds y medidores que se mueven
      ctx.font = `${W < 700 ? 8.5 : 9.5}px "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace`;
      nodos.forEach(n => {
        n.fl = Math.max(0, n.fl - dt * 2.6);
        if (n.fl > .02) { rect(ctx, n.x - 1, n.y - 1, n.w + 2, n.h + 2, 7); ctx.strokeStyle = n.col; ctx.globalAlpha = n.fl; ctx.lineWidth = 1.6; ctx.shadowColor = n.col; ctx.shadowBlur = 12; ctx.stroke(); ctx.shadowBlur = 0; ctx.globalAlpha = 1; }
        const by = n.y + n.h - 7, bw = 3, bh = n.h * .32;
        n.bar = n.bar.map(b => Math.max(.08, Math.min(1, b + (R() - .5) * dt * 6 + n.fl * .2)));
        n.bar.forEach((b, k) => { ctx.fillStyle = n.col + 'cc'; ctx.fillRect(n.x + n.w - 9 - (6 - k) * (bw + 2), by - b * bh, bw, b * bh); });
        n.led = (n.led + dt * rr(.4, 2.2)) % 1;
        ['#34d399', n.col, '#fbbf24'].forEach((c, k) => { ctx.fillStyle = (n.led + k * .33) % 1 < .5 ? c : '#1c2433'; ctx.fillRect(n.x + 9 + k * 7, by - 3, 4, 4); });
      });
    }

    function bucle(t) {
      if (!vivo) return;
      raf = requestAnimationFrame(bucle);
      if (document.hidden) return;
      if (t - last < 1000 / FPS - 2) return;
      const dt = Math.min(.1, (t - (last || t)) / 1000); last = t;
      cuadro(t / 1000, dt);
    }
    const alCambiar = () => { clearTimeout(ttRes); ttRes = setTimeout(() => { armar(); if (quieto) cuadro(1, 0); }, 180); };
    armar();
    if (quieto) { for (let i = 0; i < 40; i++) cuadro(i / 30, 1 / 30); }   // un cuadro fijo con algunos paquetes ya en camino
    else raf = requestAnimationFrame(bucle);
    addEventListener('resize', alCambiar);
    return {stop() { vivo = false; cancelAnimationFrame(raf); removeEventListener('resize', alCambiar); }};
  }
  window.CoderFx = {start};

  // en el sitio: se prende y se apaga solo según el modo puesto
  const capa = document.getElementById('cdFx');
  if (capa) {
    let h = null;
    const ver = () => {
      const on = document.documentElement.dataset.tema === 'coder';
      if (on && !h) { const cv = capa.querySelector('canvas'); h = start(cv, {lite: matchMedia('(pointer:coarse)').matches || Math.min(innerWidth, innerHeight) < 600}); }
      else if (!on && h) { h.stop(); h = null; }
    };
    new MutationObserver(ver).observe(document.documentElement, {attributes: true, attributeFilter: ['data-tema']});
    ver();
  }
})();
