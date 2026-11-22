// =====================================================================
//  optics_rig.scad -- Modular Smart Light Panels, roadmap WP 0.2
//  Optics test rig: one hexagon chamber at real panel size, lit by cut
//  SK6812 RGBW strip, with swappable depth rings, LED aim and film count.
//
//  OpenSCAD 2021.01. Units: mm. Print: FDM PETG, 0.4 mm nozzle.
//  Export a part from the command line, e.g.
//    openscad.com -o stl/frame.stl -D "part=\"frame\"" optics_rig.scad
//    openscad.com -o stl/spacer_4mm.stl -D "part=\"ring\"" -D ring_h=4 optics_rig.scad
//  (make_stl.sh in this folder exports everything.)
//
//  Coordinate frame (assembly): z = 0 is the back-plate (reflector)
//  surface, +z points at the diffuser / viewer. Side 0 is the bottom flat
//  (its inward face is the line y = -inner_apothem); sides 1..5 follow
//  counter-clockwise seen from the front. The LED chain runs the same way.
// =====================================================================

/* ---------------- Part selector ---------------- */
// assembly | back_plate | frame | ring | clamp_ring | bezel_ring |
// carriers | wedge_adapters | carrier | wedge_adapter
part = "assembly";
ring_h = 3;              // height of a "ring" part (spacers 3/3/4/5, risers 2/2)

/* ---------------- Assembly preview only ---------------- */
preview_rings = [3, 3];  // rings stacked on the frame in the preview (depth = frame_h + sum)
preview_aim   = "tilt";  // "flat" or "tilt"
preview_film  = true;

/* ---------------- Panel geometry (SPEC.md §2, decision 0004) ---------------- */
edge_L       = 100;      // common edge length on the seam centreline (SPEC §2)
seam_inset_d = 3.5;      // d: board exterior face to seam centreline (decision 0004, assumed)
board_t      = 1.6;      // edge-board thickness (SPEC §2)
led_x        = [-31.2, 0, 31.2];  // LED centres from the board centre (SPEC §2 interface contract)

/* ---------------- LED strip ---------------- */
strip_pitch  = 1000/60;  // 60 LEDs/m -> one cut segment is 16.67 mm long
strip_w      = 10;       // strip width; the LED centre sits strip_w/2 above the back plate

/* ---------------- Chamber depth ---------------- */
frame_h      = 10;       // LED frame height = shallowest depth tested (low end of H = 10-15 mm)
// Ring set to print: 3+3+4+5 gives 13/16/20/25 on top of the 10 mm frame;
// two 2 mm risers give the "diffuser 2/4 mm above the board top" cases.

/* ---------------- Printing / fits ---------------- */
fit          = 0.25;     // sliding clearance per face, PETG with 0.4 mm nozzle
bed_size     = 220;      // only used for a fit check

/* ---------------- Frame walls ---------------- */
// Wall from the inward board face out to the seam centreline, so the rig
// has the same outline as a real panel; leaves ~3.5 mm behind the LED pockets.
wall_t       = seam_inset_d + board_t;   // 5.1
plate_t      = 3;        // back plate; 3 mm white PETG is close to opaque
skirt_t      = 1.2;      // frame skirt that hugs the back-plate edge (3 perimeters)
cham         = 1.4;      // 45-degree registration chamfer between stacked rings
cham_gap     = 0.4;      // clearance of the mating skirt on that chamfer (0.28 mm normal)
clamp_t      = 2.5;      // diffuser clamp ring thickness

/* ---------------- Rubber-band tabs (hold the stack + film together) ---------------- */
tab_w        = 14;       // along the side
tab_out      = 9;        // radial reach beyond the back-plate edge: band runs ~5 mm clear of the walls
tab_notch_w  = 3.5;      // band notch
tab_notch_d  = 3;
cable_tab_x  = -24;      // extra cable-tie tab on side 0, between LED 1 and LED 2 (no wires run there)
zip_w        = 3.2;      // cable-tie slots for a 2.5 mm tie
zip_h        = 1.6;

/* ---------------- LED carriers (board stand-ins) ---------------- */
carrier_t    = board_t;            // 1.6 mm: same as the real edge board, so the LED face sits where the real one does
carrier_h    = frame_h - 0.4;      // a hair under the frame so the ring above always seats; strip may overhang the top by <= 0.4
carrier_front= strip_pitch + 0.2;  // strip face: one cut segment plus 0.2 mm
dovetail     = 30;                 // end undercut; holds the carrier against tipping inward, prints without support
rebate_d     = carrier_t + 0.05;   // pocket depth: carrier face flush with the wall face

/* ---------------- Wire slots ---------------- */
ws_gap       = 1.5;      // wall left between pocket end and wire slot (also clears the wedge adapter body)
ws_w         = 2.4;      // three 28-30 AWG wires stacked
cable_ws_w   = 3.2;      // the two slots at the chain start/end also carry the supply lead
ws_floor     = 2.5;      // slots stop 2.5 mm above the plate: the ring stays continuous at the bottom

/* ---------------- Wedge adapters (LED aim option b) ---------------- */
aim_tilt     = 25;       // LED face tilted toward the back plate (gap A1: 20-30 deg)
adapter_web  = 1.2;      // minimum adapter material behind the tilted pocket
adapter_side = 1.2;      // adapter side walls beyond the pocket

/* ---------------- Optional bezel ring ---------------- */
bezel_w      = 6;        // inward lip that hides the band of film nearest the LEDs (optional test)
bezel_h      = 2;

/* ---------------- Print layout of small parts ---------------- */
n_small      = 20;       // 18 needed + 2 spares

$fn = 32;
eps = 0.01;

// =====================================================================
//  Derived values
// =====================================================================
seam_apothem  = edge_L * sqrt(3) / 2;                      // 86.60
Ai            = seam_apothem - (seam_inset_d + board_t);   // inner apothem, 81.50
inner_side    = 2 * Ai / sqrt(3);                          // 94.10 (spec: L_board hexagon)
Ao            = Ai + wall_t;                               // outer apothem, 86.60
plate_a       = Ao - skirt_t - fit;                        // back-plate apothem, 85.15
skirt_len     = plate_t - 0.5;                             // frame skirt stops short of the table
rim_edge      = Ao - cham;                                 // film rests on Ai..rim_edge
tab_a         = plate_a + tab_out;                         // tab outer apothem
carrier_back  = carrier_front + 2 * carrier_t * tan(dovetail);
pocket_front  = carrier_front/2 + fit;                     // half-length of pocket mouth
pocket_back   = pocket_front + rebate_d * tan(dovetail);   // half-length at pocket bottom
ws_x0         = pocket_back + ws_gap;                      // wire slot starts this far from LED centre
// wedge adapter
ad_B          = pocket_back + adapter_side;                // adapter half-length
ad_y0         = adapter_web + rebate_d / cos(aim_tilt) + 0.2;  // carrier front-bottom edge, inward of wall face
tilt_top      = carrier_t * sin(aim_tilt) + carrier_h * cos(aim_tilt);

function circ(a) = a / cos(30);   // apothem -> circumradius ($fn = 6)

// ---------------- sanity checks ----------------
assert(abs(inner_side - 94.1) < 0.1, "inner side should be ~94.1 mm (decision 0004)");
assert(carrier_h <= frame_h, "carrier taller than frame");
assert(tilt_top < frame_h, "tilted carrier pokes above the frame top");
assert(max(led_x) + ws_x0 + cable_ws_w < inner_side/2 - 1, "outer wire slot runs into the corner");
assert(max(led_x) + ad_B < inner_side/2 - 2, "wedge adapter hits the corner");
assert(2 * circ(Ao) <= bed_size - 10, "frame does not fit the bed");
assert(rim_edge >= plate_a, "film traced from the back plate would not fit the rim");

echo(str("inner side ", inner_side, "  inner apothem ", Ai, "  outer apothem ", Ao,
         "  across corners ", 2*circ(Ao), "  plate apothem ", plate_a));
echo(str("carrier ", carrier_front, "/", carrier_back, " x ", carrier_h, " x ", carrier_t,
         "  wire slot at +-", ws_x0, "  adapter y0 ", ad_y0, "  tilted top ", tilt_top));

// =====================================================================
//  Helpers
// =====================================================================
// Hexagonal ring from a radial profile given in APOTHEM coordinates [a, z].
// rotate_extrude with $fn = 6 puts the profile at the corners, so scaling by
// 1/cos30 makes every flat carry exactly the profile.
module hex_extrude(pts) rotate_extrude($fn = 6) polygon([for (p = pts) [circ(p[0]), p[1]]]);

module hex2d(a) circle(r = circ(a), $fn = 6);

module on_sides(list = [0:5]) for (k = list) rotate([0, 0, 60 * k]) children();

// Dovetail pocket in (x, y): y = 0 is the wall face, y < 0 into the wall.
module pocket_2d() polygon([[-pocket_front, 1], [pocket_front, 1], [pocket_front, 0],
                            [pocket_back, -rebate_d], [-pocket_back, -rebate_d], [-pocket_front, 0]]);

// Carrier cross-section: strip face at y = 0, back at y = -carrier_t.
module carrier_2d(front_ext = 0) polygon([[-carrier_front/2, front_ext], [carrier_front/2, front_ext],
                                          [carrier_front/2, 0], [carrier_back/2, -carrier_t],
                                          [-carrier_back/2, -carrier_t], [-carrier_front/2, 0]]);

// Rubber-band tab (side-0 coordinates), with notch or cable-tie slots.
module tab_2d(x, inner_a, zip = false) {
    translate([x, 0]) difference() {
        translate([-tab_w/2, -tab_a]) square([tab_w, tab_a - inner_a]);
        if (!zip) translate([-tab_notch_w/2, -tab_a - 1]) square([tab_notch_w, tab_notch_d + 1]);
        if (zip) for (s = [-1, 1]) translate([s * 3.6 - zip_w/2, -tab_a + 2.5]) square([zip_w, zip_h]);
    }
}

// =====================================================================
//  Parts (modelled in assembly position)
// =====================================================================

// ---- Back plate: the white matte reflector. Top face = z 0. ----
module back_plate() {
    translate([0, 0, -plate_t]) linear_extrude(plate_t) {
        hex2d(plate_a);
        on_sides() tab_2d(0, plate_a - 1);
        tab_2d(cable_tab_x, plate_a - 1, zip = true);
    }
}

// ---- LED frame: the six "edge boards". Holds 18 carriers at the real LED positions. ----
module frame() {
    difference() {
        hex_extrude([[Ai, 0], [Ai, frame_h], [rim_edge, frame_h], [Ao, frame_h - cham],
                     [Ao, -skirt_len], [Ao - skirt_t, -skirt_len], [Ao - skirt_t, 0]]);
        on_sides() {
            for (x = led_x) {
                // carrier pocket, open at the top, carrier stands on the back plate
                translate([x, -Ai, -1]) linear_extrude(frame_h + 2) pocket_2d();
            }
            // skirt notch for each band tab on the back plate
            translate([-tab_w/2 - 0.6, -Ao - 1, -skirt_len - 1]) cube([tab_w + 1.2, skirt_t + fit + 1.5, skirt_len + 1]);
        }
        // skirt notch for the cable tab (side 0 only: keys the frame to the plate)
        translate([cable_tab_x - tab_w/2 - 0.6, -Ao - 1, -skirt_len - 1]) cube([tab_w + 1.2, skirt_t + fit + 1.5, skirt_len + 1]);
        // wire slots through the wall, both ends of every LED
        for (k = [0:5]) for (j = [0:2]) for (s = [-1, 1]) {
            is_cable = (k == 0 && j == 0 && s == -1) || (k == 5 && j == 2 && s == 1);
            w = is_cable ? cable_ws_w : ws_w;
            rotate([0, 0, 60 * k])
                translate([led_x[j] + s * (ws_x0 + w/2) - w/2, -Ao - 1, ws_floor]) cube([w, wall_t + 2, frame_h]);
        }
    }
}

// ---- Spacer / riser ring: stacks on the frame or another ring. ----
module ring(h = ring_h, inner = Ai) {
    hex_extrude([[inner, 0], [inner, h], [rim_edge, h], [Ao, h - cham],
                 [Ao, -cham + cham_gap], [rim_edge + cham_gap, 0]]);
}

// ---- Diffuser clamp ring: presses the film onto the top of the stack. ----
module clamp_ring() {
    union() {
        hex_extrude([[Ai, 0], [Ai, clamp_t], [Ao, clamp_t], [Ao, -cham + cham_gap], [rim_edge + cham_gap, 0]]);
        linear_extrude(clamp_t) on_sides() tab_2d(0, Ao - 1);
    }
}

// ---- Bezel ring (optional): a 2 mm ring with an inward lip under the film. ----
module bezel_ring() ring(bezel_h, Ai - bezel_w);

// ---- LED carrier: one cut strip segment is stuck on its face. ----
// Modelled standing in its pocket: face at y = 0 (looking +y), bottom at z = 0.
module carrier() {
    difference() {
        linear_extrude(carrier_h) carrier_2d();
        // centre mark on the top edge: line up the LED with it
        translate([0, 1, carrier_h + 0.2]) rotate([90, 0, 0]) linear_extrude(carrier_t + 2)
            polygon([[-0.8, 0], [0.8, 0], [0, -1.2]]);
    }
}

// ---- Wedge adapter: sits in a wall pocket and holds a carrier tilted
//      aim_tilt toward the back plate. Same coordinates as carrier(). ----
module wedge_adapter() {
    union() {
        // tongue in the wall pocket (overlaps the body by 0.5 mm)
        linear_extrude(frame_h) carrier_2d(front_ext = 0.5);
        difference() {
            intersection() {
                // everything behind the tilted carrier-face plane...
                translate([0, ad_y0, 0]) rotate([-aim_tilt, 0, 0])
                    translate([-ad_B, -60, -30]) cube([2 * ad_B, 60, 80]);
                // ...and in front of the wall face, inside the frame height
                translate([-ad_B, 0, 0]) cube([2 * ad_B, 40, frame_h]);
            }
            // tilted dovetail pocket for the carrier, open at top and bottom
            translate([0, ad_y0, 0]) rotate([-aim_tilt, 0, 0])
                translate([0, 0, -30]) linear_extrude(80) pocket_2d();
        }
    }
}

// =====================================================================
//  Print layouts (flat side down, no supports)
// =====================================================================
module print_upside_down(h) translate([0, 0, h]) rotate([180, 0, 0]) children();

module carriers_plate() {
    cols = 5;
    for (i = [0:n_small - 1])
        translate([(i % cols) * (carrier_back + 4), floor(i / cols) * (carrier_h + 4), 0])
            rotate([-90, 0, 0]) carrier();      // strip face on the bed: smooth, flat face for the adhesive
}

module adapters_plate() {
    cols = 5;
    for (i = [0:n_small - 1])
        translate([(i % cols) * (2 * ad_B + 4), floor(i / cols) * 16, 0])
            wedge_adapter();                    // upright as used: every overhang is <= aim_tilt from vertical
}

// =====================================================================
//  Assembly preview
// =====================================================================
module placed_carriers(aim) {
    on_sides() for (x = led_x) translate([x, -Ai, 0]) {
        if (aim == "flat") {
            color("ivory") carrier();
            color("gold") translate([-strip_pitch/2, 0, 0]) cube([strip_pitch, 0.2, strip_w]);
            color("white") translate([-2.5, 0.2, strip_w/2 - 2.5]) cube([5, 1.6, 5]);
        } else {
            color("lightgrey") wedge_adapter();
            translate([0, ad_y0, 0]) rotate([-aim_tilt, 0, 0]) {
                color("ivory") carrier();
                color("gold") translate([-strip_pitch/2, 0, 0]) cube([strip_pitch, 0.2, strip_w]);
                color("white") translate([-2.5, 0.2, strip_w/2 - 2.5]) cube([5, 1.6, 5]);
            }
        }
    }
}

module assembly() {
    color("white") back_plate();
    color("whitesmoke") frame();
    placed_carriers(preview_aim);
    for (i = [0:len(preview_rings) - 1]) {
        z0 = frame_h + (i == 0 ? 0 : sum_to(preview_rings, i));
        translate([0, 0, z0]) color(i % 2 ? "gainsboro" : "lightyellow") ring(preview_rings[i]);
    }
    depth = frame_h + sum_to(preview_rings, len(preview_rings));
    if (preview_film) color("lightblue", 0.4) translate([0, 0, depth]) linear_extrude(0.2) hex2d(plate_a);
    translate([0, 0, depth + 0.2]) color("silver") clamp_ring();
    echo(str("preview chamber depth = ", depth, " mm"));
}

function sum_to(v, n) = n <= 0 ? 0 : v[n - 1] + sum_to(v, n - 1);

// =====================================================================
//  Dispatcher
// =====================================================================
if (part == "assembly")            assembly();
else if (part == "back_plate")     translate([0, 0, plate_t]) back_plate();
else if (part == "frame")          print_upside_down(frame_h) frame();
else if (part == "ring")           print_upside_down(ring_h) ring(ring_h);
else if (part == "clamp_ring")     print_upside_down(clamp_t) clamp_ring();
else if (part == "bezel_ring")     print_upside_down(bezel_h) bezel_ring();
else if (part == "carriers")       carriers_plate();
else if (part == "wedge_adapters") adapters_plate();
else if (part == "carrier")        rotate([-90, 0, 0]) carrier();
else if (part == "wedge_adapter")  wedge_adapter();
else echo(str("Unknown part: ", part));
