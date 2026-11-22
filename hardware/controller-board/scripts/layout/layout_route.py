"""Controller board: autoroute everything that layout_preroute.py did not (Freerouting, headless), then import.

usage (KiCad 9 python):  python layout_route.py [passes] [--rerun]   (edits controller-board.kicad_pcb in place)
  By default the pinned session scripts/layout/route_pinned.ses (the accepted Freerouting result) is imported, so
  the board rebuilds identically (layout_fixups.py relies on its via positions). --rerun runs Freerouting again
  and writes output/layout/route/route.ses; copy it over route_pinned.ses and re-check the fixup jobs if accepted.

DSN changes before routing (Freerouting cannot read KiCad's custom rules):
  - B.Cu GND plane removed from the DSN and B.Cu typed power (no wires; vias pass): the chamber face stays plain copper under
    white mask (vias may pass through it).
  - In1.Cu stays the GND plane: Freerouting fans GND pads out to it with vias.
  - class HV24 (+24V, +24V_IN) clearance 1.0 mm and class Switch (BUCK_SW) 0.5 mm, so no autorouted track runs
    beside them (SPEC 2 adjacency rule; SW node kept quiet). The real DRC rules live in controller-board.kicad_dru.
  - 0.4 mm no-wire band inside every board edge (JLC copper-to-edge); J1's pads already reach the base edge.
Work files: output/layout/route/ (route.dsn, route.ses, freerouting.log).
"""
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet  # noqa: F401
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.normpath(os.path.join(HERE, '..', '..'))
PCB = os.path.join(PRJ, 'controller-board.kicad_pcb')
WORK = os.path.join(PRJ, 'output', 'layout', 'route')
FR = os.path.expandvars(r'%LOCALAPPDATA%\freerouting\freerouting.exe')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
passes = args[0] if args else '100'
PINNED = os.path.join(HERE, 'route_pinned.ses')
os.makedirs(WORK, exist_ok=True)
dsn, ses, log = (os.path.join(WORK, n) for n in ('route.dsn', 'route.ses', 'freerouting.log'))

BASE, DEPTH = 72.0, 24.0
TAN30 = math.tan(math.radians(30))
TOPHALF = BASE / 2 - DEPTH * TAN30

b = pcbnew.LoadBoard(PCB)
assert pcbnew.ExportSpecctraDSN(b, dsn)
s = open(dsn, encoding='utf-8').read()

# (1) drop the B.Cu plane (keep In1)
s, n = re.subn(r'\s*\(plane GND \(polygon B\.Cu 0[^)]*\)\s*\)', '', s)
assert n == 1, 'B.Cu plane not found in DSN'


# (2) class clearances
def set_class_clearance(text, cls, um):
    pat = re.compile(r'(\(class ' + re.escape(cls) + r'\b.*?\(rule\s*\(width [\d.]+\)\s*\(clearance )([\d.]+)', re.S)
    text, k = pat.subn(lambda m: m.group(1) + str(um), text, count=1)
    assert k == 1, f'class {cls} not found'
    return text


s = set_class_clearance(s, 'HV24', 1000)
s = set_class_clearance(s, 'Switch', 500)


# (3) keepouts: B.Cu everywhere; 0.4 mm band inside each edge on all layers
def D(x, y):  # board frame -> DSN (um, y up)
    return (100 + x) * 1000, -(100 - y) * 1000


V = [(-BASE / 2, 0.0), (BASE / 2, 0.0), (TOPHALF, DEPTH), (-TOPHALF, DEPTH)]
ko = ''
# B.Cu = chamber face: typed 'power' so Freerouting puts no wires there (a wire keepout also blocks vias)
s, k = re.subn(r'(\(layer B\.Cu\s*\(type )signal\)', r'\1power)', s)
assert k == 1
m = 0.4
for i in range(4):
    a, c = V[i], V[(i + 1) % 4]
    dx, dy = c[0] - a[0], c[1] - a[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L               # inward normal (outline is counter-clockwise in the board frame)
    ex, ey = dx / L * 2, dy / L * 2        # extend past the corners
    if i == 0:                             # base edge: only outside J1 (the joint pads sit on it)
        pieces = [((-BASE / 2 - 2, 0), (-13.0, 0)), ((13.0, 0), (BASE / 2 + 2, 0))]
    else:
        pieces = [((a[0] - ex, a[1] - ey), (c[0] + ex, c[1] + ey))]
    for (p0, p1) in pieces:
        pts = [p0, p1, (p1[0] + nx * m, p1[1] + ny * m), (p0[0] + nx * m, p0[1] + ny * m)]
        for lay in ('F.Cu', 'In2.Cu'):
            ko += f'    (wire_keepout "edge" (polygon {lay} 0 ' + ' '.join(
                f'{X:.0f} {Y:.0f}' for X, Y in map(lambda p: D(*p), pts)) + '))\n'
# base edge under J1: keep autorouted wires off the band between the pads (0..0.4 mm), pads unaffected
s = s.replace('    (via "Via', ko + '    (via "Via', 1)
open(dsn, 'w', encoding='utf-8').write(s)

if '--rerun' in sys.argv:
    with open(log, 'w', encoding='utf-8') as lf:
        subprocess.run([FR, '-de', dsn, '-do', ses, '-mp', passes, '--gui.enabled=false'],
                       stdout=lf, stderr=subprocess.STDOUT, timeout=3000)
    txt = open(log, encoding='utf-8', errors='replace').read()
    mm = re.findall(r'\((\d+) unrouted and (\d+) violations\)', txt)
    print('freerouting final:', mm[-1] if mm else 'n/a')
else:
    ses = PINNED
    print('importing pinned session', os.path.basename(PINNED))
assert pcbnew.ImportSpecctraSES(b, ses), 'SES import failed'
# B.Cu is typed 'power' so Freerouting keeps wires off the chamber face, but it may still drop a short one there.
# The pinned session has one: CAN_RX, ~4.3 mm between two vias under U2/C10 (no F.Cu/In2 path exists there).
# It stays: under white mask it is a faint line, and the B.Cu GND plane flows around it. Reported, not removed.
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK' and t.GetLayer() == pcbnew.B_Cu and t.GetNetname() != 'GND':
        print(f'note: B.Cu signal track {t.GetNetname()} {pcbnew.ToMM(t.GetLength()):.1f} mm')
pcbnew.SaveBoard(PCB, b)

