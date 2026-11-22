# 0005 — Signal bus on the exterior face, edge board height 22 mm

> **Superseded by [0009](0009-rear-controller-board.md) (SPEC V6.0):** all edge boards are now passive and the target height is 10–15 mm. The lane stack and H = 22 mm below no longer apply.

**Date:** 2026-11-15 · **Status:** **Accepted** (2026-11-15). The user approved it in the PCB session ("yes i approve 0005"), and that session relayed the approval. It was also accepted by the PCB placement and edge-board constraints sessions (LAYOUT-NOTES §3, §9, §11 item 2). · **Changes:** SPEC §2 zoning; board height.

## Context

After the RGBW change (decision 0003) the active board carries a 5 V buck converter and a level shifter, and B.Cu needs a third power lane (+5V). The PCB session placed all 67 parts on the hexagon outline and checked the triangle-length core (output/placement-trial/NOTES.md):

- **H = 20 mm fails:** 11 top-row parts end up above the 19.5 mm limit with nowhere to go.
- **H = 24 mm** is needed if the corner-to-corner signal bus (CANH, CANL, SENSE, DRIVE) stays on F.Cu over the GND lane, as LAYOUT-NOTES §3 planned. That bus strip runs through the LED row and the MCU region, and U1 can only sit above it.
- **H = 22 mm** fits if the bus moves to B.Cu, in a band above the +5V lane.
- Area isn't the limit: courtyards total 686 mm².

SPEC §2 reserved the exterior face (B.Cu) for power, apart from the contact strip.

## Decision

- **Run the signal bus on the exterior face (B.Cu)**, in a band above the +5V lane. SPEC §2 zoning gains this second exception, after the contact strip.
- **Board height H = 22 mm.** This is the placement minimum on both the hexagon and the triangle-length core.
- **B.Cu stack from the wall edge:**

| Band | y (mm) |
|---|---|
| Contact strip (no pour or vias) | 0 – 8.5 |
| +12V lane | 9.5 – 12.5 |
| GND lane | 13 – 16 |
| +5V lane | 16.5 – 18 |
| Signal bus (CANH, CANL, SENSE, DRIVE) | ≈18.5 – 20.3 |
| Top margin | to 22 |

- **Routing conditions:**
  - Keep GND copper or a gap of ≥0.5 mm between the +5V lane and the bus.
  - **Bus order: CANH / CANL next to the +5V lane, then DRIVE, then SENSE outermost.** This matches LAYOUT-NOTES §3: the high-impedance SENSE bus sits furthest from the LED current. Neither SENSE nor DRIVE may be adjacent to +5V or +12V.
    - The BAT54S rail clamps (D2 on the SENSE bus, D3 on the DRIVE bus) sit on the bus side of R10/R11. A bus-to-supply short therefore flows straight through the clamp into the 3V3 rail, limited only by the short itself. R11 is not in that path.
    - The HT7533 can't sink current, so a +5V short lifts VDD to ≈4.5–4.7 V. That is above the CH32V203's 4.0 V absolute maximum (datasheet Table 4-1), so it is a damaging fault, not a margin rule. A +12V short is worse.
    - CANH/CANL tolerate it: the SN65HVD230 bus pins are rated −4…16 V and the PESD2CAN stands off 24 V.
    - (This corrects a review note that estimated the DRIVE-to-5 V case at ≈14 mA through R11. That only applies if the clamp were behind R11.)
    - **Follow-up (same day):** the clamps were then moved behind R10/R11 in the schematic (D2 on SENSE_ADC, D3 on DRIVE_GPIO). A +5V short is now survivable (≈1.4 mA / ≈14 mA), and so is SENSE to +12V (≈8.4 mA, ≈70 mW in R10). The bus order above is therefore a margin rule. **Only DRIVE to +12V is still destructive**, and the stack prevents it.
  - Corner-end lane jogs stay at full lane width, with GND copper between the +12V and +5V jogs.

## Consequences

- **Board area:** the edge PCB is 2 mm taller than the 20 mm first estimate, but 2 mm shorter than the F.Cu-bus alternative.
- **Optics:** the panel depth is set by H and the frame. The optics test (gap A1) still decides whether 22 mm is deep enough; a taller board only adds space.
- **Return path:** the bus has no solid plane directly beneath it, only the F.Cu parts side. At CAN (≤250 kbps) and DC discovery speeds this is acceptable (LAYOUT-NOTES §6).
- **Seam:** the bus is above y ≈ 18.5 mm, far from the seam-bridge springs (y < 9 mm), so the bridge cannot touch it.
- **Jig:** two board-only NPTH tooling holes (Ø2.0 mm at x = −29.2 and +32.0, y = 4.0) are in the PCB as board-only footprints, not schematic symbols. They clear the contact strip and the triangle's corner pads, so one jig fits every shape.

**Alternative if the user rejects this:** keep the bus on F.Cu and use H = 24 mm. That needs no zoning change.
