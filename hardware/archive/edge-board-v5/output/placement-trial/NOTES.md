# Edge board: placement (rev A, hexagon), height finding

**Date:** 2026-11-15 · **Against:** SPEC V5.4, decisions 0001–0004, `edge-board.kicad_sch` (04:30, RGBW), LAYOUT-NOTES (12:50), GEOMETRY (V5.3 stack) · **By:** PCB layout session

## Status of `edge-board.kicad_pcb`
- **Synced to the RGBW schematic.**
  - Scripted equivalent of F8 with "replace footprints" and "delete extra footprints", plus "update from library" on J1–J3 and LED1–3.
  - R4/R6 removed. U4, U5, L1, C15–C21, R16–R18 and TP11 added. LED footprints are now SKC6812RGBW 5050-4.
  - kicad-cli DRC `--schematic-parity`: **0 issues**.
- **All 67 parts placed, plus 2 board-only NPTH tooling holes (H1/H2). Outline 93.7 × 22.0 mm (hexagon), no tracks or zones.**
  - DRC: **0 courtyard overlaps.** The rest are expected (see below).
  - Grid/drill origin = (0, 0) = centre of the wall edge.
  - Only reference designators are on silk; BOM fields are hidden.
- Backups in `../../edge-board-backups/`: `*.pre-rgbw-sync-*.bak` and `*.pre-placement-v54-*.bak`.
- **Triangle check:** `edge-board_triangle-check.kicad_pcb` uses the same core on an 81.9 mm outline. It also has 0 courtyard overlaps, and every core part is within |x| ≤ 37.0 mm (the triangle's corner-joint courtyards start at ±37.45).
- Renders: `placement_hex_22_top.png`, `placement_hex_22_bottom.png`, `placement_tri_22_top.png`.

### Expected DRC items (not placement errors)
- copper_edge_clearance (19): corner pads touch the board ends by design; GND contact pads sit 0.3 mm from the wall edge. Needs a local rule and a fab check (LAYOUT-NOTES §2, §8).
- solder_mask_bridge (7): J1's full-strip mask opening is intentional (gold-finger style). It could be waived in the footprint.
- silk (57): reference text overlap and silk-to-edge. Cosmetic; tidy after routing.
- 146 unconnected items: nothing is routed yet.


## Routing status: ACTIVE board, 4-layer (decisions 0006, 0007), 2026-11-16

**Pipeline** (all scripts in this folder; KiCad 9 bundled Python; every script imports `kicad_quiet` first, so there are no wx pop-ups). Copy the project's `.kicad_pro`/`.kicad_dru` next to any scratch board **before** running a script on it, because zone fills use the custom rules (DRIVE/SENSE vs +12V 0.5 mm).

| Step | Command | What it does |
|---|---|---|
| 1 | `setup_rules.py edge-board.kicad_pro` | Net classes and the custom DRC rules file `edge-board.kicad_dru` |
| 2 | `sync.py` | Netlist to PCB. Leaves board-only H1/H2 alone. |
| 3 | `place.py in out 93.7 22` | Placement, outline, tab keep-outs, checks |
| 4 | `stackup4.py in out 22` | 4 layers. In1 = GND. In2 = +12V y 1.0–11.5 / GND guard 12–13 / +5V 13.5–17.7 / GND under the bus 18.2–22. B.Cu GND pour. |
| 5 | `fanout.py in out` | Everything scripted is **locked**. See below. Refuses to run on a board that already has tracks. |
| 6 | `autoroute.py in out work 150 --drop "+12V,GND,+5V" --fixed` | Freerouting on the remaining signals. The DSN gets: B.Cu strip keep-out, 0.55 mm edge margins, **1.0 mm from the bevelled wall edge**, and a via keep-out across the In2 +5V lane under U1. |

**What fanout.py locks:**
- **J1 (decision 0007):** vias in the pad tops, at y 7.65; 4 per power pad, 1 per signal pad. Holes are cut in J1's keep-out to suit.
- **Corners:** the corner via fields.
- **Bus:** the B.Cu bus lines and their corner fan-outs.
- **CAN drops:** both are **F.Cu walls**, CANH at x −4.0 and CANL at x −1.0, so B.Cu under LED2 stays free for crossings.
- **Termination:** the termination taps.
- **Crystal and buck:** the crystal copper and the buck copper.
- **U1 escape, by hand:**
  - SWDIO/SWCLK/GPIO_SPARE/UART_RX/UART_TX/NRST go to the strip test pads, each through its own gap in the J1 via row.
  - CAN_TX/CAN_RX/CAN_RS go on B.Cu under the crystal, to vias in the X3|X4 gap, and on to U2.
  - The +3V3 trunk runs TP2 → strip bottom F.Cu lane (y 1.25) → C11/U2, and up at x 0 to a B.Cu spine at y 12.6 (U1.5, C8, D2/D3, R9). The west supply group (U1.16, C7, C9) is fed from the lane's west end.
  - LED_EN and LED_D1 run on B.Cu over U1's top (y 17.6 / 18.05).
- **Power pads:** a collision-checked via for every other power pad.

**Placement changes for routing (2026-11-16):**
- **Test pads:** re-ordered to match U1's escape: TP4 SWDIO, TP5 SWCLK at (−22.86, 2.54/6.35); TP9 GPIO_SPARE (−19.85, 2.54); TP8 UART_RX (−19.05, 6.35); TP6 NRST (−17.3, 2.6); TP7 UART_TX (−16.6, 5.8); TP2 +3V3 / TP10 +12V at x 16.51; TP3 GND (20.32, 6.35).
  - NRST now sits beside the SWD pads, so the jig needs one SWD group.
- **R15:** vertical under U1 pin 1.
- **C8 ↔ C10 swapped:** NRST runs straight to C10.
- **R13:** beside C6.
- **C11:** moved to (−13.8, 2.9).
- **C2:** moved to (4.4, 10.7).
- The jig hasn't been built, so the new TP coordinates are the reference.

**Step 7:** `finish.py routed out` adds:
- J1's allow-bridged-mask flag,
- the F.Cu GND pour (≥1.0 mm from the wall edge),
- the F.Cu VIN_LDO pour at U3,
- the refill,
- and a report of the narrowest In2 +12V cross-section.

**State (2026-11-16): ROUTED.**
- `hardware/edge-board/edge-board.kicad_pcb` is the **routed active board**, after `finish.py`:
  - **0 unconnected, 0 DRC errors, schematic parity 0.**
  - Warnings left: silkscreen only (reference text over pads and edges) and 1 library-footprint mismatch (J1: the in-pad holes in its keep-out).
- **Pipeline input** (placed, 4-layer, no tracks): `output/placement-trial/base/edge-board-placed.kicad_pcb`. To rebuild, run `place.py` from it, then the remaining steps.
  - Copy the project's `.kicad_pro`/`.kicad_dru` next to every scratch board first, so zone fills use the custom rules.
  - **Don't run "Update footprints from library" on J1**: that drops the in-pad holes in its keep-out.
- **Schematic:** pin swap LED_RET ↔ LED_EN, [decision 0008](../../../../docs/decisions/0008-mcu-pin-swap-led-ret-led-en.md).
- **In2 +12V:**
  - The narrowest total cross-section is 6.35 mm at x ≈ −30 (H1 jig hole, U4/C15 vias); the narrowest single run is 2.7 mm.
  - The constraints session measured 9.4 mΩ end to end, with short necks only. **Decision (LAYOUT-NOTES §13.2): 0.5 oz inner copper is fine as long as the fuse is ≤5 A.**
  - **Don't let the west-half In2 gap between +12V and +5V (2.0 mm, no GND guard) shrink below 1.5 mm.**
- **Logic vias through the In2 +12V/+5V regions** keep ≥0.5 mm plane clearance: the `logic via vs In2 supply` rule (LAYOUT-NOTES §13.6), set in `setup_rules.py`. Verified: the closest is 0.50 mm, across 42 vias.
- **Via-in-pad on reflowed parts (decision 0007, user-approved):** one, on D3.1 (GND).
- **Still to do:**
  - silkscreen clean-up,
  - a check against the LAYOUT-NOTES §13 list before fab,
  - the passive board.

## Height: **H = 22 mm** is the minimum for a clean 2-layer board
The binding constraint is where the corner-to-corner signal bus (CANH, CANL, SENSE, DRIVE) runs. Free area is not the problem: courtyards total 686 mm².

| H | Result |
|---|---|
| 20 | **Fails.** The top row (R7/R8/R10/R11/C14, D2/D3/R9, C20, R3, TP11: 11 parts) ends 0.7–1.9 mm above the 19.5 mm limit, and nothing below has room for it. There is also no B.Cu room for the bus (see below). |
| **22** | **Fits** with the bus on **B.Cu in a band above the +5V lane (y ≈ 18.5–21.5)**. F.Cu stays free for parts; bus nets drop through vias at their taps (X4–X7 stubs, discovery and CAN parts, corner pads). |
| 24 | Needed if the bus stays on **F.Cu over the GND lane** (LAYOUT-NOTES §3). That strip (y ≈ 13–16) runs through the LED row and the MCU region, so U1 (7 mm tall) can only sit above it. |

**Status:**
- **Accepted** by the constraints session (LAYOUT-NOTES 13:20) and the schematic session.
- Recorded as **decision 0005 (Proposed: needs the user's OK before fab)**, SPEC V5.5 and GEOMETRY §2.1.
- Final band: **y ≈ 18.5–20.3**, four 0.25 mm traces with 0.25 mm gaps. Order up from +5V: **CANH/CANL, then DRIVE, then SENSE outermost** (SPEC V5.5 §2, decision 0005, LAYOUT-NOTES §3; see routing condition 1).

Original proposal: bus on B.Cu, y ≈ 18.5–21.5, above the +5V lane.
- It keeps GND or +5V copper between the bus and the buck, and F.Cu GND pour above it is the reference.
- B.Cu stack at H = 22 mm, bottom to top:

| y (mm) | B.Cu |
|---|---|
| 0–8.5 | contact strip |
| 8.5–9.5 | via row |
| 9.5–12.5 | +12V |
| 13–16 | GND |
| 16.5–18 | +5V |
| 18.5–21.5 | signal bus |

## Zone plan (board frame: x = 0 at centre, y up from the wall edge; all parts on F.Cu)
| Zone | Where | Contents |
|---|---|---|
| LEDs | y 15.5, x −31.2 / 0 / +31.2 (fixed for every shape), rot 0 | VDD (top-left) over the +5V lane, GND (bottom-right) over the GND lane. C1–C4 span both lanes with the +5V pad on top (checked). |
| E | above the strip, LED1…LED2 | U1 (rot 180: OSC/NRST/VDDA/ADC/DRIVE_GPIO pins face right). Y1 at the OSC pins with C5/C6 beside it; C8 (VDDA), C10 (NRST); C7/C9 at VDD/VSS; R15 BOOT0. **Clamps on the MCU side (schematic 13:15):** D3 (DRIVE_GPIO) with pin 3 2.3 mm from U1 pin 10 and R11.1 above it; D2 (SENSE_ADC) next to C14/R10.2. Both rot 180, so GND/+3V3 pins face outboard. Top row (y 20.6): R8, R7 (PA0 divider), R11, R10, C14. |
| A | x < −25, below LED1 | U4 AHCT + C15 at pin 5; D5 SMAJ15A by the corner power pads; tooling hole H1. R5 (33 Ω) beside LED1 DIN; R3 above LED1. |
| S | F.Cu over the strip (no vias) | U2 + C11 + R13, D4 between the X4/X5 vias and U2, R12/JP1; TP4/5/7/8/9 (left); TP1 under X8; TP2/3/6/10 (right) |
| F | above the strip, LED2…LED3 | Discovery (R1 above X7, D1/R2, R9) and C4. A 2.0 mm copper channel at x ≈ 5.5–7.5, between C4 and D1/R1, is kept for the X6 DRIVE stub. **Buck:** U5 with L1 to its left (SW pad facing U5), C16/C17 under VIN, C18 at BOOT/SW, FB network R16/R17/C21 at FB, R18 at EN, C19/C20 at the L1 output. |
| B | x > 25, below LED3 | U3 HT7533 + C12 at the tab, C13 at VOUT, R14 low and outboard (VIN_LDO pour around tooling hole H2, both layers); U3 ≈11 mm from U5 |

## Test-jig reference (board frame, mm; origin = centre of the wall edge; same on every shape)
| Item | x | y | Notes |
|---|---|---|---|
| **H1** tooling hole | −29.20 | 4.00 | NPTH Ø2.0 (`MountingHole_2mm`), board-only footprint, excluded from BOM/POS. 3.2 mm to the strip, 8.8 mm to the triangle corner pads. |
| **H2** tooling hole | +32.00 | 4.00 | Same. 6.0 mm to the strip, 6.0 mm to the triangle corner pads. |
| TP4 SWDIO / TP5 SWCLK | −22.86 / −19.05 | 2.54 | |
| TP7 UART_TX / TP8 UART_RX / TP9 GPIO_SPARE | −22.86 / −19.05 / −15.24 | 6.35 | |
| TP1 SPARE | 12.70 | 5.08 | |
| TP10 +12V / TP3 GND | 16.51 / 20.32 | 2.54 | on every board (Pop ALL) |
| TP2 +3V3 / TP6 NRST | 16.51 / 20.32 | 6.35 | |
| TP11 +5V | 11.20 | 19.70 | on every board. Above D1/R2. The pad sits over the B.Cu bus band, so its +5V via goes at y ≤ 18 (in the +5V lane), reached by a short F.Cu trace; never under the pad (routing condition 10). Moved from above LED1 to stay ≥1 mm from the tab windows. |

Pads are Ø1.5 mm. All are on F.Cu, the inward face.

## Rule checks (from place.py)
- **Buck SW node vs Y1/C5/C6/C14/SENSE_ADC (incl. D2): 22 mm** (≥10 required).
  - vs CAN pads ≥17 mm; vs LED_RET 30 mm.
  - vs the SENSE bus (D1/R2 side): 5.5 mm. Accepted by the constraints session: sub-mV coupling, and discovery runs with the buck off.
- **GND hop columns (LAYOUT-NOTES §3) are clear:**
  - x = −22.5 is shared by X1 and X3. X3's via jogs along y ≈ 9 to X1's hop, so the hop must be sized for 2 springs: ≥1.6 mm wide, ≥6 vias. That keeps Y1 at the OSC pins.
  - x = +22.5 for X10 has its own GND-lane vias (condition 4).
- **Signal stubs:**
  - **CAN stubs X4 and X5 go up under LED2's body**, between its pad columns. The x −7.5 column is now used by the crystal caps, D2 and C10.
  - The X4 via jogs along y ≈ 9 to under LED2, below C5/C6.
  - **The X6 DRIVE stub must not go under LED2** (condition 8). It runs up the channel right of C4 to a bus via at y ≈ 19, ≥1 mm from C4's +5V pad.
- Tall parts (L1, U2 SOIC, D5 SMA, U3) are ≥12 mm from any LED or below the LED row.
- **Triangle corner fan-out is tight:** about 1.5–2 mm between the core edge (|x| ≤ 37.0) and the corner pads for 4 bus lines. That's fine on the hexagon.

## Agreed with the schematic session (for routing)
- **Corner pads stay where they are; the lanes jog down at the board ends.** Corner +12V sits at y 1–5 against the lane at 9.5–12.5, GND at 7.5–11.5 against 13–16, +5V at 14–16 against 16.5–18.
  - Keep each jog at full lane width.
  - Keep GND copper between the +12V and +5V jogs.
  - Moving the pads up instead would push the +5V corner pad into the bus band.
- **Tooling holes are board-only footprints** (H1/H2 above). Update-from-schematic and `sync.py` leave them alone.
- **LED rot 0 with diagonal DIN/DOUT: accepted.**
- **B.Cu bus accepted** (decision 0005, SPEC V5.5): GND copper or a ≥0.5 mm gap between the +5V lane and the bus. The bus order is in routing condition 1.

## Rule areas on the board (added by place.py)
- `top-edge keepout B`: B.Cu, the whole length, y 21–22. No copper, vias or pour, for the mouse-bite tabs.
- `panel-tab x-32`, `panel-tab x-2` and `panel-tab x+30` (centres −31.5, −2.0, +30.0): F.Cu, 5 × 1 mm at the top edge. No copper and no parts.
  - Positions per LAYOUT-NOTES §10 (13:40): no MLCC or crystal within 3 mm, and ≤ ~20 mm end overhang.
  - Measured on this placement:

| Tab | Nearest MLCC pad | Nearest any pad |
|---|---|---|
| −31.5 | C1, 4.6 mm | R3, 1.5 mm (TP11 moved away) |
| −2.0 | C14, 4.1 mm | D2, 2.2 mm |
| +30.0 | C3, 5.3 mm | LED3, 3.3 mm |

  - Overhang: left 17.9 / right 14.4 mm on the hexagon, 12.0 / 8.5 mm on the triangle.

## Routing conditions from the constraints session (13:20)
1. **Bus on B.Cu:** y ≈ 18.5–20.3.
   - **Order up from +5V: CANH/CANL, then DRIVE, then SENSE outermost.** SPEC V5.5 §2, decision 0005 and LAYOUT-NOTES §3 all agree, as reconciled by the schematic and constraints sessions.
   - Why: only the CAN pair is next to +5V, because a SENSE or DRIVE short to a supply would pump 3V3 above the CH32's 4.0 V absolute maximum through the BAT54S (CAN pins tolerate −4…16 V). SENSE is high-impedance, so it sits furthest from the LED-current lane.
   - GND copper, or a ≥0.5 mm gap, between the +5V lane and the bus.
   - ≥1.0 mm copper-free along the top edge on B.Cu (rule area above).
   - Drop the bus to F.Cu before the corner-jog region (|x| > 25), and stagger the fan-out vias on the triangle.
2. **Soft:** F.Cu GND pour over the bus band where parts allow, stitched to the GND lane at ≤10 mm.
3. **Shared X1+X3 GND hop at x −22.5:** ≥1.6 mm wide and ≥6 vias per end. X3's jog along y ≈ 9 goes on **F.Cu**; on B.Cu it would cross the X2 +12V neck at x −17.5.
4. **X10 hop:** ends in its own GND-lane vias, not through C16/C17's pads, so bridge return current stays out of the buck's hot-loop ground.
5. **C17 GND pad goes straight to U5's GND pin on F.Cu**, plus a lane via.
6. **Corner jogs:** keep full widths (≥2.8 mm for +12V/GND, ≥1.5 mm for +5V), ≥0.5 mm gaps, and only at |x| > 25.
7. **SW node about 5.5 mm from the SENSE bus:** accepted.
8. **Clamp-path rule (LAYOUT-NOTES §5, 13:40):** SENSE and DRIVE stubs and taps keep ≥0.5 mm (or GND) from any +5V or +12V pad: LED VDD, C1–C4, buck VIN/SW/output, D5. The X6 DRIVE stub does **not** run under LED2's body; the CAN stubs may.
9. **BAT54S clamps on the MCU side** (schematic 13:15): keep D2/D3 GND and +3V3 connections short, with a GND via just below each into the GND lane.
10. **TP11 (+5V) via:** in the +5V lane at y ≤ 18, reached by a short F.Cu trace from the pad. Never under the pad, which sits over the B.Cu bus band (DRIVE/SENSE). LAYOUT-NOTES §10.

## Open points
1. **User approval of decision 0005** (B.Cu bus, H = 22) before fab. Routing can start on this placement.
2. **Back reflector clearance:** parts sit down to y ≈ 0.6 on the inward face (TPs, U2, D5, C13). The reflector must stop ≥2.5 mm short of the board face, or be notched.
3. **LED data chain crosses the bus** at each LED (DIN top-right, DOUT bottom-left on this footprint). With the bus on B.Cu that costs nothing; with an F.Cu bus every LED needs a crossing.

## Scripts (KiCad 9 bundled Python: `C:/Program Files/KiCad/9.0/bin/python.exe`)
- `sync.py board.kicad_pcb netlist.net ../lib/footprints/ModularLight.pretty FORCE_REFS`: netlist → PCB sync. Verify with `kicad-cli pcb drc --schematic-parity`.
- `place.py in.kicad_pcb out.kicad_pcb L H`: places the core, draws the outline, and checks envelope/margins/SW distance. Shape variants change only L (81.9 / 89.4 / 93.7).
- `trial.py` and `trial_*.kicad_pcb`: the earlier stand-in fit trial (superseded).
