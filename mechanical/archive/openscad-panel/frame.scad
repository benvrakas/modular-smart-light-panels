// =====================================================================
//  frame.scad -- WP 1.6 panel frame ("crown"), white PETG.
//
//  A polygon ring that caps the six upright edge boards:
//   - groove: each board's top edge sits in a groove (board_t + 2 x 0.15), between the
//     exterior wall (outside) and a 0.7 mm inward lip (inside, above the LEDs). The lip and
//     the back-plate rim take the springs' inward push (SPEC §3.3 "Forces").
//   - exterior wall: runs down to z_skirt, just above the seam bridge, so the bridge and
//     springs have the seam to themselves below it (contact strip z 0-6).
//   - corners: the exterior wall and the lip stop short of every corner so the corner
//     joints (SPEC §3.4) can be drag-soldered with the boards in the frame; only the 2 mm
//     cap spans the corner. Corner pin holes take the diffuser risers / bezel.
//   - snap legs: two per side, in the seam outside the bridge carrier. Their barbs snap
//     under the back plate's tabs, which sit under the boards' wall edges, so frame, boards
//     and back plate lock together with no glue.
//
//  Print: cap DOWN on the bed (part = "print"). No supports: the barbs' undersides are 45 deg.
//  Export:  openscad.com -o stl/frame.stl -D "part=\"print\"" frame.scad
// =====================================================================
include <common.scad>

part = "print";      // print | assembly

module frame_leg(s) {
    x0 = s > 0 ? leg_x[0] : -leg_x[1];
    x1 = s > 0 ? leg_x[1] : -leg_x[0];
    r_in  = Ae + gclr;
    r_out = r_in + leg_t;
    r_tip = tab_out - hook_eng;          // barb tip under the plate tab
    z_tip = z_pb - hook_eng;             // 45 deg retaining face passes through the tab's outer corner
    sbox(x0, x1, r_in, r_out, z_leg_bot, z_skirt + 1);
    // barb: ramp below (the rising plate tab pushes the leg out), 45 deg retaining face above
    rz_prism(x0, x1, [[r_in + 0.2, z_leg_bot], [r_tip, z_tip], [r_in + 0.2, z_tip + (r_in + 0.2 - r_tip)]]);
}

module frame() {
    difference() {
        union() {
            ring_band(Ai - lip_w, Ao, board_H + gclr, z_cap_top);                       // cap
            ring_band(Ae + gclr, Ao, z_skirt, board_H + gclr + eps);                     // exterior wall
            ring_band(Ai - lip_w, Ai - gclr, board_H - lip_h, board_H + gclr + eps);     // inward lip
            all_sides() for (s = [-1, 1]) frame_leg(s);
        }
        all_sides() {
            // corner solder windows: exterior wall off within corner_zone of each board end
            sbox(HL - corner_zone, HL + 40, Ae + gclr - eps, Ao + 1, z_skirt - 1, board_H + gclr);
            sbox(-HL - 40, -HL + corner_zone, Ae + gclr - eps, Ao + 1, z_skirt - 1, board_H + gclr);
            // lip off near the corners (inward corner pads and their solder beads)
            sbox(HL - corner_lip, HL + 40, Ai - lip_w - 1, Ai, board_H - lip_h - 1, board_H + gclr);
            sbox(-HL - 40, -HL + corner_lip, Ai - lip_w - 1, Ai, board_H - lip_h - 1, board_H + gclr);
            // lip notches over inward-face test pads (TP11)
            for (tp = tp_inward) if (tp[1] + tp_dia / 2 > board_H - lip_h)
                sbox(-tp[0] - tp_dia / 2 - 0.5, -tp[0] + tp_dia / 2 + 0.5, Ai - lip_w - 1, Ai, board_H - lip_h - 1, board_H + gclr);
        }
        // registration holes for riser / bezel pins (through the cap at the corners)
        at_corners() translate([pin_cr, 0, board_H]) cylinder(d = pin_hole_d, h = 10, $fn = 24);
    }
}

if (part == "print") translate([0, 0, z_cap_top]) rotate([180, 0, 0]) frame();
else if (part == "assembly") frame();
