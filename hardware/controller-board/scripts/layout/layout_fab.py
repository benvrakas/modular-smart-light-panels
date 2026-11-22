"""Controller board: JLCPCB fabrication + assembly outputs (plain Python; calls kicad-cli).

usage:  python layout_fab.py
Writes hardware/controller-board/output/fab/:
  gerbers/ (4 copper, mask, paste, silk, edge; Protel extensions) + Excellon drill (PTH/NPTH merged, mm)
  controller-board_gerbers.zip      -> upload to JLCPCB (4 layers, 1.6 mm, JLC04161H-7628, WHITE mask, ENIG)
  BOM_controller-board_JLC.csv      -> copy of bom/BOM_controller-board.csv (Comment, Designator, Footprint, LCSC)
  CPL_controller-board_JLC.csv      -> Designator, Mid X, Mid Y, Layer, Rotation (F side only, BOM parts only)
  controller-board_assembly.pdf     -> F.Fab + courtyard + outline with references (hand assembly / jig)
  drc.json                          -> final DRC with schematic parity
"""
import csv
import os
import shutil
import subprocess
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.normpath(os.path.join(HERE, '..', '..'))
PCB = os.path.join(PRJ, 'controller-board.kicad_pcb')
FAB = os.path.join(PRJ, 'output', 'fab')
GER = os.path.join(FAB, 'gerbers')
CLI = r'C:\Program Files\KiCad\9.0\bin\kicad-cli.exe'
os.makedirs(GER, exist_ok=True)
for f in os.listdir(GER):          # clear old files (Google Drive may hold the folder itself open)
    os.remove(os.path.join(GER, f))


def run(*cmd):
    r = subprocess.run(list(cmd), capture_output=True, text=True)
    if r.returncode not in (0, 5):
        raise SystemExit(f'{cmd}\n{r.stdout}\n{r.stderr}')
    return r


run(CLI, 'pcb', 'export', 'gerbers', '-o', GER + os.sep, '--layers',
    'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts',
    '--subtract-soldermask', '--use-drill-file-origin', PCB)
run(CLI, 'pcb', 'export', 'drill', '-o', GER + os.sep, '--format', 'excellon', '--excellon-units', 'mm',
    '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', PCB)
zpath = os.path.join(FAB, 'controller-board_gerbers.zip')
with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(GER)):
        z.write(os.path.join(GER, f), f)

# CPL: KiCad position file -> JLC column names
pos = os.path.join(FAB, 'pos_kicad.csv')
run(CLI, 'pcb', 'export', 'pos', '-o', pos, '--side', 'front', '--format', 'csv', '--units', 'mm',
    '--exclude-dnp', '--use-drill-file-origin', PCB)
bom_src = os.path.join(PRJ, 'bom', 'BOM_controller-board.csv')
bom_refs = set()
with open(bom_src, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        bom_refs |= {r.strip() for r in row['Designator'].split(',')}
rows = []
with open(pos, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['Ref'] in bom_refs:
            rows.append([r['Ref'], f"{float(r['PosX']):.3f}mm", f"{float(r['PosY']):.3f}mm", 'Top',
                         f"{float(r['Rot']) % 360:.0f}"])
placed = {r[0] for r in rows}
assert placed == bom_refs, f'BOM/CPL mismatch: only BOM {bom_refs - placed}, only CPL {placed - bom_refs}'
with open(os.path.join(FAB, 'CPL_controller-board_JLC.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    w.writerows(sorted(rows, key=lambda r: (r[0].rstrip('0123456789'), int(r[0][len(r[0].rstrip('0123456789')):]))))
shutil.copyfile(bom_src, os.path.join(FAB, 'BOM_controller-board_JLC.csv'))
os.remove(pos)

run(CLI, 'pcb', 'export', 'pdf', '-o', os.path.join(FAB, 'controller-board_assembly.pdf'), '--layers',
    'F.Fab,F.Courtyard,Edge.Cuts,F.SilkS', '--mode-single', '--include-border-title', PCB)
run(CLI, 'pcb', 'drc', '--format', 'json', '--severity-all', '--schematic-parity', '--all-track-errors',
    '-o', os.path.join(FAB, 'drc.json'), PCB)
print('fab outputs ->', FAB, '|', len(rows), 'placed parts |', len(os.listdir(GER)), 'gerber/drill files')
