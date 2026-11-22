# Panel and cluster assembly plan (rev A)

**Status:** planned and accepted (2026-11-21, [decision 0014](../decisions/0014-rigid-snap-bridge-clip.md)). Not modelled yet. **Pictures:** the CAD views and cross-sections in [docs/figures/](../figures/) (generated from the SolidCraft files). **CAD:** SolidCraft, `mechanical/solidcraft/`.

## Height stack

z is in mm from the edge boards' wall edge.

| z | What |
|---|---|
| −4.3 | Back of the panel: bottoms of the clips and lugs. Dual Lock pads stick here. |
| −2.0 → 7.0 | Bridge PCB, standing in the seam |
| −0.8 | Back-plate underside; the top face of the clip |
| 0 → 13.5 | Edge boards (a soldered ring of six) |
| 3.5 | Spring contact point on the pads (no vias below 5.3) |
| 5.0 → 6.6 | Controller board, its top flush with the floor |
| 6.6 | Chamber floor (back-plate top) |
| 7.4 → 12.2 | LEDs |
| 12.8 → 15.65 | Frame lip and groove, then the 2 mm cap. The film sits on top, clamped by the bezel (no riser). |

## Parts

- **Per panel:**
  - 6 edge boards
  - 1 controller
  - frame (crown, with 12 snap legs in the seam band at |x| 30–36.5)
  - back plate (with lugs, plus a cross-bar on the controller side)
  - diffuser film and bezel (no riser)
- **Per seam:** 1 bridge PCB and 1 bridge clip.
- **Per free edge:** 1 edge cover.

## Load paths

- **Inside a panel:**
  - **Vertical:** the boards are held between the frame groove at the top and the back-plate tabs at the bottom.
  - **Sideways:** the back plate's edge and the frame lip locate them.
  - **Closing the panel:** the back plate snaps into the frame's legs.
- **Panel to panel:**
  - **Keys:** straight-sided keys with a chamfered top sit in grooves in both back plates. They carry the pull between panels in pure shear and set the seam width. They are not tapered, so a pull never pushes the clip off, even with only one panel connected.
  - **Snaps:** the clip's four in-plane snap arms put teeth into lug windows only to keep the clip on. Their latch faces slope about 25° so they print without trapped support. Zero play comes from a tight key-in-groove fit (0.08–0.1 mm gap per side), tuned on a test print.
  - **Springs:** they only make contact.
- **To the wall:** Dual Lock pads on some panels' backs.

## Interface rules for the clip (universal across shapes)

- **Clip:** about 59 × 20 mm on a 3.0 mm base (z −4.3 to −1.3; was 3.5, user 2026-11-21: the height went into the keys). The spine holds the 56 mm bridge in a slot that is 0.8 mm plus a small clearance.
- **Keys:** straight-sided ribs, 2.0 mm wide at 6.4–8.4 mm from the seam, |x| ≤ 11, rising to z 1.2 with a 0.3 mm chamfer at the top, into square-mouthed back-plate grooves: 2.5 mm of engagement, 2.2 mm of it straight wall (user 2026-11-21: chamfer the key or the groove, not both).
- **Printing:** overhangs up to 70°, steeper only with bed-standing support, never support trapped inside the part. Walls ≥ 0.75 mm. Fit gaps per side: tight 0.08–0.1 mm, loose 0.15–0.2 mm (decision 0013). The back plate prints floor-down; the clip prints bottom-down.
- **Recess and notches (replace the lugs, user 2026-11-21):** the back plate comes down to z −4.3, flush with the clip bottom. The clip sits in a recess (|x| ≤ 29.65, up to 10.15 mm from the seam). Its teeth snap into notches in the recess wall at |x| 19.85–26.15.
  - The triangle has back plate there: its half-width 11.5 mm from the seam is 30.1 mm.
- **Teeth:** both faces are obtuse, a 60° lead-in and a 45° latch, so the clip snaps in and pulls back out (user). 0.7 mm tall (z −3.7 to −1.6) to fit the thinner base; tune on the test print.
- **Controller side:** the cross-bar spans the open pocket about 5.6–12 mm from the seam, at z −1.3 to 2.2, so it can hold the key groove (0.9 mm of bar above it) and the notches.
  - **Clearances:** the joint is soldered before the back plate goes in, and the L1 window is far away.
  - **To check:** the controller's part heights near its base edge.
- **Clip ends:** they stay inside |x| ≤ 29.5, clear of the frame's snap legs.

## Build order

1. Solder the six edge boards into a ring on a separate jig (roadmap 2.3), then press the ring into the frame. The frame's corners are closed, with reliefs for the corner solder.
2. Solder the controller at 90° to the code-0 board and seat it in the back-plate pocket.
3. Snap the back plate into the frame's legs, then fit the film and the bezel.
4. Lay the panels face down. Set each bridge in its clip and push the clip onto the seam until all four teeth click; GND mates first. Fit edge covers on free edges.
5. Hang the cluster on Dual Lock. To add a panel later, take the cluster down first (accepted).

## Still to design

- **Injection bridge:** fuse relief done; the supply wires run sideways along the seam past the clip ends and down the seam centre to the wall (no grooves, user 2026-11-21).
- **Bridge retention in the slot:** snug fit or glue.
- **Controller retention** in its pocket: the printed ledges were removed (overhangs, user 2026-11-21); the controller hangs on its J4 solder joint. Add glue dabs or sloped supports if the test print shows it needs them.
- **Snap interference:** the arm-to-lug and tooth-to-window interference, tuned after a test print.
- **Jigs:** roadmap 2.3.
