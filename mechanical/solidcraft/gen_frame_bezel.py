"""SolidCraft build scripts for frame.sc and diffuser.sc (bezel), every outline driven by n_sides."""
import json, sys

T = "180 deg/n_sides"
A = f"({T} - 90 deg)"          # direction of the side-0 corner at +x


class Script:
    def __init__(self):
        self.s = []

    def c(self, cmd, **p):
        self.s.append({"command": cmd, "params": p})

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

    def wedge(self, sk, feat, r, z, dist):
        self.sketch(sk, "XY", z, [[0, 0], [f"({r})*tan({T})", f"-({r})"], [f"-({r})*tan({T})", f"-({r})"]])
        self.c("solid.extrude", sketch=sk, operation="cut", distance=dist, name=feat)


# ------------------------------------------------------------------ frame
F = Script()
F.c("timeline.delete", features=list(range(48, 69)))
F.c("set_parameter", name="n_sides", value="6", unit="", comment="Number of panel sides: 6 hexagon, 4 square, 3 triangle.")
F.c("set_parameter", name="As", value=f"edge_L / (2 * tan({T}))")
F.c("set_parameter", name="L_board", value=f"edge_L - 2*(seam_d + board_t)*tan({T})",
    comment="Edge-board length on its inward face (decision 0004).")
F.c("set_parameter", name="latch_z", value="-2.3 mm", comment="Latch plane: the back plate's hook-pocket ceiling (user 2026-11-21: more engagement).")
F.c("set_parameter", name="hook_tip", value="Ae - 1.3 mm", comment="Hook tip, 1.2 mm under the back-plate tab (tab edge at Ae - 0.1).")
F.c("set_parameter", name="lead_slope", value="35 deg", comment="Hook lead-in face from horizontal.")
F.c("set_parameter", name="leg_bot", value="latch_z - (w_in - hook_tip)*tan(latch_slope) - 0.1 mm - (w_in + 0.2 mm - hook_tip)*tan(lead_slope)",
    comment="Leg bottom, from the hook geometry (stays above the back plane z -4.3).")
TOP = "cap_bot + cap_t"
F.c("solid.cylinder", name="Blank", body_name="Frame", radius=f"Ao/cos({T}) + 5 mm", height=f"{TOP} - z_skirt",
    base=[0, 0, "z_skirt"])
F.edge_trim("Ao", "z_skirt - 1 mm", f"{TOP} + 1 mm")
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
PR = f"(Ao + lip_out - lip_w)/2/cos({T})"
F.c("solid.cylinder", name="Pin hole", operation="cut", radius="pin_hole_d/2", height="pin_hole_h + 0.5 mm",
    base=[f"{PR}*cos({A})", f"{PR}*sin({A})", f"{TOP} - pin_hole_h"])
F.pattern("Pin holes xN", ["Pin hole"])
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
F.c("measure", summary=True)

# ------------------------------------------------------------------ bezel
B = Script()
B.c("timeline.delete", features=[6, 7, 8, 9])
B.c("set_parameter", name="n_sides", value="6", unit="", comment="Number of panel sides: 6 hexagon, 4 square, 3 triangle.")
B.c("set_parameter", name="As", value=f"edge_L / (2 * tan({T}))")
B.c("set_parameter", name="pin_r", value=f"(Ao + A_in)/2/cos({T})")
Z0 = "cap_top + riser_h + film_t"
B.c("solid.cylinder", name="Blank", body_name="Bezel", radius=f"Ao/cos({T}) + 5 mm", height="bezel_t",
    base=[0, 0, Z0])
B.edge_trim("Ao", f"{Z0} - 1 mm", f"{Z0} + bezel_t + 1 mm")
B.wedge("OpeningSketch", "Opening wedge", "A_in", f"{Z0} - 1 mm", "bezel_t + 2 mm")
B.pattern("Opening xN", ["Opening wedge"])
B.c("solid.cylinder", name="Bezel pin", operation="join", participants=["Bezel"], radius="pin_d/2",
    height="pin_h + film_t + 0.2 mm", base=[f"pin_r*cos({A})", f"pin_r*sin({A})", "cap_top + riser_h - pin_h"])
B.pattern("Bezel pins xN", ["Bezel pin"])
B.c("measure", summary=True)

out = sys.argv[1]
json.dump({"commands": F.s}, open(out + "/frame_build.json", "w"), indent=1)
json.dump({"commands": B.s}, open(out + "/bezel_build.json", "w"), indent=1)
print(len(F.s), len(B.s))
