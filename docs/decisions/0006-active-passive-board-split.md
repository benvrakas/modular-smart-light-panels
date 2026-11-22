# 0006 — Separate active (4-layer) and passive (2-layer) edge boards

> **Superseded by [0009](0009-rear-controller-board.md) (SPEC V6.0):** there is no active edge board any more. The MCU section moves to a rear 4-layer controller board, and every edge board is passive (2-layer).

**Date:** 2026-11-15 · **Status:** **Accepted.** The user approved it in the PCB session: "Since we already have different size boards for different polygons, we may just want to have the ActiveBoard [4] layers and the rest of them two layers … split the design into … the active and the passive boards", then "That sounds good" to the plan. The PCB session relayed the approval. · **Supersedes:** SPEC §3.5 "one bare PCB for all edges with population variants" (V5.4 already made the outline per shape).

## Context

- Decision 0004 already requires a separate outline per polygon shape, so "one universal PCB" was gone in practice.
- The PCB session ran a Freerouting probe on the 2-layer active board, with signals on F.Cu only. It left **7 of 53 connections unrouted** (LED_EN, LED_DATA, D_IN, CAN_RX, CAN_RS, SPARE, GPIO_SPARE), and that was before power fanout, layer hops or buck copper. All of the congestion is in the MCU, buck and CAN section.
- A passive board has only the LEDs, the discovery diode/resistor, contacts and corners. It routes easily on 2 layers.

## Decision

**Two board types per shape:**

| | Active (1 per panel) | Passive (N−1 per panel) |
|---|---|---|
| Layers | **4**: F.Cu signals/parts; In1 solid GND; In2 power: +12V region low │ GND guard (or a ≥1.5 mm gap) │ +5V region │ GND under the B.Cu bus band (y ≳ 18.2 mm). In2 is the bus's reference plane (0.21 mm away), so the bus never sits over +5V, and +12V never sits beside +5V. Inner copper weight follows the measured criterion in the follow-up below. B.Cu: contact pads, the 0005 bus band, extra routing | **2**: the V5.5 B.Cu lane stack and bus, unchanged |
| Project | `hardware/archive/edge-board-v5/` (existing project: the PCB, placement and UUIDs stay linked) | `hardware/edge-board/` (new) |
| Edge ID | always code 0 (R1 = 0 Ω) | codes 1…N−1 (R1 per edge, BOM variants) |
| Parts | everything: MCU, CAN, LDO, buck, level shifter, protection, LEDs, discovery | 3 LEDs, C1–C4, D1, R1 (R2 DNP); test pads TP1/TP3/TP10/TP11 |

**Interface contract** (both board types must match it exactly; the PCB session checks each layout against it):
- J1 pads (`EdgeContacts_SpringPads`), with the origin at the polygon-edge midpoint on the wall edge.
- CornerJoint_L/_R pads and their y positions, placed with local y = 15 at 1 mm above the wall edge, including the +5V / GND / +12V pads.
- LEDs at x = −31.2, 0, +31.2 and y = 15.5, rotation 0.
- Outline length per shape (decision 0004), H = 22 mm (decision 0005) and 1.6 mm board thickness on both types.
- The B.Cu bus band position and order (CANH/CANL, DRIVE, SENSE), so bridges and corners see the same thing on either board type.

**Schematics:** two flat schematics, generated from one source so the shared part definitions can't drift.
- Shared parts keep the same reference designators and values: J1–J3, LED1–3, C1–C4, D1, R1, R2, TP1, TP3, TP10, TP11.
- A hierarchical shared sheet was considered and not used. It would change every symbol path and unlink the active board's existing placement, and sharing one sheet file between two KiCad projects is fragile.
- Population-only parts are gone:
  - On the passive board, R3 (the D_IN → LED1 link) becomes a plain net.
  - On the active board, R3 is dropped and R1 is fixed at 0 Ω.

## Consequences

- **Cost:**
  - 4-layer fab applies to only 1 of 6 boards per hexagon.
  - Passive assembly drops to about 10 placed parts, with no buck, MCU or extended parts.
  - The hex kit becomes 1 active board (4-layer order) plus a 5-board passive panel (2-layer), with R1 codes 1–5 as BOM variants.
- **Active board:** the extra layers give solid GND under the MCU, buck and crystal, and clean power distribution. The buck's EMI and the SENSE node both get easier.
- **Consistency risk:** two layouts can drift apart at the interface. The contract above and a check before every fab order address this.
- **SPEC:** §3.5 is rewritten for two board types, and §2 gets a note on the active board's 4-layer stack.

## Follow-up (2026-11-16, SPEC V5.7.2): inner copper and In2 separation

The original "0.5 oz needs a +12V region ≥10 mm wide" rule was a rule of thumb. Read literally, the routed board fails it at short necks, but those necks barely matter physically. The constraints session measured the routed rev A board and replaced the rule (LAYOUT-NOTES §13.2).

- **0.5 oz inner copper passes if all of these hold:**
  - end-to-end +12V plane resistance ≤10 mΩ;
  - no neck narrower than 6 mm;
  - no neck narrower than 8 mm that is longer than 5 mm.
- **Use 1 oz** if any check fails or the domain fuse is above 5 A.
- **Rev A measured:**
  - Mean width after antipads: 9.8 mm, giving 9.4 mΩ: 47 mV and 0.24 W at 5 A. This matches 0.98 mΩ/sq for 0.5 oz Cu, about 9.6 squares.
  - Worst neck: 6.25 mm wide over 3.7 mm at H1, adding about 0.6 mΩ and 15 mW.
  - **The board passes.** 0.5 oz inner copper is fine for a fuse of 5 A or less.
  - Through-board current is far below this anyway: the bridge assumption is ≈2 A of +12V per bridge path (§8).
- **Earlier advice superseded:** the PCB session's note to "order 1 oz inner because the narrowest section is 6.35 mm" no longer applies. 1 oz remains an optional extra margin for the prototype.
- **In2 +12V/+5V separation:** a GND guard ≥1 mm **or** a copper-free gap ≥1.5 mm. The rev A board has a guard for x > +0.4 and a 2.0 mm gap on the west half.
