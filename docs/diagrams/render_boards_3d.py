"""3D renders of the rev A boards with kicad-cli (KiCad's raytracer), for the design-reference explainer.

python render_boards_3d.py [--test] [name ...]
Writes hardware/<board>/output/3d/<name>_<view>.png: angled perspective views of each face (raytraced, high quality,
transparent background). Runs kicad-cli at below-normal CPU priority so other work (video playback) stays smooth.
"""
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CLI = r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
BELOW_NORMAL = 0x00004000

# name: (board file, output dir, zoom); views: (suffix, rotate X,Y,Z)
BOARDS = {
    "edge-board-triangle": ("hardware/edge-board/edge-board-triangle.kicad_pcb", "hardware/edge-board/output/3d", 2.0),
    "edge-board-square": ("hardware/edge-board/edge-board-square.kicad_pcb", "hardware/edge-board/output/3d", 2.0),
    "edge-board-hex": ("hardware/edge-board/edge-board-hex.kicad_pcb", "hardware/edge-board/output/3d", 2.0),
    "controller-board": ("hardware/controller-board/controller-board.kicad_pcb", "hardware/controller-board/output/3d", 1.55),
    "bridge": ("hardware/bridge/bridge.kicad_pcb", "hardware/bridge/output/3d", 1.9),
    "spring-coupon": ("hardware/bridge/coupon/spring-coupon.kicad_pcb", "hardware/bridge/coupon/output/3d", 0.95),
}
VIEWS = [("top_iso", "-50,0,28"), ("bottom_iso", "130,0,-28")]


def render(name, test=False):
    pcb, outdir, zoom = BOARDS[name]
    out = os.path.join(ROOT, *outdir.split("/"))
    os.makedirs(out, exist_ok=True)
    w, h, q = (800, 450, "basic") if test else (2400, 1350, "high")
    for suffix, rot in VIEWS:
        png = os.path.join(out, f"{name}_{suffix}{'_test' if test else ''}.png")
        cmd = [CLI, "pcb", "render", "--output", png, "--width", str(w), "--height", str(h), "--quality", q,
               "--perspective", "--rotate", " " + rot,   # leading space: kicad-cli reads "-50,..." as a flag "--zoom", str(zoom), "--floor", "--background", "transparent",
               os.path.join(ROOT, *pcb.split("/"))]
        r = subprocess.run(cmd, capture_output=True, text=True, creationflags=BELOW_NORMAL)
        ok = r.returncode == 0 and os.path.exists(png)
        if ok and not test:
            trim(png)
        print(name, suffix, "ok" if ok else f"FAILED {r.returncode} {r.stderr[-300:]}")


def trim(path, pad=24):
    """Crop the transparent margin (the board and its floor shadow stay)."""
    from PIL import Image
    im = Image.open(path)
    bb = im.getchannel("A").point(lambda a: 255 if a > 12 else 0).getbbox()
    if bb:
        w, h = im.size
        im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(w, bb[2] + pad), min(h, bb[3] + pad))).save(path)


if __name__ == "__main__":
    test = "--test" in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(BOARDS)
    for n in names:
        render(n, test)
