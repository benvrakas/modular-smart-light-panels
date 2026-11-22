# Gap Analysis & Cost Estimate (pre-project)

**Date:** 2026-11-14 · **Against:** [SPEC.md](../SPEC.md) V4 · **Status updated:** 2026-11-21 for SPEC V6.4

> **Status as of SPEC V5 (2026-11-15).** This analysis was written against V4. Where an item is resolved or changed, SPEC.md is authoritative. See also [decision 0001](decisions/0001-edge-board-parts.md).
>
> | Item | Status |
> |---|---|
> | A2 Bridge socket | **Changed twice:** card-edge sockets → Harwin side springs (V5) → **seam bridge with low-cost top-contact LCSC springs** (V5.2, [decision 0002](decisions/0002-seam-bridge-cheap-springs.md)). All edge contacts are now on the exterior face. Still to prototype: spring ratings, insertion without snagging, seam width, carrier retention. **V5.7:** the spring's final contact point must stay ≤ 6.8 mm from the wall edge, because the active board has vias in the J1 pad tops ([decision 0007](decisions/0007-vias-in-pads-active-board.md)). **V6.4:** the carrier floats and each panel has its own wall puck ([decision 0012](decisions/0012-panel-mechanics-rev-a.md)); **V6.6:** the carrier is captive with float (a slightly loose snap fit), so it stays put on free edges and during assembly. |
> | A3 Corner joints | **Partly addressed:** 20 AWG crossover jumpers designed out. ID resistors are assembled as BOM variants (one BOM per edge code). Corner joints themselves are still open. |
> | A4 Standby | **Mostly addressed (V5.3):** the CAN transceiver standby pin and a spare GPIO (PB1) are wired, and the per-panel **LED rail is switched by a P-MOSFET on the controller board** (V6.0, [decision 0010](decisions/0010-24v-bus.md); the 5 V buck stays on for the MCU and CAN), so LEDs draw nothing in standby. Spare contact X8 stays reserved. Firmware sleep still has to be written and measured. |
> | Panel geometry (new) | **Decided (V5.4):** fixed seam inset d for every shape, so the board length differs per shape: ≈94.1 / 89.8 / 82.3 mm for hexagon / square / triangle at d = 3.5 mm ([decision 0004](decisions/0004-per-shape-board-lengths.md)). A centred layout core and three outlines. **All three outlines laid out from one layout and DRC clean (V6.9, [decision 0015](decisions/0015-square-triangle-edge-boards.md)); LED spacing per shape.** **V6.9.2:** no parts below z 6.8 on the inward face (R3 is an 0402 at z 7.2), so the soldered board ring drops into a plain back plate; J4 pads give 2.5 mm of fillet land. **The rev A test prototype is triangle panels ([decision 0016](decisions/0016-triangle-test-model.md)).** **Height (V6.0): target 10–15 mm, estimate ≈12–13 mm** ([decision 0009](decisions/0009-rear-controller-board.md)). All edge boards are passive and the MCU moves to a rear controller board. This supersedes H = 22 mm (0005). Open: lay out the passive board and confirm with the optics test. |
> | Board types (new) | **Decided (V6.0, [decision 0009](decisions/0009-rear-controller-board.md)):** every edge board is the same passive 2-layer board per shape (LEDs, ID diode/resistor, contacts, lanes; R1 codes 0–5 as BOM variants). A small 4-layer **controller board** (MCU, TCAN1044V, TPS54360B, LED switch, level shifter, LDO) lies at the rear of the chamber, parts facing the wall, white mask facing the chamber. It is drag-soldered at 90° to the code-0 edge board (≈10 pads). One controller design for every shape. Supersedes the V5.6 active/passive split (0006). |
> | B4 RGB vs RGBW | **Decided (V5.3):** RGBW, SKC6812RGBW-NW (5 V, neutral white; warm white is a drop-in) on a per-panel TPS54202 5 V rail with an AHCT level shifter. No backup data line any more. +≈$0.85–1.10 per hexagon. **V6.0:** the rail is now a TPS54360B (24 V in, always on) on the controller board, with a P-MOSFET LED switch. |
> | B2 Exposed contacts | **Addressed in schematic (V5):** staggered pads (GND first), PESD2CAN per panel, SENSE/DRIVE rail clamps. DRIVE uses 100 Ω, not ≥1 kΩ, because 1 kΩ would push code 0 into code 1. **Reopened by V6.0 (24 V), addressed in V6.2** ([decision 0011](decisions/0011-24v-fault-protection-controller.md)): DRIVE is an open-drain MOSFET through 470 Ω, SENSE is 10 kΩ, there is a TLV431 3V3 shunt, the CAN TVS is a NUP3105LT1G, and a per-panel PTC sits upstream of the SMAJ28A. A sustained 24 V short on any bus line is survivable. |
> | B3 CAN termination | Unchanged: solder jumper (MCU-switchable termination not implemented). |
> | B7 Discovery robustness | **New finding:** sneak paths through idle neighbours, fixed with a series diode per ID resistor (SPEC §4.1). |
> | Cost estimate | **Re-estimated 2026-11-15 for SPEC V5.2:** the seam bridge uses 20 LCSC BW0019-series springs (≈$0.024 each), so a bridge is ≈$0.70–1.20 including PCB, double-sided assembly and carrier, instead of ≈$3.40–7.15 with Harwin springs. A hexagon is now ≈$7–16 (was ≈$11–31). Confirm after the bridge prototype. **V5.3 RGBW** adds ≈$0.85–1.10 per hexagon (LEDs plus the 5 V buck and level shifter): ≈$8–17. **V5.6 active/passive split (0006):** one 4-layer active board plus five 2-layer passive boards, and two assembly orders, add ≈$0.35–0.80: ≈$8–18 per hexagon. **V6.0 (0009 + 0010):** six short passive edge boards plus a small 4-layer controller board, and the 24 V parts (TPS54360B, TCAN1044V, LED switch), give **≈$9–18 per hexagon** (mid ≈$13). Cheaper edge boards roughly offset the 24 V parts. |

Gaps are ordered by how much damage they do if found late. **Tier A** items can force a PCB or mechanical redesign, so resolve each with a cheap prototype before ordering any custom boards. **Tier B** items are spec decisions to make before schematic capture. **Tier C** covers software and project planning.

---

## Tier A: could force a redesign (prototype first)

### A1. Optics are unproven (highest risk)
- **Current design:** 100 mm edges, 2–3 LEDs per edge (12–18 per hexagon), an air gap, a white back, and a thin LCD-style diffuser film.
- **The risk:** a few point-like LEDs shining across an air gap onto a thin film tend to show a **bright spot near each LED and a dimmer centre**. Film spreads light much less than thick opal acrylic. (In laptop screens the film sits on a light guide plate, which does most of the spreading.)
- **Unknowns:** panel depth (edge-board height), LED aim (across the panel vs. bounced off the back), back-surface reflectance, film type (haze), and the number of layers.
- **Options if hot spots show:**
  - Aim LEDs at the matte white back so only bounced light reaches the film (cheap, costs some brightness).
  - Use two film layers, or space the film a few mm off the frame.
  - Use thin opal polystyrene sheet.
  - Use a thin light guide plate (adds cost).
- **Prototype:** a printed 100 mm-edge hex frame lined with cut WS2815 *strip* (no custom PCB). Test 15 / 25 / 35 mm depths, white matte vs. foil back, LEDs aimed across vs. at the back, and one vs. two film layers.

### A2. Bridge socket selection and enclosure
> **Superseded in V5:** spring fingers on the bridge grip plated pads on the edge board; see SPEC §3.3. The text below is the original V4 analysis.

- **Decided (V4):** bridges use **off-the-shelf low-profile card-edge sockets on a small bridge PCB**, with an optional 3D-printed enclosure. No custom contacts or springs. Edge connectors therefore have gold fingers on **both** faces of a 1.6 mm board: power on the exterior face, signals on the inward face.
- **Still open:** which socket. Criteria are 1.6 mm card, keyed, low height, narrow body, ≥1 A per contact, enough positions, rated mating cycles, and stocked at LCSC/DigiKey.
- **Seam gap:** the two socket bodies side by side set the visible gap between panels. Narrow bodies matter for looks.
- **Assembly direction:** the fingers face the wall, so the workable sequence is: bridge onto panel A, then push panel B toward the wall into the bridge's second socket. Insertion force × 2–3 bridges per panel must be taken by the wall mounting. A panel lining up with several sockets at once needs **lead-in and a little float** in the enclosure.
- **Gold-finger fabrication:** bevelling requires the fingers to sit on a panel edge during fab. Decide ENIG (fine for a few insertions) vs. hard gold (costs more, survives many insertions).
- **Prototype:** buy 2–3 candidate sockets and make a test bridge PCB. Measure contact resistance, insertion force, 5 A for 1 hour, and the seam gap.

### A3. Corner connections are a large hand-assembly cost
- 100 hexagons × 6 corners × 8 nets ≈ **4,800 hand-soldered corner joints**, plus 20 AWG crossover jumpers. That is roughly 15–30 hours of soldering before any testing.
- At 100 mm edges a wall needs about 2.25× as many panels as at 150 mm, so the joint count per wall rises by the same factor.
- Corner angles differ by shape (60° / 90° / 120°), so one rigid corner part does not fit all shapes.
- **Mitigations:**
  - Cut the nets that cross corners. BIN (backup data) can be dropped if one dead LED is acceptable, and the power crossover jumpers can be designed out (**done in V5**).
  - Use large castellated or edge-plated pads that one solder bead can bridge.
  - Use a small angle-specific corner jumper PCB per shape.
  - Use spring pins.
- **ID resistor variants:** panelize each fab panel as a **"hex kit"**: six edge boards with ID codes 0–5 pre-populated, and the MCU section populated only on board 0. JLCPCB then assembles all variants in one design, with no hand-placed ID resistors. Triangles use boards 0–2 from a kit, or get their own kit design.

### A4. Standby power is large
- With only 12–18 LEDs per panel, LED quiescent current is small (≈0.1–0.3 W per panel). Idle draw is now dominated by the MCU and CAN transceiver through the linear regulator: **≈0.3–0.5 W per panel, or 30–50 W for 100 panels with the lights "off"**.
- That is roughly 260–440 kWh, or $40–65, per year doing nothing. The spec needs an "off" mode:
  - **Node sleep:** the MCU sleeps, and the CAN transceiver goes into standby with wake on bus activity.
  - **Per domain:** the coordinator switches each PSU's AC or output with a smart relay. The cluster controllers then need an always-on low-power supply to stay reachable on Wi-Fi.
  - **Per panel:** a MOSFET on the active board switches a separate *LED rail*, distinct from the pass-through bus +12V. This adds a net at every corner.
- Decide this before the schematic, because it changes the corner nets and the pinout.

### A5. Printing logistics
- **Bed size: solved by the 100 mm edge.** A hexagon is 200 mm across its corners and fits common 220–256 mm beds in one piece.
- **Print time:** ≈1–2 h per hexagon of PETG (frame, back plate, corners) × 100–225 panels ≈ **100–450 printer-hours**, plus the bridge enclosures. Batch several frames per plate.
- PETG (glass transition ≈80 °C) is fine thermally at ambient brightness, but should be confirmed at full white in a closed cavity (see B9). PETG is not flame-retardant; that matters on a ceiling with a 30 A supply behind it.

### A6. Mounting, especially ceilings
- The spec does not say how a panel attaches to a wall or ceiling. Bridges are electrical joints, not structural ones.
- Ceiling panels need **positive retention** (screws or a twist-lock plate), not adhesive or friction. A falling 300 mm acrylic panel is a real hazard.
- Walls are not flat. Bridges must tolerate a few millimetres of out-of-plane offset between neighbors without lifting contacts.
- **Serviceability:** you need a plan for removing a panel in the middle of a cluster to replace a dead LED or board. That affects the bridge design (A2).

---

## Tier B: spec decisions before schematic capture

### B1. The MCU doesn't know its own shape
Discovery yields edge codes, but an active board cannot tell whether it sits in a triangle, square, or hexagon when some edges have no neighbors. That breaks geometry reconstruction.
**Fix (decided):** one firmware image for all shapes, with the edge count coming from one of two sources:
- **LED loopback auto-detect:** the last LED's data output returns to the MCU across the final corner. Firmware sends extra colour data, counts what comes back, and works out the LED count, then the edge count.
- **A setting in config flash:** written by the jig or the app.

Which source is primary is still open. No strap resistor is used. The loopback also detects broken chains.

### B2. Protecting the exposed fingers
> **V5:** the fingers are now plated contact pads; the protections below are implemented in the rev A schematic (see the status table above).

- Unplugged panels have bare fingers that people touch. Add ESD protection: a CAN TVS (PESD2CAN class) at least on the controller, and ideally per panel.
- Mating order: GND should connect before +12V, and +12V before signals (staggered finger lengths). This prevents hot-plug latch-up and sparking when 72 LED decoupling capacitors charge.
- Put series resistors (≥1 kΩ) and clamps on SENSE and DRIVE so a card that touches the wrong contacts while sliding in, or a hot-plug event, cannot kill the MCU. Keyed sockets prevent a fully seated card from being offset.
- Alternative: make it an explicit rule that panels are only assembled with power off. Simpler, but easy to forget.

### B3. CAN topology contains loops
- The bus runs around each panel's perimeter, and three hexagons meeting at a vertex form a closed loop across panels. CAN is specified for linear buses. At 125 kbps with total runs of tens of metres it will probably work, but this is unverified.
- **Termination:** the "electrically farthest" node is only known after discovery. Consider an MCU-switchable split termination on active boards (a MOSFET plus 2 × 60 Ω), so the controller can enable it on the right panel automatically.
- **Test:** a mock cluster of 10–20 nodes, using strip-board panels with deliberate loops, at 125 / 250 / 500 kbps.

### B4. RGB vs. RGBW, and low-brightness dimming quality
- RGB-only LEDs give poor whites and low CRI. That is fine for accent lighting, weak for "pleasant warm ambient". **WS2814** is a 12 V RGBW part in the same family, worth comparing.
- 8-bit PWM bands badly at the low levels used for night or ambient scenes. Compare GS8208 vs. WS2815 PWM resolution and frequency. Plan for temporal dithering in node firmware.
- Check PWM frequency for camera and phone flicker if panels will be filmed.

### B5. AR app platform
- **iPhone Safari does not support WebXR AR** (as of the last information available). An iPhone path means a native ARKit app: a Mac with Xcode, plus a free Apple ID (re-sign every 7 days) or a $99/yr developer account.
- Android with ARCore can use WebXR in Chrome or a sideloaded APK, which is much easier.
- **Fallback if AR slips:** place clusters manually in a simple 3D room editor in the coordinator UI. That gives room-scale effects without the app.
- **Decision needed:** which phone will do the scanning.

### B5b. Flash safety
AR recognition codes and some effects flash. Rapid high-contrast or saturated-red flashing can trigger photosensitive seizures.
- Run AR codes at low brightness, using near-equal-luminance colour steps at ≤ ~3–4 changes per second.
- Cap flash rates in the effect engine.
- Offer a calm mode.

### B6. Programming and testing hundreds of boards
- First flash of 100+ active boards: SWD pads plus a pogo-pin jig (WCH-LinkE programmer). After that, the CAN bootloader takes over.
- Test every edge board before it is glued into a panel: LED chain, ID resistor reading, continuity. A cheap test fixture saves hours of debugging installed panels.
- Plan spares: ~5% extra edge boards and a few complete panels.

### B7. Discovery robustness
- LED PWM currents on GND will add noise to SENSE readings. Run discovery with LEDs off, or average many samples.
- Handle half-seated bridges (code readings between valid bands). Re-run discovery automatically when the CAN node count changes.

### B8. Power and brightness targets are unstated
Define these numbers:
- Target brightness, in nits at the diffuser or lumens per panel.
- Maximum power per panel.
- Typical vs. maximum scene power.

They set PSU count, domain size, bridge current, and whether the copper "solder bead" reinforcement is needed at all. By rough calculation it is not needed: a 150 × 10 mm 1 oz plane is ≈7.5 mΩ, about 40 mV at 5 A.

### B9. Missing spec numbers
- Edge-board height (= panel depth)
- Finger count and pitch
- Panel weight
- LED count per edge (pending A1)
- Thermal limit
- Frame rate
- Command-to-light latency target
- Maximum panels per cluster
- Boot time

---

## Tier C: software and project planning

1. **Build the simulator first.** A desktop simulator of layouts, discovery, the CAN protocol, and effects lets firmware and coordinator work proceed before hardware exists. It also becomes the coordinator UI's preview.
2. **CAN protocol document.** Message IDs, enumeration, discovery commands, time sync, frame latch, effect descriptor format, bootloader. This goes in `firmware/common/protocol/` and is shared by node and controller.
3. **Firmware version lockstep.** Every node must run a compatible effect library. Add a version handshake, plus a rule that the controller refuses to run effects on mismatched nodes.
4. **Coordinator:** choose the host (Pi vs. ESP32) and the integrations (Home Assistant / MQTT), and decide how effects are authored (built-in library vs. scripting).
5. **Wi-Fi provisioning** for multiple cluster controllers, and OTA updates for the controllers themselves.
6. **Phasing:**
   - Phase 0: prototypes A1–A3 and B3.
   - Phase 1: one hex kit plus a controller on the bench.
   - Phase 2: 5–10 panel cluster.
   - Phase 3: multi-cluster, AR.
   - Only then order 100+.

---

## Cost estimate per panel

**Assumptions:**
- **100 mm edges, 2–3 LEDs per edge.**
- Quantity ≈100 panels.
- Prices are typical 2025–26 hobby-volume figures in USD (estimates, not quotes).
- **Excludes** shipping, import duties/tariffs (these can add a large percentage on parts from China), tools, prototypes, and spares.
- The PETG frame includes a white back plate. The diffuser is LCD-style diffuser film, one or two layers.
- Bridges are the V5.2 seam bridge (SPEC §3.3, decision 0002): 10 LCSC BW0019-series top-contact springs per board face, so 20 per bridge at ≈$0.024 each (≈$0.48), plus a small 2-layer PCB, double-sided assembly and the printed carrier: ≈$0.70–1.20 per bridge. (The V5.1 Harwin flat bridge was ≈$3.40–7.15.)

### Hexagon (6 edges, 12–18 LEDs, ≈173 mm across flats, 0.026 m²)

| Item | Low | High | Basis |
|---|---|---|---|
| LEDs, 12–18 × SKC6812RGBW (V5.3) | $1.56 | $2.88 | $0.13–0.16 each (LCSC $0.134) |
| 5 V rail (V6.0): TPS54360B buck + inductor/caps, P-MOSFET LED switch, AHCT level shifter, extended-part fees | $0.80 | $1.10 | controller board |
| Bridges, share of ~1.5–2.5 per panel | $1.05 | $3.00 | 20 × BW0019 springs + PCB + carrier ≈$0.70–1.20 each |
| PCBs (V6.0): 6 × short 2-layer passive edge boards + 1 small 4-layer controller board, ENIG contact pads | $1.50 | $3.20 | edge ≈$0.20–0.40 each at ≈94 × 12–15 mm; controller ≈$0.30–0.80 |
| Controller board parts (CH32V203, crystal, TCAN1044V, LDO, SMAJ28A, clamps) + ID resistors | $1.00 | $1.50 | the TCAN1044V adds ≈$0.20 over V5's SN65HVD230 |
| PETG: frame, back plate, corners (~55–70 g) | $0.80 | $1.40 | $15–20/kg |
| Cluster controller + coordinator share | $0.60 | $1.20 | ~$8 per controller, 10–20 panels each |
| Power share (PSU, fuses, feed wiring) | $0.50 | $1.00 | One 12 V supply per 40–60 panels |
| PCB assembly (setup, stencil, part fees, joints), amortized | $0.40 | $0.90 | two orders: edge boards (≈10 parts each) and controller boards (full BOM); corner and controller joints drag-soldered by hand |
| Diffuser film, LCD-style, 1–2 layers | $0.15 | $0.60 | |
| Wall/ceiling mounting hardware | $0.20 | $0.60 | |
| Corner joints (SMD pads: solder beads, power straps) | $0.10 | $0.30 | |
| LED decoupling + passives | $0.05 | $0.15 | |
| **Total per hexagon** | **≈$9** | **≈$18** | Mid-estimate ≈$13 (V6.0: rear controller board, 24 V) |

### Other shapes (same method)

| Shape | LEDs | Total per panel | Cost per m² |
|---|---|---|---|
| Hexagon | 12–18 | $9–18 | ≈$335–690 |
| Square | 8–12 | $6–13 | ≈1.8× the hexagon |
| Triangle | 6–9 | $6–12 | ≈3× the hexagon |

### System view
- **100 hexagons (2.6 m²):** ≈$870–1,780 plus shipping and duties.
- **No single item dominates any more:** with the seam bridge, edge PCBs, LEDs, bridges and the active board are each a few dollars.
- **Size trade-off:** with the same 2–3 LEDs per edge, a 150 mm hexagon would be ≈$11–22 per panel, roughly **45% less per m²**, because the fixed per-panel parts don't shrink. But it is 300 mm across and won't fit a common print bed in one piece. Covering a wall with 100 mm panels takes ≈2.25× as many panels, MCUs, bridges, and corner joints.
- **Biggest levers, in order:**
  1. **Done in V5.2:** the low-cost seam bridge (decision 0002) cut bridge cost by about 5×. If its springs fail the prototype, the Harwin fallback brings back ≈$4–15 per hexagon.
  2. Bridges per panel, and edge length (see the size trade-off above)
  3. Edge PCB price (finish, bevel, panelization)
  4. Active-board BOM
- **Running cost:** idle draw (A4) is roughly $40–65/yr for 100 panels unless panels sleep.

---

## Commercial viability (if this ever becomes a product)

**Price gap.** Comparable modular panel kits retail for very roughly $15–25 per panel. Retail is typically 3–4× landed material cost, which puts the target near **$5–8 per hexagon** against ≈$9–18 now (V6.0: seam bridge, RGBW, rear controller board, 24 V). The gap is now spread across the fixed per-panel parts: edge PCBs, the active board, LEDs and bridges.
- One-time costs: moulding tooling is roughly $15–60k per part family, and certification testing roughly $15–40k.

**Design changes:**
- Moulded PC or PC/ABS enclosure (UL94 V-0) instead of PETG.
- No hand-soldered corners: a one-piece ring PCB, board-to-board connectors, or a moulded frame that captures the boards.
- Diffuser film held in a moulded frame, or a moulded diffuser.
- Same bridge approach in a moulded enclosure, with the socket qualified for mating cycles.
- Listed plug-in Class 2 adapters (≈100 W per circuit in the US) instead of bench supplies.
- Standby within EU limits (≈0.5 W, or ≈2 W networked), so power gating is required.
- Minimum LED count, guided onboarding that works without AR, and signed OTA with rollback.

**Compliance** (a starting map, not legal advice):
- FCC Part 15B, and 15C/RED through a pre-certified ESP32 module.
- CE: EMC, RED, RoHS, REACH, WEEE.
- UL/ETL safety listing.
- IEC 62471 photobiological safety.
- Energy rules: EU Ecodesign standby; US DoE adapter efficiency.
- Cybersecurity: UK PSTI, EU Cyber Resilience Act, US Cyber Trust Mark.
- Matter certification (optional).

**Software and service:**
- Native iOS and Android apps.
- Local-first control.
- Integrations: Matter, Apple Home, Google, Alexa, Home Assistant.
- Customer support, warranty, and replacement panels.

**Reliability testing:**
- Connector mating cycles.
- Thermal cycling at full white.
- LED failure rate against the warranty period.
- Mounting on real wall finishes, and ceiling pull-out force.
- Drop and shipping tests.

**Business and legal:**
- **Patent freedom-to-operate search first.** Established brands hold patents on connectable panels and layout detection.
- Trademark, liability insurance, and capital for MOQs and inventory.
- Validate demand (e.g., crowdfunding).

**Differentiator:** room-scale effects that run continuously across walls, ceilings, and rooms, placed by an AR scan. Most current products map a layout in 2D on one surface.
