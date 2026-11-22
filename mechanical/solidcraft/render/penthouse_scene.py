"""Penthouse showcase of the light panels (Blender 4.3, Cycles).

blender -b assets/penthouse/modern_loft_apartment.blend --disable-autoexec -P penthouse_scene.py -- MODE OUT [W H [N]]
  MODE  still : one frame -> OUT .png (N = samples, default 128)
        video : animation -> OUT .mp4, H.264 (N = frames at 30 fps, default 240)
        blend : save the dressed scene -> OUT .blend

Room: "Modern Loft Apartment" by Matteo Pascale (BlenderKit, free, royalty-free), downloaded to assets/penthouse/.
Panels: render/panel_hex.glb and panel_triangle.glb (complete panels from SolidCraft, metres, z out of the wall).
Layout: on four walls seen from the scene's Camera.008, panels grow on a triangular lattice of 100 mm edges (every
neighbour shares a full edge). Each candidate panel is ray-cast against its wall, so panels sit only on bare wall
(not on the TV, the painting, furniture or door frames). Two clusters wrap corners: west wall -> painting wall (inside
corner) -> stair-side wall (outside corner). A fourth cluster sits high on the double-height kitchen wall.
Effect: a colour wave travelling through 3D space with a slow breathing pulse (the same shader as bedroom_scene.py).
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:]
MODE, OUT = argv[0], argv[1]
RES_X = int(argv[2]) if len(argv) > 2 else 2560      # 1440p for every video and still (user, 2026-11-21)
RES_Y = int(argv[3]) if len(argv) > 3 else 1440
SHOT = os.environ.get("SHOT", "wide")                 # wide: the scene's Camera.008; close: the outside corner
NUM = int(argv[4]) if len(argv) > 4 else (128 if MODE == "still" else 240)
FPS = 30
STANDOFF = 0.010           # panel z 0 sits 10 mm off the wall (back plane -4.3 mm + 5.7 mm Dual Lock)
L = 0.1                    # lattice edge = panel edge

scene = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
lib = bpy.data.collections.new("Panel library")
scene.collection.children.link(lib)
bpy.context.view_layer.layer_collection.children["Panel library"].exclude = True
panels_col = bpy.data.collections.new("Light panels")
scene.collection.children.link(panels_col)


# ------------------------------------------------------------------ panel meshes
def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def load_panel(path, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in objs if o.type == "MESH"]
    select_only(meshes)
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.make_single_user(object=True, obdata=True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in objs:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    films = [o for o in meshes if "film" in o.name.lower()]
    out = []
    for group, name in (([o for o in meshes if o not in films], f"{tag} body"), (films, f"{tag} film")):
        select_only(group)
        bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        ob.name = name
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        lib.objects.link(ob)
        out.append(ob.data)
    return out


HEX_BODY, HEX_FILM = load_panel(os.path.join(HERE, "panel_hex.glb"), "Hexagon")
TRI_BODY, TRI_FILM = load_panel(os.path.join(HERE, "panel_triangle.glb"), "Triangle")

# ------------------------------------------------------------------ film shader: 3D colour wave + breathing
film_mat = bpy.data.materials.new("Panel glow")
film_mat.use_nodes = True
N, Lk = film_mat.node_tree.nodes, film_mat.node_tree.links
bsdf = N["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.45, 0.45, 0.47, 1)   # dimmer diffuse: room light must not wash the colours out
bsdf.inputs["Roughness"].default_value = 0.55
info = N.new("ShaderNodeObjectInfo")
tnode = N.new("ShaderNodeValue")
tnode.label = "time (s)"
tnode.outputs[0].driver_add("default_value").driver.expression = f"frame/{FPS}"


def mnode(op, a=None, b=None, c=None):
    m = N.new("ShaderNodeMath")
    m.operation = op
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            Lk.new(v, m.inputs[i])
    return m.outputs[0]


dot = N.new("ShaderNodeVectorMath")
dot.operation = "DOT_PRODUCT"
dot.inputs[1].default_value = (0.55, 0.45, 0.70)    # wave direction through the room: across the walls and upward
Lk.new(info.outputs["Location"], dot.inputs[0])
WAVE_K = float(os.environ.get("WAVE_K", "0.55"))
phase = mnode("FRACT", mnode("SUBTRACT", mnode("MULTIPLY", dot.outputs["Value"], WAVE_K), mnode("MULTIPLY", tnode.outputs[0], 0.09)))
ramp = N.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.interpolation = "B_SPLINE"
pal = [(0.0, (1.0, 0.08, 0.55)), (0.2, (0.55, 0.15, 1.0)), (0.4, (0.05, 0.55, 1.0)), (0.6, (0.0, 0.95, 0.75)),
       (0.8, (1.0, 0.55, 0.08)), (1.0, (1.0, 0.08, 0.55))]
cr.elements[0].position, cr.elements[0].color = pal[0][0], (*pal[0][1], 1)
cr.elements[1].position, cr.elements[1].color = pal[-1][0], (*pal[-1][1], 1)
for pos, col in pal[1:-1]:
    cr.elements.new(pos).color = (*col, 1)
Lk.new(phase, ramp.inputs["Fac"])
Lk.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
breath = mnode("MULTIPLY_ADD", mnode("SINE", mnode("ADD", mnode("MULTIPLY", tnode.outputs[0], 2 * math.pi * 0.22),
                                                  mnode("MULTIPLY", dot.outputs["Value"], 4.0))), 0.22, 0.78)
GLOW = float(os.environ.get("GLOW", "1.8"))
Lk.new(mnode("MULTIPLY", breath, GLOW), bsdf.inputs["Emission Strength"])
for me in (HEX_FILM, TRI_FILM):
    me.materials.clear()
    me.materials.append(film_mat)


def front_area(me):
    """Area of the film's front faces (local +z): the light-emitting surface of one panel."""
    return sum(f.area for f in me.polygons if f.normal.z > 0.9)


# Max brightness (MAXWHITE=1): every LED at full RGBW white, normalised so every shape shows the same luminance as the
# shape with the fewest LEDs per area (user 2026-11-21: the hexagon, 18 LEDs). Datasheet SKC6812RGBW-NW: W 1800-2525 mcd,
# R+G+B ~1.25 cd -> ~3.4 cd per LED, ~10.7 lm (Lambertian, phi = pi * I). Diffuser + chamber efficiency ~65 % (estimate).
LM_PER_LED, OPT_EFF, HEX_LEDS = 10.7, 0.65, 18
HEX_AREA = front_area(HEX_FILM)
EXITANCE = HEX_LEDS * LM_PER_LED * OPT_EFF / HEX_AREA          # lm/m^2 leaving the film
MAX_STRENGTH = EXITANCE / 683.0                                  # Blender emission W/m^2 (683 lm/W)
print("max brightness: hex film %.4f m2, triangle film %.4f m2, exitance %.0f lm/m2 (%.0f cd/m2), strength %.2f"
      % (HEX_AREA, front_area(TRI_FILM), EXITANCE, EXITANCE / math.pi, MAX_STRENGTH))
if os.environ.get("MAXWHITE"):
    for l_ in list(bsdf.inputs["Emission Color"].links) + list(bsdf.inputs["Emission Strength"].links):
        film_mat.node_tree.links.remove(l_)
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.97, 0.92, 1)      # NW white, ~4000 K
    bsdf.inputs["Emission Strength"].default_value = MAX_STRENGTH * float(os.environ.get("MAXSCALE", "1"))

# ------------------------------------------------------------------ walls (world): origin on the wall surface, u axis, inward normal
WALLS = {
    # name: (wall object, origin, u axis, normal, u range, z range)
    "west":    ("Walls.001", Vector((-6.92, -4.77, 0)), Vector((0, 1, 0)), Vector((1, 0, 0)), (-7.2, -0.06), (0.9, 3.30)),
    "picture": ("Wc2", Vector((-6.92, -4.77, 0)), Vector((1, 0, 0)), Vector((0, -1, 0)), (0.06, 6.22), (0.9, 3.30)),
    "stair":   ("Wc2", Vector((-0.68, -4.77, 0)), Vector((0, 1, 0)), Vector((1, 0, 0)), (0.04, 2.15), (0.35, 3.30)),
    "kitchen": ("Cube.007", Vector((0, 10.96, 0)), Vector((1, 0, 0)), Vector((0, -1, 0)), (-6.8, 6.8), (3.65, 6.95)),
}


def wall_point(w, u, v):
    _, o, U, n, _, _ = WALLS[w]
    return o + U * u + Vector((0, 0, v))


def bare_wall(w, u, v):
    """True when the wall at (u, v) is bare: a ray from 0.3 m in front meets the wall object itself, flat on."""
    obj, o, U, n, _, _ = WALLS[w]
    p = wall_point(w, u, v) + n * 0.3
    hit, loc, nor, idx, ob, _ = scene.ray_cast(dg, p, -n, distance=0.4)
    if not hit or ob.name != obj or nor.dot(n) < 0.95:
        return False
    return abs((p - loc).length - 0.3) < 0.02


# The wide camera looks at the kitchen wall past the mezzanine floor's edge, which cuts across it: panels there must be
# in plain view from both ends of the camera move, or they look as if they ran through the ceiling.
CAM0 = scene.objects["Camera.008"]
DOLLY, RISE = 1.1, 0.12
_fwd = (CAM0.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
VIEW_PTS = [CAM0.location.copy(), CAM0.location + _fwd * DOLLY + Vector((0, 0, RISE))]
SEEN_FROM = {"kitchen"}


def big(ob):
    """Occluders are objects at least 0.5 m in two directions (slabs, walls, furniture), not lamp cables or shades."""
    d = sorted(ob.dimensions, reverse=True)
    return d[1] > 0.5


def in_view(w, u, v):
    _, _, _, n, _, _ = WALLS[w]
    p0 = wall_point(w, u, v) + n * 0.05
    for eye in VIEW_PTS:
        p, todo = p0, (eye - p0).length
        d = (eye - p0).normalized()
        for _ in range(12):
            hit, loc, nor, idx, ob, _ = scene.ray_cast(dg, p, d, distance=todo)
            if not hit:
                break
            if big(ob):
                return False
            step = (loc - p).length + 1e-3
            p, todo = p + d * step, todo - step
    return True


# ------------------------------------------------------------------ triangular lattice and cluster growth
A1, A2 = Vector((L, 0)), Vector((L / 2, L * math.sqrt(3) / 2))


def vtx(i, j):
    return A1 * i + A2 * j


def cverts(c):
    i, j, k = c
    return [(i, j), (i + 1, j), (i, j + 1)] if k == 0 else [(i + 1, j), (i + 1, j + 1), (i, j + 1)]


def nbrs(c):
    i, j, k = c
    return [(i, j - 1, 1), (i - 1, j, 1), (i, j, 1)] if k == 0 else [(i, j, 0), (i + 1, j, 0), (i, j + 1, 0)]


def hex_cells(i, j):
    return [(i, j, 0), (i - 1, j, 0), (i, j - 1, 0), (i - 1, j, 1), (i - 1, j - 1, 1), (i, j - 1, 1)]


def cell_ok(w, c, cache):
    if c in cache:
        return cache[c]
    _, _, _, _, (u0, u1), (z0, z1) = WALLS[w]
    pts = [vtx(*p) for p in cverts(c)]
    ctr = sum(pts, Vector((0, 0))) / 3
    ok = all(u0 <= p.x <= u1 and z0 <= p.y <= z1 for p in pts)
    if ok:   # sample the corners (pulled 8 mm in) and the centre
        smp = [p + (ctr - p).normalized() * 0.008 for p in pts] + [ctr]
        ok = all(bare_wall(w, q.x, q.y) for q in smp) and (w not in SEEN_FROM or all(in_view(w, q.x, q.y + 0.25) for q in smp))   # 0.25 m clear of the mezzanine edge in view
    cache[c] = ok
    return ok


def grow(w, seed_uv, n_target, rng, ribbon, spread=3.0, hex_w=1.3, band=0.16):
    cache = {}
    j = round(seed_uv[1] / A2.y)
    i = round((seed_uv[0] - j * A2.x) / L)
    if not all(cell_ok(w, c, cache) for c in hex_cells(i, j)):     # nearest lattice vertex that seats a whole hexagon
        near = sorted(((i + di, j + dj) for di in range(-40, 41) for dj in range(-30, 31)),
                      key=lambda q: (vtx(*q) - Vector(seed_uv)).length)
        i, j = next(q for q in near if all(cell_ok(w, c, cache) for c in hex_cells(*q)))
        seed_uv = tuple(vtx(i, j))
        print("seed", w, "moved to", tuple(round(x, 2) for x in seed_uv))
    occ, panels = set(hex_cells(i, j)), [("hex", (i, j))]
    while len(panels) < n_target:
        cand = {}
        for c in occ:
            for nb in nbrs(c):
                if nb in occ:
                    continue
                cand[("tri", nb)] = [nb]
                for p in cverts(nb):
                    hc = hex_cells(*p)
                    if not any(x in occ for x in hc):
                        cand[("hex", p)] = hc
        cand = {k: v for k, v in cand.items() if all(cell_ok(w, c, cache) for c in v)}
        if not cand:
            break
        keys = list(cand)

        def weight(k):
            cells = cand[k]
            cu = sum(vtx(*p).x for c in cells for p in cverts(c)) / (3 * len(cells))
            cv = sum(vtx(*p).y for c in cells for p in cverts(c)) / (3 * len(cells))
            return (hex_w if k[0] == "hex" else 1.0) * math.exp(-((cv - ribbon(cu)) / band) ** 2) * \
                math.exp(spread * abs(cu - seed_uv[0])) + 0.01
        k = rng.choices(keys, weights=[weight(k) for k in keys])[0]
        occ.update(cand[k])
        panels.append(k)
    return panels


def place(w, panels):
    _, o, U, n, _, _ = WALLS[w]
    R3 = Matrix((U, Vector((0, 0, 1)), n)).transposed()        # columns: panel x, y, z in the world
    for idx, (kind, key) in enumerate(panels):
        if kind == "hex":
            c2, rot, body, film = vtx(*key), 0.0, HEX_BODY, HEX_FILM
        else:
            c2 = sum((vtx(*p) for p in cverts(key)), Vector((0, 0))) / 3
            rot, body, film = (0.0 if key[2] == 0 else math.pi), TRI_BODY, TRI_FILM
        M = Matrix.Translation(wall_point(w, c2.x, c2.y) + n * STANDOFF) @ R3.to_4x4() @ Matrix.Rotation(rot, 4, "Z")
        for me, tag in ((body, "body"), (film, "film")):
            ob = bpy.data.objects.new(f"{w} {kind} {idx} {tag}", me)
            ob.matrix_world = M
            panels_col.objects.link(ob)


rng = random.Random(11)
layout = {
    # west wall: from the corner past the TV's right edge, then a ribbon over the TV
    "west": grow("west", (-0.35, 2.05), 150, rng, lambda u: 2.05 + 0.85 * (1 - math.exp(min(0.0, u + 0.9) * 1.1)), band=0.24),
    # painting wall: from the same corner, over the painting, down the far side
    "picture": grow("picture", (0.35, 2.05), 230, rng, lambda u: 2.05 + 0.9 * math.sin(min(u, 5.0) / 5.0 * math.pi) ** 0.6),   # back to 2.05 at the outside corner, where the stair-wall ribbon starts
    # stair-side wall: picks the ribbon up round the outside corner and runs it down and back
    "stair": grow("stair", (0.25, 2.05), 85, rng, lambda u: 2.05 - 0.55 * u, band=0.22),
    # double-height kitchen wall: a large high cluster
    "kitchen": grow("kitchen", (-2.4, 5.2), 280, rng, lambda u: 5.2 + 0.55 * math.sin((u + 2.4) * 1.1), spread=0.9, band=0.42),
}
for w, p in layout.items():
    place(w, p)
    print("panels", w, len(p), "hex", sum(1 for k in p if k[0] == "hex"))

# ------------------------------------------------------------------ room light: LIGHT=day | evening (default) | night
PRESET = {"day": (1.0, 1.0), "evening": (0.18, 0.2), "night": (0.0, 0.02)}[os.environ.get("LIGHT", "evening")]
DIM = float(os.environ.get("DIM", PRESET[0]))
for o in scene.objects:
    if o.type == "LIGHT":
        o.data.energy *= DIM
if scene.world and scene.world.use_nodes:
    for nd in scene.world.node_tree.nodes:
        if nd.type == "BACKGROUND":
            nd.inputs["Strength"].default_value *= float(os.environ.get("WORLD", PRESET[1]))
if os.environ.get("VIEW"):          # e.g. VIEW="AgX|AgX - Punchy|-0.6"
    vt, lk, ex = os.environ["VIEW"].split("|")
    scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure = vt, lk, float(ex)
print("view", scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure)

# ------------------------------------------------------------------ camera
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = RES_X, RES_Y, 100
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, max(1, NUM if MODE == "video" else 1)


def ease(cam_or_obj):
    for fc in cam_or_obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "SINE"
            kp.easing = "EASE_IN_OUT"


if SHOT == "wide":                     # the scene's Camera.008, slow push-in for the video
    cam = CAM0
    if MODE == "video" and not os.environ.get("STATIC"):
        p0, r0 = cam.location.copy(), cam.rotation_euler.copy()
        cam.keyframe_insert("location", frame=1)
        cam.keyframe_insert("rotation_euler", frame=1)
        cam.location = VIEW_PTS[1]
        cam.rotation_euler = (r0.x + 0.03, r0.y, r0.z + 0.08)
        cam.keyframe_insert("location", frame=NUM)
        cam.keyframe_insert("rotation_euler", frame=NUM)
        ease(cam)
else:                                  # close-up: the outside corner where the ribbon wraps onto the stair-side wall
    corner = Vector((-0.68, -4.77, 0))
    target = bpy.data.objects.new("Close-up target", None)
    scene.collection.objects.link(target)
    target.location = (-0.78, -4.35, 1.72)
    cd = bpy.data.cameras.new("Close-up")
    cd.lens, cd.sensor_width = 32, 36
    cd.dof.use_dof, cd.dof.focus_object, cd.dof.aperture_fstop = True, target, float(os.environ.get("FSTOP", "4"))
    cam = bpy.data.objects.new("Close-up", cd)
    scene.collection.objects.link(cam)
    tc = cam.constraints.new("TRACK_TO")
    tc.target, tc.track_axis, tc.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"

    def orbit(az_deg, r, z):
        a = math.radians(az_deg)
        return corner + Vector((r * math.cos(a), r * math.sin(a), z))
    if MODE == "video":                # a slow arc round the corner, from the painting wall's side to the stair wall's
        cam.location = orbit(-64, 2.0, 1.62)
        cam.keyframe_insert("location", frame=1)
        cam.location = orbit(-26, 1.75, 1.82)
        cam.keyframe_insert("location", frame=NUM)
        ease(cam)
    else:
        cam.location = orbit(-45, 1.85, 1.7)
scene.camera = cam
if MODE != "video":
    scene.frame_set(int(FPS * float(os.environ.get("T", "3.2"))))
if MODE == "video" and os.environ.get("RANGE"):      # test a slice of the move, e.g. RANGE=120-131
    scene.frame_start, scene.frame_end = (int(x) for x in os.environ["RANGE"].split("-"))

# ------------------------------------------------------------------ output look: dither (no banding in the dark gradients), soft bloom
scene.render.dither_intensity = 1.0
scene.use_nodes = True
ct = scene.node_tree
for n_ in list(ct.nodes):
    ct.nodes.remove(n_)
rl, comp = ct.nodes.new("CompositorNodeRLayers"), ct.nodes.new("CompositorNodeComposite")
glare = ct.nodes.new("CompositorNodeGlare")
glare.glare_type, glare.quality, glare.threshold, glare.size = "FOG_GLOW", "HIGH", float(os.environ.get("BLOOM_T", "0.9")), 7
glare.mix = float(os.environ.get("BLOOM_MIX", "-0.65"))
ct.links.new(rl.outputs["Image"], glare.inputs["Image"])
ct.links.new(glare.outputs["Image"], comp.inputs["Image"])

# ------------------------------------------------------------------ Cycles on the GPU
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"
scene.cycles.samples = NUM if MODE == "still" else int(os.environ.get("SPP", "160"))
scene.cycles.use_denoising = True
# Video flicker (user 2026-11-21): per-frame denoising of a low-sample image shimmers on the dim, indirectly lit walls.
# More samples, OIDN in its accurate mode (steadier than OptiX), clamped indirect light and blurred glossy bounces all
# cut the frame-to-frame noise the denoiser has to guess at.
scene.cycles.denoiser = os.environ.get("DENOISER", "OPENIMAGEDENOISE")
if scene.cycles.denoiser == "OPENIMAGEDENOISE":
    scene.cycles.denoising_prefilter = "ACCURATE"
    scene.cycles.denoising_quality = "HIGH"
    scene.cycles.denoising_use_gpu = True
scene.cycles.adaptive_threshold = float(os.environ.get("ADAPT", "0.005"))
scene.cycles.sample_clamp_indirect = float(os.environ.get("CLAMP", "2.0"))
scene.cycles.blur_glossy = 1.0
scene.cycles.caustics_reflective = scene.cycles.caustics_refractive = False
scene.cycles.seed = 0
scene.cycles.use_animated_seed = False
scene.render.use_persistent_data = True

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
if MODE == "blend":
    bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=True)
elif MODE == "video":
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.filepath = OUT
    bpy.ops.render.render(animation=True)
else:
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
print("wrote", OUT)
