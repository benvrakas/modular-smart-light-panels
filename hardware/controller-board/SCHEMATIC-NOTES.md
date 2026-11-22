# Controller board and V6 passive edge board: schematic notes

**Date:** 2026-11-16 · **Against:** SPEC V6.1.1, decisions 0001, 0003, 0008, 0009, 0010 · **Roadmap:** WP 1.1 and 1.2
**Update (same day):** the coordinator accepted the DRIVE open-drain driver (decision 0011, SPEC V6.2, both written by the coordinator) and decided the open questions (§11). F1, a per-panel PTC, was added on the controller's +24V input (§2.1).

These notes record the V6 schematic choices: what each part is, why it was chosen, and the calculations behind the values. Where a choice changed SPEC text, it was listed under [Proposed SPEC changes](#10-proposed-spec-changes-for-the-coordinator); the coordinator has applied those to SPEC V6.2.

## 0. Files

| File | What |
|---|---|
| `controller-board.kicad_sch` / `.kicad_pro` | New controller board schematic (4-layer board, no PCB yet). A2 sheet. |
| `../edge-board/edge-board-hex.kicad_sch` | Passive edge board, rewritten for V6. The V5 board is archived in `../archive/edge-board-v5/`. The square and triangle projects (`edge-board-square`, `edge-board-triangle`) use the same schematic. |
| `scripts/gen_v6_schematics.py` | **Source of both schematics.** The circuits are data in this script, which places the symbols and writes the files. Edit the script and re-run it; don't hand-edit the generated `.kicad_sch` files, or the next regeneration loses the edit. |
| `scripts/verify_v6.py` | Runs ERC on both boards, exports the netlists, and checks every net against the script's data. |
| `scripts/make_boms_v6.py` | Writes the JLCPCB BOMs and the stock check. |
| `bom/BOM_controller-board.csv`, `../edge-board/bom/BOM_edge_code0..5.csv` | JLCPCB BOMs (Comment, Designator, Footprint, LCSC). There is one edge BOM per edge code; the V5 BOMs moved to `bom/v5/`. |
| `bom/stock-check.csv` (both projects) | JLC assembly stock, jlcsearch stock and LCSC store stock per part. |
| `output/erc.rpt`, `output/*.net`, `output/*.pdf` (both projects) | ERC report, netlist and PDF plot. |
| `../lib/symbols/ModularLight.kicad_sym` | Added symbols: `ControllerJoint`, `EdgeContacts24V`, `CornerJoint24V`, `TCAN1044V`, `TLV431_DBZ` and a `+5V_LED` power symbol. The V5 symbols are unchanged, because the V5 schematic still uses them. |
| `../lib/footprints/ModularLight.pretty/` | Added footprints: `ControllerJoint_EdgeBoard` and `ControllerJoint_ControllerEdge`. |
| `../../docs/datasheets/` | Added datasheets: `TPS54360B.pdf`, `TCAN1044V.pdf`, `TLV431.pdf` and `NUP3105LT1G(DOWO).pdf`. |

**Results:**
- **ERC:** 0 errors and 0 warnings on both schematics (`--severity-all`).
- **Netlists:** all 42 controller nets and 15 edge-board nets match the script exactly. The only unconnected pin is U5 EN, which is deliberately open.
- **V5 schematic:** `hardware/archive/edge-board-v5/edge-board.kicad_sch` still passes ERC with 0 violations after the library additions; none of its files were touched.

## 1. Parts (controller board)

Stock is JLC assembly stock from the JLCPCB parts API on 2026-11-16. Nothing is below 500. jlcsearch and LCSC store figures are in `bom/stock-check.csv`.

| Ref | Function | Part | LCSC | JLC stock | Why |
|---|---|---|---|---|---|
| U1 | MCU | CH32V203F6P6 | C3040880 | 1,575 (extended) | Carried over (decision 0001). Pins follow decision 0008: PA0 LED_EN, PA6 loop-back, PA7 LED data. **Thin stock: buy rev A quantities early.** |
| Y1, C5, C6 | 8 MHz crystal, 15 pF loads | XL2EL89COI-111YLC-8M, CL10C150JB8NNNC | C2973805, C1644 | 184k, 1.0M | Carried over |
| U2 | CAN transceiver | TCAN1044VDRQ1 | C1852061 | 1,502 (extended) | Decision 0010: bus pins rated ±58 V; system ESD ±8 kV contact on its own. VCC from +5V, VIO from 3V3. STB (PA5) has an internal pull-up, so the part stays in standby until firmware drives STB low. The V5 47 k Rs resistor is dropped. **Thin stock.** |
| D4 | CAN TVS | NUP3105LT1G (DOWO) | C22390031 | 41,672 | See §5 |
| R12 + JP1 | CAN termination | 120 Ω + open solder jumper | C22787 | 2.4M | Carried over |
| U5 | 24 → 5 V buck | TPS54360BDDAR | C524806 | 40,089 | Decision 0010. Always on; EN is left open (see §2). |
| L1 | Buck inductor | FNR6045S220MT, 22 µH, Isat 2.2 A, 116 mΩ, 6 × 6 × 4.5 mm | C168080 | 12,251 | §2. The Sunlord SWPA6045S220MT (C83454) is no longer listed at LCSC. |
| D7 | Catch diode | SS36, 60 V 3 A, SMA | C2891719 | 9,343 | §2: 60 V covers the 45.4 V clamp |
| C16, C23 / C17 | Buck input | 10 µF 50 V 1206 X5R / 100 nF 50 V | C13585 / C14663 | 4.4M / 33M | 50 V is above the SMAJ28A's 45.4 V maximum clamp. §2 |
| C19, C20 | Buck output | 22 µF 25 V 0805 X5R | C45783 | 4.0M | §2 |
| R19, R16/R17, R20/C21/C22, C18 | RT, feedback, compensation, BOOT | 162 k; 53.6 k / 10.2 k; 4.7 k / 22 nF / 100 pF; 100 nF | C22815; C2930115 / C22772; C23162 / C21122 / C14858; C14663 | ≥9,241 | §2 |
| F1 | Per-panel resettable fuse, between joint pad 1 (+24V_IN) and +24V, upstream of D5 | mSMD050-60V (TECHFUSE), 1812 PPTC: hold 0.50 A, trip 1.0 A, 60 V, 100 A max | C70113 | 142,252 | §2.1. Coordinator decision 2026-11-16: a failed TVS or a controller short should trip this panel's fuse, not the domain fuse. |
| D5 | Supply TVS | SMAJ28A-13-F | C134977 | 12,171 | Decision 0010 |
| U3, C12, C13 | 3.3 V LDO | HT7533-1 from +5V, 10 µF in and out | C14289, C15850 | 290k | Decision 0010: dissipates ≈50 mW at 5 V in; the 68 Ω resistor is removed |
| U6, R24, R25 | 3V3 over-voltage shunt | TLV431AIDBZR, 187 k / 100 k (trips at 3.56 V) | C56765, C22896, C25803 | 35k | §4.3. New. |
| Q1 | LED-rail high-side switch | AO3401A (P-MOSFET, −30 V, −4 A, 60 mΩ at −4.5 V), JLC basic part | C15127 | 1.49M | §3 |
| Q2 | Q1 gate driver | 2N7002, JLC basic part | C8545 | 6.2M | §3 |
| R21, R22, C25, R18 | Q1 gate network | 100 k pull-up, 22 k, 22 nF gate-drain, 100 k pull-down on PA0 | C25803, C31850, C21122 | basic | §3 |
| U4, C15, R5 | LED data level shifter, 33 Ω | SN74AHCT1G125 (UMW) | C20617903 | 16,173 | Carried over. **Now powered from +5V_LED** (§3). |
| R7 / R8 | Loop-back divider | 2.2 k / 3.3 k | C4190 / C22978 | basic | Carried over: PA6 is not 5 V tolerant (decision 0008) |
| R9, R10 | SENSE pull-up / series | 10 k 0805 (was 10 k + 1 k 0603) | C17414 | 47M | §4 |
| C14, D2 | ADC filter and clamp | 10 nF; BAT54S | C57112; C47546 | 5.1M; 239k | Carried over |
| Q3, R11, R23 | DRIVE open-drain driver | 2N7002 + 470 Ω 1206 + 100 k gate pull-down | C8545, C4502, C25803 | basic, 197k | §4. New. The V5 BAT54S on DRIVE (D3) is gone. |
| D6 | SENSE/DRIVE bus ESD | NUP3105LT1G (same part as D4) | C22390031 | 41,672 | §4.4 |
| R26 | SPARE → PB1 option | 10 k, DNP | C25804 | basic | Lets SPARE become a GPIO later. 10 k keeps a 24 V fault on SPARE at 2 mA and 58 mW. |
| J1 | Controller joint | 10 edge pads | none | n/a | §6 |
| TP1–TP13 | Test pads | SPARE, +3V3, GND, SWDIO, SWCLK, NRST, UART TX/RX, PB1, +24V_IN (TP10, before F1), +5V, +5V_LED, +24V (TP13, after F1) | none | n/a | Pogo jig (SPEC §3.2). TP12 and TP13 are new. TP10 sits before F1, so a jig powering the board through it also exercises F1, as in service. |

## 2. TPS54360B buck: 24 V → 5 V, sized for 1 A

The method follows TI datasheet SNVSB93 §8.2.2. The design point is VOUT 5 V and IOUT 1.0 A (0.73 A of LEDs, ≤0.1 A of logic with the CAN transceiver dominant, plus margin).

**Input voltage, set by the bus:**
- 24 V nominal, operating range 18–28 V. 28 V is the SMAJ28A standoff, the highest steady bus voltage.
- Transients up to 45.4 V, the SMAJ28A's maximum clamp.

| Step | Calculation | Result |
|---|---|---|
| Switching frequency | Eq. 25 (pulse skipping) at 45.4 V gives a maximum of 936 kHz. Eq. 26 (foldback) gives 1.75 MHz. TI's own design uses 600 kHz. | **600 kHz**. RT = 101756 / 600^1.008 = 161 k → **R19 = 162 k** (597 kHz) |
| Inductor | L_min = (28 − 5) / (1 A × 0.3) × 5 / (28 V × 600 kHz) = 22.8 µH | **L1 = 22 µH.** Ripple 0.27 A (18 V) to 0.34 A (45 V), always above TI's 150 mA minimum. Peak 1.17 A, RMS 1.00 A. FNR6045S: Isat 2.2 A, rated 2 A. |
| Isat versus current limit | TI's most conservative choice is Isat ≥ 5.5 A (the switch limit), which would need a ≈10 × 10 mm part. A 2.2 A part covers every normal condition, including soft start with ≈60 µF on the rail. | In a hard +5V short the inductor saturates during the current-limit delay (60 ns), then frequency foldback and hiccup take over. This is accepted and should be checked once on the prototype with a +5V short. |
| C_OUT, load step | Eq. 32 with ΔI = 0.73 A (all LEDs switching) and ΔV = 0.2 V (4 %) | ≥12.2 µF |
| C_OUT, unload overshoot | Eq. 33, 0.8 → 0.07 A, 5.2 V peak | ≥6.8 µF |
| C_OUT, ripple | Eq. 34, 25 mV (0.5 %) | ≥2.6 µF, ESR < 80 mΩ |
| C_OUT chosen | 2 × 22 µF 25 V 0805 X5R, ≈12 µF each after DC bias at 5 V | **≈24 µF effective** |
| Feedback | R_HS = 10.2 k × (5 − 0.8) / 0.8 = 53.55 k | **R16 = 53.6 k, R17 = 10.2 k** (TI values): 5.004 V, 78 µA |
| Modulator pole and ESR zero | f_p = 1 A / (2π × 5 V × 24 µF) = 1.33 kHz; f_z = 1 / (2π × 1.5 mΩ × 24 µF) = 4.4 MHz | |
| Crossover | min(√(f_p·f_z) = 77 kHz, √(f_p·f_sw/2) = 19.9 kHz) | f_co ≈ 20 kHz |
| R_comp (Eq. 48) | (2π × 20 kHz × 24 µF / 12 A/V) × (5 / (0.8 × 350 µS)) = 4.48 k | **R20 = 4.7 k**, basic part (f_co = 20.9 kHz) |
| C_comp (Eq. 49) | 1 / (2π × 4.7 k × 1.33 kHz) = 25.5 nF | **C21 = 22 nF**, basic part (zero at 1.54 kHz) |
| C_hf (Eqs. 50 and 51) | max(7.7 pF, 1 / (4.7 k × 600 kHz × π) = 113 pF) | **C22 = 100 pF** |
| With the LED rail on | The edge boards add ≈30–35 µF behind Q1 (6 × 10 µF X5R at 5 V, plus 18 × 100 nF) | f_co falls to ≈9 kHz, still well above f_p. Stable; load-step test it on the prototype. |
| C_IN | ≥3 µF effective and rated above V_IN max. I_rms = 0.45 A at 18 V; ΔV_IN = 1 A × 0.25 / (6 µF × 600 kHz) = 69 mV | **2 × 10 µF 50 V 1206** (≈3 µF each at 24 V) **+ 100 nF** at the pin |
| Catch diode | V_R ≥ 45.4 V; average current ≈0.8 A | **SS36** (60 V 3 A). Loss ≈0.36 W at 24 V and 0.8 A (conduction plus ≈45 mW from C_j). |
| BOOT | 0.1 µF, ≥10 V | C18 = 100 nF 50 V |
| UVLO / EN | EN open, so the internal pull-up keeps the buck always on; internal UVLO is 4.3 V | No divider. **Why:** the LED rail is off at power-up, so the start-up load is tiny, and an adjustable UVLO would only reset the MCU when an overloaded domain sags. A divider (R_UVLO1/2 per Eqs. 40 and 41) can be added if bus droop ever causes start-stop cycling. |
| Minimum V_IN | Eq. 43 | 5.3 V |
| Losses at 24 V, 0.8 A | IC (conduction, switching, gate drive, quiescent) 0.14 W; diode 0.36 W; inductor DCR 0.07 W | ≈0.57 W in total, η ≈ 87.5 %. IC junction rise ≈6 °C (42 °C/W). |
| Standby | Eco-mode: 146 µA quiescent plus 78 µA in the feedback divider | A few mW |

**Rating check:** everything on +24V is rated ≥50 V, above the 45.4 V clamp.

| Part | Rating |
|---|---|
| F1 | 60 V |
| U5 | 60 V |
| D7 | 60 V |
| C16, C17, C23 | 50 V |
| D5 | the clamp itself |
| D4, D6 | 36 V standoff; not on +24V |

### 2.1 Per-panel PTC (F1)

**Placement:** J1 pad 1 (net +24V_IN) → F1 → +24V (D5, C16/C23/C17, U5). D5 sits downstream, so a TVS that fails short, or any short on the controller, trips F1 and only this panel goes dark.

**Requirements and how mSMD050-60V meets them:**

| Requirement | mSMD050-60V | Check |
|---|---|---|
| Voltage ≥30 V, higher preferred | **60 V** | Above the 45.4 V clamp. When F1 has tripped it sees the full bus voltage, including transients. |
| Hold ≥0.3 A | **0.50 A at 25 °C**; datasheet derating 0.45 A at 40 °C, 0.43 A at 50 °C, 0.35 A at 60 °C, 0.30 A at 70 °C | Below |
| Trip ≤≈1 A | **1.0 A** | Matches |
| Interrupt rating | **100 A** | Covers a hard short fed from the bus |
| Package, stock | 1812, 142k JLC stock, ≈$0.09 | 1206 PTCs at ≥30 V top out at 0.25 A hold with 0.5 A trip (nSMD025-30V), or 0.35 A at 30 V (JK-NSMD035-30V, 16k stock), which is too tight after derating. 1812 is the right size. |

**Does the hold current cover the load?**

| Case | Current at F1 | Hold at 60 °C (0.35 A) |
|---|---|---|
| Full RGBW plus logic, 24 V bus | ≈4.9 W / 24 V = **0.20 A** | 57 % |
| Same, bus sagging to 18 V | **0.27 A** | 77 %; the 70 °C hold of 0.30 A still covers it |
| Standby | mA | n/a |

**Does the hold current cover start-up?**
- **Hot-plug charge into C16/C23/C17** (≈7 µF effective): ≈0.17 mC within microseconds, an I²t around 0.01 A²s. F1 needs ≈10 A²s to trip (0.15 s at 8 A). No effect.
- **Buck soft start:** ≈1.75 ms at 600 kHz (2.1 ms at 500 kHz, scaling with the clock). Even charging the coordinator's 45 µF to 5 V in that time takes 0.13 A at 5 V, ≈0.03 A at 24 V. The LED rail is off at power-up, so the real load is ≈30 µF and logic only.
- **LED-rail turn-on later:** the 0.9 ms soft start (§3) adds ≈0.2 A at 5 V, ≈0.05 A at 24 V, on top of the LED load.

The peak is ≈0.3 A for under 1 ms, far below F1's trip energy.

**Cost:** 0.15 Ω initial resistance (1 Ω maximum after a trip) costs ≤0.27 V of drop and ≤73 mW, which the buck absorbs.

**Selectivity against the domain fuse** (for the injection-bridge design):
- **The concern:** a hard short draws tens of amps through F1 and the injection fuse together. F1 trips in milliseconds, but a fast-acting 5 A domain fuse also clears in a few milliseconds at 30 A, so which one opens first is not guaranteed.
- **Recommendation:** make the injection fuse a **time-lag (slow-blow) type**, so the panel PTC always opens first. The bridge's spring and lane resistance also limits the short current.

## 3. LED-rail switch (Q1/Q2) and data

**Circuit:**
- **Q1 (AO3401A):** source on +5V, drain on +5V_LED. R21 (100 k) pulls the gate to +5V, so the rail is **off by default**.
- **Q2 (2N7002):** gate on PA0 (LED_EN), with R18 (100 k) to GND, so the rail stays off while PA0 floats during reset and boot. Q2 pulls Q1's gate down through R22 (22 k).

| Item | Value |
|---|---|
| V_GS when on | 5 V × 22 / 122 = 0.9 V at the gate, so V_GS = −4.1 V and R_DS(on) ≈ 60 mΩ |
| Loss at 0.73 A | 32 mW. Q1 is rated 4 A, against the ≥2 A asked for. |
| Turn-on slew | C25 (22 nF, gate to drain) sets a Miller plateau current of ≈127 µA → 5.8 V/ms, a **≈0.9 ms ramp**. Inrush into ≈35 µF of LED-rail capacitance is ≈0.2 A. Without C25 the inrush would be several amps and would dip +5V, which feeds the MCU's LDO and the CAN transceiver. |
| Turn-off | Only 18 µA through R21 charges the gate, a ≈6 ms ramp. **Firmware: send all-zero LED data before switching the rail off.** The rail then carries only the LEDs' idle current (≈1 mA each). |

**U4 (AHCT level shifter) now runs from +5V_LED:**
- **Why:** on the always-on +5V it could drive 5 V into LED1's DIN while the LEDs are unpowered, back-powering them through the input clamp.
- **Result:** the V5 firmware rule "hold PA7 low while the LED rail is off" is no longer needed for the LEDs.
- **Recommendation:** firmware should still hold PA7 low with the rail off, because the UMW clone's input current when unpowered is not specified. It costs nothing.

**Loop-back:** unchanged. LED_RETURN → 2.2 k / 3.3 k → PA6 (decision 0008).

## 4. SENSE / DRIVE: 24 V fault analysis (R10 / R11)

### 4.1 Why one resistor can't do it on DRIVE
In V5, DRIVE was a GPIO (PA4) behind R11 = 100 Ω, with a BAT54S clamp to 3V3.

**A sustained DRIVE short to +24V in that design:**
- (24 − 3.6) / 100 Ω = 204 mA through R11, 4.2 W, which burns it.
- All of that current goes into 3V3.

**What a resistor alone would need:**

| Requirement | Needs |
|---|---|
| Survive in 0603 | R11 ≥ 10 k |
| Keep injection ≤5 mA | R11 ≥ 4 k |
| Read code 0 correctly | R11 ≲ 0.5–1 k |

No single resistor meets all three. **Chosen fix: drive DRIVE with an open-drain N-MOSFET** (Q3, 2N7002, 60 V) through **R11 = 470 Ω 1206**, gate on PA4 with R23 (100 k) to GND.
- **Idle:** Q3 is off and the DRIVE bus floats (Hi-Z, exactly as the SPEC wants). A sustained short to +24V draws **no current**, so nothing heats and nothing is injected into 3V3.
- **While this panel drives DRIVE low into a short:** 24 V / 490 Ω = 49 mA and 1.13 W in R11 (57 mA and 1.53 W at 28 V). This only lasts as long as the discovery slot. **Firmware: assert DRIVE for ≤5 ms per slot.** A 1206 thick-film resistor takes ms pulses of that size; Q3 sees 49 mA, within 115 mA.
- **Normal operation:** the MCU never drives DRIVE high (the SPEC says Hi-Z or low only), so an open-drain driver loses nothing. PA4 no longer touches the bus at all.

**R11 value against the codes.** V_ADC = Vf + (3.3 − Vf) × R / (10 k + R), with Vf = 0.55 V and R = R_k + R11 + ≈20 Ω for Q3:

| Code | R_k | V_ADC with V5 100 Ω | V_ADC with 470 Ω |
|---|---|---|---|
| 0 | 0 | 0.58 V | **0.68 V** |
| 1 | 1 k | 0.83 V | 0.91 V |
| 2 | 2.7 k | 1.16 V | 1.22 V |
| 3 | 5.6 k | 1.55 V | 1.59 V |
| 4 | 12 k | 2.06 V | 2.08 V |
| 5 | 27 k | 2.56 V | 2.57 V |
| idle | none | 3.30 V | 3.30 V |

- **Gaps:** the smallest gap (code 0 to 1) shrinks from 244 to 228 mV. All codes stay separated, and thresholds get calibrated on hardware anyway (SPEC §10 item 10).
- **Q3's on-resistance:** the 2N7002's V_GS(th) can be up to 2.5 V, so at 3.3 V drive it adds tens of ohms, which shows up as a few mV of code-0 offset. If calibration shows scatter, change Q3 to a logic-level part (for example 2N7002K, C22379475).

### 4.2 SENSE
**Change:** R10 goes from 1 k to **10 k**, and R9 (R_pu, 10 k) moves to 0805. Both are now 0805 (125 mW).

**A sustained SENSE short to +24V:**

| Resistor | At 24 V | At 28 V |
|---|---|---|
| R10 (into the D2 clamp) | (24 − 3.6) / 10 k = 2.0 mA, 42 mW | 2.4 mA, 60 mW (48 % of rating) |
| R9 (into 3V3) | 2.1 mA, 43 mW | 2.5 mA, 61 mW |

The total injected into 3V3 is **4.1 mA at 24 V, 4.9 mA at 28 V**. The ADC pin itself sees only the D2 current, within its ±5 mA injection limit.

**Cost of raising R10 to 10 k:**
- **Settling:** the ADC node's settling time constant grows to ≈100–170 µs, so **firmware must wait ≥1 ms after DRIVE goes low** (it was ≥0.5 ms).
- **DC error:** ADC pin leakage (≤1 µA) and warm BAT54S leakage give ≤10–20 mV through 10 k, which calibration absorbs.

### 4.3 3V3 over-voltage shunt (U6)
- **Why it is needed:** the HT7533 cannot sink current. In standby the MCU sits in STOP mode (tens of µA) and the TCAN1044V in standby (µA), so the ≈5 mA from a SENSE short would pump 3V3 above the CH32V203's 4.0 V absolute maximum (datasheet Table 4-1).
- **Fix:** U6 (TLV431A) with R24/R25 (187 k / 100 k) clamps 3V3 at **3.56 V**. Tolerance ≈3.49–3.63 V, above the HT7533's maximum output and below 4.0 V. It sinks up to 15 mA.
- **Cost:** ≈12 µA standby.
- **Alternative:** a 680 Ω bleeder would cost 16 mW per panel, permanently.
- **If the coordinator prefers fewer parts:** drop U6/R24/R25 and accept that a SENSE-to-24V PCB defect can damage the MCU in standby. SENSE is never adjacent to +24V on the joint or the corners, and SENSE_EDGE sits behind D1.

### 4.4 ESD on the buses (D6)
- **Problem:** the D3 clamp is gone, and SENSE now has 10 k in series. The exposed seam contacts reach the buses.
- **Fix:** D6, the same NUP3105L as the CAN TVS (one BOM line), clamps SENSE and DRIVE to GND.
- **Fault tolerance:** its 36 V standoff means a sustained 24–28 V fault does not make it conduct.
- **Load on SENSE:** ≤0.5 µA leakage on the 10 k SENSE node is ≤5 mV.

### 4.5 What this does to the layout rule "DRIVE never adjacent to +24V"
- **The rule's reason is gone.** The rule existed because the short was destructive. With Q3 a DRIVE-to-24V short is not destructive: idle it draws nothing, and while driving it is a 1.1 W pulse lasting milliseconds.
- **A SENSE short is now survivable too.**
- **Proposal:** downgrade both to "prefer, where free".
- **On the controller joint,** DRIVE is still kept away from +24V, because it costs nothing there.

## 5. CAN TVS choice: NUP3105LT1G (DOWO, C22390031)

**Requirements:**
- **No conduction at the highest sustained fault voltage,** a CAN wire shorted to a +24V bus at up to 28 V. A TVS that conducts there burns. PESD2CAN (24 V standoff) and PESD1CAN / CDSOT23-T24CAN (24 V) fail this.
- **Clamp at ESD and surge levels near or below the TCAN1044V's ±58 V bus rating.**
- **Low capacitance:** up to ≈50 nodes share the segment.

**The part:** dual bidirectional TVS, SOT-23, the NUP2105L pinout (pins 1/2 lines, pin 3 GND).
- V_RWM 36 V, V_BR ≥ 40 V
- V_C ≤ 60 V at 6 A (8/20 µs)
- C_j 12–16 pF
- 41.7k JLC stock, $0.04

The onsemi original NUP3105L (32 V, ≈30 pF) and other clones (MSKSEMI C7379986, 36 V; TECH PUBLIC C2931121, 32 V, low stock) also fit.

| Alternative | Why not |
|---|---|
| PESD36VS2UT (C3001943) | Unidirectional, 60 V at only 2.5 A, 3k stock |
| PESD1CANFD36 | DFN1006 single-line: two tiny parts per bus |

**Margins:**
- 60 V at 6 A is 2 V above the transceiver's DC rating. The transceiver is itself rated ±8 kV IEC contact and ISO 7637 pulses up to +100 / −150 V, so the TVS is a second line of defence.
- **Bus load:** 50 nodes × (16 pF + 20 pF transceiver) ≈1.8 nF per line. Against 60 Ω that is a time constant of ≈0.1 µs, against a 4 µs bit at 250 kbps.

## 6. Controller joint: pin order, footprints and mapping

### 6.1 Order (pads 1 → 10)

| Pad | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Net | **+24V** | **GND** | +5V_LED | LED_RETURN | LED_DATA_OUT | SPARE | CANH | CANL | SENSE | DRIVE |

On the controller, pad 1's net is named +24V_IN, because it reaches the board's +24V through F1 (§2.1). The joint interface is still "+24V".

Rules, each with its reason. A drag-soldered joint's likely defect is a bridge between neighbouring pads, so each rule is about what a neighbour short does.

1. **+24V at an end, with GND as its only neighbour.**
   - **Reason:** a 24 V short damages almost every other net.
     - +5V_LED: 24 V on every LED and on U4.
     - LED_DATA_OUT: U4's output and LED1's DIN.
     - LED_RETURN: the last LED's DOUT, and PA6 through 2.2 k (≈9 mA, above the 5 mA injection limit).
   - Only GND, CAN (±58 V), SPARE (a test pad) and, after §4, SENSE and DRIVE tolerate it. An end position gives +24V just one neighbour.
2. **+24V never beside +5V_LED without GND between.** This is the SPEC rule: a short would put 24 V on every LED. It is satisfied by rule 1.
3. **DRIVE never beside +24V.** It sits at the far end (pad 10). With the §4 driver this is no longer destructive, but it costs nothing here.
4. **+5V_LED next to GND.**
   - **Reason:** the LED current (0.73 A) and its return run side by side, the smallest loop.
   - **Neighbour short:** a +5V_LED short to LED_RETURN is harmless, because the 2.2 k / 3.3 k divider is designed for 5 V.
5. **LED_DATA_OUT not beside +5V_LED.**
   - **Reason:** a bridge there would hold U4's output against 5 V through 33 Ω (≈150 mA when low).
   - Its neighbours are LED_RETURN (a short there only loops the chain, no damage) and SPARE (unused).
6. **CANH and CANL adjacent:** the differential pair stays together. A preference, not a hard rule.
7. **SENSE beside DRIVE:**
   - **Short:** it makes the panel's own discovery wrong, but does no damage.
   - **Detection:** the jig's isolation test finds it.

### 6.2 Footprints and pitch

**Pitch:**
- **2.54 mm, with 1.3 mm pads and 1.24 mm gaps.**
- **Why 2.54 mm:** the wider of the 2.0–2.54 mm options gives the largest gap for drag soldering, and the joint still spans only ≈24.2 mm of the ≤72 mm base.
- **Paste:** both footprints have paste openings, so reflow pre-tins the pads and the hand joint needs only flux and an iron.

**Edge board, `ControllerJoint_EdgeBoard` (J4):** on the inward face (F.Cu).
- **Pads:** 1.3 × 3.5 mm.
- **Band:** they cover the controller's 1.6 mm thickness plus ≈1.5 mm of fillet land on the wall side (Dwgs.User lines in the footprint).
- **Placeholder:** the height of the pad row above the wall edge depends on the back-plate pocket depth.
- **No vias needed:** the nets route away on F.Cu. That matters because the joint row overlaps the height of the B.Cu contact strip, where vias are banned.

**Controller board, `ControllerJoint_ControllerEdge` (J1):** plain edge pads, 1.3 × 2.0 mm, on F.Cu (the parts side, which faces the wall), running to the board edge.
- **No B.Cu pads:** that face stays plain white mask.
- **No castellation:**
  - It costs extra at JLC.
  - It would put copper on the white reflector face.
  - The joint carries no load (the snap fit holds the board).
- **Fillet:** forms on the wall side between J1 and J4.
- **Fallback:** if one-sided fillets prove weak, add castellated holes later.
- **Edge clearance:** the PCB needs a local copper-to-edge clearance rule for these pads.

### 6.3 How pad 1 maps to pad 1
Each footprint is drawn **as seen from its own copper side, with the joint edge at the bottom**:
- For J4, that is the edge board's inward face, with the wall edge down.
- For J1, that is the controller's wall side, with the trapezoid base down.

**Why that works:**
- **The edge board:** looking at its inward face from inside the panel, with the wall edge down, "right" is direction −x along the board.
- **The controller:** looking at its wall side from the wall, with the base toward the edge board (down), "right" is also −x.
- **So:** pad 1 is the leftmost pad in both footprints and lands on pad 1, pad 10 on pad 10. The two footprints use **the same numbering, not mirrored**.
- **The one condition:** **J1 must be on the same copper side as the controller's parts** (the wall side). If the PCB session flips the parts to B.Cu, flipping J1 with them keeps the mapping.
- Both footprint descriptions and the `ControllerJoint` symbol say this, and both boards use the same symbol, so the schematic pin numbers also match.

## 7. Passive edge board changes (V6)

- **+12V → +24V:**
  - The edge contacts (X2, X9), the corner joints (pad 6) and TP10.
  - New symbols `EdgeContacts24V` and `CornerJoint24V`, with the same footprints and pad numbers as V5.
- **+5V → +5V_LED,** the switched rail from the controller.
  - **Parts on it:** LED1–3 VDD, C1–C3 (100 nF, one per LED), C4 (10 µF) and TP11.
  - **Corner pad order:** still +5V_LED / GND / +24V. That order is set by the `CornerJoint_L/_R` footprints, which are unchanged; their geometry is a placeholder until the PCB session re-lays them out for the new board height.
- **New J4** (controller-joint pads, §6), on every board, used only on code 0.
- **New R3:** the code-0 link (§8).
- **Unchanged:**
  - D1 (1N4148WS) + R1 (R_ID) + R2 (0 Ω DNP bypass).
  - J1/J2/J3 footprints.
  - LED part and footprint.
  - References from V5: LED1–3, C1–C4, D1, R1, R2, J1–J3, TP1, TP3, TP10, TP11.
- **BOMs:** one per code. R1 is 0R, 1k, 2k7, 5k6, 12k or 27k (C21189, C21190, C13167, C23189, C22790, C22967). R3 is fitted on codes 1–5 and DNP on code 0.
- **Stock:** the lowest JLC stock is the 27 k at 528k; the LED is at 47.5k.

## 8. Code-0 population option

The simplest option is one link and two hard-wired nets:
- **J4.4 (LED_RETURN) is wired to D_IN,** the corner-IN D pad.
- **J4.5 (LED_DATA_OUT) is wired to LED1's DIN.**
- **R3 (0 Ω 0603) joins D_IN to LED1's DIN.**

| Variant | R1 | R3 | Result |
|---|---|---|---|
| Codes 1–5 | 1k … 27k | **fitted** | The corner-IN data feeds LED1, as before. J4 is unused: bare pads, a few mm of stub. |
| Code 0 | **0 Ω** | **DNP** | The controller feeds LED1 through J4.5. The panel's last LED (arriving at the corner-IN D pad) returns to the controller through J4.4. |

**Why only one link:**
- On boards 1–5 no controller is soldered to J4, so its pads can stay wired to the data nets. That avoids two extra 0 Ω parts per board, which the brief allowed.
- Soldering a controller onto a code 1–5 board would make U4 fight the previous LED's DOUT. The R1 code identifies the code-0 board, and the assembly note says to join the controller only there.

## 9. Rules introduced here, each with its reason

| Rule | Reason |
|---|---|
| Firmware asserts DRIVE for ≤5 ms per slot | Limits R11's pulse into a DRIVE-to-24V short (§4.1) |
| Firmware waits ≥1 ms after DRIVE goes low before reading SENSE | R10 = 10 k slows the ADC node (§4.2) |
| Firmware blanks the LEDs before switching the rail off | Q1's slow turn-off ramp (§3) |
| J1 sits on the controller's parts side | Keeps the pad-1 mapping (§6.3) |
| +24V copper is only adjacent to GND or 24 V-tolerant nets (CAN, SPARE, SENSE, DRIVE), never to +5V_LED, LED data or LED return | The same reason as the SPEC's +24V-to-+5V rule: those nets reach LED inputs or logic that 24 V destroys. This is that rule generalised; the coordinator decides whether the SPEC adopts it. |
| No vias in J4's nets inside the contact-strip zone | Already a SPEC rule (the B.Cu strip bans vias); it is noted here because J4 sits at that height |

**Rules dropped:**
- "Hold PA7 low while the LED rail is off" becomes a recommendation, not a requirement (§3).
- "DRIVE never adjacent to +24V" becomes a preference (§4.5).

## 10. Proposed SPEC changes (for the coordinator)

> **Status:** applied by the coordinator in SPEC V6.2 / decision 0011. One item is new since then and not yet in the SPEC:
> - **§3.2 Protection row:** "**F1 per-panel PTC, mSMD050-60V** (C70113, 1812, 0.5 A hold, 1.0 A trip, 60 V), between the joint's +24V pad and everything else, upstream of the SMAJ28A."
> - **§3.2 Debug row:** TP10 sits before F1; TP13 is +24V after it.
> - **§8, injection bridge:** "the injection fuse is a time-lag type so the panel PTC opens first" (§2.1).

**§3.2 table:**

| Row | Change |
|---|---|
| Protection | "CAN TVS: **NUP3105LT1G** (DOWO C22390031, 36 V standoff, ≤60 V at 6 A, 16 pF), also used on SENSE/DRIVE (D6). SENSE: R_pu and R10 both **10 kΩ 0805**, BAT54S on the ADC side. **DRIVE: open-drain 2N7002 (gate PA4, 100 k pull-down) + R11 470 Ω 1206**; the DRIVE-side BAT54S is removed. **3V3 shunt TLV431A trips at 3.56 V**, sinking fault current injected into 3V3." |
| 5 V rail | Add "fsw 600 kHz (RT 162 k), L 22 µH (FNR6045S220MT), C_OUT 2 × 22 µF, FB 53.6 k / 10.2 k, compensation 4.7 k + 22 nF ∥ 100 pF, SS36 catch diode, C_IN 2 × 10 µF 50 V + 100 nF, EN open." |
| LED rail switch | "**AO3401A** (C15127, −4 A, 60 mΩ) driven by a 2N7002 from PA0. Gate network: 100 k pull-up, 22 k, 22 nF gate-drain for a ≈0.9 ms soft start. Default off (100 k pull-down on PA0)." This replaces "≥1 A, part to be chosen". |
| Level shifter | "powered from **+5V_LED**, OE̅ to GND". Change "Firmware should hold PA7 low…" to "recommended". |
| Debug | Add a +5V_LED test pad. |
| Joint | "10 pads at **2.54 mm**, order +24V, GND, +5V_LED, LED_RETURN, LED_DATA_OUT, SPARE, CANH, CANL, SENSE, DRIVE. Pad n meets pad n (footprints ControllerJoint_EdgeBoard / _ControllerEdge, each drawn from its own copper side with the joint edge down). Pads on the controller's parts side only." |

**§3.4:**
- Rename "+5V (LED rail)" to "+5V_LED".
- Population option: "**R3 (0 Ω) from the corner-IN D pad to LED1 DIN: fitted on codes 1–5, DNP on code 0**. The joint's LED_RETURN pad is wired to the corner-IN D pad and its LED_DATA_OUT pad to LED1 DIN."

**§3.5:**
- Edge board parts: add R3 and "controller-joint pads: 10 at 2.54 mm (J4)".
- Controller board: "parts on F.Cu (the wall side)".

**§4.1:**
- "DRIVE … driven by an **open-drain N-MOSFET (PA4) through 470 Ω**, off (Hi-Z) when idle."
- "ADC input: **10 kΩ** series + 10 nF."
- Add: "Firmware asserts DRIVE ≤5 ms and samples ≥1 ms after."

**§4.2:**
- Update the table to code 0 ≈0.68, 1 ≈0.91, 2 ≈1.22, 3 ≈1.59, 4 ≈2.08, 5 ≈2.57 V (V_f 0.55 V; calibrate).

**§2 / §3.3:**
- Demote "DRIVE never adjacent to +24V" from "destructive" to a preference (§4.5).
- Optionally generalise the +24V/+5V rule as in §9.

**§10:**
- Close item 15 (R10/R11 and the CAN TVS) and item 16 (LED-rail switch).

**Decision record:** the DRIVE open-drain driver, the 3V3 shunt and the R10 change alter SPEC §4.1, so they need a decision record (proposed 0011, "24 V fault protection on the controller board").

## 11. Open questions

**Decided by the coordinator, 2026-11-16:**

| # | Question | Decision |
|---|---|---|
| 1 | Back-plate pocket depth / inductor | **Keep FNR6045S220MT (4.5 mm).** The 2.8 mm alternative's 1.45 A Isat would saturate in a +5V short. The pocket will be ≥5 mm. |
| 2 | U6 3V3 shunt | **Keep** |
| 3 | DRIVE open-drain driver | **Accepted:** decision 0011, SPEC V6.2 |
| 5 | Per-panel fuse | **Added:** F1, §2.1 |
| 6 | CAN termination burning in a CAN-to-24V short | **Risk accepted** |

**Still open:**
- Item 4: Q3 threshold.
- Item 7: L1 saturation test on the prototype.
- Item 8: thin stock on the MCU and the CAN transceiver.
- New: **the injection-bridge fuse should be time-lag**, so F1 opens first (§2.1).

The original list, kept for reference:

1. **Back-plate pocket depth.**
   - **Tallest parts:** L1 (4.5 mm), SS36 and SMAJ28A (SMA, ≈2.3 mm), SOIC-8 (1.75 mm).
   - **What it sets:** the pocket must be ≥5 mm deep, or L1 can change to a lower 22 µH part (for example SMNR6028-220MT, 2.8 mm, Isat 1.45 A, only 875 in stock).
   - **What else depends on it:** the height of J4's pad row on the edge board, and so where the LEDs can sit.
2. **U6 (3V3 shunt):** keep it (recommended), or accept the defect risk and save three parts (§4.3).
3. **DRIVE driver:** is the open-drain change acceptable as a SPEC change (decision 0011)? If not, the fallback is the layout rule alone, with R11 = 100 Ω and the V5 clamp, and a DRIVE-to-24V short stays destructive.
4. **Q3 threshold:** a 2N7002 at 3.3 V gate drive adds a little series resistance. Switch to a logic-level NMOS if code-0 calibration scatters (§4.1).
5. **No per-panel fuse or PTC on +24V.** A shorted controller (for example a failed SMAJ28A) trips the domain's injection fuse. A per-panel PTC rated ≥30 V would localise the fault; no part has been chosen.
6. **CAN termination:**
   - **The risk:** R12 (120 Ω) burns if a CAN wire is shorted to +24V while JP1 is closed; no package survives 4 W.
   - **Why it is accepted:** that short isn't credible, because CAN never neighbours +24V at the joint, the corners or the contacts.
7. **Inductor saturation:** confirm L1's behaviour with a +5V short on the prototype (§2).
8. **Thin stock at JLC:** CH32V203F6P6 (1,575) and TCAN1044VDRQ1 (1,502) are enough for rev A (4 boards), but buy before they run out.

## 12. What PCB layout needs from this

Nothing blocks starting the layout. Items to settle during it:
- **J4 position on the edge board:** x offset and the height of the row above the wall edge. This is an interface-contract item, and it depends on the back-plate pocket depth (open question 1).
- **J1 on the controller's base edge:** needs a copper-to-edge local rule.
- **Buck layout:** the TI §10 rules carry over. Keep the SW node ≥10 mm from Y1, C14 and the SENSE_ADC node. Keep FB short, and Kelvin-connect R17 to U5's GND. Connect U5's thermal pad with vias into inner GND. D5 needs short, wide connections to +24V and GND.
- **Corner joints:** CornerJoint_L/_R still need re-laying out for the 10–15 mm board (SPEC §3.4). The pad numbers are unchanged.
