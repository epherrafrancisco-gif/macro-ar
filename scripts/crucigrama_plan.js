// Arma crucigrama/plan.js: las palabras candidatas de cada día del crucigrama (pedido del dueño 02/11/2026).
// Reglas, comprobadas acá con el MISMO generador que usa la página (crucigrama.js):
//  - ninguna palabra se repite antes de GAP días;
//  - dos crucigramas cualesquiera (de todo el plan) comparten como mucho 3 palabras;
//  - cada día tiene al menos 13 palabras (casi siempre 14-15).
// Uso: node scripts/crucigrama_plan.js [días]   (por defecto 1100, unos 3 años desde el N.º 3 = 03/11/2026)
// Si se agregan palabras a palabras.js (siempre al final), volver a correrlo: los días ya pasados no se tocan si se pasa
// --desde=AAAA-MM-DD (por defecto se rehace todo desde mañana y se conserva lo anterior tal cual).
const fs = require('fs'), path = require('path');
const R = p => fs.readFileSync(path.join(__dirname, '..', p), 'utf8');
const src = R('crucigrama/crucigrama.js'), pal = R('crucigrama/palabras.js');
const DIAS = +(process.argv[2] || 1100), GAP = 14, MAXC = 3, K = 28;
const PALABRAS = new Function(pal.replace('const PALABRAS', 'var PALABRAS') + '; return PALABRAS;')();
const helpers = src.slice(src.indexOf('function semilla'), src.indexOf('// ---------- generador'));
const body = src.slice(src.indexOf('// ---------- generador'), src.indexOf('const HOR'));
const gen = new Function('HOY', 'PALABRAS', 'CRUCI_PLAN',
  'var N = Math.round((Date.parse(HOY) - Date.parse("2026-11-01")) / 864e5) + 1;' + helpers + body.replace('const W = P.ancho', 'var W = P.ancho') + '; return P.puestas.map(p => p.w);');
const { semilla, azar } = new Function(helpers + '; return {semilla, azar};')();
const idx = new Map(PALABRAS.map((e, i) => [e[0], i]));
const validos = PALABRAS.map((e, i) => i).filter(i => /^[A-ZÑ]{3,11}$/.test(PALABRAS[i][0]));
const fecha = n => new Date(Date.parse('2026-11-01') + (n - 1) * 864e5).toISOString().slice(0, 10);
// días ya jugados (N.º 1 y 2, del sistema anterior)
const VIEJAS = {1: ['DIVIDENDO','PLAZOFIJO','INCENTIVO','INVERSION','FLOTACION','FRIEDMAN','BIGMAC','TARIFA','ZLOTY','EURO','YUAN','TASA','BCRA','FED','MEP'], 2: ['REAL','SOJA','LECAP','BOLSA','FUTURO','RIESGO','DEFAULT','ARANCEL','CORRIDA','AUSTRAL','FLOTACION','SUPERAVIT','DEFLACION','AGUINALDO','MONOTRIBUTO']};
const dias = new Map(), usos = new Map(), plan = [];   // dias: palabra -> días en que salió
const anotar = (n, ws) => ws.forEach(w => { const i = idx.get(w); if (!dias.has(i)) dias.set(i, []); dias.get(i).push(n); usos.set(i, (usos.get(i) || 0) + 1); });
for (const d in VIEJAS) anotar(+d, VIEJAS[d]);
let viejo = null; try { viejo = new Function(R('crucigrama/plan.js').replace('const CRUCI_PLAN', 'var CRUCI_PLAN') + '; return CRUCI_PLAN;')(); } catch (e) {}
const desde = (process.argv.find(a => a.startsWith('--desde=')) || '').slice(8) || fecha(Math.round((Date.now() - 3 * 3600e3 - Date.parse('2026-11-01')) / 864e5) + 2);
const t0 = Date.now(); let min = 99; const hist = {};
for (let n = 3; n < 3 + DIAS; n++) {
  const HOY = fecha(n);
  let cand = null, ws = null;
  if (viejo && HOY < desde && viejo.d[n - viejo.n0]) {        // lo ya publicado no se cambia
    cand = viejo.d[n - viejo.n0].split('.').map(x => parseInt(x, 36));
    ws = gen(HOY, PALABRAS, {n0: n, d: [cand.map(i => i.toString(36)).join('.')]});
  }
  for (let a = 0; !ws; a++) {
    const r = azar(semilla('plan-' + n + '-' + a));
    const libres = validos.filter(i => { const ds = dias.get(i); return !ds || n - ds[ds.length - 1] >= GAP; })
      .map(i => [i, (usos.get(i) || 0) + r() * 2]).sort((x, y) => x[1] - y[1]).map(x => x[0]);
    const cuenta = new Map(); cand = [];
    for (const i of libres) {                                   // no sumar una palabra si con ella algún día pasaría de 3 en común
      const ds = dias.get(i) || []; if (ds.some(d => (cuenta.get(d) || 0) >= MAXC)) continue;
      cand.push(i); ds.forEach(d => cuenta.set(d, (cuenta.get(d) || 0) + 1)); if (cand.length >= K) break;
    }
    const w = gen(HOY, PALABRAS, {n0: n, d: [cand.map(i => i.toString(36)).join('.')]});
    if (w.length >= (a < 30 ? 14 : 13)) ws = w;
  }
  anotar(n, ws); plan.push(cand.map(i => i.toString(36)).join('.'));
  min = Math.min(min, ws.length); hist[ws.length] = (hist[ws.length] || 0) + 1;
}
fs.writeFileSync(path.join(__dirname, '..', 'crucigrama/plan.js'),
  '// Plan del crucigrama: palabras candidatas de cada día (índices en base 36 de PALABRAS). Lo arma scripts/crucigrama_plan.js; no editar a mano.\n' +
  'const CRUCI_PLAN = ' + JSON.stringify({n0: 3, d: plan}) + ';\n');
console.log('días', DIAS, 'hasta', fecha(2 + DIAS), 'palabras por día', hist, 'segundos', ((Date.now() - t0) / 1000).toFixed(0));
