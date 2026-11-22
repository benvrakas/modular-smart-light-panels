import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet, pcbnew
b = pcbnew.LoadBoard(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'controller-board.kicad_pcb'))
f = lambda v: f"({pcbnew.ToMM(v.x)-100:.2f},{100-pcbnew.ToMM(v.y):.2f})"
for n in sys.argv[1].split(','):
    print('==', n)
    for t in b.GetTracks():
        if t.GetNetname() == n:
            if t.GetClass() == 'PCB_VIA':
                print('  via', f(t.GetPosition()))
            else:
                print('  trk', b.GetLayerName(t.GetLayer()), f(t.GetStart()), '->', f(t.GetEnd()), f'{pcbnew.ToMM(t.GetWidth()):.2f}')
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == n:
                print('  pad', fp.GetReference() + '.' + p.GetNumber(), f(p.GetPosition()))
