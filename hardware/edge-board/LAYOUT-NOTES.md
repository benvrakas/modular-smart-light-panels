# Passive edge board V6: layout notes (all shapes, rev A)

**Date:** 2026-11-21 · **Against:** SPEC V6.3, decisions 0002, 0004, 0009, 0010, 0011 · **Roadmap:** WP 1.3
**Boards:** `edge-board-hex.kicad_pcb`, `edge-board-square.kicad_pcb` and `edge-board-triangle.kicad_pcb`, built by `scripts/build_edge_pcb.py OUT hex|square|triangle` from the generated schematic's netlist. **One layout for all three (user, 2026-11-21: keep the boards as alike as possible; decisions 0015, 0016):** the core is placed from the board centre, the end zone from the outer LED, and only the outer LEDs (and the end zone with them) move with the shape. The earlier hand-reviewed hexagon layout is archived in `hardware/archive/edge-board-hex-reviewed-2026-11-21/`. The triangle is the rev A test board. Every track is placed by the script; nothing was autorouted. Re-run the script after a schematic change (see §8).

## 1. Result

| Item | Value |
|---|---|
| Outline | **94.1 / 89.8 / 82.33 × 13.5 mm** (hexagon / square / triangle), 1.6 mm, 2-layer, 1 oz, ENIG, square-cut ends (decision 0004 at d = 3.5) |
| **Achieved height H** | **13.5 mm** (target 10–15, aim ≈13). The 0.5 mm over 13 is the bus band; see §3. |
| DRC (`output/drc-hex.json`; square and triangle in `drc-square.json`, `drc-triangle.json`, all severities, with schematic parity) | **0 violations, 0 unconnected, 0 parity issues** |
| +36V adjacency check (`scripts/check_adjacency.py`) | No 5 V-side net within 1.0 mm of +36V copper, except the J4.3 +5V_LED track 0.8 mm below the J4.1 pad, which has a GND guard track between them (§4) |
| Fab (`output/fab-hex/`, `fab-square/`, `fab-triangle/`) | Gerbers + drill (zip), `CPL_edge-board-<shape>_code0.csv` (R2, R3 left out), `CPL_edge-board-<shape>_code1-7.csv` (R2 left out), `BOM_edge_code0..7.csv` (copied from `bom/`), top/bottom renders |
| Copper plots | not kept; regenerate with `kicad-cli pcb export svg` if needed |

Coordinates: **x** along the board from its centre, seen from the inward face (F.Cu), **z** up from the wall edge. KiCad: x = X − 100, z = 100 − Y. Fab origin = the bottom-left corner.

## 2. Interface contract (for the controller board, bridge, frame and corner hardware)

| Item | Position | Notes |
|---|---|---|
| **J4 controller joint** (F.Cu) | footprint origin (0, 5.25); pads 1–10 at x = −11.43 + 2.54·(n − 1), 1.3 × 2.85 mm, **z 2.5–5.35** | Controller underside z 5.0, top z 6.6. **Changed (V6.9.2, roadmap 2.0):** the pads run z 2.5–5.35 (were 3.5–5.7; before that 3.5–7.0). 2.5 mm of fillet land below the controller underside and 0.35 mm behind its edge, so solder wicks into the gap. The gap above lets the CANH track pass between the J4 tops and LED2. The controller's J1 is unaffected. |
| **LEDs** (F.Cu, SKC6812RGBW) | x = 0 and ±LO: **LO = 31.2 hexagon, 29.9 square, 27.4 triangle** (about L/3, evenly spaced); **centre z 9.8**, rotated 180° | Body z 7.37–12.23; pad rows z 8.2 (DIN left, VDD right) and 11.4 (GND left, DOUT right). Data flows +x. |
| **Edge contacts X1–X10** (B.Cu) | x = −22.5 + 5·(n − 1); 3.0 mm wide; from z 0.3 (GND) / 0.6 (+36V) / 0.9 (signals) **to z 6.0** | No-via/no-pour rule area up to **z 5.3**. Mask open over the whole strip up to z 6.1. **Each pad has its vias in its top end, z 5.4–6.0** (decision 0007 method). The spring contact point must stay **≤ 5.0** including tolerances; nominal 3.5. |
| **Corner joints** J2 (x −L/2) / J3 (x +L/2) | origin at the board end on the wall edge; all pads touch the end | **F.Cu signal pads** 2.0 (x) × 1.3 (z) mm at 2.5 mm pitch: **D 1.5, CANH 4.0, CANL 6.5, DRIVE 9.0, SENSE 11.5**. **B.Cu power pads** 3.0 mm wide: **+36V z 0.5–3.5, GND 6.0–8.5, +5V_LED 11.0–12.6** (GND between the supplies, 2.5 mm gaps). Pad numbers are unchanged (1 D, 2 CANH, 3 CANL, 4 SENSE, 5 DRIVE, 6 +36V, 7 +5V_LED, 8 GND). |
| Test pads | TP1 SPARE (14.6, 1.6) F; TP11 +5V_LED (−LO + 0.6, 3.6) F; TP10 +36V (−(LO + 1.8), 9.6) **B**; TP3 GND (LO + 1.8, 11.4) **B** | All flat pads. They can't be reached after assembly; the boards are tested before (MECH-NOTES, accepted). |
| ID circuit | R1 (14.6, 10.7), D1 (15.6, 8.3), R2 DNP (13.8, 8.3) | In the LED2–LED3 gap (SPEC V6.2.2 request). |
| Decoupling, data link | C1 (−15.4, 9.6), C2 (5.4, 9.6), C3 (19.8, 9.6), C4 10 µF (−20.4, 8.6); R3 **0402** (−LO − 3.45, **7.2**) just under LED1's DIN pad, fitted on codes 1..n−1 only | C1/C3 sit in the gaps between the contact hop columns (≥1.4 mm from +36V). R3 (V6.9.2): pad 2 under the DIN pad (same net), pad 1 0.24 mm clear of it, fed by the D_IN via straight below at (−(LO + 3.96), 1.9). It sits inside the LED's courtyard (to z 6.9) but 0.45 mm from its body; the `.kicad_dru` allows that overlap and R3's clipped silk. Nowhere else above z 6.8 can both D_IN and LED1_DI reach without crossing the +5V_LED low band. |
| Thickness | 1.6 mm | |

**Keep-outs honoured** (controller LAYOUT-NOTES, MECH-NOTES §1/§4):
- **Inward-face part zone: no 3D part below z 6.8** (V6.9.2; only flat copper there).
  - The back-plate rim wall stands 0.15 mm inside the boards up to z 6.6.
  - The controller fills z 5.0–6.6 over |x| ≤ 36 on side 0.
  - The board ring is soldered first and lowered into the back plate along z, so a part below the wall top could not get past it (user, 2026-11-21). The V6.9 groove for R3 is gone.
- **Iron access**, within 3 mm of either end of the J4 row (|x| 12.1–15.1): only R1, R2 (0603, 0.5 mm) and D1 (SOD-323, ≈1.0 mm) are there, all ≤ 1.1 mm tall.
- **Exterior face z 0–7.5 at |x| 30–36.5** (frame snap legs): only flat copper. That is bus lanes, the D_IN B.Cu segment and its vias at (−(LO + 0.2), 1.9) and (−(LO + 3.96), 1.9), all tented and under mask. TP10/TP3 are at z ≥ 8.85.
- **Inward face z ≥ 12.8** (frame lip): no parts. The LED tops are at 12.23; only the +5V_LED via pads (tented) reach z 13.1.
- **Nothing below the wall edge**: the edge is straight.

## 3. Layer plan and why

| Layer | z | Content | Reason |
|---|---|---|---|
| B.Cu | 0–6.0 | contact strip (vias in the pad tops at 5.4–6.0) | SPEC 3.3. The pad-top vias let every pad reach copper without a via row above the strip (no extra height). |
| B.Cu | 6.45 / 7.1 / 7.75 / 8.4 | **bus lanes** b1–b4 (0.25 mm) | Left half: b1 CANH, b2 CANL. Right half: b1 CANL, b2 CANH. Both halves: b3 DRIVE, b4 SENSE. The pitch is **0.65 mm so a via fits on any lane** (the taps to J4, X4/X5 and the corners need it). X4 and X5 neck straight into b1 (the lowest lane at their x). |
| B.Cu | 8.9–10.3 | **+36V lane 1.4 mm** | Feed-through current. Next to GND above and bus nets below (36 V-tolerant), never next to +5V_LED. |
| B.Cu | 10.7–12.1 | **GND lane 1.4 mm** | Between +36V and +5V_LED. |
| B.Cu | 12.5–13.1 | **+5V_LED lane 0.6 mm** | ≤0.75 A ring current. |
| F.Cu | 0.3–2.3 | "low band" (V6.9.2): left LED1_DI 0.5, D_IN 0.95, J4.3 +5V_LED (to LED1's VDD) 1.5, GND guard 2.05; right SPARE 1.6, DRIVE (X6 → J4.10) 2.1. Right of TP1 the C3 +5V_LED run stays at 2.6 | The only free full-length channel under J4. Compressed so the J4 pads reach down to z 2.5. |
| F.Cu | 2.5–5.35 | J4 | |
| F.Cu | 5.9–7.2 | channel under LED2: the CANH jumper (b1 → J4.7) | Why the J4 pad top was lowered. |
| F.Cu | 7.4–12.2 | LEDs, caps, ID circuit, LED data at z 12.15 over the top | |

**Why not 13 mm:** the centre is the hard part. J4's 10 pads sit right over X4–X8, LED2 sits right over J4, and the J4 pin order (fixed by the controller) interleaves the bus taps (X4 CANH, X5 CANL, X6 DRIVE, then J4.7–J4.10) with the LED-data pads J4.4/J4.5. A two-layer planar routing exists only with four separate B.Cu bus lanes. At the 0.65 mm pitch that lets a via land on any lane, those take 2.6 mm; with 1.4/1.4/0.6 mm power lanes and the gaps, the top of the stack lands at 13.1 → H = 13.5. Earlier attempts at 13.0 (power lanes directly above the strip, bus on F.Cu) were not planar (Freerouting left 9–35 connections open).

**Crossings solved by vias** (each one is needed; listed for review):
- **CANH:** b1 (left) taps X4. It jumps to F.Cu at (−5.08, 6.45), runs over the J4 tops under LED2 to J4.7, and goes back to B.Cu b2 at (4.4, 7.1). That frees b1 for CANL to tap X5.
- **CANL** drops b2 → b1 at x ≈ −4 (on B.Cu), taps X5, and reaches J4.8 by a via at (5.08, 6.45).
- **DRIVE:** X6 by its pad via down the J4 gap (x 2.54) and through the low band into J4.10 from below. J4.10 reaches lane b3 by a via at (12.6, 7.75).
- **SENSE:** J4.9 via at (8.89, 8.4); D1 anode via at (16.5, 8.4).
- **D_IN** runs the low band at z 0.95, rises just past LED1's +5V riser and dives to B.Cu from x −(LO + 0.2) to −(LO + 3.96) (z 1.9) to cross under LED1_DI, which has to reach LED1 DIN from below; it comes back up under R3's pad 1.
- **Corner order** D / CANH / CANL / DRIVE / SENSE (from the wall up) is chosen so the lane vias at the ends (|x| LO + 4.4 … LO + 6.8) fan out to the pads without crossing, and the LED data (D) enters at the bottom.

## 4. Electrical rules applied (each with its reason)

| Rule | Reason | How it is met |
|---|---|---|
| +36V copper only next to GND or 36 V-tolerant nets (SPEC 2, decision 0011) | A short to +5V_LED, LED data or LED return destroys LEDs or logic | +36V lane between the bus (CAN/SENSE/DRIVE) and GND. Its corner leg is next to GND. The J4.1 riser is between GND risers. The +5V_LED low-band track passes 0.8 mm under the J4.1 pad with a **GND guard** (0.3 mm, from J4.2 to the X3 GND hop) between them. DRC rule `+36V vs 5 V nets` (0.5 mm) in `edge-board-passive.kicad_dru`. ID_K counts as tolerant: D1 (75 V) blocks it from SENSE, and R1 leads only to the SENSE_EDGE contact. |
| No pour and no vias where the springs touch (SPEC 3.3) | Springs must touch only pads or bare board | Rule area z ≤ 5.3; the pad-top vias start at 5.4; spring contact ≤ 5.0. |
| Feed-through current 2–4 A on +36V/GND | Panels in a feed path | 1.4 mm lanes: ≈33 mΩ per board, 0.13 V and 0.5 W at 4 A, ≈15 °C rise (IPC-2221, 1 oz external); ≈3.5 A at 10 °C. Corner legs 1.2 mm over ≈7 mm and 2.0 mm into the pads. |
| Contact-pad hops (the bus band lies between the strip and the power lanes) | Spring current ≈1 A per pad | GND X1: 3 vias at each end, 1.4 mm riser. X10 and X3: 2 vias, 1.0 mm riser (X10 has 2 on every shape: the triangle's LED_D2 riser needs the room). +36V X2/X9: 2 vias at each end, 1.0 mm riser. |
| +5V_LED | ≤0.75 A ring, ≤0.36 A per board normally | 0.6 mm lane ≈77 mΩ per board (≈28 mV at 0.36 A). Each LED's VDD rises under its own body to a lane via; its GND has a via under the body. 100 nF per LED: C2 beside LED2; C1 and C3 in the hop gaps (8–15 mm from their LEDs), C1 tied into the J4.3 low band and C3 into LED3's riser along the right low band. C4 10 µF hangs on the J4.3 feed. |
| LED data never on B.Cu near +36V | Same as row 1 | The LED data, +5V_LED and ID_K nets are F.Cu-only, except D_IN's B.Cu dive at |x| LO + 0.2 … LO + 3.96, z 1.9, which is far from all +36V copper. The C3 +5V_LED track runs along the right low band at z 2.6, 1.6 mm from the +17.5 +36V hop. |
| Copper to the wall edge | Mating order (GND 0.3 / +36V 0.6 / signals 0.9) | Board rule 0.3 mm; J1 pads 0.25 (`contact pads at wall edge`). Corner pads at 0 (`corner pads at board end`). |
| DRIVE next to +36V | Preference only (decision 0011) | DRIVE lane b3 is two lanes from +36V. |

## 5. Footprint changes (`hardware/lib/footprints/ModularLight.pretty/`, generated by `scripts/gen_footprints_v6.py`, V5 copies in `../archive/footprints-v5/`)

- `EdgeContacts_SpringPads`: strip to z 6.0 (was 8.0); rule area to 5.3; mask to 6.1; `allow_soldermask_bridges`; +36V labels.
- `ControllerJoint_EdgeBoard`: pads 1.3 × 2.85, z 2.5–5.35 (V6.9.2; were 1.3 × 2.2 at z 3.5–5.7, originally z 3.5–7.0). Origin, pitch and numbering unchanged.
- `Spring_BW0019CG`: the generator now writes its 3D model line too, so a full regeneration keeps it.
- `CornerJoint_L/_R`: re-laid out for 13.5 mm (§2), origin moved to the wall-edge corner, same pad numbers.
- New: `Spring_BW0019CG` (bridge), `ContactPad_3x6` and `NPTH_0.5mm` (coupon).
- `exclude_from_bom` removed from the copper-only footprints so the board matches the schematic (schematic parity). The BOM scripts skip parts without an LCSC number anyway.
- The V5 board (`hardware/archive/edge-board-v5/`) keeps its own embedded copies and is unaffected.

## 6. Things to check or decide

1. **JLC rotations:** check the LED (180°) and SOD-323 in JLC's CPL preview.
2. **Back-plate corner relief:** the inward-face corner pads D/CANH/CANL sit below z 6.6 at the board ends, and the corner solder beads there need a small relief in the back-plate corners (mechanical).
3. **Wall-edge bevel:** the GND pads start 0.3 mm from the edge, so a bevel trims their lower end. That is fine for lead-in, but order "bevel" on the exterior side only.
4. **Seam inset d:** with d = 3.5 (seam 7.0) the springs sit at 3.1 mm, close to their 3.0 mm minimum. d ≈ 3.8 (spring at 3.4 mm) would centre them; that changes L_board to ≈93.8 mm (decision 0004 formula). See BRIDGE-NOTES §5.
5. **LED 3D model:** done. The footprint uses KiCad's SK6812 PLCC4 5050 model, so the STEPs and renders show the LEDs.

## 7. Scripts (`scripts/`)

| Script | Does |
|---|---|
| `gen_footprints_v6.py` | writes the V6 library footprints |
| `build_edge_pcb.py` | netlist → complete routed board |
| `pcbutil.py` | shared pcbnew helpers (wx asserts disabled first) |
| `make_project.py` | writes the design rules into a `.kicad_pro` |
| `drcsum.py` | kicad-cli DRC (+ parity) summary in board mm |
| `check_adjacency.py` | lists nets within N mm of +36V copper |
| `fab.py` | Gerbers, drill, JLC CPL per variant, renders |
| `autoroute.py`, `route_edge.json` | Freerouting wrapper (used only for the failed 13 mm trials; kept) |

## 8. Schematic changes needed (generator `controller-board/scripts/gen_v6_schematics.py`, not edited here)

- None are required for this layout.
- Optional: mark J1–J4 and TP1/3/10/11 `in_bom no`, then restore `exclude_from_bom` in the footprints.
