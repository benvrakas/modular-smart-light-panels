"""Controller board: rebuild controller-board.kicad_pcb from the schematic netlist and make the fab outputs.

usage:  python layout_all.py            (any Python 3; calls KiCad's bundled Python for the pcbnew steps)

  1 layout_rules.py     net classes + custom DRC rules (.kicad_pro / .kicad_dru)
  2 layout_build.py     new board: outline, stackup, footprints from output/controller-board.net, placement, planes
  3 layout_preroute.py  +24V input, buck hot loop and SW node, by script (locked)
  4 layout_route.py     import the pinned Freerouting session (route_pinned.ses); --rerun-route to route again
  5 layout_finish.py    F.Cu / In2 GND pours, stitching vias, silkscreen
  6 layout_fixups.py    the few connections Freerouting left open (2-layer A*), GND island vias
  7 layout_check.py     render + DRC with schematic parity  -> output/layout/final_*
  8 layout_fab.py       gerbers, drill, BOM, CPL, assembly PDF -> output/fab/
Re-export the netlist first if the schematic changed (scripts/verify_v6.py writes output/controller-board.net).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KPY = r'C:\Program Files\KiCad\9.0\bin\python.exe'
steps = [(sys.executable, 'layout_rules.py'), (KPY, 'layout_build.py'), (KPY, 'layout_preroute.py'),
         (KPY, 'layout_route.py'), (KPY, 'layout_finish.py'), (KPY, 'layout_fixups.py'),
         (sys.executable, 'layout_check.py', 'final', '--parity', '--detail'), (sys.executable, 'layout_fab.py')]
for st in steps:
    cmd = list(st)
    cmd[1] = os.path.join(HERE, cmd[1])
    if cmd[1].endswith('layout_route.py') and '--rerun-route' in sys.argv:
        cmd.append('--rerun')
    print('>>', ' '.join(os.path.basename(c) for c in cmd[1:]), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = '\n'.join(l for l in (r.stdout + r.stderr).splitlines()
                    if l.strip() and 'image handler' not in l and 'memory leak' not in l)
    print(out)
    if r.returncode != 0:
        raise SystemExit(f'step failed: {cmd[1]}')
