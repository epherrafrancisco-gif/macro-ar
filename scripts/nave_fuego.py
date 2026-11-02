# Agrega el fuego celeste de las toberas a la nave renderizada (scripts/nave_blender.py) y la guarda lista para la web.
# Uso: python3 scripts/nave_fuego.py nave.png salida_sin_extension
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGBA'); W, H = im.size
pos = json.load(open(src + '.toberas.json'))
fuego = Image.new('RGBA', (W, H), (0, 0, 0, 0))
for (x0, y0, x1, y1, r) in pos:
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    n = 40
    for i in range(n):           # pluma: círculos que se achican y se apagan hacia atrás
        t = i / n; x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t; rr = W * r * .055 * (1 - t * .75)
        a = int(235 * (1 - t) ** 1.6)
        col = (int(170 + 85 * (1 - t)), int(215 + 40 * (1 - t)), 255, a)
        d.ellipse([x - rr, y - rr * .8, x + rr, y + rr * .8], fill=col)
    fuego = Image.alpha_composite(fuego, capa.filter(ImageFilter.GaussianBlur(W * .006)))
    nucleo = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(nucleo).ellipse([x0 - W * r * .03, y0 - W * r * .03, x0 + W * r * .03, y0 + W * r * .03], fill=(255, 255, 255, 255))
    fuego = Image.alpha_composite(fuego, nucleo.filter(ImageFilter.GaussianBlur(W * .004)))
halo = fuego.filter(ImageFilter.GaussianBlur(W * .02))
res = Image.alpha_composite(Image.alpha_composite(halo, fuego), im)
bb = res.getbbox(); res = res.crop((max(0, bb[0] - 10), max(0, bb[1] - 10), min(W, bb[2] + 10), min(H, bb[3] + 10)))
res.save(out + '.png', optimize=True); res.save(out + '.webp', quality=88, method=6)
print('listo', res.size)
