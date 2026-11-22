"""Triangle-envelope fit trial (stand-ins for V5.3 parts). Scratch only.
usage: python trial.py synced.kicad_pcb out.kicad_pcb L_board H"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kicad_quiet  # no wx assert pop-ups
import sys, pcbnew
X0, Y0 = 100.0, 100.0
src, dst, L, H = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
half = L / 2
P = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - y))
STD = sys.argv[5]
NEW = {  # stand-in ref: (lib, footprint, value)
    'U4n': ('Package_TO_SOT_SMD', 'SOT-23-5', 'AHCT1G125'),
    'C20n': ('Capacitor_SMD', 'C_0603_1608Metric', '100nF 5V'),
    'U5n': ('Package_TO_SOT_SMD', 'SOT-23-6', 'TPS54202'),
    'L1n': ('Inductor_SMD', 'L_Changjiang_FNR4030S', '10uH 4x4'),
    'C15n': ('Capacitor_SMD', 'C_0805_2012Metric', 'Cin 10uF'),
    'C16n': ('Capacitor_SMD', 'C_0603_1608Metric', 'Cin 100nF'),
    'C17n': ('Capacitor_SMD', 'C_0805_2012Metric', 'Cout 22uF'),
    'C18n': ('Capacitor_SMD', 'C_0805_2012Metric', 'Cout 22uF'),
    'C19n': ('Capacitor_SMD', 'C_0603_1608Metric', 'Cboot'),
    'R16n': ('Resistor_SMD', 'R_0603_1608Metric', 'FB top'),
    'R17n': ('Resistor_SMD', 'R_0603_1608Metric', 'FB bot'),
    'R18n': ('Resistor_SMD', 'R_0603_1608Metric', 'EN pd'),
}
REMOVE = {'R4', 'R6'}
xl = 31.2   # LED x, fixed from centre (triangle-compatible)
PLACE = {
    'J1': (0, 0, 0), 'J2': (-half, 16, 0), 'J3': (half, 16, 0),
    'LED1': (-xl, 13, 270), 'LED2': (0, 13, 270), 'LED3': (xl, 13, 270),
    'C1': (-xl + 3.75, 13, 270), 'C2': (3.75, 13, 270), 'C3': (xl - 3.75, 13, 270),
    # zone A: left side, x -37.4..-25.3
    'R3': (-35.6, 11.0, 90), 'R7': (-35.6, 14.2, 90), 'R8': (-35.6, 17.4, 90),
    'U4n': (-32.0, 6.9, 0), 'C20n': (-28.9, 6.9, 90), 'R5': (-26.8, 6.9, 90),
    # region E: above strip, between LED1 and LED2 -- MCU core
    'U1': (-14.5, 13.3, 180),
    'Y1': (-8.4, 11.7, 90), 'C5': (-5.0, 10.55, 90), 'C6': (-5.0, 13.7, 90),
    'C8': (-8.4, 15.3, 0), 'R15': (-8.4, 17.3, 0), 'C14': (-5.0, 17.0, 90),
    'C7': (-19.9, 13.3, 90), 'C9': (-21.6, 13.3, 90), 'C10': (-23.3, 13.3, 90),
    'R10': (-19.9, 16.6, 90), 'R11': (-21.6, 16.6, 90), 'C4': (-23.8, 16.6, 90),
    # band C: F.Cu under strip, left (no vias)
    'TP4': (-23.5, 6.35, 0), 'TP5': (-19.69, 6.35, 0), 'TP7': (-23.5, 2.54, 0), 'TP8': (-19.69, 2.54, 0),
    'C11': (-17.5, 4.4, 90), 'U2': (-12.9, 4.4, 0), 'R13': (-8.0, 4.4, 90),
    'JP1': (-5.6, 2.3, 90), 'R12': (-5.6, 6.2, 90),
    # band D: F.Cu under strip, right (no vias)
    'D4': (2.0, 4.4, 0),
    'TP6': (5.72, 2.54, 0), 'TP9': (5.72, 6.35, 0), 'TP2': (9.53, 2.54, 0), 'TP1': (9.53, 6.35, 0),
    'C13': (12.0, 4.4, 90), 'U3': (16.4, 4.4, 0), 'C12': (20.3, 4.4, 90), 'R14': (23.5, 5.6, 90),
    # region F: above strip, between LED2 and LED3 -- discovery, TVS
    'R1': (7.5, 11.2, 90), 'D1': (7.5, 14.6, 90), 'R2': (9.5, 14.6, 90),
    'D2': (13.0, 11.2, 0), 'D3': (13.0, 15.4, 0), 'R9': (16.4, 11.6, 90),
    'TP3': (19.05, 11.43, 0), 'TP10': (19.05, 15.24, 0),
    'D5': (24.6, 12.9, 90),
    # zone B: right side, x 25.3..37.4 -- 5 V buck
    'U5n': (28.2, 5.0, 0), 'C19n': (31.3, 5.0, 90), 'L1n': (34.6, 5.0, 0),
    'C15n': (28.2, 8.1, 0), 'C16n': (27.0, 1.6, 0), 'R16n': (30.2, 1.6, 0), 'R17n': (33.4, 1.6, 0),
    'R18n': (32.3, 8.4, 0),
    'C17n': (35.9, 11.5, 90), 'C18n': (35.9, 15.0, 90),
}
b = pcbnew.LoadBoard(src)
for ref, (lib, name, val) in NEW.items():
    fp = pcbnew.FootprintLoad(STD, name)
    fp.SetReference(ref); fp.SetValue(val); b.Add(fp)
allrefs = [f.GetReference() for f in b.GetFootprints()]
for ref in REMOVE:
    b.Delete(b.FindFootprintByReference(ref))
fps = {r: b.FindFootprintByReference(r) for r in allrefs if r not in REMOVE}
missing = set(fps) ^ set(PLACE)
assert not missing, missing
for ref, (x, y, r) in PLACE.items():
    fp = fps[ref]; fp.SetOrientationDegrees(r); fp.SetPosition(P(x, y))
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.Remove(d)
pts = [(-half, 0), (half, 0), (half, H), (-half, H)]
for i in range(4):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*pts[i])); s.SetEnd(P(*pts[(i + 1) % 4]))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.05)); b.Add(s)
ds = b.GetDesignSettings(); ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))
pcbnew.SaveBoard(dst, b)
# envelope report: courtyard extents in board frame (excluding J1-J3)
ext = []
for ref, fp in fps.items():
    if ref in ('J1', 'J2', 'J3'): continue
    for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        cy = fp.GetCourtyard(lay)
        if cy.OutlineCount():
            bb = cy.BBox()
            ext.append((ref, pcbnew.ToMM(bb.GetLeft()) - X0, pcbnew.ToMM(bb.GetRight()) - X0,
                        Y0 - pcbnew.ToMM(bb.GetBottom()), Y0 - pcbnew.ToMM(bb.GetTop())))
print("core x range: %.2f .. %.2f   y range: %.2f .. %.2f" % (
    min(e[1] for e in ext), max(e[2] for e in ext), min(e[3] for e in ext), max(e[4] for e in ext)))
for e in sorted(ext, key=lambda e: -max(abs(e[1]), abs(e[2])))[:4]:
    print("  outermost: %s x %.2f..%.2f y %.2f..%.2f" % e)
