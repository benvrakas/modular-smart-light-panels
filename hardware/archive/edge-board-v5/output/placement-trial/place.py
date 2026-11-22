"""Edge-board placement (SPEC V5.4, decisions 0003/0004). No routing.
Board frame: x along the board (0 = centre = polygon-edge midpoint), y up from
the wall edge. KiCad position = (X0 + x, Y0 - y). Grid/aux origin set to (0,0).
usage (KiCad 9 python): python place.py in.kicad_pcb out.kicad_pcb L_board H
The layout core is identical for every shape; only J2/J3 and the outline move."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kicad_quiet  # no wx assert pop-ups
import sys, math, pcbnew

X0, Y0 = 100.0, 100.0
src, dst, L, H = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
half = L / 2
P = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - y))
CORE = 37.0          # |x| limit for core parts: triangle (81.9 mm) corner-joint courtyards at 37.45
TOP = H - 0.5        # courtyard ceiling (frame/diffuser groove margin)
XL, YL = 31.2, 15.5  # LED x (fixed for every shape) and row height (GEOMETRY V5.3 stack)

PLACE = {
    # ---- fixed geometry ----
    'J1': (0, 0, 0),
    'J2': (-half, 16, 0), 'J3': (half, 16, 0),          # footprint local y=15 sits 1 mm above the wall edge
    'LED1': (-XL, YL, 0), 'LED2': (0, YL, 0), 'LED3': (XL, YL, 0),   # VDD top-left -> +5V lane, GND bottom-right -> GND lane
    'C1': (-XL - 4.85, YL, 270), 'C2': (4.4, 10.7, 0), 'C3': (XL + 4.85, YL, 270),
    # ---- region E: above the strip, LED1..LED2 -- MCU core ----
    'U1': (-17.5, 15.2, 180),                              # rot 180: OSC/NRST/VDDA/ADC/DRIVE_GPIO pins in the right column
    'Y1': (-11.25, 11.8, 0),                              # rot 0: OSC_IN pad BL, OSC_OUT pad TR face U1 pins 2/3
    'C5': (-8.3, 11.0, 90), 'C6': (-6.5, 11.0, 270),       # load caps: C5 OSC_IN pad low, C6 OSC_OUT pad high
    'C8': (-6.5, 14.6, 90),                                # VDDA (pin 5)
    'C10': (-8.3, 14.6, 90),                               # NRST (pin 4): straight F.Cu run from U1.4 along y 14.22
    # BAT54S clamps on the MCU side of R10/R11 (schematic 13:15): D3 by pin 10 / R11, D2 by pin 7 / C14
    'D3': (-11.43, 17.9, 180), 'D2': (-7.35, 17.9, 180),   # rot 180: pin 3 (signal) faces U1, GND/+3V3 pins outboard
    'C7': (-22.6, 15.2, 90), 'C9': (-24.4, 15.2, 90),      # VDD/VSS (left column)
    'R15': (-14.35, 10.2, 270),                            # BOOT0 pull-down, vertical under U1 pin 1; GND end -> X3 in-pad via
    'U4': (-30.0, 9.95, 0), 'C15': (-26.6, 9.95, 270),    # AHCT in zone A (keeps the X1/X3 GND hop column x=-22.5 clear), C15 at pin 5
    # top row (y 20.6) - R10/R11 bus side drops to the B.Cu bus band
    'R7': (-23.0, 20.6, 180),                              # D_IN (R7.1) on the right, LED_RET (R7.2) on the left
    'R8': (-24.9, 18.2, 270),                              # LED_RET pull-down beside the LED_RET riser; GND end -> C9's GND
    # gaps left for the inline B.Cu bus taps: DRIVE via at (-21.0, 20.0), SENSE via at (-16.8, 20.625)
    'R11': (-19.0, 20.6, 180), 'R10': (-14.6, 20.6, 0), 'C14': (-9.8, 20.6, 0),   # R11.2 DRIVE / R10.1 SENSE face their tap vias
    # above LED1
    'R3': (-36.0, 19.9, 90),
    'R5': (-26.4, 17.0, 90),                               # 33R between U4 and LED1 DIN (top-right of LED1)
    # ---- zone A: left of the strip, below LED1 ----
    'D5': (-34.5, 5.5, 90),
    'H1': (-29.2, 4.0, 0),                                 # NPTH 2.0 jig tooling hole (board-only)
    # ---- band S: F.Cu over the contact strip (via-free) ----
    # strip TPs ordered to match U1's escape (fanout.py): SWDIO, SWCLK | GPIO_SPARE, UART_RX | NRST, UART_TX
    'TP4': (-22.86, 2.54, 0), 'TP5': (-22.86, 6.35, 0), 'TP9': (-19.85, 2.54, 0), 'TP8': (-19.05, 6.35, 0),
    'TP7': (-16.6, 5.8, 0),
    'C11': (-13.8, 2.9, 90),                              # bottom >= 1.6: keeps an F.Cu lane at y 1.25 along the whole strip
    'R13': (-4.95, 10.9, 90),                             # CAN Rs pull-down, beside C6 (fed from the CAN_RS via above the strip)
    'TP6': (-17.3, 2.6, 0),                                # NRST beside the SWD pads (jig: one SWD group)
    'U2': (-9.0, 4.4, 0), 'D4': (-3.0, 4.4, 90),
    # CAN termination on the bus (top-left, above LED1): inline tap vias onto the B.Cu CANH/CANL lines
    'R12': (-35.45, 20.0, 0), 'JP1': (-31.5, 19.7, 0),
    'TP1': (12.70, 5.08, 0),
    'TP2': (16.51, 2.54, 0), 'TP10': (16.51, 6.35, 0), 'TP3': (20.32, 6.35, 0),  # +12V/GND TPs right under the X9/X10 in-pad vias
    # ---- region F: above the strip, LED2..LED3 -- discovery + 5 V buck ----
    'C4': (4.8, 16.2, 270),                                # +5V pad up (over the +5V lane), GND pad down
    'R1': (8.0, 11.0, 90), 'D1': (8.0, 14.4, 90), 'R2': (10.0, 14.4, 90),   # +0.5: X6 DRIVE stub channel right of LED2/C4 (x ~5.5-7.5)
    'R9': (1.5, 19.95, 90),                                 # SENSE pull-up, fed by the +3V3 trunk at x 0
    'TP11': (11.2, 19.7, 0),                               # +5V test pad: via straight down into the +5V lane; >=1 mm from every tab window
    'U5': (21.5, 15.0, 0), 'L1': (17.0, 15.0, 180),         # L1 rot 180: SW pad faces U5 pin 2, +5V pad faces C19
    'C17': (21.0, 12.4, 0), 'C16': (21.2, 10.45, 0),       # C16 clear of J1 X10's via row
    'C18': (21.5, 18.1, 180),                              # BOOT pad faces U5 pin 6
    # FB network at U5 pin 4: R16 (+5V top, FB bottom) // C21 parallel; R17 FB->GND below; R18 EN pull-down
    'R16': (24.6, 12.6, 270), 'C21': (26.4, 12.6, 270), 'R17': (25.5, 10.1, 0), 'R18': (24.6, 16.6, 90),
    'C19': (12.9, 15.0, 90), 'C20': (17.0, 19.2, 0),
    # ---- zone B: right of the strip, below LED3 -- 3V3 LDO ----
    'U3': (30.0, 9.4, 0), 'C12': (34.6, 9.4, 90), 'R14': (35.75, 4.0, 90), 'C13': (27.2, 3.0, 90),
    'H2': (32.0, 4.0, 0),                                  # NPTH 2.0 jig tooling hole (board-only)
}
HOLES = ('H1', 'H2')
HOLE_FP = ("C:/Program Files/KiCad/9.0/share/kicad/footprints/MountingHole.pretty", "MountingHole_2mm")

b = pcbnew.LoadBoard(src)
# board-only tooling holes: create if missing (before any board removal: SWIG quirk)
for h in HOLES:
    if b.FindFootprintByReference(h) is None:
        fp = pcbnew.FootprintLoad(*HOLE_FP)
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", HOLE_FP[1]))
        fp.SetReference(h); fp.SetValue("NPTH 2.0 jig tooling")
        fp.SetBoardOnly(True); fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
        b.Add(fp)
refs = [f.GetReference() for f in b.GetFootprints()]
# one core table for both board types (decision 0006): every part on the board must have an
# entry; entries for parts this board doesn't carry (e.g. R3 on the active board) are skipped
unplaced = set(refs) - set(PLACE)
assert not unplaced, f"no placement for {unplaced}"
fps = {r: b.FindFootprintByReference(r) for r in refs}
for ref, (x, y, r) in PLACE.items():
    if ref not in fps:
        continue
    fp = fps[ref]
    if fp.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(r); fp.SetPosition(P(x, y))
ds = b.GetDesignSettings(); ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))
# only the reference designator on silk; BOM fields (LCSC/MPN/Pop/...) hidden
for fp in fps.values():
    for f in fp.GetFields():
        if not f.IsReference() and f.IsVisible() and f.GetLayer() == pcbnew.F_SilkS:
            f.SetVisible(False)
# outline + rule areas last: SWIG loses object types after a board removal, so nothing else follows it
TAB_X, TAB_W, EDGE_KEEP = (-31.5, -2.0, 30.0), 5.0, 1.0   # panel tabs, top edge only; MLCC/crystal >=3 mm away (LAYOUT-NOTES 10)
old_edges = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
old_zones = [z for z in b.Zones() if z.GetZoneName().startswith(('panel-tab', 'top-edge'))]
for d in old_edges + old_zones:
    b.Delete(d)
pts = [(-half, 0), (half, 0), (half, H), (-half, H)]
for i in range(4):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*pts[i])); s.SetEnd(P(*pts[(i + 1) % 4]))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.05)); b.Add(s)


def rule_area(name, layer, x1, x2, y1, y2, footprints):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET(); ls.AddLayer(layer); z.SetLayerSet(ls)   # SetLayer() alone is ignored for rule areas
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowPads(True); z.SetDoNotAllowFootprints(footprints)
    o = z.Outline(); o.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        o.Append(P(x, y))
    b.Add(z)


# B.Cu: copper-free strip along the whole top edge (mouse-bite tabs; bus band ends at y 20.3)
rule_area('top-edge keepout B', pcbnew.B_Cu, -half, half, H - EDGE_KEEP, H, False)
# F.Cu: each tab position, 5 mm wide x 1 mm deep, no copper and no parts
for tx in TAB_X:
    rule_area(f'panel-tab x{tx:+.0f}', pcbnew.F_Cu, tx - TAB_W / 2, tx + TAB_W / 2, H - EDGE_KEEP, H, True)
pcbnew.SaveBoard(dst, b)

# ---------------- checks ----------------
bx = lambda v: (pcbnew.ToMM(v.x) - X0, Y0 - pcbnew.ToMM(v.y))
problems, area = [], 0.0
for ref, fp in fps.items():
    if ref in ('J1', 'J2', 'J3'):
        continue
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox()
    x1, x2 = pcbnew.ToMM(bb.GetLeft()) - X0, pcbnew.ToMM(bb.GetRight()) - X0
    y1, y2 = Y0 - pcbnew.ToMM(bb.GetBottom()), Y0 - pcbnew.ToMM(bb.GetTop())
    area += (x2 - x1) * (y2 - y1)
    if max(abs(x1), abs(x2)) > CORE: problems.append(f"{ref} outside core |x|<={CORE}: {x1:.2f}..{x2:.2f}")
    if y2 > TOP: problems.append(f"{ref} above top limit {TOP}: y2={y2:.2f}")
    if y1 < 0.3: problems.append(f"{ref} too close to wall edge: y1={y1:.2f}")
print(f"courtyard area (excl. J1-J3): {area:.0f} mm^2")
# buck SW node >= 10 mm from Y1/C5/C6/C14 and the SENSE_ADC node (LAYOUT-NOTES 6)
sw = [bx(p.GetPosition()) for f in fps.values() for p in f.Pads() if p.GetNetname() == '/BUCK_SW']
quiet = {}
for ref, f in fps.items():
    for p in f.Pads():
        if ref in ('Y1', 'C5', 'C6', 'C14') or p.GetNetname() == '/SENSE_ADC':
            quiet[f"{ref}.{p.GetNumber()}"] = bx(p.GetPosition())
dmin = min((math.dist(a, q), k) for a in sw for k, q in quiet.items())
print(f"SW node -> nearest quiet pad: {dmin[0]:.1f} mm ({dmin[1]})")
if dmin[0] < 10: problems.append(f"SW too close to {dmin[1]}: {dmin[0]:.1f} mm")
for net in ('/SENSE', '/CANH', '/CANL', '/LED_RET'):
    d = min(math.dist(a, bx(p.GetPosition())) for a in sw for f in fps.values() for p in f.Pads() if p.GetNetname() == net)
    print(f"SW node -> nearest {net} pad: {d:.1f} mm")
# tooling holes: >= 3 mm (hole edge) from the contact strip (|x|<=25, y<=8.5) and the
# triangle-length corner pads (|x| >= 81.9/2 - 2 = 38.95)
for h in HOLES:
    (hx, hy), r = bx(fps[h].GetPosition()), 1.0
    d_strip = math.hypot(max(abs(hx) - 25, 0), max(hy - 8.5, 0)) - r
    d_corner = 38.95 - abs(hx) - r
    print(f"{h} at ({hx:.2f}, {hy:.2f}): {d_strip:.2f} mm to strip, {d_corner:.2f} mm to triangle corner pads")
    if min(d_strip, d_corner) < 3: problems.append(f"{h} closer than 3 mm to strip/corner pads")
print("PROBLEMS:" if problems else "envelope/margin/SW/hole checks: OK", *problems, sep="\n  ")
