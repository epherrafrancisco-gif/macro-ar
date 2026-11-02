# Pasa la foto de Chongqing a estética cyberpunk (magenta/cian), con brillo en las luces y cielo extra arriba.
from PIL import Image, ImageFilter, ImageEnhance, ImageChops, ImageOps
import sys
src = Image.open(sys.argv[1]).convert('RGB')
W, H = src.size
im = ImageEnhance.Contrast(src).enhance(1.12)
im = ImageEnhance.Color(im).enhance(1.25)
# mapa de color: sombras azul-violeta, medios magenta, luces crema/cian
gris = ImageOps.grayscale(im)
mapa = ImageOps.colorize(gris, black=(6, 4, 22), mid=(150, 40, 170), white=(210, 245, 255), blackpoint=0, whitepoint=255, midpoint=120)
im = Image.blend(im, mapa, 0.34)
# las luces doradas pasan a mezclar con magenta, pero se conservan algo del dorado
r, g, b = im.split()
b = b.point(lambda v: min(255, int(v * 1.12 + 10)))
r = r.point(lambda v: min(255, int(v * 1.04)))
im = Image.merge('RGB', (r, g, b))
# brillo (bloom): luces altas difuminadas sumadas en "screen"
altas = im.point(lambda v: 0 if v < 170 else v)
bloom = altas.filter(ImageFilter.GaussianBlur(14))
bloom = ImageEnhance.Brightness(bloom).enhance(0.9)
im = ImageChops.screen(im, bloom)
# cielo extra arriba (así las puntas de las torres no quedan debajo de las cintas de cotizaciones)
extra = int(H * 0.28)
lienzo = Image.new('RGB', (W, H + extra))
top = tuple(sum(im.getpixel((x, 6))[i] for x in range(0, W, 64)) // len(range(0, W, 64)) for i in range(3))
for y in range(extra):
    t = y / extra
    col = tuple(int(4 * (1 - t) + top[i] * t) for i in range(3))
    lienzo.paste(col, (0, y, W, y + 1))
lienzo.paste(im, (0, extra))
# fundido suave entre el cielo nuevo y la foto
fund = Image.new("L", (W, 260))
for y in range(260): fund.paste(int(255 * y / 260), (0, y, W, y + 1))
cielo = lienzo.crop((0, extra, W, extra + 260))
plano = Image.new("RGB", (W, 260), top)
lienzo.paste(Image.composite(cielo, plano, fund), (0, extra))
# viñeta
vin = Image.new('L', lienzo.size, 0)
vin = ImageOps.invert(Image.radial_gradient('L').resize(lienzo.size))
vin = vin.point(lambda v: int(v * 0.4 + 150))
lienzo = ImageChops.multiply(lienzo, Image.merge('RGB', (vin, vin, vin)))
for ancho, nombre in ((2000, 'chongqing-2000'), (1100, 'chongqing-1100')):
    alto = int(lienzo.size[1] * ancho / lienzo.size[0])
    out = lienzo.resize((ancho, alto), Image.LANCZOS)
    out.save(nombre + '.webp', 'WEBP', quality=72, method=6)
    out.save(nombre + '.jpg', 'JPEG', quality=78, optimize=True, progressive=True)
    print(nombre, out.size)
