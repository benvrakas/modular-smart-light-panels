# 0007 — Vias in pads on the active board (J1 contact-pad tops)

> **Updated by [0009](0009-rear-controller-board.md) (SPEC V6.0):** the active edge board no longer exists. In-pad vias are now simply allowed on every edge board where they help.

**Date:** 2026-11-16 · **Status:** **Accepted.** In the PCB session the user said: "I'm not too worried about having vias in the pads … especially on the parts that will be hand soldering." · **Changes:** SPEC §3.3 (contact strip: "no vias"), LAYOUT-NOTES §2 and §13.3 ("≥4 per pad, at y ≥ 8.5 (no vias in the strip)"; "No vias in the corner pads").

## Context

- On the 4-layer active board, each J1 power pad (X1, X2, X3, X9, X10) needs ≥4 vias into its plane, and each signal pad (X4–X8) needs one.
  - The rule kept every via above the strip, at y ≥ 8.5.
  - That placed rows of 2×2 via fields at y ≈ 9.1–10.0, right under the MCU.
- Every MCU signal bound for the strip had to pass through 2.9 mm gaps between those fields:
  - the SWD, UART and NRST test pads,
  - the CAN transceiver U2.
- Freerouting stopped at 9 unconnected nets in that band with every strategy tried.
- The springs come to rest mid-pad (LAYOUT-NOTES §2: "aim for the middle") and slide in from the wall edge. They never reach the top end of a pad.

## Decision

1. **J1 pads: vias inside the top end of each contact pad.**
   - All 10 pads end at y = 8.0. The vias sit in one row at **y = 7.65** (0.6 mm via, 0.3 mm drill; ring at y 7.35–7.95).
   - Power pads get **4 vias at 0.75 mm pitch**. Signal pads get 1 via.
   - The footprint's "contact-strip keepout" keeps blocking vias everywhere else in the strip. On the active board it gets a hole over each pad's top end (y 7.25–8.0, pad width). `fanout.py` adds the holes to the board copy of J1; the library footprint is unchanged.
   - No necks are needed any more. The pads drop straight into the planes.
2. **New mechanical limit on the bridge:** the spring's **final contact point must stay ≤ 6.8 mm from the wall edge**, including tolerances. That is 0.55 mm below the via rings.
   - The pad middle is about y 4.2–4.5, so this leaves about ±2.3 mm of scatter.
   - The bridge/carrier design must respect it.
3. **Corner pads (hand-soldered): allowed, but not used for now.**
   - The user's approval covers them. Solder wicking into open vias is not a concern for hand soldering.
   - They don't work at the corners, though. Directly behind the +12V pad, on F.Cu, sit the DRIVE and SENSE pads, and LAYOUT-NOTES requires 0.5 mm between DRIVE/SENSE and +12V. An in-pad via there can't meet that.
   - The corner via fields stay just inboard of the pads, as before.
4. **Machine-assembled parts keep vias out of their pads where possible.** Small reflowed pads (0603, TSSOP) lose paste into an open via.
   - **One exception:** D3.1, the GND pin of the DRIVE_GPIO clamp (BAT54S, SOT-23). It is boxed in by SENSE_ADC and +3V3, so it carries a 0.3 mm via at the outer end of its pad.
   - If that joint shows starving, order that via plugged/capped, or rework the clamp area.

## Consequences

- **More room above the strip:** the band between the strip and the MCU (y ≈ 8–12) is free of via rows. With the decision 0008 pin swap, the active board then routes completely (0 unconnected, 0 DRC errors).
- **Inner planes:**
  - In1 GND gets antipads under the X2/X9 +12V via rows. Four vias at 0.75 mm pitch merge into one ~3.3 × 1.2 mm slot per pad.
  - No trace can cross that slot, because the via pitch leaves no gap for one. So no return path is cut, which is the intent of the LAYOUT-NOTES §13.2 web rule.
  - In2 +12V gets similar slots under the GND rows (X1/X3/X10). The +12V plane loses ≈1.2 mm of width locally over 3.3 mm, which doesn't matter for resistance.
- **Passive board:** unchanged. It is 2-layer, and its pads neck into the B.Cu lanes. It may adopt the same in-pad vias later if useful.
- **Fab note:** vias in an open-mask contact pad are plated and exposed, like the pad (ENIG). No plugging is needed, because the springs never touch them.
