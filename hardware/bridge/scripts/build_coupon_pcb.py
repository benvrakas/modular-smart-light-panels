"""Build hardware/bridge/coupon/spring-coupon.kicad_pcb: spring test coupon (0.8 mm 2-layer ENIG, same spec as
the bridge so it can share the JLC order or panel).

Two halves joined by two mouse-bite tabs:
  spring half (z 0-14):  4 x BW0019CG at x = -7.5, -2.5, 2.5, 7.5 (5 mm pitch like the bridge), contact points on
                         the line z 7.0; per spring a force pad below and a sense pad above (Kelvin).
  pad half    (z 16-30): 4 x ENIG 3 x 6 mm pads centred on z 23.0, force pad below, sense pad above.
M2 holes on each half's centre line (x = +-12), so the pad half flipped face-down onto the spring half lines up;
M2 standoffs + shims set the gap = spring working height (3.0-3.5 mm).
usage (KiCad 9 python):  python build_coupon_pcb.py OUT.kicad_pcb
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'edge-board', 'scripts')))
from pcbutil import (pcbnew, read_netlist, add_footprints, place, track, seg, text, setup_rules,  # noqa: E402
                     load_fp, P, mm, to_xz, HW)

PROJ = os.path.join(HW, 'bridge', 'coupon')
W = 14.0            # half width
XS = (-7.5, -2.5, 2.5, 7.5)
ZC_S, ZC_P = 7.0, 23.0


def padxz(b, ref, num='1'):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == num:
            return to_xz(p.GetPosition())


def npth(b, ref, x, z, d_fp):
    h = load_fp(d_fp)
    h.SetReference(ref)
    h.SetPosition(P(x, z))
    h.SetBoardOnly(True)
    h.SetExcludedFromBOM(True)
    h.SetExcludedFromPosFiles(True)
    h.Reference().SetVisible(False)
    h.Value().SetVisible(False)
    b.Add(h)


def build(out):
    comps, pinnet = read_netlist(os.path.join(PROJ, 'output', 'spring-coupon.net'))
    b = pcbnew.BOARD()
    setup_rules(b, thickness=0.8)
    add_footprints(b, comps, pinnet)
    # outline: both halves + two 3 mm tabs (x 6..9 and -9..-6), slot z 14..16 between them
    pts = [(-W, 0), (W, 0), (W, 14), (9, 14), (9, 16), (W, 16), (W, 30), (-W, 30), (-W, 16), (-9, 16), (-9, 14),
           (-W, 14)]
    for a, c in zip(pts, pts[1:] + pts[:1]):
        seg(b, a, c)
    for a, c in zip([(-6, 14), (6, 14), (6, 16), (-6, 16)], [(6, 14), (6, 16), (-6, 16), (-6, 14)]):
        seg(b, a, c)
    b.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I(mm(100 - W), mm(100)))

    for k, x in enumerate(XS, 1):
        place(b, f'S{k}', x, ZC_S + 0.85, 0)              # footprint origin = body centre; contact 0.85 mm lower
        place(b, f'TP{k}1', x, 2.4, 0)                    # force
        place(b, f'TP{k}2', x, 12.0, 0)                   # sense
        place(b, f'P{k}', x, ZC_P, 0)
        place(b, f'TP{k + 4}1', x, 17.8, 0)
        place(b, f'TP{k + 4}2', x, 28.2, 0)
        sp = padxz(b, f'S{k}')
        track(b, [(x, sp[1] - 1.05), (x, 2.4)], 1.2, 'F.Cu', f'/SPR{k}')       # force: land bottom edge
        track(b, [(x, sp[1] + 1.05), (x, 12.0)], 0.3, 'F.Cu', f'/SPR{k}')      # sense: land top edge
        track(b, [(x, ZC_P - 3.0), (x, 17.8)], 1.2, 'F.Cu', f'/PAD{k}')
        track(b, [(x, ZC_P + 3.0), (x, 28.2)], 0.3, 'F.Cu', f'/PAD{k}')
        text(b, f'{k}', x + 1.6, 2.4, 'F.SilkS', 0.8)
        text(b, f'{k}', x + 1.6, 17.8, 'F.SilkS', 0.8)
    for fp in b.GetFootprints():
        fp.Reference().SetVisible(False)
        fp.SetExcludedFromBOM(False)
        if fp.GetReference().startswith('TP') or fp.GetReference().startswith('P'):
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    for i, (x, z) in enumerate([(-12, ZC_S), (12, ZC_S), (-12, ZC_P), (12, ZC_P)]):
        npth(b, f'H{i + 1}', x, z, 'MountingHole:MountingHole_2.2mm_M2')
    n = 0
    for xc in (-7.5, 7.5):                                # mouse bites on both break lines of each tab
        for dx in (-1.0, 0.0, 1.0):
            for z in (14.25, 15.75):
                n += 1
                npth(b, f'MB{n}', xc + dx, z, 'ModularLight:NPTH_0.5mm')
    text(b, 'F = force   S = sense', 0, 9.6, 'B.SilkS', 0.8, mirror=True)
    text(b, 'SPRING COUPON BW0019CG', 0, 5.0, 'B.SilkS', 0.8, mirror=True)
    text(b, 'PAD COUPON: flip onto springs', 0, 21.0, 'B.SilkS', 0.8, mirror=True)
    b.BuildConnectivity()
    pcbnew.SaveBoard(out, b)
    print('saved', out, 'footprints', len(b.GetFootprints()))


if __name__ == '__main__':
    build(sys.argv[1])
