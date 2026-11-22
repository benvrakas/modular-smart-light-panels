"""Debug plot: pads/tracks/vias of F.Cu (red) and In2.Cu (blue) on a 1 mm grid in the board frame."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet, pcbnew
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
b = pcbnew.LoadBoard(os.path.join(HERE, '..', '..', 'controller-board.kicad_pcb'))
S = 24; W, H = 76 * S, 27 * S
im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
X = lambda x: (x + 38) * S; Y = lambda y: (25.5 - y) * S
tm = lambda v: (pcbnew.ToMM(v.x) - 100, 100 - pcbnew.ToMM(v.y))
for gx in range(-38, 39):
    d.line([(X(gx), 0), (X(gx), H)], fill=(225, 225, 225) if gx % 5 else (170, 170, 170))
    if gx % 5 == 0: d.text((X(gx) + 2, 2), str(gx), fill='black')
for gy in range(-1, 26):
    d.line([(0, Y(gy)), (W, Y(gy))], fill=(225, 225, 225) if gy % 5 else (170, 170, 170))
    if gy % 5 == 0: d.text((2, Y(gy) + 2), str(gy), fill='black')
hl = set(sys.argv[1].split(',')) if len(sys.argv) > 1 else set()
for fp in b.GetFootprints():
    for p in fp.Pads():
        if not p.IsOnLayer(pcbnew.F_Cu): continue
        bb = p.GetBoundingBox()
        x0, y1 = tm(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())); x1, y0 = tm(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
        col = (255, 150, 0) if p.GetNetname() in hl else ((120, 200, 120) if p.GetNetname() == 'GND' else (230, 120, 120))
        d.rectangle([X(x0), Y(y1), X(x1), Y(y0)], fill=col)
    x, y = tm(fp.GetPosition()); d.text((X(x) - 6, Y(y) - 5), fp.GetReference(), fill='black')
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        x, y = tm(t.GetPosition()); r = 0.3 * S
        d.ellipse([X(x) - r, Y(y) - r, X(x) + r, Y(y) + r], fill=(255, 150, 0) if t.GetNetname() in hl else 'black')
        continue
    lay = t.GetLayer()
    if lay not in (pcbnew.F_Cu, pcbnew.In2_Cu): continue
    col = (255, 150, 0) if t.GetNetname() in hl else ((200, 0, 0) if lay == pcbnew.F_Cu else (0, 0, 220))
    (a, c) = tm(t.GetStart()), tm(t.GetEnd())
    d.line([(X(a[0]), Y(a[1])), (X(c[0]), Y(c[1]))], fill=col, width=max(2, int(pcbnew.ToMM(t.GetWidth()) * S)))
out = os.path.join(HERE, '..', '..', 'output', 'layout', sys.argv[2] if len(sys.argv) > 2 else 'map.png')
im.save(out); print(out)
