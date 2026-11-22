# Rev A panel mechanics (SolidCraft)

**First pass, 2026-11-21.** These parts implement decisions 0012–0014 and `docs/mechanical/assembly-plan.md`.

- **Editing:** open any `.sc` file in SolidCraft. Every size is a named, commented parameter (Parameters panel), so edit those rather than the geometry.
- **Shapes:** `back_plate.sc`, `frame.sc` and `diffuser.sc` (bezel) are parametric in `n_sides`. Each has **Hexagon / Square / Triangle** configurations (Config Table); the files are saved with **Triangle** active, the rev A test model (decision 0016). The clip and the edge cover are universal.
- **How the outlines follow `n_sides`:** each outline is drawn directly, one side at a time, and patterned `n_sides` times: a centre sector or a mitred ring segment per side (angles use `180 deg/n_sides`), with per-side features drawn once at side 0. The back plate's core sector and tab band end on the corner-relief chamfer (`relief_x`, `rc`), so there is no blank and no edge or corner trim. Every sketch and extent ends exactly on the face it meets: cuts start on their face and stop on the far face or go through-all, joins start on the face they attach to (CLAUDE.md exact-references rule). Left/right and front/back features are modelled once and mirrored (snap legs, corner reliefs, tooth notches, hook pockets, arm slots, teeth, keys, springs), the clip's fuse relief is rotated 180�, and the stand-in's LEDs are a linear pattern (CLAUDE.md symmetry rule). The build scripts are kept here (`gen_back_plate.py`, `gen_frame_bezel.py`, `gen_clip_cover.py`, `gen_assembly.py`), write SolidCraft batch JSON and run through `solidcraft-cli run`; each reads the current file and deletes its features first, so a rebuild works from any state. A rebuild that only restructures must keep every configuration's volume and bounding box.
- **Exports:** per shape, `stl/<part>_<shape>.stl` (finest mesh) and `step/<part>_<shape>.step`; the universal parts as `stl/bridge_clip.stl` and `stl/edge_cover.stl`.
- **Coordinates (panel z):** z = 0 is the edge boards' wall edge, and +z points toward the diffuser. Side 0 (the controller side) faces −Y. The clip and the edge cover use seam coordinates: the seam is at y = 0.

## Parts

| File | Part | Print orientation | Notes |
|---|---|---|---|
| `back_plate.sc` | Back plate | Floor down (the floor face is the chamber reflector) | See below |
| `frame.sc` | Frame (crown) | Cap down | See below |
| `bridge_clip.sc` | Bridge clip, universal 59 × 20 mm | Bottom down | See below |
| `edge_cover.sc` | Edge cover for free cluster edges | Bottom down | See below |
| `diffuser.sc` | Bezel | Upside down: flange up, bezel face on the bed | See below |
| `edge_board_standin.sc` | Printable stand-in edge board (fit tests): board block with the LED and part envelopes; Triangle / Square / Hexagon configurations, `stl/edge_board_standin_<shape>.stl` | Exterior (flat) face down | Envelopes only, no copper. R3 is the 0402 at z 7.2 (V6.9.2), so nothing sticks out below z 6.8 |
| `bridge_standin.sc` | Printable stand-in seam bridge (fit tests): 56 × 9 × 0.8 board, panel z −2…7; `stl/bridge_standin_board.stl` (board only) and `stl/bridge_standin_springs.stl` (+ 20 spring envelopes, x ±2.5…±22.5 on both faces, z 2.6–6.1) | Board: flat. With springs: upside down, top edge on the bed (the envelopes' 20° faces are then the overhangs); add a brim | Springs are rigid envelopes 2.9 mm high, 0.2 short of the pads at d 3.5, so they show position without jamming the seam. Standard bridge (no F1, no wire pads) |
| `panel_assembly.sc` | Mixed cluster: hexagons A and B (controller sides facing), a square on A, triangle T1 on A, and T2 on T1 (controller sides facing). 22 edge boards, 5 controllers, 4 bridges and 4 clips; bezels on B, S and T2 | — | The printed parts are linked to their files in the matching configuration. The boards are the full rev A STEP models with copper, from `boards/with-copper/` (user, 2026-11-21; the pads may z-fight slightly with the board face in the viewport). Copper-free copies stay in `boards/` (`gen_assembly.py --no-copper`). The assembly also carries white printed parts and bezels with film on every panel. Renders and animations are done in Blender (`render/`). Built by `gen_assembly.py` (panel centres, rotations and seams) |

### Back plate

- **Shape:** a 2 mm floor (z 4.6–6.6) with an 8 mm rim, and a seat under the boards. The seat slopes at 20° (`seat_ch`, the shallowest the overhang rule allows) from the plate edge through the board's inner bottom corner, so the boards sit at z 0, nothing flat faces the bed when printing floor-down, and the tab keeps enough material for the frame hooks (user, 2026-11-21).
- **Flat back (user, 2026-11-21):** the rim, tabs, bosses and cross-bar all come down to z −4.3, flush with the clip bottom.
- **Controller pocket:** open through to the wall, with a cross-bar (its underside bridges the pocket, accepted by the user). The 4 support ledges were removed (user, 2026-11-21: unprintable overhangs).
- **Per side:**
  - a **clip recess** in the underside, with the key groove (tight fit) in its ceiling
  - two **tooth notches** in the recess wall, which replace the separate lugs
  - two **hook pockets** for the frame legs. Their ceiling is the latch plane `latch_z` (z −2.3) under the board tab; they reach 4.95 mm from the seam (`hook_s1`). The ledge over the hooks is about 1.75 mm thick.
- **Plate edge:** plain up to z 6.6. The boards' inward face carries no parts below z 6.8 (decision 0015), because the soldered board ring is lowered into the plate along z. The V6.9 R3 groove is gone (user, 2026-11-21: it made insertion impossible).
- **Back:** Dual Lock bosses (`boss_n`, `boss_a0`, `pad_r`, `pad_size`, set per configuration): hexagon 3 × 25 mm at r 40; square 3 × 25 mm at r 20, the same size as the hexagon's (user, 2026-11-21): the two rotated bosses reach into the controller pocket, and a Square-only cut (`Boss trim`, a configuration-suppressed feature) removes just that part through the full height, so nothing overhangs; triangle 1 × 15 mm at r 10.
- **Cross-bar:** spans the controller pocket between its side walls, from the plate edge (`bar_s0`, also the pocket's outer edge) to `bar_s1`, so no strip of rim floor hangs exposed between them.

### Frame

- **Board groove:** the cap, the inward lip and the exterior walls form it, at a tight fit.
- **Corners:** closed (user, 2026-11-21). The wall, the groove and the lip run all the way round. The board ring is soldered **before** it goes into the frame. An L-shaped relief, 1.2 mm deep, in the wall's inner face around each corner (the last 3.5 mm of each board, z 7.5–12.9) clears the solder on the corner power pads.
- **Inner lip:** one mitred segment per side, so it closes into a ring at any corner angle.
- **Snap legs:** 2 per side. The hooks reach **1.2 mm** under the back-plate tab (`hook_tip`), latching on the plane `latch_z` (z −2.3) with a 25° latch face and a 35° lead-in (`lead_slope`); the legs end at z −4.16, above the back plane (`leg_bot` follows from these). Section: `png/section_seam_hook.png`.
- **Flange step:** a step cut into the outer top edge for the bezel's flange (`rebate_w` = flange + 0.15 mm, down to `rebate_bot` = 3 mm below the cap top). Its floor slopes at 20° from horizontal (`rebate_slope`): the 70° overhang limit, since the frame prints cap-down (user, 2026-11-22). One detent dimple per side at mid-side (`det_*`, 45° faces).
- **Corner solder reliefs:** one mitred cut per side, ending on the corner bisector, so neighbouring reliefs meet exactly at any corner angle (straight boxes crossed at the triangle's 60° corners).

### Bridge clip

- **Bridge slot:** tight fit.
- **Base:** 3.0 mm (`clip_t`; z −4.3 to `z_back` −1.3). It was 3.5; the height went into the keys (user, 2026-11-21). The back-plate tab over the recess is now 0.75 mm.
- **Keys:** 2 straight-sided keys up to `key_top` z 1.2 with a 0.3 mm top chamfer: 2.5 mm in the groove, 2.2 mm of straight wall (was 1.5 / 0.7). The back-plate grooves have square mouths (chamfer the key or the groove, not both: user).
- **Fuse reliefs:** 2 channels in the spine (one per face, opposite ends) clear fuse F1, so the bridge fits either way round. They run from just below the fuse up through the spine top, so the fuse slides down into place as the bridge goes into the slot (user, 2026-11-21: a closed pocket blocked insertion). The spine is 3.9 mm wide, keeping a 0.75 mm wall.
- **Corners:** square (user, 2026-11-21: no rounding needed; the recess corners are square too).
- **Snap arms:** 4 in-plane arms, 1.8 mm wide × 15.5 mm long (`arm_w`, `arm_root_x` 14; user, 2026-11-21: thicker and shorter, about 3× stiffer than 1.5 × 17.5, 1.8 % peak strain when snapping). The edge cover's two arms match. Their teeth have **two obtuse faces**: a 60° lead-in and a 45° latch, so the clip snaps in and pulls back out (user). Teeth 0.7 mm (`tooth_h`) at z −3.7…−1.6, to fit the thinner base.

### Edge cover

- Half a clip (one key, two obtuse teeth), plus a wall that covers the exposed contact pads. It sits in the same recess as a clip and follows the clip's base, key and tooth numbers. Square corners, like the clip.

### Bezel

- **Ring:** matches the frame cap.
- **Flange (L-section):** 1 mm × 3 mm (`fl_t`, `fl_h`) down the outer edge, flush with the frame's outer face in its step. It stiffens the 2 mm bezel, which bowed on the first test print (user, 2026-11-22).
- **Detents:** one bump per side on the flange's inner face (0.45 mm, 10 mm long, 45° faces) snaps into the frame's dimple; PETG flexes enough, so no pins or arms.
- **Film:** clamped between the frame cap and the bezel. Modelled in `diffuser.sc` as a second body `Film` (0.2 mm, `film_inset` 1.5 mm inside the outer edge so it ends inside the flange; no pin holes), shown semi-transparent; per-shape outlines in `step/film_<shape>.step`. The bezel STL/STEP exports contain the bezel only.
- **No riser** (user, 2026-11-21). The frame's cap and exterior wall are one continuous part.

## Rules used

From decision 0013:
- **Overhangs:** up to 70°; steeper only with support standing on the bed. Every latch face is printable (the teeth's 45° latch, and the frame hooks at 25°).
- **Walls:** at least 0.75 mm.
- **Fit gap per side:** tight 0.09 mm, loose 0.15 mm.

## Checks done

- **Volumes:** every feature matches a volume computed by hand beforehand, within 0.01%.
- **Interference:** the two-panel assembly, with both controller sides facing across the seam, shows no interference.
- **Volume:** prints are mostly hollow, so volume is used only to verify geometry, not to save material.
- **Engagement:** a test clip shifted 0.2 mm across the seam hits the recess wall and the key groove, so it is held across the seam by solid walls.
- **Retention:** a test clip pulled 0.3 mm off the back meets only the 45° latch faces of the teeth, so it is retained, and a firm pull releases it.
- **Sections:** `png/section_seam_spring.png`, `png/section_seam_tooth.png` and `png/section_seam_hook.png` cut across the A–B seam of the assembly (made by `docs/figures/snap_cad.py` with solidcraft-cli).
- **Real boards (2026-11-21):** the rev A KiCad STEP models are placed in `panel_assembly.sc`, with copper (`png/assembly_front.png`, `png/assembly_back.png`).
  - **Mixed cluster:** across 3,242 bodies there is **no interference between parts**. The only overlaps left are inside the controller and bridge STEP models themselves (component models touching their own pads).
  - **Clashes found and fixed:** fuse F1 against the clip spine (fuse reliefs); square and triangle C1/C3/R3 against the back-plate wall and the controller (parts moved above z 6.8).
  - **V6.9.2 recheck (676 bodies):** new board STEPs (R3 at z 7.2, longer J4 pads), new clips and back plates: no interference between parts; the only overlaps are inside the controller STEP (its SOT-89 model).
  - **STEP thickness:** the boards are 1.51 mm thick (KiCad's stack-up) against 1.6 mm in the CAD. Faces are about 0.09 mm off; harmless.

## Open items

1. **Real boards:**
   - Board STEPs re-exported for V6.9.2 (J4 pads, R3) and placed in the assembly.
   - **Bridge springs:** modelled (`hardware/lib/3dmodels/Spring_BW0019CG.step`, from drawing 681-0019C-3, at the 3.05 mm installed height) and on the footprint. In the assembly all 80 contact their edge-board pads at z ≈ 3.66, overlapping only the 0.035 mm pad copper.
   - **Not checked yet, no 3D models:** the controller's F1 (1812 PTC) and U5 (buck converter).
2. **Injection supply wires:** no grooves needed (user, 2026-11-21). From the bridge's wire pads (x ±26.4, z 4) the wires run sideways along the seam gap past the clip ends (|x| > 29.5), then straight down the middle of the seam (4.2 mm clear between the two panels' snap legs) to the wall. The fuse relief is done.
3. **Controller retention:** with the ledges gone, the controller hangs on its J4 solder joint to the code-0 edge board; the cross-bar sits 2.8 mm below it. If it needs support, add glue dabs or printable (sloped) supports in the free stretches of its edges.
4. **Other shapes:** done (configurations). The triangle is the test model; check a hexagon once before releasing it (optics, widest LED pitch).
5. **Test print:**
   - Tune the snap interference (`tooth_h`, `latch_slope`, the hook overlap) and the tight fits.
   - Check the 0.3 mm gap between the cross-bar and the SMA diode D5.
6. **Debug access:** the cross-bar covers the controller's debug test pads. Flash the controller with the pogo jig before the back plate goes on; after that, update over CAN.
7. **Film template:** regenerate the cut template from `step/film_<shape>.step` (1.5 mm inset, plain polygon, no pin holes).
8. **Clip snap force:** arms now 1.8 × 15.5 mm (about 3× the stiffness of the first arms), teeth 0.7 mm; check insertion force and retention on the test print (`arm_w`, `arm_root_x`, `tooth_h`).
9. **Bezel detents:** tune `det_h` and `det_len` on the test print (snap force vs. removal).
