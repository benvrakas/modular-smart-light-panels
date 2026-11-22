// =====================================================================
//  common.scad -- helpers and mock PCBs shared by the WP 1.6 part files.
//  Part files `include <common.scad>` (this pulls in params.scad too).
// =====================================================================
include <params.scad>

// ---------------- polygon helpers ----------------
function circ(a) = a / cos(180 / n_sides);                 // apothem -> circumradius
module ngon(a) rotate(pr_rot) circle(r = circ(a), $fn = n_sides);

// Polygon ring between apothems a0 and a1, from z0 to z1.
module ring_band(a0, a1, z0, z1)
    translate([0, 0, z0]) linear_extrude(z1 - z0) difference() { ngon(a1); if (a0 > 0) ngon(a0); }

module on_sides(list) for (k = list) rotate([0, 0, k * 360 / n_sides]) children();
module all_sides() on_sides([0 : n_sides - 1]) children();

// +X points at corner k (between side k and side k+1).
module at_corners() for (k = [0 : n_sides - 1]) rotate([0, 0, -90 + 180 / n_sides + k * 360 / n_sides]) children();

// Box in side-local coordinates: X along the side, r = apothem (r grows toward -Y), z.
module sbox(x0, x1, r0, r1, z0, z1) translate([x0, -r1, z0]) cube([x1 - x0, r1 - r0, z1 - z0]);

// Prism with a cross-section given as [r, z] points, running X = x0..x1 (side-local).
module rz_prism(x0, x1, pts)
    translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) polygon([for (p = pts) [-p[0], p[1]]]);

// Controller trapezoid (side-0 local, 2D). y_ext extends the base past the board face.
// y = distance from the code-0 inward face toward the panel centre.
function ctrl_hw(y) = ctrl_base / 2 - (y - ctrl_gap) * tan(90 - ctrl_side);
module ctrl_2d(y_ext = 0) {
    y0 = ctrl_gap - y_ext;
    y1 = ctrl_gap + ctrl_depth;
    polygon([[-ctrl_hw(y0), -Ai + y0], [ctrl_hw(y0), -Ai + y0],
             [ctrl_hw(y1), -Ai + y1], [-ctrl_hw(y1), -Ai + y1]]);
}

// ---------------- controller edges in the CONTROLLER frame (LAYOUT-NOTES §1) ----------------
// Frame: x to the right and y into the board, seen from F.Cu (the wall side); base edge at y = ctrl_gap.
// Global: X = -x, Y = -Ai + y. Edges run in the notes' order: 0 base (from the left corner),
// 1 right side (from the base corner), 2 top (from the right corner), 3 left side (from the top corner).
ctrl_top_hw = ctrl_base / 2 - ctrl_depth * tan(90 - ctrl_side);
ctrl_c = [[-ctrl_base / 2, ctrl_gap], [ctrl_base / 2, ctrl_gap],
          [ctrl_top_hw, ctrl_gap + ctrl_depth], [-ctrl_top_hw, ctrl_gap + ctrl_depth]];
function ctrl_dir(i) = let(a = ctrl_c[i], b = ctrl_c[(i + 1) % 4], d = b - a) d / norm(d);
function ctrl_nrm(i) = let(d = ctrl_dir(i)) [d[1], -d[0]];          // outward normal
function ctrl_pt(i, s) = ctrl_c[i] + s * ctrl_dir(i);
function to_glob(p) = [-p[0], -Ai + p[1]];
function nrm_glob(n) = [-n[0], n[1]];

// 2D strip along edge i, s0..s1, from `outw` outside the edge to `inw` inside it (global coordinates).
module ctrl_edge_strip(i, s0, s1, outw, inw) {
    n = ctrl_nrm(i);
    polygon([to_glob(ctrl_pt(i, s0) + outw * n), to_glob(ctrl_pt(i, s1) + outw * n),
             to_glob(ctrl_pt(i, s1) - inw * n), to_glob(ctrl_pt(i, s0) - inw * n)]);
}

// Place children at s along edge i, local +Y = outward normal, origin on the edge offset by `off`.
module at_ctrl_edge(i, s, off = 0) {
    n = ctrl_nrm(i);
    ng = nrm_glob(n);
    translate(to_glob(ctrl_pt(i, s) + off * n)) rotate(atan2(ng[1], ng[0]) - 90) children();
}

// ---------------- mock PCBs (assembly only, never printed) ----------------
// One edge board in side-local position. Board x = -X (see params.scad header).
module mock_edge_board(code0 = false) {
    color("darkgreen") sbox(-HL, HL, Ai, Ae, 0, board_H);
    // exterior contact pads (B.Cu, gold)
    color("gold") for (x = pad_x) sbox(-x - 1.5, -x + 1.5, Ae, Ae + 0.05, 0.6, strip_top);
    // exterior corner power pads
    color("gold") for (s = [-1, 1]) for (zz = [[0.5, 3.5], [6.0, 8.5], [11.0, 12.6]])
        sbox(s > 0 ? HL - corner_pad_ex_w : -HL, s > 0 ? HL : -HL + corner_pad_ex_w, Ae, Ae + 0.05, zz[0], zz[1]);
    // LEDs on the inward face
    for (x = led_x) color("white")
        sbox(-x - led_size / 2, -x + led_size / 2, Ai - led_proud, Ai, led_z - led_size / 2, led_z + led_size / 2);
    // J4 joint pads (inward face, every board)
    color(code0 ? "gold" : "goldenrod") for (i = [0:9])
        sbox(-(-11.43 + 2.54 * i) - 0.65, -(-11.43 + 2.54 * i) + 0.65, Ai - 0.05, Ai, j4_z[0], j4_z[1]);
    // inward corner signal pads
    color("goldenrod") for (s = [-1, 1])
        sbox(s > 0 ? HL - corner_pad_in_w : -HL, s > 0 ? HL : -HL + corner_pad_in_w, Ai - 0.05, Ai, 0.85, 12.15);
}

module mock_boards() for (k = [0 : n_sides - 1]) rotate([0, 0, k * 360 / n_sides]) mock_edge_board(k == 0);

// Controller board at its rev A position (parts on the wall side). Mirror: controller x (seen from F.Cu) = -X.
module mock_controller() {
    color("white") translate([0, 0, z_ctrl_bot]) linear_extrude(ctrl_t)
        offset(r = ctrl_fillet) offset(delta = -ctrl_fillet) ctrl_2d();
    // L1 inductor, the tallest part (4.5 mm), hanging toward the wall
    color("dimgray") translate([-ctrl_L1[0] - ctrl_L1[2] / 2, -Ai + ctrl_gap + ctrl_L1[1] - ctrl_L1[3] / 2, z_ctrl_bot - ctrl_L1[4]])
        cube([ctrl_L1[2], ctrl_L1[3], ctrl_L1[4]]);
    // joint fillet zone
    color("silver") translate([-12.33, -Ai, z_ctrl_bot - 1.5]) cube([24.66, 2.0, 1.5]);
}

// Seam bridge in side-local position: PCB centred on the seam line r = As, springs on both faces.
module mock_bridge() {
    color("darkolivegreen") sbox(-bridge_len / 2, bridge_len / 2, As - bridge_t / 2, As + bridge_t / 2, bridge_z_bot, bridge_z_top);
    sh = spring_h_at_d;
    color("silver") for (x = pad_x) for (s = [-1, 1])
        sbox(x - spring_w / 2, x + spring_w / 2,
             s < 0 ? As - bridge_t / 2 - sh : As + bridge_t / 2,
             s < 0 ? As - bridge_t / 2 : As + bridge_t / 2 + sh,
             spring_contact_z - 0.9, spring_contact_z + 2.6);
}

// Diffuser film (cut template shape), 2D.
module film_2d() intersection() {
    ngon(film_a);
    // half-planes x' <= film_cr at every corner (corners cut clear of the registration pins)
    intersection_for (k = [0 : n_sides - 1])
        rotate(-90 + 180 / n_sides + k * 360 / n_sides) translate([film_cr - 400, -200]) square([400, 400]);
}
