"""Make the README-sized pictures (JPEG, 1600 px wide) from the full renders: python docs/readme/make_readme_images.py"""
import os

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.dirname(os.path.abspath(__file__))
PICS = {
    "showcase.jpg": "mechanical/solidcraft/render/out/penthouse_still.png",
    "closeup.jpg": "mechanical/solidcraft/render/out/penthouse_closeup.png",
    "max_day.jpg": "mechanical/solidcraft/render/out/penthouse_max_day.png",
    "max_night.jpg": "mechanical/solidcraft/render/out/penthouse_max_night.png",
    "assembly_front.jpg": "mechanical/solidcraft/png/assembly_front.png",
    "assembly_back.jpg": "mechanical/solidcraft/png/assembly_back.png",
    "section_seam.jpg": "mechanical/solidcraft/png/section_seam_spring.png",
    "edge_board_3d.jpg": "hardware/edge-board/output/3d/edge-board-triangle_top_iso.png",
    "controller_3d.jpg": "hardware/controller-board/output/3d/controller-board_top_iso.png",
    "bridge_3d.jpg": "hardware/bridge/output/3d/bridge_top_iso.png",
    "explainer_reference.jpg": "docs/diagrams/screenshots/design-reference.png",
    "explainer_planning.jpg": "docs/diagrams/screenshots/planning.png",
}

for name, rel in PICS.items():
    src = os.path.join(ROOT, *rel.split("/"))
    if not os.path.exists(src):
        print("missing", rel)
        continue
    im = Image.open(src)
    if im.mode in ("RGBA", "LA"):                       # transparent renders: flatten on white
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.getchannel("A"))
        im = bg
    im = im.convert("RGB")
    w = 1000 if name.startswith("explainer") else 1600
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, name), quality=85, optimize=True)
    print(name, im.size)
