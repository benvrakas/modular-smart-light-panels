# 0015 — Square and triangle edge boards: LED spacing per shape, one KiCad project per outline

**Date:** 2026-11-21 · **Status:** Accepted (user asked for the square and triangle boards); updated V6.9.2 (R3 above z 6.8, no back-plate groove, longer J4 pads) · **Relates to:** [0004](0004-per-shape-board-lengths.md) (board length per shape), [0009](0009-rear-controller-board.md) (passive edge board) · **Changes:** SPEC §1 (LED density note), §2 (edge board layout), §3.5 interface numbers

## Context

The user asked for the square and triangle edge boards so the SolidCraft model can use the right board for each shape. Decision 0004 already fixed the board lengths: 94.1 mm (hexagon), 89.8 mm (square), 82.33 mm (triangle). SPEC V6.8.5 still listed the LED positions x = 0, ±31.2 mm as "shared by all shapes".

That rule cannot hold on the triangle board:
- With the outer LEDs at ±31.2, the triangle board has 10 mm between the outer LED's pad edge and the corner pad.
- The end zone needs about 12 mm: the LED data riser, four bus vias, the +24V and GND drops, and the corner pads, all at the 0.2 mm netclass clearance.
- It also breaks the other rule in §1: LEDs evenly spaced, so the gap across a corner matches the gap along the board.

## Decision

- **LED positions per shape, about L_board / 3 each side of centre:**

  | Shape | Board | LEDs (x from board centre) |
  |---|---|---|
  | Hexagon | 94.1 mm | 0, ±31.2 |
  | Square | 89.8 mm | 0, ±29.9 |
  | Triangle | 82.33 mm | 0, ±27.4 |

  LED height is unchanged on all shapes: centred at z 9.8 mm. Nothing in the mechanics depends on LED x.
- **Same circuit, packed ends.** First on the square and triangle boards; since V6.9 on the hexagon too (user: keep the three boards as alike as possible; decision 0016):
  - **C1 and C3** sit at z 9.6, like the hexagon's, in the free gaps between the contact hop columns:
    - C1 at x −15.4, with its +5V pad dropping into the +5V_LED low band;
    - C3 at x +19.8, with its +5V running along the free right low band to LED3's +5V riser.
    - Both are at least 1.4 mm from +24V copper.
  - **R3** (LED1 data link, fitted only on codes 1..n−1) is an **0402 at z 7.2**, just under LED1's DIN pad (since V6.9.2; it was an 0603 at z 4.0–4.8 in a back-plate groove, see below). Its pad 2 sits under the DIN pad (same net); pad 1 is 0.24 mm clear of it and fed by the D_IN via straight below. It lies inside the LED footprint's courtyard (which reaches z 6.9) but 0.45 mm clear of the LED body, so the `.kicad_dru` allows that one courtyard overlap and the clipping of R3's silk by the DIN pad mask.
  - The end zone is packed outward from the LED at 0.2 mm clearance.
  - The triangle uses a 2-via hop on the right to clear the LED3 data riser.
  - **One layout for all three (V6.9):** the hexagon no longer keeps its hand-reviewed layout (archived in `hardware/archive/edge-board-hex-reviewed-2026-11-21/`). All three boards have the same 19 footprints and 166 tracks; only the outer LED x and the end zone move. The right GND hop has 2 vias on every shape.
  - **Superseded first pass (same day):** C1, C3 and R3 all lay under the outer LEDs at z ≤ 6.4. The assembly clash check found C1 and C3 inside the back-plate rim wall (top at z 6.6) and, on side 0, inside the controller board (z 5.0–6.6).
- **Inward-face part zone (all shapes): no 3D part below z 6.8** (only flat copper: J4, test pads, tracks).
  - The back-plate rim wall stands 0.15 mm inside the boards up to z 6.6, and the controller fills z 5.0–6.6 on side 0.
  - **Why no groove (user, V6.9.2):** the board ring is soldered at its corners first and then lowered into the back plate along z. Any part sticking out below the wall top would have to pass the wall above a groove, so the V6.9 groove at z 3.4–5.4 (for R3) made insertion impossible. The groove is gone and the plate edge is plain.
- **J4 pads (V6.9.2, roadmap 2.0):** 1.3 × 2.85 mm at z 2.5–5.35 (were 3.5–5.7), so 2.5 mm of each pad is exposed below the controller's underside (z 5.0) for the drag-solder fillet and 0.35 mm sits behind its edge. The low band under J4 moved down: left LED1_DI z 0.5, D_IN 0.95, +5V_LED 1.5, GND guard 2.05; right SPARE 1.6, DRIVE 2.1. D_IN now dives to B.Cu just past LED1's +5V riser (x −LO − 0.2). +5V_LED passes 0.8 mm below the J4.1 (+24V) pad (was 0.6), with the GND guard between them.
- **One KiCad project per outline:** `hardware/edge-board/edge-board-hex`, `edge-board-square` and `edge-board-triangle`.
  - All three use one circuit: the schematic is generated identically for each.
  - All three are built by one script: `scripts/build_edge_pcb.py OUT.kicad_pcb hex|square|triangle`.
  - Each project has its own `.kicad_dru`, DRC report (`output/drc-<shape>.json`) and fab set (`output/fab-<shape>/`).
  - All three pass DRC with 0 violations, 0 unconnected and 0 parity issues. The +24V adjacency check shows only the known J4.1 item, which has a GND guard.
- **3D:** the LED footprint now carries KiCad's SK6812 PLCC4 5050 model. STEP exports for all three boards are in `mechanical/solidcraft/boards/`.

## Consequences

- The optics test (roadmap 3.2) should check the widest pitch, the hexagon's 31.2 mm, which is the worst case.
- Each shape is its own JLC order (one kit per shape, as decision 0004 already said).
