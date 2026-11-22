# 0020 — Eight edge ID codes (up to octagons)

**Date:** 2026-11-22 · **Status:** **Accepted** (user: "we should probably plan for octagons… I don't think anything past 8 is going to happen", then "switch to the 8-edge codes") · **Changes:** SPEC §3.2 (R11), §3.5, §4.1, §4.2. Replaces the code table in [0011](0011-24v-fault-protection-controller.md).

## Context

- The discovery scheme (SPEC §4) gives each edge of a panel a code. The code is an ID resistor R_k in series with a diode, read as one ADC voltage. There were 6 codes (0–5), enough for hexagons.
- A worst-case check of the old 6 values found codes 0 and 1 only **41 mV** apart. The upper codes had 340–380 mV, and 670 mV of room was left below idle. The worst case covers diode, resistor, ADC and leakage tolerances (see Method).
- The reason: the diode's forward voltage (Vf) varies most at the low codes. The reading is V = Vf·(1 − x) + 3.3·x, with x = R/(R_pu + R), so a Vf error is scaled by 1 − x, which is largest at small R.

## Decision

- **Eight codes, 0–7**, so every shape up to an **octagon** can be identified. Nothing above 8 edges is planned.
- **R11 (DRIVE series) 470 Ω → 1 kΩ:** this lifts code 0 to where Vf matters less, and halves the pulse into a DRIVE short at 36 V ([0019](0019-36v-bus.md)).
- **Values:** chosen from the **JLC basic** E24 0603 values with the largest smallest worst-case gap (an exhaustive search):

| Code | R_k | V_ADC nominal | Worst-case window | Gap to next |
|---|---|---|---|---|
| 0 | 0 Ω | 0.81 V | 0.72–0.90 | 200 mV |
| 1 | 2.0 kΩ (C22975) | 1.18 V | 1.10–1.27 | 194 mV |
| 2 | 4.7 kΩ (C23162) | 1.54 V | 1.46–1.62 | 233 mV |
| 3 | 9.1 kΩ (C23260) | 1.92 V | 1.85–1.99 | 182 mV |
| 4 | 15 kΩ (C22809) | 2.23 V | 2.17–2.29 | 229 mV |
| 5 | 27 kΩ (C22967) | 2.56 V | 2.52–2.61 | 168 mV |
| 6 | 47 kΩ (C25819) | 2.81 V | 2.78–2.85 | 167 mV |
| 7 | 100 kΩ (C25803) | 3.04 V | 3.02–3.07 | 201 mV to idle |
| idle | — | 3.30 V | ≥3.27 | |

- **Smallest gap: 167 mV, up from 41 mV.**
- **Starting firmware thresholds:** the midpoints 1.00 / 1.37 / 1.73 / 2.08 / 2.40 / 2.69 / 2.93 / 3.17 V. Still calibrate on hardware (gap item 10).
- **Codes per shape:** triangle 0–2, square 0–3, hexagon 0–5, octagon 0–7. A panel's code-0 board is always code 0. There are now eight edge BOM variants, `BOM_edge_code0..7.csv`, and the CPL variant for codes 1–7 is `CPL_*_code1-7.csv`.

## Method

All numbers come from a worst-case corner model in [`hardware/controller-board/scripts/edge_codes.py`](../../hardware/controller-board/scripts/edge_codes.py). Run it for the table, or with `--search` for the value search.
- **Diode:** a Shockley fit for the 1N4148WS (0.62 V at 1 mA, n ≈ 1.9), evaluated at each code's own current (26–250 µA). Vf is then moved **±80 mV**: ±30 mV part spread and ±50 mV for 0–50 °C.
- **Resistors:** R_k, R_pu (10 kΩ) and R11 each ±1 %, plus 20 Ω for Q3.
- **ADC:** ±15 mV.
- **Idle:** taken as ≥3.27 V, which covers TVS and diode leakage through R_pu.
- **Settling:** code 7 settles to within ≈1.4 mV in the 1 ms wait before sampling. The time constant is ≈0.19 ms through R10 and C14.

## Consequences

- Five of the six existing ID values change. The boards are not built yet, so this costs nothing.
- All eight values are basic parts, so there is no extended-part fee per variant.
- An octagon needs its own edge-board outline (a 135° corner) and frame. That is not designed; this decision only reserves the codes.
