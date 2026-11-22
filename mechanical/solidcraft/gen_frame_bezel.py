"""SolidCraft build scripts for frame.sc and diffuser.sc (bezel), every outline driven by n_sides."""
import json, sys

T = "180 deg/n_sides"
A = f"({T} - 90 deg)"          # direction of the side-0 corner at +x


DETENT = [   # bezel bump / frame dimple (user 2026-11-22: snap detents replace the corner pins; PETG flex, no arms)
    ("det_h", "0.75 mm", "Detent bump height from the flange's inner face: 0.15 fit gap + 0.6 mm engagement (user 2026-11-22: 0.3 was too small, 1.0 too big)."),
    ("det_top", "0.3 mm", "Flat top of the bump; both faces are 45 deg (snaps on and pulls off, prints without support)."),
    ("det_len", "10 mm", "Bump length along the side (one per side, at mid-side, where the flange flexes most)."),
    ("det_zc", "1.1 mm", "Bump centre above the flange's bottom edge: the bump spans 0.2 .. 2.0 mm of the 3 mm flange."),
]


def doc(path):
    """The saved design: rebuilds delete whatever features it has and add or change parameters as needed."""
    import os, zipfile
    here = os.path.dirname(os.path.abspath(__file__))
    return json.loads(zipfile.ZipFile(os.path.join(here, path)).read("document.json"))


class Script:
    def __init__(self, existing=()):
        self.s = []
        self.existing = set(existing)

    def c(self, cmd, **p):
        if cmd == "parameters.delete":
            if p["name"] not in self.existing:
                return
            self.existing.discard(p["name"])
        self.s.append({"command": cmd, "params": p})

    def param(self, name, expr, comment=None, new=False):
        """Engine commands as solidcraft-cli runs them (set_parameter is an MCP-only alias)."""
        self.c("parameters.change" if name in self.existing else "parameters.add", name=name, expression=expr)
        self.existing.add(name)
        if comment:
            self.c("parameters.comment", name=name, comment=comment)

    def sketch(self, name, plane, offset, pts):
        p = {"plane": plane, "name": name}
        if offset is not None:
            p["offset"] = offset
        self.c("sketch.create", **p)
        self.c("sketch.line", closed=True, points=pts)
        self.c("sketch.finish")

    def pattern(self, name, feats):
        self.c("solid.pattern.circular", name=name, features=feats, axis="Z", count="n_sides")

    def segment(self, sk, feat, r_out, r_in, z, dist, op, **kw):
        """One side's mitred ring segment between inradius r_in and r_out (exact outline, no blank to trim)."""
        self.sketch(sk, "XY", z, [[f"-({r_out})*tan({T})", f"-({r_out})"], [f"({r_out})*tan({T})", f"-({r_out})"],
                                   [f"({r_in})*tan({T})", f"-({r_in})"], [f"-({r_in})*tan({T})", f"-({r_in})"]])
        self.c("solid.extrude", sketch=sk, operation=op, distance=dist, name=feat, **kw)

    def sector(self, sk, feat, r, z, dist, op, **kw):
        """One side's sector of a regular n-gon (centre to the side at inradius r)."""
        self.sketch(sk, "XY", z, [[0, 0], [f"({r})*tan({T})", f"-({r})"], [f"-({r})*tan({T})", f"-({r})"]])
        self.c("solid.extrude", sketch=sk, operation=op, distance=dist, name=feat, **kw)



SHAPES = (("Hexagon", "6"), ("Square", "4"), ("Triangle", "3"))


def flange_rows(S, D, short, full):
    """Configuration rows: each shape with the 3 mm flange, and a 'full flange' row whose flange runs the whole outer
    wall (user 2026-11-22: no seam line around the panel's side). short/full map parameter -> cell expression."""
    have = {c.get("param") for c in D["configs"]["columns"]}
    new = [k for k in short if k not in have]
    if new:
        S.c("config.configure", params=new)
    for name, n in SHAPES:
        S.c("config.row", name=name, values={"param:n_sides": n} | {f"param:{k}": v for k, v in short.items()})
        S.c("config.row", name=f"{name} full flange", values={"param:n_sides": n} | {f"param:{k}": v for k, v in full.items()})
    S.c("config.activate", row="Triangle")

# ------------------------------------------------------------------ frame
FD = doc("frame.sc")
F = Script(p["name"] for p in FD["params"])
F.c("timeline.delete", features=[f["id"] for f in FD["features"]])
F.param("fl_t", "1 mm", "Bezel flange thickness (user 2026-11-22: L-section bezel for stiffness).", new=True)
F.param("fl_h", "3 mm", "Bezel flange depth below the bezel's underside: 3 mm, or the whole outer wall in the full-flange rows.", new=True)
F.param("rebate_w", "fl_t + 0.15 mm", "Step cut into the frame's outer top edge for the bezel flange (flange + loose fit).", new=True)
F.param("rebate_bot", "cap_bot + cap_t - fl_h", "Step floor at its inner edge (0.2 mm below the flange end).", new=True)
F.param("rebate_slope", "20 deg", "Step floor slope from horizontal: the 70 deg overhang limit, since the frame prints cap-down (user 2026-11-22). 0 in the full-flange rows, where the step runs out at the wall bottom.", new=True)
F.c("parameters.delete", name="pin_hole_d")
F.c("parameters.delete", name="pin_hole_h")
for nm, ex, cm in DETENT:
    F.param(nm, ex, cm, new=True)
F.param("det_dim", "det_h - (rebate_w - fl_t) + 0.1 mm", "Dimple depth in the step wall: the bump's reach past the fit gap + 0.1 mm clearance.", new=True)
TOP = "cap_bot + cap_t"
# rings built directly from exact per-side segments (CLAUDE.md: no oversized blank trimmed back)
F.segment("CapSketch", "Cap", "Ao", "lip_out - lip_w", "cap_bot", "cap_t", "new", body_name="Frame")
F.segment("WallSketch", "Wall", "Ao", "w_in", "z_skirt", "cap_bot - z_skirt", "join")
# step for the bezel flange: per side, through-all along the side, so neighbouring steps mitre at the corners
F.sketch("RebateSketch", "YZ", None, [["-(Ao - rebate_w)", TOP], ["-(Ao - rebate_w)", "rebate_bot"],
                                       ["-Ao", "rebate_bot - rebate_w*tan(rebate_slope)"], ["-Ao", TOP]])
F.c("solid.extrude", sketch="RebateSketch", operation="cut", direction="symmetric", through_all=True, name="Flange step")
# detent dimples: one per side at mid-side, 45 deg faces from the step wall (prints cap-down without support),
# 0.1 mm larger than the bump all round
YW, YF = "-(Ao - rebate_w)", "-(Ao - rebate_w - det_dim)"
ZC = f"({TOP} + 0.2 mm - fl_h + det_zc)"
HF = "(det_top/2 + 0.1 mm)"
F.sketch("DimpleSketch", "YZ", "-(det_len/2 + 0.1 mm)", [
    [YW, f"{ZC} - {HF} - det_dim"], [YF, f"{ZC} - {HF}"], [YF, f"{ZC} + {HF}"], [YW, f"{ZC} + {HF} + det_dim"]])
F.c("solid.extrude", sketch="DimpleSketch", operation="cut", distance="det_len + 0.2 mm", name="Detent dimple")
# lip: one mitred segment per side (a closed ring once patterned)
F.sketch("LipSketch", "XY", "lip_bot", [
    [f"-lip_out*tan({T})", "-lip_out"], [f"lip_out*tan({T})", "-lip_out"],
    [f"(lip_out - lip_w)*tan({T})", "-(lip_out - lip_w)"], [f"-(lip_out - lip_w)*tan({T})", "-(lip_out - lip_w)"]])
F.c("solid.extrude", sketch="LipSketch", operation="join", distance="cap_bot - lip_bot", name="Lip")
LEG = [["-w_in", "z_skirt"], ["-(w_in + leg_t)", "z_skirt"], ["-(w_in + leg_t)", "leg_bot"],
       ["-(w_in + 0.2 mm)", "leg_bot"], ["-hook_tip", "leg_bot + (w_in + 0.2 mm - hook_tip)*tan(lead_slope)"],
       ["-hook_tip", "latch_z - (w_in - hook_tip)*tan(latch_slope)"], ["-w_in", "latch_z"]]
# snap leg: modelled once on the +x half of side 0, mirrored to -x (CAD symmetry rule)
F.sketch("LegSketch", "YZ", "leg_x0", LEG)
F.c("solid.extrude", sketch="LegSketch", operation="join", distance="leg_len", name="Leg")
F.c("solid.mirror", name="Leg mirror", features=["Leg"], plane="YZ")
F.pattern("Sides xN", ["Cap", "Wall", "Flange step", "Detent dimple", "Lip", "Leg", "Leg mirror"])
# corner solder reliefs: one mitred cut per side, ending on the corner bisector, so neighbouring
# reliefs meet exactly at any corner angle (straight boxes crossed and poked out at the triangle's 60 deg corners)
si, so = "w_in", "(w_in + strap_relief_d)"     # from the wall's inner face, from its bottom face
F.sketch("StrapReliefSketch", "XY", "z_skirt", [
    ["strap_relief_x0", f"-{si}"], [f"{si}*tan({T})", f"-{si}"],
    [f"{so}*tan({T})", f"-{so}"], ["strap_relief_x0", f"-{so}"]])
F.c("solid.extrude", sketch="StrapReliefSketch", operation="cut",
    distance="strap_relief_top - z_skirt", name="Strap relief")
F.c("solid.mirror", name="Strap relief mirror", features=["Strap relief"], plane="YZ")
F.pattern("Strap reliefs xN", ["Strap relief", "Strap relief mirror"])
flange_rows(F, FD, {"fl_h": "3 mm", "rebate_slope": "20 deg"}, {"fl_h": "cap_bot + cap_t - z_skirt", "rebate_slope": "0 deg"})
F.c("inspect.measure", summary=True)

# ------------------------------------------------------------------ bezel
BD = doc("diffuser.sc")
B = Script(p["name"] for p in BD["params"])
B.c("timeline.delete", features=[f["id"] for f in BD["features"]])     # bezel and film are both rebuilt
for nm in ("pin_r", "pin_d", "pin_h", "pin_hole_h", "pin_clear"):
    B.c("parameters.delete", name=nm)
for nm, ex, cm in DETENT:
    B.param(nm, ex, cm, new=True)
B.param("fl_t", "1 mm", "Flange thickness (user 2026-11-22: L-section bezel for stiffness; the frame has a matching step).", new=True)
B.param("fl_h", "3 mm", "Flange depth below the bezel's underside, down the frame's outer face (3 mm, or to 0.2 mm above the frame bottom in the full-flange rows).", new=True)
B.param("frame_bot", "7.5 mm", "Bottom of the frame's outer wall (frame.sc z_skirt): the full flange ends 0.2 mm above it, as the 3 mm one does above its step floor.", new=True)
B.param("film_inset", "1.5 mm", "Film edge inset from the outer edge: inside the flange (fl_t) with 0.35 mm to spare.")
Z0 = "cap_top + riser_h + film_t"
# film first: n-gon of join-type sectors (each copy merges with the ones it touches), film_inset inside the outer edge,
# on the frame cap, under the bezel
B.sector("FilmSketch", "Film", "Ao - film_inset", "cap_top + riser_h", "film_t", "join", body_name="Film")
B.pattern("Film xN", ["Film"])
B.c("appearance.assign", bodies=["Film"], color="#EEF1F5", opacity=0.45, name="Diffuser film")
# bezel: the plate segments start a new body; the flange joins (no target) merge the plate copies; the flange and bumps
# don't touch the film, so the film stays its own body
B.segment("BezelSketch", "Bezel plate", "Ao", "A_in", Z0, "bezel_t", "new", body_name="Bezel")
B.segment("FlangeSketch", "Flange", "Ao", "Ao - fl_t", f"{Z0} - fl_h", "fl_h", "join")
YI, YB = "-(Ao - fl_t)", "-(Ao - fl_t - det_h)"
ZB = f"({Z0} - fl_h + det_zc)"
B.sketch("BumpSketch", "YZ", "-det_len/2", [            # from the flange's inner face, 45 deg faces
    [YI, f"{ZB} - det_top/2 - det_h"], [YB, f"{ZB} - det_top/2"], [YB, f"{ZB} + det_top/2"], [YI, f"{ZB} + det_top/2 + det_h"]])
B.c("solid.extrude", sketch="BumpSketch", operation="join", distance="det_len", name="Detent bump")
B.pattern("Bezel xN", ["Bezel plate", "Flange", "Detent bump"])
flange_rows(B, BD, {"fl_h": "3 mm"}, {"fl_h": "cap_top - frame_bot"})
B.c("inspect.measure", summary=True)

out = sys.argv[1]
json.dump({"commands": F.s}, open(out + "/frame_build.json", "w"), indent=1)
json.dump({"commands": B.s}, open(out + "/bezel_build.json", "w"), indent=1)
print(len(F.s), len(B.s))
