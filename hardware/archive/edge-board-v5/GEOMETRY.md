# Edge board — outline geometry (length per shape, minimum height)

**Date:** 2026-11-15 · **Against:** SPEC V5.5 · **Status:** working numbers for layout. The board-length finding (§1.3) was adopted as decision 0004 (one schematic, one outline per shape). H = 22 mm comes from placement (decision 0005, accepted).

Coordinates: x runs along the board (0 = midpoint of the polygon edge), and y runs up from the **wall edge** (y = 0) toward the diffuser.

## 1. Board length per shape

### 1.1 Model
- **Panel edge = 100 mm**, taken as the tiling grid line. That is the seam centreline, so tiles of every shape line up.
- **d** is the distance from the grid line to the board's exterior face. With the seam bridge (SPEC §3.3), d ≈ half the seam ≈ **3.5 mm** (seam ≈ 6–8 mm).
- **t** is the board thickness, 1.6 mm.
- **Corner joint:** the two boards' **inward faces meet at the inner vertex**, with ends cut square. This is the longest board that fits, and it puts the corner signal pads (inward face) right at the joint. The exterior faces leave a small wedge gap at the outside corner.

**L_board = 100 − 2·(d + t)·cot(θ/2)**, where θ is the polygon's interior angle (60°, 90°, 120°).

### 1.2 Results (mm)

| d | Triangle (θ 60°) | Square (θ 90°) | Hexagon (θ 120°) |
|---|---|---|---|
| 0 (board face on the grid line) | 94.46 | 96.80 | 98.15 |
| 2.0 | 87.53 | 92.80 | 95.84 |
| 3.0 | 84.07 | 90.80 | 94.69 |
| **3.5 (seam bridge, recommended)** | **82.33** | **89.80** | **94.11** |
| 4.0 | 80.60 | 88.80 | 93.53 |

- **Fab and assembly allowance:** take ≈0.2 mm off each end (outline tolerance ±0.1–0.2 mm), so the ends don't collide. For example, the hexagon board becomes **93.7 mm**.
- **Outside-corner gap** between the two boards' exterior faces is 2·t·sin((180° − θ)/2): **2.8 mm** (triangle), **2.3 mm** (square), **1.6 mm** (hexagon). The +12V/GND strap across the outside corner (corner pads 7/8 on B.Cu) has to span this.

### 1.3 Consequence: one length cannot fit all shapes
The triangle board is ≈12 mm shorter than the hexagon board. Options:
1. **One schematic, three board outlines** (triangle, square, hexagon). The layout stays the same except where the corner joints sit. The contact strip and LEDs are centred, and only the board ends move. Each shape already gets its own fab panel (the "hex kit" in gap A3), so this adds little cost. **Recommended.**
2. One short board (the triangle length) for every shape, with corner pieces filling the 4–6 mm gaps on squares and hexagons. The corner pads then don't meet, so each corner needs a bridging part. Not recommended.

## 2. Minimum board height

### 2.1 Stack-up from the wall edge (y = 0)

| Zone | y (mm) | What sets it |
|---|---|---|
| Contact strip (B.Cu pads, no pour/vias) | 0 – 8.5 | Pads run to 8.0 mm, plus the keepout margin (SPEC §3.3). On F.Cu this band takes parts whose traces escape upward without vias. |
| Signal-via row | 8.5 – 9.5 | Five signal vias, from F.Cu routing to the B.Cu pads, just above the strip |
| B.Cu +12V lane | 9.5 – 12.5 | ≥2.8 mm for 5 A feed-through ([LAYOUT-NOTES](LAYOUT-NOTES.md) §2). Lowest, because J1's +12V pads are at the wall edge. |
| Lane gap | 12.5 – 13.0 | |
| B.Cu GND lane | 13.0 – 16.0 | ≥2.8 mm. Sits between the two supplies, so +12V copper never runs beside +5V (V5.3). |
| Lane gap | 16.0 – 16.5 | |
| B.Cu +5V lane | 16.5 – 18.0 | LED rail, ≤0.73 A falling ≈0.12 A per board; ≈1.5 mm |
| Gap / GND or ≥0.5 mm | 18.0 – 18.5 | Separates +5V from the bus; DRIVE is never next to +5V |
| **B.Cu signal bus** (CANH, CANL, SENSE, DRIVE) | ≈18.5 – 20.3 | **V5.5 / decision 0005 (accepted):** moved off F.Cu so the LED row and MCU region aren't cut by a strip |
| LED row (F.Cu) | ≈13 – 18 (placed at y = 15.5) | SKC6812RGBW body 5.0 mm, VDD via to +5V, GND via to the GND lane. The LEDs must sit above the back reflector (assumed ≤ y ≈ 3 mm). |
| Top margin | 20.3 – 22.0 | Clearance to the board top edge and the frame/diffuser groove |

> **V5.5 result (PCB placement, output/placement-trial/NOTES.md):**
> - **H = 22 mm.** All 67 parts are placed with 0 courtyard overlaps, on the hexagon outline (93.7 mm) and on the triangle-length check (81.9 mm). The core sits within |x| ≤ 37.0 mm.
> - **Why 22:** H = 20 fails (11 top-row parts above the limit). H = 24 is needed if the bus stays on F.Cu.
> - **Status:** the exterior signal bus is accepted (decision 0005, approved by the user on 2026-11-15).
> - **History:** this replaces the V5.3 estimate of H ≈ 24–25 mm and the V5.2 stack (LEDs on +12V, two lanes).

- **Passive board minimum ≈ 17.5 mm.**
- **Active board:** the MCU section (≈330 mm² of parts and courtyards, ≈650 mm² with routing) goes **beside the contact strip** (|x| > 25 mm, between the strip and the corner joints) and in the F.Cu band under the strip (y < 8.5, no vias there). It also has to avoid the LEDs.
  - **Triangle** (half-length ≈41 mm, ≈12 mm free per side): fits at ≈18–20 mm, but it is the tightest case.
  - **Hexagon** (≈18 mm free per side): fits at ≈18 mm.
- **Corner joints** (compacted footprint): signal pads span y ≈ 0–16 at the board ends, so they fit within the same height.

**Board height: H = 22 mm** (V5.5, from placement; H = 24 mm if decision 0005 is rejected). The earlier per-shape estimates above (≈18–20 mm) predate the buck and level shifter. The optics test (gap A1, 15/25/35 mm depths) may still call for a taller panel. A taller board only adds space; nothing above has to move.

### 2.2 Assumptions to confirm
- The back reflector plate is no thicker than ≈3 mm at the wall, so LEDs from y ≈ 10.5 mm sit in the light cavity.
- The bridge carrier and snap fit stay within y < 9 mm on the exterior side and don't reach above the contact strip.
- 1 oz copper, 2-layer, 5 A feed-through (if the fuse is smaller, the lanes can shrink).
- 3 LEDs per edge, evenly spaced. One LED can sit at x = 0, above the contact strip.

## 3. Placement guide (no routing)
- **J1 (contacts):** origin at (x = 0, y = 0), the polygon-edge midpoint on the wall edge, on the bottom side (pads are B.Cu).
- **J2 (`CornerJoint_L`)** at the left end and **J3 (`CornerJoint_R`)** at the right end, with the footprint's x = 0 line on the board end and pad 6 nearest the wall (pads 6→1 run up from y ≈ 1).
- **LED1–3:** centred on y ≈ 15.5 (V5.3 stack), at x ≈ −L/3, 0, +L/3. C1–C3 sit at each LED's VDD/GND pins. Buck (U5, L1, C16–C21, R16–R18) stays in one tight group away from Y1, the SENSE ADC filter and CAN.
- **Active section:** in the zones from §2.1. Keep Y1/C5/C6 within 5 mm of U1, C7/C8/C11 at their pins, D4 in the CAN path ahead of U2, U3 with a VIN_LDO pour, and R14 away from the LEDs. Test pads go on a ≥2.54 mm grid.
- **Discovery parts** (D1, R1, R2) near J1 X7.
