// Crucigrama de Pulso Macro: uno por día, igual para todos (semilla = fecha de Buenos Aires).
(function () {
'use strict';
const $ = s => document.querySelector(s);
const MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];

// ---------- fecha de Buenos Aires y semilla ----------
const ahoraBA = () => new Date(Date.now() - 3 * 3600e3);                 // Argentina no tiene horario de verano
const HOY = ahoraBA().toISOString().slice(0, 10);
const N = Math.round((Date.parse(HOY) - Date.parse('2026-11-01')) / 864e5) + 1;
function semilla(txt) { let h = 2166136261; for (const c of txt) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
function azar(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// ---------- generador ----------
const V2 = HOY >= '2026-11-03';
// los N.º 1 y 2 se arman con el banco original (las 180 primeras): si no, sumar palabras cambiaba esos crucigramas
const BANCO = (V2 ? PALABRAS : PALABRAS.slice(0, 180)).filter(([p]) => /^[A-ZÑ]{3,11}$/.test(p));
// Desde el N.º 3 (pedido del dueño 02/11/2026: "no se pueden repetir palabras"): cada día recibe una "mano" de MANO palabras
// elegidas entre las que hace más tiempo que no salen (las de los N.º 1 y 2 cuentan como usadas esos días). Como el banco
// tiene ~460 palabras, una palabra no puede volver a aparecer hasta que pasen unos 10 días. Se simula día por día desde el
// N.º 3 (solo ordenar el banco: rápido aunque pasen años).
const MANO_T = 50;
const VIEJAS = {1: ['DIVIDENDO','PLAZOFIJO','INCENTIVO','INVERSION','FLOTACION','FRIEDMAN','BIGMAC','TARIFA','ZLOTY','EURO','YUAN','TASA','BCRA','FED','MEP'], 2: ['REAL','SOJA','LECAP','BOLSA','FUTURO','RIESGO','DEFAULT','ARANCEL','CORRIDA','AUSTRAL','FLOTACION','SUPERAVIT','DEFLACION','AGUINALDO','MONOTRIBUTO']};
const MAZO = (() => { if (!V2) return null;
  const ult = new Map(); for (const d in VIEJAS) VIEJAS[d].forEach(w => ult.set(w, +d));
  let mano = null;
  for (let d = 3; d <= N; d++) {
    const r = azar(semilla('pulso-mano-' + d));
    const orden = BANCO.map(e => [e, ult.has(e[0]) ? ult.get(e[0]) : -1, r()]).sort((a, b) => a[1] - b[1] || a[2] - b[2]);
    mano = orden.slice(0, MANO_T).map(x => x[0]); mano.forEach(e => ult.set(e[0], d));
  }
  return mano; })();
function armar(rnd) {
  const lista = (MAZO || BANCO).slice();
  for (let i = lista.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [lista[i], lista[j]] = [lista[j], lista[i]]; }
  const cand = lista.slice(0, V2 ? 99 : 40).sort((a, b) => b[0].length - a[0].length);
  const G = new Map(), D = new Map(), puestas = [], MAX = V2 ? 13 : 13;  // D: dirección de cada letra puesta
  const k = (x, y) => x + ',' + y, at = (x, y) => G.get(k(x, y));
  let minX = 0, maxX = 0, minY = 0, maxY = 0;
  function cabe(w, x, y, dx, dy) {
    let cruces = 0;
    if (at(x - dx, y - dy) || at(x + dx * w.length, y + dy * w.length)) return -1;
    for (let i = 0; i < w.length; i++) {
      const cx = x + dx * i, cy = y + dy * i, c = at(cx, cy);
      if (c) { if (c !== w[i]) return -1; if (V2 && D.get(k(cx, cy)) === (dx ? 'h' : 'v')) return -1; cruces++; continue; }  // v2: un cruce tiene que ser con una palabra en la otra dirección (si no, una palabra quedaba metida adentro de otra)
      if (at(cx + dy, cy + dx) || at(cx - dy, cy - dx)) return -1;      // no pegarse a otra palabra en paralelo
    }
    const nx0 = Math.min(minX, x), ny0 = Math.min(minY, y), nx1 = Math.max(maxX, x + dx * (w.length - 1)), ny1 = Math.max(maxY, y + dy * (w.length - 1));
    if (nx1 - nx0 + 1 > MAX || ny1 - ny0 + 1 > MAX) return -1;
    return cruces;
  }
  function poner(w, pista, x, y, dx, dy) {
    for (let i = 0; i < w.length; i++) { G.set(k(x + dx * i, y + dy * i), w[i]); D.set(k(x + dx * i, y + dy * i), dx ? 'h' : 'v'); }
    minX = Math.min(minX, x); minY = Math.min(minY, y); maxX = Math.max(maxX, x + dx * (w.length - 1)); maxY = Math.max(maxY, y + dy * (w.length - 1));
    puestas.push({w, pista, x, y, dx, dy});
  }
  const [w0, p0] = cand.shift(); poner(w0, p0, 0, 0, 1, 0);
  for (let vuelta = 0; vuelta < 2; vuelta++) for (let ci = 0; ci < cand.length && puestas.length < 15; ci++) {
    const [w, pista] = cand[ci]; if (!w || puestas.some(p => p.w === w)) continue;
    let mejor = null;
    for (const p of puestas) for (let i = 0; i < p.w.length; i++) for (let j = 0; j < w.length; j++) {
      if (p.w[i] !== w[j]) continue;
      const dx = p.dx ? 0 : 1, dy = p.dx ? 1 : 0;
      const x = p.x + p.dx * i - dx * j, y = p.y + p.dy * i - dy * j;
      const c = cabe(w, x, y, dx, dy);
      if (c > 0) { const sc = c * 10 + rnd(); if (!mejor || sc > mejor.sc) mejor = {x, y, dx, dy, sc}; }
    }
    if (mejor) { poner(w, pista, mejor.x, mejor.y, mejor.dx, mejor.dy); cand[ci] = []; }
  }
  return {puestas, minX, minY, ancho: maxX - minX + 1, alto: maxY - minY + 1};
}
// varias pruebas con la semilla del día; se queda con la que tiene más palabras (y más cuadrada)
let P = null;
for (let t = 0; t < (V2 ? 50 : 30); t++) {
  const r = armar(azar(semilla('pulso-cruci-' + HOY + '-' + t)));
  const sc = r.puestas.length * 100 - Math.abs(r.ancho - r.alto) * 3;
  if (!P || sc > P.sc) P = {...r, sc};
}
// numeración clásica (izquierda a derecha, arriba a abajo)
const W = P.ancho, H = P.alto, SOL = Array.from({length: H}, () => Array(W).fill(null));
P.puestas.forEach(p => { p.x -= P.minX; p.y -= P.minY; for (let i = 0; i < p.w.length; i++) SOL[p.y + p.dy * i][p.x + p.dx * i] = p.w[i]; });
const inicio = {}; let num = 0;
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
  const ps = P.puestas.filter(p => p.x === x && p.y === y); if (ps.length) { num++; inicio[x + ',' + y] = num; ps.forEach(p => p.n = num); }
}
const HOR = P.puestas.filter(p => p.dx).sort((a, b) => a.n - b.n), VER = P.puestas.filter(p => p.dy).sort((a, b) => a.n - b.n);

// ---------- estado guardado ----------
const KEY = 'pm-cruci-' + HOY;
let E = {l: {}, t: 0, fin: false, pistas: 0};
try { E = {...E, ...JSON.parse(localStorage.getItem(KEY) || '{}')}; } catch (e) {}
const guardar = () => { try { localStorage.setItem(KEY, JSON.stringify(E)); } catch (e) {} };

// ---------- dibujar ----------
const grid = $('#grid');
grid.style.setProperty('--w', W); grid.style.setProperty('--h', H);
let html = '';
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
  const s = SOL[y][x];
  if (!s) { html += '<div class="cv"></div>'; continue; }
  const n = inicio[x + ',' + y];
  html += `<div class="cl" data-x="${x}" data-y="${y}">${n ? `<span class="nm">${n}</span>` : ''}<input maxlength="2" autocomplete="off" autocapitalize="characters" spellcheck="false" inputmode="text" aria-label="Fila ${y + 1}, columna ${x + 1}" value="${E.l[x + ',' + y] || ''}"></div>`;
}
grid.innerHTML = html;
const lista = (arr, dir) => arr.map(p => `<li data-n="${p.n}" data-d="${dir}"><b>${p.n}</b> ${p.pista} <i>(${p.w.length})</i></li>`).join('');
$('#hor').innerHTML = lista(HOR, 'h'); $('#ver').innerHTML = lista(VER, 'v');
$('#fecha').textContent = `N.º ${N} · ${+HOY.slice(8)} de ${MESES[+HOY.slice(5, 7) - 1]} de ${HOY.slice(0, 4)}`;

const inp = (x, y) => grid.querySelector(`.cl[data-x="${x}"][data-y="${y}"] input`);
let dir = 'h', cur = null;
const palabraDe = (x, y, d) => P.puestas.find(p => (d === 'h' ? p.dx : p.dy) && (p.dx ? (p.y === y && x >= p.x && x < p.x + p.w.length) : (p.x === x && y >= p.y && y < p.y + p.w.length)));
function marcar() {
  grid.querySelectorAll('.cl').forEach(c => c.classList.remove('act', 'cur'));
  document.querySelectorAll('.pistas li').forEach(li => li.classList.remove('act'));
  if (!cur) return;
  let p = palabraDe(cur.x, cur.y, dir);
  if (!p) { dir = dir === 'h' ? 'v' : 'h'; p = palabraDe(cur.x, cur.y, dir); }
  if (!p) return;
  for (let i = 0; i < p.w.length; i++) inp(p.x + p.dx * i, p.y + p.dy * i).parentNode.classList.add('act');
  inp(cur.x, cur.y).parentNode.classList.add('cur');
  const li = document.querySelector(`.pistas li[data-n="${p.n}"][data-d="${dir}"]`); if (li) li.classList.add('act');
  $('#pAct').innerHTML = `<b>${p.n} ${dir === 'h' ? 'horizontal' : 'vertical'}</b> ${p.pista} <i>(${p.w.length})</i>`;
}
function ir(x, y) { const i = inp(x, y); if (!i) return false; cur = {x, y}; i.focus({preventScroll: true}); i.select(); marcar(); return true; }
grid.addEventListener('pointerdown', e => {
  const c = e.target.closest('.cl'); if (!c) return;
  const x = +c.dataset.x, y = +c.dataset.y;
  if (cur && cur.x === x && cur.y === y && palabraDe(x, y, dir === 'h' ? 'v' : 'h')) dir = dir === 'h' ? 'v' : 'h';
  else if (!palabraDe(x, y, dir)) dir = dir === 'h' ? 'v' : 'h';
  e.preventDefault(); ir(x, y);
});
document.querySelector('.pistas').addEventListener('click', e => {
  const li = e.target.closest('li'); if (!li) return;
  const p = P.puestas.find(q => q.n === +li.dataset.n && (li.dataset.d === 'h' ? q.dx : q.dy)); dir = li.dataset.d;
  irPalabra(p);
  if (matchMedia('(max-width:879px)').matches) $('#pAct').scrollIntoView({block: 'start', behavior: 'smooth'});
});
function irPalabra(p) { dir = p.dx ? 'h' : 'v'; const cs = [...Array(p.w.length).keys()].map(i => ({x: p.x + p.dx * i, y: p.y + p.dy * i})); const c = cs.find(q => !inp(q.x, q.y).value) || cs.find(q => !fija(inp(q.x, q.y))) || cs[0]; ir(c.x, c.y); }
// próxima palabra sin resolver (Enter, Tab o al terminar una)
function siguiente(p) { const L = [...HOR, ...VER], j = L.indexOf(p); for (let k = 1; k <= L.length; k++) { const q = L[(j + k) % L.length]; if (!OKW.has(q.n + (q.dx ? 'h' : 'v'))) return q; } return null; }
$('#pAct').addEventListener('click', () => { if (cur && palabraDe(cur.x, cur.y, dir === 'h' ? 'v' : 'h')) { dir = dir === 'h' ? 'v' : 'h'; marcar(); inp(cur.x, cur.y).focus(); } });
const fija = c => !!c && c.parentNode.classList.contains('okw');  // casillero de una palabra ya resuelta (no se puede cambiar)
const paso = (d) => { const dx = dir === 'h' ? d : 0, dy = dir === 'v' ? d : 0; return {x: cur.x + dx, y: cur.y + dy}; };
grid.addEventListener('input', e => {
  const i = e.target; if (!cur) return;
  let v = i.value.toUpperCase().normalize('NFD').replace(/[̀-̂̄-ͯ]/g, '').normalize('NFC').replace(/[^A-ZÑ]/g, '');
  v = v.slice(-1);
  if (fija(i)) {  // letra de una palabra ya resuelta: queda fija. Si escribiste esa misma letra, pasa a la siguiente;
    // si escribiste otra, va al próximo casillero libre de la palabra (así se puede escribir la palabra entera o solo lo que falta)
    const x = +i.parentNode.dataset.x, y = +i.parentNode.dataset.y; i.value = SOL[y][x]; E.l[x + ',' + y] = SOL[y][x];
    if (!v) return;
    let n = paso(1);
    if (v !== SOL[y][x]) { while (fija(inp(n.x, n.y))) { cur = n; n = paso(1); } const c = inp(n.x, n.y); if (!c) { marcar(); return; }
      cur = n; c.value = v; E.l[n.x + ',' + n.y] = v; c.parentNode.classList.remove('mal'); arrancarReloj(); guardar(); verdes(true); n = paso(1); }
    if (inp(n.x, n.y)) ir(n.x, n.y); else ir(cur.x, cur.y);
    revisarFin(); return;
  }
  i.value = v; E.l[cur.x + ',' + cur.y] = v; i.parentNode.classList.remove('mal');
  arrancarReloj(); guardar();
  verdes(true);
  const pa = palabraDe(cur.x, cur.y, dir);
  if (v && pa && OKW.has(pa.n + (pa.dx ? 'h' : 'v')) && !E.fin) { const q = siguiente(pa); if (q) { irPalabra(q); revisarFin(); return; } }
  if (v) { const n = paso(1); if (inp(n.x, n.y)) ir(n.x, n.y); else marcar(); }  // pasa a la siguiente aunque esté resuelta (no se saltea: si no, la letra que sigue cae en otro casillero)
  revisarFin();
});
let borroBI = 0;
grid.addEventListener('beforeinput', e => {
  if (!cur || e.inputType !== 'deleteContentBackward') return;
  const t = e.target; borroBI = Date.now();
  if (fija(t)) { e.preventDefault(); const n = paso(-1); if (inp(n.x, n.y)) ir(n.x, n.y); return; }
  if (!t.value) { e.preventDefault(); const n = paso(-1), c = inp(n.x, n.y); if (c) { ir(n.x, n.y); if (!fija(c)) { c.value = ''; E.l[n.x + ',' + n.y] = ''; guardar(); } } }
});
grid.addEventListener('keydown', e => {
  if (!cur) return;
  if (e.key === 'Backspace' && 'onbeforeinput' in grid) return;  // lo maneja beforeinput (anda también en Android)
  const mov = {ArrowRight: [1, 0, 'h'], ArrowLeft: [-1, 0, 'h'], ArrowDown: [0, 1, 'v'], ArrowUp: [0, -1, 'v']}[e.key];
  if (mov) { e.preventDefault(); dir = mov[2]; let x = cur.x + mov[0], y = cur.y + mov[1]; while (x >= 0 && y >= 0 && x < W && y < H) { if (ir(x, y)) return; x += mov[0]; y += mov[1]; } marcar(); return; }
  if (e.key === 'Backspace' && fija(e.target)) { e.preventDefault(); const n = paso(-1); if (inp(n.x, n.y)) ir(n.x, n.y); return; }
  if (e.key === 'Backspace' && !e.target.value) { e.preventDefault(); const n = paso(-1), c = inp(n.x, n.y); if (c) { ir(n.x, n.y); if (!fija(c)) { c.value = ''; E.l[n.x + ',' + n.y] = ''; guardar(); } } }
  if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); const q = siguiente(palabraDe(cur.x, cur.y, dir)); if (q) irPalabra(q); }
});

// ---------- palabras bien = verde al instante (pedido del dueño: "para ir descartando") ----------
const OKW = new Set();
function verdes(anim) {
  for (const p of P.puestas) {
    const key = p.n + (p.dx ? 'h' : 'v');
    let ok = true; for (let i = 0; i < p.w.length; i++) if ((E.l[(p.x + p.dx * i) + ',' + (p.y + p.dy * i)] || '') !== p.w[i]) { ok = false; break; }
    if (!ok || OKW.has(key)) continue;
    OKW.add(key); E.okw = [...OKW];
    for (let i = 0; i < p.w.length; i++) {
      const c = inp(p.x + p.dx * i, p.y + p.dy * i); const d = c.parentNode;
      c.value = p.w[i]; E.l[(p.x + p.dx * i) + ',' + (p.y + p.dy * i)] = p.w[i];
      d.classList.add('okw'); d.classList.remove('mal');
      if (anim) { d.style.animationDelay = (i * 45) + 'ms'; d.classList.remove('pop'); void d.offsetWidth; d.classList.add('pop'); }
    }
    const li = document.querySelector(`.pistas li[data-n="${p.n}"][data-d="${p.dx ? 'h' : 'v'}"]`); if (li) li.classList.add('hecha');
    if (anim) try { navigator.vibrate && navigator.vibrate(15); } catch (e) {}
  }
}
// arreglo del error de 11/2026: si una letra de una palabra ya resuelta quedó borrada, se repone
(function reparar() { if (!Array.isArray(E.okw)) return; let n = 0;  // las palabras ya resueltas quedan completas aunque una letra se haya borrado
  for (const p of P.puestas) if (E.okw.includes(p.n + (p.dx ? 'h' : 'v'))) for (let i = 0; i < p.w.length; i++) { const k = (p.x + p.dx * i) + ',' + (p.y + p.dy * i); if (E.l[k] !== p.w[i]) { E.l[k] = p.w[i]; const c = inp(p.x + p.dx * i, p.y + p.dy * i); if (c) c.value = p.w[i]; n++; } }
  if (n) guardar(); })();
// ---------- reloj y pista ----------
let tic = null, t0 = 0;
function fmtT(s) { return Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0'); }
function arrancarReloj() { if (tic || E.fin) return; t0 = Date.now() - E.t * 1000; tic = setInterval(() => { E.t = Math.round((Date.now() - t0) / 1000); $('#reloj').textContent = fmtT(E.t); if (E.t % 5 === 0) guardar(); }, 1000); }
$('#reloj').textContent = fmtT(E.t);
document.addEventListener('visibilitychange', () => {  // con la pestaña oculta el reloj se frena (si no, al volver aparecían horas)
  if (document.hidden) { if (tic) { clearInterval(tic); tic = null; E.t = Math.round((Date.now() - t0) / 1000); guardar(); arrancarReloj.pausado = true; } }
  else if (arrancarReloj.pausado) { arrancarReloj.pausado = false; arrancarReloj(); }
});
// pista (pedido del dueño 01/11/2026): la letra va en el casillero donde estás parado; si ese ya está bien, en uno al azar
$('#pista').onclick = () => {
  const mal = c => c.querySelector('input').value !== SOL[+c.dataset.y][+c.dataset.x];
  let c = cur ? inp(cur.x, cur.y)?.parentNode : null, aqui = !!(c && mal(c));
  if (!aqui) { const vac = [...grid.querySelectorAll('.cl')].filter(mal); if (!vac.length) return; c = vac[Math.floor(Math.random() * vac.length)]; }
  const x = +c.dataset.x, y = +c.dataset.y;
  c.querySelector('input').value = SOL[y][x]; E.l[x + ',' + y] = SOL[y][x]; E.pistas++; c.classList.add('ayu'); c.classList.remove('mal');
  arrancarReloj(); guardar(); verdes(true);
  if (aqui) { let n = paso(1); while (fija(inp(n.x, n.y))) { cur = n; n = paso(1); } if (!ir(n.x, n.y)) ir(x, y); }
  else { if (!palabraDe(x, y, dir)) dir = dir === 'h' ? 'v' : 'h'; ir(x, y); }
  revisarFin();
};
function aviso(t) { const a = $('#aviso'); a.textContent = t; a.hidden = false; clearTimeout(aviso.t); aviso.t = setTimeout(() => a.hidden = true, 3000); }

// ---------- fin ----------
const RK = 'pm-cruci-racha';
function revisarFin() {
  if (E.fin) return;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (SOL[y][x] && (E.l[x + ',' + y] || '') !== SOL[y][x]) return;
  E.fin = true; clearInterval(tic); tic = null; guardar();
  let R = {u: '', n: 0}; try { R = JSON.parse(localStorage.getItem(RK) || '{"u":"","n":0}'); } catch (e) {}
  const ayer = new Date(Date.parse(HOY) - 864e5).toISOString().slice(0, 10);
  if (R.u !== HOY) { R.n = R.u === ayer ? R.n + 1 : 1; R.u = HOY; try { localStorage.setItem(RK, JSON.stringify(R)); } catch (e) {} }
  try { window.goatcounter && goatcounter.count({path: 'cruci-resuelto', event: true}); } catch (e) {}
  festejo(R.n);
}
function festejo(dias) {
  grid.classList.add('ok');
  $('#finT').textContent = fmtT(E.t);
  $('#finP').textContent = E.pistas ? `con ${E.pistas} ${E.pistas === 1 ? 'pista' : 'pistas'}` : 'sin pistas';
  $('#finD').textContent = dias > 1 ? `${dias} días seguidos resolviéndolo` : 'Primer día de tu racha';
  $('#fin').hidden = false; confeti(140);
  const txt = `Crucigrama de economía de Pulso Macro N.º ${N}: lo resolví en ${fmtT(E.t)} ${E.pistas ? 'con ' + E.pistas + ' pistas' : 'sin pistas'}. ¿Vos?\npulsomacro.com.ar/crucigrama/`;
  $('#finSh').onclick = () => { if (navigator.share) navigator.share({text: txt}).catch(() => {}); else { navigator.clipboard && navigator.clipboard.writeText(txt); aviso('Copiado para pegar donde quieras.'); } };
  const cd = () => { const fin = Date.parse(HOY + 'T00:00:00-03:00') + 864e5, s = Math.max(0, (fin - Date.now()) / 1000);
    $('#finN').textContent = s > 0 ? `${Math.floor(s / 3600)} h ${String(Math.floor(s % 3600 / 60)).padStart(2, '0')} min` : 'unos segundos: ya salió, recargá la página'; };
  cd(); setInterval(cd, 30000);
}
$('#finX').onclick = () => $('#fin').hidden = true;
function confeti(n) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const cv = document.createElement('canvas'), dpr = Math.min(2, devicePixelRatio || 1);
  cv.className = 'confeti'; cv.width = innerWidth * dpr; cv.height = innerHeight * dpr; document.body.appendChild(cv);
  const x = cv.getContext('2d'); x.scale(dpr, dpr); const r = azar(Date.now());
  const COL = ['#7dffc4', '#ffd23d', '#ff5c8a', '#5fb4ff', '#ffffff', '#b57bff'];
  const ps = Array.from({length: n}, () => ({x: r() * innerWidth, y: -20 - r() * innerHeight * .5, vy: 2.5 + r() * 4, vx: r() * 2 - 1, s: 3 + r() * 5, c: COL[Math.floor(r() * COL.length)], g: r() * 6}));
  const t0 = performance.now();
  (function p(t) { const k = (t - t0) / 1000; x.clearRect(0, 0, innerWidth, innerHeight);
    for (const q of ps) { q.y += q.vy; q.x += q.vx + Math.sin(q.g) * .6; q.g += .08; x.save(); x.globalAlpha = Math.max(0, Math.min(1, 3 - k)); x.translate(q.x, q.y); x.rotate(q.g); x.fillStyle = q.c; x.fillRect(-q.s, -q.s / 2, q.s * 2, q.s); x.restore(); }
    if (k < 3) requestAnimationFrame(p); else cv.remove(); })(t0);
}
if (E.fin) { grid.classList.add('ok'); $('#reloj').textContent = fmtT(E.t); let R = {n: 1}; try { R = JSON.parse(localStorage.getItem(RK) || '{"n":1}'); } catch (e) {} festejo(R.n); $('#fin').hidden = true; $('#yaFin').hidden = false; }
$('#yaFin').onclick = () => $('#fin').hidden = false;
$('#ayuda').textContent = `${P.puestas.length} palabras de economía. Tocá un casillero para empezar; tocalo de nuevo para cambiar entre horizontal y vertical.`;
verdes(false);
window.__cruci = {W, H, palabras: P.puestas.map(p => p.w)};
})();
