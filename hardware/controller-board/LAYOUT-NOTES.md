# Controller board: layout notes (rev A)

**Date:** 2026-11-20 · **Against:** SPEC V6.2.2, decisions 0009, 0010, 0011, SCHEMATIC-NOTES (§6 joint, §12 buck) · **Roadmap:** WP 1.4

**Result:** `controller-board.kicad_pcb` is fully placed and routed.
- **DRC:** 0 errors, 0 warnings, 0 unconnected items, 0 schematic-parity issues (`kicad-cli pcb drc --severity-all --schematic-parity`, in `output/fab/drc.json`).
- **Schematic:** unchanged (ERC 0, F1 included). The board is built from its netlist `output/controller-board.net`.

## 1. Outline and fit

| Item | Value |
|---|---|
| Shape | Trapezoid, 60° sides. **Base 72.0 mm** (the J1 edge, against the code-0 board's inward face), **depth 24.0 mm**, top edge 44.29 mm. Corners filleted R 1.0 mm. |
| Area | ≈1,394 mm² |
| Thickness | 1.6 mm |
| Stack-up | **4 layers**, JLC04161H-7628: F.Cu (parts, wall side) / In1 solid GND / In2 signals + GND pour / B.Cu solid GND (chamber face). 1 oz outer, 0.5 oz inner. |
| Fit in the triangle (inner side 82.3 mm at d = 3.5) | Each 60° side runs parallel to the neighbouring edge board's inward face, **4.46 mm** from it. The base corners sit 5.15 mm from the inner triangle corners, measured along the code-0 face (plus the fillet). At d = 3.9 mm (the top of the §3.3 seam range) the side gap is still 3.86 mm. The triangle's inner height is 71.3 mm, against the 24 mm depth. Squares and hexagons have more room. |

**Board frame used in this file:** origin at the centre of the base edge; x to the right and y into the board, both as seen from F.Cu (from the wall). KiCad coordinates are `x_kicad = 100 + x`, `y_kicad = 100 − y`.

## 2. J1 joint (interface to the code-0 edge board's J4)

- **Footprint:** `ModularLight:ControllerJoint_ControllerEdge`, centred on the base edge at x = 0.
- **Pads:** on F.Cu, 1.3 × 2.0 mm, from y = 0 (the board edge) to y = 2.0.
- **Pitch and order:** 2.54 mm; pad n meets J4 pad n.

| Pad | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Net | +24V_IN | GND | +5V_LED | LED_RETURN | LED_DATA_OUT | SPARE | CANH | CANL | SENSE | DRIVE |
| x (mm) | −11.43 | −8.89 | −6.35 | −3.81 | −1.27 | +1.27 | +3.81 | +6.35 | +8.89 | +11.43 |

**Pad 1 mapping (SCHEMATIC-NOTES §6.3):**
- Viewed from the wall side with the base down, pad 1 is leftmost. J1 is on the same copper side as the parts (F.Cu), so pad n meets pad n.
- The edge-board layout (`edge-board/scripts/build_edge_pcb.py`) places J4 centred at x = 0 with its origin at z = 5.25. That matches: the controller's underside (the F.Cu face) is J4's y = +0.25 line, z = 5.0, and its top is at z = 6.6.

**Edge rule:** J1's pads touch the trapezoid base, so the `.kicad_dru` exempts them from copper-to-edge clearance. All other copper keeps ≥ 0.3 mm (≥ 0.4 mm for routed tracks). JLC mills through the pad ends there; that is fine for a drag-soldered joint.

**Drag-solder access:**
- No part sits within the J1 courtyard (|x| ≤ 12.6, y ≤ 2.9).
- Nearest parts:
  - 0603 resistors R7, R5, R26 (0.55 mm tall) from y = 3.2.
  - SOT-23 TVS D4, D6 (1.1 mm) from y = 3.0.
  - Q1 from y = 3.65.
- The closest tall part is F1 (1812, 1.8 mm), 3.9 mm beyond pad 1's outer edge.
- R11 (1206, 0.55 mm) starts 0.6 mm beyond pad 10.
- So the iron can reach along the inner corner from either end.

**Keep-out on the code-0 edge board (for the edge-board layout):**
- Across x = −36 … +36 on the inward face, the controller fills z = 5.0–6.6 from the face inward.
- Its own parts hang toward the wall down to z ≈ 0.5, starting 1.6 mm from the face (D5, F1 and TP13 are nearest the base).
- So the edge board may carry nothing on its inward face below z ≈ 6.8 inside that span, apart from J4 and flat copper under mask.
- Anything protruding above z 6.6 over the controller needs clearance: the centre LED's bottom edge at z ≈ 6.9 leaves only ≈0.3 mm (see §8).

## 3. Part heights per side

| Side | Contents | Tallest |
|---|---|---|
| **F.Cu (wall side, in the back-plate pocket)** | All 56 assembled parts, 13 test pads, J1, JP1 | **L1 FNR6045S220MT: 4.5 mm max** (datasheet `docs/datasheets/FNR6045S220MT.pdf`: 6.0 ± 0.3 × 6.0 ± 0.3 × 4.5 max). Next: D5/D7 SMA ≤ 2.5 mm; F1 ≤ 1.8 mm (datasheet); C16/C23 1206 ≤ 1.8 mm; U2/U5 SO-8 ≤ 1.75 mm; U3 SOT-89 ≤ 1.6 mm; 0805 caps ≤ 1.45 mm; U1 TSSOP ≤ 1.2 mm; SOT-23 ≤ 1.1 mm; crystal ≤ 1.0 mm. |
| **B.Cu (chamber face)** | No parts, no silkscreen, no mask openings, no paste: the B.SilkS/B.Mask/B.Paste gerbers are empty. Solid GND copper under white mask. Through-vias are tented: about 85 small dimples. One short signal track: CAN_RX, ≈4.3 mm under U2/C10 (§6). | 0 mm |

Where L1 sits: centre (x −18.0, y 19.6); body ≤ 6.3 × 6.3 mm, so x −21.2 … −14.8, y 16.4 … 22.8.

## 4. Back-plate pocket (for the mechanical package 1.6)

With SPEC §10 item 17 heights (controller underside at z = 5.0, top/chamber floor at z = 6.6):

| Zone | Needed below the board underside | z of pocket floor |
|---|---|---|
| Under L1: window ≥ 7.5 × 7.5 mm centred on (−18.0, 19.6) | ≥ 4.8 mm (4.5 max + 0.3) | ≤ 0.2 → **open through to the wall**: the wall is the floor, with ≥ 0.5 mm air under L1 at nominal |
| Everywhere else | ≥ 2.8 mm (SMA 2.5 max + 0.3) | ≤ 2.2 → a printed floor of up to 2.2 mm is possible |

**Ledges and snap hooks:** part-free bands ≥ 1.5 mm deep along the edges, lengths measured from each edge's first corner (`scripts/layout/layout_edgebands.py`):

| Edge | Part-free stretches (mm along the edge) |
|---|---|
| Base | 1.8–23.3 and 48.8–69.8 (both sides of J1) |
| Right 60° side, from the base corner | 1.8–5.3, 13.8–25.8 |
| Top, from the right corner | 1.8–11.8, 31.8–36.3 |
| Left 60° side, from the top corner | 1.8–6.8, 8.8–25.8 |

The solder joint carries no load (decision 0009). The back plate's snap fit must hold the board.

## 5. Test pads (pogo jig from the wall side)

D1.5 mm pads on F.Cu. The signal pads sit on a 2.8 mm grid in the right wedge, clear of tall parts.

| Pad | Net | x | y | | Pad | Net | x | y |
|---|---|---|---|---|---|---|---|---|
| TP1 | SPARE | 25.0 | 4.0 | | TP8 | UART_RX | 27.8 | 9.6 |
| TP2 | +3V3 | 27.8 | 4.0 | | TP9 | PB1 (GPIO_SPARE) | 25.0 | 12.4 |
| TP3 | GND | 30.6 | 4.0 | | TP10 | +24V_IN (before F1) | −14.6 | 4.4 |
| TP4 | SWDIO | 25.0 | 6.8 | | TP11 | +5V | −8.6 | 21.8 |
| TP5 | SWCLK | 27.8 | 6.8 | | TP12 | +5V_LED | −11.0 | 6.4 |
| TP6 | NRST | 30.6 | 6.8 | | TP13 | +24V (after F1) | −30.6 | 3.6 |
| TP7 | UART_TX | 25.0 | 9.6 | | | | | |

- The WCH-LinkE set (SWDIO, SWCLK, NRST, 3V3, GND) is TP2–TP6, within a 2.8 × 5.6 mm area.
- J1.2 also gives the jig a GND contact at the joint.
- The jig plate needs relief for L1 (4.5 mm) and the SMA diodes when it presses from the wall side.

## 6. Placement and routing

**Floor plan, left to right:**
- **24 V input and buck** at the left (pad 1 is +24V).
- **LED-rail switch and level shifter** above J1.3–J1.5.
- **TVS diodes D4 / D6** at J1.7–J1.10.
- **MCU, crystal and CAN transceiver** in the centre-right.
- **Test pads** in the right wedge.

**+24V adjacency (SPEC §2, decision 0011):**
- **What stays apart:** +24V and +24V_IN copper keeps **≥ 1.0 mm from every net that is not GND or 24 V-tolerant**. This is a custom DRC rule, and the GND pour fills the gaps.
- **Tolerant nets:** CANH/L, SPARE, SENSE, DRIVE, plus BUCK_SW and BUCK_BOOT, which swing to 24–29 V themselves.
- **Exemption:** U5's open EN pin, which sits beside VIN inside the IC pinout.
- **Independent check:** `layout_verify.py` lists the nearest copper of every net. Within 1 mm there is only GND, BOOT and EN. The nearest intolerant copper is +5V_LED at 1.63 mm, with the GND pour between, then RT at 1.85 mm. **PASS.**
- **Layers:** +24V copper is on F.Cu only, over the In1 GND plane.
- **Tracks:** +24V_IN runs from J1.1 to F1 at 0.6 mm wide (its only neighbour is J1.2 = GND); the +24V bus is 0.8 mm. No solder reinforcement.

**Buck (SCHEMATIC-NOTES §12):**

| Rule | Implementation |
|---|---|
| Tight input loop | U5 VIN faces down, straight onto F1.2 / the +24V bus. C17 (100 nF) is 3.2 mm from VIN with a GND via at its pad. C16 / C23 (2 × 10 µF) are on the same bus. D7's anode is ≈3 mm from the C_IN grounds. The hot loop C_IN → VIN → SW → D7 → GND is ≈6 × 8 mm, with In1 GND 0.2 mm below it. |
| Small SW node | U5.8 → D7 cathode → L1.1 is one 1.0 mm spine, plus C18 (BOOT). All of it lies inside x −24.3 … −18.8, y 12.7 … 17.6. Freerouting kept 0.5 mm extra clearance from it. |
| FB away from SW | FB / COMP / RT parts are on the right of U5, the side away from SW. FB is 3.0 mm from SW copper (the IC's own pin spacing). |
| SW ≥ 10 mm from Y1 / C14 / SENSE_ADC | Measured: OSC_IN 28.8 mm, OSC_OUT 28.1 mm, SENSE_ADC 20.2 mm. A DRC rule enforces ≥ 10 mm. |
| Solid GND | In1 is solid GND. U5's thermal pad has 8 vias plus a B.Cu spreader pad, which is unmasked copper only and stays covered by mask. Ground pads of the power parts connect solid; small passives and J1.2 (hand-soldered) use thermal reliefs. |

**Routing:**
- **Scripted:** the +24V, SW and BOOT tracks, and the loop GND vias (locked).
- **Freerouting:** everything else, from a pinned session. B.Cu is typed "power", so it carries no wires.
- **Grid A* router:** the last open connections (6 signals + 4 short +3V3 links), on F.Cu + In2.
- **GND stitching:** 29 vias on a 2.5 mm grid where all 4 layers are GND, plus vias in any isolated F.Cu GND island.

**Known compromises (none affect function):**
- **CAN_RX on B.Cu:** one ≈4.3 mm link between two vias under U2/C10. No F.Cu or In2 path exists there. Under white mask it shows as a faint line at most, and the B.Cu GND plane flows around it.
- **0.10 mm necks:** two necks on LED_RET at R8, 0.25 mm long in total. The board minimum is set to 0.10 mm; JLC's 4-layer minimum is 0.09 mm. Everything else is ≥ 0.15 mm, mostly 0.2 mm; power runs 0.5–0.8 mm.
- **In2 GND pour:** broken into pieces by signal tracks. In1 is the solid reference plane.

## 7. Fab outputs (`output/fab/`)

| File | What |
|---|---|
| `controller-board_gerbers.zip` (+ `gerbers/`) | F/In1/In2/B copper, mask, paste, silk, edge, Excellon PTH/NPTH, drill map, gerber job |
| `BOM_controller-board_JLC.csv` | Copy of `bom/BOM_controller-board.csv` (Comment, Designator, Footprint, LCSC). R26 DNP; J1/JP1/TPs are copper only. |
| `CPL_controller-board_JLC.csv` | Designator, Mid X, Mid Y, Layer (all Top), Rotation for the 56 BOM parts. The script checks that it matches the BOM exactly. |
| `controller-board_assembly.pdf` | F.Fab references + courtyards + outline (assembly and jig reference; references are not on the silkscreen) |
| `drc.json` | Final DRC with schematic parity: empty |

**JLC order settings:**
- **Board:** 4 layers, 1.6 mm, stack-up JLC04161H-7628, 1 oz outer / 0.5 oz inner, **white solder mask** (JLC applies it to both sides; silkscreen is then black), HASL lead-free or ENIG.
- **Vias:** 0.3 mm drill / 0.6 mm pad, tented.
- **Assembly:** top side only.
- **Check rotations in JLC's placement preview** for the polarised and multi-pin parts (U1–U6, Q1–Q3, D2/D4–D7, Y1). The CPL uses KiCad's footprint orientation, and JLC's library zero sometimes differs.

## 8. Proposed SPEC changes (for the coordinator)

1. **§3.5 Controller board, shape:** fix the outline:
   - trapezoid with 60° sides, **base 72.0 mm × depth 24.0 mm** (top 44.3 mm, R 1 mm corners, ≈1,394 mm²)
   - 4.46 mm from the triangle's other two boards
   - stack-up F.Cu parts / In1 GND / In2 signals / B.Cu GND
2. **§3.5 Orientation and §9:** replace "≥ 5 mm pocket" with a **stepped pocket**:
   - **≥ 2.8 mm** below the board underside everywhere
   - **an open window to the wall** (≥ 7.5 × 7.5 mm, centred on L1 at x −18.0, y 19.6 in this file's frame), since L1 needs ≥ 4.8 mm below the z = 5.0 underside
   - Alternative: raise the underside to z ≥ 5.4 to keep a printable floor under L1.
3. **§3.5 Chamber face:** add that the B side has no parts, silkscreen or mask openings, and exactly one 4 mm signal track. It does have ≈85 tented via dimples.
4. **§10 item 17:** confirm the controller-side numbers:
   - underside z = 5.0, top z = 6.6
   - J4 origin z = 5.25 (pad band z 3.5–7.0), centred at x = 0
   - J1 pads 1–10 at x = −11.43 … +11.43
5. **§3.5 Interface contract:** add the **code-0 inward-face keep-out**: nothing but J4 and flat copper below z ≈ 6.8 over x = ±36 mm. Also flag the centre LED: at z 9.4 its 5050 body bottom (≈ z 6.9) clears the controller top by only ≈0.3 mm.
   - **Proposal:** LED centre ≥ z 9.8 (bottom ≥ 7.3), or an agreed tolerance stack with the back plate.
6. **§3.2 Debug row:**
   - Record the test-pad layout: TP1–TP9 on a 2.8 mm grid in the right wedge, the SWD set in TP2–TP6.
   - The jig contacts from the wall side and needs relief for L1.
7. **§2 rule wording:** BUCK_SW and BUCK_BOOT count as 24 V-tolerant. Implemented as a ≥ 1.0 mm DRC clearance between +24V and every other net, with the GND pour between.
8. **§3.2 Joint row:** record a drag-solder access rule: no controller part within the J1 courtyard (y < 2.9 mm over |x| < 12.6 mm), and no part taller than 1.1 mm within 3 mm of either end.

No decision record is needed for items 1–8: they record layout results inside the existing decisions 0009–0011. Item 2 changes a SPEC number.

## 9. Rebuilding (scripts in `scripts/layout/`)

`python layout_all.py` rebuilds the board from the netlist and remakes all outputs, in about 3 minutes. Steps:
1. `layout_rules.py`: net classes and custom DRC rules.
2. `layout_build.py`: outline, footprints, placement table, planes.
3. `layout_preroute.py`: +24V, SW and loop tracks.
4. `layout_route.py`: imports the pinned Freerouting session `route_pinned.ses`; use `--rerun-route` to route again.
5. `layout_finish.py`: pours, stitching, silkscreen.
6. `layout_fixups.py`: open connections, found by kicad-cli DRC and routed with the grid A* router; GND islands.
7. `layout_check.py`: DRC + parity + renders → `output/layout/final_*`.
8. `layout_fab.py`: fab outputs.

Helpers:
- `layout_verify.py`: the +24V / SW / interface report → `output/layout/verify.txt`.
- `layout_edgebands.py`: the part-free edge bands.
- `pads.py`, `nets.py`, `plotmap.py`: debug dumps.

All KiCad-Python scripts import `kicad_quiet` (which calls `wx.DisableAsserts()`) before `pcbnew`.

If the schematic changes:
1. Regenerate it with `scripts/gen_v6_schematics.py` and run `scripts/verify_v6.py`, which re-exports the netlist.
2. Adjust `PLACE` in `layout_build.py` and run `layout_all.py --rerun-route`.
3. Check the result, then copy `output/layout/route/route.ses` over `route_pinned.ses`.
