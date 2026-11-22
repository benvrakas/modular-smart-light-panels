"""Run ERC on both V6 schematics, export their netlists, and check every net against gen_v6_schematics.py.

Writes <project>/output/erc.rpt, erc.json and <project>.net. Exit code 1 on any ERC violation or net mismatch.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_v6_schematics as g  # noqa: E402
from kisexp import parse, find, first  # noqa: E402

CLI = r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"


def run(args):
    r = subprocess.run([CLI] + args, capture_output=True, text=True)
    if r.returncode not in (0, 5):  # 5 = ERC violations found
        print(r.stdout, r.stderr)
    return r


def netlist(path):
    t = parse(open(path, encoding='utf-8').read())
    nets = {}
    for n in find(first(t, 'nets'), 'net'):
        name = str(first(n, 'name')[1]).lstrip('/')
        nodes = {(str(first(x, 'ref')[1]), str(first(x, 'pin')[1])) for x in find(n, 'node')}
        nets[name] = nodes
    return nets


def expected(parts):
    nets = {}
    for p in parts:
        if p['key'] == 'FLAG':
            continue
        for pin, net in p['nets'].items():
            if net is not None:
                nets.setdefault(net, set()).add((p['ref'], pin))
    return nets


def check(project_dir, name, parts):
    sch = os.path.join(project_dir, name + '.kicad_sch')
    out = os.path.join(project_dir, 'output')
    os.makedirs(out, exist_ok=True)
    run(['sch', 'erc', '--format', 'report', '--severity-all', '-o', os.path.join(out, 'erc.rpt'), sch])
    run(['sch', 'erc', '--format', 'json', '--severity-all', '-o', os.path.join(out, 'erc.json'), sch])
    run(['sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', os.path.join(out, name + '.net'), sch])
    erc = json.load(open(os.path.join(out, 'erc.json'), encoding='utf-8'))
    viol = [v for s in erc.get('sheets', []) for v in s.get('violations', [])]
    print(f'== {name}: ERC violations: {len(viol)}')
    for v in viol[:40]:
        print('   ', v.get('severity'), v.get('type'), '|', v.get('description'), '|',
              '; '.join(i.get('description', '') for i in v.get('items', []))[:160])
    got = netlist(os.path.join(out, name + '.net'))
    exp = expected(parts)
    bad = 0
    for net, nodes in exp.items():
        if got.get(net) != nodes:
            bad += 1
            print(f'   NET MISMATCH {net}: expected {sorted(nodes)} got {sorted(got.get(net, []))}')
    for net, nodes in got.items():
        if net not in exp and not net.startswith('unconnected-'):
            bad += 1
            print(f'   UNEXPECTED NET {net}: {sorted(nodes)}')
    unconn = [n for n in got if n.startswith('unconnected-')]
    print(f'   nets checked: {len(exp)}, mismatches: {bad}, no-connect pins: {len(unconn)} {unconn}')
    return len(viol) + bad


if __name__ == '__main__':
    cp, _ = g.controller_parts()
    pp, _ = g.passive_parts()
    e = check(os.path.join(g.HW, 'controller-board'), 'controller-board', cp)
    for shape in ('hex', 'square', 'triangle'):
        e += check(os.path.join(g.HW, 'edge-board'), f'edge-board-{shape}', pp)
    print('TOTAL problems:', e)
    sys.exit(1 if e else 0)
