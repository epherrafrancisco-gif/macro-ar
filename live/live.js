// Pulso Live: reels armados con los datos reales de Pulso Macro (live/datos.json, robot scripts/live.py).
(function(){
'use strict';
const VER = () => Math.floor(Date.now() / 60000);
fetch('datos.json?t=' + VER()).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(arrancar).catch(() => {
  const e = document.getElementById('estado'); if (e) e.innerHTML = 'No se pudieron cargar las preguntas. <a href="">Probá de nuevo</a> o <a href="/">volvé a Pulso Macro</a>.';
});
function arrancar(P) {
// ---------- utilidades ----------
const $ = s => document.querySelector(s);
const fN = (v, d = 0) => Number(v).toLocaleString('es-AR', {minimumFractionDigits: d, maximumFractionDigits: d});
const fP = (v, d = 1) => (v > 0 ? '+' : v < 0 ? '−' : '') + fN(Math.abs(v), d) + '%';
const fA = v => Math.abs(v) >= 100 ? fN(v, 0) : Math.abs(v) >= 10 ? fN(v, 1) : fN(v, 2);
const MES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const fMes = m => MES[+m.slice(5, 7) - 1] + ' ' + m.slice(0, 4);
const fFe = f => f.slice(8, 10) + '/' + f.slice(5, 7) + '/' + f.slice(0, 4);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const hash = s => { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };
const elegir = (id, arr) => arr[hash(id) % arr.length];           // misma frase para el mismo reel
let semilla = (Date.now() ^ (Math.random() * 1e9)) >>> 0;          // orden distinto en cada visita
const rnd = () => { semilla = (semilla + 0x6D2B79F5) >>> 0; let t = semilla; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
const flag = fl => fl ? `<img src="/vendor/flags/${fl}.svg" alt="">` : '';
const sube = (v, s = 'subió', b = 'bajó') => v >= 0 ? s : b;
const HOY = P.hoy;
const SITIO = '/';
const ISO = {}; for (const k in P.paises) ISO[P.paises[k].iso] = P.paises[k];
ISO.ARG = {n: 'Argentina', fl: 'ar', k: 'argentina'};
const NOM = {DEU:'Alemania',FRA:'Francia',ITA:'Italia',NLD:'Países Bajos',AUT:'Austria',BEL:'Bélgica',PRT:'Portugal',IRL:'Irlanda',GRC:'Grecia',FIN:'Finlandia',EA20:'Zona euro'};
const pais = iso => ISO[iso] || {n: NOM[iso] || iso, fl: null};
const CC = {acc: '#2ee59d', inf: '#ff5c8a', dol: '#5fb4ff', bm: '#ffc23d', tas: '#b57bff', vf: '#ff5c8a', sim: '#2ee59d', tri: '#b57bff', arg: '#5fb4ff', mer: '#ff8a3d', mun: '#2ad4c8', his: '#ffc23d'};
// cada reel con su color (pedido del dueño: que cambien, que no parezca un tablero): pares de colores vivos, nunca dos iguales seguidos
const PAL = [['#7b2ff7', '#f107a3'], ['#ff512f', '#f09819'], ['#00b09b', '#1d6fe0'], ['#e5266b', '#7a1fd1'], ['#f7971e', '#e8336d'],
  ['#11998e', '#38ef7d'], ['#3a1c71', '#d76d77'], ['#0061ff', '#60efff'], ['#c31432', '#240b36'], ['#8e2de2', '#4a00e0'],
  ['#fc466b', '#3f5efb'], ['#f12711', '#f5af19'], ['#00c6ff', '#0072ff'], ['#d4145a', '#fbb03b'], ['#1fa2ff', '#12d8fa']];
const CATN = {acc:'Acciones', inf:'Inflación', his:'Países', dol:'Dólar', bm:'Big Mac', tas:'Tasas'};

// ---------- series ----------
const A = P.arg;
const ult = s => s[s.length - 1];
const enFecha = (s, f) => { let r = null; for (const x of s) { if (x[0] <= f) r = x; else break; } return r; };
const restar = (f, dias) => { const d = new Date(f + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() - dias); return d.toISOString().slice(0, 10); };
const ARSD = Object.fromEntries(A.fx);
const HF = P.his.f, HM = P.his.mep;
const idxF = f => { let i = -1; for (let j = 0; j < HF.length; j++) { if (HF[j] <= f) i = j; else break; } return i; };
const usd = (tk, i) => { const c = P.his.acc[tk].c[i], m = HM[i]; return c && m ? c / m : null; };
const PER = [['1m', 30, 'un mes', 'en el último mes'], ['3m', 91, 'tres meses', 'en los últimos tres meses'], ['6m', 182, 'seis meses', 'en los últimos seis meses'], ['1a', 365, 'un año', 'en el último año'], ['2a', 725, 'dos años', 'en los últimos dos años']];
const retUsd = (tk, dias) => {
  const iN = HF.length - 1, i0 = idxF(restar(HF[iN], dias)); if (i0 < 0) return null;
  const a = usd(tk, i0), b = usd(tk, iN); if (!a || !b) return null;
  const v = []; for (let i = i0; i <= iN; i++) { const x = usd(tk, i); if (x) v.push(x); }
  return {r: (b / a - 1) * 100, v, f0: HF[i0], f1: HF[iN]};
};
const NOMA = tk => P.his.acc[tk].n;

// ---------- moldes: cada uno arma reels con datos reales ----------
const R = [];   // todos los reels posibles hoy
const IDS = new Set();
const add = r => { if (r && r.id && !IDS.has(r.id)) { IDS.add(r.id); R.push(r); } };
const line = (series, a, b, opt = {}) => ({t: 'line', s: series, a, b, ...opt});

// 1. dólares del día
const DOL = [['oficial', 'oficial', 'el dólar oficial'], ['blue', 'blue', 'el blue'], ['mep', 'MEP', 'el MEP'], ['ccl', 'CCL', 'el contado con liqui'], ['mayorista', 'mayorista', 'el mayorista'], ['cripto', 'cripto', 'el dólar cripto'], ['tarjeta', 'tarjeta', 'el dólar tarjeta']];
for (const [k, n, art] of DOL) {
  const s = A[k]; if (!s || s.length < 25) continue;
  const [f, v] = ult(s), p = s[s.length - 2][1], va = (v / p - 1) * 100, m = s.slice(-31), v30 = (v / m[0][1] - 1) * 100;
  const id = 'dol-' + k + '-' + f;
  add({id, cat: 'arg', mold: 'dol', key: k, fl: 'ar', kick: 'Argentina · Dólar ' + n, score: Math.min(1, .35 + Math.abs(va) / 2),
    title: elegir(id, [`${art[0].toUpperCase() + art.slice(1)} ${sube(va)} ${fP(Math.abs(va), 2).slice(1)} en el día`, `Así se movió ${art} en el último mes`, `¿Cuánto cerró ${art}?`]),
    big: {v, pre: '$ ', d: 2}, chips: [[fP(va, 2) + ' hoy', va >= 0 ? 'up' : 'dn'], [fP(v30) + ' en 30 días', v30 >= 0 ? 'up' : 'dn']],
    viz: line([{v: m.map(x => x[1]), c: 'var(--s2)'}], 'hace 30 días', fFe(f), {area: 1}),
    src: `Cierre del ${fFe(f)}. Fuente: ${k === 'oficial' || k === 'tarjeta' ? 'Banco Nación' : k === 'mayorista' ? 'BCRA' : 'cotizaciones del mercado'}.`, go: ['dolares', 'Ver los dólares']});
}
// 2. récords (dólares, riesgo, Merval)
const REC = [['blue', 'el blue', '$ ', 2, 'arg'], ['mep', 'el MEP', '$ ', 2, 'arg'], ['ccl', 'el CCL', '$ ', 2, 'arg'], ['oficial', 'el oficial', '$ ', 2, 'arg'], ['riesgo', 'el riesgo país', '', 0, 'arg'], ['merval', 'el Merval', '', 0, 'mer']];
for (const [k, art, pre, d, cat] of REC) {
  const s = A[k]; if (!s) continue; const [f, v] = ult(s);
  for (const N of [180, 90, 60, 30]) {
    const w = s.filter(x => x[0] >= restar(f, N)); if (w.length < N * .5) continue;
    const mx = Math.max(...w.slice(0, -1).map(x => x[1])), mn = Math.min(...w.slice(0, -1).map(x => x[1]));
    const tipo = v > mx ? 'alto' : v < mn ? 'bajo' : null; if (!tipo) continue;
    const id = 'rec-' + k + '-' + f;
    add({id, cat, mold: 'rec', key: k, fl: 'ar', kick: 'Argentina · Récord', score: .95,
      title: `${art[0].toUpperCase() + art.slice(1)} quedó en su nivel más ${tipo} de los últimos ${N} días`,
      big: {v, pre, d, suf: k === 'riesgo' ? ' pb' : ''}, chips: [[(tipo === 'alto' ? 'máximo' : 'mínimo') + ' en ' + N + ' días', tipo === 'alto' ? (k === 'riesgo' ? 'dn' : 'up') : (k === 'riesgo' ? 'up' : 'dn')]],
      viz: line([{v: w.map(x => x[1]), c: 'var(--s4)'}], 'hace ' + N + ' días', fFe(f), {area: 1, mark: tipo}),
      src: `Dato del ${fFe(f)}.`, go: [k === 'merval' ? 'mercado' : k === 'riesgo' ? 'macro' : 'dolares', 'Ver en Pulso Macro']});
    break;
  }
}
// 3. brechas
{
  const ofi = ult(A.oficial)[1], f = ult(A.oficial)[0];
  const rows = DOL.filter(x => x[0] !== 'oficial' && x[0] !== 'mayorista').map(([k, n]) => ({l: n[0].toUpperCase() + n.slice(1), v: (ult(A[k])[1] / ofi - 1) * 100})).sort((a, b) => b.v - a.v);
  add({id: 'brecha-' + f, cat: 'arg', mold: 'brecha', key: 'brecha', fl: 'ar', kick: 'Argentina · Brechas', score: .75,
    title: '¿Cuánto más caro que el oficial está cada dólar?', viz: {t: 'bars', rows: rows.map(r => ({...r, txt: fP(r.v)}))},
    nota: `El oficial cerró en $ ${fN(ofi, 2)}. La brecha es cuánto más hay que pagar por cada uno de los otros.`, src: `Cotizaciones del ${fFe(f)}.`, go: ['dolares', 'Ver los dólares']});
}
// 4. riesgo país y Merval del día
for (const [k, n, pre, suf, cat, go] of [['riesgo', 'Riesgo país', '', ' pb', 'arg', 'macro'], ['merval', 'Merval', '', ' pts', 'mer', 'mercado']]) {
  const s = A[k]; const [f, v] = ult(s), p = s[s.length - 2][1], va = (v / p - 1) * 100, m = s.slice(-61);
  const id = 'dia-' + k + '-' + f;
  add({id, cat, mold: 'dia', key: k, fl: 'ar', kick: 'Argentina · ' + n, score: .5 + Math.min(.4, Math.abs(va) / 6),
    title: k === 'riesgo' ? elegir(id, [`El riesgo país ${v < p ? 'bajó' : 'subió'} a ${fN(v)} puntos`, '¿Cuánto le cuesta a Argentina pedir prestado?']) : elegir(id, [`El Merval ${sube(va)} ${fP(Math.abs(va)).slice(1)} en el día`, 'La bolsa argentina en los últimos dos meses']),
    big: {v, pre, d: 0, suf}, chips: [[fP(va) + ' en el día', (k === 'riesgo' ? -va : va) >= 0 ? 'up' : 'dn']],
    nota: k === 'riesgo' ? 'Es la tasa extra que pagan los bonos argentinos sobre los de EE.UU. Cada 100 puntos son 1 punto porcentual más.' : null,
    viz: line([{v: m.map(x => x[1]), c: k === 'riesgo' ? 'var(--s5)' : 'var(--s1)'}], 'hace 60 días', fFe(f), {area: 1}),
    src: `Cierre del ${fFe(f)}. Fuente: ${k === 'riesgo' ? 'J.P. Morgan (EMBI), vía Ámbito' : 'BYMA / MSCI'}.`, go: [go, 'Ver en Pulso Macro']});
}
// 5. "hace N años" con los dólares (mensual desde 2017) y a precios de hoy (CER)
{
  const H = A.hist, cerHoy = ult(H)[5], mesHoy = ult(H)[0];
  const COL = {1: ['oficial', 'el dólar oficial', 'oficial'], 2: ['blue', 'el blue', 'blue'], 3: ['mep', 'el MEP', 'mep'], 4: ['ccl', 'el contado con liqui', 'ccl']};
  for (const anios of [1, 2, 3, 4, 5, 6, 7, 8, 9]) {
    const mesA = (+mesHoy.slice(0, 4) - anios) + mesHoy.slice(4);
    const r = H.find(x => x[0] === mesA); if (!r) continue;
    for (const c of [1, 2, 3, 4]) {
      const [k, art] = COL[c]; if (!r[c] || !r[5]) continue;
      const hoy = ult(A[k])[1], real = r[c] * cerHoy / r[5], mult = hoy / r[c];
      const id = `hace-${k}-${anios}`;
      add({id, cat: 'his', mold: 'hace', key: k + anios, fl: 'ar', kick: `Historia · Hace ${anios === 1 ? 'un año' : anios + ' años'}`, score: .45 + rnd() * .2,
        title: elegir(id, [`En ${fMes(mesA)}, ${art} valía $ ${fA(r[c])}`, `${art[0].toUpperCase() + art.slice(1)}, hace ${anios === 1 ? 'un año' : anios + ' años'} y hoy`]),
        viz: {t: 'hace', a: {l: fMes(mesA).toUpperCase(), txt: '$ ' + fA(r[c])}, b: {l: 'HOY', txt: '$ ' + fA(hoy)}, mul: '×' + fN(mult, mult < 10 ? 1 : 0)},
        nota: `Ajustado por la inflación, aquel dólar equivale hoy a $ ${fA(real)}. ${real > hoy * 1.03 ? 'O sea: hoy el dólar está más barato que entonces, en términos reales.' : real < hoy * .97 ? 'O sea: hoy el dólar está más caro que entonces, en términos reales.' : 'O sea: en términos reales está casi igual.'}`,
        src: `Promedio mensual de ${fMes(mesA)}; inflación medida con el CER del BCRA.`, go: ['dolares', 'Ver el dólar a precios de hoy']});
    }
  }
  // poder de compra: $10.000 de cada año
  for (const y of [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]) {
    const r = H.find(x => x[0] === y + '-01'); if (!r || !r[5]) continue;
    const hoyP = 10000 * cerHoy / r[5], id = 'poder-' + y;
    add({id, cat: 'his', mold: 'poder', key: 'poder' + y, fl: 'ar', kick: 'Historia · Poder de compra', score: .5 + rnd() * .15,
      title: `Lo que comprabas con $ 10.000 en enero de ${y}, hoy cuesta…`, big: {v: hoyP, pre: '$ ', d: 0},
      chips: [['×' + fN(hoyP / 10000, hoyP < 100000 ? 1 : 0) + ' en ' + (2026 - y) + ' años', 'dn']],
      nota: `Es la inflación acumulada desde enero de ${y} hasta ${fMes(mesHoy)}, medida con el CER.`, src: 'Fuente: BCRA (CER).', go: ['calculadoras', 'Calculadora de inflación']});
  }
}
// 6. inflación argentina
{
  const I = A.infl, [m, v, yoy] = ult(I), w = I.slice(-12);
  add({id: 'infl-' + m, cat: 'arg', mold: 'infl', key: 'infl', fl: 'ar', kick: 'Argentina · Inflación', score: .8,
    title: `La inflación de ${MES[+m.slice(5) - 1]} fue ${fN(v, 1)}%`, big: {v: yoy, d: 1, suf: '%', pre: ''}, chips: [['en un año', ''], [fN(v, 1) + '% en el mes', '']],
    viz: {t: 'bars', rows: w.slice(-8).map(x => ({l: MES[+x[0].slice(5) - 1][0].toUpperCase() + MES[+x[0].slice(5) - 1].slice(1, 3) + ' ' + x[0].slice(2, 4), v: x[1], txt: fN(x[1], 1) + '%', hl: x[0] === m}))},
    src: 'Fuente: INDEC, vía BCRA.', go: ['macro', 'Ver inflación y reservas']});
}
// 7. acciones y CEDEARs del día
for (const tk in P.his.acc) {
  const c = P.his.acc[tk].c, n = c.length; if (!c[n - 1] || !c[n - 2]) continue;
  const va = (c[n - 1] / c[n - 2] - 1) * 100; if (Math.abs(va) < 1.2) continue;
  const id = 'acd-' + tk + '-' + HF[n - 1], t = P.his.acc[tk].t;
  add({id, cat: 'mer', mold: 'acd', key: tk, fl: t === 'ced' ? null : 'ar', kick: `${t === 'ced' ? 'CEDEAR' : t === 'idx' ? 'Índice' : 'Acción'} · ${tk}`, score: Math.min(1, .3 + Math.abs(va) / 8),
    title: `${NOMA(tk)} ${sube(va)} ${fP(Math.abs(va)).slice(1)} en el día`, big: {v: c[n - 1], pre: '$ ', d: 2}, chips: [[fP(va) + ' hoy', va >= 0 ? 'up' : 'dn']],
    viz: line([{v: c.slice(-60).filter(Boolean), c: va >= 0 ? 'var(--up)' : 'var(--dn)'}], 'hace 3 meses', fFe(HF[n - 1]), {area: 1}),
    src: `Precio de cierre en pesos del ${fFe(HF[n - 1])}. Fuente: BYMA.`, go: ['mercado', 'Ver Bolsa y bonos']});
}
// 8. "si hubieras puesto US$ 1.000"
for (const tk in P.his.acc) for (const [pk, dias, pn] of PER) {
  const r = retUsd(tk, dias); if (!r) continue;
  const fin = 1000 * (1 + r.r / 100), id = `si-${tk}-${pk}-${r.f1}`;
  add({id, cat: 'mer', mold: 'si', key: tk, fl: P.his.acc[tk].t === 'ced' ? null : 'ar', kick: `Simulador · ${NOMA(tk)}`, score: Math.min(1, .25 + Math.abs(r.r) / 120) + rnd() * .1,
    title: elegir(id, [`Si ponías US$ 1.000 en ${NOMA(tk)} hace ${pn}, hoy tendrías…`, `US$ 1.000 en ${NOMA(tk)} hace ${pn}: ¿cuánto serían hoy?`]),
    big: {v: fin, pre: 'US$ ', d: 0}, chips: [[fP(r.r) + ' en dólares', r.r >= 0 ? 'up' : 'dn']],
    viz: line([{v: r.v.map(x => x / r.v[0] * 1000), c: r.r >= 0 ? 'var(--up)' : 'var(--dn)'}], fFe(r.f0), fFe(r.f1), {area: 1, base: 1000}),
    nota: 'Comprando en pesos al dólar MEP de ese día y vendiendo al MEP de hoy.', src: 'Precios de BYMA y dólar MEP (AL30/AL30D).', go: ['calculadoras', 'Probalo en el simulador']});
}
// 9. rankings de acciones
for (const [pk, dias, pn, pfr] of PER.slice(0, 4)) for (const uni of ['acc', 'ced']) {
  const rows = Object.keys(P.his.acc).filter(tk => P.his.acc[tk].t === uni).map(tk => ({tk, r: retUsd(tk, dias)})).filter(x => x.r).map(x => ({l: x.tk, v: x.r.r}));
  if (rows.length < 6) continue;
  rows.sort((a, b) => b.v - a.v);
  for (const lado of ['top', 'bot']) {
    const sel = lado === 'top' ? rows.slice(0, 7) : rows.slice(-7).reverse(), id = `rk-${uni}-${pk}-${lado}-${HF[HF.length - 1]}`;
    add({id, cat: 'mer', mold: 'rank', key: 'rk' + uni, fl: uni === 'ced' ? null : 'ar', kick: `Ranking · ${uni === 'ced' ? 'CEDEARs' : 'Acciones argentinas'}`, score: .6 + rnd() * .2,
      title: `Las ${uni === 'ced' ? 'CEDEARs' : 'acciones'} que más ${lado === 'top' ? 'subieron' : 'cayeron'} ${pfr}`, viz: {t: 'bars', rows: sel.map(x => ({...x, txt: fP(x.v)}))},
      nota: 'Rendimiento en dólares MEP.', src: `Precios de BYMA al ${fFe(HF[HF.length - 1])}.`, go: ['mercado', 'Ver todas en Bolsa y bonos']});
  }
}
// 10. trivia: ¿qué rindió más?
{
  const tks = Object.keys(P.his.acc);
  for (const [pk, dias, pn, pfr] of PER.slice(1, 4)) {
    const res = {}; tks.forEach(tk => { const r = retUsd(tk, dias); if (r) res[tk] = r.r; });
    const ks = Object.keys(res);
    for (let n = 0; n < 45; n++) {
      const a = ks[Math.floor(rnd() * ks.length)], b = ks[Math.floor(rnd() * ks.length)];
      if (a === b || Math.abs(res[a] - res[b]) < 4) continue;
      const id = `tvs-${[a, b].sort().join('-')}-${pk}`, ok = res[a] > res[b] ? a : b;
      add({id, cat: 'tri', mold: 'tvs', key: a, kick: 'Trivia · ¿Qué rindió más?', score: .55 + rnd() * .3,
        title: `¿Qué rindió más en dólares ${pfr}?`, viz: {t: 'quiz', opts: [a, b].map(x => ({l: NOMA(x), fl: P.his.acc[x].t === 'ced' ? null : 'ar', ok: x === ok, txt: fP(res[x])})),
          exp: `<b>${NOMA(ok)}</b>: ${fP(res[ok])} contra ${fP(res[ok === a ? b : a])} de ${NOMA(ok === a ? b : a)}, en dólares MEP.`},
        src: 'Precios de BYMA y dólar MEP.', go: ['calculadoras', 'Probalo en el simulador']});
    }
  }
}
// 11. países: inflación contra Argentina
const AI = ult(A.infl); // [mes, mensual, interanual]
for (const k in P.paises) {
  const o = P.paises[k]; if (!o.infl) continue;
  const [m, v] = o.infl, k2 = AI[2] / v, id = `pinf-${k}-${m}`;
  add({id, cat: 'mun', mold: 'pinf', key: k, fl: o.fl, kick: `${o.n} · Inflación`, score: .45 + rnd() * .25,
    title: v > AI[2] ? `${o.n} tiene más inflación que Argentina` : k2 >= 2 ? `La inflación de Argentina es ${fN(k2, k2 < 10 ? 1 : 0)} veces la de ${o.n}` : `Inflación de un año: ${o.n} contra Argentina`,
    viz: {t: 'vs', a: {fl: o.fl, l: o.n, txt: fN(v, 1) + '%', s: 'en 12 meses, a ' + fMes(m), w: v > AI[2]}, b: {fl: 'ar', l: 'Argentina', txt: fN(AI[2], 1) + '%', s: 'en 12 meses, a ' + fMes(AI[0]), w: v <= AI[2]}},
    src: `Fuentes: BIS / bancos centrales e INDEC.`, go: [k, 'Ver ' + o.n]});
}
// 12. monedas del mundo en pesos
for (const k in P.paises) {
  const o = P.paises[k]; if (!o.fx) continue;
  const s = o.fx.filter(x => ARSD[x[0]]).map(x => [x[0], (o.inv ? ARSD[x[0]] * x[1] : ARSD[x[0]] / x[1]) * o.fac]);
  if (s.length < 80) continue;
  const [f, v] = ult(s), a = enFecha(s, restar(f, 365)) || s[0], va = (v / a[1] - 1) * 100;
  const fx0 = enFecha(o.fx, restar(f, 365)) || o.fx[0], fx1 = ult(o.fx), vsd = o.inv ? (fx1[1] / fx0[1] - 1) * 100 : (fx0[1] / fx1[1] - 1) * 100;
  const pl = /^(mil|cien) /.test(o.mon), id = `mon-${k}-${f}`, cap = o.mon[0].toUpperCase() + o.mon.slice(1);
  add({id, cat: 'mun', mold: 'mon', key: k, fl: o.fl, kick: `${o.n} · Moneda`, score: .4 + Math.min(.3, Math.abs(vsd) / 40) + rnd() * .1,
    title: elegir(id, [`¿Cuántos pesos ${pl ? 'valen' : 'vale'} ${o.mon}?`, `${cap} hoy ${pl ? 'cuestan' : 'cuesta'} $ ${fA(v)}`]), big: {v, pre: '$ ', d: v >= 100 ? 0 : 2},
    chips: [[fP(va, 0) + ' en pesos en un año', ''], [(vsd >= 0 ? 'se fortaleció ' : 'se debilitó ') + fN(Math.abs(vsd), 1) + '% contra el dólar', vsd >= 0 ? 'up' : 'dn']],
    viz: line([{v: s.slice(-260).map(x => x[1]), c: 'var(--s3)'}], 'hace un año', fFe(f), {area: 1}),
    src: `Dólar mayorista (BCRA) y cotización de ${o.n} (BCE / BIS) del ${fFe(f)}.`, go: [k, 'Ver ' + o.n]});
}
// 13. rankings del mundo (Argentina resaltada)
const REG = {todos: null, latam: ['brasil','mexico','chile','colombia','peru'], europa: ['europa','polonia','reinounido','suiza','noruega','suecia','islandia','hungria','chequia','dinamarca','rumania','serbia','espana','macedonia','turquia','rusia'], asia: ['japon','china','corea','india','indonesia','tailandia','malasia','filipinas','hongkong','singapur','australia','zelanda']};
const RGN = {todos: 'del mundo', latam: 'de Latinoamérica', europa: 'de Europa', asia: 'de Asia y Oceanía'};
for (const rg in REG) {
  const ks = (REG[rg] || Object.keys(P.paises)).filter(k => P.paises[k] && P.paises[k].infl);
  let rows = ks.map(k => ({l: P.paises[k].n, fl: P.paises[k].fl, v: P.paises[k].infl[1]}));
  if (rg !== 'europa' && rg !== 'asia') rows.push({l: 'Argentina', fl: 'ar', v: AI[2], hl: 1});
  rows.sort((a, b) => b.v - a.v); rows = rows.slice(0, 9);
  add({id: 'rinf-' + rg + '-' + AI[0], cat: 'mun', mold: 'rmun', key: 'rinf' + rg, kick: 'Ranking · Inflación', score: .65,
    title: `La inflación ${rg === 'todos' ? 'más alta ' : ''}${RGN[rg]}`, viz: {t: 'bars', rows: rows.map(r => ({...r, txt: fN(r.v, 1) + '%'}))},
    nota: 'Inflación de los últimos 12 meses, último dato de cada país.', src: 'Fuentes: BIS y bancos centrales; Argentina: INDEC.', go: ['global', 'Ver el comparador de países']});
  const kt = (REG[rg] || Object.keys(P.paises)).filter(k => P.paises[k] && P.paises[k].tasa != null);
  const rt = kt.map(k => ({l: P.paises[k].n, fl: P.paises[k].fl, v: P.paises[k].tasa})).sort((a, b) => b.v - a.v).slice(0, 9);
  add({id: 'rtas-' + rg + '-' + HOY, cat: 'mun', mold: 'rmun', key: 'rtas' + rg, kick: 'Ranking · Tasas', score: .55,
    title: `Las tasas de los bancos centrales ${RGN[rg]}`, viz: {t: 'bars', rows: rt.map(r => ({...r, txt: fN(r.v, 2) + '%'}))},
    nota: 'Es la tasa que fija cada banco central para frenar o empujar la economía.', src: 'Fuente: BIS.', go: ['global', 'Ver bancos centrales']});
}
{
  const rows = Object.values(P.paises).filter(o => o.desemp).map(o => ({l: o.n, fl: o.fl, v: o.desemp[1]})).sort((a, b) => b.v - a.v);
  for (const lado of ['top', 'bot']) add({id: 'rdes-' + lado + '-' + HOY, cat: 'mun', mold: 'rmun', key: 'rdes', kick: 'Ranking · Desempleo', score: .5,
    title: lado === 'top' ? 'Dónde hay más desempleo' : 'Dónde hay menos desempleo', viz: {t: 'bars', rows: (lado === 'top' ? rows.slice(0, 9) : rows.slice(-9).reverse()).map(r => ({...r, txt: fN(r.v, 1) + '%'}))},
    src: 'Fuente: OCDE y bancos centrales; último dato de cada país.', go: ['global', 'Ver el comparador de países']});
}
// 14. Argentina contra cada país desde 1990 (Banco Mundial)
const PPA = P.ppa, ARP = PPA.ARG || [];
for (const iso in PPA) {
  if (iso === 'ARG' || !ISO[iso]) continue; const o = ISO[iso], s = PPA[iso];
  const yrs = s.map(x => x[0]).filter(y => ARP.find(z => z[0] === y)); if (yrs.length < 20) continue;
  const a = yrs.map(y => ARP.find(z => z[0] === y)[1]), b = yrs.map(y => s.find(z => z[0] === y)[1]);
  const y0 = yrs[0], y1 = yrs[yrs.length - 1], adel0 = b[0] > a[0], adel1 = b[b.length - 1] > a[a.length - 1];
  let cruce = null; for (let i = yrs.length - 1; i > 0; i--) if ((b[i] > a[i]) !== (b[i - 1] > a[i - 1])) { cruce = yrs[i]; break; }
  const k = b[b.length - 1] / a[a.length - 1], id = 'ppa-' + iso;
  const title = !adel0 && adel1 ? `En ${y0} Argentina era más rica que ${o.n}. Desde ${cruce}, ${o.n} quedó adelante` :
    adel0 && !adel1 ? `${o.n} era más rica que Argentina en ${y0}. Desde ${cruce}, Argentina quedó adelante` :
    adel1 ? `Por habitante, ${o.n} produce ${fN(k, 1)} veces lo que Argentina` : `Por habitante, Argentina produce ${fN(1 / k, 1)} veces lo que ${o.n}`;
  add({id, cat: 'his', mold: 'ppa', key: o.k, fl: o.fl, kick: `${o.n} y Argentina desde ${y0}`, score: (!adel0 && adel1) || (adel0 && !adel1) ? .85 : .45 + rnd() * .15,
    title, viz: line([{v: b, c: 'var(--s3)', l: o.n}, {v: a, c: 'var(--s1)', l: 'Argentina'}], String(y0), String(y1), {ley: 1}),
    nota: 'PBI por habitante a paridad de poder de compra: cuánto produce cada persona, corrigiendo por lo que cuestan las cosas en cada país.', src: 'Fuente: Banco Mundial.', go: [o.k, 'Ver ' + o.n]});
}
// 15. crecimiento: años buenos y malos
const CR = P.crec, ARC = CR.ARG || [];
for (const iso in CR) {
  if (iso === 'ARG' || !ISO[iso]) continue; const o = ISO[iso];
  const yrs = CR[iso].map(x => x[0]).filter(y => ARC.find(z => z[0] === y)).slice(-10); if (yrs.length < 10) continue;
  const fila = (s) => yrs.map(y => s.find(z => z[0] === y)[1]);
  const b = fila(CR[iso]), a = fila(ARC), nb = b.filter(x => x > 0).length, na = a.filter(x => x > 0).length;
  add({id: 'crec-' + iso, cat: 'his', mold: 'crec', key: o.k, fl: o.fl, kick: `${o.n} · Crecimiento`, score: .4 + rnd() * .2,
    title: `En los últimos 10 años, ${o.n} creció ${nb} y Argentina ${na}`, viz: {t: 'dots', yrs, rows: [{l: o.n, fl: o.fl, v: b}, {l: 'Argentina', fl: 'ar', v: a}]},
    nota: 'Verde: la economía creció ese año. Rojo: cayó.', src: 'Fuente: Banco Mundial (PBI real, variación anual).', go: [o.k, 'Ver ' + o.n]});
}
// 16. Big Mac
const BM = P.bigmac, BA = BM.ARG, BMF = P.bmf ? ', ' + MES[+P.bmf.slice(5, 7) - 1] + ' de ' + P.bmf.slice(0, 4) : '';
for (const iso in BM) {
  if (iso === 'ARG' || !ISO[iso] || !BA) continue; const o = ISO[iso], b = BM[iso], id = 'bm-' + iso;
  add({id, cat: 'mun', mold: 'bm', key: o.k, fl: o.fl, kick: `${o.n} · Índice Big Mac`, score: .4 + rnd() * .2,
    title: b.usd > BA.usd ? `Un Big Mac es más caro en ${o.n} que en Argentina` : `Un Big Mac es más barato en ${o.n} que en Argentina`,
    viz: {t: 'vs', a: {fl: o.fl, l: o.n, txt: 'US$ ' + fN(b.usd, 2), s: fN(b.local, b.local < 100 ? 2 : 0) + ' ' + b.mon, w: b.usd > BA.usd}, b: {fl: 'ar', l: 'Argentina', txt: 'US$ ' + fN(BA.usd, 2), s: '$ ' + fN(BA.local) + ' pesos', w: b.usd <= BA.usd}},
    nota: 'La misma hamburguesa en todo el mundo: si en un país sale más cara en dólares, su moneda está "cara".', src: 'Fuente: The Economist' + BMF + '.', go: [o.k, 'Ver ' + o.n]});
}
// 17. bolsas del mundo (OCDE, mensual) y bonos a 10 años
for (const k in P.bolsas) {
  const b = P.bolsas[k], o = pais(b.iso), id = `bol-${k}-${b.m}`;
  add({id, cat: 'mer', mold: 'bol', key: k, fl: o.fl, kick: `${o.n} · Bolsa`, score: .35 + Math.min(.4, Math.abs(b.va) / 60),
    title: `La bolsa de ${o.n} ${sube(b.va)} ${fN(Math.abs(b.va), 1)}% en lo que va del año`, big: {v: b.va, d: 1, suf: '%', pre: b.va > 0 ? '+' : ''},
    chips: [[fP(b.vm) + ' en ' + MES[+b.m.slice(5) - 1], b.vm >= 0 ? 'up' : 'dn'], [fP(b.v12) + ' en 12 meses', b.v12 >= 0 ? 'up' : 'dn']],
    nota: `Índice ${b.idx}, en su moneda, hasta fin de ${fMes(b.m)}.`, src: 'Fuente: OCDE (índice de precios de acciones).', go: ['global', 'Ver las bolsas del mundo']});
}
{
  const rows = Object.entries(P.bolsas).map(([k, b]) => ({l: pais(b.iso).n, fl: pais(b.iso).fl, v: b.va})).sort((a, b) => b.v - a.v);
  add({id: 'rbol-' + HOY, cat: 'mer', mold: 'rmun', key: 'rbol', kick: 'Ranking · Bolsas', score: .7, title: 'Las bolsas que más subieron en el año',
    viz: {t: 'bars', rows: rows.slice(0, 9).map(r => ({...r, txt: fP(r.v)}))}, src: 'Fuente: OCDE; en moneda de cada país.', go: ['global', 'Ver las bolsas del mundo']});
  const bn = Object.entries(P.bonos).filter(([k, b]) => !b.mens).map(([k, b]) => ({l: pais(k).n, fl: pais(k).fl, v: b.v})).sort((a, b) => b.v - a.v);
  add({id: 'rbon-' + HOY, cat: 'mun', mold: 'rmun', key: 'rbon', kick: 'Ranking · Bonos a 10 años', score: .55, title: '¿Cuánto paga cada país por pedir prestado a 10 años?',
    viz: {t: 'bars', rows: bn.slice(0, 10).map(r => ({...r, txt: fN(r.v, 2) + '%'}))}, nota: 'Tasa del bono del gobierno a 10 años, en su moneda.', src: 'Fuentes: Tesoro de EE.UU., Bundesbank, BoE y otros.', go: ['global', 'Ver bonos del mundo']});
}
// 18. commodities
const CN = {soja: 'La soja', maiz: 'El maíz', trigo: 'El trigo', wti: 'El petróleo WTI', brent: 'El petróleo Brent', gas: 'El gas natural', oro: 'El oro', plata: 'La plata', cobre: 'El cobre'};
for (const k in P.com) {
  const c = P.com[k]; if (!c.s || c.s.length < 13) continue;
  const s = c.s, [f, v] = ult(s), a = c.mens ? s[s.length - 13] : (enFecha(s, restar(f, 365)) || s[0]), va = (v / a[1] - 1) * 100;
  const w = c.mens ? s.slice(-37) : s.slice(-260), id = `com-${k}-${f}`;
  add({id, cat: 'mer', mold: 'com', key: k, kick: 'Materias primas · ' + c.n, score: .45 + Math.min(.35, Math.abs(va) / 80),
    title: `${CN[k] || c.n} está ${fN(Math.abs(va), 0)}% más ${['soja', 'plata'].includes(k) ? (va >= 0 ? 'cara' : 'barata') : (va >= 0 ? 'caro' : 'barato')} que hace un año`,
    big: {v, pre: 'US$ ', d: v < 100 ? 2 : 0}, chips: [[c.u || '', ''], [fP(va, 0) + ' en un año', va >= 0 ? 'up' : 'dn']],
    viz: line([{v: w.map(x => x[1]), c: 'var(--s4)'}], c.mens ? 'hace 3 años' : 'hace un año', c.mens ? fMes(f) : fFe(f), {area: 1}),
    nota: ['soja', 'maiz', 'trigo'].includes(k) ? 'Es lo que más exporta Argentina: cuando sube, entran más dólares.' : k === 'brent' || k === 'wti' ? 'Mueve el precio de la nafta y lo que gana Vaca Muerta.' : null,
    src: `Fuente: ${c.f}${c.mens ? ' (promedio mensual)' : ''}.`, go: ['global', 'Ver commodities']});
}
// 19. trivia de números: ¿cuál de estos países...?
{
  const conI = Object.values(P.paises).filter(o => o.infl);
  for (let n = 0; n < 40; n++) {
    const tri = []; while (tri.length < 3) { const o = conI[Math.floor(rnd() * conI.length)]; if (!tri.includes(o)) tri.push(o); }
    const vals = tri.map(o => o.infl[1]); if (Math.max(...vals) - Math.min(...vals) < 1) continue;
    const ok = tri[vals.indexOf(Math.max(...vals))], id = 'tinf-' + tri.map(o => o.k).sort().join('-');
    add({id, cat: 'tri', mold: 'tnum', key: ok.k, kick: 'Trivia · Inflación', score: .5 + rnd() * .3, title: '¿Cuál de estos países tiene más inflación?',
      viz: {t: 'quiz', opts: tri.map(o => ({l: o.n, fl: o.fl, ok: o === ok, txt: fN(o.infl[1], 1) + '%'})), exp: `<b>${ok.n}</b>, con ${fN(ok.infl[1], 1)}% en 12 meses. Argentina: ${fN(AI[2], 1)}%.`},
      src: 'Fuente: BIS y bancos centrales.', go: ['global', 'Ver el comparador de países']});
  }
  const conB = Object.keys(BM).filter(i => ISO[i] && i !== 'ARG');
  for (let n = 0; n < 30; n++) {
    const tri = []; while (tri.length < 3) { const i = conB[Math.floor(rnd() * conB.length)]; if (!tri.includes(i)) tri.push(i); }
    const vals = tri.map(i => BM[i].usd); const ok = tri[vals.indexOf(Math.max(...vals))], id = 'tbm-' + tri.slice().sort().join('-');
    add({id, cat: 'tri', mold: 'tnum', key: ISO[ok].k, kick: 'Trivia · Big Mac', score: .45 + rnd() * .3, title: '¿En qué país es más caro el Big Mac?',
      viz: {t: 'quiz', opts: tri.map(i => ({l: ISO[i].n, fl: ISO[i].fl, ok: i === ok, txt: 'US$ ' + fN(BM[i].usd, 2)})), exp: `<b>${ISO[ok].n}</b>: US$ ${fN(BM[ok].usd, 2)}. En Argentina sale US$ ${fN(BA.usd, 2)}.`},
      src: 'Fuente: The Economist' + BMF + '.', go: ['global', 'Ver el mundo']});
  }
  // ¿cuánto está…? (3 opciones alrededor del dato real)
  for (const [k, q, pre, suf, d] of [['riesgo', '¿En cuánto cerró hoy el riesgo país?', '', ' pb', 0], ['blue', '¿Cuánto cerró hoy el dólar blue?', '$ ', '', 0], ['merval', '¿En cuánto cerró el Merval?', '', ' pts', 0]]) {
    const v = ult(A[k])[1], fs = [v, v * (1.12 + rnd() * .1), v * (.8 + rnd() * .06)].map(x => Math.round(x / (k === 'merval' ? 1000 : 5)) * (k === 'merval' ? 1000 : 5));
    fs[0] = v; const ops = fs.map((x, i) => ({l: pre + fN(x, d) + suf, ok: i === 0, txt: ''})).sort(() => rnd() - .5);
    add({id: 'tq-' + k + '-' + ult(A[k])[0], cat: 'tri', mold: 'tq', key: k, fl: 'ar', kick: 'Trivia · Argentina', score: .6, title: q,
      viz: {t: 'quiz', opts: ops, exp: `Cerró en <b>${pre}${fN(v, d)}${suf}</b> el ${fFe(ult(A[k])[0])}.`}, src: 'Dato de cierre.', go: [k === 'merval' ? 'mercado' : k === 'riesgo' ? 'macro' : 'dolares', 'Ver en Pulso Macro']});
  }
}
// 20. agenda: cuenta regresiva
{
  const ahora = Date.now();
  const ev = P.cal.map(e => ({...e, t: Date.parse(e.f + 'T' + (e.h || '16:00') + ':00-03:00')})).filter(e => e.t > ahora).sort((a, b) => a.t - b.t);
  if (ev.length) {
    const e = ev[0];
    add({id: 'cd-' + e.f + e.n, cat: 'age', mold: 'cd', key: 'cal', fl: 'ar', kick: 'Agenda · ' + e.org, score: .7, title: `Falta poco para: ${e.n}`,
      viz: {t: 'count', when: e.t, list: ev.slice(1, 4).map(x => ({f: fFe(x.f).slice(0, 5), n: x.n}))}, nota: e.h ? null : 'Hora estimada.', src: 'Calendario oficial del INDEC y del BCRA.', go: ['macro', 'Ver el calendario']});
  }
}
// 21. noticias (título y link al medio)
for (const x of P.nots.slice(0, 40)) {
  const hs = Math.max(1, Math.round((Date.now() - Date.parse(x.h)) / 36e5));
  add({id: 'nw-' + hash(x.u), cat: 'not', mold: 'nw', key: x.f, kick: 'Noticias · ' + x.f, score: .3 + rnd() * .2,
    viz: {t: 'news', h: x.t, u: x.u, f: x.f, hace: hs < 48 ? `hace ${hs} h` : `hace ${Math.round(hs / 24)} días`}, src: 'Título del medio; la nota completa está en su sitio.', go: ['noticias', 'Ver todas las noticias']});
}

// 22. verdadero o falso (pedido del dueño: muchos, y al votar se ve la respuesta)
const vf = (id, key, fl, kick, claim, ok, exp, src, go, score) => add({id: 'vf-' + id, cat: 'tri', mold: 'vf', key, fl, kick: kick || 'Verdadero o falso',
  score: score == null ? .55 + rnd() * .35 : score, title: claim,
  viz: {t: 'quiz', vf: 1, opts: [{l: 'Verdadero', ok: !!ok, txt: ''}, {l: 'Falso', ok: !ok, txt: ''}], exp}, src, go});
{
  // inflación: país contra Argentina y país contra país
  const conI = Object.values(P.paises).filter(o => o.infl);
  for (const o of conI) {
    const mas = o.infl[1] > AI[2];
    vf('inf-ar-' + o.k, o.k, o.fl, 'Inflación', `${o.n} tiene más inflación que Argentina`, mas,
      `${o.n}: ${fN(o.infl[1], 1)}% en 12 meses. Argentina: ${fN(AI[2], 1)}%.`, 'Fuentes: BIS / bancos centrales e INDEC.', [o.k, 'Ver ' + o.n]);
  }
  for (let n = 0; n < 400; n++) {
    const a = conI[Math.floor(rnd() * conI.length)], b = conI[Math.floor(rnd() * conI.length)];
    if (a === b || Math.abs(a.infl[1] - b.infl[1]) < .4) continue;
    vf('inf-' + a.k + '-' + b.k, a.k, a.fl, 'Inflación', `En ${a.n} los precios suben más rápido que en ${b.n}`, a.infl[1] > b.infl[1],
      `${a.n}: ${fN(a.infl[1], 1)}% en 12 meses. ${b.n}: ${fN(b.infl[1], 1)}%.`, 'Fuentes: BIS y bancos centrales.', ['global', 'Ver el comparador de países']);
  }
  // tasas de los bancos centrales
  const conT = Object.values(P.paises).filter(o => o.tasa != null && o.k !== 'eeuu');
  const eu = P.paises.eeuu;
  for (const o of conT) if (eu && eu.tasa != null && Math.abs(o.tasa - eu.tasa) >= .25)
    vf('tas-us-' + o.k, o.k, o.fl, 'Tasas', `El banco central de ${o.n} tiene la tasa más alta que la Fed`, o.tasa > eu.tasa,
      `${o.n}: ${fN(o.tasa, 2)}%. Estados Unidos: ${fN(eu.tasa - .125, 2)}–${fN(eu.tasa + .125, 2)}%.`, 'Fuente: BIS.', [o.k, 'Ver ' + o.n]);
  // inflación real: ¿la tasa le gana a los precios?
  for (const o of conT) if (o.infl && Math.abs(o.tasa - o.infl[1]) >= .3)
    vf('treal-' + o.k, o.k, o.fl, 'Tasas', `En ${o.n}, la tasa del banco central le gana a la inflación`, o.tasa > o.infl[1],
      `Tasa: ${fN(o.tasa, 2)}%. Inflación de 12 meses: ${fN(o.infl[1], 1)}%. ${o.tasa > o.infl[1] ? 'La tasa real es positiva: ahorrar en esa moneda rinde.' : 'La tasa real es negativa: el ahorro pierde contra los precios.'}`, 'Fuentes: BIS y bancos centrales.', [o.k, 'Ver ' + o.n]);
  // desempleo
  const conD = Object.values(P.paises).filter(o => o.desemp);
  for (let n = 0; n < 30; n++) {
    const a = conD[Math.floor(rnd() * conD.length)], b = conD[Math.floor(rnd() * conD.length)];
    if (a === b || Math.abs(a.desemp[1] - b.desemp[1]) < .4) continue;
    vf('des-' + a.k + '-' + b.k, a.k, a.fl, 'Desempleo', `Hay más desempleo en ${a.n} que en ${b.n}`, a.desemp[1] > b.desemp[1],
      `${a.n}: ${fN(a.desemp[1], 1)}%. ${b.n}: ${fN(b.desemp[1], 1)}%.`, 'Fuentes: OCDE y bancos centrales.', ['global', 'Ver el comparador de países']);
  }
  // Big Mac contra Argentina
  if (BA) for (const iso in BM) {
    if (iso === 'ARG' || !ISO[iso]) continue; const o = ISO[iso], b = BM[iso];
    if (Math.abs(b.usd - BA.usd) < .1) continue;
    vf('bm-' + iso, o.k, o.fl, 'Big Mac', `En dólares, un Big Mac sale más barato en Argentina que en ${o.n}`, BA.usd < b.usd,
      `Argentina: US$ ${fN(BA.usd, 2)}. ${o.n}: US$ ${fN(b.usd, 2)}.`, 'Fuente: The Economist' + BMF + '.', [o.k, 'Ver ' + o.n]);
  }
  // PBI por habitante en 1990 y hoy
  for (const iso in PPA) {
    if (iso === 'ARG' || !ISO[iso]) continue; const o = ISO[iso], s2 = PPA[iso];
    const a0 = ARP.find(z => z[0] === s2[0][0]); if (!a0) continue;
    const y0 = s2[0][0], ar0 = a0[1], ot0 = s2[0][1], aN = ult(ARP), oN = s2.find(z => z[0] === aN[0]);
    if (Math.abs(ar0 / ot0 - 1) > .04) vf('ppa0-' + iso, o.k, o.fl, 'Historia', `En ${y0}, Argentina producía más por habitante que ${o.n}`, ar0 > ot0,
      `Argentina: US$ ${fN(ar0)} por habitante. ${o.n}: US$ ${fN(ot0)} (a paridad de poder de compra, en dólares de hoy).`, 'Fuente: Banco Mundial.', [o.k, 'Ver ' + o.n]);
    if (oN && Math.abs(aN[1] / oN[1] - 1) > .04) vf('ppa1-' + iso, o.k, o.fl, 'Hoy', `Hoy, Argentina produce más por habitante que ${o.n}`, aN[1] > oN[1],
      `${aN[0]}: Argentina US$ ${fN(aN[1])} por habitante, ${o.n} US$ ${fN(oN[1])} (a paridad de poder de compra).`, 'Fuente: Banco Mundial.', [o.k, 'Ver ' + o.n]);
  }
  // crecimiento en la última década
  for (const iso in CR) {
    if (iso === 'ARG' || !ISO[iso]) continue; const o = ISO[iso];
    const yrs = CR[iso].map(x => x[0]).filter(y => ARC.find(z => z[0] === y)).slice(-10); if (yrs.length < 10) continue;
    const nb = yrs.filter(y => CR[iso].find(z => z[0] === y)[1] > 0).length, na = yrs.filter(y => ARC.find(z => z[0] === y)[1] > 0).length;
    if (nb === na) continue;
    vf('crec-' + iso, o.k, o.fl, 'Crecimiento', `En los últimos 10 años, Argentina tuvo más años de crecimiento que ${o.n}`, na > nb,
      `Argentina creció ${na} de 10 años (${yrs[0]}–${yrs[9]}); ${o.n}, ${nb}.`, 'Fuente: Banco Mundial.', [o.k, 'Ver ' + o.n]);
  }
  // bolsas del mundo en el año
  for (const k in P.bolsas) {
    const b = P.bolsas[k], o = pais(b.iso); if (Math.abs(b.va) < 1) continue;
    vf('bol-' + k + '-' + b.m, k, o.fl, 'Bolsas', `La bolsa de ${o.n} viene subiendo en lo que va del año`, b.va > 0,
      `Índice ${b.idx}: ${fP(b.va)} en el año, en su moneda, hasta fin de ${fMes(b.m)}.`, 'Fuente: OCDE.', ['global', 'Ver las bolsas del mundo']);
  }
  // materias primas contra hace un año
  for (const k in P.com) {
    const c = P.com[k]; if (!c.s || c.s.length < 13) continue;
    const s2 = c.s, [f, v] = ult(s2), a = c.mens ? s2[s2.length - 13] : (enFecha(s2, restar(f, 365)) || s2[0]), va = (v / a[1] - 1) * 100;
    if (Math.abs(va) < 2) continue;
    vf('com-' + k + '-' + f, k, null, 'Materias primas', `${CN[k] || c.n} está más ${['soja', 'plata'].includes(k) ? 'cara' : 'caro'} que hace un año`, va > 0,
      `${fP(va, 0)} en un año: ahora US$ ${fN(v, v < 100 ? 2 : 0)} (${c.u}).`, `Fuente: ${c.f}.`, ['global', 'Ver commodities']);
  }
  // acciones: A rindió más que B en dólares
  const tks = Object.keys(P.his.acc);
  const MV = P.his.acc.MERVAL ? 'MERVAL' : null;
  for (const [pk, dias, pn, pfr] of PER) {
    const res = {}; tks.forEach(tk => { const r = retUsd(tk, dias); if (r) res[tk] = r.r; });
    const ks = Object.keys(res).filter(k => k !== 'MERVAL');
    for (let n = 0; n < 160; n++) {
      const a = ks[Math.floor(rnd() * ks.length)], b = ks[Math.floor(rnd() * ks.length)];
      if (a === b || Math.abs(res[a] - res[b]) < 4) continue;
      vf(`acc-${a}-${b}-${pk}`, a, P.his.acc[a].t === 'ced' ? null : 'ar', 'Acciones', `${NOMA(a)} rindió más que ${NOMA(b)} ${pfr}, en dólares`, res[a] > res[b],
        `${NOMA(a)}: ${fP(res[a])}. ${NOMA(b)}: ${fP(res[b])}. En dólares MEP.`, 'Precios de BYMA y dólar MEP.', ['calculadoras', 'Probalo en el simulador']);
    }
    // ¿le ganó al dólar? (rendimiento en dólares positivo)
    for (const a of ks) {
      if (Math.abs(res[a]) < 3) continue;
      vf(`accd-${a}-${pk}`, a, P.his.acc[a].t === 'ced' ? null : 'ar', 'Acciones', `Quien compró ${NOMA(a)} hace ${pn} hoy tiene más dólares que antes`, res[a] > 0,
        `${fP(res[a])} en dólares MEP: US$ 1.000 pasaron a US$ ${fN(1000 * (1 + res[a] / 100))}.`, 'Precios de BYMA y dólar MEP.', ['calculadoras', 'Probalo en el simulador']);
      // "si hubieras invertido": ¿hoy tendrías más de X?
      const fin = 1000 * (1 + res[a] / 100), umb = [1100, 1250, 1500, 2000, 900, 750, 500].map(u => u).filter(u => Math.abs(fin / u - 1) > .06);
      if (umb.length) { const u = umb[Math.floor(rnd() * umb.length)];
        vf(`si-${a}-${pk}-${u}`, a, P.his.acc[a].t === 'ced' ? null : 'ar', 'Si hubieras invertido', `Si ponías US$ 1.000 en ${NOMA(a)} hace ${pn}, hoy tendrías más de US$ ${fN(u)}`, fin > u,
          `Hoy tendrías US$ ${fN(fin)} (${fP(res[a])} en dólares MEP).`, 'Comprando en pesos al MEP de ese día y vendiendo al MEP de hoy. Precios de BYMA.', ['calculadoras', 'Probalo en el simulador']); }
      // ¿le ganó al Merval?
      if (MV && res[MV] != null && Math.abs(res[a] - res[MV]) >= 3)
        vf(`mv-${a}-${pk}`, a, P.his.acc[a].t === 'ced' ? null : 'ar', 'Acciones', `${NOMA(a)} le ganó al Merval ${pfr}, en dólares`, res[a] > res[MV],
          `${NOMA(a)}: ${fP(res[a])}. Merval: ${fP(res[MV])}. En dólares MEP.`, 'Precios de BYMA y dólar MEP.', ['mercado', 'Ver Bolsa y bonos']);
    }
  }
  // inflación de un país contra un número
  for (const o of conI) for (const u of [2, 3, 5, 10, 20]) if (Math.abs(o.infl[1] - u) >= .4)
    vf(`infu-${o.k}-${u}`, o.k, o.fl, 'Inflación', `En ${o.n}, los precios subieron más del ${u}% en el último año`, o.infl[1] > u,
      `${o.n}: ${fN(o.infl[1], 1)}% en 12 meses, a ${fMes(o.infl[0])}.`, 'Fuentes: BIS y bancos centrales.', [o.k, 'Ver ' + o.n]);
  // Big Mac entre países
  const bmK = Object.keys(BM).filter(i => ISO[i] && i !== 'ARG');
  for (let n = 0; n < 250; n++) {
    const a = bmK[Math.floor(rnd() * bmK.length)], b = bmK[Math.floor(rnd() * bmK.length)];
    if (a === b || Math.abs(BM[a].usd - BM[b].usd) < .15) continue;
    vf(`bm2-${a}-${b}`, ISO[a].k, ISO[a].fl, 'Big Mac', `En dólares, un Big Mac es más caro en ${ISO[a].n} que en ${ISO[b].n}`, BM[a].usd > BM[b].usd,
      `${ISO[a].n}: US$ ${fN(BM[a].usd, 2)}. ${ISO[b].n}: US$ ${fN(BM[b].usd, 2)}.`, 'Fuente: The Economist' + BMF + '.', ['global', 'Ver el mundo']);
  }
  // PBI por habitante entre países
  const ppK = Object.keys(PPA).filter(i => ISO[i] && i !== 'ARG' && PPA[i].length);
  for (let n = 0; n < 250; n++) {
    const a = ppK[Math.floor(rnd() * ppK.length)], b = ppK[Math.floor(rnd() * ppK.length)]; if (a === b) continue;
    const va = ult(PPA[a]), vb = PPA[b].find(z => z[0] === va[0]); if (!vb || Math.abs(va[1] / vb[1] - 1) < .05) continue;
    vf(`pp2-${a}-${b}`, ISO[a].k, ISO[a].fl, 'Riqueza', `Por habitante, ${ISO[a].n} produce más que ${ISO[b].n}`, va[1] > vb[1],
      `${va[0]}: ${ISO[a].n} US$ ${fN(va[1])}, ${ISO[b].n} US$ ${fN(vb[1])} por habitante (a paridad de poder de compra).`, 'Fuente: Banco Mundial.', [ISO[a].k, 'Ver ' + ISO[a].n]);
  }
  // inflación mensual de Argentina en la historia reciente
  for (const [m, v] of A.infl.slice(-24)) for (const u of [1.5, 2, 2.5, 3, 4]) if (Math.abs(v - u) >= .2)
    vf(`ia-${m}-${u}`, 'ia' + m, 'ar', 'Inflación', `En ${fMes(m)}, la inflación en Argentina fue mayor al ${fN(u, 1)}%`, v > u,
      `Fue ${fN(v, 1)}% en el mes.`, 'Fuente: INDEC, vía BCRA.', ['macro', 'Ver inflación y reservas']);
  // dólar de hoy contra el de otros años, a precios de hoy
  const H = A.hist, cerHoy = ult(H)[5], mesHoy = ult(H)[0];
  for (const anios of [1, 2, 3, 4, 5, 6, 7, 8, 9]) {
    const mesA = (+mesHoy.slice(0, 4) - anios) + mesHoy.slice(4), r = H.find(x => x[0] === mesA); if (!r || !r[5]) continue;
    for (const [c, k, art] of [[2, 'blue', 'el blue'], [3, 'mep', 'el MEP'], [1, 'oficial', 'el oficial']]) {
      if (!r[c]) continue; const hoy = ult(A[k])[1], real = r[c] * cerHoy / r[5]; if (Math.abs(hoy / real - 1) < .03) continue;
      vf(`real-${k}-${anios}`, k + anios, 'ar', 'Dólar', `Descontando la inflación, ${art} de hoy está más caro que en ${fMes(mesA)}`, hoy > real,
        `En ${fMes(mesA)} valía $ ${fA(r[c])}, que a precios de hoy son $ ${fA(real)}. Hoy está en $ ${fA(hoy)}.`, 'Promedio mensual; inflación medida con el CER del BCRA.', ['dolares', 'Ver el dólar a precios de hoy']);
    }
  }
  // brecha
  const ofi = ult(A.oficial)[1];
  for (const [k, n] of [['blue', 'blue'], ['mep', 'MEP'], ['ccl', 'contado con liqui'], ['tarjeta', 'tarjeta'], ['cripto', 'cripto']]) {
    if (!A[k] || !A[k].length) continue; const b = (ult(A[k])[1] / ofi - 1) * 100; const umb = [5, 10, 20, 30][Math.floor(rnd() * 4)];
    if (Math.abs(b - umb) < 1.5) continue;
    vf(`bre-${k}-${umb}-${ult(A[k])[0]}`, 'brecha', 'ar', 'Dólar', `La brecha entre el dólar ${n} y el oficial supera el ${umb}%`, b > umb,
      `El ${n} cerró en $ ${fN(ult(A[k])[1], 2)} y el oficial en $ ${fN(ofi, 2)}: brecha de ${fP(b)}.`, `Cotizaciones del ${fFe(ult(A[k])[0])}.`, ['dolares', 'Ver los dólares']);
  }
}

// ---------- afuera lo poco llamativo (pedido del dueño 01/11/2026) ----------
// monedas en pesos, agenda/próximas publicaciones, noticias, bolsas y commodities mensuales, rankings de tasas/bonos/desempleo
{
  const FUERA_M = new Set(['mon', 'cd', 'nw', 'bol', 'com']);  // (desde el 01/11/2026 queda SOLO verdadero o falso)
  const FUERA_K = /^(rtas|rbon|rdes|rbol)/, FUERA_VF = /^vf-(bol|com|tas|des)-/;
  for (let i = R.length - 1; i >= 0; i--) {
    const r = R[i];
    if (r.mold !== 'vf' || FUERA_M.has(r.mold) || (r.mold === 'rmun' && FUERA_K.test(r.key)) || FUERA_VF.test(r.id)) R.splice(i, 1);
    else {  // grupo por tema, para que se mezclen y no sean todas de acciones
      const k = r.kick.replace('Verdadero o falso · ', '');
      r.cat = /Acciones|Si hubieras/.test(k) ? 'acc' : /Inflación/.test(k) ? 'inf' : /Dólar/.test(k) ? 'dol' : /Big Mac/.test(k) ? 'bm' : /Tasas/.test(k) ? 'tas' : 'his';
    }
  }
}
// ---------- el orden: al azar, pesado por interés, sin repetir molde ni tema seguido ----------
const VISTOS_K = 'pl-vistos';
let vistos = {}; try { vistos = JSON.parse(localStorage.getItem(VISTOS_K) || '{}'); } catch (e) {}
const SEMANA = 7 * 864e5;
const frescos = R.filter(r => !(vistos[r.id] && Date.now() - vistos[r.id] < SEMANA));
// cuánto de cada tema: así los cientos de "simulador" no tapan al resto
const CUOTA = {acc: 34, inf: 22, his: 18, dol: 12, bm: 9, tas: 5};
const base = frescos.length > 40 ? frescos : R;
const colas = {};
base.map(r => ({r, w: r.score * .55 + rnd() * .45})).sort((a, b) => b.w - a.w).forEach(({r}) => (colas[r.cat] = colas[r.cat] || []).push(r));
const ORD = [], recientes = [];
const sirve = (r, estricto) => {
  const u = ORD.slice(-4);
  if (u.length && r.mold === u[u.length - 1].mold && r.mold !== 'vf') return false;
  if (estricto && r.mold !== 'vf' && u.some(x => x.mold === r.mold)) return false;
  return !recientes.includes(r.key);
};
for (let total = base.length; ORD.length < total;) {
  const ultCat = ORD.length ? ORD[ORD.length - 1].cat : null;
  const cats = Object.keys(colas).filter(c => colas[c].length && c !== ultCat);
  const usables = cats.length ? cats : Object.keys(colas).filter(c => colas[c].length);
  let t = usables.reduce((s, c) => s + (CUOTA[c] || 5), 0) * rnd(), cat = usables[0];
  for (const c of usables) { t -= CUOTA[c] || 5; if (t <= 0) { cat = c; break; } }
  const q = colas[cat]; let i = q.findIndex(r => sirve(r, true)); if (i < 0) i = q.findIndex(r => sirve(r, false)); if (i < 0) i = 0;
  const r = q.splice(i, 1)[0]; ORD.push(r); recientes.push(r.key); if (recientes.length > 12) recientes.shift();
}

// el primero siempre es de Argentina y del día (a eso viene la mayoría)


// ---------- dibujar ----------
function svgLine(viz) {
  const all = viz.s.flatMap(s => s.v); let mn = Math.min(...all), mx = Math.max(...all);
  if (viz.base != null) { mn = Math.min(mn, viz.base); mx = Math.max(mx, viz.base); }
  const pad = (mx - mn) * .08 || 1; mn -= pad; mx += pad;
  const W = 400, H = 200, y = v => H - (v - mn) / (mx - mn) * H;
  let out = '';
  if (viz.base != null) out += `<line x1="0" x2="${W}" y1="${y(viz.base)}" y2="${y(viz.base)}" stroke="#ffffff30" stroke-dasharray="4 5" vector-effect="non-scaling-stroke"/>`;
  for (let g = 1; g < 4; g++) out += `<line x1="0" x2="${W}" y1="${H * g / 4}" y2="${H * g / 4}" stroke="#ffffff0c" vector-effect="non-scaling-stroke"/>`;
  const solo = viz.s.length === 1;  // una sola línea: blanca, que resalte sobre el color del reel
  viz.s.forEach((s, j) => {
  if (solo) s = {...s, c: '#ffffff'};
    const n = s.v.length, pts = s.v.map((v, i) => [(i / (n - 1)) * W, y(v)]);
    const d = 'M' + pts.map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join('L');
    if (viz.area && j === 0) out += `<path class="ar" d="${d}L${W} ${H}L0 ${H}Z" fill="url(#g${j})"/>`;
    out += `<defs><linearGradient id="g${j}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${s.c}" stop-opacity=".28"/><stop offset="1" stop-color="${s.c}" stop-opacity="0"/></linearGradient></defs>`;
    out += `<path class="p" pathLength="1" d="${d}" stroke="${s.c}"/>`;
  });
  return `<div class="ln"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">${out}</svg></div>`;
}
function vizHTML(r) {
  const v = r.viz; if (!v) return '';
  if (v.t === 'line') return svgLine(v) + `<div class="lnl"><span>${esc(v.a)}</span><span>${esc(v.b)}</span></div>` + (v.ley ? `<div class="ley">${v.s.map(s => `<span><i style="background:${s.c}"></i>${esc(s.l)}</span>`).join('')}</div>` : '');
  if (v.t === 'bars') {
    const mx = Math.max(...v.rows.map(x => Math.abs(x.v))) || 1;
    return `<div class="bars">${v.rows.map(x => `<div class="br${x.hl ? ' hl' : ''}"><span class="l">${flag(x.fl)}${esc(x.l)}</span><span class="t"><i class="${x.v < 0 ? 'neg' : ''}" data-w="${(Math.abs(x.v) / mx * 100).toFixed(1)}"></i></span><span class="v">${esc(x.txt)}</span></div>`).join('')}</div>`;
  }
  if (v.t === 'vs') { const b = x => `<div class="vb${x.w ? ' w' : ''}"><div class="h">${flag(x.fl)}${esc(x.l)}</div><div class="n">${esc(x.txt)}</div><div class="s">${esc(x.s)}</div></div>`; return `<div class="vs">${b(v.a)}<div class="vsx">CONTRA</div>${b(v.b)}</div>`; }
  if (v.t === 'hace') return `<div class="hace"><div class="col"><span class="y">${esc(v.a.l)}</span><span class="n">${esc(v.a.txt)}</span></div><span class="mul">${esc(v.mul)} →</span><div class="col"><span class="y">${esc(v.b.l)}</span><span class="n">${esc(v.b.txt)}</span></div></div>`;
  if (v.t === 'dots') return `<div class="dots">${v.rows.map(x => `<div class="dr"><div class="h">${flag(x.fl)}${esc(x.l)}<b>${x.v.filter(y => y > 0).length} de 10</b></div><div class="q">${x.v.map((y, i) => `<i class="${y > 0 ? 'u' : 'd'}" style="transition-delay:${i * 50}ms" title="${v.yrs[i]}: ${fP(y)}"></i>`).join('')}</div></div>`).join('')}<div class="dyr">${v.yrs.map(y => `<span>${String(y).slice(2)}</span>`).join('')}</div></div>`;
  if (v.t === 'quiz') return `<div class="quiz${v.vf ? ' vf' : ''}">${v.opts.map((o, i) => `<button type="button" class="op" data-q="${i}">${flag(o.fl)}${esc(o.l)}<span class="r">${esc(o.txt)}</span></button>`).join('')}</div><div class="qres" aria-live="polite">Tocá una opción.</div>`;
  if (v.t === 'count') return `<div class="cd" data-when="${v.when}"><div><b>0</b><span>días</span></div><div><b>0</b><span>horas</span></div><div><b>0</b><span>min</span></div><div><b>0</b><span>seg</span></div></div>` + (v.list.length ? `<div class="ag">${v.list.map(x => `<div><b>${esc(x.f)}</b>${esc(x.n)}</div>`).join('')}</div>` : '');
  if (v.t === 'news') return `<p class="nw">${esc(v.h)}</p><div class="nwm">${esc(v.f)} · ${esc(v.hace)}</div><a class="nwb" href="${esc(v.u)}" target="_blank" rel="noopener">Leer en ${esc(v.f)} ↗</a>`;
  return '';
}
const ICO = {
  share: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3m0 0L8 7m4-4l4 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"/></svg>',
  go: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V12M10 20V5M16 20V9M22 20H2"/></svg>'};
function reelHTML(r, i) {
  const big = r.big ? `<div class="big" data-v="${r.big.v}" data-d="${r.big.d || 0}" data-pre="${esc(r.big.pre || '')}" data-suf="${esc(r.big.suf || '')}">${esc((r.big.pre || '') + fN(r.big.v, r.big.d || 0) + (r.big.suf || ''))}</div>` : '';
  const chips = r.chips ? `<div class="chips">${r.chips.filter(c => c[0]).map(c => `<span class="chip ${c[1]}">${esc(c[0])}</span>`).join('')}</div>` : '';
  const pa = PAL[(hash(r.id) + i * 7) % PAL.length]; if (i > 0 && ORD[i - 1].pal === pa) r.pal = PAL[(PAL.indexOf(pa) + 4) % PAL.length]; else r.pal = pa;
  return `<section class="reel c-${r.cat}" data-i="${i}" style="--c:${r.pal[0]};--c2:${r.pal[1]}">
    <div class="rin"><div class="kick">${flag(r.fl)}<span>${esc(r.kick)}</span></div>
    ${r.title ? `<h2 class="tit">${esc(r.title)}</h2>` : ''}${big}${chips}
    <div class="viz">${vizHTML(r)}</div>${r.nota ? `<p class="nota">${esc(r.nota)}</p>` : ''}<div class="src">${esc(r.src)}</div></div>
    <div class="rail"><button type="button" class="rb" data-share="${i}"><i>${ICO.share}</i>Compartir</button><a class="rb" href="${SITIO}#${r.go[0]}" title="${esc(r.go[1])}"><i>${ICO.go}</i>Ver más</a></div></section>`;
}
// intro (la primera vez) con cuántos reels hay hoy
const feed = $('#feed'); feed.innerHTML = '';
let primera = true; try { primera = !localStorage.getItem('pl-intro'); } catch (e) {}
const nCats = {}; R.forEach(r => nCats[r.cat] = (nCats[r.cat] || 0) + 1);
const INTRO = `<section class="reel intro c-arg" data-i="-1"><div class="rin">
  <h1>Verdadero <span>o falso</span></h1>
  <p>La economía de Argentina y el mundo, con datos reales. ¿Cuántas acertás seguidas?</p>
  <div class="n"><b>${fN(R.length)}</b> preguntas distintas hoy</div>
  <div class="swipe"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5m0 0l-6 6m6-6l6 6"/></svg>Deslizá para arriba</div></div></section>`;
let pintados = 0;
function pintar(n) { let h = ''; for (let k = 0; k < n && pintados < ORD.length; k++, pintados++) h += reelHTML(ORD[pintados], pintados); feed.insertAdjacentHTML('beforeend', h); feed.querySelectorAll('.reel:not([data-o])').forEach(el => { el.dataset.o = 1; io.observe(el); }); }

// animaciones al entrar a cada reel + memoria de vistos
let actual = -1, tVisto = null;
const io = new IntersectionObserver(es => es.forEach(e => {
  if (!e.isIntersecting) return;
  const el = e.target, i = +el.dataset.i; actual = i;
  el.classList.add('on');
  el.querySelectorAll('.br .t i').forEach(b => requestAnimationFrame(() => b.style.width = b.dataset.w + '%'));
  const bg = el.querySelector('.big[data-v]'); if (bg && !bg.dataset.ok) { bg.dataset.ok = 1; contar(bg); }
  clearTimeout(tVisto);
  if (i >= 0) { tVisto = setTimeout(() => { vistos[ORD[i].id] = Date.now(); try { localStorage.setItem(VISTOS_K, JSON.stringify(vistos)); } catch (er) {} }, 1200); }
  else { try { localStorage.setItem('pl-intro', '1'); } catch (er) {} }
  if (i >= pintados - 4) pintar(8);
  const r = ORD[i]; $('#fCat').textContent = r ? CATN[r.cat] : 'Inicio'; $('#fBar').style.width = Math.min(100, (Math.max(0, i + 1) / ORD.length) * 100) + '%'; $('#fBar').style.background = r && r.pal ? `linear-gradient(90deg,${r.pal[0]},${r.pal[1]})` : '';
  $('#fN').textContent = i >= 0 ? `${fN(i + 1)} de ${fN(ORD.length)}` : `${fN(ORD.length)} reels`;
}), {threshold: .6});
function contar(el) {
  const v = +el.dataset.v, d = +el.dataset.d, pre = el.dataset.pre, suf = el.dataset.suf, t0 = performance.now(), dur = 900;
  const paso = t => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3); el.textContent = pre + fN(v * (.6 + .4 * e), d) + suf; if (k < 1) requestAnimationFrame(paso); else el.textContent = pre + fN(v, d) + suf; };
  requestAnimationFrame(paso);
}
if (primera) feed.insertAdjacentHTML('beforeend', INTRO);
pintar(10); if (primera) io.observe(feed.querySelector('.intro'));

// cuentas regresivas (solo la que está a la vista)
setInterval(() => { const el = document.querySelector(`.reel[data-i="${actual}"] .cd`); if (!el) return; let s = Math.max(0, (+el.dataset.when - Date.now()) / 1000);
  const v = [Math.floor(s / 86400), Math.floor(s % 86400 / 3600), Math.floor(s % 3600 / 60), Math.floor(s % 60)]; el.querySelectorAll('b').forEach((b, i) => b.textContent = String(v[i]).padStart(2, '0')); }, 250);

// trivia
feed.addEventListener('click', e => {
  const op = e.target.closest('.op'); if (op) {
    const q = op.closest('.quiz'); if (q.classList.contains('ok')) return;
    const r = ORD[+op.closest('.reel').dataset.i], o = r.viz.opts[+op.dataset.q];
    q.classList.add('ok'); q.querySelectorAll('.op').forEach((b, j) => { if (r.viz.opts[j].ok) b.classList.add('si'); });
    if (!o.ok) op.classList.add('mal');
    const ver = r.viz.vf ? `Es <b>${r.viz.opts[0].ok ? 'verdadero' : 'falso'}</b>. ` : '';
    q.nextElementSibling.innerHTML = (o.ok ? '¡Bien! ' : 'No. ') + ver + r.viz.exp;
    premio(o.ok, op, q.closest('.reel'));
    return;
  }
  const sh = e.target.closest('[data-share]'); if (sh) compartir(ORD[+sh.dataset.share]);
});
// ---------- premios al responder (pedido del dueño 01/11/2026: dopamina tipo casino, sin exagerar) ----------
let PT = {p: 0, r: 0, max: 0}; try { PT = {...PT, ...JSON.parse(localStorage.getItem('pl-pts') || '{}')}; } catch (e) {}
const ptsEl = $('#pts');
const ptsPintar = (anim) => {
  ptsEl.hidden = !PT.p && !PT.r;
  ptsEl.querySelector('b').textContent = fN(PT.p);
  const ra = ptsEl.querySelector('.ra'); ra.hidden = PT.r < 2; ra.textContent = '×' + PT.r;
  if (anim) { ptsEl.classList.remove(anim); void ptsEl.offsetWidth; ptsEl.classList.add(anim); }
};
ptsPintar();
const FRASE_OK = ['¡Bien!', '¡Bien ahí!', '¡Sabés!', '¡Crack!', '¡Exacto!'];
const FRASE_RACHA = {3: '¡Racha de 3!', 5: '¡5 seguidas!', 7: '¡Imparable!', 10: '¡10 seguidas!', 15: '¡Leyenda!'};
function premio(ok, btn, reel) {
  if (ok) {
    PT.r++; PT.max = Math.max(PT.max, PT.r);
    const gana = 10 * Math.min(5, PT.r);           // la racha multiplica (tope ×5): da ganas de no cortarla
    PT.p += gana;
    flotar(btn, '+' + gana, '#7dffc4');
    confeti(btn, PT.r >= 3 ? 34 : 18);
    if (FRASE_RACHA[PT.r]) cartel(reel, FRASE_RACHA[PT.r]);
    try { navigator.vibrate && navigator.vibrate(18); } catch (e) {}
    ptsPintar('gana');
  } else {
    const perdio = PT.r;
    PT.r = 0;
    btn.classList.remove('tiembla'); void btn.offsetWidth; btn.classList.add('tiembla');
    if (perdio >= 2) flotar(btn, 'Se cortó la racha de ' + perdio, '#ffd0d8');
    try { navigator.vibrate && navigator.vibrate([12, 40, 12]); } catch (e) {}
    ptsPintar('pierde');
  }
  try { localStorage.setItem('pl-pts', JSON.stringify(PT)); } catch (e) {}
  // empujoncito a seguir: la flecha de abajo late
  const sig = reel.querySelector('.sigue'); if (sig) sig.hidden = false;
  else reel.querySelector('.rin').insertAdjacentHTML('beforeend', `<button type="button" class="sigue">${ok ? 'Seguí la racha' : 'Probá con la próxima'} <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6l4 4 4-4"/></svg></button>`);
  try { window.goatcounter && goatcounter.count({path: ok ? 'live-acierto' : 'live-error', event: true}); } catch (e) {}
}
function flotar(el, txt, col) {
  const b = el.getBoundingClientRect(), d = document.createElement('div');
  d.className = 'flota'; d.textContent = txt; d.style.cssText = `left:${Math.max(120, Math.min(innerWidth - 120, b.left + b.width / 2))}px;top:${b.top}px;color:${col}`;
  document.body.appendChild(d); setTimeout(() => d.remove(), 1100);
}
function cartel(reel, txt) {
  const d = document.createElement('div'); d.className = 'cartel'; d.textContent = txt;
  reel.appendChild(d); setTimeout(() => d.remove(), 1500);
}
function confeti(el, n) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const b = el.getBoundingClientRect(), cx = b.left + b.width / 2, cy = b.top + b.height / 2;
  const cv = document.createElement('canvas'), dpr = Math.min(2, devicePixelRatio || 1);
  cv.className = 'confeti'; cv.width = innerWidth * dpr; cv.height = innerHeight * dpr; document.body.appendChild(cv);
  const x = cv.getContext('2d'); x.scale(dpr, dpr);
  const COL = ['#7dffc4', '#ffd23d', '#ff5c8a', '#5fb4ff', '#ffffff', '#b57bff'];
  const ps = Array.from({length: n}, () => { const a = -Math.PI / 2 + (rnd() - .5) * 2.2, v = 5 + rnd() * 7;
    return {x: cx, y: cy, vx: Math.cos(a) * v, vy: Math.sin(a) * v, r: 3 + rnd() * 4, c: COL[Math.floor(rnd() * COL.length)], g: rnd() * 6, w: rnd() * .3 - .15}; });
  const t0 = performance.now();
  (function paso(t) {
    const k = (t - t0) / 1000; x.clearRect(0, 0, innerWidth, innerHeight);
    for (const p of ps) { p.vy += .32; p.vx *= .985; p.x += p.vx; p.y += p.vy; p.g += p.w;
      x.save(); x.globalAlpha = Math.max(0, 1 - k / 1.1); x.translate(p.x, p.y); x.rotate(p.g); x.fillStyle = p.c; x.fillRect(-p.r, -p.r / 2, p.r * 2, p.r); x.restore(); }
    if (k < 1.1) requestAnimationFrame(paso); else cv.remove();
  })(t0);
}
feed.addEventListener('click', e => { if (e.target.closest('.sigue')) ir(1); });

// teclado, botones y rueda
const ir = d => { const h = feed.clientHeight; feed.scrollBy({top: d * h, behavior: 'smooth'}); };
$('#up').onclick = () => ir(-1); $('#down').onclick = () => ir(1);
addEventListener('keydown', e => { if (e.key === 'ArrowDown' || e.key === 'j' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); ir(1); } if (e.key === 'ArrowUp' || e.key === 'k' || e.key === 'PageUp') { e.preventDefault(); ir(-1); } });

// ---------- imagen para compartir (1080 × 1920, para historias) ----------
function compartir(r) {
  const W = 1080, H = 1920, cv = document.createElement('canvas'); cv.width = W; cv.height = H; const x = cv.getContext('2d');
  const col = r.pal ? r.pal[0] : CC[r.cat]; x.fillStyle = '#0b0d14'; x.fillRect(0, 0, W, H);
  if (r.pal) { const lg = x.createLinearGradient(0, 0, W, H); lg.addColorStop(0, r.pal[0] + 'aa'); lg.addColorStop(1, r.pal[1] + '66'); x.fillStyle = lg; x.fillRect(0, 0, W, H); }
  let g = x.createRadialGradient(W / 2, 0, 0, W / 2, 0, 1300); g.addColorStop(0, col + '55'); g.addColorStop(1, '#0e131900'); x.fillStyle = g; x.fillRect(0, 0, W, H);
  const M = 90, F = (s, w = 500, f = 'Instrument Sans') => `${w} ${s}px "${f}", system-ui, sans-serif`, MO = (s, w = 500) => `${w} ${s}px "JetBrains Mono", ui-monospace, monospace`;
  const wrap = (t, y, s, w, lh, maxw = W - 2 * M) => { x.font = F(s, w); const ws = t.split(' '); let l = ''; for (const p of ws) { if (x.measureText(l + p).width > maxw && l) { x.fillText(l.trim(), M, y); y += lh; l = ''; } l += p + ' '; } x.fillText(l.trim(), M, y); return y + lh; };
  x.textBaseline = 'alphabetic'; x.fillStyle = col; x.font = MO(30); x.fillText(r.kick.toUpperCase(), M, 260);
  x.fillStyle = '#e6edf3'; let y = wrap(r.title || r.viz.h || '', 360, r.viz && r.viz.t === 'news' ? 74 : 66, 600, r.viz && r.viz.t === 'news' ? 90 : 80);
  y += 30;
  if (r.big) { x.font = MO(150, 500); x.fillText((r.big.pre || '') + fN(r.big.v, r.big.d || 0) + (r.big.suf || ''), M, y + 120); y += 190;
    if (r.chips) { let cx = M; x.font = MO(34); for (const c of r.chips.filter(c => c[0])) { const tw = x.measureText(c[0]).width + 40; x.fillStyle = c[1] === 'up' ? '#2fbf7a26' : c[1] === 'dn' ? '#e5534b26' : '#ffffff14'; x.beginPath(); x.roundRect(cx, y, tw, 64, 12); x.fill(); x.fillStyle = c[1] === 'up' ? '#2fbf7a' : c[1] === 'dn' ? '#e5534b' : '#c4cfdb'; x.fillText(c[0], cx + 20, y + 44); cx += tw + 16; if (cx > W - 300) { cx = M; y += 80; } } y += 110; } }
  const v = r.viz;
  if (v && v.t === 'line') { const h = 520, all = v.s.flatMap(s => s.v); let mn = Math.min(...all), mx = Math.max(...all); const pd = (mx - mn) * .08 || 1; mn -= pd; mx += pd;
    v.s.forEach(s => { x.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue(s.c.slice(4, -1)).trim() || s.c; if (s.c.startsWith('var')) x.strokeStyle = {'var(--s1)': '#3987e5', 'var(--s2)': '#d95926', 'var(--s3)': '#199e70', 'var(--s4)': '#c98500', 'var(--s5)': '#d55181', 'var(--up)': '#2fbf7a', 'var(--dn)': '#e5534b'}[s.c] || '#6aa8d8';
      x.lineWidth = 7; x.lineJoin = 'round'; x.beginPath(); s.v.forEach((p, i) => { const px = M + i / (s.v.length - 1) * (W - 2 * M), py = y + h - (p - mn) / (mx - mn) * h; i ? x.lineTo(px, py) : x.moveTo(px, py); }); x.stroke(); });
    x.fillStyle = '#5d6b7d'; x.font = MO(28); x.fillText(v.a, M, y + h + 60); const tb = x.measureText(v.b).width; x.fillText(v.b, W - M - tb, y + h + 60); y += h + 120;
    if (v.ley) { let cx = M; x.font = F(34); v.s.forEach(s => { x.fillStyle = {'var(--s1)': '#3987e5', 'var(--s3)': '#199e70'}[s.c] || '#6aa8d8'; x.fillRect(cx, y - 14, 34, 8); x.fillStyle = '#c4cfdb'; x.fillText(s.l, cx + 48, y); cx += x.measureText(s.l).width + 110; }); y += 60; } }
  if (v && v.t === 'bars') { const mx = Math.max(...v.rows.map(z => Math.abs(z.v))) || 1; v.rows.forEach(z => { x.font = F(38, z.hl ? 700 : 500); x.fillStyle = z.hl ? '#fff' : '#c4cfdb'; x.fillText(z.l, M, y + 38); x.fillStyle = '#ffffff12'; x.fillRect(M + 330, y + 12, 430, 30); x.fillStyle = z.v < 0 ? '#e5534b' : z.hl ? '#ffffff' : col; x.fillRect(M + 330, y + 12, 430 * Math.abs(z.v) / mx, 30); x.font = MO(36); x.fillStyle = '#e6edf3'; const t = z.txt, tw = x.measureText(t).width; x.fillText(t, W - M - tw, y + 40); y += 78; }); y += 30; }
  if (v && (v.t === 'vs')) { for (const z of [v.a, v.b]) { x.fillStyle = z.w ? col + '33' : '#ffffff0d'; x.beginPath(); x.roundRect(M, y, W - 2 * M, 250, 28); x.fill(); x.fillStyle = '#c4cfdb'; x.font = F(40); x.fillText(z.l, M + 44, y + 76); x.fillStyle = '#e6edf3'; x.font = MO(104); x.fillText(z.txt, M + 44, y + 190); x.fillStyle = '#5d6b7d'; x.font = F(30); x.fillText(z.s, M + 44, y + 232); y += 280; } }
  if (v && v.t === 'hace') { x.fillStyle = '#8b9bb0'; x.font = MO(34); x.fillText(v.a.l, M, y); x.fillText(v.b.l, W / 2 + 40, y); x.fillStyle = '#e6edf3'; x.font = MO(92); x.fillText(v.a.txt, M, y + 110); x.fillText(v.b.txt, W / 2 + 40, y + 110); x.fillStyle = col; x.font = MO(44); x.fillText(v.mul, M, y + 220); y += 300; }
  if (v && v.t === 'quiz') { v.opts.forEach(o => { x.fillStyle = o.ok ? '#2fbf7a26' : '#ffffff0d'; x.beginPath(); x.roundRect(M, y, W - 2 * M, 120, 24); x.fill(); x.fillStyle = '#e6edf3'; x.font = F(44, 600); x.fillText(o.l, M + 40, y + 76); if (o.txt) { x.font = MO(40); const tw = x.measureText(o.txt).width; x.fillStyle = o.ok ? '#2fbf7a' : '#8b9bb0'; x.fillText(o.txt, W - M - 40 - tw, y + 76); } y += 145; }); }
  if (v && v.t === 'dots') { v.rows.forEach(z => { x.fillStyle = '#e6edf3'; x.font = F(40, 600); x.fillText(z.l + ' · ' + z.v.filter(q => q > 0).length + ' de 10', M, y); y += 30; z.v.forEach((q, i) => { x.fillStyle = q > 0 ? '#2fbf7a' : '#e5534b'; x.beginPath(); x.roundRect(M + i * 90, y, 74, 74, 12); x.fill(); }); y += 140; }); }
  if (v && v.t === 'count') { const s = Math.max(0, (v.when - Date.now()) / 1000); x.fillStyle = '#e6edf3'; x.font = MO(130); x.fillText(`${Math.floor(s / 86400)}d ${String(Math.floor(s % 86400 / 3600)).padStart(2, '0')}h ${String(Math.floor(s % 3600 / 60)).padStart(2, '0')}m`, M, y + 120); y += 220; }
  if (r.nota) { x.fillStyle = '#c4cfdb'; y = wrap(r.nota, y + 20, 36, 400, 52); }
  x.fillStyle = '#5d6b7d'; wrap(r.src, H - 260, 28, 400, 40);
  x.strokeStyle = '#ffffff1a'; x.lineWidth = 2; x.beginPath(); x.moveTo(M, H - 170); x.lineTo(W - M, H - 170); x.stroke();
  x.font = F(52, 700); x.fillStyle = '#e6edf3'; x.fillText('Pulso', M, H - 90); const pw = x.measureText('Pulso').width; x.font = MO(52, 500); x.fillStyle = '#6aa8d8'; x.fillText('Macro', M + pw + 4, H - 90);
  x.font = MO(32); x.fillStyle = '#8b9bb0'; const u = 'pulsomacro.com.ar', uw = x.measureText(u).width; x.fillText(u, W - M - uw, H - 94);
  const url = cv.toDataURL('image/png'); $('#mImg').src = url; $('#mDl').href = url; $('#modal').hidden = false;
  const sh = $('#mSh'); sh.hidden = true;
  cv.toBlob(b => {
    if (!b) return; const f = new File([b], 'pulso-macro_reel.png', {type: 'image/png'});
    if (navigator.canShare && navigator.canShare({files: [f]})) { sh.hidden = false; sh.onclick = () => navigator.share({files: [f], text: (r.title || '') + ' · pulsomacro.com.ar/live/ · ¿Vos sabés?'}).catch(() => {}); }
  }, 'image/png');
  try { window.goatcounter && goatcounter.count({path: 'live-compartir', event: true}); } catch (e) {}
}
$('#mX').onclick = () => $('#modal').hidden = true;
$('#modal').onclick = e => { if (e.target.id === 'modal') $('#modal').hidden = true; };
window.__reels = {total: R.length, porMolde: R.reduce((a, r) => (a[r.mold] = (a[r.mold] || 0) + 1, a), {}), porCat: nCats};
}
})();
