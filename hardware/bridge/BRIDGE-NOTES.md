# Seam bridge and spring test coupon: notes (rev A)

**Date:** 2026-11-21 · **Against:** SPEC V6.3 §3.3, §8; decision 0002; MECH-NOTES (panel mechanics) · **Roadmap:** WP 1.5
**Files:** `bridge.kicad_sch/.kicad_pcb` (standard + injection in one PCB), `coupon/spring-coupon.kicad_sch/.kicad_pcb`.
Both are generated: `scripts/gen_bridge_sch.py` writes the schematics, using the project generator's classes; `scripts/build_bridge_pcb.py` and `scripts/build_coupon_pcb.py` write the boards. Re-run them; don't hand-edit.

## 1. Result

| | Bridge | Coupon |
|---|---|---|
| ERC | 0 | 0 |
| DRC (all severities) + parity | 0 / 0 unconnected / 0 parity | 0 / 0 / 0 |
| 180° symmetry check (`scripts/check_symmetry.py`) | every face-A item has its image on face B; only the injection items differ | — |
| Fab (`output/fab/`) | Gerbers + drill zip; `CPL_bridge_standard.csv` (20 springs), `CPL_bridge_injection.csv` (+F1); `BOM_bridge_standard/injection.csv`; renders | Gerbers zip, CPL, BOM (4 springs), renders |

## 2. Bridge: dimensions and mechanical interface (for the printed carrier)

| Item | Value |
|---|---|
| Size | **56.0 (x) × 9.0 (z) × 0.8 mm**, 2-layer, 1 oz, ENIG. |
| Height | **Bottom edge at panel z −2.0, top at panel z 7.0**, centred on the seam (x = 0 at the edge-board centre). |
| x extent | **\|x\| ≤ 28.0**: the frame's snap legs start at \|x\| 30. |
| **Carrier slot zone** | panel z −2.0…2.2 (local 0–4.2): only masked copper (lanes) on both faces, no parts. **Exception: on injection bridges F1 (1206, 0.6 mm tall) sits at x 23.1–26.1, panel z −0.5…1.3 on face A**, so the injection carrier needs a relief there. |
| Springs | Lands at panel z 2.6–4.7, bodies to 6.1 (courtyards 2.35–6.35, all above the slot zone); the root bend is at the top. **Contact point at panel z 3.5** (≤5.0 including tolerances; §4). |
| Over the springs | One 0.25–0.3 mm track at panel z 6.55, under mask. |
| Supply wire pads (injection only) | THT, Ø1.25 mm drill / 2.3 mm pad, for 18 AWG: **J1 +36V IN at (26.4, panel 4.0), J2 GND IN at (−26.4, panel 4.0)**. One wire at each end; they must leave the seam past the bridge ends (\|x\| 28–30) toward the wall, so the injection carrier needs a wire channel at both ends. |
| Carrier holes | None. The carrier grips the bottom 4.2 mm in its slot. The end zones \|x\| 23.5–28 above the slot hold the J1/J2 pads (present on every bridge, used only on injection ones); if the carrier wants locating pegs, they can replace J1/J2 on a standard-only revision. |
| 3D model | `hardware/lib/3dmodels/Spring_BW0019CG.step` (source `Spring_BW0019CG.sc`, SolidCraft): envelope from drawing 681-0019C-3 at the **3.05 mm installed height** (rev A seam), contact dome at the footprint's (0, +0.85). On the library footprint and on all bridge and coupon springs; DRC/parity unchanged (0/0/0). |
| Spring force | 10 springs per face × 0.6–0.8 N ≈ 6–8 N per face, outward on each panel. On the bridge the two faces balance; at a cluster edge only one side has a panel. |
| Insertion direction | Springs mounted with the contact (free) end toward the wall; a panel slides on from above (+z) and rides over each spring from its root bend. |

## 3. Bridge: spring positions and nets

A spring at bridge position x touches panel A's pad at board x, and panel B's pad at −x (B faces the opposite way). Face A = F.Cu, face B = B.Cu, contact points on z_panel 3.5 (footprint origin = spring body centre, 0.85 mm higher).

| x | −22.5 | −17.5 | −12.5 | −7.5 | −2.5 | +2.5 | +7.5 | +12.5 | +17.5 | +22.5 |
|---|---|---|---|---|---|---|---|---|---|---|
| Face A | SA1 GND | SA2 +36V | SA3 GND | SA4 CANH | SA5 CANL | SA6 **DRV_A_SNS_B** | SA7 **SNS_A_DRV_B** | SA8 SPARE | SA9 +36V | SA10 GND |
| Face B | SB10 GND | SB9 +36V | SB8 SPARE | SB7 **DRV_A_SNS_B** | SB6 **SNS_A_DRV_B** | SB5 CANL | SB4 CANH | SB3 GND | SB2 +36V | SB1 GND |

- **SENSE ↔ DRIVE cross:** panel A's DRIVE (X6) is joined to panel B's SENSE_EDGE (X7), and the other way round.
- **180° symmetry:** rotating the bridge about the vertical axis maps face A at x to face B at −x, and the nets map onto themselves, with DRV_A_SNS_B ↔ SNS_A_DRV_B (both are "one panel's DRIVE to the other's SENSE"). The copper is generated that way, so the bridge fits either way round.
- **Routing:**
  - **Bottom (slot) band:** GND lane, panel z −1.25; +36V lane 0.8 mm, z −0.2, on both faces; CANH, z 0.9; SPARE, z 1.8.
  - **Vias:** in the spring gaps for CANL (x 0) and for the cross nets (x ±5).
  - **Over the springs:** SENSE_A/DRIVE_B, and GND from SA3 to SA1.
  - **Ties:** the back-to-back pairs are tied by vias (+36V at ±17.5, GND at ±22.5 and ±24).
- **Adjacency:** the bridge carries no 5 V nets, so the +36V rule is met trivially. +36V sits between GND and the CAN/SPARE tracks.

## 4. Why the contact point is at panel z 3.5 and the strip ends at 6.0

From the BW0019CG drawing (681-0019C-3, `docs/datasheets/springs/BW0019CG.pdf` p. 6):
- **Body:** 3.5 × 1.5 mm. The land is 2.10 × 1.50 mm at the contact end.
- **Contact dome:** 0.90 ± 0.15 mm from that end. The dome radius is ≈0.45 mm, from the 0.9 mm loop.
- **Root bend:** the C-shaped root bend fills the other 1.4 mm.

Mounted contact end toward the wall, the contact sits 0.9 mm above the spring's lower end.

**Tolerance budget** for the contact centre on the panel, worst case, roughly:

| Source | Tolerance |
|---|---|
| Dome position (drawing) | ±0.15 |
| Placement | ±0.1 |
| Bridge in carrier slot | ±0.3 |
| Carrier and panel to the wall | ±0.3 |
| Dome shift as it compresses | ±0.2 |
| **Total** | **≈±1.0 mm** |

The contact patch adds ±0.45 mm.

**Window on the edge board:** signal pads start at z 0.9, and the in-pad vias start at z 5.4. So the patch must stay within z 0.9…5.4, which puts the contact centre within 1.35…4.95.

**Nominal 3.5** leaves −2.15 / +1.45 mm of margin, more than the worst-case ±1.0. **Strip top 6.0** gives the in-pad vias room above the contact (5.4–6.0) without adding height. **Rule:** spring contact incl. tolerances ≤ 5.0 (SPEC 3.3 bridge constraint, replaces 6.8).

## 5. Seam width and the inset d (decision 0004 follow-up)

- **Seam width** = 0.8 (bridge) + 2 × spring compressed height.
- **At the assumed d = 3.5** (seam 7.0): spring height 3.1 mm. That is inside the 3.0–3.5 working range, but 0.1 mm above the drawing's limit working height.
- **Recommendation:** d ≈ 3.8 (seam 7.6, spring 3.4 mm, mid-range). That makes L_board hex ≈ 93.8, square ≈ 89.2, triangle ≈ 81.3 mm. The rev A boards are laid out at 94.1 (d = 3.5) as instructed. Confirm on the coupon (§7) before rev B.

## 6. Variants and parts

| Variant | Fitted | BOM |
|---|---|---|
| **Standard** | SA1–SA10, SB1–SB10: BW0019CG-L3.5W1.5H4.3 (C2826517) | `BOM_bridge_standard.csv` |
| **Injection** | + **F1 Bel 0685T5000-01** (C1T series, **slow-blow**, 5 A, 63 V DC, 50 A interrupt, 20 mΩ, 1206, LCSC **C3163312**, ≈5k stock, datasheet `docs/datasheets/fuses/Bel_0685T_C3163312.pdf`); J1/J2 wire pads (hand-soldered wires) | `BOM_bridge_injection.csv` |

- **Fuse choice:**
  - **Why time-lag:** the panel's 0.5 A PTC (mSMD050-60V) must trip before it (SPEC 8).
  - **Rating:** the datasheet recommends ≤80 % of the rating continuously, so 4 A. That matches 4 × 1 A of springs.
  - **Rejected:** Littelfuse 0440005.WRA (C1972666). LCSC lists it as "fast response", and its time-lag status couldn't be confirmed.
- **Injection current path** (≤4 A):
  - **Face A:** J1 → F1 → 1.2 mm extension (x 17.5–23) → +36V lanes. That is 0.8 mm per face over 35 mm.
  - **Spring share:** SA2/SA9/SB2/SB9 share it, with back-to-back vias at ±17.5. Each spring then sees ≈1 A at 4 A total.
  - **GND return:** through J2 at the other end.
- **Assembly:** springs on both faces, so **JLC double-sided SMT** is needed (the design requires it, SPEC 3.3).
- **Not included:**
  - **CAN TVS footprint** (SPEC "recommended"): no room in 56 × 9 mm with the slot zone. Each controller already has NUP3105L (D4).
  - **Isolating, segment, and segment + isolating variants** (planned, BOMs not generated yet; SPEC 3.3, decision 0021): made on this PCB by leaving out face-A springs (SA2/SA9 for +36V, SA4/SA5 for CAN). Panel A's pads for those nets then touch nothing, either way round. No +36V cut or DNP links needed.

## 7. Spring test coupon (`coupon/`)

| | |
|---|---|
| Board | 28 × 30 mm, 0.8 mm, 2-layer, ENIG (same spec as the bridge, so it can go in the same JLC order or on the same panel). Two halves joined by two 3 mm mouse-bite tabs (0.5 mm NPTH). |
| Spring half (z 0–14) | 4 × BW0019CG at x −7.5, −2.5, 2.5, 7.5 (bridge pitch), contacts on z 7.0. Per spring: **force pad** (THT 2.0/1.0 mm, below, 1.2 mm track) and **sense pad** (above, 0.3 mm track from the land's far end), so each 4-wire measurement includes the spring and its solder joint. |
| Pad half (z 16–30) | 4 × 3.0 × 6.0 mm ENIG pads (same width as the edge contacts) on z 23.0, with force/sense pads. |
| Stack | Snap apart and flip the pad half face-down onto the spring half. Four M2 holes (x ±12 on each half's centre line) align them. M2 standoffs plus shims set the gap: 3.0 / 3.3 / 3.5 mm = the spring working height (and the d decision, §5). |
| Measure | Force current F–F′, read voltage S–S′: contact plus spring resistance per spring (datasheet 30 mΩ); heat-rise per spring at 1–3 A (roadmap 3.3). Springs can be wired in parallel for a bridge-like 2-spring test. |
| Fab | `coupon/output/fab/`: Gerbers, CPL, BOM (C2826517 × 4). |

## 8. Changes needed elsewhere

**SPEC §3.3 and §3.4, and the interface contract (§3.5):**
- **Contact zone:** z 6.0.
- **Rule area:** ≤5.3, with in-pad vias at 5.4–6.0.
- **Bridge constraint:** contact ≤5.0 (was 6.8).
- **Corner pads:** 2.0 × 1.3 mm at 2.5 mm pitch (was 2 × 2 at 3.5), order D/CANH/CANL/DRIVE/SENSE from the wall up; B.Cu pads at z 0.5–3.5 / 6.0–8.5 / 11.0–12.6.
- **Bridge:** 56 × 9 × 0.8 mm, panel z −2.0…7.0.
- **Fuse:** Bel 0685T5000-01.
- **H:** 13.5 mm.
- **J4:** pad z 2.5–5.35 (V6.9.2; was 3.5–5.7).

**Mechanics:**
- Injection-carrier relief for F1.
- Wire channels at both bridge ends.
- Back-plate corner relief for the inward corner beads.
