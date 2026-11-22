"""Build hardware/bridge/bridge.kicad_pcb: the seam bridge (0.8 mm, 2-layer), standard + injection variants.

usage (KiCad 9 python):  python build_bridge_pcb.py OUT.kicad_pcb
Coordinates: x along the bridge as seen from face A (F.Cu); z = height above the BRIDGE's bottom edge
("local z"). The bridge sits 2.0 mm below the panels' wall edge, so panel z = local z - 2.0 (MECH-NOTES):
  local 0-4.2   (panel -2.0..2.2)  carrier slot: masked copper only, no parts (except the injection fuse)
  local 4.6-6.7 spring lands, contact point local 5.5 (panel 3.5), spring bodies to 8.1, courtyards 4.35-8.35
  local 8.55    one thin track over the springs; top edge local 9.0 (panel 7.0)
Face-A copper is written once below; face-B copper is its 180-degree image (x -> -x, F -> B, with the
SENSE/DRIVE cross nets swapped), so the bridge works either way round. The injection parts (F1, J1, J2 and
their copper) are the only asymmetric items. Reasons for every number: BRIDGE-NOTES.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'edge-board', 'scripts')))
from pcbutil import (pcbnew, read_netlist, add_footprints, place, track, via, outline_poly, text,  # noqa: E402
                     setup_rules, to_xz, mm, HW)

PROJ = os.path.join(HW, 'bridge')
LX = 28.0           # half length (56 mm): the panel frame's snap legs start at |x| 30 (MECH-NOTES)
H = 9.0             # height (panel z -2.0 .. 7.0; the frame wall bottom is at panel z 7.5)
Z0 = -2.0           # panel z of the bridge's bottom edge
ZC = 5.5            # spring contact point, local (panel z 3.5); footprint origin = body centre, 0.85 higher
PITCH = 5.0
SIG = 0.25
ZT = 8.55           # the track over the spring bodies
SIGMA = {'/DRV_A_SNS_B': '/SNS_A_DRV_B', '/SNS_A_DRV_B': '/DRV_A_SNS_B'}
PN, QN = '/DRV_A_SNS_B', '/SNS_A_DRV_B'

# face-A copper: (points, width, net). Lower band: GND lane 0.75, +36V lane 1.8, CANH 2.9, SPARE 3.8.
FA = [
    ([(-23.0, 0.75), (23.0, 0.75)], 0.7, 'GND'),                         # GND lane (both faces)
    ([(-22.5, 4.9), (-22.5, 1.0)], 1.0, 'GND'),                          # A1 drop
    ([(-22.5, ZC + 0.1), (-24.0, ZC + 0.1)], 0.6, 'GND'),                # A1 -> tie via to B10 (opposite)
    ([(22.5, ZC + 0.1), (24.0, ZC + 0.1)], 0.6, 'GND'),                  # A10 -> tie via to B1 (no drop: injection)
    ([(-12.5, 6.5), (-12.5, ZT), (-22.5, ZT), (-22.5, 6.5)], 0.3, 'GND'),  # A3 -> over A2 -> A1
    ([(-17.5, 4.9), (-17.5, 1.8)], 0.8, '+36V'),                         # A2 drop
    ([(17.5, 4.9), (17.5, 1.8)], 0.8, '+36V'),                           # A9 drop
    ([(-17.5, 1.8), (17.5, 1.8)], 0.8, '+36V'),                          # +36V lane
    ([(-7.5, 4.9), (-7.5, 2.9), (0, 2.9)], SIG, '/CANH'),                # A4 -> axis via
    ([(-2.5, ZC + 0.1), (0, ZC + 0.1)], SIG, '/CANL'),                   # A5 -> axis via in the spring gap
    ([(2.5, ZC + 0.1), (5.0, ZC + 0.1)], SIG, PN),                       # A6 (DRIVE_A) -> gap via at +5
    ([(7.5, 6.5), (7.5, ZT), (-5.0, ZT), (-5.0, ZC + 0.1)], SIG, QN),    # A7 (SENSE_A) -> over -> gap via at -5
    ([(12.5, 4.9), (12.5, 3.8), (0, 3.8)], SIG, '/SPARE'),               # A8 -> axis via
]
VIAS = [(0, 2.9, '/CANH'), (0, 3.8, '/SPARE'), (0, ZC + 0.1, '/CANL'), (5.0, ZC + 0.1, PN), (-5.0, ZC + 0.1, QN)]
for s in (-1, 1):
    VIAS += [(s * 17.5, 3.0, '+36V'), (s * 17.5, 3.8, '+36V'), (s * 22.1, 0.75, 'GND'), (s * 22.9, 0.75, 'GND'),
             (s * 24.0, ZC + 0.1, 'GND')]


def padxz(b, ref, num):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == num:
            return to_xz(p.GetPosition())
    raise KeyError(ref + '.' + num)


def build(out):
    comps, pinnet = read_netlist(os.path.join(PROJ, 'output', 'bridge.net'))
    b = pcbnew.BOARD()
    setup_rules(b, thickness=0.8)
    add_footprints(b, comps, pinnet)
    outline_poly(b, [(-LX, 0), (LX, 0), (LX, H), (-LX, H)])
    b.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I(mm(100 - LX), mm(100)))

    for n in range(1, 11):
        place(b, f'SA{n}', -27.5 + PITCH * n, ZC + 0.85, 0)          # face A, contact end (+y) toward the wall
        place(b, f'SB{n}', 27.5 - PITCH * n, ZC + 0.85, 0, flip=True)  # face B: panel B's pad n sits at -x
    place(b, 'F1', 24.6, 2.4, 180)                                   # injection fuse (pad 1 = +36V_IN, right)
    place(b, 'J1', 26.4, 6.0, 0)                                     # +36V IN wire pad (right end)
    place(b, 'J2', -26.4, 6.0, 0)                                    # GND IN wire pad (left end)
    for fp in b.GetFootprints():
        fp.Reference().SetVisible(False)
        fp.SetExcludedFromBOM(False)
    for r in ('J1', 'J2'):
        fp = b.FindFootprintByReference(r)
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES)

    for pts, w, n in FA:
        track(b, pts, w, 'F.Cu', n)
        track(b, [(-x, z) for x, z in pts], w, 'B.Cu', SIGMA.get(n, n))
    for x, z, n in VIAS:
        via(b, x, z, n)
    # injection copper (asymmetric, face A only: on face B the B1 GND drop occupies this corner)
    f1, f2 = padxz(b, 'F1', '1'), padxz(b, 'F1', '2')
    track(b, [(17.5, 2.0), (22.0, 2.0), f2], 1.2, 'F.Cu', '+36V')
    track(b, [f1, (26.4, f1[1] + 1.0), (26.4, 6.0)], 0.8, 'F.Cu', '/+36V_IN')
    track(b, [(-24.0, ZC + 0.1), (-26.4, 6.0)], 0.8, 'F.Cu', 'GND')

    text(b, 'SEAM BRIDGE 56 x 9 x 0.8 ENIG. Face A = F.Cu. Bottom edge = panel z -2.0.', 0, 11.0, 'Cmts.User', 1.0)
    b.BuildConnectivity()
    pcbnew.SaveBoard(out, b)
    print('saved', out, 'footprints', len(b.GetFootprints()), 'tracks', len(b.GetTracks()))


if __name__ == '__main__':
    build(sys.argv[1])
