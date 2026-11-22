# 0017 — Panel brightness normalised to the shape with the lowest LED density

**Date:** 2026-11-21 · **Status:** Accepted (user) · **Relates to:** [0015](0015-square-triangle-edge-boards.md) (LED count per shape), SPEC §5 (power, brightness limiting) · **Changes:** SPEC §5

## Context

All three shapes use three LEDs per edge, so they have very different LED densities:

| Shape | LEDs | Area inside the boards | LEDs per m² |
|---|---|---|---|
| Hexagon | 18 | 0.0230 m² | 782 |
| Square | 12 | 0.0081 m² | 1,488 |
| Triangle | 9 | 0.0029 m² | 3,065 |

At the same drive level a triangle would look about four times as bright as a hexagon, so a mixed cluster would never look even.

## Decision

- **Each panel's maximum brightness is normalised to the shape with the lowest LEDs per area**, so every shape reaches the same surface luminance at 100 %. Today that is the hexagon: hexagons run up to full output, squares up to ≈53 %, triangles up to ≈26 % (scale = 782 / the shape's LEDs per m²).
- The firmware applies the scale per panel from its shape (known from the LED loopback count), before effects and before the power-domain current budget (SPEC §5), so effects can treat every panel alike.
- **Estimated maximum** (renders, `mechanical/solidcraft/render/CREDITS.md`): SKC6812RGBW-NW at full RGBW ≈10.7 lm per LED (datasheet Iv, Lambertian); ×18 per hexagon; ≈65 % through the diffuser and chamber (estimate, to be measured in the optics test). That gives ≈4,900 lm/m² leaving the film, ≈1,570 cd/m², on every shape.

## Consequences

- Triangles and squares never use their LEDs' top range, so they run cooler and draw less: a triangle at most ≈0.09 A of LED current at 5 V (≈26 % of 9 × 40 mA), a square ≈0.25 A, a hexagon ≈0.73 A.
- If a later shape or revision has a lower LED density than the hexagon, it becomes the reference and every other shape's scale drops.
- The optics test (roadmap 3.2) should measure the real luminance per shape at the scaled maximum and correct the scales if diffuser efficiency differs by shape.
