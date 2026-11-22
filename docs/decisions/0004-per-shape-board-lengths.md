# 0004 — Fixed seam inset, edge-board length per polygon shape

**Date:** 2026-11-15 · **Status:** Accepted · **Relates to:** [0002](0002-seam-bridge-cheap-springs.md) (seam bridge)

## Context

The seam bridge (0002) works only if the gap between the two facing edge boards is fixed: bridge PCB plus two compressed springs, ≈6–8 mm. Every panel's edge boards must therefore sit at the **same inset** from the shared edge line, whatever the panel's shape. That is also what lets any two shapes mate with the same spring pressure.

Insetting a regular polygon's sides by a fixed distance shortens each side by an amount that depends on the corner angle: sharp corners lose much more than wide ones. With a fixed inset, a board's length therefore **cannot be the same for triangles, squares and hexagons**.

Options considered:
1. **A different board length per shape (chosen).**
2. **Identical boards with a gap bridged by hand-soldered wire.**
   - Rejected: 4–6 mm gaps per corner on hexagons and 2–4 mm on squares (boards sized for the triangle).
   - 8 hand-wired nets × every corner, which breaks the no-hand-placed-parts rule.
   - LEDs pushed away from the corners, plus light leaks.
3. **Contacts with enough travel or sideways range to absorb a per-shape inset.**
   - Rejected, user's point: the bridges would then have to differ depending on which shapes they join.
   - Long-travel contacts also give uneven pressure.

## Decision

- **Edge length L** (≈100 mm) is measured on the **seam centrelines**, the lines along which the panels tile. Every shape uses the same L, so all shapes still mate.
- **Fixed inset:** every board's exterior face sits **d = seam/2** from the seam centreline. This is the same for every shape and every edge. d is a design parameter set by the measured spring stack; ≈3.5 mm is assumed until the bridge prototype.
- **Board length per shape**, measured along the inward face. The ends are square-cut so neighbouring boards' inward faces meet exactly at each corner:

  **L_board = L − 2·(d + t) / tan(α/2)**, where t = board thickness (1.6 mm) and α = the polygon's corner angle.

  | Shape | α | L_board (L = 100, d = 3.5, t = 1.6) | Outside V-gap at corner ≈ 2·t·sin((180°−α)/2) |
  |---|---|---|---|
  | Hexagon | 120° | **≈ 94.1 mm** | ≈ 1.6 mm |
  | Square | 90° | **≈ 89.8 mm** | ≈ 2.3 mm |
  | Triangle | 60° | **≈ 82.3 mm** | ≈ 2.8 mm |

  The small outside V-gap is what the existing corner strap / solder bridge already spans (SPEC §3.4).
- **One schematic, one shared layout core, three outlines:**
  - The edge contact strip, LEDs, MCU section, ID resistor + diode and level shifter are placed **relative to the board centre**, within the shortest (triangle) length minus the corner-joint footprints.
  - The longer variants only extend the board ends: power-plane copper and a few traces out to the corner joints (`CornerJoint_L`/`_R` move with the ends).
- **Bridges stay universal.** On a regular polygon, the midpoint of each inset side lies on the midpoint of its seam line. A centred contact strip therefore lines up with the neighbour's strip for every shape pair (triangle–hexagon included).
- **Fabrication:** one panelized kit per shape (hexagon kit codes 0–5, square kit codes 0–3, triangle kit codes 0–2), all machine-assembled. The printed frames were already shape-specific.
- **Hexagon first:** rev A builds and proves the hexagon variant only. The square and triangle outlines are derived later from the same core.

## Consequences

- **The layout core must fit the triangle length.** About 82 mm minus the two corner joints is available for the 48 mm contact strip (exterior face) and, on the inward face, the LEDs plus the MCU section on active boards.
- **LED positions:** fixed relative to the centre, so the distance from the outer LEDs to the corner varies by shape. Corner brightness uniformity differs slightly per shape; check it in the optics test.
- **Final lengths:** recalculate the lengths when d is measured. The formula, not the numbers in the table, is the requirement.
- **Cost:** no BOM change. Three PCB designs instead of one (setup cost only).
