# 0021 — Segment bridge and superclusters (classic CAN kept)

**Date:** 2026-11-22 · **Status:** **Accepted as a plan** (user: "we can stick with CAN … have a bridge connector that actually doesn't connect the CAN lines, only the ground lines and physical connection … multiple panel clusters that are physically interlinked, but not electrically … detect each other and find their relative orientation to form like a supercluster that's controlled by two separate controllers"). To be verified on rev A hardware. · **Changes:** SPEC §1, §3.3, §4.4 (new), §5, §7.1, §7.4, §10.

## Context

- Each CAN segment has one cluster controller and carries all of its cluster's traffic (§5). Per-LED streaming from the cluster controller was considered. Classic CAN at 1 Mbps can stream every LED of about 20 hexagons (RGBW) or 26 (RGB) at 30 fps; 250 kbps, today's spec, only about 5.
- **CAN FD was evaluated and not adopted** (user: "we can stick with CAN"):
  - The CH32V203 and the ESP32-C6's CAN controller are classic only. CAN FD needs a new panel MCU (AT32M416 or STM32C092) and an ESP32-C5 or an MCP2518FD.
  - It would add ≈$0.45–1.00 per panel and a controller-board redesign with a firmware port.
  - A 2 Mbps data phase would carry about 3× classic CAN at 1 Mbps; 4 Mbps would need SIC transceivers and lower-capacitance TVS diodes.
  - Smaller segments, each with its own cluster controller (≈$8 each, ≈$0.30 per panel), give the same bandwidth on classic CAN.
- Until now, splitting a wall into two segments also split it into two clusters. Each had its own local frame and needed its own room placement, and discovery couldn't see across the split.

## Decision

- **Segment bridge:** a bridge that passes **GND and the SENSE↔DRIVE cross** but not CANH/CANL. Two CAN segments can share one rigid, clipped wall, and discovery still works across the seam. SENSE/DRIVE has to cross: it is the only electrical path that can identify the neighbouring edge, and it is panel-local, not a bus. GND has to cross because the SENSE readings need a common reference. SPARE is left as on the standard bridge.
- **Variants are BOM variants of the one bridge PCB, made by leaving out face-A springs:**

| Variant | Face-A springs left out | Joins CAN | Joins +36V |
|---|---|---|---|
| Standard | none | yes | yes |
| Isolating (power domains, §8) | SA2, SA9 (+36V) | yes | no |
| Segment | SA4, SA5 (CANH, CANL) | no | yes |
| Segment + isolating | SA2, SA4, SA5, SA9 | no | no |

  - Panel A's pads for those nets then touch nothing. The bridge net still reaches panel B through its face-B springs but stops at face A's empty lands. The bridge is 180° symmetric, so it works either way round.
  - **No layout change.** This replaces the plan in BRIDGE-NOTES of a +36V cut with DNP links.
  - **Cost:** face A pushes on panel A with fewer springs (8 springs ≈ 5.6 N, 6 springs ≈ 4.2 N, instead of ≈7 N). The clip carries the imbalance. If that ever matters, a later bridge revision can keep every spring and cut the nets with 0 Ω links instead.
- **Superclusters:** clusters joined by segment bridges form a **supercluster**: one rigid assembly, one 2D frame and one room placement, served by several cluster controllers, one per segment.
  - **Cross-segment discovery (SPEC §4.4):** the coordinator schedules every DRIVE pulse of all the segments it controls on the shared clock, one pulse at a time. Each panel already reads only its own edge code from SENSE. The driver's identity comes from the time slot.
  - **Fewer slots:** only panels with an edge left unpaired after their own segment's discovery take part, as drivers and as readers.
  - **Clock skew:** readers sample through the whole slot and report a code only if it holds steady for ≥1 ms. That tolerates the ≤2 ms skew between cluster controllers without stretching the ≤5 ms DRIVE pulse (the R11 fault limit, §3.2).
  - **Relative pose:** one cross-segment edge pair fixes the exact 2D transform between two clusters' frames, because both are rigid and in one plane. Further pairs must agree; a mismatch flags a badly seated bridge.

## Consequences

- **Rules:**
  - Every segment needs its own cluster controller on one of its own free outer edges, and its own far-end termination (§5).
  - Panels behind a segment bridge with no controller are invisible: no CAN, so they can't join the schedule.
  - A standard bridge put in by mistake between two segments puts two cluster controllers on one bus. Controllers must detect another controller's frames and report it; the coordinator then lets one of them own the merged segment.
- **Marking:** segment bridges need to be told apart when assembling (clip colour or a printed mark).
- **Discovery is coordinator-scheduled** whenever more than one segment is reachable. A cluster controller with no coordinator still runs its own discovery. If an unscheduled neighbour interferes, the readings are inconsistent and it retries after a random delay.
- **Room placement:** the AR fit (§7.4) solves one pose per supercluster.
- **Rev A test:** build two small triangle clusters joined by a segment bridge (BOM variant only) and check the cross-segment codes and the derived transform. The bus-speed test at 500 kbps and 1 Mbps (settling time after a dominant-to-recessive edge) is a separate open item.
