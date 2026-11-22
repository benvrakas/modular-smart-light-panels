# 0013 — Wall mounting by Dual Lock; flush bridge carrier; FDM design rules

**Date:** 2026-11-21 · **Status:** **Accepted**: proposed by the user as an option, recommended by the coordinator. · **Supersedes:** the wall-puck parts of [decision 0012](0012-panel-mechanics-rev-a.md) · **Changes:** SPEC §1 (Bridge), §3.3, §9

## Context

Decision 0012 mounted each panel on a screwed wall puck with two split-tube snap posts. Its screws went in through two Ø8 mm access holes in the back plate, which were then plugged.

The user raised three points:
- **Triangle:** the centre of a triangle is much closer to the controller board, so the puck's snap holes compete with the controller pocket.
- **Carrier:** the bridge carrier's wall side should be flush with the panels' wall side.
- **Alternative:** mount the panels with a reclosable interlocking fastener (3M Dual Lock) instead.

## Decision

- **Wall mounting: 3M Dual Lock pads on the back plate's wall face.**
  - **What it is:** interlocking mushroom-head stems on both halves, reclosable and much stronger than hook-and-loop.
  - **Mating:** one half stays on the wall and the other on the panel.
  - **Placement:** pads sit clear of the controller pocket on every shape.
  - **Removed:** the wall puck, its snap posts and the plugged screw-access holes in the reflector.
  - **Why:**
    - No snap holes compete with the triangle's controller.
    - No holes in the reflector.
    - No screws in the wall, and it works on ceilings.
    - It is simpler to print.
  - **Holding force:** a seam's springs push each panel sideways with only about 10 × 0.7 N ≈ 7 N, against well over 100 N of shear capacity from a few pads.
- **Panel spacing:** the tape doesn't locate the panels. A printed **spacing gauge** sets the seam width (SPEC item 18) while each panel is pressed on, and the bridge springs then centre the carriers.
- **Bridge carrier:**
  - **Not tied to the wall:** with no wall-side panel hardware, its depth toward the wall is a free design choice. Being flush with the panels' wall side was asked for only together with the wall mount (user clarification, 2026-11-21).
  - **Captive:** it stays captive with float (decision 0012, as updated): a slightly loose snap onto the panel it is first fitted to holds it, and the springs centre it.
- **FDM design rules for every printed part (user, 2026-11-21):**
  - **Snap lips:** where a part uses round or split snap posts (none in the current design, now that the wall mount is gone), the lips are **ovalized**. The lip protrudes only in the direction the split lets it flex, so nothing overhangs in the direction it can't compress.
  - **Fasteners:**
    - **Glue and metric M2/M3 screws** are allowed.
    - Screws **thread straight into the plastic** through a pilot hole with a **tapered entry**, so no heat-set inserts.
    - Starting pilot sizes in PETG: M2 ≈ Ø1.7 mm, M3 ≈ Ø2.6 mm. Tune these on a test print.
  - **Overhangs (user, 2026-11-21):**
    - Up to **65° from vertical** (faces at least 25° from horizontal) prints cleanly: use 65° wherever the geometry allows (user, 2026-11-22).
    - **70°** (20° from horizontal) also prints without support, but the lines sag slightly: only where 65° doesn't fit.
    - Steeper overhangs are allowed only if the support stands on the **print bed**.
    - No support may be trapped between a top surface of the part and a horizontal bottom surface of the same part above it.
  - **General:**
    - Every part is designed for printing: no supports where avoidable and a sensible print orientation.
    - **Walls:** at least **0.75 mm** measured across the layers, in the print's XY plane: two lines of the 0.4 mm nozzle (user, 2026-11-21; was 1.2). A thickness built up in layers (along the print's Z) can go down to about **0.5 mm**, slightly under-extruded (user, 2026-11-22).
    - **Fits, gap per side (user, 2026-11-21):**
      - **tight fit 0.08–0.1 mm** (for example the bridge-clip keys in their grooves, and the bridge PCB in its slot)
      - **loose fit 0.15–0.2 mm** (sliding or easily removable parts)
    - Snap strain stays within PETG's limits.

## Consequences

- **Panel depth:** it now depends on the engaged Dual Lock thickness (≈4–6 mm, depending on the type). It is set in params.scad once a type is chosen.
- **Shopping list:** add Dual Lock (for example SJ3550 or a low-profile type) to the P0 list.
- **Removing a panel:** pull it straight off the wall. The captive carriers come with their panel, and the springs slide off the neighbours' pads.
- **Fallback:** the wall puck from decision 0012 stays in `mechanical/archive/openscad-panel/` as an option, not used by default.
