"""Build hardware/edge-board/edge-board-{hex,square,triangle}.kicad_pcb (V6) from the netlist:
outline, footprints (schematic-linked), placement and the hand-routed copper (power lanes, bus, LED chain,
controller joint). The few local connections left (ID circuit) are routed by autoroute.py; then DRC.

usage (KiCad 9 python):  python build_edge_pcb.py OUT.kicad_pcb [hex|square|triangle]
Shapes (decision 0004, d = 3.5): hex 94.1, square 89.8, triangle 82.33. One layout for all three (decisions
0015/0016, user 2026-11-21): the core (contacts, J4, ID circuit, hops, C1/C3/C4) is placed from the board centre, the
end zone (D_OUT riser, bus end vias, power drops, corner pads) from the outer LED, and only the outer LEDs move with
the shape (about L/3, evenly spaced). The earlier hand-reviewed hex layout is archived in
hardware/archive/edge-board-hex-reviewed-2026-11-21/.
Geometry: x along the board from its centre (viewed from the inward face, F.Cu), z up from the wall edge.
Layer plan (reasons in LAYOUT-NOTES.md section 3):
  B.Cu  contact strip z 0-6.0 (vias in the pad tops, z 5.4-6.0)
        bus lanes b1..b4 at z 6.45 / 7.1 / 7.75 / 8.4 (0.25 mm, 0.65 mm pitch so a via fits on any lane)
        +24V lane 8.9-10.3 | GND lane 10.7-12.1 | +5V_LED lane 12.5-13.1 | top edge 13.5
  F.Cu  low band z 0.3-2.3 (J4 fan-out, LED data) | J4 pads 2.5-5.35 | channel 5.9-7.0 | LEDs (centre z 9.8)
        | LED data chain at z 11.9 over the top
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbutil import (pcbnew, read_netlist, add_footprints, place, track, via, outline_poly, text,  # noqa: E402
                     setup_rules, to_xz, HW)

PROJ = os.path.join(HW, 'edge-board')
SHAPE = sys.argv[2] if len(sys.argv) > 2 else 'hex'
L = {'hex': 94.1, 'square': 89.8, 'triangle': 82.33}[SHAPE]   # board length (decision 0004, d = 3.5)
H = 13.5            # board height
HL = L / 2
# End zone packed outward from the outer LED pad edge (LO + 3.45) at the 0.2 mm netclass clearance:
# D_OUT riser | 4 bus end vias at 0.8 pitch | +24V drop | GND drop | corner pads (HL - 3).
# Parts on the inward face must stay above z 6.8: below it the face runs against the back-plate wall (top z 6.6;
# controller z 5.0-6.6 on side 0), and the board ring is lowered into the plate along z after its corners are
# soldered, so nothing may stick out there (user, 2026-11-21: the old R3 groove made insertion impossible). C1 and C3 sit at z 9.6 like the hex, in the free gaps between the contact hop columns:
# C1 between the -17.5 (+24V) and -12.5 (GND) hops, its +5V pad dropping to the +5V_LED low band; C3 between
# the +17.5 (+24V) and +22.5 (GND) hops, its +5V pad running along the free right low band to LED3's riser.
# R3 (0402) sits just below LED1's DIN pad at z 7.2, pad 2 under that pad (same net), pad 1 0.24 mm clear of it
# and fed from the D_IN via straight below; it is fitted only on sides 1..n-1 (DNP on code 0).
LO = {'hex': 31.2, 'square': 29.9, 'triangle': 27.4}[SHAPE]   # about L/3: LEDs evenly spaced on their own board
DOUTX = LO + 3.45 + 0.2 + 0.125
XV_ = tuple(round(DOUTX + 0.65 + 0.8 * i, 3) for i in range(4))
X24_ = XV_[3] + 1.1
XGD_ = X24_ + 1.5            # 0.2 mm past the +24V lane's round end cap; its own cap ends before the +5V_LED pad
assert XGD_ + 0.7 <= HL - 3.0 - 0.2, 'GND lane would reach the +5V_LED corner pad'
G2 = None
C1X, C3X = -15.4, 19.8       # >= 1.4 mm from the +24V hop columns (|x| 17.0-18.0)
R3CX, R3Z = -LO - 3.45, 7.2   # R3 centre: pads z 6.88-7.52, body clear of LED1's body (x -LO-2.5)
R3X = R3CX - 0.51            # D_IN via x = R3 pad 1 x
DINV = -LO - 0.2             # D_IN dive to B.Cu: just past LED1's +5V riser, outside the strip via keepout (|x| 25.3)
# Low band under J4 (pads z 2.5-5.35, roadmap 2.0): left LED1_DI 0.5 | D_IN 0.95 | +5V_LED 1.5 | GND guard 2.05;
# right SPARE 1.6 | DRIVE 2.1. +5V_LED stays 0.8 mm below the J4.1 (+24V) pad, the GND guard between them.
ZLI, ZDI, Z5L, ZGG = 0.5, 0.95, 1.5, 2.05
ZSP, ZDR = 1.6, 2.1
LEDD2X = LO - 3.85           # LED_D2 riser, 0.4 mm left of LED3's GND/DIN pads
TP11 = (-LO + 0.6, 3.6)      # on the +5V_LED riser (the low band is taken by D_IN up to the dive)
TP10X, TP3X = -(LO + 1.8), LO + 1.8
HOPL = (-23.3, -22.5, -21.7)
HOPR = (21.7, 22.5)  # 2-via GND hop on every shape (the triangle's LED_D2 riser needs the room)
UNDER = True        # one layout for every shape (user, 2026-11-21: keep the three boards as alike as possible)
LED_X = (-LO, 0.0, LO)
LED_Z = 9.8         # controller-board session 2026-11-21: LED bottom z 7.37, 0.77 mm above the controller top
ZLO, ZHI = LED_Z - 1.6, LED_Z + 1.6   # LED pad rows (DIN/VDD low, GND/DOUT high)
J4_Z0 = 5.25        # ControllerJoint_EdgeBoard origin; the controller underside (z 5.0) is its y = +0.25 line
B1, B2, B3, B4 = 6.45, 7.1, 7.75, 8.4      # B.Cu bus lanes
Z24, W24 = 9.6, 1.4                         # +24V lane (B)
ZG, WG = 11.4, 1.4                          # GND lane (B)
ZGV = 11.0                                  # GND via row (inside the GND lane, below the LED data at 11.9)
Z5, W5 = 12.8, 0.6                          # +5V_LED lane (B)
ZPV = 5.7                                   # vias in the contact-pad tops (rule area ends at 5.3)
ZD = 12.15                                  # LED data runs (F), between the LED pad tops (12.0) and the +5V vias
XV = XV_                                    # bus end vias |x| (SENSE, CANH|-, DRIVE, -|CANL)
X24, XGD = X24_, XGD_                       # corner drops of the +24V and GND lanes
SIG = 0.25


def padxz(b, ref, num):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == num:
            return to_xz(p.GetPosition())
    raise KeyError(ref + '.' + num)


def build(out):
    comps, pinnet = read_netlist(os.path.join(PROJ, 'output', 'edge-board.net'))
    b = pcbnew.BOARD()
    setup_rules(b)
    add_footprints(b, comps, pinnet)
    outline_poly(b, [(-HL, 0), (HL, 0), (HL, H), (-HL, H)])
    b.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I(pcbnew.FromMM(100 - HL), pcbnew.FromMM(100)))  # fab origin
    T = lambda pts, w, lay, n: track(b, pts, w, lay, n)  # noqa: E731
    V = lambda x, z, n: via(b, x, z, n)  # noqa: E731

    # ================================================================ placement
    place(b, 'J1', 0, 0)                                   # contacts: origin on the wall edge, pads on B.Cu
    place(b, 'J2', -HL, 0)                                 # corner IN, left end
    place(b, 'J3', HL, 0)                                  # corner OUT, right end
    place(b, 'J4', 0, J4_Z0)                               # controller joint, centred
    for i, x in enumerate(LED_X):
        place(b, f'LED{i + 1}', x, LED_Z, 180)             # DIN lower-left, DOUT upper-right: data flows +x
    place(b, 'C1', C1X, 9.6, 90)                           # +5V pad (1) at the bottom
    place(b, 'C2', LED_X[1] + 5.4, 9.6, 90)
    place(b, 'C3', C3X, 9.6, 90)
    place(b, 'C4', -20.4, 8.6, 90)
    place(b, 'R3', R3CX, R3Z, 0)                          # code-0 link under LED1 DIN (pad 1 D_IN left, pad 2 LED1_DI right)
    place(b, 'R1', 14.6, 10.7, 180)                        # ID circuit in the LED2-LED3 gap (SPEC 2: between LEDs)
    place(b, 'D1', 15.6, 8.3, 270)                         # cathode (ID_K) on top
    place(b, 'R2', 13.8, 8.3, 270)                         # DNP bypass, parallel to D1
    place(b, 'TP1', 14.6, 1.6, 0)                          # SPARE  (flat pads: jig only, under the back plate)
    place(b, 'TP11', TP11[0], TP11[1], 0)                        # +5V_LED
    place(b, 'TP10', TP10X, Z24, 0, flip=True)             # +24V on the exterior face, inside the +24V lane
    place(b, 'TP3', TP3X, ZG, 0, flip=True)                # GND on the exterior face, inside the GND lane
    for r in ('TP1', 'TP3', 'TP10', 'TP11'):
        fp = b.FindFootprintByReference(r)
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    for fp in b.GetFootprints():
        fp.Reference().SetVisible(False)     # 13.5 mm board: no room for reference silk (refs stay on F.Fab)
        fp.SetExcludedFromBOM(False)        # schematic parity: every symbol is in_bom (the BOM scripts skip no-LCSC parts)

    # ================================================================ B.Cu power lanes
    T([(-X24, Z24), (X24, Z24)], W24, 'B.Cu', '+24V')
    T([(-XGD, ZG), (XGD, ZG)], WG, 'B.Cu', 'GND')
    T([(-(HL - 1.5), Z5), (HL - 1.5, Z5)], W5, 'B.Cu', '+5V_LED')
    for s in (-1, 1):
        T([(s * X24, Z24), (s * X24, 2.0)], 1.2, 'B.Cu', '+24V')                     # corner +24V pad z 0.5-3.5
        T([(s * X24, 2.0), (s * (HL - 1.5), 2.0)], 2.0, 'B.Cu', '+24V')
        T([(s * XGD, ZG), (s * XGD, 7.25)], 1.2, 'B.Cu', 'GND')                      # corner GND pad z 6.0-8.5
        T([(s * XGD, 7.25), (s * (HL - 1.5), 7.25)], 1.2, 'B.Cu', 'GND')
        if G2:
            T([(s * G2, 7.25), (s * (HL - 1.5), 7.25)], 2.0, 'B.Cu', 'GND')

    # ================================================================ contact-pad vias and hops over the bus band
    hops = {(-22.5, 'GND'): HOPL, (-12.5, 'GND'): (-13.6, -12.85), (22.5, 'GND'): (21.7, 22.5, 23.3),
            (-17.5, '+24V'): (-17.9, -17.1), (17.5, '+24V'): (17.1, 17.9)}
    hops[(22.5, 'GND')] = HOPR
    for (xp, n), xs in hops.items():
        xr = sum(xs) / len(xs)
        zt = ZGV if n == 'GND' else Z24
        T([(xr, ZPV), (xr, zt - 0.4 if n == 'GND' else zt)], 1.0 if len(xs) == 2 else 1.4, 'F.Cu', n)
        for x in xs:
            V(x, ZPV, n)
            V(x, zt, n)
    for x, n in ((2.54, '/DRIVE'), (7.62, '/SENSE_EDGE'), (12.9, '/SPARE')):
        V(x, ZPV, n)                                        # x in the J4 pad gaps, inside each 3 mm contact pad
    for x, n in ((-7.5, '/CANH'), (-2.5, '/CANL')):
        T([(x, 5.8), (x, B1)], 0.4, 'B.Cu', n)              # X4/X5 neck straight into lane b1

    # ================================================================ bus lanes (B.Cu)
    xs, xh, xd, xl = XV
    T([(-xh, B1), (-5.08, B1)], SIG, 'B.Cu', '/CANH')       # CANH: left corner .. X4 .. jumps to F at -5.08
    T([(-xl, B2), (-4.4, B2), (-3.6, B1), (xl, B1)], SIG, 'B.Cu', '/CANL')   # CANL: b2 -> b1, taps X5, to right corner
    T([(4.4, B2), (xh, B2)], SIG, 'B.Cu', '/CANH')          # CANH: back on B after J4.7, to the right corner
    T([(-xd, B3), (xd, B3)], SIG, 'B.Cu', '/DRIVE')
    T([(-xs, B4), (xs, B4)], SIG, 'B.Cu', '/SENSE')
    for x, z, n in ((-5.08, B1, '/CANH'), (4.4, B2, '/CANH'), (5.08, B1, '/CANL'), (8.89, B4, '/SENSE'),
                    (12.6, B3, '/DRIVE')):
        V(x, z, n)
    # ends: lane vias and F.Cu stubs to the corner signal pads (D 1.5, CANH 4.0, CANL 6.5, DRIVE 9.0, SENSE 11.5)
    pad = HL - 1.0
    # left: b1 CANH, b2 CANL
    V(-xh, B1, '/CANH'); T([(-xh, B1), (-xh, 4.0), (-pad, 4.0)], SIG, 'F.Cu', '/CANH')
    V(-xl, B2, '/CANL'); T([(-xl, B2), (-xl, 6.5), (-pad, 6.5)], SIG, 'F.Cu', '/CANL')
    # right: b1 CANL, b2 CANH (CANH via inboard, its stub runs under CANL's)
    V(xl, B1, '/CANL'); T([(xl, B1), (xl + 0.6, 6.5), (pad, 6.5)], SIG, 'F.Cu', '/CANL')
    V(xh, B2, '/CANH'); T([(xh, B2), (xh, 4.0), (pad, 4.0)], SIG, 'F.Cu', '/CANH')
    for s in (-1, 1):
        V(s * xd, B3, '/DRIVE'); T([(s * xd, B3), (s * xd, 9.0), (s * pad, 9.0)], SIG, 'F.Cu', '/DRIVE')
        V(s * xs, B4, '/SENSE'); T([(s * xs, B4), (s * xs, 11.5), (s * pad, 11.5)], SIG, 'F.Cu', '/SENSE')

    # ================================================================ controller joint J4 (F.Cu)
    T([(-11.43, 4.6), (-11.43, Z24)], 0.5, 'F.Cu', '+24V');  V(-11.43, Z24, '+24V')
    T([(-8.89, 4.6), (-8.89, ZGV)], 0.5, 'F.Cu', 'GND');     V(-8.89, ZGV, 'GND')
    # J4.3 +5V_LED: low band to LED1's VDD; C4 and TP11 hang on it
    T([(-6.35, 4.6), (-6.35, Z5L), (LED_X[0] + 0.6, Z5L), (LED_X[0] + 0.6, ZLO)], 0.4, 'F.Cu', '+5V_LED')
    c4 = padxz(b, 'C4', '1')
    T([(c4[0], Z5L), c4], 0.4, 'F.Cu', '+5V_LED')
    # GND guard under J4.1: the +5V_LED track passes below the +24V pad, so GND sits between them
    T([(-8.89, 4.6), (-8.89, ZGG), (-13.225, ZGG), (-13.225, ZPV)], 0.3, 'F.Cu', 'GND')
    # J4.4 D_IN: low band, dives to B.Cu under LED1 (crosses LED1_DI), back to F for R3 and the corner D pad
    r31 = padxz(b, 'R3', '1')
    T([(-3.81, 4.6), (-3.81, ZDI), (DINV, ZDI), (DINV, 1.9)], SIG, 'F.Cu', '/D_IN')
    V(DINV, 1.9, '/D_IN'); T([(DINV, 1.9), (R3X, 1.9)], SIG, 'B.Cu', '/D_IN'); V(R3X, 1.9, '/D_IN')
    T([(R3X, 1.9), r31], SIG, 'F.Cu', '/D_IN')
    T([(R3X, 1.9), (R3X - 0.4, 1.5), (-pad, 1.5)], SIG, 'F.Cu', '/D_IN')
    # J4.5 LED1_DI: low band to LED1 DIN (from below); R3 pad 2 to the DIN pad's left edge
    r32 = padxz(b, 'R3', '2')
    T([(-1.27, 4.6), (-1.27, ZLI), (LED_X[0] - 1.8, ZLI), (LED_X[0] - 1.8, ZLO)], SIG, 'F.Cu', '/LED1_DI')
    T([r32, (r32[0], ZLO)], SIG, 'F.Cu', '/LED1_DI')                    # straight up into LED1 DIN
    # J4.6 SPARE: low band to X8's pad via; TP1 on the way
    T([(1.27, 4.6), (1.27, ZSP), (12.9, ZSP), (12.9, ZPV)], SIG, 'F.Cu', '/SPARE')
    T([(12.9, ZSP), (14.6, 1.6)], SIG, 'F.Cu', '/SPARE')
    # X6 DRIVE: pad via down the J4 gap, low band, into J4.10 from below
    T([(2.54, ZPV), (2.54, ZDR), (11.43, ZDR), (11.43, 4.6)], SIG, 'F.Cu', '/DRIVE')
    # CANH: from its b1 via over the J4 tops (channel z 6.45, under LED2's pads) to J4.7, then back to B
    T([(-5.08, B1), (3.81, B1), (3.81, 4.6)], SIG, 'F.Cu', '/CANH')
    T([(3.81, B1), (4.4, B2)], SIG, 'F.Cu', '/CANH')
    T([(5.08, B1), (6.35, B1), (6.35, 4.6)], SIG, 'F.Cu', '/CANL')       # J4.8
    T([(8.89, 4.6), (8.89, B4)], SIG, 'F.Cu', '/SENSE')                   # J4.9
    T([(11.43, 4.6), (11.43, 7.0), (12.6, B3)], SIG, 'F.Cu', '/DRIVE')    # J4.10

    # ================================================================ LEDs: power under each body, data chain
    for xl in LED_X:
        T([(xl + 2.55, ZLO), (xl + 0.6, ZLO), (xl + 0.6, Z5)], 0.4, 'F.Cu', '+5V_LED');  V(xl + 0.6, Z5, '+5V_LED')
        T([(xl - 2.55, ZHI), (xl - 0.8, ZHI)], 0.4, 'F.Cu', 'GND');                   V(xl - 0.8, ZHI, 'GND')
    T([(LED_X[0] + 2.55, ZHI), (LED_X[0] + 2.55, ZD), (-4.0, ZD), (-4.0, ZLO), (-2.55, ZLO)], SIG, 'F.Cu', '/LED_D1')
    T([(2.55, ZHI), (2.55, ZD), (LEDD2X, ZD), (LEDD2X, ZLO), (LED_X[2] - 2.55, ZLO)], SIG, 'F.Cu', '/LED_D2')
    T([(LED_X[2] + 2.55, ZHI), (LED_X[2] + 2.55, ZD), (DOUTX, ZD), (DOUTX, 1.5), (pad, 1.5)], SIG, 'F.Cu', '/D_OUT')
    # decoupling: +5V pad to the LED's VDD pad, GND pad to a via into the GND lane
    for ref, xl in (('C1', LED_X[0]), ('C2', LED_X[1]), ('C3', LED_X[2])):
        p1, p2 = padxz(b, ref, '1'), padxz(b, ref, '2')
        if UNDER and ref == 'C1':      # +5V straight down into the +5V_LED low band (z 1.5)
            T([p1, (p1[0], Z5L)], 0.4, 'F.Cu', '+5V_LED')
        elif UNDER and ref == 'C3':    # +5V down to z 2.6, along the free right low band, up LED3's +5V riser
            T([p1, (p1[0], 2.6), (xl + 0.6, 2.6), (xl + 0.6, ZLO)], 0.4, 'F.Cu', '+5V_LED')
        if UNDER and ref != 'C2':
            T([p2, (p2[0], 11.35)], 0.4, 'F.Cu', 'GND');  V(p2[0], 11.35, 'GND')
            continue
        T([p1, (xl + 3.3, 8.2)], 0.4, 'F.Cu', '+5V_LED')
        T([p2, (p2[0], 11.35)], 0.4, 'F.Cu', 'GND');  V(p2[0], 11.35, 'GND')
    p2 = padxz(b, 'C4', '2')
    T([p2, (p2[0], ZGV)], 0.5, 'F.Cu', 'GND');  V(p2[0], ZGV, 'GND')

    # ================================================================ X7 SENSE_EDGE to the ID circuit
    r12 = padxz(b, 'R1', '2')
    T([(7.62, ZPV), (7.62, r12[1]), r12], SIG, 'F.Cu', '/SENSE_EDGE')
    # ID_K: R1.1 - D1.K - R2.1 ; SENSE: D1.A - R2.2 - via onto lane b4
    r11, dk, da, r21, r22 = (padxz(b, 'R1', '1'), padxz(b, 'D1', '1'), padxz(b, 'D1', '2'), padxz(b, 'R2', '1'),
                             padxz(b, 'R2', '2'))
    T([r11, dk], SIG, 'F.Cu', '/ID_K'); T([r21, dk], SIG, 'F.Cu', '/ID_K')
    T([r22, da], SIG, 'F.Cu', '/SENSE'); T([da, (16.5, da[1]), (16.5, B4)], SIG, 'F.Cu', '/SENSE'); V(16.5, B4, '/SENSE')

    text(b, f'EDGE BOARD V6 {SHAPE} {L} x 13.5 x 1.6 ENIG. Inward face. Wall edge = bottom.', 0, 15.0, 'Cmts.User', 1.0)
    text(b, 'Bevel the wall edge (exterior side) for spring lead-in.', 0, 16.5, 'Cmts.User', 1.0)
    b.BuildConnectivity()
    pcbnew.SaveBoard(out, b)
    print('saved', out, 'footprints', len(b.GetFootprints()), 'tracks', len(b.GetTracks()))


if __name__ == '__main__':
    build(sys.argv[1])
