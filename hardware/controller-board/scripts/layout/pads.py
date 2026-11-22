import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet, pcbnew
b = pcbnew.LoadBoard(os.path.join(os.path.dirname(__file__), '..', '..', 'controller-board.kicad_pcb'))
refs = sys.argv[1].split(',')
for r in refs:
    fp = b.FindFootprintByReference(r)
    s = []
    for p in fp.Pads():
        q = p.GetPosition()
        s.append(f"{p.GetNumber()}:{p.GetNetname().lstrip('/')}@({pcbnew.ToMM(q.x)-100:.2f},{100-pcbnew.ToMM(q.y):.2f})")
    print(r, ' '.join(s[:12]))
