"""Active edge board: post-route finishing (after autoroute.py).
usage (KiCad 9 python): python finish.py routed.kicad_pcb out.kicad_pcb
- J1: allow bridged solder-mask apertures (the whole strip is one mask opening by design, SPEC 3.3)
- F.Cu GND pour (lowest priority; >= 1.0 mm from the bevelled wall edge, islands removed)
- F.Cu VIN_LDO pour around U3 (LDO heat spreading; LAYOUT-NOTES 13.3)
- refill, then report the narrowest In2 +12V cross-section (0.5 oz vs 1 oz inner copper, LAYOUT-NOTES 13.2)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kicad_quiet  # noqa
import pcbnew

X0, Y0 = 100.0, 100.0
src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
P = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - y))
bb = b.GetBoardEdgesBoundingBox()
HALF = (pcbnew.ToMM(bb.GetWidth()) - 0.05) / 2
H = pcbnew.ToMM(bb.GetHeight()) - 0.05

j1 = b.FindFootprintByReference('J1'); j1.SetAttributes(j1.GetAttributes() | pcbnew.FP_ALLOW_SOLDERMASK_BRIDGES)
# D3.1 (GND) is boxed in and tied to In1 by its own in-pad via (fanout.py): keep the F.Cu pour off it (no starved thermal)
next(p for p in b.FindFootprintByReference('D3').Pads() if p.GetNumber() == '1').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_NONE)

def zone(name, layer, net, pts, prio, clearance=0.3, thermal=True):
    z = pcbnew.ZONE(b); z.SetZoneName(name)
    l = pcbnew.LSET(); l.AddLayer(layer); z.SetLayerSet(l)
    z.SetNet(b.FindNet(net)); z.SetAssignedPriority(prio)
    z.SetLocalClearance(pcbnew.FromMM(clearance)); z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(pcbnew.FromMM(0.3)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(P(x, y))
    b.Add(z)

for z in [z for z in b.Zones() if z.GetZoneName() in ('FIN F GND', 'FIN F VIN_LDO')]:
    b.Delete(z)
# F.Cu GND: whole board except a 1.0 mm band along the wall edge (bevel) -- board-edge clearance does the rest
zone('FIN F GND', pcbnew.F_Cu, 'GND', [(-HALF, 1.0), (HALF, 1.0), (HALF, H), (-HALF, H)], 0)
# F.Cu VIN_LDO around U3's tab and C12 / R14 (heat), above the GND pour
zone('FIN F VIN_LDO', pcbnew.F_Cu, '/VIN_LDO', [(26.8, 7.2), (36.6, 7.2), (36.6, 11.6), (26.8, 11.6)], 5, thermal=False)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)

# narrowest +12V cross-section on In2 (vertical cuts every 0.1 mm; sum of copper along the cut)
z12 = next(z for z in b.Zones() if z.GetZoneName() == 'PL In2 +12V')
fill = z12.GetFilledPolysList(pcbnew.In2_Cu)
worst = (99, None); worst_run = (99, None)
x = -HALF + 1.0
while x < HALF - 1.0:
    cut = pcbnew.SHAPE_POLY_SET(); cut.NewOutline()
    for px, py in ((x - 0.01, -1), (x + 0.01, -1), (x + 0.01, H + 1), (x - 0.01, H + 1)): cut.Append(P(px, py))
    inter = fill.CloneDropTriangulation(); inter.BooleanIntersection(cut)
    runs = []
    for i in range(inter.OutlineCount()):
        bbx = inter.Outline(i).BBox(); runs.append(pcbnew.ToMM(bbx.GetHeight()))
    tot, big = sum(runs), max(runs) if runs else 0
    if tot < worst[0]: worst = (tot, x)
    if big < worst_run[0]: worst_run = (big, x)
    x += 0.1
print(f'In2 +12V narrowest total cross-section {worst[0]:.2f} mm at x {worst[1]:.1f}; '
      f'narrowest single continuous run {worst_run[0]:.2f} mm at x {worst_run[1]:.1f}')
