"""Controller board (roadmap WP 1.4): build controller-board.kicad_pcb from the schematic netlist.

Creates the board from scratch every run (no hand edits to lose):
  - 4 copper layers (F.Cu parts / wall side, In1 GND, In2 signals, B.Cu GND = white chamber face)
  - trapezoid outline (60 deg sides, base 72 mm on the code-0 edge board, depth D)
  - every netlist footprint with its schematic path, fields and pad nets (same result as F8; checked by
    kicad-cli DRC --schematic-parity), placed from PLACE below
  - In1.Cu and B.Cu GND planes
Routing, the F.Cu / In2 pours and the fab outputs are later steps (layout_route.py, layout_finish.py).

usage (KiCad 9 python):  python layout_build.py [out.kicad_pcb]
Board frame used below: origin at the centre of the trapezoid base (the J1 joint edge), x to the right and
y INTO the board (away from the edge board), both as seen from F.Cu (the wall side). KiCad y = Y0 - y.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet  # noqa: F401  (no wx assert pop-ups)
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.normpath(os.path.join(HERE, '..', '..'))
NET = os.path.join(PRJ, 'output', 'controller-board.net')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PRJ, 'controller-board.kicad_pcb')
STD = 'C:/Program Files/KiCad/9.0/share/kicad/footprints/'
ML = os.path.normpath(os.path.join(PRJ, '..', 'lib', 'footprints', 'ModularLight.pretty'))

X0, Y0 = 100.0, 100.0
BASE = 72.0                     # trapezoid base (SPEC 3.5: <= ~72 mm)
DEPTH = 24.0                    # SPEC 3.5: 20-25 mm
TAN30 = math.tan(math.radians(30))
TOPHALF = BASE / 2 - DEPTH * TAN30
R_BASE, R_TOP = 1.0, 1.0        # corner fillets (60 deg base corners, 120 deg top corners)


def P(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - y))


def halfwidth(y):
    return BASE / 2 - y * TAN30


# ref: (x, y, rotation_deg). Rotation is KiCad's (counter-clockwise as seen from F.Cu).
PLACE = {
    'J1': (0.0, 0.0, 0),
    # --- 36 V input: J1.1 -> F1 -> +36V (D5 TVS, C_IN) ---------------------------------------------
    'F1': (-18.0, 4.6, 90),      # pad1 (+36V_IN) bottom, pad2 (+36V) top, right under U5 VIN
    'TP10': (-14.6, 4.4, 0),     # +36V_IN (before F1)
    'D5': (-25.0, 3.4, 0),       # pad1 K (+36V) left, pad2 A (GND) right
    'TP13': (-30.6, 3.6, 0),     # +36V (after F1)
    'C16': (-24.6, 7.6, 90),     # 10u/50V: pad1 (+36V) bottom
    'C23': (-27.4, 7.6, 90),
    'C17': (-21.0, 7.8, 90),     # 100n at VIN: pad1 (+36V) bottom, pad2 GND top
    # --- buck U5 (TPS54360B) -------------------------------------------------------------------------
    'U5': (-17.2, 12.4, 90),     # VIN row at the bottom (BOOT VIN EN RT), SW GND COMP FB on top
    'C18': (-20.8, 12.4, 90),    # BOOT cap: pad1 BOOT bottom, pad2 SW top
    'D7': (-23.4, 13.6, 270),    # catch diode: pad1 K (SW) top, pad2 A (GND) bottom
    'L1': (-18.0, 19.6, 0),      # pad1 SW left, pad2 +5V right
    'C19': (-12.6, 21.2, 0),     # 22u out: pad1 +5V left
    'C20': (-12.6, 18.9, 0),
    'R16': (-13.0, 15.9, 270),   # FB top: pad1 +5V top, pad2 FB bottom
    'R17': (-13.0, 12.6, 270),   # FB bottom: pad1 FB top, pad2 GND bottom
    'R19': (-13.0, 9.3, 270),    # RT: pad1 RT top, pad2 GND
    'R20': (-11.0, 15.9, 270),   # comp R: pad1 COMP top, pad2 CZ
    'C21': (-11.0, 12.6, 270),   # comp C: pad1 CZ top, pad2 GND
    'C22': (-11.0, 9.3, 270),    # comp HF: pad1 COMP top, pad2 GND
    'TP11': (-8.6, 21.8, 0),     # +5V
    # --- 3.3 V -----------------------------------------------------------------------------------------
    'U3': (-5.0, 18.0, 180),     # HT7533 SOT-89, pins face right (GND VIN VOUT), tab (VIN) left
    'C12': (-5.0, 21.7, 0),      # LDO in (+5V)
    'C13': (-1.0, 18.6, 270),    # LDO out: pad1 (+3V3) top
    'C9': (1.0, 16.6, 90),       # 1u on +3V3
    'U6': (-0.6, 13.4, 0),       # TLV431 3V3 shunt
    'R24': (2.6, 13.6, 90),
    'R25': (-3.4, 13.6, 90),
    # --- LED rail switch + data (above J1 pads 3-5) ---------------------------------------------------
    'Q1': (-7.4, 5.4, 0),        # AO3401A: G top-left, S (+5V) bottom-left, D (+5V_LED) right -> J1.3 below
    'TP12': (-11.0, 6.4, 0),     # +5V_LED (kept away from J1.1 so no +5V_LED copper runs past the +36V pad)
    'R7': (-3.81, 4.7, 90),      # LED_RETURN (J1.4) -> 2k2
    'R5': (-1.27, 4.7, 270),     # 33R -> J1.5
    'R26': (1.27, 4.7, 90),      # DNP SPARE -> PB1, at J1.6
    'C25': (-8.0, 8.6, 0),
    'R8': (-4.9, 8.6, 0),
    'U4': (-0.9, 8.6, 0),
    'C15': (2.0, 8.6, 90),
    'R21': (-8.2, 11.0, 0),
    'R22': (-5.0, 11.0, 0),
    'Q2': (-6.2, 13.6, 0),
    'R18': (-9.2, 14.0, 90),
    # --- MCU -------------------------------------------------------------------------------------------
    'U1': (8.0, 15.5, 270),      # top row pins 1..10 right->left, bottom row 11..20 left->right
    'Y1': (13.8, 20.6, 0),
    'C5': (13.2, 17.4, 0),
    'C6': (17.4, 20.8, 90),
    'C7': (9.2, 10.6, 0),        # VDD
    'C8': (9.6, 21.4, 90),       # VDDA
    'C10': (13.2, 15.6, 0),      # NRST
    'R15': (13.2, 13.6, 0),      # BOOT0
    # --- SENSE ADC side (top-left of U1, >= 10 mm from the SW node) ------------------------------------
    'R10': (0.4, 21.8, 0),
    'D2': (4.4, 21.6, 0),
    'C14': (7.6, 21.4, 90),
    # --- CAN -------------------------------------------------------------------------------------------
    'U2': (17.6, 10.0, 270),     # bottom row VIO CANL CANH STB, top row RXD VCC GND TXD
    'C11': (17.0, 15.2, 0),      # VCC
    'C24': (13.6, 8.0, 90),      # VIO
    'D4': (5.08, 5.0, 90),       # CAN TVS at J1.7/J1.8
    'R12': (21.8, 11.0, 90),
    'JP1': (21.8, 14.6, 90),
    # --- discovery: SENSE / DRIVE ----------------------------------------------------------------------
    'D6': (10.16, 5.0, 90),      # SENSE/DRIVE TVS at J1.9/J1.10
    'R11': (15.4, 4.2, 180),     # 470R 1206: pad2 (DRIVE) left toward J1.10
    'Q3': (20.0, 4.4, 0),
    'R23': (21.6, 7.7, 90),
    'R9': (6.0, 8.8, 90),        # SENSE pull-up (0805)
    # --- test pads (pogo jig from the wall side), 2.8 mm grid in the right wedge --------------------------
    'TP1': (25.0, 4.0, 0), 'TP2': (27.8, 4.0, 0), 'TP3': (30.6, 4.0, 0),
    'TP4': (25.0, 6.8, 0), 'TP5': (27.8, 6.8, 0), 'TP6': (30.6, 6.8, 0),
    'TP7': (25.0, 9.6, 0), 'TP8': (27.8, 9.6, 0), 'TP9': (25.0, 12.4, 0),
}


# ------------------------------------------------------------------------------------------- netlist
def parse(s):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', s)
    stack = [[]]
    for t in toks:
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return stack[0][0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def val(node, key, default=None):
    r = find(node, key)
    return r[0][1] if r and len(r[0]) > 1 else default


nl = parse(open(NET, encoding='utf-8').read())
comps = {}
for c in find(find(nl, 'components')[0], 'comp'):
    ref = val(c, 'ref')
    fields = {}
    for fl in find(c, 'fields'):
        for f in find(fl, 'field'):
            fields[val(f, 'name')] = f[2] if len(f) > 2 else ''
    props = {val(p, 'name'): val(p, 'value', '') for p in find(c, 'property')}
    path = val(find(c, 'sheetpath')[0], 'tstamps') + val(c, 'tstamps')
    comps[ref] = dict(value=val(c, 'value'), fpid=val(c, 'footprint'), fields=fields, path=path,
                      dnp='dnp' in props, xbom='exclude_from_bom' in props)
pinnet, netnames = {}, []
for n in find(find(nl, 'nets')[0], 'net'):
    name = val(n, 'name')
    netnames.append(name)
    for nd in find(n, 'node'):
        pinnet[(val(nd, 'ref'), val(nd, 'pin'))] = name

missing = sorted(set(comps) - set(PLACE))
extra = sorted(set(PLACE) - set(comps))
assert not missing and not extra, f'placement table mismatch: missing {missing}, extra {extra}'

# ------------------------------------------------------------------------------------------- board
b = pcbnew.NewBoard(OUT)
b.SetCopperLayerCount(4)
ls = b.GetEnabledLayers()
for lay in (pcbnew.In1_Cu, pcbnew.In2_Cu):
    ls.AddLayer(lay)
b.SetEnabledLayers(ls)
b.SetLayerName(pcbnew.In1_Cu, 'In1.Cu')
b.SetLayerName(pcbnew.In2_Cu, 'In2.Cu')
b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)     # solid GND plane
b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_SIGNAL)
ds = b.GetDesignSettings()
ds.SetBoardThickness(pcbnew.FromMM(1.6))

# title block
tb = b.GetTitleBlock()
tb.SetTitle('Controller board (4-layer, rear of panel)')
tb.SetRevision('A')
tb.SetDate('2026-11-16')
tb.SetCompany('Modular Smart Light Panels')
tb.SetComment(0, 'SPEC V6.2.1, decisions 0009/0010/0011. Parts on F.Cu (wall side) only.')
tb.SetComment(1, 'B.Cu = chamber face: white mask, no parts, no silk. Generated by scripts/layout/.')


# outline: trapezoid with filleted corners
def seg(a, c):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(pcbnew.FromMM(0.05))
    s.SetStart(P(*a))
    s.SetEnd(P(*c))
    b.Add(s)


def arc(a, m, c):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_ARC)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(pcbnew.FromMM(0.05))
    s.SetArcGeometry(P(*a), P(*m), P(*c))
    b.Add(s)


V = [(-BASE / 2, 0.0), (BASE / 2, 0.0), (TOPHALF, DEPTH), (-TOPHALF, DEPTH)]
RAD = [R_BASE, R_BASE, R_TOP, R_TOP]
corners = []
for i, v in enumerate(V):
    prv, nxt = V[i - 1], V[(i + 1) % 4]
    u1 = ((prv[0] - v[0]), (prv[1] - v[1]))
    u2 = ((nxt[0] - v[0]), (nxt[1] - v[1]))
    l1, l2 = math.hypot(*u1), math.hypot(*u2)
    u1, u2 = (u1[0] / l1, u1[1] / l1), (u2[0] / l2, u2[1] / l2)
    ang = math.acos(u1[0] * u2[0] + u1[1] * u2[1])
    r = RAD[i]
    t = r / math.tan(ang / 2)
    a = (v[0] + u1[0] * t, v[1] + u1[1] * t)
    c = (v[0] + u2[0] * t, v[1] + u2[1] * t)
    bis = (u1[0] + u2[0], u1[1] + u2[1])
    bl = math.hypot(*bis)
    bis = (bis[0] / bl, bis[1] / bl)
    dc = r / math.sin(ang / 2)
    ctr = (v[0] + bis[0] * dc, v[1] + bis[1] * dc)
    m = (ctr[0] - bis[0] * r, ctr[1] - bis[1] * r)
    corners.append((a, m, c))
for i in range(4):
    arc(*corners[i])
    seg(corners[i][2], corners[(i + 1) % 4][0])

# nets
for name in netnames:
    if b.FindNet(name) is None:
        b.Add(pcbnew.NETINFO_ITEM(b, name))

# footprints (load all first: SWIG quirk)
fps = {}
for ref, c in sorted(comps.items()):
    lib, name = c['fpid'].split(':')
    fp = pcbnew.FootprintLoad(ML if lib == 'ModularLight' else STD + lib + '.pretty', name)
    assert fp is not None, c['fpid']
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fps[ref] = fp
for ref, fp in fps.items():
    c = comps[ref]
    fp.SetReference(ref)
    fp.SetValue(c['value'])
    fp.SetPath(pcbnew.KIID_PATH(c['path']))
    b.Add(fp)
    for k, v in c['fields'].items():
        if k in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description'):
            continue
        fp.SetField(k, v)
        fp.GetFieldByName(k).SetVisible(False)
    fp.SetDNP(c['dnp'])
    fp.SetExcludedFromBOM(c['xbom'])      # as F8 does: the symbol's setting wins over the library's
    for pd in fp.Pads():
        n = pinnet.get((ref, pd.GetNumber()))
        if n is not None:
            pd.SetNet(b.FindNet(n))
    x, y, rot = PLACE[ref]
    fp.SetPosition(P(x, y))
    fp.SetOrientationDegrees(rot)
    # silkscreen: small references on the wall side, values only on F.Fab
    rt = fp.Reference()
    rt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
    rt.SetTextThickness(pcbnew.FromMM(0.12))
    fp.Value().SetLayer(pcbnew.F_Fab)
    fp.Value().SetVisible(False)
# J1: the mask web between joint pads stays (1.24 mm gaps); no bridges needed


# planes: In1 GND solid, B.Cu GND solid (chamber face; uniform copper under the white mask)
def zone(name, layer, net, pts, prio=0, clearance=0.25, thermal=False, minw=0.25):
    z = pcbnew.ZONE(b)
    z.SetZoneName(name)
    lset = pcbnew.LSET()
    lset.AddLayer(layer)
    z.SetLayerSet(lset)
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(pcbnew.FromMM(clearance))
    z.SetMinThickness(pcbnew.FromMM(minw))
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


FULL = [(-BASE / 2 - 1, -1), (BASE / 2 + 1, -1), (TOPHALF + 1, DEPTH + 1), (-TOPHALF - 1, DEPTH + 1)]
zone('GND In1', pcbnew.In1_Cu, 'GND', FULL)
zone('GND B', pcbnew.B_Cu, 'GND', FULL)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(OUT, b)
print(f'board {BASE:.1f} x {DEPTH:.1f} mm trapezoid (top {2 * TOPHALF:.2f} mm), '
      f'{len(fps)} footprints, {len(netnames)} nets -> {OUT}')
