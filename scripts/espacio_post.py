# Terminación del render de la Tierra (scripts/espacio_blender.py): estrellas en el espacio, brillo de la atmósfera y de las
# luces, grano fino; guarda los fondos del modo legendario. Uso: python3 scripts/espacio_post.py tierra.png carpeta_salida
import sys
import numpy as np
from PIL import Image, ImageFilter
src, out = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(3)
im = Image.open(src).convert('RGB'); W, H = im.size
a = np.asarray(im, float)
lum = a.mean(2)
# dónde es espacio: arriba del horizonte (columna por columna, hasta el primer píxel claro)
esp = np.zeros((H, W), bool)
claro = lum > 6
primer = np.where(claro.any(0), claro.argmax(0), H)
for x in range(W): esp[:max(0, primer[x] - 6), x] = True
# estrellas: muchas chiquitas, pocas brillantes, con colores de estrella real
n = int(W * H / 900)
xs, ys = rng.integers(0, W, n), rng.integers(0, H, n)
br = rng.pareto(2.6, n) * 34 + 10
tint = rng.choice([[1, .86, .7], [1, .95, .88], [1, 1, 1], [.82, .9, 1], [.72, .82, 1]], n)
st = np.zeros((H, W, 3))
ok = esp[ys, xs]
np.add.at(st, (ys[ok], xs[ok]), (br[ok, None] * tint[ok]))
st = np.asarray(Image.fromarray(np.clip(st, 0, 255).astype('uint8')).filter(ImageFilter.GaussianBlur(.6)), float) * 2.2
# las estrellas se apagan cerca del horizonte iluminado (la atmósfera las tapa)
yy = np.arange(H)[:, None]
fade = np.clip((primer[None, :] - yy) / (H * .16), 0, 1)
a = a + st * fade[:, :, None]
# brillo (bloom) de lo más claro: la atmósfera, el sol en las nubes y las ciudades
alto = np.clip(a - 150, 0, 255)
bloom = np.asarray(Image.fromarray(alto.astype('uint8')).filter(ImageFilter.GaussianBlur(W * .01)), float)
a = a + bloom * .55 + np.asarray(Image.fromarray(alto.astype('uint8')).filter(ImageFilter.GaussianBlur(W * .003)), float) * .35
a += rng.normal(0, 2.2, (H, W, 1))
res = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
res.save(f'{out}/espacio-2400.jpg', quality=86, optimize=True, progressive=True)
res.save(f'{out}/espacio-2400.webp', quality=82, method=6)
# celular: recorte vertical con la curva de la Tierra abajo
cw = int(H * .64); x0 = (W - cw) // 2 + int(W * .06)
cel = res.crop((x0, 0, x0 + cw, H)).resize((960, 1500), Image.LANCZOS)
cel.save(f'{out}/espacio-1200.jpg', quality=84, optimize=True, progressive=True)
cel.save(f'{out}/espacio-1200.webp', quality=80, method=6)
print('listo')
