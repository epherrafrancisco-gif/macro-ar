# Bóveda de un banco central en 3D (Blender/Cycles), fondo del modo Bóveda de Pulso Macro.
# Escena: pilas de lingotes con el anillo del logo grabado, piso de piedra pulida, pared de cajas de seguridad y la puerta
# circular de la bóveda abierta al fondo, con luz cálida de arriba y profundidad de campo.
# Uso: pip install bpy && python3 scripts/boveda_blender.py salida.png [ancho alto muestras]
import sys, math, random
import bpy, bmesh
from mathutils import Vector

OUT = sys.argv[1] if len(sys.argv) > 1 else 'boveda.png'
RW, RH, SPP = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1600, 1000, 64)
random.seed(4)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------- materiales ----------
def mat(nombre, color, metal=0.0, rough=0.5, emis=None, fuerza=0.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    if emis: b.inputs['Emission Color'].default_value = (*emis, 1); b.inputs['Emission Strength'].default_value = fuerza
    return m
ORO = mat('oro', (1.0, 0.66, 0.22), 1.0, 0.13)
ORO2 = mat('oro2', (1.0, 0.64, 0.21), 1.0, 0.2)
PISO = mat('piso', (0.012, 0.011, 0.01), 0.0, 0.12)
PARED = mat('pared', (0.02, 0.018, 0.016), 0.3, 0.6)
ACERO = mat('acero', (0.55, 0.52, 0.48), 1.0, 0.28)
ACERO_OSC = mat('acero_osc', (0.18, 0.17, 0.16), 1.0, 0.35)
CAJA = mat('caja', (0.16, 0.13, 0.09), 1.0, 0.38)
LATON = mat('laton', (0.78, 0.58, 0.32), 1.0, 0.25)
LUZ_ORO = mat('luz_oro', (0.0, 0.0, 0.0), 0.0, 1.0, (1.0, 0.55, 0.18), 0.9)

def obj(nombre, malla, m, loc=(0, 0, 0), rot=(0, 0, 0)):
    o = bpy.data.objects.new(nombre, malla); sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot; o.data.materials.append(m); return o

# ---------- lingote: prisma trapezoidal con bisel y el anillo grabado arriba ----------
def malla_lingote():
    bm = bmesh.new()
    L, A, H, l, a = .25, .11, .045, .215, .08          # largo y ancho abajo, alto, largo y ancho arriba
    v = [bm.verts.new(p) for p in [(-L/2, -A/2, 0), (L/2, -A/2, 0), (L/2, A/2, 0), (-L/2, A/2, 0),
                                    (-l/2, -a/2, H), (l/2, -a/2, H), (l/2, a/2, H), (-l/2, a/2, H)]]
    for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]: bm.faces.new([v[i] for i in f])
    me = bpy.data.meshes.new('lingote'); bm.to_mesh(me); bm.free()
    return me
ML = malla_lingote()
def malla_anillo():
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=.026, radius2=.026, depth=.0016)
    me = bpy.data.meshes.new('anillo'); bm.to_mesh(me); bm.free(); return me
def bisel(o, w=.004):
    m = o.modifiers.new('b', 'BEVEL'); m.width = w; m.segments = 3; m.limit_method = 'ANGLE'
    o.data.polygons.foreach_set('use_smooth', [False] * len(o.data.polygons))
def lingote(x, y, z, ang, m=ORO):
    o = obj('l', ML, m, (x, y, z), (0, 0, ang)); bisel(o)
    return o
def pila(x0, y0, capas, n_fila, ang0=0.0, m=ORO):
    # capas alternadas a lo largo y a lo ancho, como se apilan de verdad
    for c in range(capas):
        z = c * .046
        cruz = c % 2 == 1
        n = max(1, n_fila - (c // 2))
        for i in range(n):
            for j in range(2 if not cruz else 1):
                if cruz:
                    dx, dy = (i - (n - 1) / 2) * .118, 0
                    a = ang0 + math.pi / 2
                else:
                    dx, dy = 0, (i - (n - 1) / 2) * .118
                    a = ang0
                    dx += (j - .5) * .255
                ca, sa = math.cos(ang0), math.sin(ang0)
                lingote(x0 + dx * ca - dy * sa + random.uniform(-.002, .002), y0 + dx * sa + dy * ca + random.uniform(-.002, .002), z, a + random.uniform(-.01, .01), m)
# anillo del logo grabado en el lingote de arriba de la pila principal
MA = malla_anillo()

# ---------- piso y paredes ----------
def plano(nombre, tam, m, loc, rot):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=tam / 2)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free(); return obj(nombre, me, m, loc, rot)
plano('piso', 30, PISO, (0, 4, 0), (0, 0, 0))


# pared de cajas de seguridad (izquierda del fondo)
def caja_malla():
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new('caja'); bm.to_mesh(me); bm.free(); return me
MC = caja_malla()
for i in range(12):
    for j in range(10):
        o = obj('c', MC, CAJA, (-4.4 + i * .34, 6.42, .25 + j * .24), (0, 0, 0)); o.scale = (.32, .05, .22)
        k = obj('k', MC, LATON, (-4.4 + i * .34 + .11, 6.385, .25 + j * .24), (0, 0, 0)); k.scale = (.025, .02, .025)

# ---------- puerta circular de la bóveda, abierta (derecha del fondo) ----------
PX, PY, PZ, PR = 1.9, 6.4, 1.5, 1.35
def cilindro(r, h, seg=96):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    me = bpy.data.meshes.new('cil'); bm.to_mesh(me); bm.free(); return me
def toro(R, r):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=128, minor_segments=16)
    return bpy.context.active_object
# marco: aros en la pared
for R, r in [(PR + .18, .1), (PR + .02, .06)]:
    t = toro(R, r); t.location = (PX, PY - .02, PZ); t.rotation_euler = (math.pi / 2, 0, 0); t.data.materials.append(ACERO)
# pared con el hueco de verdad (boolean) y, atrás, la sala del tesoro: estantes de lingotes con luz propia
pared = obj('pared', MC, PARED, (0, PY + .15, 6)); pared.scale = (30, .3, 12)
hue = obj('hueco', cilindro(PR - .02, 1.0), PARED, (PX, PY + .15, PZ), (math.pi / 2, 0, 0)); hue.hide_render = True
bo = pared.modifiers.new('hueco', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = hue
fondo = obj('fondo', MC, PARED, (PX, PY + 2.6, 2)); fondo.scale = (8, .1, 6)
for est in range(5):
    z = .35 + est * .48
    e = obj('estante', MC, ACERO_OSC, (PX, PY + 2.25, z - .03)); e.scale = (5, .5, .03)
    for k in range(34):
        for capa in range(2):
            lingote(PX - 2.4 + k * .145 + capa * .07, PY + 2.2 + random.uniform(-.05, .05), z + capa * .046, math.pi / 2 + random.uniform(-.06, .06), ORO2)
# la hoja de la puerta: disco grueso girado ~75° sobre la bisagra derecha
puerta = obj('puerta', cilindro(PR - .05, .45), ACERO, (0, 0, 0), (0, 0, 0))
bis = bpy.data.objects.new('bisagra', None); sc.collection.objects.link(bis); bis.location = (PX + PR + .05, PY - .25, PZ)
puerta.parent = bis; puerta.location = (-(PR + .05), 0, 0); puerta.rotation_euler = (math.pi / 2, 0, 0)
for R, r in [(PR * .82, .03), (PR * .6, .025), (PR * .3, .03)]:
    t = toro(R, r); t.data.materials.append(ACERO_OSC); t.parent = bis; t.location = (-(PR + .05), -.23, 0); t.rotation_euler = (math.pi / 2, 0, 0)
# volante de rayos
for k in range(6):
    a = k * math.pi / 3
    rayo = obj('rayo', cilindro(.025, PR * .55, 16), LATON, (0, 0, 0)); rayo.parent = bis
    rayo.location = (-(PR + .05) + math.cos(a) * PR * .27, -.3, math.sin(a) * PR * .27); rayo.rotation_euler = (0, a + math.pi / 2, 0)
cubo = obj('cubo', cilindro(.12, .14, 48), LATON, (0, 0, 0)); cubo.parent = bis; cubo.location = (-(PR + .05), -.3, 0); cubo.rotation_euler = (math.pi / 2, 0, 0)
# cerrojos que salen del canto
for k in range(14):
    a = math.pi * .55 + k * (math.pi * .9 / 13)
    c = obj('cerrojo', cilindro(.06, .32, 24), ACERO, (0, 0, 0)); c.parent = bis
    c.location = (-(PR + .05) + math.cos(a) * (PR + .05), 0, math.sin(a) * (PR + .05)); c.rotation_euler = (0, -a + math.pi / 2, 0)
bis.rotation_euler = (0, 0, math.radians(72))

# ---------- el oro: pila principal adelante, más pilas atrás en penumbra ----------
pila(0.0, 0.0, 6, 4, math.radians(8))
pila(-.85, .9, 5, 4, math.radians(-14), ORO2)
pila(.95, 1.25, 4, 3, math.radians(22), ORO2)
pila(-1.7, 2.6, 6, 4, math.radians(4), ORO2)
pila(.4, 3.4, 5, 4, math.radians(-30), ORO2)
pila(2.3, 4.6, 6, 4, math.radians(12), ORO2)
pila(-.9, 5.2, 4, 3, math.radians(40), ORO2)
an = obj('logo', MA, ORO2, (0.0, 0.0, 5 * .046 + .045 + .0008), (0, 0, 0))   # anillo grabado sobre el lingote de arriba

# ---------- luces: cálidas, de arriba, con contraluz ----------
def luz(nombre, tipo, loc, rot, energia, color, tam=1.0):
    l = bpy.data.lights.new(nombre, tipo); l.energy = energia; l.color = color
    if tipo == 'AREA': l.size = tam
    if tipo == 'SPOT': l.spot_size = math.radians(tam); l.spot_blend = .6
    o = bpy.data.objects.new(nombre, l); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
CAL = (1.0, 0.74, 0.46)
luz('arriba', 'SPOT', (0.2, -.3, 3.2), (math.radians(8), 0, 0), 900, CAL, 34)
luz('relleno', 'AREA', (-2.5, -1.5, 2.2), (math.radians(60), 0, math.radians(-50)), 120, (1.0, .82, .62), 3)
luz('contra', 'AREA', (0.5, 2.5, 2.6), (math.radians(-55), 0, 0), 260, CAL, 2)
luz('pared', 'AREA', (-2.0, 4.5, 3.2), (math.radians(-35), 0, 0), 220, CAL, 4)
luz('sala', 'AREA', (PX, PY + 1.3, 3.0), (math.radians(-20), 0, 0), 700, (1.0, .7, .4), 3)
luz('sala2', 'AREA', (PX, PY + .9, .3), (math.radians(110), 0, 0), 160, (1.0, .7, .4), 2)
for (x, y, e) in [(-1.2, .6, 140), (1.2, 1.4, 120), (0, -2.6, 70)]:
    luz('panel', 'AREA', (x, y, 2.4), (0, 0, 0), e, (1.0, .78, .5), 1.6)
w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.002, .0018, .0015, 1); sc.world = w

# ---------- cámara baja, lente larga y poca profundidad de campo ----------
cam = bpy.data.cameras.new('cam'); cam.lens = 38; cam.dof.use_dof = True; cam.dof.aperture_fstop = 2.0
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
co.location = (-.75, -2.25, .36)
objetivo = Vector((.35, 1.2, .5)); d = objetivo - co.location
co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.dof.focus_distance = (Vector((0, 0, .15)) - co.location).length

sc.render.engine = 'CYCLES'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 4
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RW, RH, 100
VT = [x.identifier for x in sc.view_settings.bl_rna.properties['view_transform'].enum_items]
sc.view_settings.view_transform = 'Khronos PBR Neutral' if 'Khronos PBR Neutral' in VT else 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = -1.3
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('listo', OUT)
