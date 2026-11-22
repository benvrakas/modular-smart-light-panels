# Roadmap to prototype (rev A)

**Created:** 2026-11-16 against SPEC V6.1. The coordinating session ("Modular Smart Lights Master") keeps this file current. Update the status column when a work package finishes.

## Prototype definition (exit criteria)
Rev A is done when all of these work on a wall:
1. **Three triangle panels** ([decision 0016](decisions/0016-triangle-test-model.md), user 2026-11-21: the triangle is the iterative test model, with the fewest parts and the least printing). Each has 3 passive edge boards and 1 controller board, and they are joined by seam bridges. Hexagon and square follow from the same board generator and parametric parts once the triangle passes; the hexagon gets one optics check first.
2. **Power:** a 24 V supply through an injection bridge.
3. **Cluster controller:** an ESP32-C6 dev board plus a CAN transceiver stands in for the cluster controller. The custom cluster-controller PCB is **not** needed for rev A.
4. **Firmware:**
   - every panel lights all 9 LEDs (RGBW)
   - the loopback counts 9
   - discovery reports the correct adjacency for all 3 panels
   - one effect runs in sync across the panels
5. **Measured:**
   - optics (no visible LED hot spots at the chosen depth)
   - spring contact resistance and current through a bridge
   - 24 V and 5 V rails under full load
   - CAN at 125 and 250 kbps across the 3 panels

Out of scope for rev A: building hexagon and square panels (their boards and parts exist and stay in step with the triangle), AR app, coordinator, voxel effects, custom cluster-controller PCB, isolating bridges.

## Order of work and why
The two physical unknowns, **optics depth** and **spring contact zone**, set the edge board height and the contact strip. So:
- **De-risk in parallel with design.** Cheap tests run while the schematics are drawn.
- **Layout last.** Layouts start from estimates and are finalised before ordering.
- **One combined JLCPCB order** keeps shipping cost and wait time down.

## Work packages

| # | Package | Depends on | Owner | Status |
|---|---|---|---|---|
| **P0 — de-risk and setup (start now)** |||||
| 0.1 | Spring datasheet → bridge numbers | — | coordinator | **Done**: 30 mΩ, 60–80 gf, 20k cycles, working height 3.0–3.5 mm, no current rating. Seam ≈6.8–7.8 mm (d ≈3.4–3.9). |
| 0.2 | ~~Optics test rig with LED strip~~ **Dropped (user, 2026-11-16):** the optics test runs on the rev A boards instead (see 3.2). A partial rig model is kept in `mechanical/archive/optics-test/` for reference. | — | — | Dropped |
| 0.3 | Buy the test and bring-up kit (see shopping list below) | — | **user** (I can't place orders) | Waiting |
| 0.4 | **LED height on the edge board: as low as possible** (decided 2026-11-16, see below). Panel depth is then tuned on the rev A boards using the frame's adjustable diffuser height (1.6, 3.2). | — | coordinator | Decided |
| 0.5 | Toolchains: OpenSCAD (installed, 2021.01), RISC-V GCC for CH32V203 (MounRiver Studio or xPack), ESP-IDF for ESP32-C6 (≈3–5 GB) | — | **user**, when starting firmware | Deferred |
| **P1 — design rev A** |||||
| 1.1 | Controller board schematic (new 4-layer project `hardware/controller-board/`), from the V5 active schematic, with the 24 V changes (decision 0010) | — | schematic agent | **Done** (ERC 0), incl. PTC F1 (V6.2.1) |
| 1.2 | Passive edge board schematic V6: controller-joint pads, code-0 population option, +24V, LED decoupling on +5V | — | schematic agent | **Done** (ERC 0) |
| 1.3 | Edge board layout: hexagon outline (94.1 mm), minimum height, contact strip per the spring data | 1.2, (0.4 to finalise H) | PCB agent | **Done** (H 13.5, DRC 0) |
| 1.4 | Controller board layout: trapezoid (60° sides, base ≤72 mm), parts on one side, joint pads matched to 1.3 | 1.1 | PCB agent (controller) | **Done** (DRC 0; fab outputs in hardware/controller-board/output/fab/) |
| 1.5 | Bridge PCB: standard + injection variants, BW0019CG springs on both faces, plus a spring test coupon | 0.1, 1.3 (pad positions) | PCB agent | **Done** (bridge + injection variant + coupon, DRC 0) |
| 1.6 | Panel mechanics CAD: hex frame (board slots, corner holders), back plate with controller pocket, wall mount, bridge carrier, **diffuser retention with adjustable height above the board top (risers, e.g. 0/3/6/10 mm)** so the optics test can run on rev A | 1.3, 1.4 | mechanical agent | **First pass done in SolidCraft** (mechanical/solidcraft/). The back plate, frame and bezel are parametric with Hexagon / Square / Triangle configurations; the clip and edge cover are universal. The mixed cluster assembly (2 hexagons, 1 square, 2 triangles, all board STEPs) has no interference. Open: test-print tuning |
| 1.7 | Firmware v0, node (CH32V203): clocks, CAN, SK6812 RGBW SPI+DMA driver, loopback counter, LED-rail switch, discovery ADC/DRIVE, simple test effect | 0.5 | firmware session (user starts it later) | Deferred |
| 1.8 | Firmware v0, controller (ESP32-C6 dev board): TWAI CAN, enumeration, discovery scheduling, time sync, effect broadcast; shared protocol header in `firmware/common/protocol/` | 0.5 | firmware session (user starts it later) | Deferred |
| 1.9 | **Design review gate:** ERC/DRC, interface contract checks, LCSC/JLC stock and BOM, cost | 1.3–1.5 | coordinator (review agent) | Started |
| **P2 — order (user action)** |||||
| 2.1 | Single JLCPCB order:<br>• 4 triangle kits of edge boards (9 needed + spare; decision 0016)<br>• 4 controller boards<br>• 8 standard + 2 injection bridges<br>• spring test coupon<br>• stencils | 1.9 | **user** | — |
| 2.2 | Print the Triangle-configuration back plates, frames and bezels for 3 panels, plus bridge clips and edge covers (`mechanical/solidcraft/stl/*_triangle.stl`, finest mesh) | 1.6 | **user** | — |
| 2.3 | **Soldering and assembly jigs (noted 2026-11-21, not started):** printed jigs/fixtures for every hand step. Corner joints: a ring jig that holds the six edge boards at 120° while the corners are soldered (the frame has closed corners now and is no longer the jig); the controller-to-edge-board 90° joint; bridge-into-carrier and edge-board-into-frame fitting; the spring-coupon stack; the stencil and paste holder for the boards you reflow yourself; a pogo-pin test jig for the controller (TP1–TP9, with relief for L1) and edge boards (test before assembly); the Dual Lock and spacing-gauge placement. Follow the FDM rules (decision 0013). How many are needed depends on whether JLC assembles the boards (PCBA) or you reflow them. | 1.6, 2.1 | mechanics agent (when asked) | Deferred |
| 2.0 | **Pre-order fix, edge board J4 (raised by the user 2026-11-21):** only z 3.5–5.0 of each J4 pad sits below the controller's underside (z 5.0), where the drag-solder fillet forms; the top 0.7 mm is behind the controller's edge. Extend the pads down, to z ≈ 2.5–3.0 (2–2.5 mm exposed), keeping the top ≈0.3–0.4 mm above z 5.0 so solder wicks into the gap. This needs the tracks that run under J4 rerouted: DRIVE at z 2.9, GND at 3.15 and +5V_LED at 2.6, with D_IN, SPARE and LED1_DI lower. No vias are allowed there (contact-strip rule area to z 5.3 at abs(x) < 25). Check that the back-plate pocket and the J1 pads still match. | 1.3 | PCB agent | **Done (V6.9.2):** pads z 2.5–5.35 on all three boards; low band moved to z 0.5–2.05; DRC/parity 0; assembly shows no interference |
| 2.0b | **Pre-order fix, edge board R3 (raised by the user 2026-11-21):** R3 sits on the inward face under LED1 at z 4.4 (x = −LO − 3.35), inside the back-plate edge-part groove (z 3.4–5.4, 1.2 mm deep). The edge boards are soldered into a ring before they go into the back plate and drop in along z, so R3 hits the plate wall above the groove and the ring can't be inserted. Move R3 up to the free band above z 6.8 (beside the LEDs and C1/C3, z ≈ 7–12), reroute its tracks, and re-run DRC on all three shapes. Then remove the groove from `back_plate.sc` (band features in gen_back_plate.py) so that the inward-face rule becomes simply: no parts below z 6.8. Update decision 0015, LAYOUT-NOTES.md, the board STEPs and the stand-in boards (`edge_board_standin.sc`, which still has R3 at z 4.4). | 1.3 | PCB agent, then mechanics | **Done (V6.9.2):** R3 is an 0402 (C17168, basic) at z 7.2 under LED1's DIN pad; groove removed from the back plate; DRC/parity 0; STEPs, fab sets, BOMs and stand-ins regenerated |
| 2.0c | **Pre-print CAD fix, bridge clip key engagement (raised by the user 2026-11-21):** the user expects the keys to be too shallow to hold the seam. Today the clip base is 3.5 mm (`clip_t`, z −4.3 to `z_back` −0.8) and each key rises only 1.5 mm into the back-plate groove (to `key_top` 0.7), of which 1.1 mm is straight wall under the 0.4 mm chamfer. Make the base thinner (e.g. 2.0–2.5 mm, bottom still flush at z −4.3, so `z_back` and the recess ceiling drop by 1.0–1.5 mm) and give that room to the keys, which then engage ≈2.5–3 mm. Check: the snap arms and teeth (they're `clip_t` thick, so they get more flexible: re-tune `tooth_h`), the tooth notches and recess depth in `back_plate.sc`, the frame hook pockets (`latch_z` −2.3) next to the recess, the bridge slot depth, the edge cover (same key), and the ≥0.75 mm walls. Re-export the clip, edge cover and back-plate STLs. | 1.6 | mechanics | **Done (V6.9.2):** base 3.0 mm, keys to z 1.2 (2.5 mm engagement, 2.2 straight), chamfer on the key only, teeth 0.7 mm; all STLs/STEPs re-exported; no interference |
| **P3 — bring-up** |||||
| 3.1 | Bench: 24 V → 5 V/3.3 V rails, SWD flashing, LEDs + loopback on one controller + one edge board | 2.1, 1.7 | user + coordinator | — |
| 3.2 | Assemble 1 panel: corner joints, controller joint. Run discovery codes and calibrate thresholds. **Optics test:** photograph the lit panel with 1 and 2 film layers at the fixed film height (no riser, decision 0014); if hot spots show, make the frame cap taller for rev B. | 3.1 | user | — |
| 3.3 | Measure bridge contact resistance and current; assemble 3 panels on the wall; CAN at 125/250 kbps; synced effect | 3.2, 1.8 | user + coordinator | — |
| 3.4 | Write up results, update SPEC/decisions, list rev B changes | 3.3 | coordinator | — |

## LED height on the edge board (decided 2026-11-16)
- **Rule:** place the LEDs **as low on the board as possible**: just above the controller-joint pads and the back plate. The LED centre lands at roughly y ≈ 6–7 mm on a ≈12–13 mm board.
- **Why:**
  - The 5050 LEDs face straight into the panel with a ≈120° cone.
  - Mounted low, the lower half of that cone lands on the white back plate (and the controller board's white top) and bounces before reaching the film.
  - The direct upper half has the longest possible path to the diffuser, so the bright band near each edge is weakest.
  - Mid-height cuts that path roughly in half. Near the top is worst: the film sits right in front of the LEDs.
- **Depth:** the remaining knob is how high the frame holds the diffuser above the board top, adjustable on rev A.

## Shopping list for P0 (user to buy)
Exact part numbers are in [docs/bringup/shopping-list-p0.md](bringup/shopping-list-p0.md).
- **Optics (tested on rev A, no LED strip):** LCD-style diffuser film samples (2–3 haze grades), and white PETG for the back plate.
- **Firmware bring-up:**
  - CH32V203 dev board ×2
  - WCH-LinkE programmer
  - ESP32-C6 dev board
  - 3 × CAN transceiver breakouts (TCAN1044 or SN65HVD230 for bench use)
  - 24 V supply (≥60 W, Class 2)
  - a cheap logic analyzer
- **Springs:** 50 × BW0019CG-L3.5W1.5H4.3 (C2826517). They can also come with the JLC order.

## Coordination rules
- Each agent owns its own folders and **does not edit SPEC.md or decision records**. It reports changes to the coordinator, who updates the spec. This avoids conflicting edits.
- Interfaces between packages, such as the joint pads and the contact pad positions, are agreed through the coordinator before layout is final.
- Minimum constraints: every constraint comes with its reason (see memory/CLAUDE.md conventions).
