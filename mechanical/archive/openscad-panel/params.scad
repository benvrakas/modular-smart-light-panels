// =====================================================================
//  params.scad -- Modular Smart Light Panels, roadmap WP 1.6 (panel mechanics, rev A)
//  Every interface value lives here, with its source. Part files include this file.
//
//  Sources:  SPEC = SPEC.md V6.2.2 (2026-11-16);  D000x = docs/decisions/000x-*.md
//            EDGE = hardware/edge-board-passive/edge-board-passive.kicad_pcb (2026-11-20 15:15) and its
//                   scripts build_edge_pcb.py / gen_footprints_v6.py (layout in progress, not final)
//            CTRL = hardware/controller-board/controller-board.kicad_pcb (2026-11-20 15:15) and
//                   scripts/layout/layout_build.py (layout in progress, not final)
//            MECH = chosen here (WP 1.6), reasons in MECH-NOTES.md
//  "CONFIRM" marks a value the PCB layouts must still confirm (listed in MECH-NOTES.md §1).
//
//  OpenSCAD 2021.01. Units mm.
//  Panel frame:  z = 0 is the edge boards' WALL EDGE, +z points to the diffuser/viewer.
//  The panel centre is the origin. Side 0 is the code-0 side (controller); its outward
//  normal is -Y. Sides k = 0..n-1 follow counter-clockwise seen from the front.
//  Side-local coordinates: X along the side (global X for side 0), r = distance from the
//  panel centre along the side normal ("apothem").  Board x (as the PCB files use it,
//  seen from the inward face, wall edge down) = -X.
// =====================================================================

/* ---------------- Polygon and seam geometry ---------------- */
n_sides   = 6;        // SPEC §2: rev A builds the hexagon only (D0004)
edge_L    = 100;      // SPEC §2: common edge length on the seam centrelines
seam_d    = 3.5;      // SPEC §2/§3.3, D0004: d = seam/2, board exterior face to seam centreline. CONFIRM (SPEC §10 item 11, bridge prototype)
board_t   = 1.6;      // SPEC §2, §3.5: edge board thickness
board_H   = 13.5;     // EDGE .kicad_pcb outline 94.1 x 13.5 (SPEC §10 item 17 said ~13). CONFIRM (final layout)

alpha     = 180 - 360 / n_sides;                         // corner angle (120 for the hexagon)
board_L   = edge_L - 2 * (seam_d + board_t) / tan(alpha / 2);   // SPEC §2 formula: 94.1 (hex)
HL        = board_L / 2;
As        = edge_L / (2 * tan(180 / n_sides));           // seam-line apothem (86.60 hex)
Ae        = As - seam_d;                                 // board exterior face (83.10)
Ai        = Ae - board_t;                                // board inward face (81.50)

/* ---------------- Edge board features (exterior face = B.Cu, inward face = F.Cu) ---------------- */
strip_half      = 25.0;   // EDGE EdgeContacts_SpringPads: contact-strip rule area x = +-25
strip_top       = 6.0;    // EDGE: pad tops z 6.0 (SPEC §3.3 "contact zone ~6 mm"); rule area to 6.2
pad_x           = [for (i = [0:9]) -22.5 + 5 * i];       // SPEC §3.3 / EDGE: 10 pads, 5.0 mm pitch, 3.0 wide
spring_contact_z= 3.5;    // EDGE footprint note: BW0019CG contact point z 3.5 nominal. CONFIRM (bridge layout)
spring_contact_max = 5.0; // EDGE: rule area to z 5.3, in-pad vias at 5.7: contact incl. tolerances must stay <= 5.0
led_x           = [-31.2, 0, 31.2];   // SPEC §2 interface contract (board x)
led_z           = 9.8;    // coordinator 2026-11-20 / CTRL LAYOUT-NOTES §8.5: LEDs move to z 9.8 (was 9.4,
                          //   SPEC §10 item 17), so the 5050 bottom (7.3) clears the controller top. CONFIRM (edge layout)
led_size        = 5.0;    // SKC6812RGBW 5050 body (D0003)  -> body z 6.9..11.9
led_proud       = 1.6;    // LED body height off the inward face (5050 package)
j4_halfw        = 12.33;  // EDGE ControllerJoint_EdgeBoard: pads x +-11.43, 1.3 wide -> +-12.33
j4_z            = [3.5, 5.7];   // EDGE: J4 pad z 3.5..5.7 (pads present on every board, used on code 0)
corner_pad_in_w = 2.0;    // EDGE CornerJoint: inward signal pads 2.0 mm from the board end, z 0.85..12.15
corner_pad_ex_w = 3.0;    // EDGE CornerJoint: exterior power pads 3.0 mm from the end, z 0.5..12.6
corner_pad_top  = 12.6;   // EDGE: top of the +5V_LED corner pad (exterior face)
tp_inward       = [[-28.3, 2.6], [14.6, 1.6]];   // EDGE TP11 (+5V_LED), TP1 (SPARE): F.Cu D1.5 [board x, z].
                      //   Now low on the inward face: the back-plate rim covers them (no lip notch needed)
tp_dia          = 1.5;    // EDGE TestPoint_Pad_D1.5mm

/* ---------------- Controller board (SPEC §3.5, D0009, D0011) ---------------- */
z_floor     = 6.6;    // SPEC §10 item 17, D0011: chamber floor = controller top = back-plate top
ctrl_t      = 1.6;    // CTRL: 4-layer, 1.6 mm
z_ctrl_bot  = z_floor - ctrl_t;   // 5.0: controller underside (SPEC §10 item 17, EDGE J4 Dwgs line)
pocket_min  = 5.0;    // SPEC §3.5: >= 5 mm pocket for parts facing the wall (L1 is 4.5 mm)
ctrl_base   = 72.0;   // SPEC §3.5 (<= ~72); CTRL .kicad_pcb outline: base 72 (y 100), R1 fillets. CONFIRM
ctrl_depth  = 24.0;   // SPEC §3.5 (20-25); CTRL .kicad_pcb outline: depth 24 (top edge y 76). CONFIRM
ctrl_side   = 60;     // SPEC §3.5: 60 deg sides
ctrl_fillet = 1.0;    // CTRL R_BASE / R_TOP corner fillets
ctrl_gap    = 0.2;    // MECH: controller base edge to the code-0 inward face (drag-solder gap). CONFIRM
ctrl_keepout= 0.7;    // MECH: the ledge reaches ledge_w - ctrl_clr = 0.7 mm under the board edge, only inside the
                      //       free stretches (ctrl_free, >= 1.5 mm deep). Elsewhere the edge is free
ctrl_base_keep = 1.25; // MECH: rim fingers reach 1.25 mm under the base edge, only inside the free base stretches
                      //       beyond joint_iron from the pad row (|x| 18.5 .. 34). CTRL LAYOUT-NOTES §4 bands are 1.5 deep
ctrl_L1     = [-18.0, 19.6, 6.3, 6.3, 4.5];   // CTRL LAYOUT-NOTES §3: L1 FNR6045 [x, y, w, l, h], body <= 6.3 sq, 4.5 max
ctrl_pocket_min = 2.8;  // CTRL LAYOUT-NOTES §4: >= 2.8 below the underside everywhere, open to the wall under L1
                        //   (L1 needs 4.8). This design leaves the whole pocket open to the wall (wall at z_wall).
// CTRL LAYOUT-NOTES §4: part-free edge stretches (>= 1.5 mm deep), [edge, s0, s1] in mm along each edge:
//   edge 0 base (from the left corner), 1 right side (from the base corner), 2 top (from the right corner),
//   3 left side (from the top corner); left/right as seen from F.Cu (the wall side).
ctrl_free   = [[0, 1.8, 23.3], [0, 48.8, 69.8], [1, 1.8, 5.3], [1, 13.8, 25.8],
               [2, 1.8, 11.8], [2, 31.8, 36.3], [3, 1.8, 6.8], [3, 8.8, 25.8]];
ctrl_hooks  = [[1, 19.8], [3, 17.3], [2, 6.8]];   // MECH: snap tongues centred inside free stretches [edge, s]
joint_iron  = 6.0;      // MECH: iron access left free beyond each end of the J1/J4 pad row (CTRL LAYOUT-NOTES §2)

/* ---------------- Seam bridge (SPEC §3.3, D0002) ---------------- */
bridge_t     = 0.8;   // SPEC §3.3: bridge PCB thickness
spring_free  = 4.3;   // SPEC §3.3: BW0019CG free height
spring_work  = [3.0, 3.5];   // SPEC §3.3: working height min..normal
spring_len   = 3.5;   // SPEC §3.3: 3.5 x 1.5 mm body
spring_w     = 1.5;
bridge_len   = 56.0;  // MECH assumption: springs at x +-22.5 (+-0.75) plus routing margin. CONFIRM (bridge layout)
bridge_z_bot = -2.0;  // MECH: bridge bottom edge, sits in the carrier slot. CONFIRM (bridge layout)
bridge_z_top = 7.0;   // MECH assumption: springs reach z 6.1 (root bend), PCB margin above. CONFIRM

/* ---------------- Wall ---------------- */
z_wall       = -3.0;  // MECH: wall surface. 3 mm leaves room for the frame's snap hooks under the boards

/* ---------------- Print and fit (FDM PETG, 0.4 mm nozzle) ---------------- */
wall_min   = 1.2;     // task brief: walls >= 1.2 mm (3 perimeters)
clr_slide  = 0.25;    // sliding fit per face
clr_snug   = 0.15;    // close fit per face (board in groove)
bed        = 220;     // smallest print bed to plan for (SPEC §2: 220-256 mm)

/* ---------------- Frame (crown + legs) ---------------- */
seam_gap   = 0.3;     // MECH: frame outer face this far inside the seam line (0.6 mm visible gap between panels)
Ao         = As - seam_gap;          // frame outer face (86.30)
gclr       = clr_snug;               // board-in-groove clearance per face
cap_t      = 2.0;     // MECH: cap over the board tops; it is the only material over the open corners, and the film seat
lip_w      = 1.0;     // MECH: inward lip over the board top (holds the board against the spring push)
lip_h      = 0.7;     // MECH: lip reaches down to z H-0.7 = 12.3 (LED body top 11.9)
z_skirt    = bridge_z_top + 0.5;     // exterior wall bottom: clears the bridge PCB top (7.5)
corner_zone= corner_pad_ex_w + 1.0;  // exterior wall removed this far from each board end (solder access)
corner_lip = corner_pad_in_w + 0.6;  // inward lip removed this far from each board end (corner beads)
leg_x      = [30.0, 36.5];  // MECH: snap legs, |X| range; outside the carrier (|X| <= 29.5), inside the corner zone
                            //       (triangle: HL 41.15 - 4 = 37.15, so the same legs fit every shape)
leg_t      = 1.3;     // MECH: leg thickness (flexes 0.8 mm outward into the seam when the back plate goes in)
hook_eng   = 0.8;     // MECH: hook engagement under the back-plate tab
z_leg_bot  = z_wall + 0.3;           // legs stop 0.3 mm short of the wall

/* ---------------- Back plate ---------------- */
pclr       = clr_slide;              // plate edge to board inward face
Ab         = Ai - pclr;              // plate apothem (81.25)
z_pb       = -0.8;    // MECH: plate underside (the snap tabs under the board edges are 0.8 thick)
tab_out    = Ae - 0.1;               // tab reaches under the full board thickness
corner_rel = corner_pad_in_w + 1.0;  // plate edge stops this far from each board end (inner corner beads)
j4_relief  = 0.5;     // MECH: plate edge relief over the (unused) J4 pads on sides 1..n-1
ctrl_clr   = 0.3;     // MECH: pocket clearance around the controller outline
ledge_w    = 1.0;     // MECH: support ledges under the controller margin (45 deg underside), in the free stretches
rim_c      = 1.2;     // MECH: rim fingers under the controller base margin (side 0): board y 0 .. 1.25
hook_w     = 5.0;     // MECH: controller snap tongues
hook_t     = 0.9;
hook_slot  = 0.6;
hook_over  = 0.7;     // lip reach over the pocket wall (0.3 clearance + 0.4 on the controller face)
hook_root  = 0.0;     // tongue root height (slot bottom)

/* ---------------- Wall puck (snap mount) ---------------- */
// The triangle's controller pocket reaches past the panel centre, so its puck is shorter and
// sits toward the far corner (not rev A; geometry generated but unchecked).
puck_len   = n_sides == 3 ? 38 : 64;   // MECH
puck_w     = 16;
puck_dy    = n_sides == 3 ? 11 : 0;    // MECH: puck centre offset along +Y (away from side 0)
z_puck_top = 1.2;     // puck top = plate recess ceiling (the puck sets the panel's z)
post_x     = n_sides == 3 ? 12 : 22;   // two posts fix position and rotation
post_d     = 6.0;     // post OD; split tube, 2 prongs
post_id    = 3.4;
post_slot  = 1.2;
barb_d     = 7.0;
neck_d     = 6.3;     // socket neck in the plate
neck_len   = 1.6;
screw_x    = n_sides == 3 ? 0 : 8;     // countersunk wood screw / M3.5, driven through access holes in the plate
screw_d    = 3.8;
screw_head = 7.4;
access_d   = 8.0;     // plate access hole (plug supplied)

/* ---------------- Bridge carrier ---------------- */
car_half   = 29.5;    // MECH: carrier half length (bridge_len/2 + 1.5)
car_w      = 10.0;    // MECH: base width (5 mm each side of the seam; stays clear of the back plates)
car_spine_w= 3.4;     // spine around the bridge slot
car_spine_top = 2.0;  // spine top (spring contact ends start at z 2.6)
car_slot_clr  = 0.1;  // slot = bridge_t + 0.1, with 0.1 crush ribs

/* ---------------- Diffuser stack ---------------- */
riser_set  = [3, 6, 10];   // roadmap WP 1.6: risers 0/3/6/10 mm ("0" = film straight on the frame cap)
pin_d      = 2.4;     // registration pins under risers / bezel
pin_h      = 1.8;
pin_hole_d = 2.5;     // press fit; tune to the printer
pin_hole_h = 1.9;
pin_face   = 2.64;    // MECH: pin centre to the frame's outer faces at a corner (pin wall 1.44 mm)
pin_cr     = (As - seam_gap) / cos(180 / n_sides) - pin_face / sin(90 - 180 / n_sides);
                      // pin circle radius at the corners, outside the film corners (96.6 hex)
bezel_t    = 2.0;
film_t     = 0.2;     // SPEC §2: 0.1-0.3 mm per layer
film_a     = Ao - 0.5;               // film apothem (cut template)
film_cr    = pin_cr - pin_hole_d / 2 - 0.3;   // film corners cut off at this radius

/* ---------------- Misc ---------------- */
$fn = 40;
eps = 0.01;

// ---------------- Derived values and checks ----------------
pr_rot   = (270 - 180 / n_sides) % (360 / n_sides);   // rotates circle($fn=n) so a flat faces -Y
z_cap_top= board_H + gclr + cap_t;                     // film seat with no riser (15.65)
seam_w   = 2 * seam_d;
spring_h_at_d = (seam_w - bridge_t) / 2;               // spring working height this seam gives

assert(n_sides != 6 || abs(board_L - 94.1) < 0.05, "hex board length should be 94.1 (SPEC §2)");
assert(spring_h_at_d >= spring_work[0] && spring_h_at_d <= spring_work[1],
       "seam_d gives a spring height outside 3.0-3.5 mm (SPEC §3.3)");
assert(z_ctrl_bot - z_wall >= pocket_min, "controller pocket shallower than SPEC §3.5");
assert(car_half < leg_x[0] - 0.4, "carrier runs into the snap legs");
assert(leg_x[1] < HL - corner_zone - 0.5, "snap legs run into the corner solder zone");
assert(bridge_len / 2 <= car_half - 1.2, "bridge longer than the carrier slot");
assert(z_skirt - bridge_z_top >= 0.5, "frame wall does not clear the bridge top");
// the carrier can rise 0.3 mm (its gap under the board edges); allow 0.5 mm for spring and placement tolerance
assert(spring_contact_z + 0.3 + 0.5 <= spring_contact_max, "spring contact can rise above the via-free zone");
assert(board_H - lip_h >= led_z + led_size / 2 + 0.3, "frame lip covers the LEDs");
assert(Ao - (Ae + gclr) >= wall_min, "frame exterior wall below 1.2 mm");
assert(2 * Ao / cos(180 / n_sides) <= bed - 10, "frame does not fit the print bed");
assert(film_cr > (Ai - lip_w) / cos(180 / n_sides) + 0.5, "film corner cut opens the chamber corner");

echo(str("PANEL n=", n_sides, "  board_L=", board_L, "  As=", As, "  Ae=", Ae, "  Ai=", Ai,
         "  Ao=", Ao, "  Ab=", Ab, "  across corners=", 2 * Ao / cos(180 / n_sides),
         "  spring height=", spring_h_at_d, "  film seat z=", z_cap_top));
