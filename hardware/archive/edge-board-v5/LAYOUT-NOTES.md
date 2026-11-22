# Edge board — layout design constraints (rev A)

**Date:** 2026-11-15 (updated 2026-11-16: SPEC V5.7.2, decisions 0007 vias in pads and 0008 pin swap; §13 checked against the routed active board) · **Against:** SPEC **V5.7.2**, decisions [0001](../../docs/decisions/0001-edge-board-parts.md)–[0008](../../docs/decisions/0008-mcu-pin-swap-led-ret-led-en.md), all accepted (0003 incl. "Resolved during schematic implementation"), PCB placement trial `output/placement-trial/NOTES.md`, active `edge-board.kicad_sch` and passive `../edge-board-passive/edge-board-passive.kicad_sch` (ERC clean per the schematic session), `ModularLight.pretty` (04:30), `docs/datasheets/TPS54202DDCR.pdf`

**Board types (decision [0006](../../docs/decisions/0006-active-passive-board-split.md), 14:33):**
- The **PASSIVE** board (`hardware/edge-board-passive/`, 2-layer) follows §1–§12 as written.
- The **ACTIVE** board (`hardware/edge-board/`, 4-layer) follows §1–§12 **except where §13 overrides them.**

**Purpose:** these are the electrical, thermal and mechanical limits the PCB layout has to meet. *Where* parts go is up to the PCB session (modular-smart-light-panels-41); the outline and lane stack are in [GEOMETRY.md](GEOMETRY.md). These notes are not decisions: items in §11 would change the spec or a footprint, so they need a decision record before they're adopted. The numbers are rough hand calculations; the assumptions are in §12.

---

## 0. The short list

1. **Board height: H = 22 mm is the placement minimum** on both the triangle and hexagon outlines (PCB trial, 0 courtyard overlaps). That holds **only with the corner-to-corner bus on B.Cu** above the +5V lane, which is accepted here with conditions (§3). The user approved this exception to SPEC §2 zoning (decision 0005, SPEC V5.5).
2. **Keep the +12V and GND lanes uncut.** With +12V lowest, the three GND contact pads must cross the +12V lane. Cross with a small F.Cu jumper sized for the springs' current, not by cutting the 5 A lane (§3).
3. **Buck layout rules:** hot loop tight, SW node small and ≥10 mm from the crystal, SENSE/ADC and CAN, FB sensed with a Kelvin connection (§6).
4. **Copper path rating:** the +12V and GND paths must carry the **feed-through current**, sized to the injection fuse (target 5 A), not just the panel's own ~0.4 A (§1).
5. **The LDO's heatsink copper is net VIN_LDO** (the SOT-89 tab is pin 2), not GND (§7).
6. **DRIVE must never neighbour +12V on either layer.** That short is still destructive (84 mA through R11 into 3V3). Shorts to +5V, and SENSE to +12V, are now survivable after the clamp move, but SENSE and DRIVE stay off both supplies as a margin rule (§5).
7. **Breakaway tabs:** no ceramic capacitor within 3 mm of a tab, and ≥3 tabs spread along the board (§10). Resolved on the active placement.
8. **ACTIVE board, 4-layer (§13):**
   - In2 must be **GND under the B.Cu bus band**, since it's the bus's reference plane, 0.21 mm away.
   - **DRIVE vias** through the In2 +12V region need ≥0.5 mm plane clearance.
   - **0.5 oz inner copper is enough** (measured: +12V plane 9.4 mΩ end to end, worst neck 6.25 mm over 3.7 mm). Order 1 oz only if the fuse goes above 5 A (§13.2).
   - **3.3 V logic vias through the +12V or +5V plane get ≥0.5 mm clearance.** This applies to DRIVE (destructive, hard rule) and to LED_EN on PA0 and the CAN logic nets (margin) (§13.6). Applied and verified on the routed board.
   - **≥8 vias per corner power pad.**

**Done in the schematic and library since the last revision** (checked):
- Corner power pads ordered **+5V / GND / +12V** with 2.5 mm gaps.
- C1–C4 moved to +5V.
- Buck EN (LED_EN) on **PA0** with a 100 kΩ pull-down (R18). It was on PA6 before the decision 0008 pin swap.
- TP11 on +5V.
- LED loop-back (LED_RET) on **PA6** (TIM3_CH1) through a 2.2 k / 3.3 k divider. It was on PA0 before the swap. PA6 is not 5 V tolerant, so the divider stays.
- AHCT OE̅ tied to GND.

**Resolved by V5.3:** the hot-plug overvoltage risk to the LEDs. They now sit behind the buck, and everything left on +12V is rated for 28 V or more.

---

## 1. Current budget and copper rating

### 1.1 Currents (LED figures from the SKC6812RGBW datasheet, decision 0003)
| Item | Current | Notes |
|---|---|---|
| One LED, full RGBW | ≈40 mA at 5 V (0.2 W) | RGB 8 mA each, W 16.5 mA |
| One board, 3 LEDs | ≈120 mA on +5V | |
| +5V rail, one hexagon | ≈0.73 A | From the buck on the active board, around the corner ring |
| Buck input (+12V), one hexagon | ≈0.35 A | 3.7 W out at ~87 % efficiency |
| Logic from +12V (HT7533) | 25–35 mA | |
| **Panel total on +12V** | **≈0.38 A** | |
| Spring-limited joint | +12V ≈ 2 A, GND ≈ 3 A | 2 +12V and 3 GND springs per face, at ≈1 A per spring (unconfirmed) |
| **Board +12V/GND design target** | **5 A continuous** corner to corner, or the injection fuse rating if higher | A downstream fault is limited only by the fuse. |

**Rule:** the injection fuse protects the springs and the board copper, so never fuse above what they're rated for.

### 1.2 Copper limits (1 oz external, sheet resistance 0.49 mΩ/□; IPC-2221 at 10 °C rise)

| +12V/GND lane width | R per 100 mm | At 5 A: drop / loss / ΔT |
|---|---|---|
| 3 mm | 16 mΩ | 82 mV / 0.41 W / 9 °C |
| 5 mm | 9.8 mΩ | 49 mV / 0.25 W / 4 °C |

| Element | Constraint |
|---|---|
| +12V and GND **lanes** (feed-through) | ≥2.8 mm everywhere, **uncut** corner to corner. GEOMETRY.md's 3.0 mm lanes meet this. |
| Pad necks into their own lane | Full pad width (3.0 mm) |
| **Pad crossings** (a pad that must pass another net's lane) | Sized for that pad's spring: ≈1 A, so plan 2 A for margin. That's ≥0.8 mm and ≥3 × 0.3 mm vias per end (§3). |
| +5V ring (≤0.6 A per segment if one corner is open, ≤0.3 A normally) | **≥1.5 mm**, set by voltage drop. Per board ≈31 mΩ: worst two-way ≈17 mV, one-way with an open corner ≈55 mV (double both for the GND return). Keep the buck-to-farthest-LED round trip ≤ ~0.2 V. |
| Layer change in a feed-through path | ≥8 × 0.3 mm or ≥6 × 0.4 mm vias. For +5V, ≥2 × 0.3 mm. |
| Gap between different power nets | ≥0.5 mm. **+12V copper never next to +5V copper on the same layer** (GND lane between; holds in the V5.4 stack). |
| Signal traces | ≤35 mA: 0.25 mm / 0.2 mm spacing is fine. |

---

## 2. Edge-contact strip (exterior face, B.Cu)

These already hold in the footprint: 10 pads in the order GND, +12V, GND, CANH, CANL, DRIVE, SENSE_EDGE, SPARE, +12V, GND; 3.0 mm pads at 5.0 mm pitch with a 48 mm span (rule area ±25 mm); setbacks of 0.3 / 0.6 / 0.9 mm; a full mask opening; and a rule area with no pour or vias, tracks allowed.

- **The 48 mm strip fits every shape:** ≈13 mm per side after the corner pads in the triangle (82.3 mm), ≈19 mm in the hexagon. It must be centred on the board, which decision 0004 places on the seam-line midpoint, so bridges stay universal.
- **Mating order versus tilt:** I checked it. GND → +12V → signals holds for any tilt up to ±45°.
- **Remaining risk: scatter in the spring contact points.** A 0.3 mm step only tolerates about ±0.15 mm of scatter. **Prefer ≥0.5 mm steps** if the pad length still covers the final contact point. Confirm on the prototype.
- **Final contact height:** where the spring comes to rest when seated must fall within the pad (setback to 8 mm), including tolerances. Aim for the middle.
- **Lateral float ≤ ±0.7 mm.** The 2.0 mm gap between pads is wider than the 1.5 mm spring, so one healthy spring can't bridge two pads.
- **No paste, silkscreen or vias in the strip.** Vias are blocked through the whole board there, so parts on F.Cu over the strip (|x| < 25, y < 8.5) can't use vias; only via-free parts belong there.
  - **Exception (active board, [decision 0007](../../docs/decisions/0007-vias-in-pads-active-board.md)):** each pad carries its own vias in its top end (row at y 7.65), through a hole in the keep-out. The springs must come to rest ≤ 6.8 mm from the wall edge.
- **Copper-to-edge and bevel:** GND pads 0.3 mm from the edge are at a typical fab minimum for routed edges. Confirm the fab's bevel depth.
- **Finish:** ENIG (~0.05 µm gold) wears through after tens of sliding cycles, which is fine for assembling once.
- **SPARE (X8):** a reserved signal. Standby uses the buck's EN pin, not this pad.

---

## 3. B.Cu stack and crossings (H = 22, PCB trial 13:06)

| y (mm) | B.Cu | Constraint |
|---|---|---|
| 0–8.5 | contact strip | §2 |
| 8.5–9.5 | via row | Signal stubs and GND-hop vias |
| 9.5–12.5 | +12V lane | ≥2.8 mm, uncut |
| 13–16 | GND lane | ≥2.8 mm, uncut |
| 16.5–18 | +5V lane | ≥1.5 mm |
| ≈18.5–20.3 | **signal bus** (CANH, CANL, DRIVE, SENSE) | See below. Keep ≥1.0 mm of copper-free margin to the top edge (§10). |

- **Why this order:** the +12V pads neck straight into the lowest lane; GND sits between +12V and +5V (same order as the corner pads); and the bus sits next to +5V, never +12V. That keeps the DRIVE↔12 V rule in §5 by construction.
- **GND contact-pad crossings:** the three GND pads (X1, X3, X10) cross the +12V lane by **hopping over on F.Cu**:
  - via above the strip (y ≥ 8.5),
  - an F.Cu trace past the +12V lane,
  - vias into the GND lane.

  **Never cut the +12V lane.** Size each hop for the springs it carries:
  - one spring: ≥0.8 mm, ≥3 × 0.3 mm vias per end;
  - **the shared X1+X3 hop at x = −22.5: ≥1.6 mm, ≥6 vias per end** (accepted).

  **X3's jog along y ≈ 9 must be on F.Cu.** On B.Cu it would cross the X2 +12V neck at x = −17.5.
- **X10 hop:** terminate it in **its own vias into the GND lane**, not through C16/C17's pads. Bridge return current must not flow through the buck's hot-loop ground node.
- **Bus on B.Cu (accepted, replacing "bus on F.Cu over the GND lane"):**
  - **Order from the +5V lane upward:** CANH/CANL, DRIVE, SENSE (reconciled with SPEC V5.5 §2 / decision 0005). Two reasons:
    - **Safety:** only the CAN pair neighbours a supply. CAN is tolerant: SN65HVD230 −4…16 V, PESD2CAN 24 V. With the clamps now behind R10/R11, SENSE/DRIVE shorts to +5V are survivable, so this is a margin rule. DRIVE ↔ +12V is still destructive and stays a hard rule (§5).
    - **Noise:** high-impedance SENSE goes outermost, farthest from the LED-current lane.
  - **Width:** 4 × 0.25 mm traces with 0.25 mm gaps ≈1.75 mm, leaving ≥1.5 mm top margin at H = 22.
  - **Reference:** the +5V lane next to it, plus F.Cu GND pour over the band where the top-row parts allow, stitched to the GND lane at ≤10 mm intervals. CAN is differential at ≤250 kbps and SENSE/DRIVE are near-DC, so a fragmented reference is acceptable. No hard rule.
  - **Taps:** each bus net drops by a via to F.Cu and runs down to its via above the strip. The X5/X6 stubs under LED2's body (between its pad columns) are fine.
  - **Mechanical:** the bus is on the exterior face, under solder mask, facing the seam. No frame, snap-fit or carrier feature may rub the band.
  - **Side benefit:** the LED data chain (DIN/DOUT diagonal on the SKC6812 footprint) no longer crosses the bus.
- **4-layer:** adopted for the active board only (decision 0006). The hop rules above apply to the 2-layer passive board (§13.4).
- **LED supply:** each LED's VDD (pin 3) via goes to the +5V lane and GND (pin 1) to the GND lane, with 100 nF across the two pins in the smallest possible loop.

---

## 4. Hot plug (re-checked with the 04:30 schematic)

- **Capacitance on +12V per hexagon:** C16 (10 µF 50 V X7R 1206, ≈7–8 µF effective at 12 V) + C17 100 nF. C12 sits behind R14's 68 Ω. C1–C4 are now on +5V.
- **Estimate** (L = 50 nH, R = 20–40 mΩ): peaks of ≈100–120 A and **≈18–20 V**, lasting about a microsecond.
- **Parts are safe:**
  - TPS54202 VIN: 30 V absolute maximum (28 V recommended).
  - HT7533: 30 V.
  - SMAJ15A: starts to clip above 16.7 V.
- **What's left:** contact wear from the ~100 A make spikes. Measure on the prototype with a single-shot scope capture of +12V at C16 during 10 plug-ins.
- **Buck at plug-in:** EN has an internal pull-up (Ip ≈ 0.7 µA, datasheet), and R18 (100 kΩ) holds it at ≈0.07 V, below the 1.21 V threshold. The LED rail stays off until PA0 (LED_EN, decision 0008) drives it. The EN pin's 7 V absolute maximum is fine at 3.3 V. PA0 resets as a floating input, so R18 holds the buck off through reset and boot.

---

## 5. Contact and corner shorts (for clearances and pad order)

| Short | Result | Constraint / status |
|---|---|---|
| **+12V ↔ +5V** | 12 V on the LED rail: 18 LEDs, the AHCT and the PA6 loop-back divider are likely destroyed. | **Holds:** GND between them in the corner pads and the lanes. Keep it that way in routing (no +12V trace beside +5V). |
| GND ↔ +12V (adjacent contact pads, corner pads) | Bus short, limited only by the fuse | Gaps > spring width plus float (holds). Corner gaps 2.5 mm (holds). Fast fuse. |
| GND ↔ +5V | Buck goes into cycle-by-cycle current limit (high-side 2.5–3.9 A), then hiccup after 512 cycles. No damage expected. | — |
| **DRIVE bus ↔ +12V** | **Destructive.** The clamps were moved behind the resistors (netlist checked 13:55: D3 on /DRIVE_GPIO behind R11 100 Ω, D2 on /SENSE_ADC behind R10 1 kΩ). The fault then puts (12 − 3.6)/100 ≈ **84 mA** through R11 (0.7 W in an 0603 rated 0.1 W) and into +3V3. That's more than the MCU's load absorbs, so the rail rises. R11 stays 100 Ω because raising it would shift the discovery codes. | **Hard rule:** DRIVE never next to +12V copper on either layer. The stack guarantees it on B.Cu (+12V is at the bottom, the bus at the top). |
| SENSE bus ↔ +12V | **Survivable (series-limited).** (12 − 3.6)/1 kΩ ≈ 8.4 mA through R10 (≈70 mW) plus 0.9 mA through R9 (10 kΩ). The MCU's load absorbs it. | Margin rule: keep SENSE off +12V anyway. |
| DRIVE or SENSE bus ↔ +5V | **Survivable (series-limited).** ≈14 mA (DRIVE, 20 mW in R11) or ≈1.4 mA (SENSE) into +3V3, which the MCU's load absorbs. Only possible while the LED rail is on, which is also when the MCU is awake. Before the clamp move this case pumped 3V3 above the 4.0 V absolute maximum. | **Margin rule:** B.Cu bus order from the +5V lane up is CANH/CANL, DRIVE, SENSE (SPEC V5.5 §2). On F.Cu, keep SENSE/DRIVE stubs and taps ≥0.5 mm (or GND) from +5V and +12V pads: LED VDD, C1–C4, buck VIN/SW/output, D5. Prefer not to run the X6 DRIVE stub under an LED body. |
| Discovery accuracy (not a fault) | BAT54S reverse leakage rises steeply with temperature, and it loads the 10 kΩ SENSE node through R10. At a warm cavity that could shift codes by tens of mV, ~0.1 V worst case. | Calibrate thresholds (SPEC open item 10), and run discovery with the LED rail off, which also keeps the board cool. |
| Internal 3.3 V logic nets with no series resistor ↔ +12V or +5V (LED_EN on PA0, LED_DATA on PA7, CAN_TX/RX/RS, SWD) | **Destructive:** the pin's ESD diode dumps the supply into +3V3, limited only by the short. None of these nets reaches the seam or a corner. The only exposure is fab-defect clearances, such as a via through an In2 supply plane. | **Margin rule:** ≥0.5 mm via-to-plane clearance in the In2 +12V and +5V regions (§13.6). On F.Cu, normal DRC clearance. |
| SENSE_EDGE (X7, R1 side) ↔ 12 V or 5 V | D1 is reverse-biased and blocks it | None needed. SENSE_EDGE may sit next to SPARE. |
| LED data D ↔ SENSE/DRIVE (corner bead) | The SK6812 DOUT pushes at most ~10–20 mA through the clamp. The MCU's ~20–30 mA load holds +3V3, so it's probably not damaging, but discovery and the LED chain are wrong. | Isolation-test every corner in the jig. |
| Signal ↔ signal (corner beads) | No damage, but CAN, the LED chain or discovery stops working | Corner signal gap is now 1.5 mm (3.5 mm pitch). Isolation-test every corner in the jig. |
| 3V3 short | R14 limits current to ≈176 mA, then dissipates 2.1 W and fails open | Keep R14 clear of the PETG frame and the LEDs. |

**ESD:** the clamps (D2–D5) are on the active board only. The CAN bus must pass **through D4's pads before U2**.

---

## 6. Signal-integrity and noise constraints

**Trace capacitance and impedance are not constraints on this board.**
- A 0.25 mm trace over GND 1.6 mm away is ≈138 Ω, 0.42 pF/cm and 7.9 nH/cm.
- CAN and the 800 kHz LED data only behave as transmission lines at lengths of metres, and each LED regenerates the data.

**Buck (U5 TPS54202, L1 15 µH, C16/C17 in, C19/C20 2 × 22 µF out, R16/R17 100 k / 13.3 k, C21 75 pF):** the switch node swings 0–12 V at ≈500 kHz with fast edges.

| Element | Constraint (TI §10.1 plus this board) |
|---|---|
| **Input hot loop** (C16/C17 – VIN – GND pin) | C17 and C16 **directly at the VIN and GND pins**, smallest loop, with several vias. No switching current flowing under the IC. |
| **SW node** | Short and only as wide as needed, pad to L1 only. **≥10 mm from Y1/C5/C6, C14 and the SENSE/ADC node**, and not under or beside the CAN pair or the LED_RET loop-back trace (PA6). Routed board, 2026-11-16: BUCK_SW is ≈39 mm from LED_RET, 26 mm from SENSE_ADC, 25 mm from the OSC nets and 19 mm from CAN. Passes. |
| C18 (BOOT) | At the BOOT and SW pins |
| L1 and C19/C20 | L1 next to SW. C19/C20 returns go by a wide path to the IC's GND pin. Solid GND under the whole buck. |
| **FB** (R16, R17, C21) | At the FB pin, with a small FB node. R16 fed by a separate trace from the +5V output. R17 grounded with a Kelvin connection to the IC's GND pin. Shield FB with GND, away from SW and L1. |
| Loop speed | TI's crossover estimate fo = 3.95 / (VOUT·COUT) must be < 40 kHz. With ≈25 µF effective at the buck that's ≈32 kHz; with all ≈65 µF on the ring counted it's ≈12 kHz. Both are inside the limit, so the distributed per-board C4 doesn't threaten stability. Do a load-step test on the prototype. |
| Firmware hook | **Run discovery with the buck disabled,** which removes LED PWM and switching noise from SENSE. |

Other nets:

| Net or area | Constraint |
|---|---|
| Y1, C5, C6 | Within ~5 mm of U1 pins 2/3, short and symmetric, guarded by GND. Buck ≥10 mm away. (C5/C6 = 15 pF assumes ~4 pF stray.) |
| SENSE_ADC / C14 | C14 at the ADC pin, with its GND return close to VSS/VSSA |
| SENSE, DRIVE | In the B.Cu bus band (§3), SENSE farthest from the +5V lane. Firmware waits ≥0.5 ms after DRIVE goes low (τ ≈100 µs). |
| CANH/CANL | Adjacent pair (B.Cu bus band, next to the +5V lane). Stub to U2 < ~20 mm. R12/JP1 at U2. |
| LED data (PA7 → U4 AHCT → 33 Ω → LED1) | U4 with C15 at pin 5. The 5 V output trace to LED1 short; the 3.3 V trace from PA7 can be longer. Firmware holds PA7 low while the rail is off. |
| Loop-back LED_RET (last DO → 2.2 k/3.3 k → PA6, TIM3 external clock) | Divider at the MCU end: 3.0 V high, Thevenin 1.3 kΩ × ~10 pF ≈ 13 ns, fine at 800 kHz. No added capacitance. |
| Decoupling | C7 at U1 VDD pin 16 / VSS pin 15. C8 at VDDA pin 5. C11 at U2 pin 3. C1–C3 at each LED. C4 (+5V bulk) on every board. Vias beside the pads. |
| D5 (TVS) | Short and wide to +12V and GND, ≥2 vias per side |

---

## 7. Thermal constraints

| Part | Dissipation | Constraint |
|---|---|---|
| **U3 HT7533 (SOT-89)** | 0.20–0.24 W | The tab is pin 2, VIN, so the heatsink copper is the **VIN_LDO** net, 2–3 cm². Junction rise ~20–24 °C with that copper, ~36–44 °C without. |
| R14 (68 Ω 1206) | 61–83 mW | Fine; place it with C12 at U3's input. |
| **U5 TPS54202 (SOT-23-6, RθJA 89 °C/W, JEDEC)** | ≈0.3 W of the ≈0.5 W buck loss | Junction rise ≈27 °C. Wide VIN and GND copper (TI). Thermal shutdown is at 155 °C. |
| L1 SWPA4030S150MT | DCR loss at 0.73 A | **Check the datasheet:** Isat ≥ ~1.2 A (normal peak ≈0.93 A at full white, plus soft-start charging of ~65 µF) and the DCR loss. A +5V short drives it up to the 2.5–3.9 A current limit for 512 cycles before hiccup. That's acceptable if it saturates briefly, but confirm. The datasheet isn't in `docs/datasheets/`. |
| LEDs | 3 × 0.2 W per board | Heat leaves through the pins, so connect VDD/GND to wide copper. Check the maximum operating temperature against a closed cavity (decision 0003 open item). |

**The active board has ~1 W of local heat in a closed PETG cavity** (buck ≈0.5 W, LDO + R14 ≈0.3 W, 3 LEDs). Don't cluster the buck, U3 and R14.

---

## 8. Corner joints (`CornerJoint_L/_R`, 04:30)

**Checked against my constraints:**
- Power pads on B.Cu: **+5V (y 0–2, 3 × 2 mm), GND (y 4.5–8.5, 3 × 4 mm), +12V (y 11–15, 3 × 4 mm)**, with 2.5 mm gaps and GND between the supplies.
  - +12V and GND at 3 mm wide meet 5 A.
  - +5V at 3 × 2 mm is fine for ≤0.6 A.
- Signal pads on F.Cu: 5 × (2 × 2 mm) at 3.5 mm pitch, a 1.5 mm gap.
- Total span ≈16 mm.

Still to watch:
- **Corner pads vs lanes:** copper jogs at the ends are fine (accepted).
  - The pads are +12V at y 1–5, GND at 7.5–11.5 and +5V at 14–16, against lanes at 9.5–12.5, 13–16 and 16.5–18.
  - The vertical order is the same, so each lane bends down to its pad without crossing.
  - Keep the full width through each jog (+12V/GND ≥2.8 mm, +5V ≥1.5 mm), ≥0.5 mm gaps, and stay at |x| > 25 (outside the strip rule area).
  - The bus drops to F.Cu before the jog region.
  - **Triangle:** the fan-out of 4 bus vias in the ≈1.5–2 mm between the core (|x| ≤ 37.0) and the corner pads is tight. Stagger the vias.
- **Outside-corner V-gap** the strap or bead must span: ≈1.6 mm (hexagon), 2.3 mm (square), 2.8 mm (triangle). A bead alone gets unreliable as the gap grows, so check the triangle case.
- **Pad attachment:** the strap's mechanical load sits on SMD pads. Tie them solidly into their copper (anchoring, but needs a strong iron). If thermal reliefs are used instead, they must still meet the pad current.
- **Copper at the board end:** all corner pads touch it, which is a DRC violation the fab may trim. Use a local rule and confirm with the fab.
- **Corner pads move with the board ends per shape** (decision 0004). The extensions for longer boards are plain copper and traces only.

---

## 9. Layout-core fit — settled by placement

The PCB trial (13:06) **supersedes my earlier area estimate** (H ≈ 24–25).

| H | Result |
|---|---|
| 20 | Fails: 11 top-row parts overflow. |
| **22** | **Fits** both the triangle (81.9 mm) and hexagon (93.7 mm) outlines: 0 courtyard overlaps, core within \|x\| ≤ 37.0 mm, 686 mm² of courtyards. Requires the B.Cu bus (§3). |
| 24 | Needed if the bus stays on F.Cu |

Checks against these constraints (from the PCB session's place.py; I reviewed the render):
- **SW node:** 26 mm from Y1/C5/C6/C14/SENSE_ADC; ≥17 mm from CAN; 30 mm from LED_RET.
  - **5.9 mm from the SENSE bus (D1/R2): accepted.** The coupling is <0.1 pF into 10 nF (sub-mV), and discovery runs with the buck off.
- **Hot loop:** C16/C17 at U5 VIN. **C17's GND pad goes straight to U5's GND pin on F.Cu** (shortest loop), with its via into the GND lane in addition, not instead.
- **Tall parts** (L1 ~3 mm, U2, D5, U3) are ≥12 mm from the LEDs or below the LED row. L1 subtends ~12° from the board plane as seen from LED2/LED3, outside the SK6812's ~60° half-angle cone, so it causes no meaningful shading.
- **Thermal:** U3/R14 ≈12 mm from U5, with room for a VIN_LDO pour on both layers.

The optics test (A1) may still ask for a taller panel. A taller board only adds space.

---

## 10. Mechanical and fab constraints that touch the layout

- **Spring force:** ≈10 springs × 0.5–1.5 N ≈ 5–15 N per board, pushing toward the panel interior, concentrated in the 48 mm strip. The frame and snap fit take it; keep the frame's support features clear.
- **Breakaway tabs only on the top (diffuser) edge**, not on the wall edge or the ends. No V-score.
  - **Top-edge margin:** ≥1.0 mm copper-free on B.Cu along the whole length (the bus band, §3).
  - On F.Cu, keep ≥1.0 mm at each tab position (≈5 × 1 mm windows, between top-row parts).
  - **Tab spacing:** neither end may overhang the outermost tab by more than ~20 mm, so use ≥3 tabs on the 93.7 mm hexagon.
  - **MLCC crack rule:** no ceramic capacitor or crystal within **3 mm** of a tab window. Within 5 mm, orient its long axis parallel to the top edge. Snapping the tabs bends the board, and a cracked MLCC on +5V/+12V becomes a short.
  - **Placement check (14:05, re-measured on the board):** windows at x −31.5, −2.0, +30.0 (5 × 1 mm, y 21–22).
    - Nearest MLCC/crystal: 4.6 mm (C1), 4.1 mm (C14), 5.3 mm (C3). Passes.
    - Overhang outside the windows: 12.9 / 14.4 mm (hexagon), 7.0 / 8.5 mm (triangle). Passes.
    - **Resolved (14:20):** TP11 moved to (11.2, 19.7). Every pad is now ≥1.53 mm from every tab window (nearest R3), and TP11 is 1.3 mm from the nearest SENSE pad (R9.2).
    - **Routing condition:** TP11's pad sits over the B.Cu bus band (y 18.5–20.3). Its **+5V via must land in the +5V lane (y ≤ 18)**, reached by a short F.Cu trace, not under the pad. Otherwise +5V copper ends up among the DRIVE/SENSE bus traces on B.Cu.
    - D2 (BAT54S, SOT-23) at 2.2 mm from the −2 window is acceptable; leaded SOT parts aren't crack-prone like MLCCs.
  - **Tab nubs:** mouse-bite nubs (~0.3–0.5 mm) land on the top edge, which sits in the frame/diffuser groove. Sand them, or give the groove ≥0.5 mm relief at the tab positions.
- **Back reflector clearance (mechanical constraint):** parts sit down to y ≈ 0.6 mm on the inward face.
  - The tall ones are D5 (SMA, ≈2.3 mm), U2 (SOIC, ≈1.75 mm) and U3 (SOT-89, ≈1.5 mm); the TPs are flat.
  - The reflector must stop ≥2.5 mm short of the board face, or be notched at those parts (the notch avoids a dark slot along the edge).
  - This goes to the frame/reflector design.
- **Board thickness t = 1.6 mm ±10%:** it enters the length formula (decision 0004) and sets spring compression. State it on the fab order.
- **Single-sided assembly:** all components on F.Cu; B.Cu holds only pads and copper.
- **Light path:** no tall parts (L1, SOIC-8, SMA, crystal) between the LEDs and the panel interior.
- **Inward-face colour:** consider white solder mask (the board forms the panel's side wall).
- **Test points:** on a ≥2.54 mm grid, plus 2 NPTH tooling holes. +12V, +5V (TP11) and GND are on every board.
- **Panelization:** one kit per shape (decision 0004).

---

## 11. Open items needing a decision record or schematic change if adopted

Open:
1. Mating setback steps ≥0.5 mm (`EdgeContacts_SpringPads`, SPEC §3.3). With decision 0007 the final contact point must also stay ≤6.8 mm from the wall edge, so check both on the bridge prototype.
2. Back reflector clearance (§10), for the frame/reflector design.
3. Injection fuse ≤ the springs' and board's rating (SPEC §8). Above 5 A, the active board needs 1 oz inner copper (§13.2).
4. Optional ESD footprint at J1 on every board.
5. Add the SWPA4030S150MT datasheet to `docs/datasheets/` and confirm Isat and DCR (§7).

Closed:
- **Signal bus on B.Cu and H = 22 mm:** accepted by the user (decision 0005, SPEC V5.5).
- **4-layer:** active board only (decision 0006).
- **Active In2 stack:** GND under the bus band and the 1.6 mm thickness contract are adopted (decision 0006, SPEC V5.6).
- **Active inner copper: 0.5 oz** at a fuse of ≤5 A, from the measured plane (§13.2, 2026-11-16). The criterion and the "guard or ≥1.5 mm gap" rule are now in decision 0006 (follow-up section) and SPEC V5.7.2 §2. **This depends on the injection fuse being ≤5 A.** No rating is set yet (SPEC §8, open item 3 above).
- **Vias in J1 pad tops** (decision 0007) and the **LED_EN/LED_RET pin swap** (decision 0008) are folded into §2, §4–§6 and §13.
- **NPTH tooling holes** H1 (−29.2, 4.0) and H2 (+32.0, 4.0): Ø2.0, board-only footprints, ≥2.2 mm from the nearest pads (D5, R14), outside the strip and the triangle's corner pads.
- **Schematic items:** corner power-pad order and gaps; C4 moved to +5V; the EN pull-down; the +5V test point; the loop-back divider (now on PA6).

## 12. Assumptions

- 1 oz copper, FR4 εr 4.5, t = 1.6 mm, via plating 18–25 µm. Current capacity from IPC-2221 (external, 10 °C); vias treated as internal conductors, which is conservative.
- LED 0.2 W at 5 V (datasheet, decision 0003). Buck efficiency ~87 %. Spring rating ≈1 A each (unconfirmed).
- The hot-plug model is a series RLC with guessed L and R. Treat it as an order-of-magnitude figure.
- The tilt check assumes a straight, rigid edge and identical springs.
- Board height comes from the PCB session's placement trial (13:06), not from my earlier area estimate.
- Calculations were done in scratchpad scripts, not kept in the project.

---

## 13. ACTIVE board, 4-layer (decision 0006): what changes

This section applies to `hardware/edge-board/` only. The passive board keeps §1–§12 unchanged. Where they conflict, this section wins for the active board.

### 13.1 Stack-up
- **JLC standard 4-layer, 1.6 mm:** L1–L2 prepreg ≈0.21 mm, core ≈1.07 mm, L3–L4 prepreg ≈0.21 mm. Outer layers 1 oz, inner 0.5 oz by default (see §13.2).
- **Total thickness must be 1.6 mm ±10%, the same as the passive board.** t enters the board-length formula (decision 0004) and sets spring compression, so it's part of the interface contract. Same ENIG finish.
- **Layer roles** (decision 0006): F.Cu parts and signals; In1 solid GND; In2 power; B.Cu J1 pads, the bus band, extra routing and GND pour.
- **B.Cu sits only 0.21 mm from In2,** so **In2 is the reference plane for every B.Cu signal, including the bus band.** In1 is the reference for F.Cu.
  - A 0.25 mm trace over its plane is now ≈65 Ω and 0.9 pF/cm.
  - Still no impedance control needed.

### 13.2 Plane rules
| Layer | Rule |
|---|---|
| **In1 GND** | Solid, with no traces and no splits. Via antipads must not merge into slots: keep ≥0.3 mm of copper web between them, and stagger via rows such as the J1 signal-via row (y 8.5–9.5) and the bus drops. End to end it's ≈4.2 mΩ at 0.5 oz. |
| **In2 power**, from the wall edge up | **+12V region** (y ≈ 1.0 to ≈11.5) │ **GND guard ≥1.0 mm, or a copper-free gap ≥1.5 mm** where the guard can't stay continuous │ **+5V region** (≥3 mm, covering the LED VDD vias and the buck output) │ **GND region under the whole B.Cu bus band (y ≳ 18.2)**. The last band is **new**: B.Cu signals reference In2, so the bus must sit over GND, not over +5V. Gaps ≥0.5 mm between regions. Stitch the GND regions to In1 at ≤10 mm intervals. |
| **+12V region width / copper weight** | **0.5 oz passes when both of these hold:**<br>• **end-to-end resistance ≤ 10 mΩ.** That's a mean width of ≳9.5 mm after antipads, giving ≤50 mV and ≤0.25 W at 5 A.<br>• **No neck narrower than 6 mm, and none narrower than 8 mm that runs longer than 5 mm.** A short neck adds almost no resistance, and its heat spreads into the copper around it. For example, a 6 mm × 4 mm neck dissipates ≈15 mW at 5 A. The fuse's fusing margin is large (≈300 A for 10 ms).<br>**If either check fails, or the fuse is above 5 A, order 1 oz inner copper.**<br>**Measured on the routed active board (2026-11-16, 0.1 mm x step):** mean width 9.8 mm, **9.4 mΩ** (47 mV and 0.24 W at 5 A). Worst neck **6.25 mm over 3.7 mm** at x ≈ −29, caused by the H1 tooling hole. The next-worst necks are 7.15 mm over 1.6 mm and 7.6 mm over 3.3 mm (the corner via fields). The other necks come from the J1 GND via slots (decision 0007) and signal antipads, and none is below 8.5 mm. **Result: 0.5 oz inner, if the fuse is ≤5 A.** |
| **+12V never beside +5V** | Holds through the GND guard or the ≥1.5 mm gap on In2. On an inner layer a gap can't collect a solder bead or debris, so a wider empty gap is as good as a guard strip. Routed board: the guard is present for x > +0.4, and the west half has a 2.0 mm empty gap. Passes. On B.Cu and F.Cu, §1.2 still applies. |
| **Inner planes pulled back from the board edges** (routed board checked 2026-11-16: 1.0 mm wall, 0.5 mm ends and top edge. Passes.) | **≥1.0 mm from the wall edge** on In1 and In2. The wall edge is bevelled, and the springs ride over it during insertion. If +12V on In2 is exposed in the bevel, a GND spring passing over it shorts the bus, and exposed GND is the same risk in reverse. **≥0.5 mm from the board ends**, where a corner bead or strap could reach the end face. ≥0.3 mm (fab minimum) on the top edge. The +12V region therefore starts at y ≈ 1.0, not 0. |
| Gaps between In2 regions | ≥0.5 mm everywhere, including +5V → the GND band under the bus. That pair is benign (a short only trips the buck's current limit), but keep the margin. |
| B.Cu | J1 strip rules (§2) unchanged. Bus band position and order unchanged (interface contract). The rest of B.Cu is GND pour plus extra routing. Keep the top-edge copper-free strip (y 21–22). |

### 13.3 Via counts (0.3 mm drill, ≈0.7–0.9 A each, conservative)
| Connection | Current | Vias |
|---|---|---|
| **Corner +12V and GND pads → In2 / In1** | Full feed-through, 5 A target | **≥8 × 0.3 mm (or ≥6 × 0.4 mm) per pad, at both ends** |
| Corner +5V pad → In2 +5V | ≤0.6 A | ≥2 |
| J1 X2/X9 (+12V) → In2; X1/X3/X10 (GND) → In1 | ≈1 A each (one spring), plus brief fault current until the fuse opens | ≥4 per pad. Active board: in the pad top, row at y 7.65 (decision 0007) |
| U5 VIN, C16, C17 → +12V; U5 GND, C16/C17/C19/C20 GND → In1 | Buck pulse currents | ≥2 per pad, beside the pad |
| U3 tab (VIN_LDO) | Heat | Thermal vias into a VIN_LDO island on B.Cu are fine. Never connect it to a plane net. |
| LED VDD → +5V, LED GND → In1 | 40 mA | ≥1 each, 2 preferred |

- **No vias in the corner pads.** They're hand-soldered, and open vias wick the solder (plugged via-in-pad costs extra). Place the via fields just inboard of the pads.
  - Decision 0007: the user is fine with vias in hand-soldered pads. They still can't go in the +12V corner pad, because the F.Cu DRIVE/SENSE pads sit directly behind it, inside the 0.5 mm rule. The fields stay inboard.
  - **Triangle outline:** check that ≥8-via fields fit between the corner pads and the core edge (|x| ≤ 37.0), alongside the bus fan-out.
- **Hand soldering:** corner pads tied into planes sink more heat than on the 2-layer passive board, and a corner joint now joins one of each type. Plan a hotter iron or thermal-relief spokes (≥4 × 1 mm, still good for 5 A).

### 13.4 Rules that drop out on the active board
- The **GND hops** for X1/X3/X10 (including the shared X1+X3 hop and its F.Cu jog), the **B.Cu power lanes**, and the **lane jogs at the corners** (§3, §8). Power pads drop straight into their planes by via.
- Everything else in §2, §3's bus rules, §5–§10 still applies.

### 13.5 Buck with In1 GND directly underneath
- **Better than before:** the hot loop now closes through In1 0.21 mm below, a far smaller loop area. In1 also shields the SW node from In2 and B.Cu. The SW copper's capacitance to In1 is ≈2 pF per 10 mm², which is negligible.
- **Added rules:**
  - U5 GND pin, C16/C17 GND and C19/C20 GND each get ≥2 vias to In1 **right at the pad**. Keep the direct F.Cu link from C17's GND to U5's GND as well.
  - **In1 stays unbroken under the buck group** (U5, L1, C16–C20): no antipad clusters or slots under the hot loop or SW node.
  - FB (R17) still gets a Kelvin connection to U5's GND pin, not a nearby plane via.
  - The ≥10 mm SW distance rules (§6) stay. The current placement has 22 mm.
- **Crystal:** In1 under Y1/C5/C6 is fine and recommended. OSC trace capacitance to In1 is ≈0.2–0.5 pF, well inside the ~4 pF stray budget. Keep In2 under the crystal as static copper (GND or +12V), with no switching nodes.

### 13.6 Clamp rule on 4 layers
- **DRIVE ↔ +12V is still the one destructive short (§5).** On 4 layers there's a new path: a **DRIVE via passing through the In2 +12V region**, for example the X6 tap via at y ≈ 9, which can't avoid it. Only the via-to-plane antipad separates them.
- **Rule:** DRIVE vias inside the +12V region get **≥0.5 mm plane clearance** (a local clearance rule in KiCad), or move the layer change outside the region.
  - Routed board: the X6 DRIVE via at (2.5, 7.65) has 0.50 mm. Passes.
- Treat SENSE vias the same way (margin rule).
- **Extended margin rule:** give ≥0.5 mm via-to-plane clearance to every 3.3 V logic net with no series resistor that passes through the In2 +12V or +5V region (§5). On today's board these are:
  - **LED_EN** (now PA0, decision 0008): 2 vias in the +5V region;
  - CAN_TX, CAN_RX and CAN_RS: in the +12V region at y ≈ 9.1 and in the +5V region.
  - **Applied (2026-11-16):** the PCB session added the rule as `logic via vs In2 supply` in `edge-board.kicad_dru`. I re-measured: every non-power via near an In2 supply fill is at 0.50 mm. DRC shows 0 errors. After the refill the +12V plane is 9.5 mΩ with the same 6.25 mm worst neck, so 0.5 oz still holds.

  One custom rule covers all of them. Example: `(rule logic_via_supply (constraint clearance (min 0.5mm)) (condition "A.Type == 'Via' && B.Type == 'Zone' && B.Layer == 'In2.Cu' && (B.NetName == '+12V' || B.NetName == '+5V') && A.NetName != 'GND' && A.NetName != '+12V' && A.NetName != '+5V'"))`. This is a fab-defect margin, not a hard rule. Each via loses ≈0.4 mm more plane, which doesn't change the §13.2 result.
- CAN bus vias (CANH/CANL) and SENSE_EDGE/SPARE are fine at default clearance. The bus pins tolerate 16 V, and D1 blocks SENSE_EDGE.

### 13.7 Interface contract notes (from the constraints side)
In addition to decision 0006's list, both board types must match on:
- thickness (1.6 mm),
- J1's mask opening and finish,
- the corner pad copper (the strap or bead joins one of each type),
- the bus band order (CANH/CANL, DRIVE, SENSE from +5V up).

Tab windows may differ per board type and panel, but the MLCC ≥3 mm rule (§10) applies to both.
