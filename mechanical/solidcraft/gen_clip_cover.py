"""SolidCraft build scripts for bridge_clip.sc and edge_cover.sc (solidcraft-cli run SCRIPT --in FILE --save FILE).

python gen_clip_cover.py OUTDIR  ->  OUTDIR/clip_build.json, OUTDIR/cover_build.json
Each script deletes the part's current features (the parameters stay) and rebuilds it. Rules (CLAUDE.md): every
profile and extent ends exactly on the face it meets (no overshoot), and repeated features are modelled once and
mirrored or patterned.
Panel/seam coordinates: x along the seam, y across it (seam at y 0), z panel height (clip top at z_back).
"""
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def doc(path):
    return json.loads(zipfile.ZipFile(os.path.join(HERE, path)).read("document.json"))


class Script:
    def __init__(self, path):
        self.s = [{"command": "timeline.delete", "params": {"features": [f["id"] for f in doc(path)["features"]]}}]

    def c(self, cmd, **p):
        self.s.append({"command": cmd, "params": p})

    def box(self, name, center, length, width, height, op, **kw):
        self.c("solid.box", name=name, center=center, length=length, width=width, height=height, operation=op, **kw)

    def profile(self, sketch, plane, offset, pts, feat, op, distance):
        self.c("sketch.create", plane=plane, offset=offset, name=sketch)
        self.c("sketch.line", closed=True, points=pts)
        self.c("sketch.finish")
        self.c("solid.extrude", sketch=sketch, operation=op, distance=distance, name=feat)


# arm slot: from the arm root to the clip end, through the plate's thickness exactly
ARM = dict(center=["(arm_root_x + clip_L/2)/2", None, "z_back - clip_t/2"], length="clip_L/2 - arm_root_x",
           width="arm_slot", height="clip_t")
KEY = lambda sg: [[f"{sg}key_s0", "z_back"], [f"{sg}(key_s0 + key_w)", "z_back"], [f"{sg}(key_s0 + key_w)", "key_top - key_ch"],
                  [f"{sg}(key_s0 + key_w - key_ch)", "key_top"], [f"{sg}(key_s0 + key_ch)", "key_top"], [f"{sg}key_s0", "key_top - key_ch"]]
TOOTH = lambda sg: [[f"{sg}clip_W/2", "tooth_zb1"], [f"{sg}(clip_W/2 + tooth_h)", "tooth_zb1 - tooth_h*tan(tooth_lead)"],
                    [f"{sg}(clip_W/2 + tooth_h)", "tooth_zb0 + tooth_h*tan(tooth_latch)"], [f"{sg}clip_W/2", "tooth_zb0"]]

# ------------------------------------------------------------------ bridge clip (symmetric about x and y)
C = Script("bridge_clip.sc")
C.box("Clip plate", [0, 0, "z_back - clip_t/2"], "clip_L", "clip_W", "clip_t", "new", body_name="Bridge clip")
C.box("Spine", [0, 0, "(spine_top + z_back)/2"], "spine_L", "spine_w", "spine_top - z_back", "join")
C.box("Arm slot", [ARM["center"][0], "clip_W/2 - arm_w - arm_slot/2", ARM["center"][2]], ARM["length"], ARM["width"],
      ARM["height"], "cut")
C.box("Bridge slot", [0, 0, "(spine_top + bridge_bot)/2"], "bridge_L + 2*slot_clr", "bridge_t + 2*slot_clr",
      "spine_top - bridge_bot", "cut")
# fuse relief: from the slot wall to 0.1 mm past the fuse + fit, from below the fuse up through the spine top
FR_Y0, FR_Y1 = "(bridge_t/2 + slot_clr)", "(bridge_t/2 + fuse_t + fit_loose + 0.1 mm)"
C.box("Fuse relief", ["-(fuse_x0 + fuse_x1)/2", f"({FR_Y0} + {FR_Y1})/2", "(fuse_z0 - fit_loose + spine_top)/2"],
      "fuse_x1 - fuse_x0 + 2*fit_loose", f"{FR_Y1} - {FR_Y0}", "spine_top - fuse_z0 + fit_loose", "cut")
C.profile("KeySketch", "YZ", "-key_half", KEY(""), "Key", "join", "2*key_half")
C.profile("ToothSketch", "YZ", "tooth_xc - tooth_len/2", TOOTH(""), "Tooth", "join", "tooth_len")
C.c("solid.mirror", name="Mirror left-right", features=["Arm slot", "Tooth"], plane="YZ")
C.c("solid.mirror", name="Mirror front-back", features=["Arm slot", "Tooth", "Mirror left-right", "Key"], plane="XZ")
C.c("solid.pattern.circular", name="Fuse relief x2 (180 deg)", features=["Fuse relief"], axis="Z", count=2)
C.c("inspect.measure", summary=True)

# ------------------------------------------------------------------ edge cover (half a clip on the -y side, plus a pad wall)
E = Script("edge_cover.sc")
E.box("Cover plate", [0, "-(clip_W/2 + seam_gap)/2", "z_back - clip_t/2"], "clip_L", "clip_W/2 - seam_gap", "clip_t", "new",
      body_name="Edge cover")
E.box("Pad cover wall", [0, "-(seam_gap + wall_t/2)", "(wall_top + z_back)/2"], "clip_L", "wall_t", "wall_top - z_back", "join")
E.box("Arm slot", [ARM["center"][0], "-(clip_W/2 - arm_w - arm_slot/2)", ARM["center"][2]], ARM["length"], ARM["width"],
      ARM["height"], "cut")
E.profile("KeySketch", "YZ", "-key_half", KEY("-"), "Key", "join", "2*key_half")
E.profile("ToothSketch", "YZ", "tooth_xc - tooth_len/2", TOOTH("-"), "Tooth", "join", "tooth_len")
E.c("solid.mirror", name="Mirror left-right", features=["Arm slot", "Tooth"], plane="YZ")
E.c("inspect.measure", summary=True)

out = sys.argv[1]
json.dump({"commands": C.s}, open(os.path.join(out, "clip_build.json"), "w"), indent=1)
json.dump({"commands": E.s}, open(os.path.join(out, "cover_build.json"), "w"), indent=1)
print(len(C.s), len(E.s))
