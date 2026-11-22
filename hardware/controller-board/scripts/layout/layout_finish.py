"""Controller board: post-route finishing (after layout_route.py).

usage (KiCad 9 python):  python layout_finish.py      (edits controller-board.kicad_pcb in place)

  - F.Cu and In2.Cu GND pours (lowest priority). Thermal reliefs on small passives (reflow / no tombstoning) and
    on J1.2 (hand drag-soldered joint); solid connection on the power parts' ground pads and U5's thermal pad.
  - GND stitching vias on a 2.5 mm grid wherever every layer is GND-filled there (F, In1, In2, B), so the
    pours, the In1 plane and the B.Cu plane are one low-impedance ground.
  - Silkscreen: references move to F.Fab (assembly drawing); F.Silk keeps outlines, pin-1 marks and a short
    board label. B.Silk stays empty (the chamber face is plain white mask).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet  # noqa: F401
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, '..', '..', 'controller-board.kicad_pcb'))
X0, Y0 = 100.0, 100.0
BASE, DEPTH = 72.0, 24.0
TAN30 = math.tan(math.radians(30))
TOPHALF = BASE / 2 - DEPTH * TAN30

b = pcbnew.LoadBoard(PCB)
assert not any(z.GetZoneName() in ('GND F', 'GND In2') for z in b.Zones()), 'run on a freshly routed board'


def P(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - y))


FULL = [(-BASE / 2 - 1, -1), (BASE / 2 + 1, -1), (TOPHALF + 1, DEPTH + 1), (-TOPHALF - 1, DEPTH + 1)]


def zone(name, layer, net, pts, prio=0, clearance=0.25, thermal=True):
    z = pcbnew.ZONE(b)
    z.SetZoneName(name)
    lset = pcbnew.LSET()
    lset.AddLayer(layer)
    z.SetLayerSet(lset)
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(pcbnew.FromMM(clearance))
    z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(pcbnew.FromMM(0.25))
    z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for p in pts:
        o.Append(P(*p))
    b.Add(z)
    return z


zone('GND F', pcbnew.F_Cu, 'GND', FULL)
zone('GND In2', pcbnew.In2_Cu, 'GND', FULL)

# solid ground on the power parts (current paths, heat); thermal on everything else (default above)
SOLID = {('U5', '7'), ('U5', '9'), ('D7', '2'), ('D5', '2'), ('C16', '2'), ('C23', '2'), ('C17', '2'),
         ('C19', '2'), ('C20', '2'), ('U3', '1'), ('D4', '3'), ('D6', '3'), ('TP3', '1'),
         ('C9', '2'), ('U2', '2')}  # the last two: too boxed in for two thermal spokes
for fp in b.GetFootprints():
    for pd in fp.Pads():
        if (fp.GetReference(), pd.GetNumber()) in SOLID:
            pd.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())

# ---------------------------------------------------------------------------------- stitching vias
gnd_fill = {}
for z in b.Zones():
    if z.GetNetname() == 'GND':
        for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(lay):
                poly = z.GetFilledPolysList(lay).CloneDropTriangulation()
                poly.Inflate(pcbnew.FromMM(-0.55), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.05))
                gnd_fill[lay] = poly
assert len(gnd_fill) == 4, gnd_fill.keys()
# keep clear of every hole and pad (incl. GND SMD pads: no vias in pads, paste would wick)
holes = [(pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y)) for v in b.GetTracks()
         if v.GetClass() == 'PCB_VIA']
pad_boxes = []
for fp in b.GetFootprints():
    for pd in fp.Pads():
        bb = pd.GetBoundingBox()
        pad_boxes.append((pcbnew.ToMM(bb.GetLeft()) - 0.5, pcbnew.ToMM(bb.GetTop()) - 0.5,
                          pcbnew.ToMM(bb.GetRight()) + 0.5, pcbnew.ToMM(bb.GetBottom()) + 0.5))
        if pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            holes.append((pcbnew.ToMM(pd.GetPosition().x), pcbnew.ToMM(pd.GetPosition().y)))
added = 0
gnd = b.FindNet('GND')
step = 2.5
y = 1.5
while y < DEPTH - 0.8:
    x = -BASE / 2
    while x < BASE / 2:
        X, Y = X0 + x, Y0 - y
        pt = P(x, y)
        ok = all(poly.Contains(pt) for poly in gnd_fill.values())
        ok = ok and all(math.hypot(X - hx, Y - hy) > 1.2 for hx, hy in holes)
        ok = ok and not any(l <= X <= r and t <= Y <= btm for l, t, r, btm in pad_boxes)
        if ok:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pt)
            v.SetWidth(pcbnew.FromMM(0.6))
            v.SetDrill(pcbnew.FromMM(0.3))
            v.SetNet(gnd)
            b.Add(v)
            holes.append((X, Y))
            added += 1
        x += step
    y += step
print('stitching vias added:', added)

# ---------------------------------------------------------------------------------- silkscreen
for fp in b.GetFootprints():
    rt = fp.Reference()
    rt.SetLayer(pcbnew.F_Fab)
    rt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.6), pcbnew.FromMM(0.6)))
    rt.SetTextThickness(pcbnew.FromMM(0.09))
    rt.SetPosition(fp.GetPosition())
    rt.SetVisible(True)


def silk_text(s, x, y, size=0.8, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetLayer(layer)
    t.SetPosition(P(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
    t.SetTextThickness(pcbnew.FromMM(0.12))
    b.Add(t)


silk_text('CTRL rev A', 21.0, 18.6)
silk_text('wall side', 21.0, 17.4)

filler.Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print('zones:', [z.GetZoneName() for z in b.Zones()])
