"""check_symmetry.py BOARD: every face-A (F.Cu) copper item must have a 180-degree image on face B
(x -> -x, B.Cu) with the SENSE/DRIVE cross nets swapped. Injection items (F1, J1, J2, +24V_IN, their tracks) excluded."""
import os, sys
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'edge-board', 'scripts')))
from pcbutil import pcbnew, to_xz  # noqa: E402
SIG = {'/DRV_A_SNS_B': '/SNS_A_DRV_B', '/SNS_A_DRV_B': '/DRV_A_SNS_B'}
b = pcbnew.LoadBoard(sys.argv[1])
def key(x, z, n, w=0): return (round(x, 2), round(z, 2), n, round(w, 2))
F, B = set(), set()
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        x, z = to_xz(t.GetPosition()); F.add(('via',) + key(x, z, t.GetNetname())); continue
    a, c = to_xz(t.GetStart()), to_xz(t.GetEnd())
    seg = tuple(sorted([key(*a, t.GetNetname()), key(*c, t.GetNetname())]))
    (F if t.GetLayer() == pcbnew.F_Cu else B).add(('trk', seg, round(pcbnew.ToMM(t.GetWidth()), 2)))
for fp in b.GetFootprints():
    if fp.GetReference() in ('F1', 'J1', 'J2'): continue
    for p in fp.Pads():
        x, z = to_xz(p.GetPosition())
        (B if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else F).add(('pad',) + key(x, z, p.GetNetname()))
def img(it):
    if it[0] == 'via': return ('via', round(-it[1], 2), it[2], SIG.get(it[3], it[3]), it[4])
    if it[0] == 'pad': return ('pad', round(-it[1], 2), it[2], SIG.get(it[3], it[3]), it[4])
    seg = tuple(sorted([(round(-p[0], 2), p[1], SIG.get(p[2], p[2]), p[3]) for p in it[1]])); return ('trk', seg, it[2])
vias = {i for i in F if i[0] == 'via'}
Fc = {i for i in F if i[0] != 'via'}
miss = [i for i in Fc if img(i) not in B and '/+24V_IN' not in str(i)]
missv = [v for v in vias if img(v) not in vias and v[1] < 24]   # x > 24: injection vias
extraB = [i for i in B if img(i) not in Fc and '/+24V_IN' not in str(i)]
print('face-A items', len(Fc), 'face-B items', len(B), 'vias', len(vias))
print('A items without a B image (injection excluded):', miss)
print('B items without an A image:', extraB)
print('vias without an image:', missv)
