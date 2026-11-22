"""SolidCraft build scripts for frame.sc and diffuser.sc (bezel), every outline driven by n_sides."""
import json, sys

T = "180 deg/n_sides"
A = f"({T} - 90 deg)"          # direction of the side-0 corner at +x


DETENT = [   # bezel bump / frame dimple (user 2026-11-22: snap detents replace the corner pins; PETG flex, no arms)
    ("det_h", "0.45 mm", "Detent bump height from the flange's inner face: 0.15 fit gap + 0.3 mm engagement."),
    ("det_top", "0.3 mm", "Flat top of the bump; both faces are 45 deg (snaps on and pulls off, prints without support)."),
    ("det_len", "10 mm", "Bump length along the side (one per side, at mid-side, where the flange flexes most)."),
    ("det_zc", "0.9 mm", "Bump centre above the flange's bottom edge."),
]


class Script:
    def __init__(self):
        self.s = []

    def c(self, cmd, **p):
        self.s.append({"command": cmd, "params": p})

    def param(self, name, expr, comment=None, new=False):
        """Engine commands as solidcraft-cli runs them (set_parameter is an MCP-only alias)."""
        self.c("parameters.add" if new else "parameters.change", name=name, expression=expr)
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

    def edge_trim(self, r, z0, z1):
        far = f"-({r}/cos({T}) + 10 mm)"
        self.sketch("EdgeTrimSketch", "YZ", None, [[f"-{r}", z0], [far, z0], [far, z1], [f"-{r}", z1]])
        self.c("solid.extrude", sketch="EdgeTrimSketch", operation="cut", direction="symmetric",
               distance=f"4*{r} + 100 mm", name="Edge trim")
        self.pattern("Edge trim xN", ["Edge trim"])

    def wedge(self, sk, feat, r, z, dist, targets=None):
        self.sketch(sk, "XY", z, [[0, 0], [f"({r})*tan({T})", f"-({r})"], [f"-({r})*tan({T})", f"-({r})"]])
        extra = {"targets": targets} if targets else {}
        self.c("solid.extrude", sketch=sk, operation="cut", distance=dist, name=feat, **extra)


# ------------------------------------------------------------------ frame
F = Script()
F.c("timeline.delete", features=list(range(69, 92)))
F.param("fl_t", "1 mm", "Bezel flange thickness (user 2026-11-22: L-section bezel for stiffness).", new=True)
F.param("fl_h", "3 mm", "Bezel flange depth below the bezel's underside.", new=True)
F.param("rebate_w", "fl_t + 0.15 mm", "Step cut into the frame's outer top edge for the bezel flange (flange + loose fit).", new=True)
F.param("rebate_bot", "cap_bot + cap_t - fl_h", "Step floor at its inner edge (0.2 mm below the flange end).", new=True)
F.param("rebate_slope", "20 deg", "Step floor slope from horizontal: the 70 deg overhang limit, since the frame prints cap-down (user 2026-11-22).", new=True)
F.c("parameters.delete", name="pin_hole_d")
F.c("parameters.delete", name="pin_hole_h")
for nm, ex, cm in DETENT:
    F.param(nm, ex, cm, new=True)
F.param("det_dim", "det_h - (rebate_w - fl_t) + 0.1 mm", "Dimple depth in the step wall: the bump's reach past the fit gap + 0.1 mm clearance.", new=True)
TOP = "cap_bot + cap_t"
F.c("solid.cylinder", name="Blank", body_name="Frame", radius=f"Ao/cos({T}) + 5 mm", height=f"{TOP} - z_skirt",
    base=[0, 0, "z_skirt"])
F.edge_trim("Ao", "z_skirt - 1 mm", f"{TOP} + 1 mm")
# step for the bezel flange: per side, patterned, so the corners mitre at any angle
FAR = f"-(Ao/cos({T}) + 20 mm)"
F.sketch("RebateSketch", "YZ", None, [["-(Ao - rebate_w)", f"{TOP} + 1 mm"], ["-(Ao - rebate_w)", "rebate_bot"],
                                       ["-Ao", "rebate_bot - rebate_w*tan(rebate_slope)"], [FAR, "rebate_bot - rebate_w*tan(rebate_slope)"],
                                       [FAR, f"{TOP} + 1 mm"]])
F.c("solid.extrude", sketch="RebateSketch", operation="cut", direction="symmetric", distance="4*Ao + 100 mm", name="Flange step")
F.pattern("Flange step xN", ["Flange step"])
# detent dimples: one per side at mid-side, 45 deg faces (prints cap-down without support), 0.1 mm larger than the bump
YW, YF = "-(Ao - rebate_w)", "-(Ao - rebate_w - det_dim)"
ZC = f"({TOP} + 0.2 mm - fl_h + det_zc)"
HF = "(det_top/2 + 0.1 mm)"
F.sketch("DimpleSketch", "YZ", "-(det_len/2 + 0.1 mm)", [
    [f"{YW} - 0.2 mm", f"{ZC} - {HF} - det_dim - 0.2 mm"], [YF, f"{ZC} - {HF}"], [YF, f"{ZC} + {HF}"],
    [f"{YW} - 0.2 mm", f"{ZC} + {HF} + det_dim + 0.2 mm"]])
F.c("solid.extrude", sketch="DimpleSketch", operation="cut", distance="det_len + 0.2 mm", name="Detent dimple")
F.pattern("Detent dimples xN", ["Detent dimple"])
F.wedge("UnderCapSketch", "Under cap wedge", "w_in", "z_skirt - 1 mm", "cap_bot - z_skirt + 1 mm")
F.wedge("OpeningSketch", "Opening wedge", "lip_out - lip_w", "z_skirt - 1 mm", f"{TOP} - z_skirt + 2 mm")
F.pattern("Inside xN", ["Under cap wedge", "Opening wedge"])
# lip: one mitred segment per side (a closed ring once patterned)
F.sketch("LipSketch", "XY", "lip_bot", [
    [f"-lip_out*tan({T})", "-lip_out"], [f"lip_out*tan({T})", "-lip_out"],
    [f"(lip_out - lip_w)*tan({T})", "-(lip_out - lip_w)"], [f"-(lip_out - lip_w)*tan({T})", "-(lip_out - lip_w)"]])
F.c("solid.extrude", sketch="LipSketch", operation="join", distance="cap_bot - lip_bot", name="Lip")
LEG = [["-w_in", "z_skirt + 0.1 mm"], ["-(w_in + leg_t)", "z_skirt + 0.1 mm"], ["-(w_in + leg_t)", "leg_bot"],
       ["-(w_in + 0.2 mm)", "leg_bot"], ["-hook_tip", "leg_bot + (w_in + 0.2 mm - hook_tip)*tan(lead_slope)"],
       ["-hook_tip", "latch_z - (w_in - hook_tip)*tan(latch_slope)"], ["-w_in", "latch_z"]]
F.sketch("LegSketchR", "YZ", "leg_x0", LEG)
F.c("solid.extrude", sketch="LegSketchR", operation="join", distance="leg_len", name="Leg R")
F.sketch("LegSketchL", "YZ", "-(leg_x0 + leg_len)", LEG)
F.c("solid.extrude", sketch="LegSketchL", operation="join", distance="leg_len", name="Leg L")
F.pattern("Sides xN", ["Lip", "Leg R", "Leg L"])
# corner solder reliefs: one mitred cut per side, ending on the corner bisector, so neighbouring
# reliefs meet exactly at any corner angle (straight boxes crossed and poked out at the triangle's 60 deg corners)
for side, sgn in (("R", ""), ("L", "-")):
    si, so = "(w_in - 0.5 mm)", "(w_in + strap_relief_d)"
    F.sketch(f"StrapReliefSketch{side}", "XY", "z_skirt - 0.1 mm", [
        [f"{sgn}strap_relief_x0", f"-{si}"], [f"{sgn}{si}*tan({T})", f"-{si}"],
        [f"{sgn}{so}*tan({T})", f"-{so}"], [f"{sgn}strap_relief_x0", f"-{so}"]])
    F.c("solid.extrude", sketch=f"StrapReliefSketch{side}", operation="cut",
        distance="strap_relief_top - z_skirt + 0.1 mm", name=f"Strap relief {side}")
F.pattern("Strap reliefs xN", ["Strap relief R", "Strap relief L"])
F.c("inspect.measure", summary=True)

# ------------------------------------------------------------------ bezel
B = Script()
B.c("timeline.delete", features=list(range(10, 19)) + [26, 27])      # bezel and the film's pin holes; the film stays
for nm in ("pin_r", "pin_d", "pin_h", "pin_hole_h", "pin_clear"):
    B.c("parameters.delete", name=nm)
for nm, ex, cm in DETENT:
    B.param(nm, ex, cm, new=True)
B.param("fl_t", "1 mm", "Flange thickness (user 2026-11-22: L-section bezel for stiffness; the frame has a matching step).", new=True)
B.param("fl_h", "3 mm", "Flange depth below the bezel's underside, down the frame's outer face.", new=True)
B.param("film_inset", "1.5 mm", "Film edge inset from the outer edge: inside the flange (fl_t) with 0.35 mm to spare.")
Z0 = "cap_top + riser_h + film_t"
B.c("solid.cylinder", name="Blank", body_name="Bezel", radius=f"Ao/cos({T}) + 5 mm", height="bezel_t + fl_h",
    base=[0, 0, f"{Z0} - fl_h"])
B.edge_trim("Ao", f"{Z0} - fl_h - 1 mm", f"{Z0} + bezel_t + 1 mm")
B.wedge("FlangeSketch", "Flange inside", "Ao - fl_t", f"{Z0} - fl_h - 1 mm", "fl_h + 1 mm", targets=["Bezel"])   # not the film
B.wedge("OpeningSketch", "Opening wedge", "A_in", f"{Z0} - 1 mm", "bezel_t + 2 mm", targets=["Bezel"])
B.pattern("Opening xN", ["Flange inside", "Opening wedge"])
YI, YB = "-(Ao - fl_t)", "-(Ao - fl_t - det_h)"
ZB = f"({Z0} - fl_h + det_zc)"
B.sketch("BumpSketch", "YZ", "-det_len/2", [
    [f"{YI} - 0.2 mm", f"{ZB} - det_top/2 - det_h - 0.2 mm"], [YB, f"{ZB} - det_top/2"], [YB, f"{ZB} + det_top/2"],
    [f"{YI} - 0.2 mm", f"{ZB} + det_top/2 + det_h + 0.2 mm"]])
B.c("solid.extrude", sketch="BumpSketch", operation="join", distance="det_len", name="Detent bump", targets=["Bezel"])
B.pattern("Detent bumps xN", ["Detent bump"])
B.c("inspect.measure", summary=True)

out = sys.argv[1]
json.dump({"commands": F.s}, open(out + "/frame_build.json", "w"), indent=1)
json.dump({"commands": B.s}, open(out + "/bezel_build.json", "w"), indent=1)
print(len(F.s), len(B.s))
