// =====================================================================
//  assembly.scad -- WP 1.6 rev A panel assembly with mock PCBs (not for printing).
//
//  view = "cluster"  : the rev A wall, 3 hexagons with 3 seam bridges, pucks and carriers.
//                      P0 shows the chamber (no diffuser); P1 / P2 carry the 3 mm riser stack.
//  view = "exploded" : one panel, exploded along z.
//  view = "section"  : P0 and P1 cut through both centres, square to their shared seam:
//                      shows every height (wall, puck, plate, controller, boards, bridge,
//                      frame, riser, film).
//  view = "panel"    : one panel, assembled, riser 3.
//  Parameters are read from params.scad (edit it there; -D on this file does not reach
//  the part modules).
//
//  Render:  openscad.com -o png/assembly_cluster.png --render -D "view=\"cluster\"" assembly.scad
// =====================================================================
include <common.scad>
use <frame.scad>
use <back_plate.scad>
use <wall_puck.scad>
use <bridge_carrier.scad>
use <diffuser.scad>

view = "cluster";
riser_show = 3;

P1 = 2 * As * [cos(-30), sin(-30), 0];
P2 = 2 * As * [cos(30), sin(30), 0];

module panel(riser = -1, ctrl = true, puck = true) {
    color("white") frame();
    color("ivory") back_plate();
    mock_boards();
    if (ctrl) mock_controller();
    if (puck) color("silver") translate([0, puck_dy, 0]) wall_puck();
    if (riser >= 0) diffuser_stack(riser);
}

// seam k of a panel at the origin: carrier + bridge
module seam(k) rotate([0, 0, k * 360 / n_sides]) {
    translate([0, -As, 0]) color("orange") bridge_carrier();
    mock_bridge();
}

module wall(sz = 420) color("tan", 0.5) translate([-sz / 2 + 80, -sz / 2, z_wall - 1]) cube([sz, sz, 1]);

module cluster() {
    panel(-1);
    translate(P1) panel(riser_show);
    translate(P2) panel(riser_show);
    seam(1); seam(2);
    translate(P1) seam(3);
}

module exploded(e = 14) {
    translate([0, 0, -2 * e]) color("silver") translate([0, puck_dy, 0]) wall_puck();
    translate([0, 0, -e]) { color("ivory") back_plate(); mock_controller(); }
    mock_boards();
    translate([0, 0, e]) color("white") frame();
    translate([0, 0, 2 * e]) diffuser_stack(riser_show, e);
    translate([0, 0, -2 * e]) seam(1);
}

// Cut plane through P0 and P1 centres (direction -30 deg), moved 2.5 mm so it passes
// through a spring (pads at x = +-2.5): keep the far half.
module section() {
    intersection() {
        union() { panel(riser_show); translate(P1) panel(riser_show); seam(1); }
        rotate([0, 0, -30]) translate([-150, -2.5, -20]) cube([2 * As + 300, 200, 80]);
    }
}

// Cut through the controller pocket (plane X = 18, through L1), panel P0 only.
module section_ctrl() {
    intersection() {
        union() { panel(riser_show); seam(0); }
        translate([-ctrl_L1[0], -150, -20]) cube([200, 300, 80]);
    }
}

// ---------------- 2D sections (one colour per part, labelled z levels) ----------------
module cut2d(c) color(c) projection(cut = true) children();

// Section transforms: the cut plane becomes z = 0, panel z becomes 2D y.
module Tsec(mode) {
    if (mode == "seam") rotate([-90, 0, 0]) translate([0, 2.5, 0]) rotate([0, 0, 30]) children();
    else rotate([0, 0, 90]) rotate([0, 90, 0]) translate([ctrl_L1[0], 0, 0]) children();
}

module parts_2d(mode, offsets, h) {
    for (p = offsets) {
        cut2d("lightgray") Tsec(mode) translate(p) frame();
        cut2d("wheat") Tsec(mode) translate(p) back_plate();
        cut2d("darkgreen") Tsec(mode) translate(p) mock_boards();
        cut2d("steelblue") Tsec(mode) translate(p) mock_controller();
        cut2d("dimgray") Tsec(mode) translate(p + [0, puck_dy, 0]) wall_puck();
        if (h > 0) cut2d("silver") Tsec(mode) translate(p + [0, 0, z_cap_top]) riser(h);
        cut2d("deepskyblue") Tsec(mode) translate(p + [0, 0, z_cap_top + h]) linear_extrude(film_t) film_2d();
        cut2d("gray") Tsec(mode) translate(p + [0, 0, z_cap_top + h + film_t]) bezel();
    }
}

module z_levels(x0, x1, h) {
    lv = [[z_wall, str("wall z ", z_wall)], [0, "board wall edge z 0"],
          [spring_contact_z, str("spring contact z ", spring_contact_z)],
          [z_ctrl_bot, str("controller underside z ", z_ctrl_bot)], [z_floor, str("floor z ", z_floor)],
          [z_skirt + 0.9, str("frame wall bottom z ", z_skirt)],      // label offset so it clears "floor"
          [board_H, str("board top z ", board_H)], [z_cap_top + h, str("film z ", z_cap_top + h)]];
    for (l = lv) color("red") {
        translate([x0, l[0] - 0.03]) square([x1 - x0, 0.06]);
        translate([x1 + 1, l[0] - 0.5]) text(l[1], size = 1.0);
    }
}

module seam_section_2d(h = riser_show) {
    parts_2d("seam", [[0, 0, 0], P1], h);
    cut2d("orange") Tsec("seam") seam_parts_carrier();
    cut2d("olive") Tsec("seam") seam_parts_bridge();
    z_levels(As - 25, As + 25, h);
}
module seam_parts_carrier() rotate([0, 0, 360 / n_sides]) translate([0, -As, 0]) bridge_carrier();
module seam_parts_bridge() rotate([0, 0, 360 / n_sides]) mock_bridge();

module ctrl_section_2d(h = riser_show) {
    parts_2d("ctrl", [[0, 0, 0]], h);
    z_levels(40, 95, h);
}

if (view == "cluster") { cluster(); }
else if (view == "section2d") seam_section_2d();
else if (view == "ctrl2d") ctrl_section_2d();
else if (view == "exploded") exploded();
else if (view == "section") section();
else if (view == "section_ctrl") section_ctrl();
else if (view == "panel") panel(riser_show);
