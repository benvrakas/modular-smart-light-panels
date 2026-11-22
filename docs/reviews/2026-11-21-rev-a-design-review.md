# Rev A design review: gate before the JLCPCB order (roadmap WP 1.9)

**Date:** 2026-11-21 · **Against:** SPEC V6.5, decisions 0009–0012 (no decision record is newer than the spec, so the spec is current) · **Scope:** controller-board, edge-board-passive (codes 0–5), bridge (standard + injection), spring coupon, `mechanical/archive/openscad-panel/params.scad` and `bridge_carrier.scad`.

This was a review only. No design file was changed. ERC and DRC ran on scratch copies, so no `.kicad_pro` was rewritten. Every number below was read from the `.kicad_pcb` files (pcbnew dump), `params.scad` or the fab outputs, not from the notes.

**Verdict:** no design file has to change before the order. Two checks in JLC's order preview must pass before paying (B1, B2). Nine should-fix items are cheap and most are order settings. Fix S1 (the corner pad order) now only if it can be re-routed in about an hour; otherwise accept it for rev A with the mitigation given.

---

## Blockers: must pass before paying (order time, no design-file change)

| # | Item | Where | Fix |
|---|---|---|---|
| **B1** | **LED orientation in JLC's placement.** The LED footprint matches the OPSCO datasheet: pad 1 GND is the notched corner, then 2 DIN, 3 VDD, 4 DOUT. At rotation 0, pad 1 is at the lower right; the CPL rotates the LEDs 180°. If JLC's library model has pin 1 somewhere else, the part goes on 180° wrong. That swaps VDD with GND and DIN with DOUT, and all 90 LEDs die at first power. I couldn't fetch JLC's footprint (EasyEDA API returned 403), so this can't be confirmed offline. | `edge-board/output/fab/CPL_edge-board-passive_code0.csv`, `…code1-5.csv`: LED1–3, rotation 180 | In JLC's DFM/placement preview, confirm that on every LED the **chamfer / pin-1 mark sits at the top left** (toward the board top edge, at −x), on the GND/DOUT row at z 11.4. Correct the rotation in the CPL if it doesn't. Check all 6 variant orders. |
| **B2** | **Spring orientation and centroid on the bridge and coupon.** The footprint origin is the body centre, but the only land is offset +0.7 mm toward the contact end. If JLC centres its model on the land, or turns it 180°, the spring's solder base lands half off the copper. The free end then points away from the wall, so the springs snag on insertion. A 180° turn also puts the dome at z 5.2, over the 5.0 limit and into the in-pad vias. | `bridge/output/fab/CPL_bridge_*.csv` (SA1–10 Top rot 0, SB1–10 **Bottom** rot 180); `bridge/coupon/output/fab/CPL_spring-coupon.csv` | In the preview, on **both faces**: the spring body must sit over its land; the C-shaped **root bend must point away from the bridge's bottom (wall) edge**; the free end and dome must sit over the land, toward the wall edge. Reject and correct if it doesn't. Write the correction into the CPL for reuse. |

---

## Should-fix

| # | Item | Where | Suggested fix |
|---|---|---|---|
| **S1** | **Corner joint: LED data sits directly behind +24V.** At each board end, the inward D pad (LED data: D_IN/D_OUT; LED RETURN on code 0) at z 0.85–2.15 sits behind the exterior +24V pad at z 0.5–3.5. Both pads touch the board end, and the two corner beads are separated only by the 1.6 mm board end and the V-gap. A +24V bead that runs into the V-gap reaches the D bead at the inner corner. That breaks the intent of the SPEC §2 rule ("never next to LED data or LED return"). It kills ≈2 LEDs per short; on code 0 it puts ≈9 mA into PA6. CANH (3.35–4.65) also overlaps the +24V pad, which is fine because CAN tolerates 24 V. | `CornerJoint_L/_R` (`edge-board/scripts/gen_footprints_v6.py`), J2/J3 at x ±47.05 | **Rev A, no change:** solder and inspect the inward signal beads first. Keep the +24V strap small, then run a +24V-to-D (and +24V-to-+5V_LED) isolation test on every corner before applying power. **If it can be re-routed cheaply now:** swap the D and CANL heights (D to z 6.5, behind GND 6.0–8.5; CANL to 1.5, behind +24V). Otherwise make it a rev B item. Either way, record the decision in SPEC §3.4. |
| **S2** | **Bridge is 9.0 mm wide and double-sided.** That is below JLC's usual ≈10 mm minimum for assembly handling (confirm in the quote). It has 4.3 mm springs on both faces. JLC Economic PCBA has historically been top-side only, so this probably needs Standard PCBA. | `bridge/output/fab/bridge_gerbers.zip` (single 56 × 9 board) | Order "Panel by JLCPCB" (or a KiKit panel) with rails. Neither long edge is functional, but sand any tab nubs on the bottom edge, because the carrier slot has only 0.1 mm clearance. Choose double-sided (Standard) assembly. The edge board (13.5 mm) should be fine on its own. **Don't put rails or tabs on its wall edge or its ends:** the springs wipe the wall edge, and the corner pads run to the ends. |
| **S3** | **There is no CAN tap for the ESP32 stand-in** (roadmap exit criterion 3). No board has CANH/CANL wire or test pads. The controller TPs, the bridge's J1/J2 and the edge-board test pads carry no CAN. | — | **No-change fallback:** solder three wires on one controller, from the wall side through the open pocket: R12.1 (CANH), JP1.2 (CANL) and TP3 (GND). **Cleaner:** add CANH/CANL pads to the controller TP grid, or to the injection bridge's gaps at x ±10/±15. Decide before ordering. |
| **S4** | **Edge-board solder-mask colour isn't specified.** The inward face, z 6.6–13, is the light-chamber wall the LEDs sit on. Green mask there absorbs light and tints the edge band. | LAYOUT-NOTES-V6 §1 (fab spec) | Order the edge boards in **white mask** (no extra cost at JLC; the silkscreen becomes black), the same as the controller. |
| **S5** | **Six BOM variants means six separate PCBA orders.** JLC allows one BOM per order. That is ≈6 × (PCB with ENIG + $8 setup + $1.50 stencil + $3 LED fee) ≈ $180 for 30 boards. | `edge-board/output/fab/BOM_edge_code0..5.csv` | Accept it, or panelize a **"hex kit" panel**: the six codes in one design with unique designators, one BOM, 5 panels. That is ≈ $50 in total. The panel must keep the wall edge and the ends clean, so tabs go on the top edge only and the ends are routed. That makes it a new KiKit file, which is about a day's work. |
| **S6** | **Copper runs to the board edge, and the wall-edge bevel.** The corner pads reach 0 mm from the board ends. Controller J1 reaches 0 mm from the base edge. The GND contact pads end 0.3 mm from the wall edge. JLC may pull the copper back or put the order on hold. JLC's bevel option is for gold fingers, bevels both faces, and adds cost. | edge board J2/J3/J1; controller J1 | Add an order remark: "Pads at the board outline are intentional. Do not pull back; route through." **Don't order a bevel for rev A:** the springs' root-bend ramp already gives lead-in. Lightly hand-chamfer the wall edge if insertion snags (S7 below). |
| **S7** | **Springs compressed to 3.1 mm at d = 3.5** (SPEC item 18; the minimum is 3.0). The frames don't limit this: with the 0.6 mm visible gap closed, the springs would go to 2.8 mm. | `params.scad` `seam_d`; MECH-NOTES assembly step 8 | **Rev A, no PCB change:** set panel pitch with a printed **spacing gauge at 173.8 mm** centre to centre (seam 7.6, springs at 3.4 mm, visible gap 1.2 mm). The carrier base still reaches 1.2 mm under each board edge. Add a 3.1 mm shim to the coupon set so the coupon also measures today's d = 3.5 case. |
| **S8** | **No injection or free-edge carrier exists.** On the injection bridge, F1 (1206) sits on face A at x 22.4–26.8, z −0.5…1.3, inside the 1.25 mm spine wall. J1/J2 wires at x ±26.4 have no exit: the carrier ends at 29.5 and the legs start at 30.0. The screw-tab variant (decision 0012, ruling 1) isn't modelled. `bridge_carrier.scad` (11-20 15:05) predates the bridge layout. | `mechanical/archive/openscad-panel/bridge_carrier.scad` | Put the rev A injection bridge on a **free cluster edge** (MECH Q5). Add `part="injection"`: an F1 pocket ≥1.0 mm deep at x 22–27.2, z ≤ 1.6 on one spine face; screw tabs; and a wire exit on the open side. Add a printed cover over the open face's live springs. These are printed parts, so this doesn't block the JLC order. |
| **S9** | **BOM header is "LCSC".** JLC's template expects "LCSC Part #"; it usually auto-maps, but not always. | all `output/fab/BOM_*.csv` | Map the column in the uploader, or rename the header to `LCSC Part #`. |

---

## Notes (checked, no action needed unless stated)

### 1. ERC, DRC and parity (re-run 2026-11-21, kicad-cli 9.0.6, `--severity-all`, DRC with `--schematic-parity --all-track-errors`)

| Board | ERC | DRC violations | Unconnected | Parity | Exclusions |
|---|---|---|---|---|---|
| controller-board | 0 | 0 | 0 | 0 | none |
| edge-board-passive | 0 | 0 | 0 | 0 | none |
| bridge | 0 | 0 | 0 | 0 | none |
| spring-coupon | 0 | 0 | 0 | 0 | none |

- **Rules ignored on purpose (each has a stated reason):**
  - edge board corner pads at the board end
  - controller J1 at the base edge
  - footprint/courtyard library checks
- **Gerbers are current:** regenerated from the boards and compared with `output/fab/`, they are identical on every copper, mask, paste and edge layer.
  - Edge board, bridge and coupon use the aux origin; the controller uses absolute coordinates.
  - The CPL origins match.

### 2. Interface contract, cross-checked from the files

| Check | Result |
|---|---|
| **J1 ↔ J4** | Both have 10 pads at x = −11.43 + 2.54(n−1), 1.3 wide, on F.Cu, and the nets match pad for pad (+24V_IN/+24V, GND, +5V_LED, LED_RETURN = D_IN, LED_DATA_OUT = LED1_DI, SPARE, CANH, CANL, SENSE, DRIVE). In 3-D, both boards' +x is world −X (the controller seen from the wall, the edge board seen from inside), so pad n meets pad n with no mirroring. J4 is at z 3.5–5.7; the controller underside is z 5.0, so there is 1.5 mm of fillet land on the wall side. ✓ |
| **Floor and LEDs** | Floor and controller top z 6.6. LEDs at x −31.2/0/+31.2, centre z 9.8, body 7.37–12.23: **0.77 mm** clearance. The lowest inward-face parts over the controller span are D1 (pad z 6.95), R2 (7.08) and C4 (7.15), all ≥ 6.8. R3 (6.78) is at x −36.6, outside the controller's |x| ≤ 36. ✓ |
| **X1–X10 ↔ springs** | Pads at x −22.5…+22.5 (5 mm pitch), nets GND, +24V, GND, CANH, CANL, DRIVE, SENSE_EDGE, SPARE, +24V, GND, as in SPEC. Face A springs SA(x) meet panel A's pad at x; face B springs SB meet panel B's pad at −x. Every net matches. SA6/SB6 and SA7/SB7 make the SENSE↔DRIVE cross. Rotating the bridge 180° maps every net onto itself (DRV_A_SNS_B ↔ SNS_A_DRV_B). ✓ |
| **Spring contact vs no-via zone** | Spring lands at panel z 2.6–4.7, dome at **3.5** (footprint origin 4.35 − 0.85). In-pad vias are at z 5.4–6.0 (centres 5.7). The only B.Cu copper in the strip apart from pads is the X4/X5 necks at z 5.8–6.45, on their own nets. Worst case 3.5 + 1.0 + 0.45 = 4.95 ≤ 5.0. ✓ |
| **Bridge envelope** | Outline 56.0 × 9.0 × 0.8, panel z −2.0…7.0, \|x\| ≤ 28. Carrier slot 56.6 long and 0.9 wide; spine top z 2.0; frame wall bottom z 7.5 (0.5 mm over the bridge top); legs from \|x\| 30. Nothing on the faces below z 2.2 except F1 on the injection bridge (S8). ✓ |
| **Mechanical keep-outs** | Exterior face at \|x\| 30–36.5, z 0–7.5 (legs): only tented copper (D_IN segment and via at −36.6, 1.9, lanes b1/b2). Inward face z ≥ 12.8 (lip): only tented +5V_LED vias (z 12.5–13.1). Inward face below z 6.6: only J4, TP1, TP11, tracks and vias. The wall edge is straight. ✓ |
| **Corner pads** | J2 (L, IN) and J3 (R, OUT) have the same heights. Inward face: D 0.85–2.15, CANH 3.35–4.65, CANL 5.85–7.15, DRIVE 8.35–9.65, SENSE 10.85–12.15. Exterior face: +24V 0.5–3.5, GND 6.0–8.5, +5V_LED 11.0–12.6. Board n's J3 meets board n+1's J2 with the same net at the same z (D_OUT → D_IN). Frame corner windows (exterior 4.0, lip 2.6, plate 3.0 from each end) clear the 3.0/2.0 mm pads. ✓ (see S1) |
| **Controller outline** | Bounding box 70.59 × 24.05 mm, which matches a 72.0 base with R1 fillets at 60°. In the triangle (82.3 mm inner side) the slanted sides clear the boards by **4.36 mm** with the 0.2 mm joint gap (4.46 mm without it, as the notes say). The top edge, 44.3 mm, fits inside the 54.4 mm available at that depth. ✓ |

### 3. Nets end to end (3-panel cluster)

- **Power:** +24V, GND and +5V_LED run all the way round each panel through J2/J3. The controller feeds +24V_IN → F1 → +24V. The bridges join +24V/GND springs back to back.
- **LED chain:**
  - Controller U4 → R5 → J1.5 → code-0 J4.5 (LED1_DI) → LED1–3 → J3.1 D_OUT.
  - Boards 1–5: J2.1 D_IN → R3 (fitted) → LED1 → … → board 5 D_OUT.
  - Back on code 0: J2.1 D_IN → J4.4 → J1.4 LED_RETURN → R7/R8 → PA6. That makes 18 LEDs.
  - On code 0, R3 is left out of both the BOM and the CPL ✓. Mark the code on each board when it arrives: the variants differ only in R1 and R3.
- **Discovery:**
  - SENSE bus → D1 (anode on SENSE, pin 2) → R1 → X7 SENSE_EDGE → bridge cross → the neighbour's X6 DRIVE → its R11/Q3. The diode direction is correct.
  - Each panel's SENSE and DRIVE form a ring through the corners.
  - CAN is a ring inside each panel and a mesh across the bridges. That is harmless at 125–250 kbps.
- **+24V adjacency:**
  - Controller: DRC rule ≥ 1.0 mm, passes.
  - Edge board: DRC rule ≥ 0.5 mm to +5V_LED and the LED/ID nets, passes, with a GND guard under J4.1.
  - Contacts: X2 sits between GND pads; X9 between SPARE and GND.
  - Bridge: carries no 5 V nets.
  - J1/J4: pad 1 has only GND beside it.
  - **Two exceptions:**
    - The corner joint (S1).
    - On the injection bridge, live J1 (+24V_IN) faces panel B's tented D_IN trace and via at x −26, z 1.9, across a 3.1 mm gap. Low risk, and none at all on a free edge.

### 4. Fab readiness

- **Files present for every board:**
  - Gerbers and drill zip
  - BOM and CPL. The CPLs match the BOMs, and DNP parts are left out (controller R26, edge R2, code-0 R3).
- **Gerbers are fully masked where needed:**
  - Edge board: B.Paste empty, so the contact pads stay bare ENIG.
  - Controller: B.Mask, B.Silk and B.Paste empty, so the chamber face is plain white mask.
- **The gerber jobs say "Finish: None",** so set these at order time:

| Board | Layers / thickness | Finish | Mask | Notes |
|---|---|---|---|---|
| Edge | 2L, 1.6 mm, 1 oz | **ENIG** | **white** (S4) | |
| Controller | 4L, 1.6 mm, JLC04161H-7628 | HASL lead-free or ENIG | **white** | tented vias |
| Bridge | 2L, **0.8 mm** | **ENIG** | — | panel with rails, double-sided assembly (S2) |
| Coupon | 2L, 0.8 mm | ENIG | — | The two halves are joined by mouse bites inside one outline. JLC may count it as two designs, which costs a few dollars. |

- **Rotations to confirm in JLC's preview.** The CPL uses KiCad's orientations; JLC's library zero often differs for SOT-23, SMA and SOIC.

| Board | Parts | What to look for |
|---|---|---|
| Edge | **LED1–3** (B1) | chamfer at top left |
| | **D1** SOD-323, −90° | cathode band on the **upper** pad (ID_K, z 9.35), anode toward the wall edge |
| Controller | U1 TSSOP-20 (−90°), U2 SOIC-8 (−90°), U5 PowerPAD (90°), U3 SOT-89 (180°), U4 SOT-23-5, U6 TLV431 SOT-23 | pin 1 positions |
| | Q1–Q3, D2, D4, D6 SOT-23 | |
| | **D5 / D7 SMA** | cathode bands: D5 cathode on +24V, D7 cathode on SW |
| | Y1 | pin 1 |
| Bridge, coupon | **springs** (B2) | |

- **Stock** (JLCPCB parts API, 2026-11-21, JLC assembly stock):
  - Nothing is out of stock, and every line is far above 3× the rev A quantity.
  - The thinnest: CH32V203F6P6 **1,279** (need 5, 256×) and TCAN1044VDRQ1 **1,349**. Both have fallen since 11-16 (1,575 / 1,502). **Order soon.**
  - Others: 0685T5000-01 4,966 (need 10); 162 k 7,976; SS36 9,292; FNR6045S 11,603; SMAJ28A 12,164; springs C2826517 43,409 (need ≈220); LED C5348912 42,257 (need 90).
- **Extended parts** ($3 each per order): controller 17, edge 1 (the LED), bridge 2, coupon 1.

### 5. Other observations

- **Spring finish:**
  - The BW0019CG part-number decoder reads "CG = 雾锡 (matte tin)".
  - Drawing note 8 gives Ni 50–80 µ″ under a **1 µ″ gold flash**.
  - The SPEC says gold over nickel.
  - So confirm the finish on the delivered parts. Treat contact wear as a coupon measurement: 1 µ″ of gold against ENIG is thin.
- **Bridge CAN TVS (left out):** accepted for rev A.
  - Each controller has D4 (CAN) and D6 (SENSE/DRIVE).
  - The TCAN1044V is rated ±58 V and ±8 kV.
  - Handle bridges ESD-safe; their springs are the only exposed bus metal before mounting.
- **Free cluster edges** leave X1–X10 exposed at the wall, with +24V and GND 2 mm apart. That's acceptable on a Class 2 supply. A printed edge cover is cheap.
- **Mechanical files hold stale comments; regenerate after S8:**
  - `params.scad` still mentions "rule area to 6.2", "in-pad vias at 5.7", "body z 6.9..11.9" and `pocket_min = 5.0`.
  - MECH-NOTES E3 says the PCB "still has 9.4"; the PCB now has 9.8.
- **Roadmap WP 2.1 quantities** (4 kits, 4 controllers, 8 + 2 bridges) differ from this order list. The coordinator should update them.

---

## Order list (rev A: 3 hexagon panels plus spares)

**Assumptions:** JLC 2025–26 list prices as I know them. **Nothing below is a quote; every figure is an estimate.** Parts cost is computed from the live JLC parts-API unit prices (2026-11-21). Setup, stencil and PCB prices are typical. No order was placed and no account was used.

| Line | PCB qty | Assembled | PCB (est.) | Assembly + stencil + ext. fees (est.) | Parts (API prices) | Line total (est.) |
|---|---|---|---|---|---|---|
| Edge board **code 0** (R1 0 Ω, R3 DNP) | 5 | 5 | $12–18 (ENIG, white) | $8 + $1.5 + $3 | $1.90 | ≈ $30 |
| Edge board **codes 1–5** (5 separate orders, R1 1k/2k7/5k6/12k/27k) | 5 each | 5 each | $12–18 each | $12.5 each | $1.91 each | ≈ $150 |
| Controller (4L, white) | 5 | 5 | $10–15 | $8 + $1.5 + 17 × $3 = $60.5 | $17.93 | ≈ $90–95 |
| Bridge: one BOM with **F1 fitted on all** (works as standard or injection; F1 only connects the unused J1 pad) | 10 (panelized) | 10 | $15–25 (0.8 mm ENIG) | Standard, double-sided: ≈ $25–40 + 2 × $3 | $9.00 | ≈ $55–80 |
| Spring coupon | 5 | 2–5 | $12–17 (0.8 mm ENIG) | $8 + $1.5 + $3 | $0.40 | ≈ $25–30 |
| Shipping (DHL/FedEx, combined) | | | | | | ≈ $25–35 |
| **Total** | | | | | | **≈ $375–430** |

- The bridge line covers 3 standard + 1 injection, plus 6 spares for spring wear and the carrier trials.
- **With the hex-kit panel (S5):** the edge-board lines drop from ≈ $180 to ≈ $50, for a total of **≈ $250–300**.
- **Separate standard and injection bridge orders instead of one BOM:** add ≈ $35–50.
- **Loose springs** for bench trials (roadmap shopping list, 50 × C2826517): ≈ $1 from LCSC. Optional.

---

## Top risks for the rev A build, with mitigations that fit this order

| Risk | Mitigation in this order |
|---|---|
| Wrong LED or spring orientation by JLC | B1/B2 checks in the preview. Assemble 2 of the 5 coupons first if JLC offers it. |
| Spring overcompression at d = 3.5 (3.1 mm; 2.8 mm if the frames touch) | S7: 173.8 mm spacing gauge, 3.1 mm coupon shim. The coupon decides d before rev B. |
| +24V bead into LED data at a corner | S1: solder order and per-corner isolation test before power. Swap the pad heights if cheap. |
| J1.1 (+24V_IN) bridged to J1.2 (GND) at the drag-soldered joint: a direct bus short upstream of F1 | Ohm-check J1.1 to J1.2 after soldering. Bring each panel up through TP10 on a current-limited bench supply first. |
| Injection carrier: no F1 relief, no wire exit, no free-edge hold | S8: injection bridge on a free edge, carrier variant with F1 pocket, screw tabs and open-side wire exit. |
| No CAN tap for the ESP32 stand-in | S3: wire to R12.1, JP1.2 and TP3 on one controller from the wall side, or add pads now. |
| Missing bridge CAN TVS | Accepted. Controller D4/D6 plus TCAN1044V ratings; ESD handling of the bridges. |
| Spring current rating unknown | The coupon's 4-wire measurement at 1–3 A. The rev A load is only ≈0.6–0.8 A for 3 panels. |
| Thin MCU and transceiver stock | Order this week. |
