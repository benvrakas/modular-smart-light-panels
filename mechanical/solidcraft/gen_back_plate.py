"""SolidCraft build script for back_plate.sc, every outline driven by n_sides.

python gen_back_plate.py OUT.json  ->  solidcraft-cli run OUT.json --in back_plate.sc --save back_plate.sc
The script deletes the part's current features (the parameters stay) and rebuilds it. Rules (CLAUDE.md): every profile
and extent ends exactly on the face it meets (no overshoot, no oversized blank trimmed back), and repeated features are
modelled once and mirrored or patterned.
Coordinates: side 0 is the -y side (seam at y = -As); s = distance in from the seam, so a face at s sits at y = -As + s.
"""
import json
import os
import sys
import zipfile

T = "180 deg/n_sides"           # half the central angle of one side
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.loads(zipfile.ZipFile(os.path.join(HERE, "back_plate.sc")).read("document.json"))
EXISTING = {p["name"] for p in D["params"]}
S = []


def c(cmd, **p):
    S.append({"command": cmd, "params": p})


def param(name, expr, comment=None):
    c("parameters.change" if name in EXISTING else "parameters.add", name=name, expression=expr)
    EXISTING.add(name)
    if comment:
        c("parameters.comment", name=name, comment=comment)


def sketch(name, plane, offset, pts):
    p = {"plane": plane, "name": name}
    if offset is not None:
        p["offset"] = offset
    c("sketch.create", **p)
    c("sketch.line", closed=True, points=pts)
    c("sketch.finish")


def box(name, center, l, w, h, op):
    c("solid.box", name=name, center=center, length=l, width=w, height=h, operation=op)


def pattern(name, feats):
    c("solid.pattern.circular", name=name, features=feats, axis="Z", count="n_sides")


if any(f["name"] == "Boss trim" for f in D["features"]):
    c("config.column", feature="Boss trim", delete=True)   # recreated below with the new feature
c("timeline.delete", features=[f["id"] for f in D["features"]])

# ---- parameters
param("As", f"edge_L / (2 * tan({T}))", "Panel inradius to the seam centreline (decision 0004); n_sides picks the shape.")
param("relief_x", f"edge_L/2 - (seam_d + board_t)*tan({T}) - corner_rel",
      "Corner relief: where the corner chamfer meets the plate edge (Ab), measured along the side from its centre; "
      "corner_rel short of the boards' inner corner, so the soldered corner joint has room.")
param("rc", f"Ab*cos({T}) + relief_x*sin({T})", "Corner chamfer distance from the centre, along the corner direction.")
# No edge-part groove (user 2026-11-21): the board ring goes in along z after its corners are soldered, so R3 moved
# above z 6.8 on the boards (roadmap 2.0b) and the plate edge is plain.
# Clip (roadmap 2.0c, user 2026-11-21): base 3.0 (was 3.5), keys to z 1.2 (were 0.7); the chamfer is on the key only.
param("z_back", "-1.3 mm", "Clip top = clip-recess ceiling (clip base 3.0 mm from z_bot; was -0.8 with a 3.5 mm base).")
param("key_top", "1.2 mm", "Key top (straight engagement z_back .. key_top - key_ch = 2.2 mm). Side 0: 0.9 mm of cross-bar stays above the groove.")
param("key_ch", "0.3 mm", "Key-top chamfer (lead-in on the clip only; the groove mouth is square, user 2026-11-21).")
param("tooth_h", "0.7 mm")
param("tooth_zb0", "-3.7 mm")
param("tooth_zb1", "-1.6 mm")
param("latch_z", "-2.3 mm", "Frame-hook latch plane: the hook-pocket ceiling under the board tab (user 2026-11-21: more engagement).")
param("hook_s1", "4.95 mm", "Hook pocket depth from the seam: frame hook tip (seam distance 4.8) + fit_loose.")
param("seat_ch", "25 deg", "Board seat slope from horizontal: a 65 deg overhang in the floor-down print (user 2026-11-22: 65 is safe, 70 sags). The slope runs from the plate edge through the board's inner bottom corner (z 0), so there is no flat. The tab edge keeps 0.60 mm over the clip recess (a thickness along the print's Z, fine down to about 0.5 mm) and 1.6 mm over the frame hooks.")
param("bar_s0", "As - Ab", "Cross-bar outer end: the plate edge, which is also the controller pocket's outer edge, so no strip of rim floor hangs exposed between them.")

# ---- outline, per side (patterned): core sector to the plate edge Ab, tab band out to tab_out, both ending on the
# corner chamfer (rc), so the outline is drawn directly instead of trimming a blank
HX = "relief_x"                                   # chamfer on the plate edge (y = -Ab)
TX = f"(relief_x - (tab_out - Ab)/tan({T}))"      # chamfer on the tab's outer edge (y = -tab_out)
sketch("CoreSketch", "XY", "z_bot", [
    [0, 0], [f"rc*sin({T})", f"-rc*cos({T})"], [HX, "-Ab"], [f"-{HX}", "-Ab"], [f"-rc*sin({T})", f"-rc*cos({T})"]])
# join-type: the first copy starts the body and each later copy merges with the sector it touches
c("solid.extrude", sketch="CoreSketch", operation="join", distance="z_top - z_bot", name="Core", body_name="Back plate")
HA, HT = "(Ai - Ab)*tan(seat_ch)", "-(tab_out - Ai)*tan(seat_ch)"   # seat line at the plate edge / at tab_out
sketch("TabBandSketch", "XY", "z_bot", [[HX, "-Ab"], [TX, "-tab_out"], [f"-{TX}", "-tab_out"], [f"-{HX}", "-Ab"]])
c("solid.extrude", sketch="TabBandSketch", operation="join", distance=f"{HA} - z_bot", name="Tab band")
# board seat: the band's top slopes at seat_ch from the plate edge down to tab_out (through the board's inner bottom
# corner); the triangle sits on the band's top and outer faces, through-all along the side
sketch("SeatSketch", "YZ", None, [["-Ab", HA], ["-tab_out", HT], ["-tab_out", HA]])
c("solid.extrude", sketch="SeatSketch", operation="cut", direction="symmetric", through_all=True, name="Board seat")
# back cavity: from the wall plane up to the floor
sketch("CavitySketch", "XY", "z_bot", [[0, 0], [f"(Ab - rim_w)*tan({T})", "-(Ab - rim_w)"], [f"-(Ab - rim_w)*tan({T})", "-(Ab - rim_w)"]])
c("solid.extrude", sketch="CavitySketch", operation="cut", distance="z_top - floor_t - z_bot", name="Cavity")
pattern("Sides xN", ["Core", "Tab band", "Board seat", "Cavity"])

# ---- controller pocket (side 0): the controller outline + fit, 30 deg sides, from its inner edge out to the plate
# edge, from the clip-recess ceiling to the top face; the cross-bar spans it between the walls
RIN = "(Ai - ctrl_gap - ctrl_depth - fit_loose)"
HWI = "((ctrl_base - 2*ctrl_depth*tan(30 deg))/2 + fit_loose*tan(30 deg))"
def hw(r):
    """Pocket half-width at inradius r (on its 30 deg side walls)."""
    return f"({HWI} + (({r}) - {RIN})*tan(30 deg))"
def trap(r_out, r_in):
    return [[f"-{hw(r_out)}", f"-({r_out})"], [hw(r_out), f"-({r_out})"], [hw(r_in), f"-({r_in})"], [f"-{hw(r_in)}", f"-({r_in})"]]
sketch("PocketSketch", "XY", "z_back", trap("Ab", RIN))
c("solid.extrude", sketch="PocketSketch", operation="cut", distance="z_top - z_back", name="Controller pocket")
sketch("CrossBarSketch", "XY", "z_back", trap("As - bar_s0", "As - bar_s1"))
c("solid.extrude", sketch="CrossBarSketch", operation="join", distance="bar_top - z_back", name="Cross-bar")

# ---- Dual Lock bosses: from the wall plane up to the cavity ceiling
box("Dual Lock boss", ["pad_r*cos(boss_a0)", "pad_r*sin(boss_a0)", "(z_top - floor_t + z_bot)/2"],
    "pad_size", "pad_size", "z_top - floor_t - z_bot", "join")
c("solid.pattern.circular", name="Dual Lock bosses xN", features=["Dual Lock boss"], axis="Z", count="boss_n")
# Boss trim (user 2026-11-21): bosses keep their full size (square 25 mm, as on the hexagon); only the part inside the
# controller pocket is cut away, through the full height, so nothing is left hanging in the pocket. The cut covers the
# pocket footprint from the rim's inner edge to the pocket's far edge, where only boss material exists.
# Only the square's rotated bosses reach the pocket, so the cut is active in the Square configuration only. On the
# triangle that footprint would reach the other sides' rims: keep it suppressed for any shape whose bosses don't need it.
sketch("BossTrimSketch", "XY", "z_bot", trap("Ab - rim_w", RIN))
c("solid.extrude", sketch="BossTrimSketch", operation="cut", distance="z_top - z_bot", name="Boss trim")
c("config.configure", features=["Boss trim"])
for row, sup in (("Hexagon", True), ("Square", False), ("Triangle", True)):
    c("config.row", name=row, values={"suppress:Boss trim": sup} | ({"param:pad_size": "25 mm"} if row == "Square" else {}))
c("config.activate", row="Triangle")

# ---- per-side clip features at side 0, patterned
SEAM = "(As - tab_out)"        # s of the tab's outer face: the recesses open there
box("Clip recess", [0, "-(tab_out + As - lug_s0)/2", "(z_back + z_bot)/2"], "2*(clip_half + fit_loose)",
    f"lug_s0 - {SEAM}", "z_back - z_bot", "cut")
sketch("GrooveSketch", "YZ", "-(key_half + fit_tight)", [            # from the clip-recess ceiling
    ["-As + key_s0 - fit_tight", "z_back"],
    ["-As + key_s0 - fit_tight", "key_top + fit_tight"],
    ["-As + key_s0 + key_w + fit_tight", "key_top + fit_tight"],
    ["-As + key_s0 + key_w + fit_tight", "z_back"]])
c("solid.extrude", sketch="GrooveSketch", operation="cut", distance="2*(key_half + fit_tight)", name="Groove")
# tooth notch: the clip tooth's lead and latch faces + fit, from the recess wall (s = lug_s0) to the tooth tip + fit
LEAD = lambda d: f"tooth_zb1 + fit_loose/cos(tooth_lead) - ({d})*tan(tooth_lead)"
LATCH = lambda d: f"tooth_zb0 - fit_loose/cos(tooth_latch) + ({d})*tan(tooth_latch)"
TIP = "tooth_h + fit_loose"
sketch("NotchSketch", "YZ", "lug_xc - tooth_len/2 - fit_loose", [
    ["-As + lug_s0", LEAD("lug_s0 - clip_edge")], ["-As + clip_edge + " + TIP, LEAD(TIP)],
    ["-As + clip_edge + " + TIP, LATCH(TIP)], ["-As + lug_s0", LATCH("lug_s0 - clip_edge")]])
c("solid.extrude", sketch="NotchSketch", operation="cut", distance="tooth_len + 2*fit_loose", name="Notch")
# frame-hook pocket: from the recess side wall out to hook_x1, from the tab's outer face to hook_s1, wall plane to latch_z
box("Hook pocket", ["(hook_x1 + clip_half + fit_loose)/2", "-(tab_out + As - hook_s1)/2", "(latch_z + z_bot)/2"],
    "hook_x1 - clip_half - fit_loose", f"hook_s1 - {SEAM}", "latch_z - z_bot", "cut")
# notch and hook pocket: modelled once on the +x half of side 0, mirrored to -x (CAD symmetry rule)
c("solid.mirror", name="Mirror left-right", features=["Notch", "Hook pocket"], plane="YZ")
pattern("Side features xN", ["Clip recess", "Groove", "Notch", "Hook pocket", "Mirror left-right"])

c("inspect.measure", summary=True)
json.dump({"commands": S}, open(sys.argv[1], "w"), indent=1)
print(len(S), "steps")
