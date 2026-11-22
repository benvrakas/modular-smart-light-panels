# 0016 — Triangle panels are the rev A test model

**Date:** 2026-11-21 · **Status:** Accepted (user) · **Supersedes:** "rev A builds the hexagon only" (SPEC §1 V5.4, decision 0004 build order) · **Relates to:** [0015](0015-square-triangle-edge-boards.md) · **Changes:** SPEC §1 build order, roadmap exit criteria

## Context

The user: during the testing phase, the triangle is the iterative model, because it has the fewest parts and the least 3D printing.

All three shapes now exist:
- **Edge boards:** one KiCad project per outline, built by one script (decision 0015).
- **Printed parts:** the back plate, frame and bezel are one parametric SolidCraft file each, with Hexagon / Square / Triangle configurations. The clip and edge cover are universal.

So switching the test shape costs only a configuration change.

## Decision

- **Rev A iterations are built as triangle panels.** Each panel has 3 edge boards (codes 0–2) and 1 controller board.
  - **Printed parts per panel:** 1 back plate, 1 frame and 1 bezel, from the Triangle configuration, plus clips and edge covers.
  - **The controller board is unchanged.** It was always sized for the triangle.
- **Exit criteria scale with the shape:**
  - each panel lights all 9 LEDs, and the loopback counts 9;
  - discovery, CAN, power injection and synced effects as before, across the test cluster.
- **Hexagon and square follow from the same files once the triangle passes.** The parametric parts and the shared board circuit carry the fixes over.

## Consequences

- **What the triangle does not test:**
  - **Optics:** the widest LED pitch is on the hexagon (31.2 mm against 27.4 mm on the triangle). Optics conclusions from the triangle need one hexagon check before the hexagon is released.
  - **Edge-board layout:** the user chose to keep the three boards as alike as possible (2026-11-21). They now share one layout; only the outer LED x and the end zone move. So the triangle board validates the others' routing, apart from the end-zone spacing.
- **The JLC order (roadmap 2.1) becomes triangle kits** (3 boards per kit) instead of hexagon kits. The bridge count depends on the test cluster's seams.
