# MECH-NOTES: panel mechanics, rev A (roadmap WP 1.6)

**Date:** 2026-11-21 · **Against:** SPEC V6.2.2 (no later decision records), decisions 0002, 0004, 0009, 0011; controller `LAYOUT-NOTES.md` (finished layout); edge-board `.kicad_pcb` (in progress) · **Status:** parametric first cut. The controller numbers are final; the edge-board and bridge numbers are provisional (§1).

Every number comes from `params.scad`, which cites a source for each one. Edit values there, then run `sh make_all.sh` to regenerate all STLs, PNGs and the film template (≈10 min). `-D` on `assembly.scad` doesn't reach the part modules; on a part file it does.

## 0. What was built

| File | Part | Material |
|---|---|---|
| `frame.scad` | **Frame ("crown")**: board groove, inward lip, exterior wall, open corners (the corner holders), 12 snap legs | white PETG |
| `back_plate.scad` | **Back plate**: chamber floor and reflector, controller pocket, tabs for the snap legs, puck sockets; `part="plug"` gives the access-hole plug | white PETG |
| `diffuser.scad` | **Diffuser retention**: risers 3 / 6 / 10 mm, bezel, film cut template | white PETG |
| `bridge_carrier.scad` | **Bridge carrier**: holds the 0.8 mm bridge upright in the seam | PETG |
| `wall_puck.scad` | **Wall mount**: a screwed bar with two snap posts | PETG |
| `assembly.scad` | Views: `cluster` (the 3-panel rev A wall), `panel`, `exploded`, `section2d` (seam), `ctrl2d` (controller pocket) | — |
| `common.scad`, `params.scad` | Helpers and mock PCBs; every interface value | — |

Outputs:
- `stl/`: frame, back_plate, plug, wall_puck, bridge_carrier, riser_3/6/10, bezel. `stl/square/` and `stl/triangle/` were generated from the same parameters but are **unchecked and not for rev A**.
- `film_template.dxf` / `.svg`
- `png/`: parts, assembly (CGAL `--render` plus coloured `_color` previews), and two labelled cross-sections: `section_seam.png` and `section_controller.png`.

### Values taken from the PCB files (2026-11-20/21)

| Value | Taken from | Was |
|---|---|---|
| Board height **H = 13.5** | `edge-board-passive.kicad_pcb` outline (94.1 × 13.5) and `build_edge_pcb.py` | 13.0 (SPEC §10 item 17 estimate) |
| Contact-strip rule area to z 5.3, in-pad vias at 5.7, so **spring contact ≤ z 5.0** including tolerances | `gen_footprints_v6.py` | 6.2 |
| TP11 (+5V_LED) at x −28.3, z 2.6 and TP1 (SPARE) at x 14.6, z 1.6, both on the inward face; TP10 / TP3 on B.Cu at z 9.6 / 11.4 | edge `.kicad_pcb` | TP11 at z 11.9 (needed a lip notch; it no longer does) |
| Corner pads, J4 (z 3.5–5.7, \|x\| ≤ 12.08), contact pads X1–X10 | edge `.kicad_pcb` (pads measured) | unchanged |
| **LED centres z 9.8** (body 7.3–12.3) | coordinator message, controller LAYOUT-NOTES §8.5 | 9.4 |
| Controller outline 72.0 × 24.0, top 44.29, R1, 1.6 thick | controller `.kicad_pcb` outline + LAYOUT-NOTES §1 | same (layout_build.py) |
| Controller underside z 5.0, top z 6.6 | LAYOUT-NOTES §2, §4 | same |
| Pocket: ≥ 2.8 mm below the underside everywhere, open under L1 (7.5 × 7.5 around (−18.0, 19.6)) | LAYOUT-NOTES §4 | SPEC "≥ 5 mm" |
| Part-free edge stretches (≥ 1.5 mm deep) for ledges and snap hooks | LAYOUT-NOTES §4 (`ctrl_free`) | continuous ledge |
| Iron access at both ends of the J1 pad row | LAYOUT-NOTES §2 | fingers started at the pad-row ends |
| Test pads TP1–TP9 in the right wedge (TP2–TP6 SWD), TP10–TP13 | LAYOUT-NOTES §5 | — |

### Coordinates and the height stack (hexagon)
- z = 0 is the edge boards' wall edge, and +z points at the viewer.
- Side 0 is the code-0 side, with its normal along −Y.
- Board x (as the PCB files use it, seen from the inward face) = −X.
- Controller x (seen from F.Cu) = −X.

| z (mm) | What |
|---|---|
| −3.0 | wall surface (**new**: the panel stands 3 mm off the wall) |
| −3.0 … 1.2 | wall puck; its top face sets the panel's height |
| −3.0 … −0.3 | carrier base, under both panels' board edges, 0.3 mm clear |
| −2.7 … 7.5 | frame snap legs, in the seam at \|X\| 30–36.5 |
| −2.0 … 7.0 | bridge PCB (assumed), in the carrier slot from −2.0 to 2.0 |
| −0.8 … 0 | back-plate tabs under the board wall edges |
| −0.8 … 6.6 | back plate; its top face is the chamber floor (SPEC §10 item 17) |
| 0 … 13.5 | edge boards; contact pads 0.3/0.6/0.9 … 6.0; spring contact at 3.5 (≤ 5.0) |
| 0.5 … 5.0 / 5.0 … 6.6 | controller parts (L1 is the deepest; 3.5 mm of air under it to the wall) / controller board, white top flush with the floor |
| 7.3 … 12.3 | LED bodies |
| 7.5 … 13.65 | frame exterior wall (above the bridge); lip at 12.8 … 13.65 |
| 13.65 … 15.65 | frame cap; this is the film seat with no riser |
| 15.65 + riser | film; the bezel (2.0 mm) sits on top |

**Film height above the board top:** 2.15 mm (no riser), 5.15 (3 mm riser), 8.15 (6), 12.15 (10).

**Panel depth from the wall to the bezel top:** 20.85 / 23.85 / 26.85 / 30.85 mm.

**Frame size:** 172.6 mm across the flats, 199.3 across the corners (fits a 220 mm bed). The visible gap between panels is 0.6 mm.

### Load paths (snap fits only, no glue)
- **Springs push each board inward (≈7 N).**
  - At the bottom, the back-plate rim takes it (0.25 mm gap), directly behind the contact strip.
  - At the top, the frame lip takes it.
  - Opposite sides cancel through the plate in compression.
  - On the code-0 side the rim is open for \|X\| < 37 (the controller pocket). There the board bears on the controller's base edge (0.2 mm gap), which the plate holds through the rim fingers and ledges. The solder joint is not loaded in tension.
- **Frame to plate:** the plate's 12 tabs sit under the board wall edges, and each leg's 45° barb snaps under a tab. Boards are captured in z between the groove ceiling and the tabs.
- **Controller:**
  - Below it: rim fingers under its base margin at \|x\| 18.3–33.9 (1.25 mm deep). They stop 6 mm beyond each end of the J1 pad row, leaving iron access.
  - Below it: 45° ledges (0.7 mm under the board) along the part-free stretches of the slanted sides and the top edge.
  - Above it: three snap-tongue lips (0.4 mm over the white face) at right side s 19.8, left side s 17.3 and top s 6.8 (LAYOUT-NOTES edge coordinates).
- **Panel to wall:** two split-tube snap posts on the puck engage sockets in the plate. The 45° barbs release with a firm pull.
- **Carrier:** it floats.
  - It is trapped between the wall and the two panels' board edges.
  - The balanced springs centre it across the seam.
  - The snap legs bound it along the seam (±0.5 mm).
  - **The pucks, not the carrier, locate the panels and take the springs' push-apart force** (see proposed SPEC change P1).

### Assembly order
1. Put the frame cap-down on the bench and drop the six boards into the groove: wall edge up, exterior face out, code-0 board on side 0.
2. Drag-solder the six corner joints. The inward pads are reached from inside; the exterior pads through the corner windows.
3. Press the controller into the back-plate pocket, white side up. Three tongues click over its edge.
4. Lower the plate into the board ring with the controller base along the code-0 board. Its 12 tabs push the legs out and the barbs snap under them. Press progressively from one side (§3, Q2).
5. Drag-solder the controller joint from the wall side, through the open pocket. The iron reaches along the inner corner from either end of the pad row.
6. Bring-up: the pogo jig reaches the controller test pads from the wall side through the open pocket (the panel lies face down). No separate jig hole is needed.
7. Fit the diffuser: riser (optional) pins into the cap holes, then the film, then the bezel.
8. Mount on the wall:
   1. Snap the puck onto the panel. Hold the panel against its already-mounted neighbours, with the carrier and bridge slid under the neighbour's board edge first.
   2. Drive the two screws through the plate's access holes.
   3. Push in the plugs.

## 1. Values the PCB layouts must confirm

| # | Value assumed | Used for | Source now | Owner |
|---|---|---|---|---|
| E1 | Board height **H = 13.5** | groove depth, lip, cap, film height | edge `.kicad_pcb` | edge-board layout |
| E2 | Board length **94.1** (d = 3.5, t = 1.6), square-cut ends | groove, corner geometry | SPEC §2 formula, edge `.kicad_pcb` | edge layout / bridge prototype (d) |
| E3 | **LED centres z 9.8**, body 7.3–12.3, 1.6 mm proud | lip bottom at z 12.8 (0.5 mm margin), floor at 6.6 | coordinator / controller LAYOUT-NOTES | edge layout (not in the `.kicad_pcb` yet: it still has 9.4) |
| E4 | **Inward face below z 6.6 carries only flat copper:** J4 pads (z 3.5–5.7, \|x\| ≤ 12.1), corner pads (2.0 mm from each end), TP1 and TP11 | the plate rim bears there; it is relieved 0.5 mm over J4 on sides 1–5 and cut back 3.0 mm from each end. **TP1 / TP11 are covered by the rim after assembly**: probe them before the plate goes in | edge `.kicad_pcb` | edge layout |
| E5 | **Inward face top band z ≥ 12.8 is clear** | frame lip | edge `.kicad_pcb` (highest inward part: R1 body ≈ 11.1) | edge layout |
| E6 | **Exterior face z 0–7.5 at \|x\| 30–36.5 is free of parts** (tracks and mask are fine) | snap legs, 0.15 mm off the face | MECH; currently met | edge layout |
| E7 | Exterior face above z 7.5 is covered by the frame (for \|x\| < 43). **TP10 (z 9.6) and TP3 (z 11.4) on B.Cu are unreachable after assembly.** | — | edge `.kicad_pcb` | edge layout: test the boards before assembly, or move them (Q9) |
| E8 | Nothing below z 0 at \|x\| 30.4–36.1 (the back-plate tabs sit under the wall edge there) | tabs | MECH | edge layout |
| E9 | Corner pads: exterior power pads ≤ 3.0 mm from the end, top at z 12.6; inward signal pads ≤ 2.0 mm from the end, z 0.85–12.15 | corner windows: exterior wall off 4.0 mm from each end below z 13.65; lip off 2.6 mm | edge `.kicad_pcb` | edge layout |
| E10 | Exterior wall-edge bevel ≤ 0.5 mm | — | SPEC §3.3 | edge layout |
| E11 | Spring contact must stay ≤ z 5.0. The bridge sits at nominal 3.5; the carrier can rise 0.3 mm | — | `gen_footprints_v6.py` | bridge layout |
| C1 | Outline 72.0 × 24.0, 60°, R1, 1.6 thick | pocket (+0.3 clearance) | controller `.kicad_pcb`, LAYOUT-NOTES §1 | **confirmed** |
| C2 | Underside z 5.0, top flush at 6.6; base edge 0.2 mm from the code-0 inward face (`ctrl_gap`) | recess, rim fingers | LAYOUT-NOTES §2/§4; the gap is MECH | controller: confirm the 0.2 mm joint gap |
| C3 | Ledges and tongues only on the part-free stretches (LAYOUT-NOTES §4); ledges reach 0.7 mm under the edge, within the ≥ 1.5 mm bands | ledges, tongues | LAYOUT-NOTES §4 | **met by design**; keep the bands if the placement changes |
| C4 | Base margin 1.25 mm deep at \|x\| 18.3–33.9 (inside the free base stretches, 6 mm clear of the pad row) | rim fingers | LAYOUT-NOTES §2/§4 | **met** |
| C5 | Tongue lips 0.4 mm over the chamber face (B.Cu: plain white mask, no openings) | retention | LAYOUT-NOTES §3 | **met** |
| C6 | Parts hang ≤ 4.5 mm below the board. The pocket is open to the wall, with 3.5 mm air under L1 and 5.5 mm under the SMA diodes | — | LAYOUT-NOTES §3/§4 | **met**, see note below |
| B1 | Bridge **length 56 (\|x\| ≤ 28)**, **z −2.0 … 7.0** (9.0 tall), 0.8 thick | carrier slot (56.6 long), frame wall at 7.5 | MECH | bridge layout |
| B2 | Spring dome at **z 3.5 = 5.5 mm above the bridge's bottom edge**; spring contact ends at z ≥ 2.6 | carrier spine top at z 2.0 | footprint note (EDGE) | bridge layout |
| B3 | **Nothing on either bridge face below z 2.2** (the bottom 4.2 mm): the carrier spine walls (1.25 mm) cover it | spine | MECH | bridge layout |
| B4 | Parts on the bridge faces in the seam ≤ 2.5 mm tall (3.1 mm to the board face at d = 3.5) | seam | SPEC §3.3 | bridge layout |
| B5 | Seam: d = 3.5 → 7.0 mm seam → springs at 3.1 mm working height (within 3.0–3.5) | everything | SPEC §3.3, §10 item 11 | bridge prototype |

**Note on C6:** LAYOUT-NOTES §4 reads "open through to the wall: the wall is the floor", which assumes the wall is at z 0. In this design the wall is at z −3.0, so L1 has 3.5 mm of air under it, not 0.5. Their alternative, raising the underside to z ≥ 5.4, isn't needed.

## 2. Print orientation and settings
All parts: PETG, 0.4 mm nozzle, 0.2 mm layers, no supports.

| Part | Orientation | Notes |
|---|---|---|
| Frame | **Cap down** (`part="print"`) | The film seat prints on the bed. Legs stand up as fins. The barbs' undersides are 45°. Bridges only over the 1.9 mm groove gaps. ≈200 mm across the corners. |
| Back plate | **Right side up** (wall side on the bed) | Slicer infill 15 %, ≥ 7 top layers (opacity: the top face is the reflector), 3 perimeters. The ledge undersides are 45°. The tongue lips overhang 0.7 mm (short, prints fine). The puck-recess ceiling bridges 17 mm. ≈75 g. |
| Riser 3 / 6 / 10 | **Top face down**, pins up | 6 corner pins Ø2.4, press fit in Ø2.5 holes. Tune `pin_hole_d` to the printer. |
| Bezel | **Top face down**, pins up | |
| Bridge carrier | **Base down** | Slot = 0.9 mm. Tune `car_slot_clr` so the bridge is a light press fit. |
| Wall puck | **Base down**, posts up | Posts are split tubes. Barb retaining face 45°, lead-in about 30°. |
| Plug ×2 | Upright | Friction fit in the Ø8 access holes. |
| Film | Not printed | Cut from `film_template.dxf` (hexagon, apothem 85.8, corners cut at R 95.05 to clear the pins). One or two layers. |

## 3. Open questions
1. **Seam bridge layout (B1–B4)** sets the carrier slot, spine height and frame-wall height. All are parameters; rerun `make_all.sh` once the bridge is drawn.
2. **Snap force when fitting the back plate.** 12 barbs each need ≈4 N of leg deflection (≈8 N push with friction), so ≈90 N if all engage at once. Press progressively from one side, or reduce `hook_eng` (0.8) or `leg_t` (1.3) after a test print. Hold-off is about the same per barb (≈90 N total); the puck posts release at well below that, so a panel comes off the wall before it comes apart.
3. **Puck screw access holes (Ø8) in the reflector.** Plugs close them. The alternative is a printed spacing gauge (173.2 mm hex pitch) so pucks can be screwed before the panels go on. Is the "panel as gauge" method acceptable?
4. **Free (cluster-edge) bridges**, i.e. the injection bridge or the ESP32 stand-in with a one-sided spring row. With no second panel, nothing traps the carrier and the springs push it away from the panel. Use VHB tape (the 10 × 59 mm base is the only footprint), or add a free-edge carrier variant with screw tabs. Which does the coordinator want for rev A?
5. **Injection supply cable route.** At an internal seam the only exit is along the wall under a back plate (2.2 mm gap). Recommend putting the rev A injection bridge on a free outer edge (see Q4).
6. **Optics:**
   - Cap overhang 1.0 mm over the board tops.
   - Tongue lips (3 × 5 mm, 0.95 mm tall) and tongue slots in the floor.
   - Plugs.
   - The 0.5 mm J4 relief lines on sides 1–5.
   - 1 mm white PETG over infill is somewhat translucent; check the floor's reflectance in the rev A optics test (WP 3.2). Fallbacks: a white film on the floor, or more top layers.
7. **Board retention before the plate is fitted.** Boards sit loose in the groove until the plate snaps in. That's why the order is cap-down (gravity holds them). If that's annoying, add 0.1 mm crush ribs in the groove.
8. **Wall unevenness.** Each panel's height is set by its puck. Carriers float in z (0.3 mm gap). A carrier on a dip of up to ≈2.5 mm still lands the spring contact on the pads (0.9 … 5.0). It can never rise above z 3.8, so it stays under the 5.0 via limit. Larger steps need shimming the puck. Confirm on the wall.
9. **Edge-board test pads.** TP3 and TP10 (exterior, under the frame wall) and TP1 and TP11 (inward, under the plate rim) are unreachable once assembled (E4, E7). That's fine if the boards are tested before assembly; otherwise the PCB agent should move them.
10. **Square and triangle.**
    - They generate from the same parameters: legs, carrier and bridge are universal; frame, plate, risers and bezel are per shape.
    - **The triangle needs a different puck layout:** its controller pocket (24.5 mm deep) passes the panel centre (inner apothem 23.8). The puck is shortened to 38 mm, moved 11 mm toward the far corner, and has one central screw.
    - The controller notes give 4.46 mm between its slanted sides and the triangle's boards, which leaves 3.9 mm of plate for the tongues.
    - Not checked further, and not needed for rev A.

## 4. Proposed SPEC changes (for the coordinator; SPEC.md not edited)
- **P1 §3.3 / §1 "Bridge" / §9: the carrier floats; the panels are located by wall pucks.**
  - SPEC says "The panels' snap fits locate on the carrier" and that the carrier "anchors it to the wall".
  - Proposed: "The carrier is trapped between the wall and the two panels' board edges and centred by the balanced springs. Each panel snaps onto its own wall puck, which locates it and takes the springs' push-apart force."
  - **Why:** a wall-anchored carrier plus a wall-anchored panel over-constrain the seam. A carrier that also holds both panels against separation needs an undercut on the panel that can't be made in a 3.5 mm half-seam without crossing the board.
  - Consequence: one puck per panel, positioned using the already-mounted neighbours.
- **P2 §9 wall mount (new text):** a screwed puck with two split-tube snap posts. The panel stands **3.0 mm off the wall**; its depth is ≈20.9 mm plus the riser (§0).
- **P3 §2 diffuser:** "held in a groove in the printed frame" → "clamped flat between the frame cap (or a riser ring) and a bezel ring registered on corner pins; film corners are cut off". Rev A risers are 0/3/6/10 mm, so the film sits 2.15–12.15 mm above the board top.
- **P4 §10 item 17 (heights):**
  - H = 13.5
  - LED centres z 9.8
  - wall at z −3.0
  - film seat z 15.65 (2.15 above the board top) plus riser
  - frame wall bottom z 7.5, which sets **bridge top ≤ 7.0** and **bridge \|x\| ≤ 28**
  - spring contact ≤ z 5.0
- **P5 §3.5 controller pocket:** replace "≥ 5 mm pocket" with the LAYOUT-NOTES §4 stepped pocket rule (≥ 2.8 mm everywhere, open under L1). Record that the rev A back plate meets it by leaving the pocket open to the wall (wall at z −3.0). That gives wall-side jig and iron access.
- **P6 §3.5 interface contract:** add the mechanical keep-outs. These are reserved, not forbidden: they hold only for the reasons given.
  - Edge board: exterior face z 0–7.5 at \|x\| 30–36.5 reserved for the snap legs.
  - Edge board: inward face top band z ≥ 12.8 reserved for the frame lip.
  - Edge board: nothing below the wall edge at \|x\| 30.4–36.1.
  - Edge board: inward face below z 6.6 flat copper only (it bears on the plate rim).
  - Controller: keep the LAYOUT-NOTES §4 part-free edge stretches (ledges and snap tongues use them).
- **P7 §9 corner hardware:** the frame leaves each corner open below the cap (4.0 mm exterior, 2.6 mm inward), so the corner joints are soldered with the boards already in the frame (the frame is the jig). Only the 2 mm cap spans the corner.
- **P8 §3.5 controller joint:** on the code-0 board the spring push at \|x\| < 37 is carried by the controller's base edge (0.2 mm gap) and the back plate. The solder joint is still not loaded in tension.
