// Arma crucigrama/grillas.js: la grilla completa de cada día del crucigrama, formato "estilo La Nación" (pedido del dueño
// 02/11/2026: 25 a 32 palabras, casilleros grandes). Grilla de 11×11 con casilleros negros, simétrica (giro de 180°):
// filas y columnas pares tienen palabras (de 3, 5, 7 u 11 letras); en las impares, una letra sí y una no, de modo que cada
// palabra se cruza con otras cada dos letras.
// Reglas comprobadas día por día (desde el 03/11/2026, solo economía: con menos palabras, se repiten antes; ver CLAUDE.md):
//  - ninguna palabra de 5 letras o más se repite antes de GAP días (60, pedido del dueño); las de 3 letras, GAP3 (en español
//    hay pocas palabras de 3 letras: se repiten antes, pero nunca dentro de las 3 semanas);
//  - dos crucigramas cualesquiera comparten como mucho MAXC palabras (4, pedido del dueño);
//  - entre 26 y 28 palabras por día; como mucho SIGLAS siglas por día.
// Uso: node scripts/crucigrama_grillas.js [días] [--desde=AAAA-MM-DD]
//   Los días anteriores a --desde (por defecto, mañana) se conservan tal cual del archivo anterior (lo publicado no cambia).
//   Palabras nuevas: SIEMPRE al final de palabras.js; para sacar una, dejar ['', ''] y volver a correr esto.
const fs = require('fs'), path = require('path');
const R = p => fs.readFileSync(path.join(__dirname, '..', p), 'utf8');
// SOLO ECONOMÍA (pedido del dueño 03/11/2026: "se lo anuncié a todo el mundo como un crucigrama de economía"): se usan las
// palabras de palabras.js hasta la marca "FIN DE ECONOMÍA"; lo que está debajo (cosas de todos los días) queda afuera.
const TXT = R('crucigrama/palabras.js'), CORTE = TXT.indexOf('FIN DE ECONOMÍA');
// también entran las de abajo que tienen un 1 como tercer dato (palabras con pista de economía, sumadas el 03/11/2026)
const N_ECO = CORTE > 0 ? (TXT.slice(0, CORTE).match(/^\s*\['/gm) || []).length : Infinity;
const PALABRAS = new Function(TXT.replace('const PALABRAS', 'var PALABRAS') + '; return PALABRAS;')().filter((e, i) => i < N_ECO || e[2] === 1);
const ENV = k => process.env[k] != null ? +process.env[k] : null;
const DIAS = +(process.argv.find(a => /^\d+$/.test(a)) || 760), N0 = 3, GAP = ENV('GAP') ?? 21, GAP3 = ENV('GAP3') ?? 7, MAXC = ENV('MAXC') ?? 6, SIGLAS = ENV('SIGLAS') ?? 12, SZ = 11;
const fecha = n => new Date(Date.parse('2026-11-01') + (n - 1) * 864e5).toISOString().slice(0, 10);
const desde = (process.argv.find(a => a.startsWith('--desde=')) || '').slice(8) || fecha(Math.round((Date.now() - 3 * 3600e3 - Date.parse('2026-11-01')) / 864e5) + 2);

function semilla(txt) { let h = 2166136261; for (const c of txt) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
function azar(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// ---------- banco ----------
const PISTA = new Map(); for (const [w, p] of PALABRAS) if (w && /^[A-ZÑ]+$/.test(w) && !PISTA.has(w)) PISTA.set(w, p);
const byLen = {}; for (const w of PISTA.keys()) if ([3, 5, 7, 11].includes(w.length)) (byLen[w.length] = byLen[w.length] || []).push(w);
const esSigla = w => /sigla|código|abreviatura/i.test(PISTA.get(w));
const M = {}, FULL = {};
for (const L in byLen) {
  const n = byLen[L].length, Wd = (n + 31) >>> 5; FULL[L] = new Uint32Array(Wd); for (let i = 0; i < n; i++) FULL[L][i >>> 5] |= 1 << (i & 31);
  M[L] = []; for (let p = 0; p < L; p++) { const m = new Map(); byLen[L].forEach((w, i) => { if (!m.has(w[p])) m.set(w[p], new Uint32Array(Wd)); m.get(w[p])[i >>> 5] |= 1 << (i & 31); }); M[L].push(m); }
}
const pc = a => { let c = 0; for (let v of a) { v = v - ((v >>> 1) & 0x55555555); v = (v & 0x33333333) + ((v >>> 2) & 0x33333333); c += (((v + (v >>> 4)) & 0xF0F0F0F) * 0x1010101) >>> 24; } return c; };

// ---------- dibujo de casilleros negros ----------
// cada par de filas (0 y 10, 2 y 8, 4 y 6) y de columnas lleva el mismo corte, al revés: así queda simétrica
function patron(rnd) {
  // un par con tres palabras de 3 (si no, no se llega a 26 palabras); el resto, 5 + 5 o 3 + 7. De vez en cuando una de 11
  // letras de punta a punta, compensada con otro par de tres palabras de 3 (pocas palabras de 3: se usan lo justo)
  const pares = Array.from({length: 6}, () => { const x = rnd(); return x < .54 ? [5, 5] : x < .77 ? [3, 7] : [7, 3]; });
  const orden = [0, 1, 2, 3, 4, 5].sort(() => rnd() - .5);
  pares[orden[0]] = [3, 3, 3];
  if (rnd() < .12) { pares[orden[1]] = [11]; pares[orden[2]] = [3, 3, 3]; }
  const pr = pares.slice(0, 3), pcl = pares.slice(3);
  const g = Array.from({length: SZ}, (_, y) => Array.from({length: SZ}, (_, x) => (x % 2 && y % 2) ? 1 : 0));
  const corta = (parts, fn) => { let pos = 0; parts.forEach((L, j) => { pos += L; if (j < parts.length - 1) { fn(pos); pos++; } }); };
  for (let i = 0; i < 3; i++) {
    corta(pr[i], x => { g[2 * i][x] = 1; }); corta(pr[i].slice().reverse(), x => { g[10 - 2 * i][x] = 1; });
    corta(pcl[i], y => { g[y][2 * i] = 1; }); corta(pcl[i].slice().reverse(), y => { g[y][10 - 2 * i] = 1; });
  }
  // validar: sin tramos de 2; toda casilla blanca en una palabra de 3+
  const en = new Set(); let ok = true;
  const tramos = (get, fn) => { for (let a = 0; a < SZ; a++) { let b = 0; while (b < SZ) { if (!get(a, b)) { const s = b; while (b < SZ && !get(a, b)) b++; fn(a, s, b - s); } else b++; } } };
  tramos((y, x) => g[y][x], (y, s, L) => { if (L === 2) ok = false; if (L >= 3) for (let k = s; k < s + L; k++) en.add(k + ',' + y); });
  tramos((x, y) => g[y][x], (x, s, L) => { if (L === 2) ok = false; if (L >= 3) for (let k = s; k < s + L; k++) en.add(x + ',' + k); });
  for (let y = 0; y < SZ; y++) for (let x = 0; x < SZ; x++) if (!g[y][x] && !en.has(x + ',' + y)) ok = false;
  if (!ok) return null;
  // todo conectado (si no, quedaban cuatro crucigramas separados) y el centro abierto por al menos 2 lados
  const vis = new Set(['0,0']), cola = [[0, 0]];
  while (cola.length) { const [x, y] = cola.pop(); for (const [a, b] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) if (a >= 0 && b >= 0 && a < SZ && b < SZ && !g[b][a] && !vis.has(a + ',' + b)) { vis.add(a + ',' + b); cola.push([a, b]); } }
  let blancas = 0; for (let y = 0; y < SZ; y++) for (let x = 0; x < SZ; x++) if (!g[y][x]) blancas++;
  if (vis.size !== blancas) return null;
  let pasan = 0; for (let k = 0; k < SZ; k += 2) { if (!g[5][k]) pasan++; if (!g[k][5]) pasan++; }
  return pasan >= 4 ? g : null;
}

// ---------- llenar con palabras (búsqueda con vuelta atrás; prefiere las que hace más que no salen) ----------
function llenar(g, permit, prio, rnd) {
  const S = [];
  for (let y = 0; y < SZ; y++) { let x = 0; while (x < SZ) { if (!g[y][x]) { const s = x; while (x < SZ && !g[y][x]) x++; if (x - s >= 3) S.push({c: Array.from({length: x - s}, (_, i) => y * SZ + s + i)}); } else x++; } }
  for (let x = 0; x < SZ; x++) { let y = 0; while (y < SZ) { if (!g[y][x]) { const s = y; while (y < SZ && !g[y][x]) y++; if (y - s >= 3) S.push({c: Array.from({length: y - s}, (_, i) => (s + i) * SZ + x)}); } else y++; } }
  if (S.length < 26 || S.length > 32) return null;
  const L = new Array(SZ * SZ).fill(null), used = new Set(); let pasos = 0, sig = 0;
  const dom = s => { const n = s.c.length; let d = null; for (let p = 0; p < n; p++) { const ch = L[s.c[p]]; if (ch) { const m = M[n][p].get(ch); if (!m) return new Uint32Array(FULL[n].length); if (!d) d = m.slice(); else for (let i = 0; i < d.length; i++) d[i] &= m[i]; } } if (!d) return permit[n]; for (let i = 0; i < d.length; i++) d[i] &= permit[n][i]; return d; };
  function rec() {
    if (++pasos > 60000) return false; let bs = null, bd = null, bc = 1e9;
    for (const s of S) { if (s.w) continue; const d = dom(s); const c = pc(d); if (c === 0) return false; if (c < bc) { bc = c; bs = s; bd = d; } }
    if (!bs) return true; const n = bs.c.length, ids = [];
    for (let i = 0; i < bd.length; i++) { let v = bd[i]; while (v) { const b = v & -v; ids.push(i * 32 + 31 - Math.clz32(b)); v ^= b; } }
    const or = ids.map(i => [i, prio(byLen[n][i]) + rnd() * 3]).sort((a, b) => a[1] - b[1]).slice(0, 12);
    for (const [i] of or) {
      const w = byLen[n][i]; if (used.has(w)) continue; const sg = esSigla(w); if (sg && sig >= SIGLAS) continue;
      const prev = bs.c.map(k => L[k]); bs.c.forEach((k, p) => L[k] = w[p]); bs.w = w; used.add(w); if (sg) sig++;
      if (rec()) return true;
      used.delete(w); if (sg) sig--; bs.w = null; bs.c.forEach((k, p) => L[k] = prev[p]); if (pasos > 60000) return false;
    }
    return false;
  }
  return rec() ? {S, L, words: S.map(s => s.w)} : null;
}

// ---------- plan día por día ----------
const ult = new Map(), usos = new Map(), diasDe = new Map(), plan = [];
let viejo = null; try { viejo = new Function(R('crucigrama/grillas.js').replace('const CRUCI_G', 'var CRUCI_G') + '; return CRUCI_G;')(); } catch (e) {}
const palabrasDe = s => { const g = Array.from({length: SZ}, (_, y) => s.slice(y * SZ, y * SZ + SZ)), out = [];
  for (let y = 0; y < SZ; y++) for (const m of g[y].matchAll(/[A-ZÑ]{3,}/g)) out.push(m[0]);
  for (let x = 0; x < SZ; x++) { const col = g.map(r => r[x]).join(''); for (const m of col.matchAll(/[A-ZÑ]{3,}/g)) out.push(m[0]); }
  return out; };
const anotar = (n, ws) => ws.forEach(w => { ult.set(w, n); usos.set(w, (usos.get(w) || 0) + 1); if (!diasDe.has(w)) diasDe.set(w, []); diasDe.get(w).push(n); });
const t0 = Date.now(), cuantas = {}, tres = [], relaj = [];
for (let n = N0; n < N0 + DIAS; n++) {
  const HOY = fecha(n); let res = null;
  if (viejo && HOY < desde && viejo.d[n - viejo.n0]) { const s = viejo.d[n - viejo.n0]; res = {s, words: palabrasDe(s)}; }
  for (let a = 0, gap = GAP; !res; a++) {
    if (a && a % 400 === 0) { gap -= 5; relaj.push(n); }               // si no sale, se afloja de a poco (avisa al final)
    const rnd = azar(semilla('grilla-' + n + '-' + a));
    const permit = {};
    for (const Lx in byLen) { const lim = +Lx === 3 ? GAP3 : gap; permit[Lx] = FULL[Lx].slice(); byLen[Lx].forEach((w, i) => { if (ult.has(w) && n - ult.get(w) < lim) permit[Lx][i >>> 5] &= ~(1 << (i & 31)); }); }
    const g = patron(rnd); if (!g) continue;
    const r = llenar(g, permit, w => (usos.get(w) || 0) * 4 + (ult.has(w) ? -Math.min(ult.get(w), n) / 400 : -1) + (esSigla(w) ? 2 : 0), rnd); if (!r) continue;
    // máx. MAXC palabras en común con cualquier día anterior
    const comun = new Map(); for (const w of r.words) for (const d of diasDe.get(w) || []) comun.set(d, (comun.get(d) || 0) + 1);
    if ([...comun.values()].some(c => c > MAXC)) continue;
    res = {a, s: g.map((row, y) => row.map((b, x) => b ? '#' : r.L[y * SZ + x]).join('')).join(''), words: r.words};
  }
  anotar(n, res.words); plan.push(res.s); if (process.env.V) console.error(n, res.words.length, res.a, ((Date.now() - t0) / 1000).toFixed(1));
  cuantas[res.words.length] = (cuantas[res.words.length] || 0) + 1; tres.push(res.words.filter(w => w.length === 3).length);
}
// comprobación final, independiente
let peorGap = {}, peorC = 0;
for (const [w, ds] of diasDe) for (let i = 1; i < ds.length; i++) { const L = w.length === 3 ? 3 : 5; peorGap[L] = Math.min(peorGap[L] ?? 1e9, ds[i] - ds[i - 1]); }
const sets = plan.map(palabrasDe).map(ws => new Set(ws));
for (let i = 0; i < sets.length; i++) for (let j = 0; j < i; j++) { let c = 0; for (const w of sets[i]) if (sets[j].has(w)) c++; peorC = Math.max(peorC, c); }
fs.writeFileSync(path.join(__dirname, '..', 'crucigrama/grillas.js'),
  '// Generado por scripts/crucigrama_grillas.js: grilla de 11×11 de cada día (# = negro), desde el N.º ' + N0 + '.\n' +
  'const CRUCI_G={n0:' + N0 + ',d:[\n' + plan.map(s => "'" + s + "'").join(',\n') + ']};\n');
console.log('días', plan.length, 'hasta', fecha(N0 + plan.length - 1), 'palabras por día', cuantas, 'de 3 letras por día ~', (tres.reduce((a, b) => a + b, 0) / tres.length).toFixed(1));
console.log('menor distancia entre repeticiones (3 letras / 5+):', peorGap[3], '/', peorGap[5], ' máx. en común entre dos días:', peorC, ' días aflojados:', relaj.length ? [...new Set(relaj)].join(',') : 'ninguno', ' s', ((Date.now() - t0) / 1000).toFixed(0));
