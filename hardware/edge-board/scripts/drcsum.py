"""drcsum.py BOARD.kicad_pcb [OUT.json] [--schematic-parity] [--all]
Run kicad-cli DRC (all severities, optional schematic parity) and print a compact summary in board (x, z) mm.
Coordinates assume the build scripts' origin: x = X - 100, z = 100 - Y."""
import json
import os
import subprocess
import sys
from collections import Counter

b = sys.argv[1]
par = '--schematic-parity' in sys.argv
outs = [a for a in sys.argv[2:] if a.endswith('.json')]
out = outs[0] if outs else os.path.splitext(b)[0] + '_drc.json'
cmd = [r'C:\Program Files\KiCad\9.0\bin\kicad-cli.exe', 'pcb', 'drc', '--format', 'json', '--severity-all',
       '-o', out]
if par:
    cmd.append('--schematic-parity')
cmd.append(b)
r = subprocess.run(cmd, capture_output=True, text=True)
d = json.load(open(out, encoding='utf-8'))
IGN = {'silk_over_copper', 'silk_overlap', 'lib_footprint_issues', 'lib_footprint_mismatch', 'silk_edge_clearance'}
print('violations', dict(Counter((v['type'], v['severity']) for v in d['violations'])))
for v in d['violations']:
    if v['type'] in IGN and '--all' not in sys.argv:
        continue
    print(' ', v['severity'][0], v['type'], '|', ' / '.join(
        i['description'][:58] + ' @(%.2f,%.2f)' % (i['pos']['x'] - 100, 100 - i['pos']['y']) for i in v['items']))
print('unconnected', len(d['unconnected_items']))
for v in d['unconnected_items']:
    print('  ', ' / '.join(i['description'][:50] + ' @(%.1f,%.1f)' % (i['pos']['x'] - 100, 100 - i['pos']['y'])
                           for i in v['items']))
if par:
    print('parity', len(d.get('schematic_parity', [])))
    for v in d.get('schematic_parity', []):
        print('  ', v['type'], [i['description'] for i in v['items']])
