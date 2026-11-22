# 0009 — Controller on a rear daughter board, all edge boards passive, shorter edge boards

**Date:** 2026-11-16 · **Status:** **Accepted** (the user approved the proposal shown in the explainer: "Yes, very good… go ahead with all") · **Supersedes:** [0005](0005-exterior-signal-bus-h22.md) (lane stack, H = 22 mm), [0006](0006-active-passive-board-split.md) (active/passive edge boards), and [0007](0007-vias-in-pads-active-board.md) as an active-board-only rule. In-pad vias are now simply allowed.

## Context

- The V5 active edge board carried the MCU, CAN, regulators and 5 V buck. Fitting all of that into the triangle-length core needed a 22 mm board height (0005) and a 4-layer active board (0006).
- The user wants **shorter edge boards** for a slimmer panel. On an active edge board that is hard to achieve.
- Most of the 22 mm came from the exterior lane stack, not the MCU. That stack existed because the inward face was crowded with MCU-section parts.

## Decision

- **Every edge board is passive and identical per shape** (2-layer): LEDs, decoupling, ID diode + resistor, contact pads, lanes, test pads and the controller-joint pads.
  - The edge ID resistor is still a BOM variant per position.
  - The **code-0 board** is where the controller joins; the LED chain starts and ends there. A population option (for example a 0 Ω link that is DNP on the code-0 board) lets the shared design serve that role.
- **A small 4-layer controller board** carries the MCU, CAN transceiver, 5 V converter, LED-rail switch, level shifter, 3.3 V regulator and protection.
  - **Placement:** it lies flat on the printed back plate at the **rear of the light chamber, inside the enclosure**.
  - **Parts face the wall,** in a pocket of the back plate. The chamber-facing side is plain **white solder mask** and acts as part of the back reflector, so nothing casts shadows.
  - **One design for every shape,** so it is **sized for the triangle** (added 2026-11-16, user correction).
    - **Shape:** a trapezoid with 60° sides, base along the code-0 board ≤ ≈72 mm, depth ≈20–25 mm.
    - **Why:** a rectangle the length of the edge board doesn't fit inside a triangle.
    - **Other shapes:** squares and hexagons fit it with room to spare.
  - **Mounting:** held by a snap fit in the back plate.
- **Joint:** ≈10 edge pads along one edge of the controller board, **drag-soldered by hand at 90°** to matching pads on the code-0 edge board's inward face.
  - Nets: +24V, GND, +5V (to the LEDs), LED data out, LED return in, CANH, CANL, SENSE, DRIVE, and a spare.
  - The joint carries no mechanical load.
- **Edge board height target: H = 10–15 mm**, down from 22 mm. The estimate is ≈12–13 mm; the layout sets the final value.
- **Minimum constraints** (user instruction: no artificial rules). Lanes and the bus may run on either face at any height. Only constraints with a stated reason apply:
  - **Contact pads on the exterior face, inside the springs' contact zone:** the seam bridge presses there.
  - **GND pads reach closest to the wall edge:** they make contact first when a panel slides in.
  - **DRIVE never adjacent to +24V:** a short would be destructive.
  - **+24V never beside +5V without GND or a gap between them:** a short would put 24 V on every LED.
  - **LED positions are shared by all shapes:** set by the optics.
  - **Board thickness is 1.6 mm:** it sets the seam inset and the corner geometry (decision 0004).
- **Soldering:** small parts on both boards are pasted and reflowed; the corner and controller joints are drag-soldered. The user is fine with hand-soldering joints; the concern is only tiny parts.

## Consequences

- **The PCB work changes.** The V5.7 active edge board layout (fully routed) stops being the target, and its circuit becomes the starting point for the controller board. The passive board is re-laid out for minimum height.
- **The triangle core gets easier.** It no longer has to hold an MCU, just LEDs, the ID circuit and joint pads.
- **Optics:** a shallower chamber raises hot-spot risk (gap A1). The frame can hold the diffuser above the board top if the optics test needs more mixing distance.
- **Contact strip:** shrinking it from ≈8 mm to ≈6 mm saves height, but the bridge springs must then touch lower. The bridge prototype has to confirm that.
- **Cost:** roughly neutral.
  - Edge PCBs: 6 × short 2-layer boards instead of 1 × 4-layer + 5 × 2-layer.
  - Controller board: one small 4-layer board.
  - Assembly: two orders (edge boards, controller boards).
  - With decision 0010 (24 V), a hexagon is ≈$9–18.
- **Serviceability:** a dead MCU means desoldering one joint and swapping the controller board.
- **Room for extras:** the controller board has space for later additions such as a light sensor, temperature sensor or microphone.
