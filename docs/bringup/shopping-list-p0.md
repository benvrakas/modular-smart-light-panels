# Shopping list — P0 (optics test and firmware bring-up)

For: the user to buy. Claude can't place orders. Prices are typical 2025–26 figures to sanity-check against, not quotes. LCSC numbers are exact where given.

## A. Optics: tested on the rev A boards (no LED strip; user decision 2026-11-16)
Only the film and the back-plate material are needed now.

| Item | Spec | Qty | Where | ≈ Price |
|---|---|---|---|---|
| Diffuser film samples | LCD backlight diffuser film, PET/PC, 0.1–0.3 mm. Get 2–3 different haze grades, or salvage the films from a dead LCD monitor or laptop panel (free). | A4 sheets | AliExpress "LCD diffuser film" / "light diffusion sheet PET" | $5–15 |
| White PETG | Matte white, for the back plate | 1 spool (if not on hand) | any | $20 |
| 3M Dual Lock | Reclosable mushroom-stem fastener for wall mounting (decision 0013): SJ3550 (or a low-profile type), 25 mm wide | 1 roll / ≈1 m | Amazon / 3M | $15–25 |

## B. Firmware bring-up (roadmap 1.7, 1.8)
| Item | Spec | Qty | Where | ≈ Price |
|---|---|---|---|---|
| CH32V203 dev board | Any CH32V203C8T6 board (WCH "CH32V203C8T6-EVT", WeAct, or similar). Same core and CAN peripheral as our CH32V203F6P6. | 2 | AliExpress / Amazon / LCSC | $3–8 each |
| WCH-LinkE programmer | Official WCH-LinkE (SWD/SDI for CH32V) | 1 | AliExpress / LCSC (sold as a CH32V003 EVT + WCH-LinkE bundle, C5236707, $7) | $5–8 |
| ESP32-C6 dev board | ESP32-C6-DevKitC-1 (N8), or any ESP32-C6 board with USB | 1–2 | Mouser/DigiKey/Amazon | $8–10 |
| CAN transceiver breakouts | 3.3 V CAN module (SN65HVD230 type) for bench work with the dev boards | 3–4 | AliExpress/Amazon "SN65HVD230 CAN module" | $2–4 each |
| 24 V supply | 24 V, ≥60 W, ideally a Class 2 adapter with a barrel jack, or a Mean Well LRS-75-24 | 1 | Amazon / Mouser | $15–30 |
| Logic analyzer | 8-channel 24 MHz "Saleae-compatible" clone (sigrok/PulseView) | 1 | AliExpress/Amazon | $10–15 |

## C. Rev A parts that go with the JLCPCB order later (roadmap 2.1)
- **Bridge springs BW0019CG-L3.5W1.5H4.3, LCSC C2826517.** 20 per bridge. Rev A needs 10 bridges plus a test coupon, so ≈250. Add them to the JLC assembly BOM rather than buying separately.
- The schematic agent's BOMs (`hardware/*/bom/`) will list everything else, with LCSC numbers and stock checked.

## Tools assumed on hand
Soldering iron with a drag-soldering tip, flux, multimeter, 3D printer (≥220 × 220 mm bed). Solder paste, a stencil and a hot plate or reflow oven are only needed if you assemble boards yourself; JLC can assemble the small parts.
