// Monitor de Pulso Macro (pulsomacro.com.ar/monitor/, también dentro de Mundo › Monitor y del botón de Geopolítica).
// Pedido del dueño 11/11/2026: "más como Bloomberg", petroleros en tiempo real y un monitor de geopolítica "muy hacker".
// Todo lo que se ve sale de datos reales (nada simulado):
//   barcos.json   Worker pulso-vivo + AISStream (petroleros por AIS; una región por minuto, rotando).
//   geovivo.json  scripts/geovivo.py: GDELT (reportes de prensa de combates), NASA FIRMS (focos de calor), FMI PortWatch.
//   geopolitica.json (guerras, muertes, riesgo geopolítico) y global.json (petróleo, gas, oro, trigo, Tesoro).
// Los reportes AIS que llegan cada minuto se van mostrando a lo largo del minuto siguiente, con su hora real.
// Si no hay datos de algo, el panel lo dice; no se rellena.
"use strict";
(() => {
const $ = id => document.getElementById(id);
const CLARO = document.documentElement.dataset.tema === 'claro';
const fmt = (v, d = 0) => v == null || !isFinite(v) ? '—' : v.toLocaleString('es-AR', {minimumFractionDigits: d, maximumFractionDigits: d});
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const VER = () => Math.floor(Date.now() / 60000);
const FONT = getComputedStyle(document.body).fontFamily;
const EMBEBIDO = window.parent !== window;
const K = CLARO ? {
  sph: '#f6e6c2', sphL: '#c9a25a', grat: 'rgba(154,91,0,.10)', land: '#e3c58e', landL: '#b98c48', lane: 'rgba(154,91,0,.32)',
  ship: 'rgba(154,91,0,.9)', shipB: '#5e3500', ping: '14,116,128', pingS: '#0e7480', lab: 'rgba(251,241,220,.92)', am: '#9a5b00', rj: '#b0352a',
  warM: 'rgba(176,53,42,.45)', warm: 'rgba(200,110,40,.32)', warA: 'rgba(176,53,42,.12)', zSea: '#f6e6c2', zLand: '#e0bf85', zCoast: '#b98c48',
  zGrid: 'rgba(14,116,128,.10)', zTxt: 'rgba(122,92,51,.95)', quieto: '#7a5c33',
  gLand: '#ead2ad', gLandL: '#c9a07a', gGrat: 'rgba(176,53,42,.10)', gTxt: 'rgba(176,53,42,.55)', gShip: 'rgba(154,91,0,.5)', gLane: 'rgba(154,91,0,.18)',
  fire: [176, 70, 20], ev: '#2a1c0c'
} : {
  sph: '#050d16', sphL: '#1d2c3a', grat: 'rgba(60,196,207,.07)', land: '#0d1822', landL: '#21374a', lane: 'rgba(255,160,40,.2)',
  ship: 'rgba(255,160,40,.85)', shipB: '#ffc266', ping: '60,196,207', pingS: '#3cc4cf', lab: 'rgba(3,6,10,.82)', am: '#ffa028', rj: '#ff4d42',
  warM: 'rgba(255,77,66,.42)', warm: 'rgba(255,138,61,.28)', warA: 'rgba(255,77,66,.10)', zSea: '#04101a', zLand: '#132230', zCoast: '#2a465c',
  zGrid: 'rgba(60,196,207,.08)', zTxt: 'rgba(127,139,151,.9)', quieto: '#a8742a',
  gLand: '#120b0c', gLandL: '#33201f', gGrat: 'rgba(255,77,66,.07)', gTxt: 'rgba(255,120,110,.45)', gShip: 'rgba(255,160,40,.5)', gLane: 'rgba(255,160,40,.12)',
  fire: [255, 110, 40], ev: '#ffffff'
};
const COL_NIV = CLARO ? {mayor: '#b0352a', menor: '#c8662a', conflicto: '#a8801e', choque: '#8a7a60'} : {mayor: '#ff4d42', menor: '#ff8a3d', conflicto: '#e0b23a', choque: '#8a7f6a'};
const RANK = {mayor: 4, menor: 3, conflicto: 2, choque: 1};

async function bajar(u){ const r = await fetch(u); if(!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }
function fitCv(cv){ const r = cv.getBoundingClientRect(), dpr = Math.min(1.25, devicePixelRatio || 1);
  cv.width = Math.max(2, Math.round(r.width * dpr)); cv.height = Math.max(2, Math.round(r.height * dpr));
  const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0); return {c, w: r.width, h: r.height}; }
const hace = ms => { const m = Math.max(0, Math.round(ms / 60000)); return m < 60 ? m + ' min' : Math.floor(m / 60) + ' h ' + String(m % 60).padStart(2, '0'); };
const ddmm = d => { const x = new Date(d); return String(x.getDate()).padStart(2, '0') + '/' + String(x.getMonth() + 1).padStart(2, '0'); };
const hhmmUTC = t => new Date(t).toISOString().substr(11, 8);
const MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

// ---------------------------------------------------------------- geografía fija
// Rutas habituales de los petroleros (aproximadas, solo de referencia en el globo).
const RUTAS = [
  [[50.5, 27.5], [53, 26.6], [56.3, 26.5], [57.5, 25], [60, 23], [62, 19], [55, 14], [49, 12.5], [43.4, 12.6], [42, 15], [38.5, 20], [34, 27.5], [32.55, 29.9], [32.35, 31.3], [30, 33], [20, 35], [11, 37.3], [0, 36.5], [-5.6, 35.95], [-9.5, 38], [-9.5, 43], [-5, 48.5], [1.5, 50.5], [4, 51.95]],
  [[57.5, 25], [62, 22], [68, 18], [74, 10], [80, 5.7], [88, 6], [95, 6], [98.5, 4.5], [101, 2.7], [103.8, 1.2], [105, 3], [108, 8], [111, 14], [114, 20], [118, 24], [121, 29], [125, 31], [130, 32.5], [135, 34]],
  [[57.5, 25], [60, 20], [58, 10], [52, 0], [45, -12], [40, -22], [33, -32], [20, -35.5], [15, -30], [5, -15], [-5, 0], [-20, 10], [-40, 20], [-70, 25], [-90, 27]],
  [[-94, 29], [-88, 26], [-82, 24.5], [-79.5, 26], [-70, 32], [-50, 40], [-30, 44], [-10, 47], [-5, 48.5], [1.5, 50.5], [4, 51.95]],
  [[-43, -23.5], [-35, -25], [-10, -33], [18, -36], [40, -30], [60, -15], [80, -2], [95, 5], [98.5, 4.5]],
  [[37.8, 44.7], [33, 43], [29.1, 41.2], [26.5, 40.2], [25, 37], [20, 35]],
  [[-79.9, 9.4], [-77, 12], [-75, 17], [-74, 20], [-73, 22], [-75, 25], [-79.5, 26]],
  [[-79.5, 8.9], [-80, 6], [-85, 3], [-90, -5], [-80, -12]],
  [[5, 4], [0, 3], [-10, 6], [-18, 15], [-17, 25], [-10, 35], [-5.6, 35.95]],
  [[28.7, 60.3], [22, 59.5], [18, 57], [14, 55.3], [11, 57.5], [8, 58], [4, 57], [2, 53]]
];
const PASOS = {ormuz: {n: 'Estrecho de Ormuz', c: [56.4, 26.5], box: [[54.6, 24.6], [58.6, 27.6]]},
  bab: {n: 'Bab el-Mandeb', c: [43.4, 12.6], box: [[41.6, 11.2], [45.4, 14.4]]},
  suez: {n: 'Canal de Suez', c: [32.55, 30.2], box: [[31.4, 28.6], [33.8, 31.6]]},
  malaca: {n: 'Estrecho de Malaca', c: [101, 2.6], box: [[98.8, 0.6], [104.6, 4.8]]},
  panama: {n: 'Canal de Panamá', c: [-79.7, 9.1]}, bosforo: {n: 'Bósforo', c: [29.05, 41.1], box: [[27.6, 39.9], [30.4, 42.0]]},
  cabo: {n: 'Cabo de Buena Esperanza', c: [18.5, -34.6]}, gib: {n: 'Gibraltar', c: [-5.6, 35.95], box: [[-7.6, 34.6], [-3.4, 37.4]]}};
// Zooms que no son pasos del FMI (no tienen recuadro en el globo): donde AISStream sí tiene antenas.
const ZEXTRA = {mancha: {n: 'Canal de la Mancha y Róterdam', box: [[-6, 48.6], [5.5, 53.4]]}, houston: {n: 'Golfo de México · Houston', box: [[-96.2, 27.3], [-92.8, 30.1]]}};
const ZBOX = Object.assign({}, PASOS, ZEXTRA);
// Se muestran solo los que tienen ≥2 petroleros: AISStream casi no tiene antenas en Ormuz, Bab el-Mandeb ni Malaca (medido 11/11/2026).
const ZOOMS = ['ormuz', 'bab', 'malaca', 'suez', 'gib', 'bosforo', 'mancha', 'houston'];
const ZONA = [[56, 59, 22, 28, 'Golfo de Omán'], [47, 56, 24, 30.5, 'Golfo Pérsico'], [41, 46, 11, 16, 'Bab el-Mandeb'], [32, 44, 15, 30, 'Mar Rojo'],
  [32, 33, 29.8, 31.6, 'Canal de Suez'], [44, 60, 8, 22, 'Mar Arábigo'], [95, 105, 0, 7, 'Estrecho de Malaca'], [103.5, 104.6, 1, 1.6, 'Singapur'],
  [105, 123, 5, 30, 'Mar de China Meridional'], [118, 142, 28, 40, 'Mar de China Oriental y Japón'], [-6, 36, 30, 46, 'Mediterráneo'],
  [27, 42, 40, 47.5, 'Mar Negro'], [-98, -80, 18, 31, 'Golfo de México'], [-85, -60, 7, 20, 'Caribe'], [10, 30, 53, 61, 'Báltico'],
  [-12, 10, 43, 61, 'Mar del Norte y Canal'], [55, 80, 5, 25, 'Mar Arábigo'], [-50, -35, -38, -18, 'Costa de Brasil'], [10, 35, -38, -25, 'Sudáfrica']];
const zona = (la, lo) => { const z = ZONA.find(z => lo >= z[0] && lo <= z[1] && la >= z[2] && la <= z[3]); return z ? z[4] : 'mar abierto'; };
const ZGUERRA = [['Golfo Pérsico y Ormuz', [47, 22, 60, 30.5]], ['Mar Rojo y Bab el-Mandeb', [32, 11, 46, 30]], ['Golfo de Adén', [43, 10, 52, 15]], ['Mar Negro', [26, 40, 42, 47.5]]];
const CLK = [['Nueva York', 'America/New_York', [9.5, 16]], ['Londres', 'Europe/London', [8, 16.5]], ['Fráncfort', 'Europe/Berlin', [9, 17.5]], ['Dubái', 'Asia/Dubai', [10, 15]],
  ['Riad', 'Asia/Riyadh', [10, 15]], ['Bombay', 'Asia/Kolkata', [9.25, 15.5]], ['Singapur', 'Asia/Singapore', [9, 17]], ['Shanghái', 'Asia/Shanghai', [9.5, 15]],
  ['Tokio', 'Asia/Tokyo', [9, 15.5]], ['Buenos Aires', 'America/Argentina/Buenos_Aires', [11, 17]]];
// País de la guerra -> zona de focos de calor de geovivo.py
const ZFOCO = {UKR: 'ucr', RUS: 'ucr', SDN: 'sdn', MMR: 'mmr', ISR: 'gaz', PSE: 'gaz', LBN: 'gaz'};
const CENTRO = {DZA: [-1.5, 14], ISR: [35, 31.8], RUS: [37.5, 48.5], UKR: [36.5, 48.6], MEX: [-104, 24]};

// ---------------------------------------------------------------- estado
let land, ISO = {}, nivDe = {}, GUERRAS = [], GPR = [], COST = null, GL = null, GV = null, BAR = null;
const SHIPS = new Map();             // mmsi -> {la, lo, sog, cog, t, len, name, ping}
let lastRepT = 0, enCola = new Set(), repLog = [];
let vista = 1, focoZ = 0, focoZT = 0, foco2 = 0, foco2T = 0, evI = 0, evT = 0, evHi = null;

function armarGuerras(geo){
  GUERRAS = (geo.conflictos && geo.conflictos.lista || []).map(c => {
    const m = c.muertes || {}, n = s => s ? +String(s).split(/[–-]/)[0].replace(/\D/g, '') || 0 : 0;
    const f = s => s ? String(s).replace(/,/g, '.') : '—';
    return {es: c.es || c.n, nivel: c.nivel, iso: c.iso || [], ini: c.ini, m26: f(m['2026']), m25: f(m['2025']), n26: n(m['2026'])};
  });
  nivDe = {};
  for(const g of GUERRAS) g.iso.forEach((c, i) => {
    const p = nivDe[c], main = i === 0;
    if(!p || (main && (!p.main || RANK[g.nivel] > RANK[p.n])) || (!p.main && !main && RANK[g.nivel] > RANK[p.n])) nivDe[c] = {n: g.nivel, main: main || (p && p.main) || false};
  });
  GPR = (geo.gpr && geo.gpr.diario || []).map(d => [d[0], d[1]]);
}

// ---------------------------------------------------------------- barcos
function clase(len){ return len >= 300 ? 'VLCC' : len >= 250 ? 'SUEZMAX' : len >= 200 ? 'AFRAMAX' : 'PETROLERO'; }
function aplicarBarcos(B, primera){
  BAR = B;
  const vivos = new Set();
  const reps = (B.rep || []).filter(r => r[0] > lastRepT);
  const nuevos = primera ? [] : reps;
  const cola = new Set(nuevos.map(r => r[1]));
  for(const b of B.b || []){
    vivos.add(b[0]);
    const s = SHIPS.get(b[0]);
    if(s && cola.has(b[0])){ s.len = b[6]; s.name = b[8]; continue; }   // se mueve cuando le toca su reporte
    SHIPS.set(b[0], Object.assign(s || {ping: -1e9}, {la: b[1], lo: b[2], sog: b[3], cog: b[4], t: b[5], len: b[6], name: b[8]}));
  }
  for(const m of [...SHIPS.keys()]) if(!vivos.has(m) && !cola.has(m)) SHIPS.delete(m);
  if(primera){ for(const r of reps.slice(-45)) lineaAis(r, false); }
  else if(nuevos.length){
    const t0 = nuevos[0][0], span = Math.max(1, nuevos[nuevos.length - 1][0] - t0);
    nuevos.forEach(r => { enCola.add(r[1]); setTimeout(() => reporte(r), nuevos.length > 1 ? (r[0] - t0) / span * 55000 : 0); });
  }
  if(reps.length) lastRepT = Math.max(lastRepT, ...reps.map(r => r[0]));
  panelBarcos();
}
function reporte(r){
  enCola.delete(r[1]);
  const s = SHIPS.get(r[1]) || {}, nm = BAR && BAR.nombre && BAR.nombre[r[1]];
  SHIPS.set(r[1], Object.assign(s, {la: r[2], lo: r[3], sog: r[4], cog: r[5], t: r[0], ping: performance.now(), len: s.len || (nm && nm[0]) || 0, name: s.name || (nm && nm[1]) || ''}));
  lineaAis(r, true);
}
function lineaAis(r, nuevo){
  const s = SHIPS.get(r[1]) || {}, nm = BAR && BAR.nombre && BAR.nombre[r[1]], len = s.len || (nm && nm[0]) || 0, name = s.name || (nm && nm[1]) || 'MMSI ' + r[1];
  repLog.push(Date.now());
  const quieto = r[4] != null && r[4] < 1;
  const ln = document.createElement('div'); ln.className = 'ln' + (nuevo ? ' nw' : '');
  ln.innerHTML = `<span class="t">${hhmmUTC(r[0])}</span><span>${esc(name)} <em>${clase(len)}${len ? ' ' + len + 'm' : ''}</em> · <b>${r[4] == null ? '—' : fmt(r[4], 1) + ' kn'}</b>${quieto ? ' <em>quieto</em>' : r[5] != null ? ' · ' + r[5] + '°' : ''} <em>· ${zona(r[2], r[3])}</em></span>`;
  const el = $('ais'); el.prepend(ln); if(nuevo) setTimeout(() => ln.classList.remove('nw'), 2500);
  while(el.children.length > 70) el.lastChild.remove();
}
function enCaja(s, w, so, e, n){ return s.lo >= w && s.lo <= e && s.la >= so && s.la <= n; }
function cuenta(box){ let n = 0; for(const s of SHIPS.values()) if(enCaja(s, box[0][0], box[0][1], box[1][0], box[1][1])) n++; return n; }
function barcosFrescos(){ return BAR && Date.now() - BAR.t < 10 * 60000; }
function panelBarcos(){
  const el = $('pet');
  if(!BAR || !SHIPS.size){
    el.innerHTML = `<div class="vacio">${BAR ? 'Todavía no hay petroleros identificados: cada barco avisa qué tipo de buque es cada unos 6 minutos y el registro se va llenando solo en las primeras horas.' : 'Todavía sin datos de barcos.'}</div>`;
  } else {
    let g = 0, m = 0, c = 0, sl = 0;
    for(const s of SHIPS.values()){ if(!s.len) sl++; else if(s.len >= 300) g++; else if(s.len >= 150) m++; else c++; }
    const d = BAR.diag || {};
    el.innerHTML = `<div class="big">${fmt(SHIPS.size)}<small>petroleros con posición</small></div>
      <div class="row"><span>Gigantes (VLCC, +300 m)</span><b>${fmt(g)}</b></div><div class="row"><span>Medianos (150-300 m)</span><b>${fmt(m)}</b></div>
      <div class="row"><span>Chicos (menos de 150 m)</span><b>${fmt(c)}</b></div>${sl ? `<div class="row"><span>Sin largo informado</span><b>${fmt(sl)}</b></div>` : ''}
      <div class="row"><span>Petroleros identificados</span><b>${fmt(BAR.petroleros)}</b></div>
      <div class="row"><span>Mensajes AIS en el último minuto</span><b>${fmt(d.msgs)}</b></div>
      <div class="row nota">Antenas en la costa (AISStream): se ve bien Europa y parte de EE.UU.; en el Golfo Pérsico, el Mar Rojo y Asia casi no hay señal, así que ahí aparecen pocos aunque haya muchos.${barcosFrescos() ? '' : ' Sin datos nuevos desde las ' + new Date(BAR.t).toLocaleTimeString('es-AR', {hour: '2-digit', minute: '2-digit'}) + '.'}</div>`;
  }
  kpis();
}

// ---------------------------------------------------------------- paneles
const ch = (a, b) => b ? (a / b - 1) * 100 : null;
function com(pref){ return GL && (GL.commodities || []).find(c => c.n.startsWith(pref)); }
function cuando(c){ if(!c) return ''; if(c.mensual || String(c.t).length === 7){ const m = +String(c.t).slice(5, 7); return 'prom. ' + MES[m - 1]; }
  const t = Date.parse(c.t); return t && Date.now() - t > 4 * 864e5 ? 'al ' + ddmm(t) : ''; }
function kpiHtml(items){ return items.map(([n, v, c, cls, nota]) => `<div${cls ? ` class="${cls}"` : ''}><small>${n}</small><b>${v}${c != null ? `<span class="${c >= 0 ? 'up' : 'dn'}">${c >= 0 ? '▲' : '▼'} ${fmt(Math.abs(c), 2)}%</span>` : ''}${nota ? `<em>${nota}</em>` : ''}</b></div>`).join(''); }
function kpis(){
  const br = com('Petróleo Brent'), wt = com('Petróleo WTI'), gs = com('Gas natural'), oro = com('Oro'), t10 = GL && GL.termo && GL.termo.us10y, g = GPR[GPR.length - 1];
  const k = c => c ? [fmt(c.v, c.v > 1000 ? 0 : 2), ch(c.v, c.prev), null, cuando(c)] : ['—', null, null, ''];
  const ship = SHIPS.size && barcosFrescos();
  $('kpi1').innerHTML = kpiHtml([['PETRÓLEO BRENT · US$', ...k(br)], ['PETRÓLEO WTI · US$', ...k(wt)], ['GAS EE.UU. · US$/MMBTU', ...k(gs)], ['ORO · US$', ...k(oro)],
    ['TESORO 10 AÑOS', t10 ? fmt(t10.v, 2) + '%' : '—'], ['RIESGO GEOPOLÍTICO', g ? fmt(g[1], 1) : '—', null, 'g', g ? 'al ' + g[0].slice(8, 10) + '/' + g[0].slice(5, 7) : ''],
    ['PETROLEROS CON POSICIÓN', ship ? fmt(SHIPS.size) : '—'], ['PETROLEROS EN ORMUZ', ship ? fmt(cuenta(PASOS.ormuz.box)) : '—']]);
  const f = GV && GV.firms, ev = GV && GV.gdelt && GV.gdelt.ev || [];
  const sem = GPR.slice(-7);
  $('kpi2').innerHTML = kpiHtml([['GUERRAS MAYORES', GUERRAS.filter(g => g.nivel === 'mayor').length], ['CONFLICTOS ACTIVOS', GUERRAS.length],
    ['RIESGO GEOPOLÍTICO', g ? fmt(g[1], 1) : '—', null, 'g', g ? 'al ' + g[0].slice(8, 10) + '/' + g[0].slice(5, 7) : ''], ['RIESGO · PROM. 7 DÍAS', sem.length ? fmt(d3.mean(sem, d => d[1]), 1) : '—'],
    ['PETRÓLEO BRENT · US$', ...k(br)], ['ORO · US$', ...k(oro)],
    ['FOCOS DE CALOR 24 H', f ? fmt(d3.sum(f.zonas, z => z[3])) : '—', null, 'g'], ['REPORTES DE PRENSA · 2 H', GV && GV.gdelt ? fmt(ev.length) : '—', null, 'g']]);
}
function panelesFijos(){
  // pasos clave (FMI PortWatch)
  const P = GV && GV.pasos && GV.pasos.p;
  $('cps').innerHTML = $('cps2').innerHTML = P && P.length ? P.map(p => { const mx = Math.max(p.v, p.p || 0) * 1.25 || 1, al = p.p && p.v < p.p * 0.8;
      return `<div class="cp${al ? ' alerta' : ''}" title="${esc(p.n)}: ${p.v} petroleros el ${ddmm(p.f + 'T12:00')} (promedio 2025: ${fmt(p.p, 1)})"><span>${esc(p.n)}</span><b>${p.v}</b><span class="bar"><i style="width:${p.v / mx * 100}%"></i>${p.p ? `<u style="left:${p.p / mx * 100}%"></u>` : ''}</span></div>`; }).join('') +
      `<div class="row nota">Raya = promedio de 2025. Dato del ${ddmm(GV.pasos.ult + 'T12:00')}: el FMI (PortWatch) lo publica con unos días de atraso.</div>`
    : '<div class="vacio">Sin datos de PortWatch todavía.</div>';
  // focos de calor
  const fx = () => { const f = GV && GV.firms; if(!f) return '<div class="vacio">Sin datos del satélite todavía.</div>';
    const z = [...f.zonas].sort((a, b) => b[3] - a[3]), mx = Math.max(1, ...z.map(x => x[3]));
    return z.map(x => `<div class="fx"><span>${esc(x[1])}</span><span class="bar"><i style="width:${x[3] / mx * 100}%"></i></span><b>${fmt(x[3])}</b></div>`).join('') +
      `<div class="row nota">Solo frentes donde el fuego suele ser combate o bombardeo; igual puede ser un incendio o una quema: el satélite no los distingue. Actualizado ${ddmm(f.t * 1000)} ${new Date(f.t * 1000).toLocaleTimeString('es-AR', {hour: '2-digit', minute: '2-digit'})}.</div>`; };
  $('fx1').innerHTML = $('fx2').innerHTML = fx();
  // mercados
  const mv = [['Brent', com('Petróleo Brent')], ['WTI', com('Petróleo WTI')], ['Gas natural EE.UU.', com('Gas natural')], ['Oro', com('Oro')], ['Trigo', com('Trigo')]].filter(x => x[1]);
  const tk = mv.map(([n, c]) => { const d = ch(c.v, c.prev); return `<div class="tick"><span>${n}${cuando(c) ? ' <em style="font-style:normal">(' + cuando(c) + ')</em>' : ''}</span><b>${fmt(c.v, c.v > 1000 ? 0 : 2)}</b><span class="${d >= 0 ? 'up' : 'dn'}">${d == null ? '' : (d >= 0 ? '▲' : '▼') + ' ' + fmt(Math.abs(d), 2) + '%'}</span></div>`; }).join('');
  $('mv1').innerHTML = $('mv2').innerHTML = (tk || '<div class="vacio">Sin datos.</div>') + '<div class="row nota">Petróleo y gas: EIA (diario). Oro y trigo: Banco Mundial (promedio del mes).</div>';
  // guerras
  const nv = {mayor: 0, menor: 0, conflicto: 0, choque: 0}; GUERRAS.forEach(g => nv[g.nivel] = (nv[g.nivel] || 0) + 1);
  $('niv').innerHTML = [['mayor', 'MAYORES'], ['menor', 'MENORES'], ['conflicto', 'CONFLICTOS'], ['choque', 'CHOQUES']].map(([k, t]) => `<span><b style="color:${COL_NIV[k]}">${nv[k]}</b>${t}</span>`).join('');
  const W = [...GUERRAS].filter(g => g.nivel !== 'choque').sort((a, b) => RANK[b.nivel] - RANK[a.nivel] || b.n26 - a.n26);
  $('wars').innerHTML = W.slice(0, 24).map(g => `<div class="war" data-i="${GUERRAS.indexOf(g)}"><i style="background:${COL_NIV[g.nivel]}"></i><span title="${esc(g.es)}">${esc(g.es)}</span><b>${g.m26}</b></div>`).join('') +
    '<div class="row nota">Fuente: Wikipedia, lista de conflictos armados en curso (CC BY-SA 4.0), con datos de UCDP, ACLED y otros.</div>';
  // riesgo geopolítico
  if(GPR.length){ const S = GPR.slice(-120), Wd = 280, H = 50, x = d3.scaleLinear([0, S.length - 1], [0, Wd]), y = d3.scaleLinear([0, d3.max(S, d => d[1]) * 1.05], [H, 2]), u = S[S.length - 1];
    $('gpr').innerHTML = `<div class="big" style="color:var(--rj)">${fmt(u[1], 1)}<small>al ${u[0].split('-').reverse().join('/')}</small></div><svg class="spk" viewBox="0 0 ${Wd} ${H}" preserveAspectRatio="none"><line x1="0" x2="${Wd}" y1="${y(100)}" y2="${y(100)}" stroke="currentColor" opacity=".3" stroke-dasharray="3 3"/><path d="${d3.line((d, i) => x(i), d => y(d[1]))(S)}" fill="none" stroke="var(--rj)" stroke-width="1.3"/></svg><div class="row nota">Últimos 4 meses. Caldara e Iacoviello (Reserva Federal): cuántas noticias de guerras, amenazas y atentados publican los grandes diarios.</div>`; }
  else $('gpr').innerHTML = '<div class="vacio">Sin datos.</div>';
  kpis(); feeds(true);
}
let evVistos = new Set();
function feeds(todo){
  const ev = GV && GV.gdelt && GV.gdelt.ev || [], ahora = Date.now();
  for(const id of ['gd1', 'gd2']){
    const el = $(id);
    if(!ev.length){ el.innerHTML = `<div class="vacio" style="padding:6px 8px">${GV && GV.gdelt ? 'Sin reportes de combates en las últimas 2 horas.' : 'Sin datos de GDELT todavía.'}</div>`; continue; }
    el.innerHTML = ev.slice(0, 60).map(e => { const nuevo = !todo && !evVistos.has(e.join('|'));
      return `<div class="ln${nuevo ? ' nw' : ''}"><span class="t">${hace(ahora - e[0] * 1000)}</span><span class="k">${esc(e[1].toUpperCase())}</span><span>${esc(e[4])}, ${esc(e[6])} <em>· ${esc(e[7])}${e[8] > 1 ? ' · ' + e[8] + ' notas' : ''}</em></span></div>`; }).join('');
  }
  ev.forEach(e => evVistos.add(e.join('|')));
}
function relojes(){
  const now = new Date();
  $('clk').innerHTML = CLK.map(([n, z, [a, b]]) => { const s = now.toLocaleTimeString('es-AR', {timeZone: z, hour: '2-digit', minute: '2-digit', hour12: false});
    const [hh, mm] = s.split(':').map(Number), dow = new Date(now.toLocaleString('en-US', {timeZone: z})).getDay(), ab = dow > 0 && dow < 6 && hh + mm / 60 >= a && hh + mm / 60 < b;
    return `<div><span class="${ab ? 'on' : ''}">${ab ? '●' : '○'}</span> ${n.toUpperCase()}<b>${s}</b></div>`; }).join('');
  const u = now.toISOString(); $('utc1').textContent = $('utc2').textContent = u.substr(0, 10) + '  ' + u.substr(11, 8) + ' UTC';
  const n10 = repLog.filter(t => Date.now() - t < 600000).length; repLog = repLog.filter(t => Date.now() - t < 600000);
  $('rps').textContent = BAR ? fmt(n10) + ' EN 10 MIN · HORA UTC' : 'HORA UTC';
}

// ---------------------------------------------------------------- dibujo: globo
let G1, Z1, proj1, path1, rot = [-40, -18, 0];
function init1(){ G1 = fitCv($('cv1')); Z1 = fitCv($('cvZ')); const R = Math.min(G1.w * 0.42, G1.h * 0.47);
  proj1 = d3.geoOrthographic().scale(R).translate([G1.w * 0.42, G1.h * 0.53]).clipAngle(90).precision(.5); path1 = d3.geoPath(proj1, G1.c); }
function zoomsConBarcos(){ return ZOOMS.filter(k => cuenta(ZBOX[k].box) >= 2); }
function draw1(now){
  const {c, w, h} = G1; c.clearRect(0, 0, w, h);
  const zs = zoomsConBarcos(); $('zoom').hidden = !zs.length;
  if(zs.length && Z1.w < 50) Z1 = fitCv($('cvZ'));   // estaba oculto al medir
  if(zs.length && now - focoZT > 16000){ focoZT = now; focoZ = (focoZ + 1) % zs.length; }
  const kz = zs.length ? zs[focoZ % zs.length] : 'ormuz', P = ZBOX[kz], cz = P.c || [(P.box[0][0] + P.box[1][0]) / 2, (P.box[0][1] + P.box[1][1]) / 2];
  const tgt = [-cz[0] + 28, -cz[1] * 0.6];
  rot[0] += (tgt[0] - rot[0]) * 0.012; rot[1] += (tgt[1] - rot[1]) * 0.012; proj1.rotate(rot);
  c.beginPath(); path1({type: 'Sphere'}); c.fillStyle = K.sph; c.fill(); c.strokeStyle = K.sphL; c.lineWidth = 1; c.stroke();
  c.beginPath(); path1(d3.geoGraticule10()); c.strokeStyle = K.grat; c.stroke();
  c.beginPath(); path1(land); c.fillStyle = K.land; c.fill(); c.strokeStyle = K.landL; c.lineWidth = .6; c.stroke();
  for(const iso in nivDe){ const f = ISO[iso]; if(!f) continue; const d = nivDe[iso]; c.beginPath(); path1(f); c.fillStyle = d.main && d.n === 'mayor' ? K.warM : d.main ? K.warm : K.warA; c.fill(); }
  c.setLineDash([2, 4]); c.strokeStyle = K.lane; c.lineWidth = 1; RUTAS.forEach(r => { c.beginPath(); path1({type: 'LineString', coordinates: r}); c.stroke(); }); c.setLineDash([]);
  const ctr = proj1.invert(proj1.translate());
  for(const s of SHIPS.values()){
    const p = [s.lo, s.la]; if(d3.geoDistance(p, ctr) > 1.55) continue; const xy = proj1(p); if(!xy) continue;
    const age = now - s.ping;
    if(age < 1600){ const k = age / 1600; c.beginPath(); c.arc(xy[0], xy[1], 2 + k * 11, 0, 7); c.strokeStyle = `rgba(${K.ping},${1 - k})`; c.lineWidth = 1.2; c.stroke(); c.fillStyle = K.pingS; }
    else c.fillStyle = s.len >= 300 ? K.shipB : K.ship;
    const z = s.len >= 300 ? 2.6 : 2; c.fillRect(xy[0] - z / 2, xy[1] - z / 2, z, z);
  }
  c.font = '600 10.5px ' + FONT;
  const PW = GV && GV.pasos && GV.pasos.p || [];
  for(const k in PASOS){ const p = PASOS[k]; if(d3.geoDistance(p.c, ctr) > 1.45) continue; const xy = proj1(p.c), d = PW.find(x => x.k === k), al = d && d.p && d.v < d.p * .8;
    c.strokeStyle = al ? K.rj : K.am; c.lineWidth = 1; c.strokeRect(xy[0] - 7, xy[1] - 7, 14, 14);
    const tx = p.n.toUpperCase() + (d ? `  ${d.v}/día` : ''), tw = c.measureText(tx).width;
    c.fillStyle = K.lab; c.fillRect(xy[0] + 10, xy[1] - 17, tw + 10, 15); c.fillStyle = al ? K.rj : K.am; c.fillText(tx, xy[0] + 15, xy[1] - 6); }
  if(zs.length) drawZoom(now, kz);
}
function drawZoom(now, kz){
  const {c, w, h} = Z1, P = ZBOX[kz]; c.clearRect(0, 0, w, h);
  const pr = d3.geoIdentity().reflectY(true).fitExtent([[0, 18], [w, h]], {type: 'MultiPoint', coordinates: P.box}), pa = d3.geoPath(pr, c);
  c.fillStyle = K.zSea; c.fillRect(0, 18, w, h);
  c.strokeStyle = K.zGrid; c.lineWidth = 1; c.beginPath();
  for(let x = Math.ceil(P.box[0][0]); x <= P.box[1][0]; x++){ const a = pr([x, P.box[0][1] - 1]), b = pr([x, P.box[1][1] + 1]); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); }
  for(let y = Math.ceil(P.box[0][1]); y <= P.box[1][1]; y++){ const a = pr([P.box[0][0] - 1, y]), b = pr([P.box[1][0] + 1, y]); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); }
  c.stroke();
  if(COST && COST[kz]){ c.beginPath(); pa(COST[kz]); c.fillStyle = K.zLand; c.fill(); c.strokeStyle = K.zCoast; c.lineWidth = .8; c.stroke(); }
  let n = 0;
  for(const s of SHIPS.values()){
    if(!enCaja(s, P.box[0][0], P.box[0][1], P.box[1][0], P.box[1][1])) continue; n++;
    const xy = pr([s.lo, s.la]), age = now - s.ping, nuevo = age < 1600, z = s.len >= 300 ? 5 : s.len >= 150 ? 3.8 : 2.8;
    const quieto = s.sog == null || s.sog < 1 || s.cog == null;
    c.fillStyle = nuevo ? K.pingS : quieto ? K.quieto : K.am;
    if(quieto){ c.beginPath(); c.arc(xy[0], xy[1], z * .55, 0, 7); c.fill(); }
    else {
      const a = (s.cog - 90) * Math.PI / 180;
      // línea de rumbo: hacia dónde va en los próximos 30 minutos a esta velocidad (sog en nudos = millas por hora)
      const dist = s.sog * 0.5 / 60, q = pr([s.lo + Math.sin(s.cog * Math.PI / 180) * dist / Math.cos(s.la * Math.PI / 180), s.la + Math.cos(s.cog * Math.PI / 180) * dist]);
      c.strokeStyle = nuevo ? K.pingS : K.am; c.globalAlpha = .45; c.beginPath(); c.moveTo(xy[0], xy[1]); c.lineTo(q[0], q[1]); c.stroke(); c.globalAlpha = 1;
      c.save(); c.translate(xy[0], xy[1]); c.rotate(a); c.beginPath(); c.moveTo(z, 0); c.lineTo(-z * .7, z * .55); c.lineTo(-z * .7, -z * .55); c.closePath(); c.fill(); c.restore();
    }
    if(nuevo){ const k = age / 1600; c.beginPath(); c.arc(xy[0], xy[1], 4 + k * 14, 0, 7); c.strokeStyle = `rgba(${K.ping},${1 - k})`; c.lineWidth = 1; c.stroke(); }
  }
  $('zT').textContent = 'ZOOM · ' + P.n.toUpperCase(); $('zN').textContent = n + ' PETROLEROS';
  c.fillStyle = K.zTxt; c.font = '9.5px ' + FONT; c.fillText('▲ navegando (línea: adónde llega en 30 min)   ● quieto', 8, h - 7);
}

// ---------------------------------------------------------------- dibujo: geopolítica
let G2, proj2, path2;
const GUERRAS_FOCO = () => GUERRAS.filter(g => g.nivel === 'mayor');
function init2(){ G2 = fitCv($('cv2'));
  proj2 = d3.geoMercator().rotate([-15, 0]).fitExtent([[0, 0], [G2.w, G2.h]], {type: 'MultiPoint', coordinates: [[-125, -42], [155, 72]]}); path2 = d3.geoPath(proj2, G2.c); }
function centro(g){ const k = g.iso[0]; if(CENTRO[k]) return CENTRO[k]; const f = ISO[k]; return f ? d3.geoCentroid(f) : null; }
function draw2(now){
  const {c, w, h} = G2; c.clearRect(0, 0, w, h);
  c.beginPath(); path2(d3.geoGraticule().step([15, 15])()); c.strokeStyle = K.gGrat; c.lineWidth = 1; c.stroke();
  c.beginPath(); path2(land); c.fillStyle = K.gLand; c.fill(); c.strokeStyle = K.gLandL; c.lineWidth = .6; c.stroke();
  for(const iso in nivDe){ const f = ISO[iso]; if(!f) continue; const d = nivDe[iso]; c.beginPath(); path2(f);
    c.globalAlpha = d.main ? (d.n === 'mayor' ? .55 : d.n === 'menor' ? .45 : .32) : .13; c.fillStyle = d.main ? COL_NIV[d.n] : COL_NIV.mayor; c.fill(); }
  c.globalAlpha = 1;
  c.fillStyle = K.gTxt; c.font = '9px ' + FONT;
  for(let lo = -120; lo <= 150; lo += 30){ const p = proj2([lo, 71]); c.fillText(lo < 0 ? -lo + 'O' : lo + 'E', p[0] + 2, p[1] + 10); }
  for(let la = -30; la <= 60; la += 15){ const p = proj2([-124, la]); c.fillText(la < 0 ? -la + 'S' : la + 'N', p[0] + 2, p[1] - 2); }
  c.setLineDash([2, 4]); c.strokeStyle = K.gLane; RUTAS.forEach(r => { c.beginPath(); path2({type: 'LineString', coordinates: r}); c.stroke(); }); c.setLineDash([]);
  c.fillStyle = K.gShip; for(const s of SHIPS.values()){ const xy = proj2([s.lo, s.la]); c.fillRect(xy[0] - .7, xy[1] - .7, 1.4, 1.4); }
  // focos de calor de las últimas 24 h: más fuertes los más recientes
  const F = GV && GV.firms && GV.firms.p || [], ahora = Date.now(), [fr, fg, fb] = K.fire;
  for(const p of F){ const t = Date.parse(p[3].replace(' ', 'T') + ':00Z'), age = isFinite(t) ? (ahora - t) / 36e5 : 24, a = Math.max(.25, 1 - age / 26);
    const xy = proj2([p[1], p[0]]); c.fillStyle = `rgba(${fr},${fg},${fb},${a})`; const s = age < 6 ? 2.2 : 1.4; c.fillRect(xy[0] - s / 2, xy[1] - s / 2, s, s); }
  // reportes de prensa (últimas 2 h): todos como punto; uno por vez se destaca con su antigüedad
  const ev = GV && GV.gdelt && GV.gdelt.ev || [];
  c.fillStyle = K.ev; for(const e of ev){ const xy = proj2([e[3], e[2]]); c.fillRect(xy[0] - 1.5, xy[1] - 1.5, 3, 3); }
  if(ev.length){ if(!evHi || now - evT > 2600){ evT = now; evI = (evI + 1) % Math.min(ev.length, 40); evHi = ev[evI]; }
    const e = evHi, xy = proj2([e[3], e[2]]), age = now - evT;
    c.strokeStyle = K.rj; c.lineWidth = 1.2; for(let r = 0; r < 2; r++){ const rr = ((age / 900 + r * .5) % 1) * 16 + 3; c.globalAlpha = 1 - ((age / 900 + r * .5) % 1); c.beginPath(); c.arc(xy[0], xy[1], rr, 0, 7); c.stroke(); }
    c.globalAlpha = 1; c.font = '600 9.5px ' + FONT; const tx = `${e[1].toUpperCase()} · ${e[4]} · hace ${hace(Date.now() - e[0] * 1000)}`, tw = c.measureText(tx).width;
    const lx = Math.min(w - tw - 14, xy[0] + 10); c.fillStyle = K.lab; c.fillRect(lx - 3, xy[1] - 18, tw + 8, 14); c.fillStyle = K.rj; c.fillText(tx, lx + 1, xy[1] - 7); }
  // mira sobre la guerra en foco
  const GF = GUERRAS_FOCO(); if(!GF.length) return;
  const g = GF[foco2 % GF.length], cc = centro(g); if(!cc) return;
  const xy = proj2(cc), r = 26;
  c.strokeStyle = K.rj; c.lineWidth = 1; c.strokeRect(xy[0] - r, xy[1] - r, r * 2, r * 2);
  c.globalAlpha = .22; c.beginPath(); c.moveTo(0, xy[1]); c.lineTo(xy[0] - r, xy[1]); c.moveTo(xy[0] + r, xy[1]); c.lineTo(w, xy[1]); c.moveTo(xy[0], 0); c.lineTo(xy[0], xy[1] - r); c.moveTo(xy[0], xy[1] + r); c.lineTo(xy[0], h); c.stroke(); c.globalAlpha = 1;
  const cl = $('call'), cw = cl.offsetWidth || 270, chh = cl.offsetHeight || 110;
  cl.style.left = (xy[0] + r + 12 + cw > w ? xy[0] - r - 12 - cw : xy[0] + r + 12) + 'px'; cl.style.top = Math.max(8, Math.min(h - chh - 8, xy[1] - r)) + 'px';
}
function callout(){
  const GF = GUERRAS_FOCO(); if(!GF.length){ $('call').style.display = 'none'; return; }
  const g = GF[foco2 % GF.length], zk = ZFOCO[g.iso[0]], f = GV && GV.firms, zf = f && zk ? f.zonas.find(z => z[0] === zk) : null;
  const ev = (GV && GV.gdelt && GV.gdelt.ev || []).filter(e => g.iso.includes(e[5])).length;
  $('call').innerHTML = `<div class="n">${esc(g.es.toUpperCase())}</div><div class="r"><span>Muertes en 2026</span><b>${g.m26}</b></div><div class="r"><span>Muertes en 2025</span><b>${g.m25}</b></div><div class="r"><span>Desde</span><b>${g.ini || '—'}</b></div>${zf ? `<div class="r"><span>Focos de calor 24 h (${esc(zf[1])})</span><b>${fmt(zf[3])}</b></div>` : ''}${GV && GV.gdelt ? `<div class="r"><span>Reportes de prensa, últimas 2 h</span><b>${fmt(ev)}</b></div>` : ''}`;
  document.querySelectorAll('#wars .war').forEach(el => el.classList.toggle('foc', GUERRAS[+el.dataset.i] === g));
}

// ---------------------------------------------------------------- vistas y arranque
// Desde el 11/11/2026 esta página es solo "Geopolítica en vivo" (el Monitor completo volvió a index.html, Mundo › Monitor).
const ABRIO_GEO = true;
function ver(v){ vista = v; $('v2').classList.toggle('on', v === 2); if(v === 2){ init2(); callout(); } else init1(); }
function salirGeo(){ if(EMBEBIDO){ parent.postMessage({pm: 'monitor-cerrar'}, location.origin); return; } location.href = '/#global'; }
$('aGeo').onclick = () => ver(2); $('cGeo').onclick = salirGeo;
async function pantalla(){ try{ if(document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }catch(e){}
  try{ if(!window.__wl) window.__wl = await navigator.wakeLock.request('screen'); }catch(e){} }
$('fs1').onclick = pantalla; $('fs2').onclick = pantalla;
addEventListener('keydown', e => { if(e.key === 'Escape' && vista === 2 && !document.fullscreenElement) salirGeo(); });
addEventListener('resize', () => { init1(); if(vista === 2) init2(); });

async function cargarGeo(){ try{ GV = await bajar('/geovivo.json?t=' + VER()); }catch(e){} }
async function cargarGlobal(){ try{ GL = await bajar('/global.json?t=' + VER()); }catch(e){} }

async function arrancar(){
  const [w, cst, geo] = await Promise.all([bajar('/world.json'), bajar('/monitor/costas.json').catch(() => null), bajar('/geopolitica.json?t=' + VER()).catch(() => ({}))]);
  land = topojson.feature(w, w.objects.land); topojson.feature(w, w.objects.countries).features.forEach(f => { ISO[f.id] = f; });
  COST = cst; armarGuerras(geo);
  await Promise.all([cargarGeo(), cargarGlobal()]);
  panelesFijos(); relojes(); setInterval(relojes, 1000);
  // Barcos por AIS sacados el 12/11/2026 (pedido del dueño): no se piden más.
  ver(ABRIO_GEO ? 2 : 1);
  setInterval(async () => { if(document.hidden) return; await cargarGeo(); panelesFijos(); if(vista === 2) callout(); }, 5 * 60000);
  setInterval(async () => { if(document.hidden) return; await cargarGlobal(); panelesFijos(); }, 10 * 60000);
  setInterval(() => { if(!document.hidden) feeds(false); }, 60000);
  let ult = 0;
  const loop = now => {
    requestAnimationFrame(loop);
    if(document.hidden || now - ult < 33) return; ult = now;
    if(vista === 2 && now - foco2T > 9000){ foco2T = now; foco2++; callout(); }
    if(vista === 1) draw1(now); else draw2(now);
  };
  requestAnimationFrame(loop);
}
arrancar();
})();
