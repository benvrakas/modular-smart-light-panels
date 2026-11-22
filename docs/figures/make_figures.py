"""Make the pictures in docs/figures/ from the design files. Never edit the pictures by hand: re-run this.

python docs/figures/make_figures.py            web-sized copies of the existing renders, snapshots and 3D views
python docs/figures/make_figures.py --all      first re-render the KiCad 3D views (render_boards_3d.py) and the
                                               SolidCraft snapshots and sections (snap_cad.py)
The Blender renders come from mechanical/solidcraft/render/render_batch.py (slow, GPU), so they are only copied here.
SPEC.md and the README embed these files; the written description lives only in SPEC.md and docs/decisions/.
"""
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
RO = "mechanical/solidcraft/render/out/"
SC = "mechanical/solidcraft/png/"
PICS = {
    # Blender (render_batch.py)
    "render_evening.jpg": RO + "penthouse_still.png",
    "render_closeup.jpg": RO + "penthouse_closeup.png",
    "render_max_day.jpg": RO + "penthouse_max_day.png",
    "render_max_night.jpg": RO + "penthouse_max_night.png",
    "render_max_day_closeup.jpg": RO + "penthouse_max_day_closeup.png",
    "render_max_night_closeup.jpg": RO + "penthouse_max_night_closeup.png",
    "render_fx_aurora.jpg": RO + "penthouse_fx_aurora.png",
    "render_fx_sunset.jpg": RO + "penthouse_fx_sunset.png",
    "render_fx_ocean.jpg": RO + "penthouse_fx_ocean.png",
    "render_fx_confetti.jpg": RO + "penthouse_fx_confetti.png",
    "render_fx_warm.jpg": RO + "penthouse_fx_warm.png",
    "render_fx_fire.jpg": RO + "penthouse_fx_fire.png",
    "render_vertical_corner.jpg": RO + "penthouse_vertical_corner.png",
    "render_vertical_wall.jpg": RO + "penthouse_vertical_wall.png",
    "render_vertical_inside.jpg": RO + "penthouse_vertical_inside.png",
    # SolidCraft (snap_cad.py)
    "cad_assembly_front.jpg": SC + "assembly_front.png",
    "cad_assembly_back.jpg": SC + "assembly_back.png",
    "cad_back_plate.jpg": SC + "back_plate_triangle.png",
    "cad_back_plate_back.jpg": SC + "back_plate_triangle_back.png",
    "cad_frame.jpg": SC + "frame_triangle.png",
    "cad_bezel.jpg": SC + "bezel_triangle.png",
    "cad_bridge_clip.jpg": SC + "bridge_clip.png",
    "cad_edge_cover.jpg": SC + "edge_cover.png",
    "cad_standin_edge_board.jpg": SC + "edge_board_standin.png",
    "cad_standin_bridge.jpg": SC + "bridge_standin.png",
    "section_seam_spring.jpg": SC + "section_seam_spring.png",
    "section_seam_tooth.jpg": SC + "section_seam_tooth.png",
    "section_seam_hook.jpg": SC + "section_seam_hook.png",
    # KiCad (render_boards_3d.py)
    "board_edge_triangle_top.jpg": "hardware/edge-board/output/3d/edge-board-triangle_top_iso.png",
    "board_edge_triangle_bottom.jpg": "hardware/edge-board/output/3d/edge-board-triangle_bottom_iso.png",
    "board_edge_square_top.jpg": "hardware/edge-board/output/3d/edge-board-square_top_iso.png",
    "board_edge_hex_top.jpg": "hardware/edge-board/output/3d/edge-board-hex_top_iso.png",
    "board_controller_top.jpg": "hardware/controller-board/output/3d/controller-board_top_iso.png",
    "board_controller_bottom.jpg": "hardware/controller-board/output/3d/controller-board_bottom_iso.png",
    "board_bridge_top.jpg": "hardware/bridge/output/3d/bridge_top_iso.png",
    "board_bridge_bottom.jpg": "hardware/bridge/output/3d/bridge_bottom_iso.png",
    "board_spring_coupon.jpg": "hardware/bridge/coupon/output/3d/spring-coupon_top_iso.png",
}


def web_copy(name, rel, width=1600):
    src = os.path.join(ROOT, *rel.split("/"))
    if not os.path.exists(src):
        print("missing", rel)
        return
    im = Image.open(src)
    if im.mode in ("RGBA", "LA"):                       # transparent renders: flatten on white
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.getchannel("A"))
        im = bg
    im = im.convert("RGB")
    if im.height > im.width:                            # portrait renders: same pixel budget
        width = 900
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(os.path.join(HERE, name), quality=85, optimize=True)


if __name__ == "__main__":
    if "--all" in sys.argv:
        for script in ("render_boards_3d.py", "snap_cad.py"):
            subprocess.run([sys.executable, os.path.join(HERE, script)], check=True)
    for name, rel in PICS.items():
        web_copy(name, rel)
    print("figures:", len([n for n in PICS if os.path.exists(os.path.join(HERE, n))]), "of", len(PICS))
