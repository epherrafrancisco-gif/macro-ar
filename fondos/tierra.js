// Modo Órbita de Pulso Macro: la Tierra vista desde la órbita sobre Argentina, dibujada en vivo con WebGL 2 y girando.
// Un solo shader: rayo por píxel contra la esfera; texturas reales (Solar System Scope, CC BY 4.0, basadas en la NASA: día y
// luces de noche; océanos y nubes de la NASA), reflejo del sol en el mar, nubes que se mueven, atmósfera y estrellas.
// Corre solo con html[data-tema="orbita"] y la pestaña visible; si no hay WebGL 2, queda la imagen fija de fondo.
(function () {
  'use strict';
  const RAIZ = document.documentElement, CAPA = document.getElementById('orFx');
  if (!CAPA || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const R = 6.371;
  const sph = (lat, lon, r) => { const a = lat * Math.PI / 180, o = lon * Math.PI / 180; return [r * Math.cos(a) * Math.cos(o), r * Math.cos(a) * Math.sin(o), r * Math.sin(a)]; };
  const sub = (a, b) => a.map((v, i) => v - b[i]), nor = a => { const l = Math.hypot(...a); return a.map(v => v / l); };
  const cruz = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  // la misma toma que el render de Blender (scripts/espacio_blender.py)
  const CAM = sph(-40, -38, R + 1.7), MIRA = sph(-31, -64, R), SOL = nor(sph(-17, -122, 1));
  const F = nor(sub(MIRA, CAM)), DER = nor(cruz(F, nor(CAM))), ARR = cruz(DER, F);
  const GIRO = 360 / 900;            // grados por segundo: una vuelta cada 15 minutos (se ve girar sin marear)

  const VS = `#version 300 es
in vec2 p; void main(){ gl_Position = vec4(p, 0., 1.); }`;
  const FS = `#version 300 es
precision highp float;
uniform vec2 uRes; uniform vec3 uCam, uF, uR, uU, uSol; uniform float uTan, uShift, uRot, uT;
uniform sampler2D uDia, uNoche, uAux;
out vec4 o;
const float R = ${R.toFixed(3)}, PI = 3.14159265;
vec3 lin(vec3 c){ return pow(c, vec3(2.2)); }
float h3(vec3 p){ p = fract(p * .3183099 + .1); p *= 17.; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float ruido(vec3 x){ vec3 i = floor(x), f = fract(x); f = f * f * (3. - 2. * f);
  return mix(mix(mix(h3(i), h3(i + vec3(1,0,0)), f.x), mix(h3(i + vec3(0,1,0)), h3(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(h3(i + vec3(0,0,1)), h3(i + vec3(1,0,1)), f.x), mix(h3(i + vec3(0,1,1)), h3(i + vec3(1,1,1)), f.x), f.y), f.z); }
float fbm(vec3 p){ float s = 0., a = .5; for (int i = 0; i < 6; i++){ s += a * ruido(p); p = p * 2.03 + 3.1; a *= .5; } return s; }
vec3 aces(vec3 x){ return clamp((x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14), 0., 1.); }
// muestra equirectangular sin costura en el antimeridiano (derivadas con la u corrida)
vec4 eq(sampler2D t, vec2 uv){ vec2 uv2 = vec2(fract(uv.x + .5), uv.y);
  vec2 dx = dFdx(uv), dy = dFdy(uv), dx2 = dFdx(uv2), dy2 = dFdy(uv2);
  if (dot(dx2, dx2) < dot(dx, dx)) { dx = dx2; } if (dot(dy2, dy2) < dot(dy, dy)) { dy = dy2; }
  return textureGrad(t, uv, dx, dy); }
void main(){
  vec2 q = (gl_FragCoord.xy - .5 * uRes) / (.5 * max(uRes.x, uRes.y));
  vec3 d = normalize(uF + uR * q.x * uTan + uU * (q.y + uShift) * uTan);
  float b = dot(uCam, d), c = dot(uCam, uCam) - R * R, disc = b * b - c;
  // atmósfera: cuánto se acerca el rayo a la superficie
  float tc = max(-b, 0.); vec3 pc = uCam + d * tc; float alto = length(pc) - R;
  vec3 col = vec3(0.);
  float luzLimbo = dot(normalize(pc), uSol);
  vec3 atmCol = mix(vec3(1., .38, .12), vec3(.32, .58, 1.), smoothstep(-.05, .35, luzLimbo)) * smoothstep(-.32, .08, luzLimbo);
  if (disc > 0. && -b - sqrt(disc) > 0.) {
    vec3 p = uCam + d * (-b - sqrt(disc)), n = normalize(p);
    // coordenadas de la Tierra que gira (el sol queda quieto: el día y la noche avanzan sobre el planeta)
    float cr = cos(uRot), sr = sin(uRot); vec3 l = vec3(cr * n.x + sr * n.y, -sr * n.x + cr * n.y, n.z);
    vec2 uv = vec2(atan(l.y, l.x) / (2. * PI) + .5, asin(clamp(l.z, -1., 1.)) / PI + .5);
    vec3 dia = lin(eq(uDia, uv).rgb), noche = lin(eq(uNoche, uv).rgb); vec4 aux = eq(uAux, uv);
    float ndl = dot(n, uSol), luz = smoothstep(-.06, .22, ndl) * max(ndl + .06, 0.) / 1.06;
    // nubes: dónde hay sistemas de nubes (NASA) + detalle que se mueve despacio con el viento
    // nubes reales (mapa de nubes de 8K) con un poco de relieve fino para que no se vean planas de cerca
    float fd = fbm(l * 60. + vec3(uT * .002, 0., 0.));
    float nub = smoothstep(.08, .82, aux.g * (.82 + fd * .36)) * .97;
    float oc = smoothstep(.35, .75, aux.r);
    vec3 suelo = dia * (luz * 3.4 + .012);
    vec3 h = normalize(uSol - d);
    float brillo = (pow(max(dot(n, h), 0.), 900.) * .8 * (.35 + fbm(l * 220.) * 1.1) + pow(max(dot(n, h), 0.), 220.) * .025) * oc * smoothstep(0., .15, ndl);
    suelo += vec3(1., .86, .66) * brillo;
    suelo += noche * vec3(1., .78, .5) * 2.4 * (1. - smoothstep(-.12, .05, ndl)) * (1. - nub * .75);
    vec3 nube = vec3(.93, .95, 1.) * (luz * 2.5 + .01) + vec3(1., .5, .25) * smoothstep(-.1, .05, ndl) * (1. - smoothstep(.05, .2, ndl)) * .35;
    col = mix(suelo, nube, nub);
    // bruma azul hacia el borde (se mira de costado a través de más aire)
    float fres = pow(1. - max(dot(n, -d), 0.), 5.);
    col = mix(col, atmCol * 1.2, clamp(fres * .7 + .015, 0., 1.) * smoothstep(-.3, .1, ndl));
  } else {
    // estrellas
    vec3 cel = floor(d * 900.);
    float s = h3(cel), e = step(.9988, s) * (s - .9988) / .0012;
    col = vec3(e * e) * mix(vec3(1., .85, .7), vec3(.75, .85, 1.), h3(cel + 7.)) * 1.4;
  }
  // el halo del horizonte, por encima y sobre el borde
  float halo = exp(-max(alto, 0.) / .045) * smoothstep(-.05, .0, alto + .05);
  col += atmCol * halo * 1.35 * (disc > 0. ? .35 : 1.);
  col = aces(col * 1.15);
  o = vec4(pow(col, vec3(1. / 2.2)), 1.);
}`;

  let gl = null, cv = null, prog = null, U = {}, listo = false, corriendo = false, t0 = 0, ult = 0, rot0 = 0;
  function sh(tipo, src) { const s = gl.createShader(tipo); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
  function tex(unidad, url) {
    return new Promise((ok, mal) => { const im = new Image(); im.decoding = 'async';
      im.onload = () => { (im.decode ? im.decode().catch(() => {}) : Promise.resolve()).then(() => { const t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unidad); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im); gl.generateMipmap(gl.TEXTURE_2D);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        const an = gl.getExtension('EXT_texture_filter_anisotropic'); if (an) gl.texParameterf(gl.TEXTURE_2D, an.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, gl.getParameter(an.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
        ok(); }); };
      im.onerror = mal; im.src = url; });
  }
  // Foto del último cuadro y punto del giro, por pestaña: al volver a la página se muestra al instante y la animación sigue
  // desde ahí. Sin foto, la Tierra aparece desde el negro (la imagen fija de respaldo tiene otro encuadre y se veía "saltar").
  const CLAVE = 'pm-tierra';
  function tapar() {
    const tie = CAPA.querySelector('.tie'); if (!tie) return;
    let f = null; try { f = JSON.parse(sessionStorage.getItem(CLAVE) || 'null'); } catch (e) {}
    if (f && f.img && Math.abs(f.w / f.h - innerWidth / innerHeight) < .1) { tie.style.background = `#020306 url(${f.img}) 0 0/100% 100% no-repeat`; rot0 = f.rot || 0; }
    else { tie.style.background = '#020306'; if (f) rot0 = f.rot || 0; }
  }
  function guardar() {
    if (!listo || !cv || RAIZ.dataset.tema !== 'orbita') return;
    try {
      const rot = corriendo ? rot0 + (performance.now() - t0) / 1000 * GIRO : rot0;
      gl.uniform1f(U.uRot, rot * Math.PI / 180); gl.drawArrays(gl.TRIANGLES, 0, 3);   // el búfer se borra tras mostrarse: redibujar antes de copiar
      sessionStorage.setItem(CLAVE, JSON.stringify({rot: rot % 360, w: innerWidth, h: innerHeight, img: cv.toDataURL('image/jpeg', .72)}));
    } catch (e) { try { sessionStorage.removeItem(CLAVE); } catch (e2) {} }
  }
  addEventListener('pagehide', guardar);
  async function iniciar() {
    if (gl) return;
    cv = document.createElement('canvas'); cv.className = 'tierra'; cv.setAttribute('aria-hidden', 'true');
    gl = cv.getContext('webgl2', {antialias: false, alpha: false, powerPreference: 'low-power'});
    if (!gl) return;
    const tie = CAPA.querySelector('.tie'), soltar = () => { if (tie) tie.style.background = ''; };   // sin WebGL: vuelve la imagen fija
    tapar();
    try {
      prog = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    } catch (e) { gl = null; soltar(); return; }
    gl.useProgram(prog);
    const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    for (const n of ['uRes', 'uCam', 'uF', 'uR', 'uU', 'uSol', 'uTan', 'uShift', 'uRot', 'uT', 'uDia', 'uNoche', 'uAux']) U[n] = gl.getUniformLocation(prog, n);
    gl.uniform3fv(U.uCam, CAM); gl.uniform3fv(U.uF, F); gl.uniform3fv(U.uR, DER); gl.uniform3fv(U.uU, ARR); gl.uniform3fv(U.uSol, SOL);
    gl.uniform1i(U.uDia, 0); gl.uniform1i(U.uNoche, 1); gl.uniform1i(U.uAux, 2);
    const grande = Math.max(screen.width, screen.height) * (devicePixelRatio || 1) > 1600 ? '4096' : '2048';
    try { await Promise.all([tex(0, `/fondos/tierra/dia-${grande}.webp`), tex(1, `/fondos/tierra/noche-${grande}.webp`), tex(2, `/fondos/tierra/aux-${grande}.webp`)]); }
    catch (e) { gl = null; soltar(); return; }
    CAPA.insertBefore(cv, CAPA.firstChild.nextSibling);
    listo = true; t0 = performance.now(); arrancar();
  }
  function medir() {
    const esc = Math.min(devicePixelRatio || 1, innerWidth < 700 ? 1.5 : 1.25);
    const w = Math.round(innerWidth * esc), h = Math.round(innerHeight * esc);
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; gl.viewport(0, 0, w, h); }
    // en la compu el campo de 62° va en el ancho; en el celular (vertical), el horizonte más abajo y más cerca
    const vertical = h > w;
    gl.uniform2f(U.uRes, w, h); gl.uniform1f(U.uTan, vertical ? .5 : .6); gl.uniform1f(U.uShift, vertical ? .5 : .32);
  }
  function cuadro(ahora) {
    if (!corriendo) return;
    if (ahora - ult > 1000 / 30) {          // 30 cuadros por segundo alcanzan: gira lento
      ult = ahora; medir();
      const seg = (ahora - t0) / 1000;
      gl.uniform1f(U.uRot, (rot0 + seg * GIRO) * Math.PI / 180); gl.uniform1f(U.uT, seg);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      if (!cv.classList.contains('on')) cv.classList.add('on');
    }
    requestAnimationFrame(cuadro);
  }
  function arrancar() { if (!listo || corriendo) return; corriendo = true; ult = 0; t0 = performance.now(); requestAnimationFrame(cuadro); }
  function parar() { if (corriendo) rot0 += (performance.now() - t0) / 1000 * GIRO; corriendo = false; }
  function revisar() {
    const on = RAIZ.dataset.tema === 'orbita' && !document.hidden;
    if (on) { if (!gl) iniciar(); else arrancar(); } else parar();
  }
  new MutationObserver(revisar).observe(RAIZ, {attributes: true, attributeFilter: ['data-tema']});
  document.addEventListener('visibilitychange', () => { if (corriendo || RAIZ.dataset.tema === 'orbita') { if (document.hidden) { guardar(); parar(); } else revisar(); } });
  revisar();
})();
