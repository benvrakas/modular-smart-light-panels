"""Active edge board (4-layer, decision 0006): scripted power fan-out and fixed structures.
Everything added is LOCKED so Freerouting routes around it.
usage (KiCad 9 python): python fanout.py in.kicad_pcb out.kicad_pcb
Board frame: x along the board (0 = centre), y up from the wall edge. KiCad = (100 + x, 100 - y).
Rules: LAYOUT-NOTES 13 (4-layer active), SPEC V5.6 2."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kicad_quiet  # noqa
import pcbnew

X0, Y0 = 100.0, 100.0
src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
if len(b.GetTracks()):   # must start from a placed, unrouted board (re-running would duplicate everything)
    sys.exit(f'fanout.py: {src} already has {len(b.GetTracks())} tracks/vias; run it on the output of place.py + stackup4.py')
bb = b.GetBoardEdgesBoundingBox()
HALF = (pcbnew.ToMM(bb.GetWidth()) - 0.05) / 2
H = pcbnew.ToMM(bb.GetHeight()) - 0.05
P = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - y))
bx = lambda v: (pcbnew.ToMM(v.x) - X0, Y0 - pcbnew.ToMM(v.y))
NET = lambda n: b.FindNet(n)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
CLR = 0.2                       # default copper clearance
STRIP_X, STRIP_Y = 25.0, 8.5    # J1 rule area: no vias
BUS_LO, BUS_HI = 18.35, 21.0    # B.Cu bus band: no fan-out vias
REGION = {'+12V': (1.6, 10.9), '+5V': (14.1, 17.1), 'GND': (1.4, H - 1.4)}   # In2 region per net (via centre)
HOLES = []
# no vias here: keeps a continuous In2 +5V corridor (y ~15.2-16.3) under U1, C7, C9 (antipads would cut the lane)
NO_VIA = [(-24.5, -12.5, 14.6, 16.9)]

# ---------------------------------------------------------------- obstacle model
pads = []   # (net, layerset{F,B}, x1, x2, y1, y2, ref, num)
for fp in b.GetFootprints():
    for p in fp.Pads():
        bbp = p.GetBoundingBox()
        x1, x2 = pcbnew.ToMM(bbp.GetLeft()) - X0, pcbnew.ToMM(bbp.GetRight()) - X0
        y1, y2 = Y0 - pcbnew.ToMM(bbp.GetBottom()), Y0 - pcbnew.ToMM(bbp.GetTop())
        lay = {l for l in (F, B) if p.IsOnLayer(l)}
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            HOLES.append(((x1 + x2) / 2, (y1 + y2) / 2, (x2 - x1) / 2)); lay = {F, B}
        pads.append((p.GetNetname(), lay, x1, x2, y1, y2, fp.GetReference(), p.GetNumber()))
vias, tracks = [], []           # vias: (net, x, y, r); tracks: (net, layer, (x1,y1), (x2,y2), w)
added = []                      # board items to lock

def d_pt_rect(x, y, r):
    dx = max(r[0] - x, 0, x - r[1]); dy = max(r[2] - y, 0, y - r[3]); return math.hypot(dx, dy)

def d_pt_seg(x, y, a, c):
    (ax, ay), (cx, cy) = a, c
    L2 = (cx - ax) ** 2 + (cy - ay) ** 2
    t = 0 if L2 == 0 else max(0, min(1, ((x - ax) * (cx - ax) + (y - ay) * (cy - ay)) / L2))
    return math.hypot(x - ax - t * (cx - ax), y - ay - t * (cy - ay))

def extra(n1, n2):  # net-pair extra clearance (custom DRC rules)
    s = {n1, n2}
    if '+12V' in s and (s & {'/DRIVE', '/SENSE', '+5V'}): return 0.5
    return CLR

def via_ok(net, x, y, r=0.3, bus_ok=False, region=True):
    if region:
        lo, hi = REGION.get(net, (1.4, H - 1.4))
        if not (lo <= y <= hi): return False
    if abs(x) > HALF - 0.9 or y < 1.3 or y > H - 1.3: return False
    if abs(x) < STRIP_X + r + 0.1 and y < STRIP_Y + r + 0.05: return False
    if not bus_ok and BUS_LO < y < BUS_HI: return False
    if any(a <= x <= c and lo <= y <= hi for a, c, lo, hi in NO_VIA): return False
    for hx, hy, hr in HOLES:
        if math.hypot(x - hx, y - hy) < hr + r + 0.35: return False
    for n, lay, *rect, ref, num in pads:
        d = d_pt_rect(x, y, rect)
        if n == net:
            if d < 0.05 and not (d == 0 and False): pass
            if d == 0: return False            # no via-in-pad
        elif d < r + max(extra(n, net), 0.25): return False
    for n, vx, vy, vr in vias:
        if math.hypot(x - vx, y - vy) < r + vr + (0.25 if n == net else max(extra(n, net), 0.3)): return False
    for n, lay, a, c, w in tracks:
        if n != net and d_pt_seg(x, y, a, c) < r + w / 2 + extra(n, net): return False
    return True

def seg_ok(net, layer, a, c, w, ignore_pad=None):
    L = math.hypot(c[0] - a[0], c[1] - a[1]); steps = max(2, int(L / 0.05))
    pts = [(a[0] + (c[0] - a[0]) * i / steps, a[1] + (c[1] - a[1]) * i / steps) for i in range(steps + 1)]
    for x, y in pts:
        if abs(x) > HALF - 0.5 or y < 0.6 or y > H - 0.6: return False
    for n, lay, *rect, ref, num in pads:
        if n == net or layer not in lay: continue
        for x, y in pts:
            if d_pt_rect(x, y, rect) < w / 2 + extra(n, net): return False
    for n, vx, vy, vr in vias:
        if n == net: continue
        if d_pt_seg(vx, vy, a, c) < vr + w / 2 + extra(n, net): return False
    for n, lay, s1, s2, w2 in tracks:
        if n == net or lay != layer: continue
        for x, y in pts[::2]:
            if d_pt_seg(x, y, s1, s2) < w / 2 + w2 / 2 + extra(n, net): return False
    return True

def add_track(net, layer, pts, w):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(pcbnew.FromMM(w))
        t.SetLayer(layer); t.SetNet(NET(net)); b.Add(t); added.append(t)
        tracks.append((net, layer, a, c, w))

def add_via(net, x, y, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(pcbnew.FromMM(d))
    v.SetDrill(pcbnew.FromMM(drill)); v.SetNet(NET(net)); b.Add(v); added.append(v)
    vias.append((net, x, y, d / 2))

def add_zone(name, layer, net, x1, x2, y1, y2, prio=1):
    z = pcbnew.ZONE(b); z.SetZoneName(name)
    l = pcbnew.LSET(); l.AddLayer(layer); z.SetLayerSet(l)
    z.SetNet(NET(net)); z.SetAssignedPriority(prio)
    z.SetLocalClearance(pcbnew.FromMM(0.3)); z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    o = z.Outline(); o.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)): o.Append(P(x, y))
    b.Add(z)

def pad(ref, num):
    p = next(p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num)
    return bx(p.GetPosition())

report = []

# ---------------------------------------------------------------- 1. J1 contact pads: vias IN the pad tops (decision 0007)
# The springs come to rest mid-pad and never reach the top end, so each pad's vias sit in a
# row at y 7.65 (ring 7.35-7.95; pad tops are at 8.0). The footprint's via keep-out gets a
# matching hole over each pad top. This removes the via rows above the strip that blocked
# every MCU -> strip route.
J1_VIA_Y = 7.65
J1fp = b.FindFootprintByReference('J1')
for z in J1fp.Zones():                       # holes in the "contact-strip keepout" over the pad tops
    if z.GetIsRuleArea():
        o = z.Outline()
        for p in J1fp.Pads():
            x, _ = bx(p.GetPosition())
            o.NewHole()
            for hx, hy in ((x - 1.5, 7.25), (x + 1.5, 7.25), (x + 1.5, 8.0), (x - 1.5, 8.0)):
                o.Append(P(hx, hy), 0, o.HoleCount(0) - 1)
for i in range(1, 11):
    num = f'X{i}'
    p = next(q for q in J1fp.Pads() if q.GetNumber() == num)
    net = p.GetNetname(); x, _ = bx(p.GetPosition())
    if net in ('+12V', 'GND'):      # >= 4 vias (one spring each, LAYOUT-NOTES 13): one row at 0.75 pitch
        for dx in (-1.125, -0.375, 0.375, 1.125): add_via(net, x + dx, J1_VIA_Y)
    else:                           # signal: one via in the pad top
        add_via(net, x, J1_VIA_Y)
report.append('J1: 4 vias in each power pad top, 1 in each signal pad top (y 7.65)')

# ---------------------------------------------------------------- 2. corner pads: via fields just inboard, local B.Cu copper
for ref, sgn in (('J2', -1), ('J3', +1)):
    inner = sgn * (HALF - 3.0)                     # inner edge of the 3 mm corner power pads
    cols = [inner - sgn * c for c in (0.55, 1.55, 2.55)]
    for vy in (3.1, 4.0):                          # +12V: 6 x 0.4 mm, between the DRIVE (y 2) and SENSE (y 5.5) entries
        for vx in cols: add_via('+12V', vx, vy, 0.8, 0.4)
    for vy in (7.25, 10.75):                       # GND: 6 x 0.4 mm, in the gaps around CANL (y 9)
        for vx in cols: add_via('GND', vx, vy, 0.8, 0.4)
    for vx in cols: add_via('+5V', vx, 14.6)       # +5V: 3 x 0.3 mm (>= 2)
    xa, xb = sorted((sgn * HALF, inner - sgn * 3.2))
    add_zone(f'FO {ref} +12V B', B, '+12V', xa, xb, 1.0, 5.0)
    add_zone(f'FO {ref} +5V B', B, '+5V', xa, xb, 13.9, 16.1)
report.append('corners: 6 + 6 x 0.4 mm and 3 x 0.3 mm vias per end, B.Cu +12V/+5V pads tied in')

# ---------------------------------------------------------------- 3. B.Cu signal bus (SPEC V5.6 2): CANH/CANL, DRIVE, SENSE (outermost)
# Each line ends in a via that drops to F.Cu and runs straight down, then out to its corner pad.
# Descent order (outer -> inner) = pad height order (high -> low) so nothing crosses:
#   CANH (pad y 12.5), CANL (9.0), SENSE (5.5), DRIVE (2.0 -- passes 0.575 mm under the +12V via rows)
inner = HALF - 3.0                       # inner edge of the corner power pads
X_DESC = {'/CANH': inner - 3.3, '/CANL': inner - 3.95, '/SENSE': inner - 4.6, '/DRIVE': inner - 5.25}  # clear of the via fields
BUS = [('/CANH', 18.75), ('/CANL', 19.375), ('/DRIVE', 20.0), ('/SENSE', 20.625)]
CORNER_PAD_Y = {'/CANH': 12.5, '/CANL': 9.0, '/SENSE': 5.5, '/DRIVE': 2.0}
for net, y in BUS:
    xe = X_DESC[net]
    add_track(net, B, [(-xe, y), (xe, y)], 0.25)
    for s in (-1, 1):
        add_via(net, s * xe, y)
        add_track(net, F, [(s * xe, y), (s * xe, CORNER_PAD_Y[net]), (s * (HALF - 1.0), CORNER_PAD_Y[net])], 0.25)
report.append(f'bus: 4 B.Cu lines y 18.75..20.625 + corner fan-outs on F.Cu (descents at |x| {X_DESC["/DRIVE"]:.2f}..{X_DESC["/CANH"]:.2f})')
# corner D pads (LED chain in/out) hop to B.Cu right at the pad, so they never cross the descents on F.Cu
for ref, s, net in (('J2', -1, '/D_IN'), ('J3', 1, '/D_OUT')):
    vx = s * (inner - 0.05)
    add_via(net, vx, 17.1); add_track(net, F, [(s * (HALF - 1.0), 16.0), (vx, 17.1)], 0.3)
# X6 DRIVE stub (LAYOUT-NOTES 5/13): not under LED2; up the channel right of C4 to an inline via on the DRIVE line
add_track('/DRIVE', F, [(2.5, J1_VIA_Y), (2.5, 9.1), (6.3, 9.1), (6.3, 20.0)], 0.25)
add_via('/DRIVE', 6.3, 20.0)
report.append('DRIVE X6 stub: via (2.5, 9.1) -> F.Cu x 6.3 -> B.Cu DRIVE line at (6.3, 20.0)')
# CAN stubs X4/X5 up under LED2's body (between its pad columns; LAYOUT-NOTES 13 allows CAN there)
# X4 -> CANH line on F.Cu: jog out of the strip, then straight up at x -4.0 to an inline via on the B.Cu CANH line.
# Both CAN drops (CANH x -4.0, CANL x -1.0) are F.Cu, so B.Cu stays free for everything crossing under LED2.
add_track('/CANH', F, [(-7.5, J1_VIA_Y), (-4.6, 8.6), (-4.0, 9.2), (-4.0, 18.75)], 0.25); add_via('/CANH', -4.0, 18.75)
add_track('/CANH', F, [pad('U2', '7'), (-5.0, pad('U2', '7')[1]), (-5.0, 8.469)], 0.25)        # U2 CANH east of U2.8 onto the jog
# CAN_RX: U1.17 -> via under U1 -> B.Cu under R15/crystal -> via above the strip -> F.Cu down under U2's body to U2.4
add_track('/CAN_RX', F, [pad('U1', '17'), (-18.9, 14.22)], 0.25); add_via('/CAN_RX', -18.9, 14.22)
add_track('/CAN_RX', B, [(-18.9, 14.22), (-16.18, 11.5), (-11.9, 11.5), (-9.5, 9.1)], 0.25); add_via('/CAN_RX', -9.5, 9.1)
add_track('/CAN_RX', F, [(-9.5, 9.1), (-9.5, 3.0), (-10.0, 2.5), pad('U2', '4')], 0.25)
# CAN_RS: U2.8 out under the body, up to a via above the strip (Freerouting takes it on to U1.11 on B.Cu);
# B.Cu under C6 to R13 (Rs pull-down) beside C6
add_track('/CAN_RS', F, [pad('U2', '8'), (-8.3, pad('U2', '8')[1]), (-8.3, 9.1)], 0.25); add_via('/CAN_RS', -8.3, 9.1)
add_track('/CAN_RS', B, [(-8.3, 9.1), (-7.3, 10.0), (-5.6, 10.0), (-5.05, 9.2)], 0.25); add_via('/CAN_RS', -5.05, 9.2)
add_track('/CAN_RS', F, [(-5.05, 9.2), pad('R13', '1')], 0.25)
add_via('GND', -4.8, 13.3); add_track('GND', F, [pad('R13', '2'), (-4.85, 12.4), (-4.8, 13.3)], 0.3)   # R13 GND
# +3V3 trunk to the CAN transceiver: TP2 (LDO side) -> strip bottom F.Cu lane (y 1.25) -> C11 / U2.3,
# and up between the X5/X6 vias (x 0, under LED2's body) to a via: B.Cu carries it on west (Freerouting)
add_track('+3V3', F, [pad('TP2', '1'), (16.51, 1.25), (0.0, 1.25), (0.0, 12.6)], 0.3); add_via('+3V3', 0.0, 12.6)
# +3V3 spine on B.Cu (y 12.6) from the trunk via: west to U1.5, C8 and the D2/D3 clamps; east to R9
add_track('+3V3', B, [(0.0, 12.6), (-12.0, 12.6), (-12.0, 14.88)], 0.3)
add_via('+3V3', -12.0, 14.88); add_track('+3V3', F, [pad('U1', '5'), (-12.0, 14.88)], 0.3)
add_via('+3V3', -5.55, 13.83); add_track('+3V3', F, [pad('C8', '1'), (-5.55, 13.83)], 0.3); add_track('+3V3', B, [(-5.55, 13.83), (-5.55, 12.6)], 0.3)
add_via('+3V3', -8.3, 16.9); add_track('+3V3', B, [(-8.3, 16.9), (-8.3, 12.6)], 0.3)
add_track('+3V3', F, [(-8.3, 16.9), (-9.4, 17.2), (-9.4, 18.5), pad('D3', '2')], 0.25); add_track('+3V3', F, [pad('D3', '2'), pad('D2', '2')], 0.25)
add_track('+3V3', F, [(0.0, 12.6), (0.0, 18.4), pad('R9', '1')], 0.3)                     # on up under LED2's body to R9 (SENSE pull-up)
add_via('/SENSE', 2.4, 20.625); add_track('/SENSE', F, [pad('R9', '2'), (2.4, 20.625)], 0.25)   # R9 onto the SENSE line
# U1's west supply group (U1.16, C7, C9) sits on the far side of the CAN fence under U1: feed it from the strip's
# bottom lane via the west end (B.Cu down x -25.8, outside the strip)
add_via('+3V3', -25.4, 13.6); add_track('+3V3', F, [pad('C9', '1'), (-25.4, 13.6)], 0.3)
add_track('+3V3', B, [(-25.4, 13.6), (-25.8, 13.2), (-25.8, 1.7)], 0.3); add_via('+3V3', -25.8, 1.7)
add_track('+3V3', F, [(-25.8, 1.7), (-25.35, 1.25), (-12.9, 1.25)], 0.3)
# CAN_RS: U1.11 -> via under U1 -> B.Cu SE, north of CAN_RX, under the +3V3 spine corner -> the CAN_RS via above the strip
add_track('/CAN_RS', F, [pad('U1', '11'), (-19.1, 18.12), (-18.9, 17.92), (-18.9, 16.95)], 0.25); add_via('/CAN_RS', -18.9, 16.95)
add_track('/CAN_RS', B, [(-18.9, 16.95), (-13.95, 12.0), (-11.2, 12.0), (-8.3, 9.1)], 0.25)
# Over U1's top-left (pin swap LED_RET <-> LED_EN, decision 0008):
#  LED_RET: U1.12 straight to R7.2 / R8.1 (top row, west) on F.Cu
add_track('/LED_RET', F, [pad('U1', '12'), (-21.6, 17.47), (-23.83, 17.47), pad('R7', '2')], 0.25)
add_track('/LED_RET', F, [pad('R8', '1'), (-23.83, pad('R8', '1')[1])], 0.25)
add_track('GND', F, [pad('R8', '2'), pad('C9', '2')], 0.3)
#  D_IN: J2 corner via -> B.Cu y 18.1 -> via -> F.Cu up to R7.1
add_track('/D_IN', B, [(-(HALF - 3.0 - 0.05), 17.1), (-42.8, 18.1), (-22.4, 18.1)], 0.25); add_via('/D_IN', -22.4, 18.1)
add_track('/D_IN', F, [(-22.4, 18.1), (-22.17, 18.6), pad('R7', '1')], 0.25)
#  LED_D1: LED1 -> B.Cu under D_IN, past the CAN_RS via, to LED2
add_track('/LED_D1', F, [pad('LED1', '4'), (-32.3, 13.9)], 0.25); add_via('/LED_D1', -32.3, 13.9)
add_track('/LED_D1', B, [(-32.3, 13.9), (-28.75, 17.45), (-21.75, 17.45), (-21.15, 18.05), (0.85, 18.05), (1.0, 17.9)], 0.25); add_via('/LED_D1', 1.0, 17.9)
add_track('/LED_D1', F, [(1.0, 17.9), pad('LED2', '2')], 0.25)
#  SENSE_ADC (U1.7): east along y 16.17, then 0.2 mm necks under the clamp bodies: up between D3's pads to R10.2
#  (top row; R10.2 -> C14.1 by Freerouting), and east between D2.3 and D2.1 into D2.3
add_track('/SENSE_ADC', F, [pad('U1', '7'), (-12.05, 16.17), (-12.05, 16.78)], 0.25)
add_track('/SENSE_ADC', F, [(-12.05, 16.78), (-10.97, 17.86), (-11.13, 18.07), (-13.6, 20.55)], 0.2)
add_track('/SENSE_ADC', F, [(-13.6, 20.55), pad('R10', '2')], 0.25)
add_track('/SENSE_ADC', F, [(-12.05, 16.17), (-9.41, 16.17)], 0.25)
add_track('/SENSE_ADC', F, [(-9.41, 16.17), (-8.1, 16.14), (-7.9, 16.34)], 0.2)
add_track('/SENSE_ADC', F, [(-7.9, 16.34), (-7.64, 16.6), (-7.64, 17.25), pad('D2', '3')], 0.25)
#  D3.1 (GND) is boxed in by SENSE_ADC and +3V3: via at the outer end of its own pad (via in pad, decision 0007)
add_via('GND', -10.05, 16.92)
#  DRIVE_GPIO (U1.10) -> D3.3 straight east under SENSE_ADC's neck (Freerouting does U1.10 -> R11)
add_track('/DRIVE_GPIO', F, [pad('U1', '10'), (-14.51, 18.0), (-12.37, 18.0), pad('D3', '3')], 0.2)
#  LED_DATA: U1.13 -> via west of U1 -> B.Cu west (y 14.4) and down x -27.7 -> via -> F.Cu between U4's pins 4/5,
#  under its body into U4.2 (the level shifter's input faces away from the MCU)
add_track('/LED_DATA', F, [pad('U1', '13'), (-21.3, 16.83), (-21.6, 16.45)], 0.25); add_via('/LED_DATA', -21.6, 16.45)
add_track('/LED_DATA', B, [(-21.6, 16.45), (-22.5, 14.4), (-27.7, 14.4), (-27.7, 9.95)], 0.25); add_via('/LED_DATA', -27.7, 9.95)
add_track('/LED_DATA', F, [(-27.7, 9.95), (-30.0, 9.95), pad('U4', '2')], 0.25)
#  LED_EN: U1.6 -> via just east of U1 -> B.Cu up to y 17.55 (under LED_D1) and east under both CAN walls (Freerouting
#  finishes it to U5). Keeps the F.Cu corridor between the D2/D3 and C8/C10 rows free for SENSE_ADC.
add_track('/LED_EN', F, [pad('U1', '6'), (-12.7, 15.54)], 0.25); add_via('/LED_EN', -12.7, 15.54)   # below SENSE_ADC's y 16.17 exit
add_track('/LED_EN', B, [(-12.7, 15.54), (-12.7, 17.1), (-12.25, 17.55), (-1.6, 17.55), (-1.0, 16.95)], 0.25)
add_track('+3V3', F, [(0.0, 1.25), (-12.9, 1.25), (-12.9, 2.1), pad('C11', '1')], 0.3)
add_track('+3V3', F, [(-12.9, 2.1), (-12.9, pad('U2', '3')[1]), pad('U2', '3')], 0.3)
# NRST: U1.4 -> C10 straight along y 14.22 (C10 sits at x -8.3, west of the CANH wall)
add_track('/NRST', F, [pad('U1', '4'), (-9.2, 14.22), pad('C10', '1')], 0.25)
# termination R12/JP1 (top-left): inline taps onto CANH / CANL
add_via('/CANH', -36.4, 18.75); add_track('/CANH', F, [pad('R12', '1'), (-36.4, 18.75)], 0.25)
add_via('/CANL', -29.6, 19.375); add_track('/CANL', F, [pad('JP1', '2'), (-29.6, 19.375)], 0.25)
add_track('/CAN_TERM', F, [pad('R12', '2'), pad('JP1', '1')], 0.25)
# D4 (rot 90): GND pin up -> via between the X4/X5 vias
add_via('GND', -3.3, 9.8); add_track('GND', F, [pad('D4', '3'), (-3.0, 6.3), (-3.3, 6.6), (-3.3, 9.8)], 0.3)
add_track('/CANL', F, [pad('D4', '2'), (-2.05, 7.0), (-2.5, J1_VIA_Y)], 0.25)        # D4 CANL straight up into X5's in-pad via
add_track('/SPARE', F, [(12.5, J1_VIA_Y), pad('TP1', '1')], 0.25)                   # X8 -> TP1
add_track('/CANL', F, [(-2.5, J1_VIA_Y), (-1.0, 9.15), (-1.0, 19.375)], 0.25); add_via('/CANL', -1.0, 19.375)
# MCU-side taps: R11.2 (DRIVE) and R10.1 (SENSE) drop to their bus lines in the top-row gaps
add_track('/DRIVE', F, [pad('R11', '2'), (-21.0, 20.0)], 0.25); add_via('/DRIVE', -21.0, 20.0)
add_track('/SENSE', F, [pad('R10', '1'), (-16.8, 20.625)], 0.25); add_via('/SENSE', -16.8, 20.625)
report.append('CAN stubs under LED2 + DRIVE/SENSE taps at R11/R10')
# ---------------------------------------------------------------- crystal (LAYOUT-NOTES 6): short, GND-tied, before anything else
Y = lambda n: pad('Y1', n)
add_track('/OSC_IN', F, [Y('1'), (-13.0, 11.2), (-13.55, 11.45), (-13.55, 12.92), pad('U1', '2')], 0.25)
add_track('/OSC_IN', F, [Y('1'), (Y('1')[0], 9.95), (pad('C5', '1')[0], 9.95), pad('C5', '1')], 0.25)
add_track('/OSC_OUT', F, [Y('3'), (Y('3')[0], 13.58), pad('U1', '3')], 0.25)
add_track('/OSC_OUT', F, [Y('3'), (Y('3')[0] + 0.6, 12.8), (pad('C6', '1')[0], 12.8), pad('C6', '1')], 0.25)
add_track('GND', F, [Y('4'), Y('2')], 0.25)                                 # crystal GND pads tied under the body
add_track('GND', F, [Y('2'), pad('C5', '2')], 0.3)
add_track('GND', F, [pad('C5', '2'), (-7.3, 10.9), pad('C6', '2')], 0.3)
add_via('GND', pad('C6', '2')[0], 9.15); add_track('GND', F, [pad('C6', '2'), (pad('C6', '2')[0], 9.15)], 0.3)
add_track('/BOOT0', F, [pad('R15', '1'), pad('U1', '1')], 0.25)                 # R15 stands vertically under U1.1
add_track('GND', F, [pad('R15', '2'), (pad('R15', '2')[0], 8.6), (-13.625, J1_VIA_Y)], 0.3)   # -> X3 in-pad via
report.append('crystal: OSC_IN/OUT + load caps + GND hand-routed')
# C11 / U2 GND straight up into X3's in-pad vias
add_track('GND', F, [pad('C11', '2'), (-13.8, 7.2), (-13.625, J1_VIA_Y)], 0.4)
add_track('GND', F, [pad('U2', '2'), (-13.8, pad('U2', '2')[1])], 0.4)
# ---------------------------------------------------------------- U1 escape (hand-routed; Freerouting jams here)
# Bottom escape into the strip test pads, each through its own gap in the J1 in-pad via row (y 7.65):
#   gap W (x < -23.9): SWDIO | gap A (X1|X2): SWCLK, GPIO_SPARE, UART_RX | gap B (X2|X3): UART_TX, NRST
# Left-column pins SWCLK/SWDIO leave west; GPIO_SPARE/UART/NRST leave under the body (F.Cu, x -17.5..-15.95).
add_track('/SWCLK', F, [pad('U1', '20'), (-21.6, 12.28), (-21.6, 9.6), (-20.75, 8.75), (-20.75, 6.35), pad('TP5', '1')], 0.25)
add_track('/SWDIO', F, [pad('U1', '19'), (-22.1, 12.92), (-22.1, 10.6), (-24.4, 8.3), (-24.4, 2.54), pad('TP4', '1')], 0.25)
add_track('/GPIO_SPARE', F, [pad('U1', '14'), (-17.5, 16.17), (-17.5, 11.3), (-20.25, 8.55), (-20.25, 3.3), pad('TP9', '1')], 0.25)
add_track('/UART_RX', F, [pad('U1', '9'), (-16.9, 17.47), (-16.9, 11.0), (-19.75, 8.15), (-19.75, 7.6), pad('TP8', '1')], 0.25)
add_track('/UART_TX', F, [pad('U1', '8'), (-16.45, 16.83), (-16.45, 9.6), (-15.7, 8.85), (-15.7, 7.0), pad('TP7', '1')], 0.25)
add_track('/NRST', F, [pad('U1', '4'), (-15.95, 14.22), (-15.95, 11.0), (-15.2, 10.25), (-15.2, 4.7), (-17.0, 4.7),
                       (-17.3, 4.2), pad('TP6', '1')], 0.25)
# CAN_TX follows CAN_RX: via under U1 -> B.Cu under the crystal -> via above the strip -> F.Cu to U2.1
add_track('/CAN_TX', F, [pad('U1', '18'), (-19.3, 13.58), (-19.0, 13.28)], 0.25); add_via('/CAN_TX', -19.0, 13.28)
add_track('/CAN_TX', B, [(-19.0, 13.28), (-16.72, 11.0), (-12.2, 11.0), (-10.7, 9.2)], 0.25); add_via('/CAN_TX', -10.7, 9.2)
add_track('/CAN_TX', F, [(-10.7, 9.2), (-10.7, 7.1), (-10.9, 6.8), pad('U2', '1')], 0.25)
# U1 supply pins west to C7/C9 (C9's GND pad gets the via; no vias in the +5V corridor under U1)
add_track('+3V3', F, [pad('U1', '16'), (-21.5, 14.88), pad('C7', '1'), pad('C9', '1')], 0.3)
add_track('GND', F, [pad('U1', '15'), (-21.5, 15.53), pad('C7', '2'), pad('C9', '2')], 0.3)
report.append('U1 escape: SWD/UART/GPIO/NRST to the strip TPs, CAN_TX/RX on B.Cu, supply pins to C7/C9')

# ---------------------------------------------------------------- 4. buck (LAYOUT-NOTES 6, 13): explicit copper
add_track('/BUCK_SW', F, [pad('U5', '2'), pad('L1', '1')], 0.6)                      # SW: ~1.9 mm, pad to L1 only
add_track('/BUCK_SW', F, [pad('C18', '2'), (19.2, 17.6), (19.2, 15.0)], 0.4)         # BOOT cap to SW (0.3 mm from U5 GND pad)
add_track('/BUCK_BOOT', F, [pad('C18', '1'), (22.64, 16.6), pad('U5', '6')], 0.3)
add_track('+12V', F, [pad('C16', '1'), pad('C17', '1'), pad('U5', '3')], 0.6)          # VIN
add_track('GND', F, [pad('C16', '2'), pad('C17', '2')], 0.6)
add_track('GND', F, [pad('C17', '2'), (21.5, 12.9), (21.5, 15.95), pad('U5', '1')], 0.4)  # C17 GND -> U5 GND (direct F.Cu)
for v in ((20.8, 16.9), (21.65, 16.9)): add_via('GND', *v)                              # U5 GND
for v in ((23.6, 10.0), (23.6, 10.85)): add_via('GND', *v); add_track('GND', F, [v, pad('C16', '2')], 0.6)  # C16 GND (own vias, not X10's)
for v in ((22.55, 12.4), (22.55, 13.25)): add_via('GND', *v)                            # C17 GND
for v in ((19.35, 10.45), (19.35, 9.6)): add_via('+12V', *v)                            # C16 VIN: 2 vias beside the pad
add_track('+12V', F, [pad('C16', '1'), (19.35, 10.45), (19.35, 9.6)], 0.6)
add_track('+5V', F, [(15.5, 14.3), pad('C19', '1')], 0.6)                               # L1 out -> C19
add_track('+5V', F, [(15.6, 16.6), pad('C20', '1')], 0.6)                               # L1 out -> C20
for v in ((14.2, 15.3), (14.2, 16.15)): add_via('+5V', *v); add_track('+5V', F, [v, (15.3, v[1])], 0.6)
for v in ((11.85, 15.95), (12.9, 17.05)): add_via('GND', *v); add_track('GND', F, [v, pad('C19', '2')], 0.6)
for v in ((17.15, 17.95), (18.0, 17.95)): add_via('GND', *v); add_track('GND', F, [v, pad('C20', '2')], 0.6)
add_track('/BUCK_FB', F, [pad('U5', '4'), (23.3, 14.05), (23.3, 11.78), pad('R16', '2')], 0.3)  # small FB node
add_track('/BUCK_FB', F, [pad('R16', '2'), pad('R17', '1')], 0.3)
add_track('/BUCK_FB', F, [pad('R16', '2'), pad('C21', '2')], 0.3)
add_track('+5V', F, [pad('R16', '1'), pad('C21', '1')], 0.4)
add_via('+5V', 25.5, 14.5); add_track('+5V', F, [(25.5, 13.4), (25.5, 14.5)], 0.4)       # divider top from +5V plane
add_track('/LED_EN', F, [pad('U5', '5'), (23.8, 15.0), pad('R18', '1')], 0.25)
add_via('GND', 25.5, 17.42); add_track('GND', F, [pad('R18', '2'), (25.5, 17.42)], 0.4)
add_via('GND', 26.33, 9.0); add_track('GND', F, [pad('R17', '2'), (26.33, 9.0)], 0.4)  # R17 to GND (Kelvin via In1)
report.append('buck: SW/BOOT/VIN/FB/EN copper + 2 GND vias at U5, C16, C17, C19, C20')

# ---------------------------------------------------------------- 5. generic fan-out for the remaining power pads
done = set()
for n, vx, vy, vr in vias: pass
EXPLICIT = {('U5', '1'), ('U5', '3'), ('C16', '1'), ('C16', '2'), ('C17', '1'), ('C17', '2'),
            ('C19', '1'), ('C19', '2'), ('C20', '1'), ('C20', '2'), ('L1', '2'), ('R16', '1'), ('C21', '1'),
            ('R17', '2'), ('R18', '2'), ('C14', '2'), ('D4', '3'), ('C11', '2'), ('U2', '2'), ('R15', '2'), ('R13', '2'), ('R8', '2'), ('D3', '1'), ('U1', '15'), ('C7', '2'),
            ('Y1', '2'), ('Y1', '4'), ('C5', '2'), ('C6', '2')}
NEED2 = {('D5', '1'), ('D5', '2')}                        # TVS: >= 2 vias per side
todo = []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref in ('J1', 'J2', 'J3'): continue
    for p in fp.Pads():
        net = p.GetNetname()
        if net not in ('GND', '+5V', '+12V') or (ref, p.GetNumber()) in EXPLICIT: continue
        x, y = bx(p.GetPosition()); s = p.GetSize()
        w = max(0.3, min(0.6, 0.8 * min(pcbnew.ToMM(s.x), pcbnew.ToMM(s.y))))
        todo.append((abs(x) < STRIP_X and y < STRIP_Y, ref, p.GetNumber(), net, x, y, w))
todo.sort(key=lambda t: (t[0], t[1].startswith('U'), t[1]))   # caps/LEDs first; ICs may then share cap vias; strip pads last

def try_connect(net, x, y, w, rmax, allow_share=True, share_r=2.5):
    # (a) share an existing same-net via
    if allow_share:
        for n, vx, vy, vr in sorted(vias, key=lambda v: math.hypot(v[1] - x, v[2] - y)):
            if n != net: continue
            d = math.hypot(vx - x, vy - y)
            if d > min(rmax, share_r): break
            if seg_ok(net, F, (x, y), (vx, vy), w): add_track(net, F, [(x, y), (vx, vy)], w); return 'shared'
    # (b) new via, straight stub, then L-shaped stubs
    cands = []
    r = 0.9
    while r <= rmax:
        for k in range(24):
            a = 2 * math.pi * k / 24
            cands.append((r, x + r * math.cos(a), y + r * math.sin(a)))
        r += 0.25
    for _, vx, vy in cands:
        if via_ok(net, vx, vy) and seg_ok(net, F, (x, y), (vx, vy), w):
            add_via(net, vx, vy); add_track(net, F, [(x, y), (vx, vy)], w); return 'via'
    for _, vx, vy in cands:
        if not via_ok(net, vx, vy): continue
        for mid in ((x, vy), (vx, y)):
            if seg_ok(net, F, (x, y), mid, w) and seg_ok(net, F, mid, (vx, vy), w):
                add_via(net, vx, vy); add_track(net, F, [(x, y), mid, (vx, vy)], w); return 'via-L'
    return None

fails = []
for strip, ref, num, net, x, y, w in todo:
    need = 2 if (ref, num) in NEED2 else 1
    for k in range(need):
        res = try_connect(net, x, y, w, 9.0 if strip else (7.0 if net != 'GND' else 4.0), allow_share=(k == 0 and need == 1), share_r=4.0 if strip else 2.5)
        if res is None:
            fails.append(f'{ref}.{num} {net} ({x:.2f},{y:.2f})'); break
report.append(f'generic: {len(todo)} pads, {len(fails)} unresolved')
# C14 (ADC filter) sits in the top row over the bus band, where no via can go: tie its GND to D3's GND pad
add_track('GND', F, [pad('C14', '2'), (-5.3, 20.6), (-5.3, 17.9), (-6.2, 17.9), (-6.2, 17.25)], 0.3)  # C14 GND -> D2.1 (right), clear of SENSE_ADC

for it in added:
    it.SetLocked(True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
print('\n'.join(report))
print('vias:', len(vias), 'tracks:', len(tracks))
if fails: print('UNRESOLVED:', *fails, sep='\n  ')
