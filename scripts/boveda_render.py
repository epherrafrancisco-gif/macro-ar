# Bóveda de un banco central, renderizada por código (modo legendario de Pulso Macro).
# No es una foto: pared de cajas de seguridad, puerta circular gigante abierta, pilas de lingotes con el anillo del logo,
# piso de piedra pulida con reflejos y haces de luz cálida desde arriba. Uso: python3 scripts/boveda_render.py carpeta_salida
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H = 2400, 1500
PISO = 1010                      # donde la pared toca el piso
random.seed(11); np.random.seed(11)

def mezcla(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))
def grad_v(w, h, c0, c1):
    t = np.linspace(0, 1, h)[:, None, None]
    return (np.array(c0, float) * (1 - t) + np.array(c1, float) * t) * np.ones((1, w, 1))

# ---------- pared del fondo: acero oscuro con luz cálida ----------
img = grad_v(W, H, (22, 17, 11), (10, 8, 6))
base = Image.fromarray(np.clip(img, 0, 255).astype('uint8'))
d = ImageDraw.Draw(base)

# cajas de seguridad (pared izquierda y centro), con bocallave y número
CX0, CX1, CY0, CY1 = 0, 1330, 70, PISO - 30
cw, ch = 74, 50
for j, y0 in enumerate(range(CY0, CY1 - ch, ch + 6)):
    for i, x0 in enumerate(range(CX0 - 20, CX1, cw + 6)):
        luz = 1 - min(1, abs((x0 + cw / 2) - 760) / 1200) * .55 - (j / 18) * .25
        c = tuple(int(v * luz) for v in (58, 48, 34))
        d.rectangle([x0, y0, x0 + cw, y0 + ch], fill=c)
        d.line([x0, y0, x0 + cw, y0], fill=tuple(int(v * luz) for v in (104, 86, 58)), width=2)
        d.line([x0, y0 + ch, x0 + cw, y0 + ch], fill=(8, 6, 4), width=2)
        kx, ky = x0 + cw - 16, y0 + ch / 2
        d.ellipse([kx - 5, ky - 5, kx + 5, ky + 5], fill=tuple(int(v * luz) for v in (150, 118, 62)))
        d.rectangle([kx - 1.4, ky, kx + 1.4, ky + 6], fill=(18, 14, 9))
        d.rectangle([x0 + 9, y0 + 10, x0 + 28, y0 + 16], fill=tuple(int(v * luz) for v in (120, 98, 60)))
# columna de acero que separa las cajas de la puerta
d.rectangle([1330, 0, 1400, PISO], fill=(30, 24, 16))
d.line([1332, 0, 1332, PISO], fill=(90, 72, 44), width=3)

# ---------- puerta: marco circular en la pared, interior iluminado de oro ----------
PX, PY, PR = 1820, 560, 390
glow = Image.new('RGB', (W, H))
gd = ImageDraw.Draw(glow)
for k in range(60, 0, -1):
    r = PR * k / 60
    gd.ellipse([PX - r, PY - r, PX + r, PY + r], fill=mezcla((255, 196, 90), (70, 44, 14), k / 60))
# adentro: lingotes lejanos en la sala de atrás
for est in range(4):                      # estantes de la sala de atrás, llenos de lingotes
    ye = PY - 170 + est * 118
    gd.rectangle([PX - PR, ye + 4, PX + PR, ye + 14], fill=(60, 40, 14))
    for capa in range(3):
        yb = ye - capa * 22
        for xb in range(PX - PR - 20 + (capa % 2) * 26, PX + PR, 54):
            t = .75 + .25 * (1 - abs(xb - PX) / PR)
            gd.polygon([(xb, yb), (xb + 50, yb), (xb + 44, yb - 14), (xb + 6, yb - 14)], fill=mezcla((90, 58, 16), (236, 178, 70), t))
            gd.polygon([(xb + 6, yb - 14), (xb + 44, yb - 14), (xb + 40, yb - 20), (xb + 10, yb - 20)], fill=mezcla((120, 84, 30), (255, 222, 140), t))
mask = Image.new('L', (W, H)); ImageDraw.Draw(mask).ellipse([PX - PR, PY - PR, PX + PR, PY + PR], fill=255)
base.paste(glow.filter(ImageFilter.GaussianBlur(2)), (0, 0), mask)
d = ImageDraw.Draw(base)
# marco grueso con anillos mecanizados
for k, (r, c) in enumerate([(PR + 70, (40, 32, 22)), (PR + 52, (96, 80, 56)), (PR + 40, (60, 50, 34)), (PR + 16, (128, 108, 74)), (PR + 4, (34, 27, 18))]):
    d.ellipse([PX - r, PY - r, PX + r, PY + r], outline=c, width=14 if k == 0 else 8)
for a in range(0, 360, 15):  # remaches del marco
    t = math.radians(a); rx, ry = PX + (PR + 60) * math.cos(t), PY + (PR + 60) * math.sin(t)
    d.ellipse([rx - 6, ry - 6, rx + 6, ry + 6], fill=(150, 126, 84)); d.ellipse([rx - 3, ry - 4, rx + 1, ry], fill=(220, 196, 140))

# ---------- la hoja de la puerta, abierta hacia nosotros (de costado: elipse angosta) ----------
DX, DY, DRX, DRY = 2210, 600, 170, 440
door = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(door)
# canto (espesor) de la puerta
for k in range(46):
    dd.ellipse([DX - DRX - k, DY - DRY, DX + DRX - k, DY + DRY], fill=mezcla((40, 34, 24), (112, 94, 64), k / 46) + (255,))
# cara de la puerta
for k in range(40, 0, -1):
    f = k / 40
    dd.ellipse([DX - DRX * f, DY - DRY * f, DX + DRX * f, DY + DRY * f], fill=mezcla((190, 166, 120), (70, 60, 44), f) + (255,))
for f, c in [(.92, (60, 50, 36)), (.78, (140, 120, 86)), (.62, (64, 54, 38)), (.3, (150, 130, 92))]:
    dd.ellipse([DX - DRX * f, DY - DRY * f, DX + DRX * f, DY + DRY * f], outline=c + (255,), width=6)
# volante central con rayos
for a in range(0, 360, 60):
    t = math.radians(a)
    dd.line([DX, DY, DX + DRX * .5 * math.cos(t), DY + DRY * .5 * math.sin(t)], fill=(214, 190, 140, 255), width=10)
    hx, hy = DX + DRX * .5 * math.cos(t), DY + DRY * .5 * math.sin(t)
    dd.ellipse([hx - 9, hy - 14, hx + 9, hy + 14], fill=(226, 204, 152, 255))
dd.ellipse([DX - 26, DY - 44, DX + 26, DY + 44], fill=(232, 210, 160, 255), outline=(90, 76, 52, 255), width=4)
# pasadores (cerrojos) que salen del canto de la puerta, del lado del marco
for a in range(110, 251, 14):
    t = math.radians(a)
    bx, by = DX - 46 + DRX * math.cos(t), DY + DRY * math.sin(t)
    dd.rounded_rectangle([bx - 74, by - 12, bx, by + 12], 10, fill=(176, 154, 110, 255))
    dd.line([bx - 74, by - 8, bx, by - 8], fill=(236, 220, 176, 255), width=3)
    dd.line([bx - 74, by + 9, bx, by + 9], fill=(70, 58, 40, 255), width=3)
# bisagras grandes contra la pared
for hy in (DY - 300, DY + 300):
    dd.rounded_rectangle([DX + DRX - 30, hy - 46, DX + DRX + 90, hy + 46], 12, fill=(64, 54, 38, 255), outline=(138, 118, 84, 255), width=4)
base.paste(door, (0, 0), door)
d = ImageDraw.Draw(base)

# ---------- piso: piedra pulida en perspectiva ----------
fl = grad_v(W, H - PISO, (34, 26, 16), (14, 11, 8))
base.paste(Image.fromarray(np.clip(fl, 0, 255).astype('uint8')), (0, PISO))
d = ImageDraw.Draw(base)
VX = 1180  # punto de fuga
for x in range(-3000, 5400, 260):
    d.line([(VX + (x - VX) * .18, PISO), (x, H)], fill=(44, 34, 22), width=2)
y, k = PISO + 8, 10
while y < H:
    d.line([(0, y), (W, y)], fill=(42, 32, 20), width=2); k *= 1.32; y += k
# reflejo de la puerta iluminada en el piso
ref = base.crop((0, PISO - 520, W, PISO)).transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(10))
refm = Image.fromarray((np.linspace(110, 0, 520)[:, None] * np.ones((1, W))).astype('uint8'))
base.paste(ref, (0, PISO), refm)
d = ImageDraw.Draw(base)

# ---------- pilas de lingotes en primer plano ----------
def lingote(dr, x, y, s, tono=1.0):
    w, h, p = 150 * s, 40 * s, 30 * s       # largo, alto, profundidad (hacia atrás)
    oro = lambda c: tuple(min(255, int(v * tono)) for v in c)
    top = [(x + p * .5, y - h), (x + w - p * .5, y - h), (x + w - p * .9, y - h - p * .55), (x + p * .9, y - h - p * .55)]
    frente = [(x, y), (x + w, y), (x + w - p * .5, y - h), (x + p * .5, y - h)]
    dr.polygon(frente, fill=oro((196, 140, 40)))
    dr.polygon(top, fill=oro((246, 200, 96)))
    dr.line([top[0], top[1]], fill=oro((255, 240, 180)), width=max(1, int(3 * s)))
    dr.line([(x + 4 * s, y - 2 * s), (x + w - 4 * s, y - 2 * s)], fill=oro((120, 80, 18)), width=max(1, int(3 * s)))
    # el anillo del logo grabado en la cara de arriba
    cx, cy, r = x + w / 2, y - h - p * .28, 9 * s
    dr.ellipse([cx - r * 1.6, cy - r * .55, cx + r * 1.6, cy + r * .55], outline=oro((170, 118, 30)), width=max(1, int(2.4 * s)))
def pila(dr, x0, y0, s, filas, tono=1.0):
    w, h = 150 * s, 40 * s
    for f in range(filas):
        n = filas - f
        for i in range(n):
            lingote(dr, x0 + i * (w + 1 * s) + f * (w + 1 * s) / 2, y0 - f * (h + 30 * s * .42), s, tono * (0.86 + 0.14 * f / max(1, filas - 1)))
gold = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gdr = ImageDraw.Draw(gold)
pila(gdr, 980, PISO + 40, .78, 4, .8)
pila(gdr, 240, PISO + 230, 1.05, 4, .95)
pila(gdr, 1300, PISO + 300, 1.25, 3, 1.0)
pila(gdr, 1960, PISO + 250, .95, 3, .9)
sombra = Image.new('L', (W, H)); sd = ImageDraw.Draw(sombra)
for (x, y, w) in [(980, PISO + 44, 520), (240, PISO + 236, 700), (1300, PISO + 306, 610), (1960, PISO + 256, 470)]:
    sd.ellipse([x - 40, y - 20, x + w + 40, y + 34], fill=170)
base.paste((0, 0, 0), (0, 0), sombra.filter(ImageFilter.GaussianBlur(20)))
base.paste(gold, (0, 0), gold)

# ---------- haces de luz desde arriba (aditivos) y brillo ----------
luz = Image.new('RGB', (W, H)); ld = ImageDraw.Draw(luz)
for (xt, ancho, inc, a) in [(520, 140, 260, 46), (1040, 190, 300, 56), (1600, 120, 220, 34)]:
    ld.polygon([(xt, -40), (xt + ancho, -40), (xt + ancho + inc + ancho * 1.6, H), (xt + inc - ancho * .4, H)], fill=(a, int(a * .78), int(a * .42)))
luz = luz.filter(ImageFilter.GaussianBlur(46))
base = ImageChops.add(base, luz)
arr = np.asarray(base, float)
br = np.clip(arr - 170, 0, 255)
bloom = np.asarray(Image.fromarray(br.astype('uint8')).filter(ImageFilter.GaussianBlur(26)), float)
arr = arr + bloom * .9
# polvo en suspensión en los haces
pol = np.zeros((H, W)); n = 2600
xs, ys = np.random.randint(0, W, n), np.random.randint(0, H, n)
pol[ys, xs] = np.random.rand(n) * 255
pol = np.asarray(Image.fromarray(pol.astype('uint8')).filter(ImageFilter.GaussianBlur(1.1)), float)
lm = np.asarray(luz.convert('L'), float) / 60
arr += (pol * lm)[:, :, None] * np.array([1, .85, .55]) * 1.4
# viñeta y grano
yy, xx = np.mgrid[0:H, 0:W]
v = 1 - .55 * np.clip(((xx - W * .55) / (W * .62)) ** 2 + ((yy - H * .48) / (H * .7)) ** 2, 0, 1)
arr *= v[:, :, None]
arr += np.random.normal(0, 4.5, (H, W, 1))
out = Image.fromarray(np.clip(arr, 0, 255).astype('uint8'))

out.save(f'{OUT}/boveda-2400.jpg', quality=84, optimize=True, progressive=True)
out.save(f'{OUT}/boveda-2400.webp', quality=80, method=6)
chico = out.crop((int(W * .34), 0, int(W * .34) + 1500 * 900 // 1500 * 1, H)) if False else out
cel = out.crop((W - 1200 - 260, 0, W - 260, H)).resize((960, 1200), Image.LANCZOS)   # encuadre del celular: la puerta y el oro
cel.save(f'{OUT}/boveda-1200.jpg', quality=82, optimize=True, progressive=True)
cel.save(f'{OUT}/boveda-1200.webp', quality=78, method=6)
print('listo')
