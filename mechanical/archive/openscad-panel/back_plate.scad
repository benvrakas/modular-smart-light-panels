// =====================================================================
//  back_plate.scad -- WP 1.6 back plate, white PETG (it is the white back reflector).
//
//  Solid polygon plate inside the ring of edge boards, z_pb .. z_floor (-0.8 .. 6.6):
//   - top face = chamber floor at z 6.6 (SPEC §10 item 17), flush with the controller's white top.
//   - rim: its edge (0.25 mm off the boards' inward faces) takes the springs' inward push
//     low down, right behind the contact strip (SPEC §3.3 "Forces").
//   - corners cut back so the inward corner pads and beads stay free (SPEC §3.4).
//   - tabs under the board wall edges at the snap-leg positions: the frame legs snap under
//     them (frame.scad). The tabs also seat the boards in z.
//   - controller pocket on side 0 (code-0), per hardware/controller-board/LAYOUT-NOTES.md §4:
//     open from the floor through to the wall (parts face the wall; >= 2.8 mm everywhere and the
//     L1 window are both met, 8 mm of air under the board), so the jig and the joint iron reach
//     from behind. 45 deg ledges and 3 snap tongues sit only on the board's part-free edge
//     stretches; rim fingers carry the base margin and stop joint_iron short of the pad row.
//     The tongue lips hold the controller's chamber face (SPEC §3.5 "the back plate's snap fit
//     holds the board").
//   - underside recess and two sockets for the wall puck (wall_puck.scad); two access holes
//     for the puck screws, closed with the printed plugs afterwards.
//
//  Print: right side up (wall side on the bed), 15 % infill, >= 5 top layers for opacity.
//  Overhangs: the ledge underside is 45 deg; the tongue lips overhang 0.7 mm. No supports.
//  Export:  openscad.com -o stl/back_plate.stl -D "part=\"print\"" back_plate.scad
//           openscad.com -o stl/plug.stl       -D "part=\"plug\""  back_plate.scad
// =====================================================================
include <common.scad>

part = "print";      // print | assembly | plug

r_cut = Ab * cos(180 / n_sides) + (HL - corner_rel) * sin(180 / n_sides);   // corner chord distance
ledge_h = ledge_w + ctrl_clr;          // 45 deg ledge underside
y_mid = ctrl_gap + ctrl_depth / 2;

module plate_outline() intersection() {
    ngon(Ab);
    intersection_for (k = [0 : n_sides - 1])
        rotate(-90 + 180 / n_sides + k * 360 / n_sides) translate([r_cut - 400, -200]) square([400, 400]);
}

// Controller pocket (side 0): open from the chamber floor straight through to the wall.
// The base is pushed past the plate edge (open toward the code-0 board). This gives
// LAYOUT-NOTES §4's ">= 2.8 mm everywhere, open window under L1" with room to spare
// (the wall is z_wall below), and full wall-side access for the jig and the joint iron.
module pocket_cut() {
    translate([0, 0, z_pb - 1]) linear_extrude(z_floor - z_pb + 3) offset(delta = ctrl_clr) ctrl_2d(3);
}

// Support ledges, only inside the controller's part-free edge stretches (not on the base:
// the rim fingers carry the base margin). 45 deg underside, top at the controller underside.
module ctrl_ledges() {
    intersection() {
        difference() {
            translate([0, 0, z_ctrl_bot - ledge_h]) linear_extrude(ledge_h) offset(delta = ctrl_clr + eps) ctrl_2d(0);
            hull() {
                translate([0, 0, z_ctrl_bot - eps]) linear_extrude(2 * eps) offset(delta = -ledge_w) ctrl_2d(0);
                translate([0, 0, z_ctrl_bot - ledge_h - eps]) linear_extrude(eps) offset(delta = ctrl_clr) ctrl_2d(0);
            }
        }
        for (f = ctrl_free) if (f[0] != 0)
            translate([0, 0, z_ctrl_bot - ledge_h - 1]) linear_extrude(ledge_h + 2)
                ctrl_edge_strip(f[0], f[1] + 0.3, f[2] - 0.3, ctrl_clr + 1, ledge_w + 1);
    }
}

// Rim fingers under the base margin: inside the free base stretches and >= joint_iron beyond the pad row.
module ctrl_rim_fingers() {
    x_in = j4_halfw + joint_iron;
    for (f = ctrl_free) if (f[0] == 0) {
        x0 = max(-ctrl_base / 2 + f[1] + 0.3, f[1] < ctrl_base / 2 ? -1e3 : x_in);
        x1 = min(-ctrl_base / 2 + f[2] - 0.3, f[1] < ctrl_base / 2 ? -x_in : 1e3);
        if (x1 > x0 + 2) sbox(-x1, -x0, Ab - rim_c, Ab, z_pb, z_ctrl_bot);   // controller x -> global X = -x
    }
}

// Snap tongue frames: origin on the pocket wall, +v (local +Y) points away from the pocket.
module ctrl_hook_frames() {
    for (h = ctrl_hooks) at_ctrl_edge(h[0], h[1], ctrl_clr) children();
}

module hook_slots() {
    hw = hook_w / 2;
    translate([0, 0, hook_root]) linear_extrude(z_floor - hook_root + 2) {
        translate([-hw - hook_slot, hook_t]) square([hook_w + 2 * hook_slot, hook_slot]);
        for (s = [-1, 1]) translate([s > 0 ? hw : -hw - hook_slot, -1]) square([hook_slot, hook_t + 1 + eps]);
    }
}

module hook_lip() {
    hw = hook_w / 2;
    zt = z_floor + 0.25;
    translate([-hw, 0, 0]) rotate([90, 0, 90]) linear_extrude(hook_w) polygon([
        [hook_t, z_floor - 0.01], [0, z_floor - 0.01], [0, z_floor + 0.05], [-hook_over, z_floor + 0.05],
        [-hook_over, zt], [0, zt + hook_over], [hook_t, zt + hook_over]]);
}

module back_plate() {
    difference() {
        union() {
            difference() {
                translate([0, 0, z_pb]) linear_extrude(z_floor - z_pb) plate_outline();
                pocket_cut();
            }
            // controller supports: rim fingers under the base margin, ledges along the free edge stretches
            ctrl_rim_fingers();
            ctrl_ledges();
            // tabs under the board wall edges, where the frame legs snap
            all_sides() for (s = [-1, 1])
                sbox(s > 0 ? leg_x[0] + 0.4 : -leg_x[1] + 0.4, s > 0 ? leg_x[1] - 0.4 : -leg_x[0] - 0.4,
                     Ab - 1.0, tab_out, z_pb, 0);
            // snap-tongue lips over the controller's chamber face
            ctrl_hook_frames() hook_lip();
        }
        // free the snap tongues
        ctrl_hook_frames() hook_slots();
        // relief over the unused J4 pads on sides 1..n-1 (pre-tinned pads stand proud)
        on_sides([1 : n_sides - 1]) sbox(-j4_halfw - 0.8, j4_halfw + 0.8, Ab - j4_relief, Ab + 1, j4_z[0] - 0.5, z_floor + 1);
        // wall puck: recess, post sockets, screw access holes
        translate([-(puck_len / 2 + 0.5), puck_dy - (puck_w / 2 + 0.5), z_pb - 1]) cube([puck_len + 1, puck_w + 1, z_puck_top - z_pb + 1]);
        for (s = [-1, 1]) translate([s * post_x, puck_dy, 0]) {
            translate([0, 0, z_puck_top - eps]) cylinder(d = neck_d, h = neck_len + 2 * eps);
            translate([0, 0, z_puck_top + neck_len]) cylinder(d = barb_d + 0.8, h = z_floor - 1.2 - z_puck_top - neck_len);
            translate([s * (screw_x - post_x), 0, z_pb - 1]) cylinder(d = access_d, h = z_floor - z_pb + 2);
        }
    }
}

// Plug for the screw access holes (rests on the countersunk screw head, top flush with the floor).
module plug() cylinder(d = access_d - 0.15, h = z_floor - z_puck_top - 0.3);

if (part == "print") translate([0, 0, -z_pb]) back_plate();
else if (part == "assembly") back_plate();
else if (part == "plug") plug();
