// =====================================================================
//  diffuser.scad -- WP 1.6 diffuser retention with adjustable height, white PETG.
//
//  The film lies flat on the frame cap (no riser) or on a riser ring, and a bezel ring clamps
//  it. Risers and the bezel register on corner pins (press fit into the holes in the part
//  below); the film's corners are cut off so the pins pass outside it (no holes in the film).
//
//  Film height above the board top = 0.15 groove + 2.0 cap + riser:
//      riser 0 -> 2.15 mm,  3 -> 5.15 mm,  6 -> 8.15 mm,  10 -> 12.15 mm
//  The risers continue the chamber wall in line with the frame lip (white, reflective).
//
//  Parts (each printed top face down, pins up, no supports):
//      riser_3 / riser_6 / riser_10, bezel, and a 2D cut template for the film (DXF/SVG).
//  Export:
//      openscad.com -o stl/riser_3.stl  -D "part=\"riser\"" -D riser_h=3  diffuser.scad
//      openscad.com -o stl/bezel.stl    -D "part=\"bezel\""               diffuser.scad
//      openscad.com -o film_template.dxf -D "part=\"film\""                diffuser.scad
// =====================================================================
include <common.scad>

part = "riser";      // riser | bezel | film | assembly
riser_h = 3;

module corner_pins() at_corners() translate([pin_cr, 0, -pin_h]) {
    cylinder(d = pin_d, h = pin_h + eps, $fn = 24);
}
module corner_pin_holes(h) at_corners() translate([pin_cr, 0, h - pin_hole_h]) cylinder(d = pin_hole_d, h = pin_hole_h + 1, $fn = 24);

// Riser ring, bottom at z 0 (sits on the frame cap).
module riser(h = riser_h) {
    assert(h >= pin_hole_h + 1.0, "riser too thin for the pin holes");
    difference() {
        union() { ring_band(Ai - lip_w, Ao, 0, h); corner_pins(); }
        corner_pin_holes(h);
    }
}

// Bezel ring, bottom at z 0 (rests on the film).
module bezel() union() { ring_band(Ai - lip_w, Ao, 0, bezel_t); corner_pins(); }

module film() color("lightblue", 0.45) linear_extrude(film_t) film_2d();

// Diffuser stack in panel position, riser h (0 = none).
module diffuser_stack(h = 3, explode = 0) {
    z0 = z_cap_top;
    if (h > 0) translate([0, 0, z0 + explode]) color("whitesmoke") riser(h);
    translate([0, 0, z0 + h + 2 * explode]) film();
    translate([0, 0, z0 + h + film_t + 3 * explode]) color("gainsboro") bezel();
}

module print_flip(h) translate([0, 0, h]) rotate([180, 0, 0]) children();

if (part == "riser") print_flip(riser_h) riser(riser_h);
else if (part == "bezel") print_flip(bezel_t) bezel();
else if (part == "film") film_2d();
else if (part == "assembly") diffuser_stack(riser_h);
