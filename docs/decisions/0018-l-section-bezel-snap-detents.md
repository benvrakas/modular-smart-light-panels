# 0018 — L-section bezel held by snap detents

**Date:** 2026-11-22 · **Status:** Accepted (user) · **Relates to:** [0014](0014-rigid-snap-bridge-clip.md) (film clamped between frame cap and bezel, no riser), [0013](0013-dual-lock-mounting-fdm-rules.md) (FDM rules)

## Context

A test print of the flat bezel bowed: a thin plate around the panel's outer edge has little stiffness. It was located and held by corner pins in holes in the frame cap.

## Decision

- **L-section bezel:** a flange 1 mm thick and 3 mm deep runs down the bezel's outer edge and sits flush in a step cut into the frame's outer top edge (step width = flange + 0.15 mm). The step floor slopes at 20° from horizontal, so the frame still prints cap-down within the 70° overhang limit. The film stops 1.5 mm inside the outer edge, inside the flange.
- **Snap detents instead of pins:** one bump per side, at mid-side on the flange's inner face, snaps into a matching dimple in the frame's step wall. PETG's flex is enough, so there are no pins or snap arms. Both faces are 45°, so the bezel snaps on and pulls off, and both parts print without support.
- **Detent size (user, 2026-11-22):** 0.6 mm engagement (bump 0.75 mm proud including the 0.15 mm fit gap, 0.3 mm flat top, 10 mm long, spanning 0.2–2.0 mm of the flange's depth). The first 0.3 mm was too small, and a trial at 1.0 mm was too big. The dimple is 0.7 mm deep (0.1 mm clearance); the thinnest wall behind it is about 1.3 mm.

## Consequences

- To pass a bump, the flange bends out by the engagement. Treating the flange as a simple cantilever, 0.6 mm gives about 10 % strain, above PETG's ≈4–5 % yield. In practice the bezel plate twists and the flange spreads the bend along the side, so the real strain is lower, but the test print must confirm that the flange snaps on without whitening or cracking. If it doesn't, reduce `det_h`, or deepen the flange (`fl_h`): strain falls with the square of the depth.
- The pin holes in the frame cap are gone, and so are the pin parameters.
- Tuning knobs: `det_h`, `det_len`, `det_zc` (in both `frame.sc` and `diffuser.sc`, set together by `mechanical/solidcraft/gen_frame_bezel.py`).
