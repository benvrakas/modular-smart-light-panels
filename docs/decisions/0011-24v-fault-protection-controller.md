# 0011 — 24 V fault protection on the controller board

**Date:** 2026-11-16 · **Status:** **Accepted by the coordinator** under the user's delegation to coordinate prototype work (2026-11-16). The user may override. · **Proposed by:** the schematic agent (`hardware/controller-board/SCHEMATIC-NOTES.md` §4–§5, §10) · **Changes:** SPEC §2, §3.2, §4.1, §4.2

## Context

Decision 0010 moved the bus to 24 V. The V5 discovery circuit (R10 = 1 kΩ on SENSE, R11 = 100 Ω on DRIVE, BAT54S clamps into 3V3) survives 12 V faults but not 24 V:
- **DRIVE can't be fixed with one resistor.** Surviving a sustained 24 V short needs ≈10 kΩ, but reading code 0 correctly needs ≲1 kΩ.
- **Clamp current lifts the 3.3 V rail.** Current pushed through the SENSE clamps into 3V3 would raise the rail above the CH32V203's 4.0 V absolute maximum, because the HT7533 can't sink current.

## Decision

- **DRIVE is driven by an open-drain N-MOSFET** (2N7002, gate from PA4 with a 100 k pull-down) through **R11 = 470 Ω 1206**.
  - **When idle**, the MOSFET is off, so a sustained 24 V short draws no current.
  - **While this panel drives** (a discovery slot), the short is a 1.1–1.5 W pulse in R11 that lasts only as long as the slot.
  - The V5 DRIVE-side BAT54S is removed.
- **SENSE:** R_pu and R10 are both **10 kΩ 0805**, so they survive 28 V continuously. The BAT54S stays on the ADC side.
- **3V3 overvoltage shunt:** a **TLV431A** clamps 3V3 at ≈3.56 V. It sinks the fault current injected through the SENSE clamp (≈4.9 mA at 24 V), which would otherwise lift 3V3 past 4.0 V in standby.
- **CAN TVS:** **NUP3105LT1G** (DOWO, C22390031). 36 V standoff stays off at the 28 V bus maximum; it clamps at ≤60 V at 6 A, adds 12–16 pF per line, and is also used on SENSE/DRIVE.
- **Per-panel input protection:** a resettable fuse (PTC) of ≥30 V on the controller's +24V input, **upstream of the SMAJ28A**. A shorted controller or failed TVS then trips its own PTC, not the domain's injection fuse. **Chosen (V6.2.1): F1 mSMD050-60V** (TECHFUSE C70113, 1812, 0.50 A hold, 60 V). The domain's injection fuse must be time-lag so F1 trips first.
- **Firmware rules, each with its reason:**
  - **Assert DRIVE for ≤5 ms per slot:** this bounds R11's pulse into a DRIVE-to-24 V short.
  - **Sample SENSE ≥1 ms after DRIVE goes low:** R10 = 10 k slows the ADC node.
  - **Send all-zero LED data before switching the LED rail off:** the switch's soft turn-off ramp.
- **Layout rules updated (§2):**
  - "DRIVE never adjacent to +24V" drops from a damage rule to a **preference**: the short is now survivable.
  - The +24V/+5V rule is **generalised**: +24V copper may only sit next to GND or 24 V-tolerant nets (CAN, SPARE, SENSE, DRIVE), never next to +5V_LED, LED data or LED return. Those nets reach LED or logic inputs that 24 V destroys.
- **Inductor:** keep the FNR6045S220MT (22 µH, 4.5 mm tall).
  - **Why not the 2.8 mm SMNR6028:** its Isat of 1.45 A is far below the TPS54360B's cycle-by-cycle current limit, so a +5V short would saturate it.
  - **Cost:** the back-plate pocket must be ≥5 mm deep. The chamber floor (controller top = back-plate top) therefore sits at z ≈ 6.6 mm above the wall edge, which sets the LED and joint heights in §3.5. **Update (V6.3):** the controller layout replaced the uniform pocket with a stepped one (≥2.8 mm plus an open window under L1); the floor stays at z = 6.6 mm.

## Consequences

- **Discovery codes shift:** the code voltages become ≈0.68, 0.91, 1.22, 1.59, 2.08 and 2.57 V (still to be calibrated). The smallest gap, code 0 to 1, shrinks from 244 to 228 mV.
- **Cost:** a few cents of extra parts (2N7002, TLV431, 3 resistors, PTC).
- **SPEC §10 items 15 and 16 are closed.**
- **Fallback if rejected:** R11 = 100 Ω with the V5 clamp and the layout rule alone. A DRIVE-to-24 V short then stays destructive.
