# Ciudad cyberpunk vista desde lo alto, renderizada por código (modo Ciudad de Pulso Macro).
# No es una foto: capas de edificios en perspectiva con niebla, ventanas, terrazas, calles con luces y carteles de neón
# (varios dicen 宏观脉搏, "Pulso Macro" en chino). Uso: python3 scripts/ciudad_render.py carpeta_salida
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H = 2400, 1500
HOR = int(H * 0.40)          # horizonte (la cámara está alta: se ve la ciudad hacia abajo)
random.seed(7); np.random.seed(7)
FUENTE = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
try:
    ImageFont.truetype(FUENTE, 20, index=2)
except Exception:
    import glob
    FUENTE = (glob.glob('/usr/share/fonts/**/NotoSansCJK*Bold*', recursive=True) + glob.glob('/usr/share/fonts/**/NotoSansCJK*', recursive=True))[0]
def fuente(t):
    for idx in (2, 0, 1, 3):
        try: return ImageFont.truetype(FUENTE, t, index=idx)
        except Exception: pass
    return ImageFont.load_default()

def mezcla(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))

# ---------- cielo: contaminación lumínica violeta/naranja en el horizonte, nubes bajas ----------
y = np.linspace(0, 1, H)[:, None]
cielo_top = np.array([4, 4, 14], float); cielo_mid = np.array([30, 12, 48], float); cielo_hor = np.array([120, 40, 92], float)
t = np.clip(y / (HOR / H), 0, 1)
img = np.where(t < .7, cielo_top + (cielo_mid - cielo_top) * (t / .7), cielo_mid + (cielo_hor - cielo_mid) * ((t - .7) / .3))
img = np.broadcast_to(img[:, None, :], (H, W, 3)).astype(float).copy()
# nubes: ruido suavizado, más denso cerca del horizonte
ruido = np.random.rand(H // 8, W // 8)
for s in (1,):
    pass
nub = Image.fromarray((ruido * 255).astype('uint8')).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(28))
nub = np.asarray(nub, float) / 255
nub = np.clip((nub - .45) * 2.2, 0, 1) * np.clip(1 - np.abs(y - HOR / H * .8) * 2.4, 0, 1)
img += nub[:, :, None] * np.array([70, 30, 70])
base = Image.fromarray(np.clip(img, 0, 255).astype('uint8'))

glow = Image.new('RGB', (W, H), (0, 0, 0))     # todo lo que brilla, para el bloom final
gd = ImageDraw.Draw(glow)

PAL_VENT = [(255, 214, 150), (255, 236, 196), (170, 230, 255), (255, 170, 210), (200, 210, 255)]
NEON = [(0, 240, 255), (255, 43, 214), (252, 238, 10), (57, 255, 158), (164, 107, 255), (255, 90, 60)]
PALABRAS = ['宏观脉搏', '宏观脉搏', '金融', '银行', '证券', '汇率', '股市', '夜市', '火锅', '面馆', '外汇', '贸易', '酒店', '茶馆', '数据', '科技']

def edificio(d, gdr, x, top, w, piso, prof, col, niebla, dens, cerca):
    """Edificio en perspectiva desde arriba: cara frontal, cara lateral y terraza."""
    lado = int(w * random.uniform(.18, .32)) if cerca > .3 else int(w * .15)
    dir_ = 1 if x + w / 2 < W / 2 else -1        # lado visible según de qué lado del centro está
    terraza = int(max(2, w * .22 * cerca))
    col = col[:3]
    f = mezcla(col, niebla, prof)
    s = mezcla(tuple(int(c * .62) for c in col), niebla, prof)
    r = mezcla(tuple(min(255, int(c * 1.25)) for c in col), niebla, prof)
    # cara lateral
    if dir_ > 0: lp = [(x + w, top), (x + w + lado, top - terraza), (x + w + lado, piso), (x + w, piso)]
    else: lp = [(x, top), (x - lado, top - terraza), (x - lado, piso), (x, piso)]
    d.polygon(lp, fill=s)
    # cara frontal con degradé vertical (más clara arriba por la luz del cielo)
    d.rectangle([x, top, x + w, piso], fill=f)
    for k in range(0, int(piso - top), 6):
        a = .10 * (1 - k / max(1, piso - top))
        d.line([(x, top + k), (x + w, top + k)], fill=mezcla(f, (90, 70, 130), a))
    # terraza (se ve porque la cámara está arriba)
    if dir_ > 0: tp = [(x, top), (x + lado, top - terraza), (x + w + lado, top - terraza), (x + w, top)]
    else: tp = [(x - lado, top - terraza), (x, top), (x + w, top), (x + w - lado, top - terraza)]
    d.polygon(tp, fill=r)
    if cerca > .5 and random.random() < .5:   # equipos en la terraza
        ex = x + random.randint(4, max(5, w - 20)); d.rectangle([ex, top - terraza + 2, ex + w * .18, top - 2], fill=mezcla(r, (0, 0, 0), .35))
    # ventanas
    vw = max(1, int(1 + 4 * cerca)); vh = max(1, int(1 + 4 * cerca)); sx = vw + max(1, int(1 + 2.5 * cerca)); sy = vh + max(1, int(2 + 3 * cerca))
    pal = random.choice(PAL_VENT); apagado = random.random() < .15
    for wy in range(int(top) + 4, min(int(piso), H) - 2, sy):
        fila_on = random.random() < .85
        for wx in range(int(x) + 3, int(x + w) - vw - 1, sx):
            if fila_on and random.random() < dens and not apagado:
                i = random.uniform(.35, 1.0)
                c = mezcla(mezcla(f, pal, i), niebla, prof * .7)
                d.rectangle([wx, wy, wx + vw - 1, wy + vh - 1], fill=c)
                if i > .8 and cerca > .2: gdr.rectangle([wx, wy, wx + vw - 1, wy + vh - 1], fill=mezcla(pal, (0, 0, 0), .55 + prof * .4))
    # franja de neón en el borde
    if random.random() < .16 * (cerca + .2):
        nc = random.choice(NEON)
        if random.random() < .5:
            yb = top + (piso - top) * .35
            d.line([(x, top), (x, yb)], fill=mezcla(nc, niebla, prof * .6), width=max(1, int(2 * cerca + 1)))
            gdr.line([(x, top), (x, yb)], fill=mezcla(nc, (0, 0, 0), prof * .5), width=max(2, int(4 * cerca + 2)))
        else:
            yy = top + random.randint(8, 40)
            d.line([(x, yy), (x + w, yy)], fill=mezcla(nc, niebla, prof * .6), width=max(1, int(2 * cerca + 1)))
            gdr.line([(x, yy), (x + w, yy)], fill=mezcla(nc, (0, 0, 0), prof * .5), width=max(2, int(4 * cerca + 2)))
    # luz roja de aviso en la punta de los altos
    if cerca > .12 and piso - top > 200 and random.random() < .35:
        rr = 1.5 + 2 * cerca
        gdr.ellipse([x + w / 2 - rr, top - terraza - 2 * rr, x + w / 2 + rr, top - terraza], fill=mezcla((255, 40, 60), (0, 0, 0), prof))

CARTELES = []
MAX_CARTELES = 22
def cartel(x, y, alto, col, prof, pal=None, vertical=True):
    pal = pal or random.choice(PALABRAS)
    if vertical:
        paso = max(14, alto // len(pal)); ancho = int(paso * 1.25)
        caja = [x, y, x + ancho, y + paso * len(pal) + paso * .4]
    else:
        paso = max(14, alto); ancho = int(paso * len(pal) * 1.08 + paso * .6)
        caja = [x, y, x + ancho, y + paso * 1.45]
    for c in CARTELES:
        if not (caja[2] + 6 < c[0] or c[2] + 6 < caja[0] or caja[3] + 6 < c[1] or c[3] + 6 < caja[1]): return
    if caja[2] > W - 4 or caja[0] < 4 or len(CARTELES) >= MAX_CARTELES: return
    CARTELES.append(caja + [pal, col, prof, vertical, paso])

# ---------- capas, de la más lejana a la más cercana ----------
lienzo = base.copy()
niebla_lejos = (118, 52, 110); niebla_cerca = (40, 18, 58)
CAPAS = 12
for L in range(CAPAS):
    k = L / (CAPAS - 1)                         # 0 = lejos, 1 = cerca
    cerca = k ** 1.7
    prof = (1 - k) ** 1.25 * .86
    niebla = mezcla(niebla_lejos, niebla_cerca, k)
    piso_capa = int(HOR + (H - HOR) * (k ** 1.2) * 1.15) + 30
    escala = .14 + 2.0 * cerca
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    x = random.randint(-120, 0)
    while x < W + 60:
        w = int(random.uniform(24, 66) * escala)
        h = int(random.uniform(80, 360) * escala * (1.6 if random.random() < .1 else 1))
        if 6 <= L <= 8 and random.random() < .05: h = int(h * 2.0)    # algún rascacielos muy alto
        top = piso_capa - h
        col = random.choice([(22, 24, 44), (28, 26, 52), (18, 22, 40), (34, 30, 58), (24, 30, 50), (30, 34, 56)])
        edificio(d, gd, x, top, w, H + 10, prof, col + (255,), niebla, random.uniform(.22, .55), cerca)
        if L >= 6 and random.random() < .22 and h > 150 * escala:
            alto = int(random.uniform(50, 100) * (.45 + cerca))
            cartel(int(x + random.uniform(.05, .55) * w), int(top + random.uniform(.10, .40) * h), alto,
                   random.choice(NEON), prof, vertical=random.random() < .8)
        x += w + int(random.uniform(-4, 20) * escala)
    # calles: tramos cortos de luces de autos en los huecos, a la distancia de esa capa
    if 3 <= L <= 10:
        yy = piso_capa - int(4 * escala)
        for _ in range(int(14 * (1 + k))):
            x0 = random.randint(0, W); ln = random.randint(14, 60) * (1 + 2 * k)
            c2 = random.choice([(255, 210, 140), (255, 70, 60), (255, 240, 220)])
            gd.line([(x0, yy + random.randint(-2, 2)), (x0 + ln, yy + random.randint(-2, 2))], fill=mezcla(c2, (0, 0, 0), .35 + prof * .6), width=max(1, int(2 * k)))
    if L < 6: capa = capa.filter(ImageFilter.GaussianBlur(1.1 - L * .17))    # lo lejano, apenas fuera de foco
    lienzo = Image.alpha_composite(lienzo.convert('RGBA'), capa).convert('RGB')
    # neblina en la base de la capa (separa una distancia de la siguiente)
    capa_niebla = Image.new('RGB', (W, H), niebla)
    m = Image.new('L', (W, H), 0); md = ImageDraw.Draw(m)
    for yy in range(max(0, piso_capa - 300), min(H, piso_capa + 40)):
        a = max(0, 1 - abs(yy - (piso_capa - 30)) / 260) * (60 if k < .8 else 26)
        md.line([(0, yy), (W, yy)], fill=int(a))
    lienzo = Image.composite(capa_niebla, lienzo, m)

# ---------- carteles de neón ----------
cd = ImageDraw.Draw(lienzo)
for (x0, y0, x1, y1, pal, col, prof, vertical, paso) in CARTELES:
    fondo = mezcla((8, 4, 16), (60, 24, 70), prof)
    cd.rectangle([x0, y0, x1, y1], fill=fondo)
    borde = mezcla(col, (90, 50, 100), prof * .7)
    cd.rectangle([x0, y0, x1, y1], outline=borde, width=max(1, int(paso / 14)))
    gd.rectangle([x0, y0, x1, y1], outline=mezcla(col, (0, 0, 0), prof * .5), width=max(2, int(paso / 8)))
    fnt = fuente(int(paso * .86))
    texto_col = mezcla((255, 255, 255), col, .35)
    texto_col = mezcla(texto_col, (120, 70, 120), prof * .6)
    if vertical:
        for i, ch in enumerate(pal):
            cx = (x0 + x1) / 2; cy = y0 + paso * .2 + i * paso + paso / 2
            cd.text((cx, cy), ch, font=fnt, fill=texto_col, anchor='mm')
            gd.text((cx, cy), ch, font=fnt, fill=mezcla(col, (0, 0, 0), prof * .4), anchor='mm')
    else:
        cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
        cd.text((cx, cy), pal, font=fnt, fill=texto_col, anchor='mm')
        gd.text((cx, cy), pal, font=fnt, fill=mezcla(col, (0, 0, 0), prof * .4), anchor='mm')

# ---------- un gran cartel "宏观脉搏" en la torre más cercana del centro, como protagonista ----------
fx, fy, paso = int(W * .66), int(H * .30), 74
torre = Image.new('RGBA', (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(torre)
tg = Image.new('RGB', (W, H), (0, 0, 0)); tgd = ImageDraw.Draw(tg)
random.seed(99)
edificio(td, tgd, fx - 70, fy - 120, 230, H + 10, .05, (26, 28, 52, 255), (40, 18, 58), .45, .9)
lienzo = Image.alpha_composite(lienzo.convert('RGBA'), torre).convert('RGB'); cd = ImageDraw.Draw(lienzo)
glow = ImageChops.lighter(glow, tg); gd = ImageDraw.Draw(glow)
fnt = fuente(int(paso * .86)); pal = '宏观脉搏'
cd.rectangle([fx - 10, fy - 10, fx + paso + 10, fy + paso * 4 + 10], fill=(8, 4, 18), outline=(255, 43, 214), width=4)
gd.rectangle([fx - 10, fy - 10, fx + paso + 10, fy + paso * 4 + 10], outline=(255, 43, 214), width=10)
for i, ch in enumerate(pal):
    cy = fy + i * paso + paso / 2
    cd.text((fx + paso / 2, cy), ch, font=fnt, fill=(255, 225, 250), anchor='mm')
    gd.text((fx + paso / 2, cy), ch, font=fnt, fill=(255, 43, 214), anchor='mm')

# ---------- bloom, grano y viñeta ----------
im = np.asarray(lienzo, float)
g = np.asarray(glow, float)
for r, peso in ((3, .9), (10, .7), (28, .55)):
    bl = np.asarray(glow.filter(ImageFilter.GaussianBlur(r)), float)
    im = 255 - (255 - im) * (255 - bl * peso) / 255     # "screen"
im = np.maximum(im, g * .9)
im += np.random.normal(0, 4.5, im.shape)                # grano de foto nocturna
yy, xx = np.mgrid[0:H, 0:W]
vin = 1 - .45 * (((xx - W / 2) / (W / 2)) ** 2 * .6 + ((yy - H * .55) / (H * .7)) ** 2)
im *= np.clip(vin, .45, 1)[:, :, None]
out = Image.fromarray(np.clip(im, 0, 255).astype('uint8'))
for ancho, nombre in ((2400, 'ciudad3-2400'), (1200, 'ciudad3-1200')):
    alto = int(H * ancho / W)
    o = out.resize((ancho, alto), Image.LANCZOS)
    o.save(f'{OUT}/{nombre}.webp', 'WEBP', quality=74, method=6)
    o.save(f'{OUT}/{nombre}.jpg', 'JPEG', quality=80, optimize=True, progressive=True)
print('listo', len(CARTELES), 'carteles')
