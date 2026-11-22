# 0018 — L-section bezel held by snap detents

**Date:** 2026-11-22 · **Status:** Accepted (user) · **Relates to:** [0014](0014-rigid-snap-bridge-clip.md) (film clamped between frame cap and bezel, no riser), [0013](0013-dual-lock-mounting-fdm-rules.md) (FDM rules)

## Context

A test print of the flat bezel bowed: a thin plate around the panel's outer edge has little stiffness. It was located and held by corner pins in holes in the frame cap.

## Decision

- **L-section bezel with a full-length flange (user, 2026-11-22):** a 1 mm flange runs down the bezel's outer edge over the frame's whole outer wall and ends 0.2 mm above the frame's bottom plane (`fl_gap`; the film clamp sets the bezel's height, not the flange). The frame's outer face is stepped in by the flange + 0.15 mm fit over its full height, so the flange sits flush and the panel's side shows no seam line; the only joint is at the back edge, facing the wall. The flange stiffens the thin bezel and locates it. The film stops 1.5 mm inside the outer edge, inside the flange.
  - **Superseded first version:** a 3 mm flange in a step at the top of the frame, with its floor sloped at 20° for the 70° overhang rule. It left a seam line around the side; the user preferred the full-length flange after trying both, and the 3 mm version and its files were removed.
- **Snap detents instead of pins:** one bump per side, at mid-side on the flange's inner face near its lower end, snaps into a matching dimple in the frame wall. PETG's flex is enough, so there are no pins or snap arms. Both faces are at 65° from the flange face (`det_ang`, 25° from horizontal; user, 2026-11-22: steep for a good snap). That is the safe overhang in both print orientations, and the bezel still pulls off with a firm pull.
- **Detent size (user, 2026-11-22):** 0.6 mm engagement (bump 0.75 mm proud including the 0.15 mm fit gap, 0.3 mm flat top, 10 mm long, spanning 0.2–2.0 mm above the flange end). The first 0.3 mm was too small, and a trial at 1.0 mm was too big. The dimple is 0.7 mm deep (0.1 mm clearance), leaving about 1.3 mm of wall behind it.
- **Corner solder reliefs:** 1.16 mm deep into the wall's inner face (user: room for the solder), which leaves 0.8 mm of wall under the flange there.

## Consequences

- To pass a bump, the flange bends out by the engagement. The bump sits about 7 mm below the flange root, so treating the flange as a simple cantilever, 0.6 mm gives about 2 % strain, well under PETG's ≈4–5 % yield (with the 3 mm flange it was about 10 %).
- The frame wall is 1.96 mm thick over its full height (flange step taken out of the 3.11 mm wall).
- The pin holes in the frame cap are gone, and so are the pin parameters.
- Tuning knobs: `det_h`, `det_len`, `det_zc` (in both `frame.sc` and `diffuser.sc`, set together by `mechanical/solidcraft/gen_frame_bezel.py`), `strap_relief_d` (frame).
