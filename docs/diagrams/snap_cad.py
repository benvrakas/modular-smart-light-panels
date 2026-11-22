"""Snapshots of the current SolidCraft CAD for the explainers, with solidcraft-cli (headless, below-normal priority).

python snap_cad.py [name ...]   ->  mechanical/solidcraft/png/<name>.png
Parts open in their saved configuration (Triangle, the rev A test model).
"""
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SC = os.path.join(ROOT, "mechanical", "solidcraft")
CLI = r"C:\Program Files\SolidCraft\solidcraft-cli.exe"
BELOW_NORMAL = 0x00004000

# name: (design file, view, width, height)
SHOTS = {
    "assembly_front": ("panel_assembly.sc", "iso", 1800, 1100),
    "assembly_back": ("panel_assembly.sc", "bottom", 1800, 1100),
    "back_plate_triangle": ("back_plate.sc", "iso", 1400, 1000),
    "back_plate_triangle_back": ("back_plate.sc", "bottom", 1400, 1000),
    "frame_triangle": ("frame.sc", "iso", 1400, 1000),
    "bridge_clip": ("bridge_clip.sc", "iso", 1400, 900),
    "edge_cover": ("edge_cover.sc", "iso", 1400, 900),
    "bezel_triangle": ("diffuser.sc", "iso", 1400, 1000),
    "edge_board_standin": ("edge_board_standin.sc", "iso", 1600, 700),
    "bridge_standin": ("bridge_standin.sc", "iso", 1400, 800),
}
# Sections across the seam between hexagons A and B (seam along x at y -86.6; controller sides facing), looking along the
# seam from the +x side (yaw -pi/2) at the cut: (plane x, camera target z, distance)
SECTIONS = {
    "section_seam_spring": (2.5, 5.6, 46),     # through a bridge spring: boards, springs, bridge, clip keys, controller joint
    "section_seam_tooth": (23.0, 0.5, 26),     # through a clip tooth in its back-plate notch
    "section_seam_hook": (33.0, 1.0, 30),      # through a frame snap leg hooked under the back-plate tab
}


def snap(name):
    design, view, w, h = SHOTS[name]
    out = os.path.join(SC, "png", name + ".png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [CLI, "snapshot", "--in", os.path.join(SC, design), "--out", out, "--width", str(w), "--height", str(h),
           "--view", view, "--no-grid", "--no-axes", "--quality", "fine"]
    r = subprocess.run(cmd, capture_output=True, text=True, creationflags=BELOW_NORMAL)
    ok = r.returncode == 0 and os.path.exists(out)
    if ok:
        autocrop(out)
    print(name, "ok" if ok else f"FAILED {r.returncode} {(r.stderr or r.stdout)[-300:]}")


def section(name):
    x, z, dist = SECTIONS[name]
    out = os.path.join(SC, "png", name + ".png")
    cam = '{"target":[%s,-86.6,%s],"yaw":-1.5708,"pitch":0.0,"distance":%s}' % (x, z, dist)
    cmd = [CLI, "snapshot", "--in", os.path.join(SC, "panel_assembly.sc"), "--out", out, "--width", "1600", "--height", "1000",
           "--section", f"x={x}", "--camera", cam, "--no-grid", "--no-axes", "--quality", "fine"]
    r = subprocess.run(cmd, capture_output=True, text=True, creationflags=BELOW_NORMAL)
    print(name, "ok" if r.returncode == 0 and os.path.exists(out) else f"FAILED {r.returncode} {(r.stderr or r.stdout)[-300:]}")


def autocrop(path, margin=0.06):
    """Crop to the model: the background is a vertical gradient, so compare each pixel with its row's edge colour."""
    from PIL import Image, ImageChops
    im = Image.open(path).convert("RGB")
    w, h = im.size
    edge = im.crop((0, 0, 6, h)).resize((1, h)).resize((w, h))
    diff = ImageChops.difference(im, edge).convert("L").point(lambda v: 255 if v > 14 else 0)
    bb = diff.getbbox()
    if not bb:
        return
    mx, my = int((bb[2] - bb[0]) * margin) + 10, int((bb[3] - bb[1]) * margin) + 10
    im.crop((max(0, bb[0] - mx), max(0, bb[1] - my), min(w, bb[2] + mx), min(h, bb[3] + my))).save(path)


if __name__ == "__main__":
    for n in [a for a in sys.argv[1:]] or list(SHOTS) + list(SECTIONS):
        section(n) if n in SECTIONS else snap(n)
