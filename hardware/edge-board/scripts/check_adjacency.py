"""check_adjacency.py BOARD.kicad_pcb [mm=1.0]
SPEC 2 / SCHEMATIC-NOTES 9: +24V copper may only neighbour GND or 24 V-tolerant nets. Lists every copper item of
another net within `mm` of +24V copper on the same layer, and flags the non-tolerant ones."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbutil import pcbnew, mm, to_xz  # noqa: E402

# ID_K is 24 V-tolerant: D1 blocks it from SENSE (75 V rating) and R1 leads only to the SENSE_EDGE contact,
# which faces the neighbour's open-drain DRIVE (decision 0011). R2 (the bypass) is DNP.
TOL = {'GND', '/ID_K', '/CANH', '/CANL', '/SENSE', '/DRIVE', '/SPARE', '/SENSE_EDGE', '+24V', 'P', 'Q',
       '/P_DRV_A_SNS_B', '/Q_SNS_A_DRV_B', '+24V_IN', ''}
b = pcbnew.LoadBoard(sys.argv[1])
lim = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
items = list(b.GetTracks()) + [p for f in b.GetFootprints() for p in f.Pads()]
p24 = [i for i in items if i.GetNetname() in ('+24V', '+24V_IN')]
bad, seen = [], set()
for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
    a_l = [i for i in p24 if i.IsOnLayer(lay)]
    o_l = [i for i in items if i.IsOnLayer(lay) and i.GetNetname() not in ('+24V', '+24V_IN')]
    for a in a_l:
        sa = a.GetEffectiveShape(lay)
        for o in o_l:
            if sa.Collide(o.GetEffectiveShape(lay), mm(lim)):
                key = (lay, o.GetNetname(), a.m_Uuid.AsString(), o.m_Uuid.AsString())
                if key in seen: continue
                seen.add(key)
                n = o.GetNetname()
                if n not in TOL:
                    x, z = to_xz(o.GetPosition())
                    bad.append((pcbnew.LayerName(lay), n, round(x, 2), round(z, 2)))
nets = sorted({k[1] for k in seen})
print(f'nets within {lim} mm of +24V copper:', nets)
print('NON-TOLERANT neighbours:', bad if bad else 'none')
