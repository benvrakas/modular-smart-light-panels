# 0008 — MCU pin swap: LED_RET ↔ LED_EN (active board)

> **Carried over by [0009](0009-rear-controller-board.md)/[0010](0010-24v-bus.md) (SPEC V6.0):** the pins (PA0 LED_EN, PA6 loop-back) move with the MCU to the controller board. PA0 now drives a P-MOSFET LED-rail switch instead of the buck's enable pin.

**Date:** 2026-11-16 · **Status:** **Accepted.** The PCB session asked whether to swap these two MCU pins to finish routing, and the user answered "Yes, swap them". · **Changes:** SPEC §3.2 (5 V LED rail EN pin; LED loop-back pin) and the schematic GPIO map.

## Context

- The active board (decision 0006) routed down to 7 open connections. All of them were above U1's top-left.
- **LED_RET** was on **PA0, pin 6** (U1's right column). It feeds R7/R8 at the board's west top row.
- **LED_EN** was on **PA6, pin 12** (U1's left column). It drives the buck enable at the east end.
- Each net had to cross U1 to reach its side. With LED_D1, D_IN and the CAN_RS via they shared one B.Cu band under the bus, about 1 mm wide and good for 2 tracks.

## Decision

| Net | Before | After |
|---|---|---|
| LED_EN (buck EN, 100 kΩ pull-down) | PA6 (pin 12) | **PA0 (pin 6)** |
| LED_RET (LED loop-back, through the 2.2 k / 3.3 k divider) | PA0 (pin 6) | **PA6 (pin 12)** |

- **Firmware:** count the returned LED bits with **TIM3 using TI1 (PA6, TIM3_CH1) as its external clock**, instead of TIM2_ETR on PA0. TIM3 is unused, because LED_DATA runs on SPI1_MOSI + DMA (PA7). PA6 is also SPI1_MISO, so a SPI read-back of the chain is an alternative.
- **LED_EN on PA0:** a plain push-pull output. It needs no special function.
- **Divider:** the loop-back divider stays. **Confirmed on 2026-11-16:** PA6 is not 5 V tolerant. The CH32V203 datasheet V2.8 pin table has no FT mark on TSSOP20 pin 12, so the divider is required.
- **Edits made:** two net labels on U1 in `hardware/archive/edge-board-v5/edge-board.kicad_sch` and its GPIO map note. ERC shows 0 violations. The PCB is synced, with parity 0.
- **Passive board:** has no MCU, so it is unaffected.

## Consequences

- **Routing:** the active board routes completely, with 0 unconnected and 0 DRC errors.
- **Firmware:** the LED-count timer moves from TIM2 to TIM3, and the LED_EN GPIO from PA6 to PA0.
