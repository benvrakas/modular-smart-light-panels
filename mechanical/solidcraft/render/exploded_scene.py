"""Exploded view of one hexagon panel (Blender 4.3, Cycles), studio backdrop.

blender -b --factory-startup -P exploded_scene.py -- OUT.png [W H [SAMPLES]]   (default 2560 x 1440, 256 samples)
  EXPLODE=0 renders the assembled panel from the same camera.

Panel: render/panel_hex.glb (built by gen_panel_glb.py hex; metres, z out of the wall, side 0 = controller at -Y).
The parts separate along z in assembly order: back plate on the table, the soldered board ring (six edge boards plus
the controller, drag-soldered at 90 deg to the code-0 board; it goes into the plate as one piece), frame, diffuser
film, bezel. The camera looks from the side opposite side 0, so the controller's white face shows inside the ring.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
RES_X = int(argv[1]) if len(argv) > 1 else 2560
RES_Y = int(argv[2]) if len(argv) > 2 else 1440
SAMPLES = int(argv[3]) if len(argv) > 3 else 256
EXPLODE = float(os.environ.get("EXPLODE", "1"))
GLB = os.environ.get("GLB", os.path.join(HERE, "panel_hex.glb"))

# z lift per part (m), assembly order bottom-up
LIFT = {"Back plate": 0.0, "Controller": 0.075, "Edge board": 0.075, "Frame": 0.150, "Film": 0.222, "Bezel": 0.262}

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=GLB)
scene = bpy.context.scene


def part_of(o):
    """Name of the assembly node above a mesh ("Edge board:3" -> "Edge board"); the film is its own part."""
    if o.name.startswith("Film"):
        return "Film"
    p = o
    while p.parent is not None and p.parent.parent is not None:
        p = p.parent
    return p.name.split(":")[0]


bpy.context.view_layer.update()
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
groups = {}
for o in meshes:
    groups.setdefault(part_of(o), []).append(o)
print("parts:", {k: len(v) for k, v in groups.items()})
assert set(groups) == set(LIFT), set(groups) ^ set(LIFT)

# un-parent (keep world transforms), then lift each part
for o in meshes:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
for o in [o for o in bpy.data.objects if o.type != "MESH"]:
    bpy.data.objects.remove(o)
for name, objs in groups.items():
    for o in objs:
        o.location.z += LIFT[name] * EXPLODE
bpy.context.view_layer.update()
for name, objs in groups.items():
    zs = [(o.matrix_world @ Vector(c)).z * 1000 for o in objs for c in o.bound_box]
    print(f"z {name}: {min(zs):.1f} .. {max(zs):.1f} mm")

# ------------------------------------------------------------------ materials
film = bpy.data.materials.new("Diffuser film")
film.use_nodes = True
b = film.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.92, 0.93, 0.95, 1)
b.inputs["Roughness"].default_value = 0.35
b.inputs["Transmission Weight"].default_value = 1.0
b.inputs["Alpha"].default_value = 0.3
for o in groups["Film"]:
    o.data.materials.clear()
    o.data.materials.append(film)

petg = bpy.data.materials.new("White PETG")      # the GLB's appearance colour, with a satin print finish
petg.use_nodes = True
b = petg.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.86, 0.86, 0.84, 1)
b.inputs["Roughness"].default_value = 0.42
b.inputs["Subsurface Weight"].default_value = 0.15
b.inputs["Subsurface Radius"].default_value = (0.002, 0.002, 0.002)
for name in ("Back plate", "Frame", "Bezel"):
    for o in groups[name]:
        o.data.materials.clear()
        o.data.materials.append(petg)
        for poly in o.data.polygons:
            poly.use_smooth = False

# ------------------------------------------------------------------ studio: seamless floor, three area lights
lo = min((o.matrix_world @ Vector(c)).z for o in groups["Back plate"] for c in o.bound_box)
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, lo))
floor = bpy.context.active_object
fm = bpy.data.materials.new("Backdrop")
fm.use_nodes = True
fb = fm.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.045, 0.048, 0.055, 1)
fb.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(fm)

world = bpy.data.worlds.new("Studio")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.012, 0.013, 0.016, 1)
bg.inputs["Strength"].default_value = 1.0

centre = Vector((0, 0, lo + 0.135 * EXPLODE + 0.008))
AZ, EL = math.radians(float(os.environ.get("AZ", "118"))), math.radians(float(os.environ.get("EL", "21")))


def around(r, az_off, z):
    """A point r from the stack axis, az_off degrees from the camera's azimuth, at height z."""
    a = AZ + math.radians(az_off)
    return (r * math.cos(a), r * math.sin(a), z)


def area(name, loc, energy, size, colour=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy, d.size, d.color = energy, size, colour
    d.shape = "DISK"
    ob = bpy.data.objects.new(name, d)
    scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (centre - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


area("Key", around(1.3, 45, 1.3), 45, 1.0, (1.0, 0.97, 0.93))
area("Fill", around(1.3, -60, 0.6), 12, 1.4, (0.93, 0.96, 1.0))
area("Rim", around(1.3, 160, 0.9), 40, 0.8)

# ------------------------------------------------------------------ camera: three-quarter view, side 0 at the back
cam_d = bpy.data.cameras.new("Camera")
cam_d.lens = 70
cam_d.dof.use_dof = True
cam_d.dof.aperture_fstop = 11
cam = bpy.data.objects.new("Camera", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam
DIST = float(os.environ.get("DIST", "1.42"))
cam.location = centre + DIST * Vector((math.cos(EL) * math.cos(AZ), math.cos(EL) * math.sin(AZ), math.sin(EL)))
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
cam_d.dof.focus_distance = (centre - cam.location).length

# ------------------------------------------------------------------ render
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == kind
            scene.cycles.device = "GPU"
            print("device:", kind)
            break
    except TypeError:
        continue
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("wrote", OUT)
