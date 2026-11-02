# Ciudad de neón tipo Chongqing para el modo Ciudad de Pulso Macro (fondos/ciudad2.svg).
# Uso: python3 ciudad2.py salida.svg [--quieta]   (--quieta = sin animaciones, para "reducir movimiento")
import random, sys
random.seed(11)
OUT = sys.argv[1]
QUIETA = '--quieta' in sys.argv
W, H, BASE = 1600, 900, 742          # BASE = orilla del río
NEON = ['#00f0ff', '#ff2bd6', '#fcee0a', '#39ff9e', '#a46bff', '#ff5a3c']
PAL = ['金融', '市场', '银行', '证券', '汇率', '股市', '经济', '黄金', '贸易', '投资', '夜市', '火锅', '重庆', '茶馆',
       '酒店', '咖啡', '科技', '数据', '脉搏', '宏观', '外汇', '期货', '面馆', '电器']
o = []
A = o.append

A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice">')
estilo = '''
.t{font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC","Noto Serif CJK SC","Source Han Sans SC",sans-serif;font-weight:700;text-anchor:middle}
'''
if not QUIETA:
    estilo += '''
.fk{animation:fk 11s infinite}.fk2{animation:fk 17s infinite 3s}.fk3{animation:fk 23s infinite 7s}
@keyframes fk{0%,90%,100%{opacity:1}91%{opacity:.25}92%{opacity:1}94%{opacity:.35}95%{opacity:1}}
.wa{animation:wa 29s steps(1) infinite}.wb{animation:wa 41s steps(1) infinite 9s}.wc{animation:wa 53s steps(1) infinite 21s}
@keyframes wa{0%,61%{opacity:.9}62%,100%{opacity:.08}}
.rf{animation:rf 7s ease-in-out infinite alternate}.rf2{animation:rf 9s ease-in-out infinite alternate-reverse}
@keyframes rf{from{transform:translateX(-6px);opacity:.35}to{transform:translateX(6px);opacity:.6}}
.cr{animation:cr 5s ease-in-out infinite alternate}@keyframes cr{from{opacity:.55}to{opacity:1}}
.ant{animation:ant 2.4s steps(1) infinite}@keyframes ant{0%,50%{opacity:1}51%,100%{opacity:.15}}
'''
A('<defs><style>' + estilo + '</style>')
A('''<linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#03030b"/><stop offset=".45" stop-color="#0f0826"/><stop offset=".72" stop-color="#2a0c3e"/><stop offset="1" stop-color="#4f1450"/></linearGradient>
<radialGradient id="hm"><stop offset="0" stop-color="#ff2bd6" stop-opacity=".28"/><stop offset="1" stop-color="#ff2bd6" stop-opacity="0"/></radialGradient>
<radialGradient id="hc"><stop offset="0" stop-color="#00f0ff" stop-opacity=".18"/><stop offset="1" stop-color="#00f0ff" stop-opacity="0"/></radialGradient>
<linearGradient id="niebla" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b44dff" stop-opacity="0"/><stop offset=".6" stop-color="#ff4fd8" stop-opacity=".16"/><stop offset="1" stop-color="#ff4fd8" stop-opacity=".3"/></linearGradient>
<linearGradient id="niebla2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7a5cff" stop-opacity="0"/><stop offset="1" stop-color="#7a5cff" stop-opacity=".22"/></linearGradient>
<linearGradient id="rio" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c0a33"/><stop offset="1" stop-color="#03040a"/></linearGradient>
<linearGradient id="vid" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#101a3a"/><stop offset=".5" stop-color="#1b2a55"/><stop offset="1" stop-color="#0c1430"/></linearGradient>
<filter id="gl" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="glw" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="5"/></filter>
</defs>''')
A(f'<rect width="{W}" height="{H}" fill="url(#cielo)"/>')
A('<ellipse cx="1150" cy="640" rx="820" ry="430" fill="url(#hm)"/><ellipse cx="280" cy="660" rx="620" ry="380" fill="url(#hc)"/>')
# estrellas tenues arriba (casi tapadas por la contaminación lumínica)
for _ in range(70):
    A(f'<circle cx="{random.randint(0,W)}" cy="{random.randint(10,260)}" r="{random.uniform(.4,1.1):.1f}" fill="#fff" opacity="{random.uniform(.15,.5):.2f}"/>')

def montana(base, amp, col, seed):
    random.seed(seed); pts = []; x = -40
    while x < W + 60:
        pts.append((x, base - amp * (0.55 + 0.45 * random.random()))); x += random.randint(70, 140)
    d = f'M-40 {BASE} ' + ' '.join(f'L{x} {y:.0f}' for x, y in pts) + f' L{W+60} {BASE} Z'
    A(f'<path d="{d}" fill="{col}"/>')

def ventanas(x, y, w, h, dens, col, anim=0.0, paso=(7, 9), tam=(3, 4)):
    c = []
    for wy in range(int(y) + 8, BASE - 6, paso[1]):
        for wx in range(int(x) + 4, int(x + w) - 4, paso[0]):
            if random.random() < dens:
                op = random.uniform(.3, .95)
                cls = ''
                if anim and random.random() < anim: cls = ' class="' + random.choice(['wa', 'wb', 'wc']) + '"'
                c.append(f'<rect x="{wx}" y="{wy}" width="{tam[0]}" height="{tam[1]}" fill="{col}" opacity="{op:.2f}"{cls}/>')
    A(''.join(c))

OCUP = []   # rectángulos ya usados por carteles
PEND = []   # carteles para dibujar al terminar la capa
def libre(x, y, w, h, m=6):
    for a, b, c2, d in OCUP:
        if x < a + c2 + m and a < x + w + m and y < b + d + m and b < y + h + m: return False
    return True
def cartel_chino(x, y, alto, col):
    """Cartel vertical de neón con 2 a 4 caracteres."""
    pal = random.choice(PAL) + (random.choice(PAL) if random.random() < .35 else '')
    pal = pal[:4]; n = len(pal); paso = max(18, min(26, alto // n)); w = paso + 8
    if not libre(x, y, w, n*paso+10) or x < 4 or x + w > W - 4: return
    OCUP.append((x, y, w, n*paso+10)); PEND.append(lambda: cartel_chino_dib(x, y, pal, n, paso, w, col))
def cartel_chino_dib(x, y, pal, n, paso, w, col):
    cls = random.choice(['fk', 'fk2', 'fk3', '', '', '']) if not QUIETA else ''
    g = f'<g class="{cls}" filter="url(#gl)">' if cls else '<g filter="url(#gl)">'
    g += f'<rect x="{x}" y="{y}" width="{w}" height="{n*paso+10}" rx="2" fill="#07030f" fill-opacity=".85" stroke="{col}" stroke-width="1.6"/>'
    for i, ch in enumerate(pal):
        g += f'<text class="t" x="{x+w/2:.1f}" y="{y+8+(i+1)*paso-paso*0.22:.1f}" font-size="{paso-5}" fill="{col}">{ch}</text>'
    A(g + '</g>')

def cartel_horizontal(x, y, col):
    pal = random.choice(PAL); fs = random.choice([13, 15, 17])
    w = fs * len(pal) + 12
    if not libre(x, y, w, fs + 8): return
    OCUP.append((x, y, w, fs + 8))
    cls = random.choice(['fk2', 'fk3', '']) if not QUIETA else ''
    A(f'<g class="{cls}" filter="url(#gl)"><rect x="{x}" y="{y}" width="{w}" height="{fs+8}" rx="2" fill="#07030f" fill-opacity=".8" stroke="{col}" stroke-width="1.3"/>'
      f'<text class="t" x="{x+w/2}" y="{y+fs+1}" font-size="{fs}" fill="{col}">{pal}</text></g>')

def techo(x, y, w, col, op):
    r = random.random()
    if r < .3:   # antena con luz roja
        A(f'<rect x="{x+w/2-1}" y="{y-38}" width="2" height="38" fill="{col}" opacity="{op}"/><circle class="{"" if QUIETA else "ant"}" cx="{x+w/2}" cy="{y-39}" r="2.2" fill="#ff3b5c" filter="url(#gl)"/>')
    elif r < .5:  # escalonado
        A(f'<rect x="{x+w*.15:.0f}" y="{y-16}" width="{w*.7:.0f}" height="16" fill="{col}" opacity="{op}"/><rect x="{x+w*.3:.0f}" y="{y-28}" width="{w*.4:.0f}" height="12" fill="{col}" opacity="{op}"/>')
    elif r < .62:  # techo inclinado
        A(f'<path d="M{x} {y} L{x+w} {y-22} L{x+w} {y} Z" fill="{col}" opacity="{op}"/>')

def capa(hmin, hmax, wmin, wmax, col, dens, op, p_neon, p_chino, wcol, anim, alto_extra=0.10):
    x = -30
    while x < W + 30:
        w = random.randint(wmin, wmax); h = random.randint(hmin, hmax)
        if random.random() < alto_extra: h = int(h * 1.5)
        y = BASE - h
        A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}" opacity="{op}"/>')
        techo(x, y, w, col, op)
        ventanas(x, y, w, h, dens, random.choice(wcol), anim)
        if random.random() < p_neon:   # borde o franja de neón
            nc = random.choice(NEON)
            if random.random() < .5:
                A(f'<line x1="{x+.5}" y1="{y}" x2="{x+.5}" y2="{BASE}" stroke="{nc}" stroke-width="1.4" filter="url(#gl)" opacity=".85"/>')
            else:
                A(f'<rect x="{x}" y="{y+random.randint(14,50)}" width="{w}" height="2" fill="{nc}" filter="url(#gl)" opacity=".85"/>')
        if random.random() < p_chino and h > 120:
            cartel_chino(x + w - random.randint(22, 34), y + random.randint(18, max(19, h // 3)), random.randint(70, 110), random.choice(NEON))
        x += w + random.randint(-8, 3)

def hito(x, w, h, col, corona):
    """Rascacielos icónico: cuerpo, corona iluminada y aguja."""
    y = BASE - h
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#vid)"/>')
    A(f'<rect x="{x+w*.12:.0f}" y="{y-40}" width="{w*.76:.0f}" height="40" fill="url(#vid)"/>')
    A(f'<rect x="{x+w*.3:.0f}" y="{y-70}" width="{w*.4:.0f}" height="30" fill="url(#vid)"/>')
    A(f'<rect x="{x+w/2-1.2:.1f}" y="{y-150}" width="2.4" height="80" fill="#9fb4ff"/>')
    cl = '' if QUIETA else ' class="cr"'
    A(f'<g{cl} filter="url(#gl)"><path d="M{x} {y} L{x+w*.12:.0f} {y} L{x+w*.12:.0f} {y-40} L{x+w*.3:.0f} {y-40} L{x+w*.3:.0f} {y-70} L{x+w*.7:.0f} {y-70} L{x+w*.7:.0f} {y-40} L{x+w*.88:.0f} {y-40} L{x+w*.88:.0f} {y} L{x+w} {y}" fill="none" stroke="{corona}" stroke-width="2"/>'
      f'<line x1="{x+w/2:.1f}" y1="{y-150}" x2="{x+w/2:.1f}" y2="{y-70}" stroke="{corona}" stroke-width="1.4"/></g>')
    A(f'<circle class="{"" if QUIETA else "ant"}" cx="{x+w/2:.1f}" cy="{y-152}" r="2.6" fill="#ff3b5c" filter="url(#gl)"/>')
    # fachada de vidrio con líneas de piso y luces
    for fy in range(int(y) + 10, BASE, 12):
        A(f'<line x1="{x+3}" y1="{fy}" x2="{x+w-3}" y2="{fy}" stroke="#8fb0ff" stroke-opacity=".10" stroke-width="1"/>')
    ventanas(x, y, w, h, .35, '#cfe3ff', 0.05, paso=(6, 12), tam=(3, 5))
    # franjas verticales de luz en la fachada
    A(f'<rect x="{x+w*.2:.0f}" y="{y}" width="2" height="{h}" fill="{corona}" opacity=".55" filter="url(#gl)"/><rect x="{x+w*.8:.0f}" y="{y}" width="2" height="{h}" fill="{corona}" opacity=".55" filter="url(#gl)"/>')

# montañas de fondo (Chongqing es una ciudad en las montañas)
montana(BASE - 250, 140, '#160b2c', 3)
montana(BASE - 170, 120, '#1a0d33', 5)
random.seed(21)
capa(250, 480, 18, 38, '#1d1440', .10, .95, .12, .05, ['#ffd38a', '#9ff4ff'], 0, .14)   # torres lejanas, finas
A(f'<rect y="{BASE-330}" width="{W}" height="330" fill="url(#niebla2)"/>')
random.seed(22)
# tres rascacielos icónicos
hito(300, 46, 560, '#00f0ff', '#00f0ff')
hito(1010, 54, 610, '#ff2bd6', '#ff2bd6')
hito(1380, 40, 500, '#fcee0a', '#fcee0a')
random.seed(23)
capa(170, 380, 30, 64, '#150d2e', .26, .97, .45, .28, ['#ffd38a', '#9ff4ff', '#ffb3f0', '#fff1c2'], .06)
A(f'<rect y="{BASE-160}" width="{W}" height="160" fill="url(#niebla)"/>')
random.seed(24)
capa(70, 230, 40, 92, '#0a0718', .30, 1, .7, .38, ['#ffd38a', '#9ff4ff', '#ffb3f0'], .08, .05)
# todos los carteles al final, así ningún edificio los corta
for f in PEND: f()
PEND.clear()
# puente atirantado sobre el río
py = BASE - 16
for px in (420, 1180):
    A(f'<rect x="{px-4}" y="{py-150}" width="8" height="166" fill="#0b0816"/><rect x="{px-4}" y="{py-150}" width="8" height="166" fill="none" stroke="#00f0ff" stroke-opacity=".5" stroke-width="1"/>')
    A(f'<circle class="{"" if QUIETA else "ant"}" cx="{px}" cy="{py-152}" r="2.4" fill="#ff3b5c" filter="url(#gl)"/>')
    for k in range(1, 9):
        for s in (-1, 1):
            A(f'<line x1="{px}" y1="{py-150+k*9}" x2="{px+s*k*40}" y2="{py}" stroke="#00f0ff" stroke-opacity=".38" stroke-width=".8"/>')
A(f'<rect x="-20" y="{py}" width="1640" height="5" fill="#0b0818"/><line x1="-20" y1="{py}" x2="1620" y2="{py}" stroke="#00f0ff" stroke-width="1.6" filter="url(#gl)" opacity=".9"/>')
for bx in range(0, W, 26):   # luces de autos sobre el puente
    A(f'<circle cx="{bx+random.randint(0,20)}" cy="{py+2.5}" r="1.1" fill="{random.choice(["#fff1c2","#ff3b3b"])}" opacity=".9"/>')
# carteles horizontales sueltos en la capa cercana
for _ in range(14):
    hx = random.randint(20, W - 120)
    if any(abs(hx + 30 - px) < 70 for px in (420, 1180)): continue
    cartel_horizontal(hx, random.randint(BASE - 200, BASE - 60), random.choice(NEON))
for _ in range(0):
    cartel_horizontal(random.randint(20, W - 120), random.randint(BASE - 200, BASE - 60), random.choice(NEON))
# río con reflejos
A(f'<rect y="{BASE}" width="{W}" height="{H-BASE}" fill="url(#rio)"/>')
for g in range(2):
    cls = '' if QUIETA else (' class="rf"' if g == 0 else ' class="rf2"')
    c = [f'<g{cls}>']
    for _ in range(170):
        x = random.randint(0, W); y = random.randint(BASE + 6, H - 8); w = random.randint(8, 46)
        c.append(f'<rect x="{x}" y="{y}" width="{w}" height="1.6" fill="{random.choice(NEON+["#ffd38a","#ffd38a"])}" opacity="{random.uniform(.25,.7):.2f}"/>')
    A(''.join(c) + '</g>')
# reflejo largo de los tres rascacielos
for x, col in ((323, '#00f0ff'), (1037, '#ff2bd6'), (1400, '#fcee0a')):
    A(f'<rect x="{x-3}" y="{BASE+4}" width="6" height="{H-BASE-20}" fill="{col}" opacity=".18" filter="url(#glw)"/>')
A('</svg>')
s = '\n'.join(o)
open(OUT, 'w').write(s)
print(OUT, len(s.encode()) // 1024, 'KB')
