# 0003 — RGBW LEDs on a per-panel 5 V rail

> **Updated by [0010](0010-24v-bus.md) (SPEC V6.0):** the 5 V rail now comes from a TPS54360B (60 V) that stays on, and the LED rail is switched by a P-MOSFET. The bus is 24 V. The LED choice is unchanged.

**Date:** 2026-11-15 · **Status:** Accepted for prototype rev A (replaces the WS2815B-V1 RGB LED of [0001](0001-edge-board-parts.md)) · **Requested by:** user ("premium" colour quality)

## Context

The rev A design used **WS2815B-V1**: 12 V, RGB, driver built in, with a backup data input. RGB-only white is poor, with low CRI and weak warm tones, and a dedicated white channel gives much better whites, pastels and warm ambient light (gap analysis B4). The user chose RGBW.

An LCSC search on 2026-11-15 found:

- **No 12 V RGBW LED with a built-in driver.** Every RGBW part with an integrated driver is 5 V (SK6812-family RGBW).
- **12 V RGBW is only available as a separate driver plus LED:** WS2814 driver (≈$0.08–0.10) plus a discrete RGBW 5050 (≈$0.066–0.079). The driver burns the 12 V headroom as heat, about 0.4–0.6 W per pixel at full white, and needs two parts per LED.
- **Tunable white (WS2805 + RGBCW):** the most premium option, at roughly 2× the added cost, with the same heat problem. No matching LED was found.

Options compared (per 18-LED hexagon):
- **A:** 5 V integrated RGBW plus a per-panel buck converter. +≈$0.85–1.10.
- **B:** WS2814 plus discrete RGBW. +≈$1.00–1.50.
- **C:** WS2805 tunable white. +≈$2–3.

**Option A was chosen:** cheapest, one part per LED, and the buck is more efficient than burning 12 V headroom.

## Decision

- **LED:** **SKC6812RGBW-NW** (LCSC C5348912)
  - Neutral white, 3600–4500 K, 5050-size 4-pin, 3.5–5.5 V, ≈$0.134, ≈48k in stock.
  - Drop-in alternatives: **SKC6812RGBW-WS** (warm white, C5378724) and -BW (cool white, C5181320). Confirm footprint and pinout from the datasheet.
  - Protocol: single-wire 800 kHz, **32 bits per LED (GRBW)**.
  - **No backup data line:** a dead LED blanks the rest of that panel's chain. The loopback count detects and locates this.
- **5 V LED rail, one buck per panel on the active board:** **TPS54202DDCR** (C191884, 4.5–28 V input, 2 A, ≈$0.23), with inductor, input and output caps, bootstrap and feedback network per datasheet.
  - The **28 V input rating** sits above the SMAJ15A clamp voltage on +12V, which the 17 V TPS563201 (C116592, $0.07) does not. The TPS563201 remains a cheaper alternative if supply overshoot is controlled at the injection bridge.
  - Load: ≈0.25 W per LED at full white, so 18 LEDs ≈ 4.5 W ≈ 0.9 A at 5 V.
- **Buck enable from an MCU GPIO = the switched LED rail.** In standby the MCU disables the buck, so the LEDs draw nothing. This replaces the "switched LED rail on the spare contact" idea for per-panel standby. Spare contact X8 stays reserved.
- **Data level shifter:** **SN74AHCT1G125** (UMW, C20617903, ≈$0.045), powered from 5 V. It takes PA7 (3.3 V, VIH ≈ 2 V on AHCT) and drives LED1 DIN at 5 V. SK6812 VIH ≈ 0.7 × VDD ≈ 3.5 V, so direct 3.3 V drive is out of spec.
- **Loopback:** the last LED's DO (5 V logic) returns to **PA0** (TIM2 counter) through the existing 2.2 kΩ.
  - **Confirm PA0 is 5 V tolerant.** If not, use a divider, for example 2.2 kΩ / 3.3 kΩ.
  - The PA6 backup-line input is no longer needed (spare pin).
  - Firmware divides the returned bit count by **32**, not 24.
- **Corner nets:**
  - **LED BIN is dropped**, because there is no backup line.
  - **+5V is added**, as an exterior-face SMD corner pad next to +12V and GND, to carry the LED rail around the panel.
  - Signal corner pads become: LED D, CANH, CANL, SENSE, DRIVE (5).
  - Power corner pads become: +12V, +5V, GND.
- **3.3 V logic regulator unchanged:** HT7533 + 68 Ω from +12V, so the MCU stays powered while the 5 V rail is off in standby.

## Consequences

- **Cost:** ≈ +$0.85–1.10 per 18-LED hexagon.
  - LEDs: 18 × (0.134 − 0.108) ≈ +$0.47.
  - Buck section: ≈$0.30–0.40.
  - Level shifter: $0.045.
  - JLC extended-part fees amortized over ≈100 panels: ≈$0.05–0.15.
  - Hexagon total ≈ $8–17 (was ≈ $7–16).
- **Colour and light:**
  - Real neutral-white channel, much better whites and pastels, and higher efficiency for white light.
  - The overall efficiency gain is to be measured in the optics test.
- **Robustness:**
  - The LEDs sit behind the buck, so 12 V overshoot no longer reaches them. The weak point moves from the WS2815's 13.5 V absolute maximum to the TPS54202's 28 V.
  - The backup data line is lost.
- **Firmware:**
  - 32-bit GRBW frames (≈40 µs per LED, still well under 1 ms per panel).
  - RGB→RGBW white extraction in the frame builder.
  - Buck-enable control in the power manager.
  - Loopback ÷32.
- **Software:**
  - The effect colour model gains a white channel.
  - Studio preview needs RGBW rendering.
  - Streamed samples grow from 3 to 4 bytes per edge (+33%).
- **Schematic:**
  - Replace LED symbol and footprint.
  - Add the buck section and level shifter.
  - Add the +5V net and corner pad; remove LED BIN.
  - Rework the passive-board LED1 input links.
- **Open:** confirm SKC6812RGBW current per channel and thermal performance in a closed cavity from the datasheet and the optics test.

## Resolved during schematic implementation (2026-11-15)

- **LED pinout and footprint:** the OPSCO datasheet gives the same pinout for -NW, -WS and -BW: 1 GND, 2 DIN, 3 VDD, 4 DOUT. The recommended pads are 1.8 × 1.2 mm at ±2.55 / ±1.6 mm, now footprint `ModularLight:LED_SKC6812RGBW_5050-4`. Warm white is a true drop-in.
- **Current per channel** (datasheet): RGB 8 mA each, W 16.5 mA, so ≈40 mA (0.2 W) per LED at full RGBW and ≈0.73 A for 18 LEDs. That is below the 0.9 A assumed above. Thermal performance still needs the optics test.
- **PA0 is not 5 V tolerant:** the CH32V203 datasheet gives 5.5 V only for FT pins, and PA0 is VDD + 0.3 V. The loopback uses a 2.2 kΩ / 3.3 kΩ divider (5 V → 3.0 V).
- **Buck:** TI's 5 V reference values. L 15 µH (Sunlord SWPA4030S150MT, C83475), C_out 2 × 22 µF 16 V, C_in 10 µF 50 V 1206, FB 100 k / 13.3 k with a 75 pF feed-forward capacitor. EN is driven by PA6 with a 100 kΩ pull-down (the EN pin's internal pull-up would otherwise enable the rail at power-up).
- **Corner power pads:** ordered +5V / GND / +12V, with GND between the two supplies so a stray bead cannot put 12 V on the 5 V rail (SPEC §3.4).

> **Pins changed by [0008](0008-mcu-pin-swap-led-ret-led-en.md) (SPEC V5.7, 2026-11-16):** buck EN (LED_EN) is now on **PA0**. The loop-back (LED_RET) is now on **PA6**, counted by TIM3 using TI1 as its external clock. The divider and the EN pull-down are unchanged. The two bullets above that name PA0 and PA6 are kept as history.
