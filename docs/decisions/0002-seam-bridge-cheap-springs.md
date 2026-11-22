# 0002 — Seam bridge with low-cost top-contact springs

**Date:** 2026-11-15 · **Status:** Accepted for prototype rev A (replaces the flat bridge of SPEC V5.1 §3.3) · **Supersedes:** the bridge and edge-contact parts of [0001](0001-edge-board-parts.md)

## Context

The V5.1 bridge was a flat PCB on the wall. Its Harwin S1961-46R springs pressed **sideways** on pads on both faces of each edge board: 10 springs per board, 20 per bridge.

The springs dominated panel cost:
- 20 × ≈$0.16–0.33 put a bridge at ≈$3.40–7.15 including PCB and snap fit.
- At 1.5–2.5 bridges per panel, that is $5–18 per hexagon, about half the panel.

The user asked for a cheaper design.

An LCSC search (2026-11-15, jlcsearch API) found **no low-cost side-contact springs**. The only sideways-rated parts were the Harwin multi-directional springs. The cheap parts LCSC stocks in quantity are **top-contact SMT "antenna" springs**, which compress toward the PCB they are soldered to:

| LCSC | Part | Size (L × W × H) | Finish | Price (100+) | Stock |
|---|---|---|---|---|---|
| C2826517 | BW0019CG-L3.5W1.5H4.3 | 3.5 × 1.5 × 4.3 mm | Gold over SUS301 | $0.024 | 43.5k |
| C2826516 | BW0019BG-L3.5W1.5H3.8 | 3.5 × 1.5 × 3.8 mm | Gold over SUS301 | $0.024 | 18.0k |
| C2826523 | BW0025BG-L2.8W1.55H1.35 | 2.8 × 1.55 × 1.35 mm | Gold over SUS301 | $0.023 | 7.2k |

For comparison:
- Harwin S1941-42R at LCSC: C18236241, $1.15, stock 1.
- Harwin S1961-46R: not stocked at LCSC. About $0.16–0.33 elsewhere.

## Decision

Rotate the bridge so cheap top-contact springs can be used.

- **Seam bridge:**
  - The bridge PCB stands **upright in the seam**, between and parallel to the two panels' edge boards, at the wall edge.
  - It is thin (≈0.8 mm) and fully double-sided: top-contact springs on each face press straight onto the facing panel's exterior face.
  - A 3D-printed carrier (snap fit) holds it in the seam and anchors it to the wall. The panels' snap fits locate on the carrier. **Superseded (2026-11-21, [decision 0012](0012-panel-mechanics-rev-a.md)):** the carrier floats, trapped by the panels and centred by the springs; each panel is located by its own wall puck.
- **Edge contacts move to one face:**
  - All 10 contact pads go on the **exterior face (B.Cu)**, along the wall edge.
  - The inward-face contact pads are removed.
  - Signal nets reach their exterior pads through vias. The B.Cu power planes keep clear of the signal pads.
- **Reference pad set (exterior face, centred, symmetric positions):**
  - X1 GND, X2 +12V, X3 GND, X4 CANH, X5 CANL, X6 DRIVE, X7 SENSE_EDGE, X8 SPARE, X9 +12V, X10 GND.
  - DRIVE and SENSE_EDGE were swapped from the first draft during footprint implementation. A DRIVE↔12 V short burns R11 and back-feeds 3V3, and SPARE may become the 12 V LED rail, so DRIVE must not neighbour SPARE or +12V. SENSE_EDGE is protected by D1.
  - Pads are ≈3.0 mm wide at ≈5.0 mm pitch (≈48 mm span), so a 1.5 mm spring has about ±0.7 mm lateral tolerance.
  - The bridge routes nets with its own traces, so the order is flexible. Keep GND outermost and keep the positions symmetric about the centre so spring forces balance across the bridge.
- **Mating order kept:** pads start 0.3 mm (GND), 0.6 mm (+12V) and 0.9 mm (signals) from the wall edge. The panel slides toward the wall, so GND touches its springs first.
- **Spring:** BW0019CG-L3.5W1.5H4.3 (C2826517), with BW0019BG-L3.5W1.5H3.8 (C2826516) as alternate.
  - 10 per board, 20 per bridge, mounted with the cantilever's free end pointing toward the wall. The bevelled board edge then rides up the spring's ramp instead of snagging it.
  - **Not yet confirmed from the datasheet:** current rating, working height and contact force. They must be measured on the prototype.
  - Until then, assume ≈1 A per spring. Springs are $0.02 each, so if more current capacity is needed, add power springs and pads rather than change the part.
- **Bridge routing and variants (unchanged):** SENSE_EDGE ↔ DRIVE cross-connect on the bridge, a 180° symmetric layout, and the standard / injection / isolating variants.
- **Cluster controller:** attaches to a free outer edge with a one-sided version of the same spring row.

## Consequences

**Cost:**
- Bridge ≈$0.70–1.20: 20 × $0.024 = $0.48, plus a small 2-layer PCB, double-sided assembly and the printed carrier.
- Per hexagon (1.5–2.5 bridges): ≈$1.05–3.00, down from $5.10–17.90.
- Hexagon total: ≈$7–16, down from ≈$11–31.

**Seam:** ≈6–8 mm (bridge PCB + 2 compressed spring heights), down from ≈10–11 mm.

**Edge board:**
- Contact footprint changes: all pads on B.Cu, none on F.Cu.
- Signal-to-pad vias are needed, and the exterior power planes need keep-outs around the signal pads.
- The schematic nets and pins are unchanged.

**Forces:**
- The springs push the two panels apart instead of pinching one board. A board sees about 10 × the spring force (≈0.5–1.5 N each, to be measured) toward its panel's interior.
- The panel frame and snap fit must take this. Inside a tiled cluster the forces mostly cancel; at cluster edges they don't.

**Risks to prototype:**
- Spring snagging during insertion (orientation, bevel, lead-in).
- Contact resistance and current per spring.
- Seam width.
- Carrier retention, and tolerance to a few mm of wall unevenness.

**Fallback:** the V5.1 flat bridge with Harwin S1961-46R side springs (decision 0001) still works electrically, at the higher cost.
