// =====================================================================
//  bridge_carrier.scad -- WP 1.6 seam-bridge carrier, PETG (SPEC §3.3, D0002).
//
//  Holds the 0.8 mm bridge PCB upright on the seam centreline so its top-contact springs
//  press on the exterior-face contact pads of the two neighbouring edge boards.
//   - base on the wall (z -3.0 .. -0.3), 10 mm wide: it reaches under both panels' board
//     wall edges (0.3 mm below them) but stays clear of the back plates and the snap legs.
//     The two panels trap it against the wall; VHB tape under it is optional.
//   - spine with the bridge slot, slot floor at z -2.0, spine top z 2.0 (below the springs'
//     contact ends at z 2.6). The slot's closed ends locate the bridge along the seam.
//   - the carrier floats: across the seam the balanced springs centre it, along the seam the
//     snap legs of both panels bound it (+-0.5 mm). Panels are located by their wall pucks.
//
//  Seam tolerance (SPEC §3.3: 6.8-7.8 mm): the carrier and bridge self-centre, so the seam
//  can vary over the springs' working range (3.0-3.5 mm each side) without changing the part.
//
//  Coordinates: X along the seam, Y across it (0 = seam centreline), z = panel z.
//  Print: base down. No supports.
//  Export:  openscad.com -o stl/bridge_carrier.stl bridge_carrier.scad
// =====================================================================
include <common.scad>

part = "print";      // print | assembly

slot_w = bridge_t + car_slot_clr;
slot_len = bridge_len + 0.6;

module bridge_carrier() {
    difference() {
        union() {
            // base
            translate([0, 0, z_wall]) linear_extrude(-0.3 - z_wall)
                offset(r = 2) offset(delta = -2) square([2 * car_half, car_w], center = true);
            // spine, 45 deg chamfered top
            translate([-car_half + 0.5, 0, -0.3 - eps]) rotate([90, 0, 90]) linear_extrude(2 * car_half - 1)
                polygon([[-car_spine_w / 2, 0], [car_spine_w / 2, 0], [car_spine_w / 2, car_spine_top + 0.3 - 0.8],
                         [car_spine_w / 2 - 0.8, car_spine_top + 0.3], [-car_spine_w / 2 + 0.8, car_spine_top + 0.3],
                         [-car_spine_w / 2, car_spine_top + 0.3 - 0.8]]);
        }
        // bridge slot with a 0.4 mm lead-in at the top
        translate([-slot_len / 2, -slot_w / 2, bridge_z_bot]) cube([slot_len, slot_w, 10]);
        translate([-slot_len / 2, 0, car_spine_top]) rotate([90, 0, 90]) linear_extrude(slot_len)
            polygon([[-slot_w / 2, -0.4], [slot_w / 2, -0.4], [slot_w / 2 + 0.4, 0.01], [-slot_w / 2 - 0.4, 0.01]]);
    }
}

if (part == "print") translate([0, 0, -z_wall]) bridge_carrier();
else if (part == "assembly") bridge_carrier();
