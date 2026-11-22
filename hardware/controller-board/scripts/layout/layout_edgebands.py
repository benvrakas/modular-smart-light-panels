"""Controller board: part-free stretches along each board edge (for the back-plate pocket ledge / snap hooks).

usage (KiCad 9 python):  python layout_edgebands.py [min_band_mm]
For every edge, samples every 0.5 mm and reports the stretches where no F.Cu courtyard comes within `min_band`
(default 1.5 mm) of the edge. Distances along the edge are from its first corner.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet  # noqa: F401
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
b = pcbnew.LoadBoard(os.path.normpath(os.path.join(HERE, '..', '..', 'controller-board.kicad_pcb')))
band = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
BASE, DEPTH = 72.0, 24.0
TAN30 = math.tan(math.radians(30))
TOPHALF = BASE / 2 - DEPTH * TAN30
tm = lambda v: (pcbnew.ToMM(v.x) - 100, 100 - pcbnew.ToMM(v.y))
polys = []
for fp in b.GetFootprints():
    fp.BuildCourtyardCaches()
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    assert cy.OutlineCount(), fp.GetReference()
    polys.append((fp.GetReference(), cy))
EDGES = [('base (J1 edge)', (-BASE / 2, 0), (BASE / 2, 0)), ('right 60 deg side', (BASE / 2, 0), (TOPHALF, DEPTH)),
         ('top', (TOPHALF, DEPTH), (-TOPHALF, DEPTH)), ('left 60 deg side', (-TOPHALF, DEPTH), (-BASE / 2, 0))]
for name, a, c in EDGES:
    L = math.hypot(c[0] - a[0], c[1] - a[1])
    ux, uy = (c[0] - a[0]) / L, (c[1] - a[1]) / L
    nx, ny = -uy, ux                                  # inward normal (counter-clockwise outline)
    free = []
    s = 1.8                                           # skip the corner fillets
    while s <= L - 1.8:
        px, py = a[0] + ux * s, a[1] + uy * s
        ok = True
        for k in range(0, int(band / 0.25) + 1):     # probe a line from the edge inward to `band`
            q = (px + nx * k * 0.25, py + ny * k * 0.25)
            v = pcbnew.VECTOR2I(pcbnew.FromMM(100 + q[0]), pcbnew.FromMM(100 - q[1]))
            if any(cy.Contains(v) for _, cy in polys):
                ok = False
                break
        free.append((s, ok))
        s += 0.5
    runs, start = [], None
    for s, ok in free + [(None, False)]:
        if ok and start is None:
            start = s
        if not ok and start is not None:
            runs.append((start, prev))
            start = None
        prev = s
    txt = ', '.join(f'{r0:.1f}-{r1:.1f}' for r0, r1 in runs if r1 - r0 >= 3)
    print(f'{name:18s} length {L:5.1f} mm; part-free >= {band} mm deep (>= 3 mm long): {txt}')
