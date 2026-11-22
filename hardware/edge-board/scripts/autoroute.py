"""Export -> Freerouting (headless) -> import, with the V6 board rules Freerouting cannot read from KiCad.
Adapted from hardware/archive/edge-board-v5/output/placement-trial/autoroute.py (V5).

usage (KiCad 9 python):
  python autoroute.py IN.kicad_pcb OUT.kicad_pcb WORKDIR CONFIG.json [passes]
CONFIG.json keys (all optional):
  drop:      [net, ...]               nets Freerouting ignores (fully hand-routed)
  f_only:    [net, ...]               nets restricted to F.Cu (reason given in the caller's notes)
  b_only:    [net, ...]               nets restricted to B.Cu
  keepouts:  [[kind, layer, x0, z0, x1, z1], ...]  kind = wire_keepout | via_keepout | keepout, board mm (x, z)
  edge:      copper-free margin along the outline (mm), default 0.35
Existing tracks/vias are locked (Freerouting keeps them).
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbutil import pcbnew, X0, Y0  # noqa: E402  (pcbutil disables wx asserts first)

src, dst, work, cfgp = sys.argv[1:5]
passes = sys.argv[5] if len(sys.argv) > 5 else '40'
cfg = json.load(open(cfgp, encoding='utf-8'))
FR = os.path.expandvars(r'%LOCALAPPDATA%\freerouting\freerouting.exe')
os.makedirs(work, exist_ok=True)
dsn, ses, log = (os.path.join(work, n) for n in ('route.dsn', 'route.ses', 'freerouting.log'))


def D(x, z):  # board (x, z) mm -> DSN um
    return f'{(X0 + x) * 1000:.0f} {(z - Y0) * 1000:.0f}'


def tok(n):
    return f'"{n}"' if re.search(r'[()\s"]', n) else n


b = pcbnew.LoadBoard(src)
for t in b.GetTracks():
    t.SetLocked(True)
assert pcbnew.ExportSpecctraDSN(b, dsn)
s = open(dsn, encoding='utf-8').read()

for n in cfg.get('drop', []):
    s = re.sub(r'\(net ' + re.escape(tok(n)) + r'\s*\(pins[^)]*\)\s*\)', '', s)
m = re.search(r'\(class kicad_default ([^(]*)', s)
members = m.group(1).split()
special = {}
for key, lay in (('f_only', 'F.Cu'), ('b_only', 'B.Cu')):
    for n in cfg.get(key, []):
        special[tok(n)] = lay
keep = [n for n in members if n not in special and n not in [tok(d) for d in cfg.get('drop', [])]]
s = s.replace(m.group(0), '(class kicad_default ' + ' '.join(keep) + '\n      ', 1)
cls = ''
for lay in ('F.Cu', 'B.Cu'):
    ns = [n for n, l in special.items() if l == lay]
    if ns:
        cls += (f'    (class only_{lay[0]} {" ".join(ns)}\n      (circuit (use_via "Via[0-1]_600:300_um") (use_layer {lay}))\n'
                '      (rule (width 250) (clearance 200))\n    )\n')
s = s.replace('    (class kicad_default', cls + '    (class kicad_default', 1)

# keepouts
bd = [float(v) for v in re.search(r'\(boundary\s*\(path pcb 0\s*([-\d\s.]+)\)', s).group(1).split()]
xs, ys = bd[0::2], bd[1::2]
x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
e = cfg.get('edge', 0.35) * 1000
ko = ''
for lay in ('F.Cu', 'B.Cu'):
    for (a, bq, c, d) in ((x1, y1, x2, y1 + e), (x1, y2 - e, x2, y2), (x1, y1, x1 + e, y2), (x2 - e, y1, x2, y2)):
        ko += f'    (wire_keepout "edge" (polygon {lay} 0  {a:.0f} {bq:.0f}  {c:.0f} {bq:.0f}  {c:.0f} {d:.0f}  {a:.0f} {d:.0f}))\n'
for i, (kind, lay, xa, za, xb, zb) in enumerate(cfg.get('keepouts', [])):
    ko += (f'    ({kind} "k{i}" (polygon {lay} 0  {D(xa, za)}  {D(xb, za)}  {D(xb, zb)}  {D(xa, zb)}))\n')
s = s.replace('    (via "Via', ko + '    (via "Via', 1)
open(dsn, 'w', encoding='utf-8').write(s)

with open(log, 'w', encoding='utf-8') as lf:
    subprocess.run([FR, '-de', dsn, '-do', ses, '-mp', passes, '--gui.enabled=false'],
                   stdout=lf, stderr=subprocess.STDOUT, timeout=1800)
txt = open(log, encoding='utf-8', errors='replace').read()
m = re.findall(r'\((\d+) unrouted and (\d+) violations\)', txt)
print('freerouting final:', m[-1] if m else 'n/a', '| unrouted nets:',
      sorted(set(re.findall(r"Net '([^']+)' \(\d+ unrouted", txt))))
assert pcbnew.ImportSpecctraSES(b, ses), 'SES import failed'
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
print('tracks:', sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'),
      'vias:', sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA'))
