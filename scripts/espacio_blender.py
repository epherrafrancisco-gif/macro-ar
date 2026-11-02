# La Tierra vista desde la órbita, sobre Argentina al atardecer (Blender/Cycles): fondo del modo legendario de Pulso Macro.
# Texturas: Solar System Scope (CC BY 4.0, basadas en datos de la NASA): 8k_earth_daymap.jpg, 8k_earth_nightmap.jpg;
# nubes y océanos de los mapas de la NASA que trae three.js (earth_clouds_1024.png, earth_specular_2048.jpg).
# Uso: pip install bpy && python3 scripts/espacio_blender.py carpeta_texturas salida.png [ancho alto muestras]
import sys, math
import bpy
from mathutils import Vector

TEX, OUT = sys.argv[1], sys.argv[2]
RW, RH, SPP = (int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1200, 750, 32)
R = 6.371                                   # 1 unidad = 1.000 km
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def sph(lat, lon, r=1.0):
    la, lo = math.radians(lat), math.radians(lon)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))

# ---------- parámetros de la toma ----------
SOL = sph(-17, -150)                        # punto subsolar: en Buenos Aires está cayendo el sol
CAM = sph(-40, -38, R + 1.7)                # cámara sobre el Atlántico Sur, a 1.700 km
MIRA = sph(-31, -64, R)                     # mira hacia el centro de Argentina y la cordillera

def nodos(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); return nt, nt.nodes, nt.links
def coords_latlon(nt, N, L):
    """u, v equirectangulares a partir de la posición en el objeto (lon = atan2(y, x), lat = asin(z))"""
    tc = N.new('ShaderNodeTexCoord'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    nrm = N.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'; L.new(tc.outputs['Object'], nrm.inputs[0])
    sz = N.new('ShaderNodeSeparateXYZ'); L.new(nrm.outputs[0], sz.inputs[0])
    at = N.new('ShaderNodeMath'); at.operation = 'ARCTAN2'; L.new(sep.outputs['Y'], at.inputs[0]); L.new(sep.outputs['X'], at.inputs[1])
    u = N.new('ShaderNodeMath'); u.operation = 'MULTIPLY_ADD'; L.new(at.outputs[0], u.inputs[0]); u.inputs[1].default_value = 1 / (2 * math.pi); u.inputs[2].default_value = .5
    asn = N.new('ShaderNodeMath'); asn.operation = 'ARCSINE'; L.new(sz.outputs['Z'], asn.inputs[0])
    v = N.new('ShaderNodeMath'); v.operation = 'MULTIPLY_ADD'; L.new(asn.outputs[0], v.inputs[0]); v.inputs[1].default_value = 1 / math.pi; v.inputs[2].default_value = .5
    cxyz = N.new('ShaderNodeCombineXYZ'); L.new(u.outputs[0], cxyz.inputs[0]); L.new(v.outputs[0], cxyz.inputs[1])
    return cxyz.outputs[0]
def imagen(N, L, uv, archivo, color=True):
    t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(f'{TEX}/{archivo}'); t.interpolation = 'Cubic'
    if not color: t.image.colorspace_settings.name = 'Non-Color'
    L.new(uv, t.inputs[0]); return t
def luz_sol(nt, N, L, a=-.12, b=.18):
    """factor 0 (noche) → 1 (día) según el ángulo entre la normal y el sol"""
    g = N.new('ShaderNodeNewGeometry'); d = N.new('ShaderNodeVectorMath'); d.operation = 'DOT_PRODUCT'
    L.new(g.outputs['Normal'], d.inputs[0]); d.inputs[1].default_value = SOL.normalized()
    mr = N.new('ShaderNodeMapRange'); L.new(d.outputs['Value'], mr.inputs['Value']); mr.inputs['From Min'].default_value = a; mr.inputs['From Max'].default_value = b
    return mr.outputs[0], d.outputs['Value']
def esfera(nombre, r, m, seg=256):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r)
    o = bpy.context.active_object; o.name = nombre; bpy.ops.object.shade_smooth(); o.data.materials.append(m); return o

# ---------- la Tierra: día, océanos que brillan y luces de las ciudades de noche ----------
m = bpy.data.materials.new('tierra'); nt, N, L = nodos(m)
uv = coords_latlon(nt, N, L)
dia = imagen(N, L, uv, '8k_earth_daymap.jpg'); noche = imagen(N, L, uv, '8k_earth_nightmap.jpg'); spec = imagen(N, L, uv, 'earth_specular_2048.jpg', False)
bsdf = N.new('ShaderNodeBsdfPrincipled'); L.new(dia.outputs[0], bsdf.inputs['Base Color'])
rug = N.new('ShaderNodeMapRange'); L.new(spec.outputs[0], rug.inputs['Value']); rug.inputs['To Min'].default_value = .85; rug.inputs['To Max'].default_value = .32
L.new(rug.outputs[0], bsdf.inputs['Roughness'])
dia_f, _ = luz_sol(nt, N, L, -.05, .12)
inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; L.new(dia_f, inv.inputs[1])
luces = N.new('ShaderNodeMath'); luces.operation = 'MULTIPLY'; L.new(inv.outputs[0], luces.inputs[0]); luces.inputs[1].default_value = 3.2
em = N.new('ShaderNodeEmission'); L.new(noche.outputs[0], em.inputs['Color']); L.new(luces.outputs[0], em.inputs['Strength'])
su = N.new('ShaderNodeAddShader'); L.new(bsdf.outputs[0], su.inputs[0]); L.new(em.outputs[0], su.inputs[1])
out = N.new('ShaderNodeOutputMaterial'); L.new(su.outputs[0], out.inputs['Surface'])
tierra = esfera('tierra', R, m)

# ---------- nubes: el mapa de la NASA da dónde hay tormentas; ruido fino da el detalle ----------
m = bpy.data.materials.new('nubes'); nt, N, L = nodos(m)
uv = coords_latlon(nt, N, L)
cl = imagen(N, L, uv, 'nubes_mask.png', False)          # canal alfa del mapa de nubes, pasado a gris (ver texturas)
tc = N.new('ShaderNodeTexCoord')
def ruido(esc, det, rug):
    n = N.new('ShaderNodeTexNoise'); L.new(tc.outputs['Object'], n.inputs['Vector'])
    n.inputs['Scale'].default_value = esc; n.inputs['Detail'].default_value = det; n.inputs['Roughness'].default_value = rug; n.inputs['Distortion'].default_value = .4
    return n.outputs['Fac']
def rango(x, a, b):
    r = N.new('ShaderNodeMapRange'); L.new(x, r.inputs['Value']); r.inputs['From Min'].default_value = a; r.inputs['From Max'].default_value = b; return r.outputs[0]
def op(o, a, b):
    m_ = N.new('ShaderNodeMath'); m_.operation = o; m_.use_clamp = True
    for i, x in enumerate((a, b)):
        if isinstance(x, (int, float)): m_.inputs[i].default_value = x
        else: L.new(x, m_.inputs[i])
    return m_.outputs[0]
grandes = op('MULTIPLY', rango(cl.outputs[0], .03, .5), rango(ruido(5.0, 15, .6), .3, .62))
sueltas = op('MULTIPLY', rango(ruido(9.0, 15, .66), .56, .74), .55)
class _R: pass
ramp = _R(); ramp.outputs = [op('ADD', grandes, sueltas)]
b = N.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = (.95, .95, .95, 1); b.inputs['Roughness'].default_value = 1
tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader')
L.new(ramp.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2])
out = N.new('ShaderNodeOutputMaterial'); L.new(mx.outputs[0], out.inputs['Surface'])
esfera('nubes', R + .014, m)

# ---------- atmósfera: borde azul del lado de día, franja naranja en el terminador ----------
m = bpy.data.materials.new('atmosfera'); nt, N, L = nodos(m); m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = .5
pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; L.new(lw.outputs['Facing'], pw.inputs[0]); pw.inputs[1].default_value = 5.0
f_dia, dotv = luz_sol(nt, N, L, -.22, .25)
cr = N.new('ShaderNodeValToRGB'); L.new(f_dia, cr.inputs['Fac'])
cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
e1 = cr.color_ramp.elements.new(.32); e1.color = (1.0, .32, .08, 1)
e2 = cr.color_ramp.elements.new(.6); e2.color = (.45, .62, 1.0, 1)
cr.color_ramp.elements[1].position = 1.0; cr.color_ramp.elements[1].color = (.28, .52, 1.0, 1)
fu = N.new('ShaderNodeMath'); fu.operation = 'MULTIPLY'; L.new(pw.outputs[0], fu.inputs[0]); fu.inputs[1].default_value = 1.5
em = N.new('ShaderNodeEmission'); L.new(cr.outputs[0], em.inputs['Color']); L.new(fu.outputs[0], em.inputs['Strength'])
tr = N.new('ShaderNodeBsdfTransparent'); ad = N.new('ShaderNodeAddShader'); L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
out = N.new('ShaderNodeOutputMaterial'); L.new(ad.outputs[0], out.inputs['Surface'])
esfera('atmosfera', R + .11, m)

# ---------- el sol ----------
s = bpy.data.lights.new('sol', 'SUN'); s.energy = 4.2; s.angle = math.radians(.53); s.color = (1.0, .97, .92)
so = bpy.data.objects.new('sol', s); sc.collection.objects.link(so)
so.rotation_euler = SOL.normalized().to_track_quat('Z', 'Y').to_euler()
w = bpy.data.worlds.new('w'); sc.world = w
try:
    w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1)
except Exception: pass

# ---------- cámara ----------
cam = bpy.data.cameras.new('cam'); cam.lens = 30; cam.clip_end = 100
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
co.location = CAM
d = (MIRA - CAM)
q = d.to_track_quat('-Z', 'Y')
up = CAM.normalized()                       # "arriba" = hacia afuera de la Tierra: el horizonte queda horizontal
x = d.normalized().cross(up).normalized(); y = x.cross(d.normalized()).normalized()
from mathutils import Matrix
co.matrix_world = Matrix((
    (x[0], y[0], -d.normalized()[0], CAM[0]),
    (x[1], y[1], -d.normalized()[1], CAM[1]),
    (x[2], y[2], -d.normalized()[2], CAM[2]),
    (0, 0, 0, 1)))
cam.shift_y = .16                           # baja el horizonte: más espacio negro arriba para el contenido

sc.render.engine = 'CYCLES'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 3; sc.cycles.transparent_max_bounces = 8
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RW, RH, 100
VT = [v.identifier for v in sc.view_settings.bl_rna.properties['view_transform'].enum_items]
sc.view_settings.view_transform = 'AgX' if 'AgX' in VT else 'Filmic'
sc.view_settings.exposure = -0.2
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('listo', OUT)
