"""Controller board: independent checks of the layout rules that DRC expresses only indirectly.

usage (KiCad 9 python):  python layout_verify.py  -> prints a report (also used for LAYOUT-NOTES.md)

  1 +36V neighbours (SPEC 2 / decision 0011): for every +36V / +36V_IN copper item (tracks, pads, vias), the nearest
    copper of each other net on the same layer. Anything within 1.0 mm must be GND or a 36 V-tolerant net.
  2 SW node (SCHEMATIC-NOTES 12): distance from BUCK_SW copper to the crystal and the ADC node.
  3 Interface: J1 pad centres, test pad centres (board frame: origin = base centre, y into the board, seen from F.Cu).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet  # noqa: F401
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, '..', '..', 'controller-board.kicad_pcb'))
b = pcbnew.LoadBoard(PCB)
tm = lambda v: (pcbnew.ToMM(v.x) - 100, 100 - pcbnew.ToMM(v.y))
HV = {'+36V', '/+36V_IN'}
TOL = {'GND', '/CANH', '/CANL', '/SPARE', '/SENSE', '/DRIVE', '/BUCK_SW', '/BUCK_BOOT', 'unconnected-(U5-EN-Pad3)'} | HV
LAYERS = {pcbnew.F_Cu: 'F.Cu', pcbnew.In1_Cu: 'In1.Cu', pcbnew.In2_Cu: 'In2.Cu', pcbnew.B_Cu: 'B.Cu'}

items = []   # (net, layer, shape, label)
for t in b.GetTracks():
    for lay in LAYERS:
        if t.IsOnLayer(lay):
            items.append((t.GetNetname(), lay, t.GetEffectiveShape(lay), t.GetClass()))
for fp in b.GetFootprints():
    for pd in fp.Pads():
        for lay in LAYERS:
            if pd.IsOnLayer(lay):
                items.append((pd.GetNetname(), lay, pd.GetEffectiveShape(lay), f'{fp.GetReference()}.{pd.GetNumber()}'))


def dist(s1, s2, limit=12.0):
    if s1.Collide(s2, 0):
        return 0.0
    lo, hi = 0.0, pcbnew.FromMM(limit)
    if not s1.Collide(s2, int(hi)):
        return limit
    for _ in range(18):
        mid = (lo + hi) / 2
        if s1.Collide(s2, int(mid)):
            hi = mid
        else:
            lo = mid
    return pcbnew.ToMM(int(hi))


# 1 +36V neighbours
nearest = {}
for n1, l1, s1, lab1 in items:
    if n1 not in HV:
        continue
    for n2, l2, s2, lab2 in items:
        if l2 != l1 or n2 in HV or not n2:
            continue
        d = dist(s1, s2, 3.0)
        key = (n2, LAYERS[l1])
        if d < nearest.get(key, (99,))[0]:
            nearest[key] = (d, lab1, lab2)
print('1. Nearest copper to +36V / +36V_IN, per net (same layer), within 3 mm:')
bad = 0
for (n2, lay), (d, a, c) in sorted(nearest.items(), key=lambda kv: kv[1][0]):
    if d >= 3.0:
        continue
    ok = n2 in TOL or d >= 1.0
    bad += not ok
    print(f'   {d:5.2f} mm  {n2:28s} {lay:7s} ({a} <-> {c})  {"ok" if ok else "VIOLATION"}')
print(f'   -> {"PASS" if not bad else "FAIL"}: every net within 1.0 mm of +36V copper is GND or 36 V-tolerant')

# 2 SW node
print('2. BUCK_SW copper to sensitive nets:')
for target in ('/OSC_IN', '/OSC_OUT', '/SENSE_ADC', '/BUCK_FB'):
    best = (99, '', '')
    for n1, l1, s1, lab1 in items:
        if n1 != '/BUCK_SW':
            continue
        for n2, l2, s2, lab2 in items:
            if n2 == target and l2 == l1:
                d = dist(s1, s2, 30.0)
                if d < best[0]:
                    best = (d, lab1, lab2)
    print(f'   {target:12s} {best[0]:5.1f} mm ({best[1]} <-> {best[2]})')

# 3 interface
print('3. J1 pads (centre x, y; 1.3 x 2.0 mm, F.Cu, running to the base edge y = 0):')
j1 = b.FindFootprintByReference('J1')
for pd in sorted(j1.Pads(), key=lambda p: int(p.GetNumber())):
    x, y = tm(pd.GetPosition())
    print(f'   J1.{pd.GetNumber():2s} {pd.GetNetname().lstrip("/"):14s} x {x:7.2f}  y {y:5.2f}')
print('   test pads (D1.5 mm, F.Cu):')
for fp in sorted(b.GetFootprints(), key=lambda f: int(f.GetReference()[2:]) if f.GetReference().startswith('TP') else 0):
    if fp.GetReference().startswith('TP'):
        x, y = tm(fp.GetPosition())
        print(f'   {fp.GetReference():5s} {fp.Pads()[0].GetNetname().lstrip("/"):11s} x {x:6.2f}  y {y:5.2f}')
