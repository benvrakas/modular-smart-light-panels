"""Generate the SolidCraft command script that rebuilds back_plate.sc with every outline driven by n_sides."""
import json, sys

T = "180 deg/n_sides"           # half the central angle of one side
S = []


def c(cmd, **p):
    if cmd == "set_parameter":        # MCP alias -> engine commands, as solidcraft-cli runs them
        S.append({"command": "parameters.change", "params": {"name": p["name"], "expression": p["value"]}})
        if p.get("comment"):
            S.append({"command": "parameters.comment", "params": {"name": p["name"], "comment": p["comment"]}})
        return
    if cmd == "measure":
        cmd = "inspect.measure"
    S.append({"command": cmd, "params": p})


def sketch(name, plane, offset, pts):
    p = {"plane": plane, "name": name}
    if offset is not None:
        p["offset"] = offset
    c("sketch.create", **p)
    c("sketch.line", closed=True, points=pts)
    c("sketch.finish")


def box(name, center, l, w, h, op):
    c("solid.box", name=name, center=center, length=l, width=w, height=h, operation=op)


def pattern(name, feats, count):
    c("solid.pattern.circular", name=name, features=feats, axis="Z", count=count)


old_ids = list(range(280, 305))  # update after each rebuild
c("config.column", feature="Boss trim", delete=True)   # recreated below with the new feature
c("timeline.delete", features=old_ids)

# ---- parameters
c("set_parameter", name="As", value=f"edge_L / (2 * tan({T}))",
  comment="Panel inradius to the seam centreline (decision 0004); n_sides picks the shape.")
c("set_parameter", name="rc",
  value=f"Ab*cos({T}) + (edge_L/2 - (seam_d + board_t)*tan({T}) - corner_rel)*sin({T})",
  comment="Corner trim distance from the centre, measured along the corner direction.")
# No edge-part groove (user 2026-11-21): the board ring goes in along z after its corners are soldered, so R3 moved
# above z 6.8 on the boards (roadmap 2.0b) and the plate edge is plain.
# (band_z0/band_z1/band_d were deleted from back_plate.sc in that rebuild.)
# Clip (roadmap 2.0c, user 2026-11-21): base 3.0 (was 3.5), keys to z 1.2 (were 0.7); the chamfer is on the key only.
c("set_parameter", name="z_back", value="-1.3 mm", comment="Clip top = clip-recess ceiling (clip base 3.0 mm from z_bot; was -0.8 with a 3.5 mm base).")
c("set_parameter", name="key_top", value="1.2 mm", comment="Key top (straight engagement z_back .. key_top - key_ch = 2.2 mm). Side 0: 0.9 mm of cross-bar stays above the groove.")
c("set_parameter", name="key_ch", value="0.3 mm", comment="Key-top chamfer (lead-in on the clip only; the groove mouth is square, user 2026-11-21).")
c("set_parameter", name="tooth_h", value="0.7 mm")
c("set_parameter", name="tooth_zb0", value="-3.7 mm")
c("set_parameter", name="tooth_zb1", value="-1.6 mm")
c("set_parameter", name="latch_z", value="-2.3 mm", comment="Frame-hook latch plane: the hook-pocket ceiling under the board tab (user 2026-11-21: more engagement).")
c("set_parameter", name="hook_s1", value="4.95 mm", comment="Hook pocket depth from the seam: frame hook tip (seam distance 4.8) + fit_loose.")
c("set_parameter", name="seat_ch", value="20 deg", comment="Board seat slope from horizontal: 20 deg is the shallowest that prints unsupported (user rule). The slope runs from the plate edge through the board's inner bottom corner (z 0), so there is no flat; the tab edge keeps 0.75 mm over the clip recess and 1.75 mm over the frame hooks (user 2026-11-21).")

# ---- blank: one cylinder from the wall plane to the floor top; everything else is cut from it
c("solid.cylinder", name="Blank", body_name="Back plate", radius=f"tab_out/cos({T}) + 10 mm",
  height="z_top - z_bot", base=[0, 0, "z_bot"])

# ---- back cavity: one wedge per side, patterned
sketch("CavityWedgeSketch", "XY", "z_bot - 1 mm",
       [[0, 0], [f"(Ab - rim_w)*tan({T})", "-(Ab - rim_w)"], [f"-(Ab - rim_w)*tan({T})", "-(Ab - rim_w)"]])
c("solid.extrude", sketch="CavityWedgeSketch", operation="cut", distance="z_top - floor_t - z_bot + 1 mm",
  name="Cavity wedge")
pattern("Cavity xN", ["Cavity wedge"], "n_sides")

# ---- controller pocket (side 0), cross-bar
sketch("PocketSketch", "XY", "z_back", [
    ["-(ctrl_base/2 + fit_loose*2*cos(30 deg))", "-(Ai - ctrl_gap) - fit_loose"],
    ["ctrl_base/2 + fit_loose*2*cos(30 deg)", "-(Ai - ctrl_gap) - fit_loose"],
    ["(ctrl_base - 2*ctrl_depth*tan(30 deg))/2 + fit_loose*tan(30 deg)", "-(Ai - ctrl_gap - ctrl_depth) + fit_loose"],
    ["-((ctrl_base - 2*ctrl_depth*tan(30 deg))/2 + fit_loose*tan(30 deg))", "-(Ai - ctrl_gap - ctrl_depth) + fit_loose"]])
c("solid.extrude", sketch="PocketSketch", operation="cut", distance="z_top - z_back + 1 mm", name="Controller pocket")
box("Cross-bar", [0, "-As + (bar_s0 + bar_s1)/2", "(bar_top + z_back)/2"], "74 mm", "bar_s1 - bar_s0",
    "bar_top - z_back", "join")

# ---- Dual Lock bosses
box("Dual Lock boss", ["pad_r*cos(boss_a0)", "pad_r*sin(boss_a0)", "(z_top - floor_t + z_bot)/2"],
    "pad_size", "pad_size", "z_top - floor_t - z_bot", "join")
pattern("Dual Lock bosses xN", ["Dual Lock boss"], "boss_n")
# Boss trim (user 2026-11-21): bosses keep their full size (square 25 mm, as on the hexagon); only the part inside the
# controller pocket is cut away, through the full height, so nothing is left hanging in the pocket. The cut covers the
# pocket footprint from the rim's inner edge to the pocket's far edge, where only boss material exists.
TR_YR, TR_YF = "-(Ab - rim_w)", "-(Ai - ctrl_gap - ctrl_depth) + fit_loose"
TR_HF = "((ctrl_base - 2*ctrl_depth*tan(30 deg))/2 + fit_loose*tan(30 deg))"
TR_HR = f"({TR_HF} + ((Ab - rim_w) - (Ai - ctrl_gap - ctrl_depth) + fit_loose)*tan(30 deg))"
# Only the square's rotated bosses reach the pocket, so the cut is active in the Square configuration only. There the
# footprint between the rim (Ab - rim_w) and the pocket's far edge is empty except for boss material (|x| <= 31.6
# against the side rims at 36.75). On the triangle that footprint would reach the other sides' rims: keep it suppressed
# for any shape whose bosses don't need it.
sketch("BossTrimSketch", "XY", "z_bot - 1 mm", [[f"-{TR_HR}", TR_YR], [TR_HR, TR_YR], [TR_HF, TR_YF], [f"-{TR_HF}", TR_YF]])
c("solid.extrude", sketch="BossTrimSketch", operation="cut", distance="z_top - z_bot + 2 mm", name="Boss trim")
c("config.configure", features=["Boss trim"])
for row, sup in (("Hexagon", True), ("Square", False), ("Triangle", True)):
    c("config.row", name=row, values={"suppress:Boss trim": sup} | ({"param:pad_size": "25 mm"} if row == "Square" else {}))
c("config.activate", row="Triangle")

# ---- per-side features at side 0, patterned
box("Clip recess", [0, "-As + (lug_s0 - 1 mm)/2", "(z_back + z_bot - 1 mm)/2"], "2*(clip_half + fit_loose)",
    "lug_s0 + 1 mm", "z_back - z_bot + 1 mm", "cut")
sketch("GrooveSketch", "YZ", "-(key_half + fit_tight)", [
    ["-As + key_s0 - fit_tight", "z_back - 0.7 mm"],
    ["-As + key_s0 - fit_tight", "key_top + fit_tight"],
    ["-As + key_s0 + key_w + fit_tight", "key_top + fit_tight"],
    ["-As + key_s0 + key_w + fit_tight", "z_back - 0.7 mm"]])
c("solid.extrude", sketch="GrooveSketch", operation="cut", distance="2*(key_half + fit_tight)", name="Groove")
NOTCH = [
    ["-As + clip_edge + 0.05 mm", "tooth_zb1 + fit_loose/cos(tooth_lead) - 0.05 mm*tan(tooth_lead)"],
    ["-As + clip_edge + tooth_h + fit_loose", "tooth_zb1 + fit_loose/cos(tooth_lead) - (tooth_h + fit_loose)*tan(tooth_lead)"],
    ["-As + clip_edge + tooth_h + fit_loose", "tooth_zb0 - fit_loose/cos(tooth_latch) + (tooth_h + fit_loose)*tan(tooth_latch)"],
    ["-As + clip_edge + 0.05 mm", "tooth_zb0 - fit_loose/cos(tooth_latch) + 0.05 mm*tan(tooth_latch)"]]
# tooth notch and hook pocket: modelled once on the +x half of side 0, mirrored to -x (CAD symmetry rule)
sketch("NotchSketch", "YZ", "lug_xc - tooth_len/2 - fit_loose", NOTCH)
c("solid.extrude", sketch="NotchSketch", operation="cut", distance="tooth_len + 2*fit_loose", name="Notch")
box("Hook pocket", ["(hook_x1 + clip_half + fit_loose)/2", "-As + (hook_s1 - 1 mm)/2", "(latch_z + z_bot - 1 mm)/2"],
    "hook_x1 - clip_half - fit_loose", "hook_s1 + 1 mm", "latch_z - z_bot + 1 mm", "cut")
c("solid.mirror", name="Mirror left-right", features=["Notch", "Hook pocket"], plane="YZ")
pattern("Side features xN", ["Clip recess", "Groove", "Notch", "Hook pocket", "Mirror left-right"], "n_sides")

# ---- outline: edge profile per side (plate edge Ab above z 0, board seat sloped at seat_ch, tab_out below)
sketch("EdgeTrimSketch", "YZ", None, [
    ["-Ab", "z_top + 1 mm"], ["-Ab", "(Ai - Ab)*tan(seat_ch)"],
    ["-tab_out", "-(tab_out - Ai)*tan(seat_ch)"], ["-tab_out", "z_bot - 1 mm"],
    [f"-(tab_out/cos({T}) + 20 mm)", "z_bot - 1 mm"], [f"-(tab_out/cos({T}) + 20 mm)", "z_top + 1 mm"]])
c("solid.extrude", sketch="EdgeTrimSketch", operation="cut", direction="symmetric", distance="4*tab_out + 100 mm",
  name="Edge trim")
pattern("Edge trim xN", ["Edge trim"], "n_sides")

# ---- corner trim (corner reliefs), one half-plane per corner
A = f"({T} - 90 deg)"
def P(r, w):
    return [f"({r})*cos({A}) - ({w})*sin({A})", f"({r})*sin({A}) + ({w})*cos({A})"]
sketch("CornerTrimSketch", "XY", "z_bot - 1 mm",
       [P("rc", "30 mm"), P("rc", "-30 mm"), P("rc + 30 mm", "-30 mm"), P("rc + 30 mm", "30 mm")])
c("solid.extrude", sketch="CornerTrimSketch", operation="cut", distance="z_top - z_bot + 2 mm", name="Corner trim")
pattern("Corner trim xN", ["Corner trim"], "n_sides")

c("measure", summary=True)
json.dump({"commands": S}, open(sys.argv[1], "w"), indent=1)
print(len(S), "steps")
