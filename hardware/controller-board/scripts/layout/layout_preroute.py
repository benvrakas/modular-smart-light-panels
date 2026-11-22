"""Controller board: hand-defined (scripted) routes that the autorouter must not choose for us.

  - +24V_IN : J1.1 -> F1.1, TP10 stub                    (HV24, 0.6 mm; only GND / tolerant neighbours)
  - +24V    : F1.2 -> U5 VIN, C17, C16, C23, D5, TP13    (0.8 mm bus, 0.6 mm riser)
  - BUCK_SW : U5.8 -> D7 cathode, L1.1, C18.2            (1.0 mm, as short as the parts allow)
  - BOOT    : U5.1 -> C18.1
  - GND vias at the hot-loop / output-cap / TVS grounds into the In1 plane
All of these are locked, so layout_route.py keeps them (Freerouting gets them as protected wiring).

usage (KiCad 9 python):  python layout_preroute.py      (edits controller-board.kicad_pcb in place)
Coordinates: board frame of layout_build.py (origin = base centre, y into the board, seen from F.Cu).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet  # noqa: F401
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, '..', '..', 'controller-board.kicad_pcb'))
X0, Y0 = 100.0, 100.0
b = pcbnew.LoadBoard(PCB)

# runs on a fresh board from layout_build.py (removing items breaks pcbnew's SWIG typing, see memory notes)
assert not any(True for _ in b.GetTracks()), 'run layout_build.py first (board already has tracks)'


def P(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - y))


def pad(spec):
    ref, num = spec.split('.')
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            q = p.GetPosition()
            return (pcbnew.ToMM(q.x) - X0, Y0 - pcbnew.ToMM(q.y)), p.GetNetname()
    raise KeyError(spec)


def route(net, pts, w, layer=pcbnew.F_Cu):
    """pts: list of 'REF.PAD' or (x, y); consecutive points joined by straight tracks."""
    xy = []
    for p in pts:
        if isinstance(p, str):
            p_xy, pn = pad(p)
            assert pn == net, f'{p} is on {pn}, not {net}'
            xy.append(p_xy)
        else:
            xy.append(p)
    ni = b.FindNet(net)
    for a, c in zip(xy, xy[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(P(*a))
        t.SetEnd(P(*c))
        t.SetWidth(pcbnew.FromMM(w))
        t.SetLayer(layer)
        t.SetNet(ni)
        t.SetLocked(True)
        b.Add(t)


def via(net, x, y, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(P(x, y))
    v.SetWidth(pcbnew.FromMM(d))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetNet(b.FindNet(net))
    v.SetLocked(True)
    b.Add(v)


# +24V_IN: joint pad 1 -> F1 (left, away from J1.2 = GND, the only neighbour), TP10 on the way
route('/+24V_IN', ['J1.1', (-11.43, 1.0), (-12.8, 1.0), (-14.26, 2.46), 'F1.1'], 0.6)
route('/+24V_IN', [(-14.6, 2.46), 'TP10.1'], 0.6)
# +24V: F1.2 straight up into U5 VIN; bus left along y = 6.74 to C17 / C16 / C23 / D5 / TP13
route('+24V', ['F1.2', (-17.83, 6.74), 'U5.2'], 0.6)
route('+24V', ['F1.2', (-21.0, 6.74), 'C17.1'], 0.8)
route('+24V', [(-21.0, 6.74), (-23.4, 6.74), (-24.0, 6.12), 'C16.1', 'C23.1'], 0.8)
route('+24V', ['D5.1', (-27.0, 6.12)], 0.8)
route('+24V', ['TP13.1', 'D5.1'], 0.6)
# BOOT: U5.1 down/left to C18.1 (BOOT sits beside VIN in the IC; both are 24 V nets)
route('/BUCK_BOOT', ['U5.1', (-19.11, 10.2), (-20.8, 10.2), 'C18.1'], 0.3)
# SW node: one short 1.0 mm spine D7.K -> U5.8, a branch up into L1.1, and C18.2
route('/BUCK_SW', ['D7.1', (-19.11, 15.6), 'U5.8'], 1.0)
route('/BUCK_SW', [(-20.25, 15.6), (-20.25, 17.6)], 1.0)
route('/BUCK_SW', ['C18.2', (-20.8, 14.0), (-19.6, 14.6), (-19.11, 14.6)], 0.4)

# GND vias into In1 next to the loop / filter grounds (short, low inductance return)
for x, y in [(-22.2, 8.58),           # C17.2 (C_IN HF)
             (-24.6, 10.2), (-27.4, 10.2),  # C16.2, C23.2 (C_IN bulk)
             (-23.4, 10.3), (-22.3, 11.6),  # D7.2 (catch diode anode)
             (-21.6, 3.4), (-22.0, 4.6),     # D5.2 (input TVS)
             ]:
    via('GND', x, y)
route('GND', ['C17.2', (-22.2, 8.58)], 0.6)
route('GND', ['C16.2', (-24.6, 10.2)], 0.8)
route('GND', ['C23.2', (-27.4, 10.2)], 0.8)
route('GND', ['D7.2', (-23.4, 10.3)], 0.8)
route('GND', ['D7.2', (-22.3, 11.6)], 0.8)
route('GND', ['D5.2', (-21.6, 3.4)], 0.8)
route('GND', ['D5.2', (-22.0, 4.6)], 0.6)

b.BuildConnectivity()
pcbnew.SaveBoard(PCB, b)
print('pre-routes:', sum(1 for t in b.GetTracks() if t.IsLocked()), 'locked items')
