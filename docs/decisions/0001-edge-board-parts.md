# 0001 — Edge board part selection

**Date:** 2026-11-15 · **Status:** Accepted for prototype rev A · **Schematic:** [hardware/archive/edge-board-v5/edge-board.kicad_sch](../../hardware/archive/edge-board-v5/edge-board.kicad_sch)

## Context

SPEC V4 §3 defines one universal edge board, with an **active** variant (MCU, CAN, regulator) and a **passive** variant (LEDs and pass-through). Every part needed a real, stocked part number before schematic capture. Three spec assumptions failed on checking:

- The TSSOP20 MCU with 64 KB has no CAN.
- The gold-finger card-edge socket approach was replaced by spring contacts.
- The discovery circuit has a sneak path.

## Decisions

### Active-board parts

| Function | Part | LCSC | Why |
|---|---|---|---|
| MCU | **WCH CH32V203F6P6** (TSSOP-20) | C3040880 | Of the TSSOP20 parts, only the F6 has CAN. **The F8P6 has no CAN** (WCH datasheet V2.8, Table 2-1). The "32 KB" flash figure is only the zero-wait area; every V203 has 224 KB of flash in total, which is plenty for the effect engine plus a CAN bootloader. 10 KB of SRAM is enough for 18 LEDs. |
| CAN transceiver | TI **SN65HVD230DR** (SOIC-8) | C12084 | 3.3 V native. Rs pin: high = standby (370 µA, receiver stays on, so it can wake on bus traffic). |
| Crystal | YXC **XL2EL89COI-111YLC-8M**, 8 MHz, 12 pF, ±10 ppm (3225) | C2973805 | CAN bit timing needs better clock accuracy than the internal RC gives. Load caps are 15 pF (C1644). The 18 pF part is out of stock, and 15 pF is closer to 2 × (12 − ~4 pF stray) anyway. |
| 3.3 V regulator | Holtek **HT7533-1** (SOT-89, 30 V in, 100 mA, 2.5 µA Iq) | C14289 | A linear regulator is enough at about 30 mA. A 68 Ω 1206 resistor (C17976) ahead of it takes about a third of the heat. A buck converter would save about 0.3 W per lit panel for about $0.40 more, and is not justified. |
| 12 V TVS | SMAJ15A (SMA) | C693535 | One per panel. Note that the WS2815 absolute maximum VDD is only 13.5 V, so the PSU and injection bridge must protect against overshoot. |
| CAN ESD | PESD2CAN (SOT-23, NUP2105L pinout) | C2687131 | |
| SENSE/DRIVE clamps | BAT54S ×2 | C47546 | Rail clamps behind the 1 kΩ and 100 Ω series resistors. |

### Parts on every board

| Function | Part | LCSC | Why |
|---|---|---|---|
| LED | Worldsemi **WS2815B-V1** (5050-6) | C5446699 | **VIH = 2.7 V, so it is driven directly from 3.3 V** (closes SPEC §10 item 1). DIN2 is the backup input: it is wired to the previous LED's DIN1, which skips one dead LED. |
| ID-path diode | **1N4148WS** (SOD-323) | C2128 | In series with R_ID. See "Discovery fix" below. |
| ID resistor | 0 Ω / 1k / 2k7 / 5k6 / 12k / 27k, 1 % 0603 | C21189 / C21190 / C13167 / C23189 / C22790 / C22967 | Codes 0 to 5 per SPEC §4.2. |

All passives are 0603, from UNI-ROYAL, YAGEO, Samsung and FH, and stocked at LCSC. The full lists are in [hardware/archive/edge-board-v5/bom/](../../hardware/archive/edge-board-v5/bom/): one BOM per variant (`ACTIVE_code0` and `PASSIVE_code1` to `PASSIVE_code5`), in JLCPCB column format.

> **LED superseded by [0003](0003-rgbw-leds-5v-rail.md) (SPEC V5.3):** WS2815B-V1 was replaced by the SKC6812RGBW-NW (5 V RGBW) on a per-panel 5 V buck rail, with a level shifter. The WS2815B row and the PA6 backup-line input above are kept as history.

### Panel-to-bridge contacts: SMT spring fingers on the bridge, plated pads on the edge board

> **Superseded by [0002](0002-seam-bridge-cheap-springs.md) (SPEC V5.2):** the bridge now stands upright in the seam, uses low-cost top-contact LCSC springs, and all edge contacts are on the exterior face. This section is kept as the record of the Harwin flat-bridge design, which remains the fallback.

This replaces the gold fingers and card-edge sockets in SPEC §3.3. The **bridge** is a flat PCB against the wall. Each edge board stands on it, and **SMT spring fingers on the bridge grip both faces of the board's wall edge**. A 3D-printed snap fit provides the mechanical retention, so the contacts carry no structural load. Everything is machine-placed from tape and reel. The edge board carries only plated pads (footprint `ModularLight:EdgeContacts_SpringPads`):

- **Inward face (F.Cu), 5 signal pads**, 4 mm wide at 7 mm pitch: CANH, CANL, SENSE_EDGE, DRIVE, SPARE.
- **Exterior face (B.Cu), 5 power pads**, 4 mm wide at 7 mm pitch: GND, +12V, GND, +12V, GND.
- **Symmetric (revised after PCB review):** each exterior pad sits directly behind an inward pad, so opposing springs balance and the pinch pressure is even. The first draft offset the power pads to one side so the two panels' springs could interleave in the seam; that made the pressure uneven and was dropped. The cost is a wider seam: both panels' exterior springs sit back to back, ≈10–11 mm with S1961-size springs.
- **Mating order:** GND pads reach to 0.3 mm from the edge, +12V to 0.6 mm, signals to 0.9 mm. GND therefore connects first (SPEC gap analysis B2).
- **Routing:** the bridge maps nets with its own traces, including the SENSE↔DRIVE cross-connect. The edge board pinout no longer needs to be a palindrome.
- **Bridge springs** (for the bridge design, not part of this board), all Harwin multi-directional, rated for sideways compression:
  - **Default on both faces:** S1961-46R. 14 A, tin, 4.6 × 3.7 × 3.55 mm, 1.2 N, 887 in stock at DigiKey (thin). It out-rates the larger part, so separate big power springs are no longer needed.
  - **Optional on the exterior face:** S1941-42R. 9 A, gold contact, 9.6 × 5.7 × 7.25 mm, 1.2 N (same force, so pressure still balances), $0.48–0.79, 42k in stock. It widens the seam to ≈20 mm.
  - 10 springs per board, 20 per bridge. Also test a generic LCSC side-contact spring to bring bridge cost down.
  - The pads cover a contact height of about 0.5–8 mm and use a 7 mm pitch, so they fit either family.
- **Corner joints:** mirror-image footprints, `CornerJoint_L` (corner IN, left end) and `CornerJoint_R` (corner OUT, right end). All pads are SMD: signals on the inward face, +12V/GND on the exterior face. No through-holes.
- The **20 AWG power crossover jumpers** (SPEC §2) are no longer needed. The +12V contact sits on the exterior (power-plane) face itself.

Rejected options:
- **PCIe x1 card-edge sockets:** cheap and keyed, but they set a wide seam.
- **TE 2-2363962-0:** a 0.4 mm-pitch mezzanine plug at 0.5 A per contact. It mates in the wrong direction and is not available.
- **Top-down springs** (Harwin S7091 and S7151): good parts, but they don't fit the sideways-grip geometry.

### Discovery fix (deviates from SPEC §4.1)

With plain resistors, a reading panel's SENSE bus connects through R_j to an **idle** neighbour's floating DRIVE bus. From there it can reach a third panel's SENSE bus, and through that panel's R to the panel currently driving. Any 4-hex rhombus contains this path, and it shifts the ADC reading enough to cross code thresholds.

The fix is a **1N4148WS in series with each R_ID** (anode on the SENSE bus). Every SENSE→DRIVE path then conducts only one way: an idle DRIVE bus can only charge up, so it can't sink current. The new expected readings, to be calibrated on hardware:

| Code | R_ID | V_ADC (≈) |
|---|---|---|
| 0 | 0 Ω | 0.55 V |
| 1 | 1k | 0.80 V |
| 2 | 2k7 | 1.13 V |
| 3 | 5k6 | 1.54 V |
| 4 | 12k | 2.05 V |
| 5 | 27k | 2.55 V |
| idle | — | 3.30 V |

R2 (0 Ω, DNP) bypasses the diode if the original scheme is ever wanted.

### LED loop-back

The last LED's DO reaches the active board's corner-IN `D_IN` pad. It goes through 2.2 kΩ to **PA0**, where TIM2 runs on an external clock and counts the returned bits. The backup path (`B_IN`) goes to **PA6** (TIM3_CH1), so a dead last LED doesn't break shape detection. LED data out is **PA7** (SPI1_MOSI + DMA).

## Consequences / follow-ups

- **SPEC.md updated to V5** (2026-11-15) with all of the above. The gap analysis has a V5 status table.
- **Board geometry** (edge height, LED pitch, where the contact pads sit along the edge) is set at layout. The corner-joint footprint is a placeholder until the corner hardware (gap analysis A3) is designed.
- **Before ordering:** prototype the bridge with both spring families and confirm contact resistance, seam width, and retention with the snap fit (gap analysis A2).
- **Availability:** the S1961-46R data spring is the thinnest-stocked part. Alternatives are the S1921-46R, or the S1941-42R everywhere.
