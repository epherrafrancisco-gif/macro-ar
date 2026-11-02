# Nave espacial de Pulso Macro (diseño propio), Blender/Cycles con fondo transparente, para el modo legendario.
# Avión espacial: fuselaje blanco con panza negra de escudo térmico, alas delta, dos derivas con el anillo del logo,
# franja celeste (#6aa8d8) y tres toberas encendidas. Uso: python3 scripts/nave_blender.py salida.png [ancho alto muestras]
import sys, math
import bpy, bmesh
from mathutils import Vector, Matrix

OUT = sys.argv[1]
RW, RH, SPP = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1200, 600, 64)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def mat(n, c, metal=0.0, rough=.4, emis=None, fz=0.0, coat=0.0):
    m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*c, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    if coat: b.inputs['Coat Weight'].default_value = coat
    if emis: b.inputs['Emission Color'].default_value = (*emis, 1); b.inputs['Emission Strength'].default_value = fz
    return m
BLANCO = mat('blanco', (.86, .87, .88), 0, .32, coat=.4)
def paneles(m, esc, fuerza):
    nt = m.node_tree; N = nt.nodes; L = nt.links; b = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); br = N.new('ShaderNodeTexBrick'); L.new(tc.outputs['Object'], br.inputs['Vector'])
    br.inputs['Scale'].default_value = esc; br.inputs['Mortar Size'].default_value = .004; br.inputs['Color1'].default_value = (1, 1, 1, 1); br.inputs['Color2'].default_value = (.92, .92, .93, 1)
    bu = N.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = fuerza; L.new(br.outputs['Fac'], bu.inputs['Height']); L.new(bu.outputs['Normal'], b.inputs['Normal'])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['Factor'].default_value = .22
    mx.inputs['A'].default_value = b.inputs['Base Color'].default_value[:]
    L.new(br.outputs['Color'], mx.inputs['B']); mx.blend_type = 'MULTIPLY'; L.new(mx.outputs['Result'], b.inputs['Base Color'])
paneles(BLANCO, 1.6, .08)
NEGRO = mat('escudo', (.025, .026, .03), 0, .7)
paneles(NEGRO, 4.0, .4)
GRAFITO = mat('grafito', (.09, .1, .115), .6, .35)
CELESTE = mat('celeste', (.27, .55, .78), 0, .3, coat=.3)
VIDRIO = mat('vidrio', (.01, .012, .016), .9, .05)
METAL = mat('metal', (.55, .55, .58), 1, .3)
TOBERA = mat('tobera', (.3, .62, 1.0), 0, 1, (.42, .72, 1.0), 40)
ANILLO_M = mat('anillo', (.27, .55, .78), 0, .25, (.27, .55, .78), .6)

def obj_de(bm, nombre, m, suave=True):
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nombre, me); sc.collection.objects.link(o); o.data.materials.append(m)
    if suave:
        o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
        try: o.modifiers.new('n', 'WEIGHTED_NORMAL')
        except Exception: pass
    return o

# ---------- fuselaje: anillos a lo largo de X (nariz en +X), sección elíptica con panza plana ----------
LARGO, ANCHO, ALTO, NS = 6.0, .62, .5, 48
def perfil(t):          # t = 0 cola, 1 nariz
    if t > .62: return max(0, 1 - ((t - .62) / .38) ** 1.7) ** .75
    return .82 + .18 * (t / .72) ** .6
bm = bmesh.new(); anillos = []
N_A = 60
for i in range(N_A + 1):
    t = i / N_A; x = (t - .5) * LARGO; f = perfil(t)
    zc = .06 * t           # la nariz sube apenas
    fila = []
    for k in range(NS):
        a = 2 * math.pi * k / NS
        y = math.cos(a) * ANCHO * f
        z = math.sin(a) * ALTO * f * (1.0 if math.sin(a) > 0 else .55)   # panza más plana
        fila.append(bm.verts.new((x, y, z + zc)))
    anillos.append(fila)
for i in range(N_A):
    for k in range(NS):
        a, b = anillos[i][k], anillos[i][(k + 1) % NS]; c, d = anillos[i + 1][(k + 1) % NS], anillos[i + 1][k]
        bm.faces.new((a, b, c, d))
bm.faces.new(list(reversed(anillos[0])))
fus = obj_de(bm, 'fuselaje', BLANCO)
sub = fus.modifiers.new('s', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
# panza negra: segundo material en las caras de abajo
fus.data.materials.append(NEGRO)
for p in fus.data.polygons:
    if p.center.z < -.02: p.material_index = 1

# ---------- alas delta y derivas (prismas finos con bisel) ----------
def placa(pts, esp, nombre, m, z0=0.0):
    bm = bmesh.new()
    a = [bm.verts.new((x, y, z0 - esp / 2)) for x, y in pts]; b = [bm.verts.new((x, y, z0 + esp / 2)) for x, y in pts]
    bm.faces.new(list(reversed(a))); bm.faces.new(b)
    n = len(pts)
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    o = obj_de(bm, nombre, m, False); bv = o.modifiers.new('b', 'BEVEL'); bv.width = .02; bv.segments = 3
    return o
ala = [(1.2, .35), (-2.6, 2.5), (-2.95, 2.5), (-2.9, .3)]
for lado in (1, -1):
    o = placa([(x, y * lado) for x, y in ala], .08, 'ala', BLANCO, -.12)
    o.data.materials.append(NEGRO)
    # franja celeste en el borde de ataque del ala
    f = placa([(x, y * lado) for x, y in [(1.15, .36), (-2.55, 2.46), (-2.62, 2.42), (1.0, .38)]], .085, 'franja_ala', CELESTE, -.12)
    # deriva canteada
    der = placa([(-1.9, 0), (-2.95, 0), (-3.05, 1.35), (-2.55, 1.35)], .07, 'deriva', BLANCO)
    der.rotation_euler = (math.radians(90 - 18) * lado, 0, 0); der.location = (0, .42 * lado, .1)
    # el anillo del logo de Pulso Macro en la deriva
    bpy.ops.mesh.primitive_torus_add(major_radius=.22, minor_radius=.035, major_segments=64, minor_segments=12)
    an = bpy.context.active_object; an.data.materials.append(ANILLO_M); an.parent = der
    an.location = (-2.55, .82, .05 * lado); an.rotation_euler = (0, 0, 0)
    # latido adentro del anillo (cinco segmentos, como el logo)
    pts = [(-.18, 0), (-.04, 0), (0, .1), (.04, -.14), (.08, .16), (.12, 0), (.18, 0)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        L = math.hypot(x2 - x1, y2 - y1)
        bpy.ops.mesh.primitive_cylinder_add(radius=.016, depth=L, vertices=8)
        c = bpy.context.active_object; c.data.materials.append(BLANCO); c.parent = der
        c.location = (-2.55 + (x1 + x2) / 2, .82 + (y1 + y2) / 2, .05 * lado)
        c.rotation_euler = (0, math.pi / 2, math.atan2(y2 - y1, x2 - x1))

# ---------- franja celeste a lo largo del fuselaje ----------
bm = bmesh.new()
for lado in (1, -1):
    pass
for lado in (1, -1):
    bpy.ops.mesh.primitive_cube_add(size=1)
    fr = bpy.context.active_object; fr.data.materials.append(CELESTE)
    fr.scale = (4.6, .02, .09); fr.location = (-.3, (ANCHO * .9) * lado, -.12)

# ---------- nombre en el costado ----------
for lado in (1, -1):
    cu = bpy.data.curves.new('nombre', 'FONT'); cu.body = 'PULSO MACRO'; cu.size = .3; cu.extrude = .004; cu.align_x = 'CENTER'
    try: cu.font = bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
    except Exception: pass
    t = bpy.data.objects.new('nombre', cu); sc.collection.objects.link(t); t.data.materials.append(GRAFITO)
    t.location = (-.35, (ANCHO * .93) * lado, .12); t.rotation_euler = (math.radians(90 if lado < 0 else -90), 0, 0 if lado < 0 else math.pi)
    if lado > 0: t.scale = (1, 1, 1)
# ---------- cabina ----------
# ventanillas: cuatro paneles oscuros sobre el lomo, detrás de la nariz
for i, (dx, ya) in enumerate([(0, .17), (.27, .15)]):
    for lado in (1, -1):
        bpy.ops.mesh.primitive_cube_add(size=1); v = bpy.context.active_object; v.data.materials.append(VIDRIO)
        v.scale = (.24, .15, .03); v.location = (1.55 + dx, ya * lado * .9, .45 - dx * .12)
        v.rotation_euler = (math.radians(14) * lado, math.radians(-10), 0)
bpy.ops.mesh.primitive_cube_add(size=1); v = bpy.context.active_object; v.data.materials.append(VIDRIO)
v.scale = (.05, .34, .03); v.location = (1.42, 0, .47)

# ---------- tobera: tres campanas con la llama celeste ----------
for (y, z, r) in [(0, .12, .26), (.36, -.05, .2), (-.36, -.05, .2)]:
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=r, radius2=r * .7, depth=.42, end_fill_type='NOTHING')
    c = bpy.context.active_object; c.data.materials.append(GRAFITO); c.rotation_euler = (0, math.pi / 2, 0); c.location = (-3.15, y, z)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=r * .92, fill_type='NGON')
    d = bpy.context.active_object; d.data.materials.append(TOBERA); d.rotation_euler = (0, math.pi / 2, 0); d.location = (-3.34, y, z)
    # pluma: cono transparente-emisivo que se desvanece
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r * .85, radius2=r * .25, depth=1.4, end_fill_type='NOTHING')
    pl = bpy.context.active_object; pl.rotation_euler = (0, -math.pi / 2, 0); pl.location = (-4.05, y, z)
    m = bpy.data.materials.new('pluma'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links; N.clear()
    lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = .4
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; Lk.new(lw.outputs['Facing'], inv.inputs[1])
    gc = N.new('ShaderNodeTexGradient'); tcn = N.new('ShaderNodeTexCoord'); Lk.new(tcn.outputs['Generated'], gc.inputs['Vector'])
    mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; Lk.new(inv.outputs[0], mul.inputs[0]); Lk.new(gc.outputs['Fac'], mul.inputs[1])
    fz = N.new('ShaderNodeMath'); fz.operation = 'MULTIPLY'; Lk.new(mul.outputs[0], fz.inputs[0]); fz.inputs[1].default_value = 9
    em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.42, .72, 1.0, 1); Lk.new(fz.outputs[0], em.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent'); ad = N.new('ShaderNodeAddShader'); Lk.new(tr.outputs[0], ad.inputs[0]); Lk.new(em.outputs[0], ad.inputs[1])
    o = N.new('ShaderNodeOutputMaterial'); Lk.new(ad.outputs[0], o.inputs['Surface'])
    pl.data.materials.append(m)

# ---------- detalles: luces de navegación y paneles ----------
for (x, y, col) in [(-2.75, 2.47, (1, .1, .1)), (-2.75, -2.47, (.1, 1, .3))]:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.04); l = bpy.context.active_object; l.location = (x, y, -.12)
    l.data.materials.append(mat('nav', col, 0, .5, col, 25))

# ---------- luz: sol duro arriba a la izquierda + brillo azul de la Tierra desde abajo ----------
def luz(t, loc, rot, e, c, tam=1):
    L = bpy.data.lights.new(t, t if t in ('SUN', 'AREA', 'POINT') else 'SUN'); L.energy = e; L.color = c
    if t == 'AREA': L.size = tam
    o = bpy.data.objects.new(t, L); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
luz('SUN', (0, 0, 10), (math.radians(40), math.radians(-25), math.radians(30)), 5.0, (1.0, .96, .9))
luz('AREA', (0, 0, -6), (math.radians(180), 0, 0), 900, (.35, .55, 1.0), 12)
w = bpy.data.worlds.new('w'); sc.world = w
try: w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.004, .005, .008, 1)
except Exception: pass

# ---------- cámara: tres cuartos, de arriba y de costado (la nave va hacia la derecha) ----------
cam = bpy.data.cameras.new('cam'); cam.lens = 70
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
co.location = Vector((5.5, -19.0, 7.5))
co.rotation_euler = (Vector((-.4, 0, -.1)) - co.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.film_transparent = True
sc.render.engine = 'CYCLES'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RW, RH, 100
VT = [v.identifier for v in sc.view_settings.bl_rna.properties['view_transform'].enum_items]
sc.view_settings.view_transform = 'AgX' if 'AgX' in VT else 'Filmic'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
# dónde quedan las toberas en la imagen (para dibujar el fuego encima: con fondo transparente la emisión no se guarda)
from bpy_extras.object_utils import world_to_camera_view
import json
pos = []
for (y, z, r) in [(0, .12, .26), (.36, -.05, .2), (-.36, -.05, .2)]:
    a = world_to_camera_view(sc, co, Vector((-3.34, y, z))); b = world_to_camera_view(sc, co, Vector((-5.2, y, z)))
    pos.append([a.x * RW, (1 - a.y) * RH, b.x * RW, (1 - b.y) * RH, r])
json.dump(pos, open(OUT + '.toberas.json', 'w'))
print('listo', OUT)
