# 0014 — Rigid snap-fit bridge clip; panels form one rigid cluster

**Date:** 2026-11-21 · **Status:** **Accepted by the user** (2026-11-21) · **Supersedes:** the captive-with-float carrier in [decision 0012](0012-panel-mechanics-rev-a.md) and [0013](0013-dual-lock-mounting-fdm-rules.md) · **Changes:** SPEC §1 (Bridge), §3.3, §9 · **Plan:** [docs/mechanical/assembly-plan.md](../mechanical/assembly-plan.md)

## Context

The user wants panels joined to each other into one rigid assembly, so that only some panels need to be stuck to the wall. The connection between panels must be solid, very strong and free of play, and it must be a snap fit, as with Nanoleaf's linkers, not screws. Mechanics now move to SolidCraft (`mechanical/solidcraft/`) so that the user can edit the parts in its GUI.

## Decision

- **Bridge clip:** a rigid printed plate across the back of the seam, holding the bridge PCB upright in a close-fitting slot.
  - **Snap arms:** four arms lie in the plate's own plane, two per panel, each cut into a long edge of the plate.
    - **Print orientation:** they are printed flat, so they flex along the layers.
    - **Retention:** a tooth on each arm snaps into a window in a **lug** that hangs from each panel's back plate.
  - **Zero play:** comes from a **tight fit** of the straight-sided keys in their grooves, a 0.08–0.1 mm gap per side (decision 0013), tuned on a test print.
  - **No screws.** To remove a clip, press the teeth in through the lug windows with a small screwdriver.
  - **It sets the seam width exactly.** Its keys carry the loads between panels; the springs only make contact.
- **Correction (2026-11-21, raised by the user): what holds the panels together.** The first version located the panels only through the snap arms. Their preload pushed the panels apart, and a tooth in a through-window does not resist separation, so the panels could slide off. The springs push apart too (≈7 N per panel per seam).
  - **Straight-sided keys take the pull (user, 2026-11-21: vertical sides with a chamfer at the top, not tapered):** two rigid ribs on the clip's top face, one per panel, at |y| ≈ 5.8–7.8 mm from the seam and running along it (|x| ≤ 26), rise to z ≈ 0.7 into matching grooves in each back plate's underside. A chamfer on the key top (and the groove mouth) gives the lead-in. **Why not tapered:** a taper turns any pull between panels into a force that pushes the clip off; with only one panel connected that would make panels tend to pop off. Straight sides carry the pull in pure shear. The groove walls face across the seam, so a panel pulling away loads the key in shear. That is a rigid path with no flexing parts. Same principle as Nanoleaf's linker blade in its slots.
  - **The snaps only keep the clip on:** the arms and teeth carry no sideways load.
  - **Their latch faces slope ≈25° from horizontal**, a 65° overhang, so the back plate (printed floor-down, lugs pointing up) and the clip print without trapped support. The slope also gives a slight upward preload that keeps the clip's top on the back plate.
  - **Controller side:** the cross-bar grows to z −0.8 to ≈2.2 (V6.9.2: −1.3 to 2.2, with the clip base thinned to 3.0 mm and the keys raised to z 1.2) and ≈5.6–12 mm from the seam, so it can hold the key groove. Check it against the controller's part heights near its base edge; the joint is soldered before the back plate goes in.
- **Update (user, 2026-11-21, first CAD pass):**
  - **Flat back:** the panel bottom is flush with the clip bottom (z −4.3).
  - **No separate lugs:** the thin lugs are replaced by notches in the wall of a clip recess in the back plate.
  - **Removable teeth:** both tooth faces are obtuse (60° lead-in, 45° latch), so the clip snaps in and back out instead of locking permanently.
  - **Closed frame corners:** the exterior wall, the board groove and the inward lip run all the way round each corner. The edge-board ring is soldered **before** it goes into the frame, so the frame is no longer the corner-soldering jig (that jig moves to roadmap 2.3). A relief in the wall's inner face around each corner clears the solder on the corner power pads: 0.6 mm deep since V6.9.8 (was 1.2 mm; the user wanted the wall back).
  - **No riser:** the diffuser riser is removed. The bezel clamps the film straight onto the frame cap, and the cap and exterior wall are one continuous part. The optics test can no longer vary the film height with risers; if it shows hot spots, the frame cap gets taller instead.
- **One clip for every shape pair** (so it is universal):
  - **Size:** clip ≈ 59 mm long (it must hold the 56 mm bridge), keys at |x| ≤ 26, lugs at |x| 19–27 and ≤ 11.5 mm from the seam.
  - **Why:** every shape (triangle included) has back plate there: 11.5 mm from the seam a triangle is still 30.1 mm wide on each side of centre.
  - **This replaces** the first SolidCraft pass (88 mm, lugs at |x| 34–44), which works only on a hexagon.
- **Controller side:** the controller pocket is open through to the wall, so on that side the back plate has a **cross-bar** across the bottom of the pocket that carries the key groove and the lugs (size in the correction above).
- **Frame to back plate:** the 12 snap legs in the seam band (|x| 30–36.5) stay. With the clip ending inside |x| ≤ 29.5, they no longer collide with it.
- **Free edges:** an **edge cover** snaps into the same lugs on one panel and closes off the seam band. It covers the exposed contact pads, +24V included, on the outside edges of a cluster.
- **Assembly:**
  - Clusters are assembled face down, off the wall. Each clip, with its bridge, is pushed onto its seam from the back (wall side).
  - The springs wipe the pads from the wall edge, so GND still mates first.
  - The finished cluster is hung with Dual Lock on a few panels (decision 0013).

## Consequences

- **Adding a panel:** you can't add a panel to a cluster that is already on the wall. Take the cluster down, clip the new panel on, and hang it again. **The user accepted this** (2026-11-21).
- **Panel back:** the panel's back plane moves to the bottoms of the clips and lugs (z ≈ −4.3). The Dual Lock pads go on that plane, clear of the lugs and the clips.
- **Superseded:** the spacing gauge and the free-edge screw-tab variant are no longer needed, because the clip sets the spacing.
- **Still to model:**
  - the injection bridge's fuse relief and the supply-wire exit through the clip
  - bridge retention in the slot (snug fit or glue)
