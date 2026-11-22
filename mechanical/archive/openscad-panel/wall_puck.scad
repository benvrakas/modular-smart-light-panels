// =====================================================================
//  wall_puck.scad -- WP 1.6 wall mount ("puck"), PETG.
//
//  A bar screwed to the wall under the panel centre. Two split-tube snap posts push into
//  sockets in the back plate's underside; their 45 deg barbs catch the socket necks, so a
//  panel snaps on straight toward the wall (the only direction the seam bridges allow) and
//  pulls off with a firm tug. Two posts fix the panel's position and rotation; the puck's top
//  face (z 1.2) sets the panel's height above the wall (wall at z -3.0).
//
//  Mounting: snap the puck onto the panel, offer the panel up against its already-mounted
//  neighbours (the bridges set the seam), then drive the two countersunk screws through the
//  back plate's access holes. Push the printed plugs into the holes afterwards.
//
//  Print: flat side down, posts up. No supports (barb underside 45 deg, lead-in cone 30 deg).
//  Export:  openscad.com -o stl/wall_puck.stl wall_puck.scad
// =====================================================================
include <common.scad>

part = "print";      // print | assembly

module snap_post() {
    // profile [r, z] above the puck top
    zr = neck_len + 0.05;
    zb = (z_wall + 1.2) - z_puck_top - 0.1;          // root on the groove floor
    difference() {
        rotate_extrude($fn = 40) polygon([
            [post_id / 2, zb], [post_d / 2, zb], [post_d / 2, zr],
            [barb_d / 2, zr + (barb_d - post_d) / 2],            // 45 deg retaining face
            [barb_d / 2, zr + (barb_d - post_d) / 2 + 0.3],
            [post_d / 2 - 0.4, zr + (barb_d - post_d) / 2 + 0.3 + 1.5],   // lead-in cone
            [post_id / 2, zr + (barb_d - post_d) / 2 + 0.3 + 1.5]]);
        // split into two prongs
        translate([-post_slot / 2, -5, zb + 0.8]) cube([post_slot, 10, 12]);
    }
}

module wall_puck() {
    h = z_puck_top - z_wall;
    difference() {
        translate([0, 0, z_wall]) linear_extrude(h)
            offset(r = 3) offset(delta = -3) square([puck_len, puck_w], center = true);
        // annular grooves: longer, springier prongs
        for (s = [-1, 1]) translate([s * post_x, 0, z_wall + 1.2]) cylinder(d = post_d + 2.4, h = h);
        // countersunk screws (90 deg head, flush with the top)
        for (s = [-1, 1]) translate([s * screw_x, 0, 0]) {
            translate([0, 0, z_wall - 1]) cylinder(d = screw_d, h = h + 2);
            translate([0, 0, z_puck_top - screw_head / 2 + eps]) cylinder(d1 = 0, d2 = screw_head, h = screw_head / 2);
        }
    }
    for (s = [-1, 1]) translate([s * post_x, 0, z_puck_top]) snap_post();
}

if (part == "print") translate([0, 0, -z_wall]) wall_puck();
else if (part == "assembly") wall_puck();
