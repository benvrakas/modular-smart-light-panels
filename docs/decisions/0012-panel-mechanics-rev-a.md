# 0012 — Panel mechanics, rev A: floating bridge carrier, wall pucks, film clamp

**Date:** 2026-11-21 · **Note:** the bridge carrier is superseded by [decision 0014](0014-rigid-snap-bridge-clip.md) (rigid snap clip); the wall puck is superseded by [decision 0013](0013-dual-lock-mounting-fdm-rules.md) (Dual Lock mounting). · **Status:** **Accepted by the coordinator** under the user's delegation to coordinate prototype work. The user may override. · **Proposed by:** the mechanics agent (`mechanical/archive/openscad-panel/MECH-NOTES.md` §3–§4) · **Changes:** SPEC §1 (Bridge), §2, §3.3, §9, §10 item 17

## Context

Work package 1.6 modelled the rev A hexagon panel in OpenSCAD (`mechanical/archive/openscad-panel/`), using the controller layout (finished) and the in-progress edge-board layout. SPEC V6.3 had said the bridge carrier anchors to the wall and the panels' snap fits locate on it.

## Decision

- **The bridge carrier is captive with float** (updated 2026-11-21 at the user's request). A **slightly loose snap fit** retains it, so it can't fall out while one side (or both) has no panel yet, for example during assembly or on a free cluster edge. The snap leaves ≈0.3–0.5 mm of play, so the balanced springs still centre it once both panels are on.
  - **Original rev A model (superseded by the line above):** the carrier floated freely.
  - It is trapped between the wall and the two panels' board edges, and centred by the balanced springs on its two faces.
  - **Why:** a wall-anchored carrier plus wall-anchored panels over-constrain the seam. A carrier that also holds both panels against separation would need an undercut on the panel, and that can't fit in a 3.5 mm half-seam without crossing the board.
- **Each panel snaps onto its own wall puck.**
  - The puck is a screwed bar with two split-tube snap posts. It locates the panel and takes the springs' push-apart force.
  - The panel stands **3.0 mm off the wall**, which leaves room for the carrier base under the board edges.
  - The puck screws go in through two Ø8 mm access holes in the back plate, which are closed with printed white plugs afterwards.
- **Diffuser film is clamped**, not held in a groove.
  - It sits flat between the frame cap (or a riser ring) and a bezel ring registered on corner pins. The film corners are cut off, so it needs no holes.
  - ~~Rev A risers are 0/3/6/10 mm~~ — **Superseded (2026-11-21, decision 0014):** no riser; the bezel clamps the film straight onto the frame cap.
- **Frame:**
  - The board top edges sit in a groove in a printed crown.
  - The corners are open below the 2 mm cap, so the corner joints are soldered with the boards already in the frame (the frame is the soldering jig). **Superseded (2026-11-21, decision 0014):** corners closed; the ring is soldered before it goes into the frame.
  - 12 snap legs sit in the seam band.
- **Controller pocket:** the rev A back plate meets the stepped-pocket rule (SPEC §3.5) by leaving the pocket open through to the wall. This gives wall-side access for the test jig and the joint iron.
- **Coordinator rulings on the open questions:**
  1. ~~**A carrier on a free cluster edge** gets a screw-tab variant~~ — **Superseded (2026-11-21):** the loose snap retention covers free edges too.
  2. **Plugged puck-access holes in the reflector are accepted for rev A.** The optics test will show whether they're visible. The fallback is a printed spacing gauge so the pucks go on before the panels.
  3. **Back-plate insertion force** (≈90 N with all 12 barbs engaging at once) is tuned after a test print.

## Consequences

- **Panel depth** from the wall to the bezel top is ≈20.9 mm with no riser.
- **Edge-board keep-outs** (reserved for the reasons given, not forbidden otherwise):
  - exterior face z 0–7.5 at |x| 30–36.5 (snap legs)
  - inward face z ≥ 12.8 (frame lip)
  - inward face below z 6.6 flat copper only (it bears on the back-plate rim)
  - nothing below the wall edge at |x| 30.4–36.1
- **Bridge envelope:** top ≤ z 7.0, |x| ≤ 28, nothing on its faces below z 2.2, spring contact ≤ z 5.0. The carrier is regenerated once the bridge is laid out.
- **Code-0 board:** the spring push there (|x| < 37) is carried by the controller's base edge (0.2 mm gap) and the back plate. The controller joint is still not loaded in tension.
- **Assembly:** one puck per panel, positioned using the neighbours already mounted.
- **Status:** the square and triangle variants are generated from the same parameters but not checked yet. The triangle needs a shorter, offset puck.
