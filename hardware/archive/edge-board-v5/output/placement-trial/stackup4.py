"""Active edge board -> 4-layer (decision 0006): F.Cu / In1 GND plane / In2 power / B.Cu.
usage (KiCad 9 python): python stackup4.py in.kicad_pcb out.kicad_pcb H
Idempotent: removes/re-creates zones it owns (names starting 'PL ')."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kicad_quiet  # no wx assert pop-ups
import sys, pcbnew

X0, Y0 = 100.0, 100.0
src, dst, H = sys.argv[1], sys.argv[2], float(sys.argv[3])
P = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - y))
b = pcbnew.LoadBoard(src)
bb = b.GetBoardEdgesBoundingBox()
half = (pcbnew.ToMM(bb.GetWidth()) - 0.05) / 2

# --- layers: 4 copper, inner layers typed "power" (planes only; autorouter keeps traces off them)
b.SetCopperLayerCount(4)
ls = b.GetEnabledLayers(); ls.AddLayer(pcbnew.In1_Cu); ls.AddLayer(pcbnew.In2_Cu); b.SetEnabledLayers(ls)
b.SetLayerName(pcbnew.In1_Cu, "In1.Cu"); b.SetLayerName(pcbnew.In2_Cu, "In2.Cu")
b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER); b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)

nets = {n: b.FindNet(n) for n in ('GND', '+12V', '+5V')}
assert all(nets.values())

PLANES = [  # (name, layer, net, x1, x2, y1, y2, priority)
    # inner planes >=1.0 mm from the bevelled wall edge (springs ride over it), >=0.5 mm from
    # the ends and top (board-edge clearance does that) -- LAYOUT-NOTES 13.2
    ('PL In1 GND',       pcbnew.In1_Cu, 'GND',  -half, half, 1.0, H, 0),
    # In2 (LAYOUT-NOTES 13): +12V low | GND guard >=1 mm | +5V | >=0.5 gap | GND under the B.Cu bus band
    ('PL In2 +12V',      pcbnew.In2_Cu, '+12V', -half, half, 1.0, 11.5, 0),
    ('PL In2 GND guard', pcbnew.In2_Cu, 'GND',  -half, half, 12.0, 13.0, 0),
    ('PL In2 +5V',       pcbnew.In2_Cu, '+5V',  -half, half, 13.5, 17.7, 0),
    ('PL In2 GND bus',   pcbnew.In2_Cu, 'GND',  -half, half, 18.2, H, 0),
    ('PL B GND',         pcbnew.B_Cu,   'GND',  -half, half, 1.0, H, 0),
]

def make_zone(name, layer, net, x1, x2, y1, y2, prio):
    z = pcbnew.ZONE(b)
    z.SetZoneName(name)
    l = pcbnew.LSET(); l.AddLayer(layer); z.SetLayerSet(l)
    z.SetNet(nets[net]); z.SetAssignedPriority(prio)
    z.SetLocalClearance(pcbnew.FromMM(0.3))
    z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)       # SMD power pads/vias solid (current paths)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        o.Append(P(x, y))
    b.Add(z)

# removal last-but-one (SWIG quirk: nothing that needs typed objects may follow a Delete)
old = [z for z in b.Zones() if z.GetZoneName().startswith('PL ')]
for z in old:
    b.Delete(z)
for p in PLANES:
    make_zone(*p)
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
print("copper layers:", b.GetCopperLayerCount(), "| zones:", [z.GetZoneName() for z in b.Zones()])
