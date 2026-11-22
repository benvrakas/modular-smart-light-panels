"""fab.py BOARD.kicad_pcb FABDIR NAME [--cpl VARIANT=DNP1,DNP2 ...] [--no-render]
JLCPCB outputs with kicad-cli: Gerbers + Excellon drill (zipped), JLC CPL (Designator, Mid X, Mid Y, Layer,
Rotation) per variant (refs listed after '=' are left out), and top/bottom renders.
Positions are taken from kicad-cli's position export (SMD parts, both sides); JLC rotations still need a check in
their preview, as the KiCad and JLC zero orientations differ for some packages."""
import csv
import os
import subprocess
import sys
import zipfile

ZOOM = next((a.split('=')[1] for a in sys.argv if a.startswith('--zoom=')), '3.2')
CLI = r'C:\Program Files\KiCad\9.0\bin\kicad-cli.exe'
board, fab, name = sys.argv[1], sys.argv[2], sys.argv[3]
variants = {}
args = sys.argv[4:]
for i, a in enumerate(args):
    if a == '--cpl':
        k, _, v = args[i + 1].partition('=')
        variants[k] = [r for r in v.split(',') if r]
os.makedirs(fab, exist_ok=True)
gdir = os.path.join(fab, 'gerber')
os.makedirs(gdir, exist_ok=True)
for f in os.listdir(gdir):
    os.remove(os.path.join(gdir, f))


def run(*a):
    r = subprocess.run([CLI, *a], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit('kicad-cli failed: ' + ' '.join(a[:3]))
    return r.stdout


run('pcb', 'export', 'gerbers', '--layers', 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts',
    '--subtract-soldermask', '--use-drill-file-origin', '-o', gdir + os.sep, board)
run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-units', 'mm', '--excellon-separate-th',
    '--generate-map', '--map-format', 'gerberx2', '-o', gdir + os.sep, board)
zp = os.path.join(fab, f'{name}_gerbers.zip')
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(gdir)):
        z.write(os.path.join(gdir, f), f)
print('gerbers:', zp, len(os.listdir(gdir)), 'files')

pos = os.path.join(fab, f'{name}_pos_raw.csv')
run('pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '--exclude-fp-th', '--use-drill-file-origin', '-o', pos, board)
rows = list(csv.DictReader(open(pos, encoding='utf-8')))
os.remove(pos)
for var, dnp in (variants or {'all': []}).items():
    out = os.path.join(fab, f'CPL_{name}{"" if var == "all" else "_" + var}.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        n = 0
        for r in rows:
            if r['Ref'] in dnp:
                continue
            w.writerow([r['Ref'], r['PosX'] + 'mm', r['PosY'] + 'mm', 'Top' if r['Side'] == 'top' else 'Bottom',
                        r['Rot']])
            n += 1
    print('cpl:', out, n, 'parts')

if '--no-render' not in sys.argv:
    for side in ('top', 'bottom'):
        png = os.path.join(fab, f'{name}_render_{side}.png')
        run('pcb', 'render', '--side', side, '--width', '2400', '--height', '700', '--quality', 'high',
            '--background', 'opaque', '--zoom', ZOOM, '-o', png, board)
        print('render:', png)
