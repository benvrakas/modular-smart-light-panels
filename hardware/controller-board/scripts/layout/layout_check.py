"""Render and DRC helper for the controller board (plain Python; calls kicad-cli and pdftoppm).

usage:  python layout_check.py [tag] [--no-render] [--parity]
  - renders F side (copper, silk, fab, courtyard) and the inner/back copper to output/layout/<tag>_*.png
  - runs kicad-cli DRC (with --schematic-parity if asked) -> output/layout/<tag>_drc.json and prints a summary
"""
import collections
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.normpath(os.path.join(HERE, '..', '..'))
PCB = os.path.join(PRJ, 'controller-board.kicad_pcb')
OUTD = os.path.join(PRJ, 'output', 'layout')
CLI = r'C:\Program Files\KiCad\9.0\bin\kicad-cli.exe'
args = [a for a in sys.argv[1:] if not a.startswith('--')]
tag = args[0] if args else 'check'
os.makedirs(OUTD, exist_ok=True)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode not in (0, 5):
        print(r.stdout[-2000:], r.stderr[-2000:])
    return r


if '--no-render' not in sys.argv:
    views = {'F': 'F.Cu,F.SilkS,F.Fab,F.Courtyard,Edge.Cuts', 'In2': 'In2.Cu,Edge.Cuts', 'B': 'B.Cu,B.SilkS,Edge.Cuts',
             'In1': 'In1.Cu,Edge.Cuts'}
    for name, layers in views.items():
        pdf = os.path.join(OUTD, f'{tag}_{name}.pdf')
        run([CLI, 'pcb', 'export', 'pdf', '--layers', layers, '--mode-single', '--include-border-title',
             '-o', pdf, PCB] if False else
            [CLI, 'pcb', 'export', 'pdf', '--layers', layers, '--mode-single', '-o', pdf, PCB])
        # kicad-cli may write <name>.pdf or a folder; find it
        if os.path.isdir(pdf):
            inner = [f for f in os.listdir(pdf) if f.endswith('.pdf')][0]
            src = os.path.join(pdf, inner)
        else:
            src = pdf
        png = os.path.join(OUTD, f'{tag}_{name}')
        run(['pdftoppm', '-png', '-r', '300', '-singlefile', '-cropbox', src, png])

drc = os.path.join(OUTD, f'{tag}_drc.json')
cmd = [CLI, 'pcb', 'drc', '--format', 'json', '--severity-all', '--all-track-errors', '-o', drc]
if '--parity' in sys.argv:
    cmd.append('--schematic-parity')
run(cmd + [PCB])
d = json.load(open(drc, encoding='utf-8'))
cnt = collections.Counter()
for v in d.get('violations', []):
    cnt[(v['severity'], v['type'])] += 1
print('violations:', dict(cnt))
print('unconnected:', len(d.get('unconnected_items', [])))
print('parity:', len(d.get('schematic_parity', [])))
if '--detail' in sys.argv:
    for v in d.get('violations', []):
        items = ' | '.join(i['description'] for i in v['items'])
        print(f"  {v['severity']:7s} {v['type']:24s} {items}")
    for v in d.get('schematic_parity', []):
        print('  parity', v['type'], ' | '.join(i['description'] for i in v['items']))
