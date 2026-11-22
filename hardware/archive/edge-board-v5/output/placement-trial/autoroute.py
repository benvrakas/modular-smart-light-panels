"""Export -> Freerouting (headless) -> import, for the edge board.
usage (KiCad 9 python):
  python autoroute.py in.kicad_pcb out.kicad_pcb workdir [passes] [--drop NET,NET] [--fixed]
  --drop   nets removed from the DSN network (Freerouting ignores them; pads stay obstacles)
  --fixed  mark existing tracks/vias as fixed so Freerouting will not rip them up
Writes workdir/route.dsn, route.ses, freerouting.log; refills zones; reports unrouted."""
import os, sys, re, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kicad_quiet  # no wx pop-ups
import pcbnew

args = sys.argv[1:]
src, dst, work = args[0], args[1], args[2]
passes = args[3] if len(args) > 3 and not args[3].startswith('--') else '60'
drop = set(args[args.index('--drop') + 1].split(',')) if '--drop' in args else set()
FR = os.path.expandvars(r'%LOCALAPPDATA%\freerouting\freerouting.exe')
os.makedirs(work, exist_ok=True)
dsn, ses, log = (os.path.join(work, n) for n in ('route.dsn', 'route.ses', 'freerouting.log'))

b = pcbnew.LoadBoard(src)
if '--fixed' in args:
    for t in b.GetTracks():
        t.SetLocked(True)          # KiCad exports locked wiring as (type protect) -> Freerouting keeps it
assert pcbnew.ExportSpecctraDSN(b, dsn)

if drop:  # remove whole (net ...) blocks from the network section
    s = open(dsn, encoding='utf-8').read()
    for n in drop:
        tok = re.escape(f'"{n}"' if re.search(r'[()\s-]', n) else n)
        s = re.sub(r'\(net ' + tok + r'\s*\(pins[^)]*\)\s*\)', '', s)
        s = re.sub(r'(\(class [^()]*?)\s' + tok + r'(?=[\s)])', r'\1', s)
    open(dsn, 'w', encoding='utf-8').write(s)

# board-specific routing constraints Freerouting can't get from KiCad:
s = open(dsn, encoding='utf-8').read()
# (1) the B.Cu GND pour is refilled afterwards; as a DSN "plane" it would block B.Cu routing
s = re.sub(r'\s*\(plane \S+ \(polygon B\.Cu 0[^)]*\)\s*\)', '', s)
# (2) no traces on B.Cu over the contact strip (|x| < 25, y < 8.6): open mask, springs wipe it
ko = '    (wire_keepout "contact strip" (polygon B.Cu 0  75000 -100000  125000 -100000  125000 -91400  75000 -91400))\n'
# (3) 0.55 mm no-wire margin along every board edge (KiCad edge clearance 0.5; Freerouting uses 0.2)
bd = [float(v) for v in re.search(r'\(boundary\s*\(path pcb 0\s*([-\d\s.]+)\)', s).group(1).split()]
xs, ys = bd[0::2], bd[1::2]; x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys); m = 550
for lay in ('F.Cu', 'B.Cu'):
    for (a, bq, c, d) in ((x1, y1, x2, y1 + m), (x1, y2 - m, x2, y2), (x1, y1, x1 + m, y2), (x2 - m, y1, x2, y2)):
        ko += f'    (wire_keepout "edge" (polygon {lay} 0  {a:.0f} {bq:.0f}  {c:.0f} {bq:.0f}  {c:.0f} {d:.0f}  {a:.0f} {d:.0f}))\n'
# (4) no vias across the In2 +5V lane under U1/C7/C9 (fanout.py NO_VIA): antipads in a column would cut the lane
for lay in ('F.Cu', 'B.Cu'):
    ko += f'    (via_keepout "5V corridor" (polygon {lay} 0  75500 -85400  87500 -85400  87500 -83100  75500 -83100))\n'
    # wall edge (DSN y1 = board y 0; bevelled, springs ride over it): >= 1.0 mm, like the inner planes (LAYOUT-NOTES 13.2)
    ko += f'    (wire_keepout "wall edge" (polygon {lay} 0  {x1:.0f} {y1:.0f}  {x2:.0f} {y1:.0f}  {x2:.0f} {y1 + 1000:.0f}  {x1:.0f} {y1 + 1000:.0f}))\n'
s = s.replace('    (via "Via', ko + '    (via "Via', 1)
open(dsn, 'w', encoding='utf-8').write(s)

with open(log, 'w', encoding='utf-8') as lf:
    extra = args[args.index('--fr') + 1].split() if '--fr' in args else []
    subprocess.run([FR, '-de', dsn, '-do', ses, '-mp', passes, '--gui.enabled=false'] + extra,
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
