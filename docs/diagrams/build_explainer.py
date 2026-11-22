"""Generates system-explainer.html (the visual explainer for SPEC.md).

Run:  python build_explainer.py
Geometry (hexes, LEDs, edge codes) is computed here so the diagrams stay exact.
"""
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_REF = os.path.join(HERE, "design-reference.html")
OUT_PLAN = os.path.join(HERE, "planning.html")
S3 = math.sqrt(3)

R_PU = 10_000
CODES = [0, 1000, 2700, 5600, 12000, 27000]
RES_LABEL = ["0 Ω", "1.0 kΩ", "2.7 kΩ", "5.6 kΩ", "12 kΩ", "27 kΩ"]
VOLTS = [0.68, 0.91, 1.22, 1.59, 2.08, 2.57]  # SPEC V5 §4.2 (series diode), calibrate on hardware


def n(x):
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def hex_pts(cx, cy, R):
    return [(cx + R * math.cos(math.radians(60 * k)), cy + R * math.sin(math.radians(60 * k))) for k in range(6)]


def pts(p):
    return " ".join(f"{n(x)},{n(y)}" for x, y in p)


def normal(e):
    a = math.radians(60 * e + 30)
    return math.cos(a), math.sin(a)


def shrink(p, q, d):
    L = math.dist(p, q)
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    return (p[0] + ux * d, p[1] + uy * d), (q[0] - ux * d, q[1] - uy * d)


def axial(q, r, R):
    return R * 1.5 * q, R * S3 * (r + q / 2)


AX_NEIGHBORS = {(1, 0): 0, (0, 1): 1, (-1, 1): 2, (-1, 0): 3, (0, -1): 4, (1, -1): 5}
# flat-top hex, y down: edge e sits between vertex e and e+1, outward normal at 60e+30 deg.
# axial neighbour directions above map to the edge index that faces them.


def fix_dirs():
    # verify mapping numerically
    for (dq, dr), e in AX_NEIGHBORS.items():
        x, y = axial(dq, dr, 1)
        a = math.degrees(math.atan2(y, x)) % 360
        assert abs(a - (60 * e + 30) % 360) < 1e-6, (dq, dr, e, a)


fix_dirs()


def defs(p):
    out = [f'<defs>']
    for name, cls in [("ink", "mk-ink"), ("led", "mk-led"), ("can", "mk-can"), ("muted", "mk-muted"), ("sense", "mk-sense")]:
        out.append(
            f'<marker id="{p}-{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" class="{cls}"/></marker>'
        )
    out.append("</defs>")
    return "".join(out)


def text(x, y, s, cls="", anchor="start", extra=""):
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{n(x)}" y="{n(y)}" text-anchor="{anchor}"{c}{extra}>{s}</text>'


def anchor_for(cx):
    return "start" if cx > 0.3 else ("end" if cx < -0.3 else "middle")


# ---------------------------------------------------------------- figure 1: system
def fig_system():
    W, H = 960, 470
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="The coordinator talks to one ESP32 cluster controller per flat cluster over Wi-Fi; each controller runs a CAN bus through its cluster of panels; the AR app sends cluster poses to the coordinator.">', defs("f1")]
    # top row
    o.append('<rect x="60" y="24" width="180" height="64" rx="6" class="box"/>')
    o.append(text(150, 52, "AR app", "t-title", "middle"))
    o.append(text(150, 72, "phone · ARKit/ARCore", "t-muted t-sm", "middle"))
    o.append('<rect x="380" y="24" width="200" height="64" rx="6" class="box box-key"/>')
    o.append(text(480, 52, "Coordinator", "t-title", "middle"))
    o.append(text(480, 72, "room layout · voxel engine", "t-muted t-sm", "middle"))
    o.append('<rect x="720" y="24" width="180" height="64" rx="6" class="box"/>')
    o.append(text(810, 52, "You / home automation", "t-title", "middle"))
    o.append(text(810, 72, "scenes · effects", "t-muted t-sm", "middle"))
    o.append('<line x1="240" y1="56" x2="376" y2="56" class="w-ink" marker-end="url(#f1-ink)"/>')
    o.append(text(308, 48, "cluster poses", "t-sm", "middle"))
    o.append('<line x1="720" y1="56" x2="584" y2="56" class="w-ink" marker-end="url(#f1-ink)"/>')
    o.append(text(652, 48, "commands", "t-sm", "middle"))

    ctrl_x = [140, 480, 820]
    names = ["Wall A", "Wall B", "Ceiling"]
    for cx in ctrl_x:
        o.append(f'<line x1="480" y1="88" x2="{cx}" y2="168" class="w-wifi" marker-end="url(#f1-muted)"/>')
    o.append(text(492, 116, "Wi-Fi", "t-sm t-strong"))
    o.append(text(492, 131, "↓ effects + clock", "t-sm t-muted"))
    o.append(text(492, 146, "↑ topology", "t-sm t-muted"))

    clusters = [
        [(0, 0), (1, 0), (1, -1)],
        [(0, 0), (1, 0), (1, -1), (2, -1)],
        [(0, 0), (1, -1), (0, 1)],
    ]
    rots = [[1, 4, 0], [2, 5, 1, 3], [0, 3, 5]]
    Rh = 25
    for ci, (cx, cl) in enumerate(zip(ctrl_x, clusters)):
        o.append(f'<rect x="{cx-100}" y="170" width="200" height="56" rx="6" class="box"/>')
        o.append(text(cx, 194, "Cluster controller", "t-title", "middle"))
        o.append(text(cx, 213, f"ESP32 · {names[ci]}", "t-muted t-sm", "middle"))
        centers = [axial(q, r, Rh) for q, r in cl]
        mx = (min(c[0] for c in centers) + max(c[0] for c in centers)) / 2
        my = (min(c[1] for c in centers) + max(c[1] for c in centers)) / 2
        centers = [(x - mx + cx, y - my + 352) for x, y in centers]
        top = min(range(len(centers)), key=lambda i: centers[i][1])
        tx, ty = centers[top][0], centers[top][1] - Rh * S3 / 2
        o.append(f'<line x1="{cx}" y1="226" x2="{n(tx)}" y2="{n(ty)}" class="w-can"/>')
        o.append(text(cx + 8, 252, "CAN", "t-sm t-can"))
        o.append(f'<circle cx="{n(tx)}" cy="{n(ty)}" r="3.5" class="dot-can"/>')
        for i, (hx, hy) in enumerate(centers):
            P = hex_pts(hx, hy, Rh)
            o.append(f'<polygon points="{pts(P)}" class="hex"/>')
            a = rots[ci][i]
            p1, p2 = shrink(P[a], P[(a + 1) % 6], 4)
            o.append(f'<line x1="{n(p1[0])}" y1="{n(p1[1])}" x2="{n(p2[0])}" y2="{n(p2[1])}" class="edge-active-sm"/>')
        # bridges
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                d = (cl[j][0] - cl[i][0], cl[j][1] - cl[i][1])
                if d in AX_NEIGHBORS:
                    mx2 = (centers[i][0] + centers[j][0]) / 2
                    my2 = (centers[i][1] + centers[j][1]) / 2
                    o.append(f'<circle cx="{n(mx2)}" cy="{n(my2)}" r="3.5" class="dot-ink"/>')
        o.append(text(cx, 446, f"{names[ci]} · {len(cl)} panels · one CAN bus", "t-sm t-muted", "middle"))
    # annotation for bridge + active board (on cluster B)
    o.append(text(612, 300, "● bridge", "t-sm t-muted"))
    o.append(text(612, 316, "▬ code-0 edge", "t-sm t-led"))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- figure 2: panel anatomy
def fig_panel():
    W, H = 960, 520
    cx, cy, R = 290, 262, 188
    active = 1  # bottom edge
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="A hexagonal panel is six passive edge boards. The code-0 board at the bottom is where the rear controller board joins; the other five are codes 1 to 5 clockwise, each with its own ID resistor. LED data runs once around the inside.">', defs("f2")]
    P = hex_pts(cx, cy, R)
    o.append(f'<polygon points="{pts(P)}" class="hex-face"/>')
    # LED chain path (inner hex)
    Ri = R - 46
    Q = hex_pts(cx, cy, Ri)
    a0, a1 = Q[active], Q[(active + 1) % 6]
    # start just left of the MCU, run clockwise on screen (toward codes 1..5), stop short of the start corner
    chain = [((a0[0] + a1[0]) / 2 - 32, a0[1])]
    for k in range(1, 6):
        chain.append(Q[(active + k) % 6])
    last, corner = Q[(active + 5) % 6], Q[active]
    chain.append(corner)
    chain.append(((a0[0] + a1[0]) / 2 + 34, a0[1]))
    o.append(f'<polyline points="{pts(chain)}" class="w-led-dash" marker-end="url(#f2-led)"/>')
    # boards
    for e in range(6):
        code = (e - active) % 6
        p1, p2 = shrink(P[e], P[(e + 1) % 6], 13)
        cls = "board board-active" if code == 0 else "board"
        o.append(f'<line x1="{n(p1[0])}" y1="{n(p1[1])}" x2="{n(p2[0])}" y2="{n(p2[1])}" class="{cls}"/>')
        nx, ny = normal(e)
        # LEDs on the inner face
        for k in range(3):
            t = 0.22 + k * 0.28
            lx = P[e][0] + (P[(e + 1) % 6][0] - P[e][0]) * t - nx * 15
            ly = P[e][1] + (P[(e + 1) % 6][1] - P[e][1]) * t - ny * 15
            o.append(f'<circle cx="{n(lx)}" cy="{n(ly)}" r="6" class="led"/>')
        mx = (P[e][0] + P[(e + 1) % 6][0]) / 2
        my = (P[e][1] + P[(e + 1) % 6][1]) / 2
        lx, ly = mx + nx * 30, my + ny * 30
        anc = anchor_for(nx)
        y1 = ly - 14 if ny < -0.3 else (ly + 4 if ny > 0.3 else ly - 4)
        if code == 0:
            o.append(text(lx, y1, "edge 0 · code-0 board · ID 0 Ω", "t-strong t-led", anc))
            o.append(text(lx, y1 + 16, "rear controller board joins here", "t-sm t-muted", anc))
        else:
            o.append(text(lx, y1, f"edge {code}", "t-strong", anc))
            o.append(text(lx, y1 + 15, f"ID {RES_LABEL[code]}", "t-sm t-muted", anc))
    # MCU chip on the active board
    mx = (P[active][0] + P[(active + 1) % 6][0]) / 2
    my = (P[active][1] + P[(active + 1) % 6][1]) / 2
    o.append(f'<rect x="{n(mx-26)}" y="{n(my-44)}" width="52" height="22" rx="3" class="chip"/>')
    o.append(text(mx, my - 29, "CTRL", "t-xs t-chip", "middle"))
    # corner connections
    for v in P:
        o.append(f'<circle cx="{n(v[0])}" cy="{n(v[1])}" r="7" class="corner"/>')
    v = P[5]
    o.append(f'<line x1="{n(v[0]+8)}" y1="{n(v[1]-8)}" x2="{n(v[0]+40)}" y2="{n(v[1]-40)}" class="w-leader"/>')
    o.append(text(v[0] + 44, v[1] - 44, "corner connection", "t-sm"))
    # center labels
    o.append(text(cx, cy - 18, "LED data chain", "t-strong t-led", "middle"))
    o.append(text(cx, cy - 2, "loops back to the MCU", "t-sm t-led", "middle"))
    o.append(text(cx, cy + 28, "air gap behind", "t-sm t-muted", "middle"))
    o.append(text(cx, cy + 43, "diffuser film", "t-sm t-muted", "middle"))

    # net table
    x0 = 590
    o.append(text(x0, 92, "What crosses each joint", "t-title"))
    o.append(text(x0 + 220, 120, "corner", "t-sm t-muted", "middle"))
    o.append(text(x0 + 300, 120, "bridge", "t-sm t-muted", "middle"))
    rows = [
        ("+24V", "sw-power", True, True),
        ("GND", "sw-gnd", True, True),
        ("LED DIN", "sw-led", True, False),
        ("+5V LED rail", "sw-5v", True, False),
        ("LED return (last corner)", "sw-led", True, False),
        ("CANH", "sw-can", True, True),
        ("CANL", "sw-can", True, True),
        ("SENSE", "sw-sense", True, True),
        ("DRIVE", "sw-sense", True, True),
    ]
    for i, (name, sw, c, b) in enumerate(rows):
        y = 148 + i * 30
        o.append(f'<line x1="{x0}" y1="{y+10}" x2="{x0+330}" y2="{y+10}" class="rule"/>')
        o.append(f'<rect x="{x0}" y="{y-9}" width="12" height="12" rx="2" class="{sw}"/>')
        o.append(text(x0 + 22, y + 2, name))
        o.append(text(x0 + 220, y + 2, "✓" if c else "—", "t-strong" if c else "t-muted", "middle"))
        o.append(text(x0 + 300, y + 2, "✓" if b else "—", "t-strong" if b else "t-muted", "middle"))
    o.append(text(x0, 424, "LED data never leaves its panel.", "t-sm"))
    o.append(text(x0, 440, "Panels share power, CAN and the ID lines.", "t-sm t-muted"))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- figure 3: seam cross-section
def fig_seam():
    W, H = 960, 430
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Side cut through the seam between two panels: each seam board has LEDs on its inward face and copper power planes on its exterior face; contact pads on each exterior face are pressed by low-cost springs on both faces of a thin bridge PCB standing upright in the seam, held by a 3D-printed carrier.">', defs("f3")]
    o.append(text(24, 30, "room ↑", "t-sm t-muted"))
    # wall
    o.append('<rect x="0" y="380" width="960" height="22" class="wall"/>')
    o.append(text(24, 396, "wall", "t-sm t-muted"))
    boards = [(40, "out"), (430, "seamL"), (518, "seamR"), (910, "out")]
    top, bot = 70, 330
    # diffusers
    o.append('<rect x="40" y="60" width="402" height="4" class="diffuser"/>')
    o.append('<rect x="518" y="60" width="402" height="4" class="diffuser"/>')
    o.append(text(60, 50, "diffuser film (LCD-style)", "t-sm"))
    # light rays
    rays = [((418, 180), [(300, 66), (180, 66), (90, 140)]), ((542, 180), [(660, 66), (780, 66), (870, 140)]),
            ((62, 200), [(170, 66), (260, 120)]), ((898, 200), [(790, 66), (700, 120)])]
    for (sx, sy), targets in rays:
        for tx, ty in targets:
            o.append(f'<line x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" class="ray"/>')
    for x, kind in boards:
        o.append(f'<rect x="{x}" y="{top}" width="12" height="{372-top}" class="pcb"/>')
    # copper exterior faces on seam boards
    o.append(f'<rect x="442" y="{top}" width="5" height="{326-top}" class="copper"/>')
    o.append(f'<rect x="513" y="{top}" width="5" height="{326-top}" class="copper"/>')
    for px in (442, 514):
        o.append(f'<rect x="{px}" y="340" width="4" height="30" class="finger"/>')
    # LEDs on inward faces
    for x in (418, 530):
        o.append(f'<rect x="{x}" y="170" width="12" height="20" rx="2" class="led"/>')
    o.append('<rect x="52" y="190" width="10" height="20" rx="2" class="led"/>')
    o.append('<rect x="898" y="190" width="10" height="20" rx="2" class="led"/>')
    # MCU on left seam board (active)
    # seam bridge: thin PCB upright in the seam, top-contact springs on both faces, printed carrier
    o.append('<rect x="452" y="322" width="56" height="56" rx="3" class="encl"/>')
    o.append('<rect x="478" y="328" width="4" height="46" class="bpcb"/>')
    o.append('<path d="M478,334 L468,334 Q450,342 449,354 L458,364" class="spring"/>')
    o.append('<path d="M482,334 L492,334 Q510,342 511,354 L502,364" class="spring"/>')
    # labels
    o.append(text(240, 230, "air gap", "t-sm t-muted", "middle"))
    o.append(text(720, 230, "air gap", "t-sm t-muted", "middle"))
    o.append(text(240, 104, "Panel 1", "t-title", "middle"))
    o.append(text(720, 104, "Panel 2", "t-title", "middle"))
    o.append('<line x1="480" y1="22" x2="480" y2="40" class="w-leader"/>')
    o.append('<path d="M480,40 L447,96 M480,40 L513,96" class="w-leader"/>')
    o.append(text(490, 24, "exterior faces: contact pads, +24V / GND lanes", "t-sm t-power"))
    o.append('<line x1="560" y1="150" x2="534" y2="176" class="w-leader"/>')
    o.append(text(566, 150, "inward face: LEDs, LED data, CAN, ID lines", "t-sm"))
    o.append('<line x1="562" y1="320" x2="483" y2="330" class="w-leader"/>')
    o.append(text(566, 324, "upright bridge PCB in the seam (≈6–8 mm)", "t-sm"))
    o.append('<line x1="562" y1="336" x2="511" y2="350" class="w-leader"/>')
    o.append(text(566, 340, "$0.02 top-contact springs, free end toward the wall", "t-sm"))
    o.append('<line x1="562" y1="352" x2="518" y2="356" class="w-leader"/>')
    o.append(text(566, 356, "contact pads on each exterior face", "t-sm"))
    o.append('<line x1="562" y1="368" x2="508" y2="372" class="w-leader"/>')
    o.append(text(566, 372, "3D-printed carrier, anchored to the wall", "t-sm"))
    o.append(text(936, 30, "not to scale", "t-xs t-muted", "end"))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- figure 4: mirror rule
def fig_mirror():
    o = ['<svg viewBox="0 0 960 320" role="img" aria-label="All ten edge-contact pads sit on the exterior face along the wall edge: three GND, two +24V and five signals, with GND reaching closest to the edge. The bridge PCB connects each net straight through, except SENSE and DRIVE, which it crosses.">']
    edge = 236
    o.append(text(30, 28, "Exterior face · 10 contact pads along the wall edge", "t-title"))
    o.append(f'<rect x="30" y="44" width="570" height="{edge-44}" rx="3" class="pcb-body"/>')
    o.append('<rect x="40" y="52" width="550" height="62" class="plane"/>')
    o.append(text(315, 88, "+24V and GND lanes (others on either face)", "t-xs t-body-on", "middle"))
    nets = [("GND", "sw-gnd", 3), ("+24V", "sw-power", 6), ("GND", "sw-gnd", 3), ("CANH", "sw-can", 9), ("CANL", "sw-can2", 9),
            ("DRIVE", "sw-drive", 9), ("SENSE", "sw-sense", 9), ("SPARE", "sw-spare", 9), ("+24V", "sw-power", 6), ("GND", "sw-gnd", 3)]
    x0 = 315 - (9 * 52 + 30) / 2
    for i, (nm, sw, gap) in enumerate(nets):
        x = x0 + i * 52
        o.append(f'<rect x="{n(x)}" y="140" width="30" height="{edge-gap-140}" class="{sw}"/>')
        if gap == 9:
            o.append(f'<circle cx="{n(x+15)}" cy="128" r="4" class="via"/>')
        o.append(text(x + 15, 254, f"X{i+1}", "t-xs t-muted", "middle"))
        o.append(text(x + 15, 270, nm, "t-xs", "middle"))
    o.append(text(600, 128, "◀ vias up to the inward face", "t-xs t-body-on", "end"))
    o.append(text(30, 298, "Pads stop 0.9 mm (signals), 0.6 mm (+24V), 0.3 mm (GND) short of the", "t-xs t-muted"))
    o.append(text(30, 314, "wall edge, so GND meets its spring first as the panel slides in.", "t-xs t-muted"))
    o.append(text(690, 28, "Bridge routing", "t-title"))
    o.append('<rect x="752" y="58" width="116" height="192" rx="3" class="bpcb-band"/>')
    o.append(text(744, 52, "Panel A", "t-xs t-strong", "end"))
    o.append(text(876, 52, "Panel B", "t-xs t-strong"))
    rnets = ["GND", "+24V", "CANH", "CANL", "SENSE", "DRIVE", "SPARE"]
    ys = {nm: 74 + i * 28 for i, nm in enumerate(rnets)}
    for nm in rnets:
        o.append(text(744, ys[nm] + 4, nm, "t-xs", "end"))
        o.append(text(876, ys[nm] + 4, nm, "t-xs"))
        other = {"SENSE": "DRIVE", "DRIVE": "SENSE"}.get(nm, nm)
        o.append(f'<line x1="752" y1="{ys[nm]}" x2="868" y2="{ys[other]}" class="{"mate-cross" if other != nm else "route"}"/>')
    o.append(text(810, 274, "the SENSE ↔ DRIVE cross", "t-xs t-sense", "middle"))
    o.append(text(810, 290, "is in the bridge traces", "t-xs t-sense", "middle"))
    o.append(text(810, 308, "180° symmetric: fits either way", "t-xs t-muted", "middle"))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- figure 5: discovery circuit
def zig_v(x, y0, y1, w=8, k=6):
    step = (y1 - y0) / k
    p = [(x, y0)]
    for i in range(k):
        p.append((x + (w if i % 2 == 0 else -w), y0 + step * (i + 0.5)))
    p.append((x, y1))
    return pts(p)


def zig_h(y, x0, x1, h=8, k=6):
    step = (x1 - x0) / k
    p = [(x0, y)]
    for i in range(k):
        p.append((x0 + step * (i + 0.5), y + (h if i % 2 == 0 else -h)))
    p.append((x1, y))
    return pts(p)


def fig_circuit():
    W, H = 960, 400
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="When panel B pulls its DRIVE line low, current flows from 3.3 V through A\'s 10 kilohm pull-up, a diode and A\'s edge ID resistor, across the bridge into B. A reads a voltage that identifies its own edge.">', defs("f5")]
    o.append('<line x1="480" y1="20" x2="480" y2="236" class="seam"/>')
    o.append(text(480, 252, "bridge crosses SENSE ↔ DRIVE", "t-sm t-muted", "middle"))
    o.append(text(240, 26, "Panel A · listening", "t-title", "middle"))
    o.append(text(720, 26, "Panel B · its turn", "t-title", "middle"))
    # A side
    o.append(text(120, 58, "3.3 V", "t-strong", "middle"))
    o.append('<line x1="120" y1="64" x2="120" y2="76" class="w-ink"/>')
    o.append(f'<polyline points="{zig_v(120, 76, 120)}" class="w-ink"/>')
    o.append('<line x1="120" y1="120" x2="120" y2="140" class="w-ink"/>')
    o.append(text(134, 102, "R_pu 10 kΩ", "t-sm"))
    o.append('<circle cx="120" cy="140" r="3.5" class="dot-ink"/>')
    o.append('<line x1="120" y1="140" x2="76" y2="140" class="w-ink"/>')
    o.append('<rect x="24" y="128" width="52" height="24" rx="3" class="box"/>')
    o.append(text(50, 144, "ADC", "t-sm", "middle"))
    o.append(text(50, 170, "A's MCU", "t-xs t-muted", "middle"))
    o.append('<line x1="120" y1="140" x2="300" y2="140" class="w-sense"/>')
    o.append(text(210, 130, "SENSE bus", "t-sm t-sense", "middle"))
    o.append(f'<polyline points="{zig_h(140, 300, 380)}" class="w-sense"/>')
    o.append(text(330, 118, "R_k (this edge only)", "t-sm", "middle"))
    o.append('<line x1="380" y1="140" x2="400" y2="140" class="w-sense"/>')
    o.append('<polygon points="400,131 400,149 418,140" class="diode"/>')
    o.append('<line x1="418" y1="131" x2="418" y2="149" class="w-sense"/>')
    o.append('<line x1="418" y1="140" x2="446" y2="140" class="w-sense"/>')
    o.append(text(409, 168, "1N4148WS", "t-xs t-muted", "middle"))
    o.append('<rect x="446" y="128" width="24" height="24" class="finger"/>')
    o.append(text(458, 178, "SENSE", "t-xs", "middle"))
    o.append(text(458, 191, "pad", "t-xs t-muted", "middle"))
    # B side
    o.append('<rect x="490" y="128" width="24" height="24" class="finger"/>')
    o.append(text(502, 178, "DRIVE", "t-xs", "middle"))
    o.append(text(502, 191, "pad", "t-xs t-muted", "middle"))
    o.append('<line x1="514" y1="140" x2="760" y2="140" class="w-sense"/>')
    o.append(text(640, 130, "DRIVE bus", "t-sm t-sense", "middle"))
    o.append('<rect x="760" y="128" width="64" height="24" rx="3" class="box"/>')
    o.append(text(792, 144, "FET", "t-sm", "middle"))
    o.append('<line x1="792" y1="152" x2="792" y2="196" class="w-ink"/>')
    o.append('<path d="M776,196 H808 M781,203 H803 M787,210 H797" class="w-ink"/>')
    o.append(text(836, 144, "pulls LOW", "t-sm t-strong"))
    o.append(text(836, 160, "on command", "t-sm t-muted"))
    # current arrows
    for x in (228, 410, 580, 700):
        o.append(f'<path d="M{x-6},{134} L{x+4},{140} L{x-6},{146}" class="arrow-sense"/>')
    o.append(text(624, 96, "B's SENSE ↔ A's DRIVE: idle this turn", "t-xs t-muted", "middle"))
    o.append(text(24, 226, "V_ADC ≈ Vf + (3.3 V − Vf) × R_k / (10 kΩ + R_k)", "t-strong"))

    # ruler
    x0, x1, y = 80, 880, 330
    sx = (x1 - x0) / 3.3
    o.append(text(x0, 288, "What A reads → which of A's edges touches B", "t-sm t-muted"))
    o.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" class="w-ink"/>')
    marks = [(VOLTS[i], f"edge {i}", RES_LABEL[i]) for i in range(6)] + [(3.3, "idle", "no driver")]
    for v, lab, sub in marks:
        x = x0 + v * sx
        o.append(f'<line x1="{n(x)}" y1="{y-6}" x2="{n(x)}" y2="{y+6}" class="w-ink"/>')
        o.append(text(x, y - 12, lab, "t-sm t-strong", "middle"))
        o.append(text(x, y + 22, f"{v:.2f} V", "t-xs", "middle"))
        o.append(text(x, y + 36, sub, "t-xs t-muted", "middle"))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- figure 6: discovery stepper
STEP_CLUSTER = [("A", (0, 0), 0), ("B", (1, -1), 2), ("C", (1, 0), 5), ("D", (2, 0), 1), ("E", (-1, 1), 3)]


def stepper_data(Rh, ox, oy):
    panels = []
    for name, (q, r), rot in STEP_CLUSTER:
        x, y = axial(q, r, Rh)
        panels.append({"id": name, "q": q, "r": r, "rot": rot, "x": x + ox, "y": y + oy})
    for p in panels:
        p["codes"] = [(e - p["rot"]) % 6 for e in range(6)]
        p["nb"] = {}
        for o2 in panels:
            d = (o2["q"] - p["q"], o2["r"] - p["r"])
            if d in AX_NEIGHBORS:
                e = AX_NEIGHBORS[d]
                p["nb"][str(e)] = [o2["id"], (e + 3) % 6]
    return panels


def fig_stepper():
    W, H = 560, 420
    Rh = 56
    panels = stepper_data(Rh, 0, 0)
    xs = [p["x"] for p in panels]
    ys = [p["y"] for p in panels]
    ox = W / 2 - (min(xs) + max(xs)) / 2
    oy = H / 2 - (min(ys) + max(ys)) / 2
    for p in panels:
        p["x"] += ox
        p["y"] += oy
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Five panels, A to E, mounted at different rotations. Each turn one panel drives its DRIVE line low and its neighbours report which of their own edges heard it." id="stepper-svg">']
    for p in panels:
        P = hex_pts(p["x"], p["y"], Rh)
        o.append(f'<polygon points="{pts(P)}" class="hex" id="hx-{p["id"]}"/>')
    for p in panels:
        P = hex_pts(p["x"], p["y"], Rh)
        for e in range(6):
            p1, p2 = shrink(P[e], P[(e + 1) % 6], 7)
            code = p["codes"][e]
            cls = "sedge sedge-active" if code == 0 else "sedge"
            o.append(f'<line x1="{n(p1[0])}" y1="{n(p1[1])}" x2="{n(p2[0])}" y2="{n(p2[1])}" class="{cls}" id="ed-{p["id"]}-{e}"/>')
            nx, ny = normal(e)
            mx = (P[e][0] + P[(e + 1) % 6][0]) / 2 - nx * 13
            my = (P[e][1] + P[(e + 1) % 6][1]) / 2 - ny * 13
            o.append(text(mx, my + 3.5, str(code), "t-xs t-muted" if code else "t-xs t-led", "middle", f' id="cd-{p["id"]}-{e}"'))
        o.append(text(p["x"], p["y"] + 2, p["id"], "t-hexid", "middle"))
        o.append(text(p["x"], p["y"] + 20, "", "t-xs t-note", "middle", f' id="nt-{p["id"]}"'))
    o.append("</svg>")
    data = [{"id": p["id"], "codes": p["codes"], "nb": p["nb"]} for p in panels]
    return "".join(o), data


# ---------------------------------------------------------------- figure 7: rendering
PALETTE = [(24, 38, 140), (120, 40, 200), (236, 64, 122), (255, 170, 40), (255, 236, 170)]
WAVE = {"kx": 0.022, "ky": 0.009, "w": 1.6}


def pal(v):
    v = max(0.0, min(1.0, v)) * (len(PALETTE) - 1)
    i = min(int(v), len(PALETTE) - 2)
    t = v - i
    a, b = PALETTE[i], PALETTE[i + 1]
    return "#%02x%02x%02x" % tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3))


def fig_render():
    W, H = 960, 440
    Rh = 44
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Two wall clusters separated by a gap show one continuous colour wave, because every panel evaluates the same formula at its own LED positions in shared room coordinates." id="render-svg">', defs("f7")]
    o.append('<rect x="0" y="0" width="960" height="440" rx="8" class="stage"/>')
    o.append('<rect x="250" y="20" width="460" height="40" rx="6" class="msg"/>')
    o.append(text(480, 45, "wave · k=(0.022, 0.009) · ω=1.6 · palette 4 · t₀", "t-sm t-stage", "middle"))
    o.append(text(240, 45, "one CAN message →", "t-sm t-stage-muted", "end"))
    o.append(text(720, 45, "← each node renders", "t-sm t-stage-muted"))
    clusters = [
        ([(0, 0), (1, 0), (1, -1), (0, 1), (2, -1)], 110, 228, "Wall A cluster"),
        ([(0, 0), (1, -1), (1, 0), (0, 1)], 640, 250, "Wall B cluster"),
    ]
    leds = []
    for cl, ox, oy, label in clusters:
        cxs = [axial(q, r, Rh)[0] + ox for q, r in cl]
        o.append(text((min(cxs) + max(cxs)) / 2, 420, label, "t-sm t-stage-muted", "middle"))
        for q, r in cl:
            x, y = axial(q, r, Rh)
            x += ox
            y += oy
            P = hex_pts(x, y, Rh)
            o.append(f'<polygon points="{pts(P)}" class="hex-stage"/>')
            for e in range(6):
                nx, ny = normal(e)
                for k in range(3):
                    t = 0.2 + k * 0.3
                    lx = P[e][0] + (P[(e + 1) % 6][0] - P[e][0]) * t - nx * 7
                    ly = P[e][1] + (P[(e + 1) % 6][1] - P[e][1]) * t - ny * 7
                    leds.append((round(lx, 1), round(ly, 1)))
    for lx, ly in leds:
        v = 0.5 + 0.5 * math.sin(0 - (WAVE["kx"] * lx + WAVE["ky"] * ly))
        o.append(f'<circle cx="{lx}" cy="{ly}" r="5" class="px" fill="{pal(v)}"/>')
    o.append('<line x1="470" y1="110" x2="470" y2="400" class="stage-gap"/>')
    o.append(text(470, 100, "gap: no wiring between clusters", "t-xs t-stage-muted", "middle"))
    o.append("</svg>")
    return "".join(o), leds


# ---------------------------------------------------------------- figure 8: power domains
def fig_power():
    W, H = 960, 270
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Two power supplies each feed their own domain through an injection bridge and fuse. An isolating bridge between the domains carries GND and CAN but no +24V, so the supplies never back-feed each other.">', defs("f8")]
    px = [150, 270, 390, 530, 650, 770]
    for x in px:
        o.append(f'<rect x="{x}" y="100" width="100" height="72" rx="6" class="panel-box"/>')
        o.append(text(x + 50, 166, "panel", "t-xs t-muted", "middle"))
    # bridges
    for x in (253, 373, 633, 753):
        o.append(f'<rect x="{x}" y="96" width="14" height="80" rx="2" class="bridge"/>')
    o.append('<rect x="503" y="96" width="14" height="80" rx="2" class="bridge-iso"/>')
    # injection bridges
    for x in (128, 878):
        o.append(f'<rect x="{x}" y="96" width="14" height="80" rx="2" class="bridge"/>')
    # rails
    o.append('<line x1="135" y1="118" x2="503" y2="118" class="w-power"/>')
    o.append('<line x1="517" y1="118" x2="885" y2="118" class="w-power"/>')
    o.append('<line x1="135" y1="148" x2="885" y2="148" class="w-can"/>')
    o.append(text(122, 122, "+24V", "t-sm t-power", "end"))
    o.append(text(122, 152, "GND + CAN", "t-sm t-can", "end"))
    # PSUs
    for cx, name in ((135, "PSU 1"), (885, "PSU 2")):
        o.append(f'<rect x="{cx-50}" y="10" width="100" height="40" rx="6" class="box"/>')
        o.append(text(cx, 35, name, "t-title", "middle"))
        o.append(f'<line x1="{cx}" y1="50" x2="{cx}" y2="96" class="w-power"/>')
        o.append(f'<rect x="{cx-7}" y="62" width="14" height="20" rx="2" class="fuse"/>')
        side = 1 if cx < 480 else -1
        o.append(text(cx + side * 14, 76, "fuse", "t-xs", "start" if side > 0 else "end"))
    o.append(text(135, 196, "injection bridge", "t-xs t-muted", "middle"))
    o.append(text(885, 196, "injection bridge", "t-xs t-muted", "middle"))
    o.append('<line x1="510" y1="74" x2="510" y2="92" class="w-leader"/>')
    o.append(text(510, 68, "isolating bridge: no +24V contacts", "t-sm t-strong", "middle"))
    # domain brackets
    for a, b, lab in ((135, 503, "Domain 1 · limited to PSU 1's budget"), (517, 885, "Domain 2 · limited to PSU 2's budget")):
        o.append(f'<path d="M{a},216 V224 H{b} V216" class="w-leader"/>')
        o.append(text((a + b) / 2, 244, lab, "t-sm", "middle"))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- figure 9: AR placement
SYMCLS = {"R": "sym-r", "G": "sym-g", "B": "sym-b", "0": "sym-off", "W": "sym-w"}


def code_for(pid):
    digits = []
    v = pid
    for _ in range(6):
        digits.append(v % 4)
        v //= 4
    chk = sum(digits) % 4
    return ["W"] + ["0RGB"[d] for d in digits] + ["0RGB"[chk], "0RGB"[(chk + 2) % 4]]


def fig_ar():
    W, H = 960, 340
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Every panel flashes a unique colour sequence. The phone tracks each glowing panel, decodes its ID, raycasts it onto the detected wall plane, then fits the whole cluster pose to the layout already known from discovery.">', defs("f9")]
    o.append(text(20, 28, "Each panel flashes its own time code", "t-title"))
    o.append(text(211, 52, "sync", "t-xs t-muted", "middle"))
    o.append(text(289, 52, "panel ID · 6 symbols", "t-xs t-muted", "middle"))
    o.append(text(393, 52, "check", "t-xs t-muted", "middle"))
    for i, (pid, cl) in enumerate([(42, "Wall A"), (19, "Wall A"), (55, "Ceiling")]):
        y = 92 + i * 72
        o.append(f'<polygon points="{pts(hex_pts(46, y, 22))}" class="hex"/>')
        o.append(text(80, y - 4, f"panel {pid}", "t-strong"))
        o.append(text(80, y + 12, cl, "t-xs t-muted"))
        for k, s in enumerate(code_for(pid)):
            x = 200 + k * 26
            o.append(f'<rect x="{x}" y="{y-11}" width="22" height="22" rx="3" class="{SYMCLS[s]}"/>')
    o.append('<line x1="200" y1="300" x2="430" y2="300" class="w-ink" marker-end="url(#f9-ink)"/>')
    o.append(text(200, 320, "time · 250 ms per symbol · ≈2.3 s per code", "t-xs t-muted"))
    # pipeline
    steps = [
        ("1 · Track glowing panels", "ARKit camera pose every frame"),
        ("2 · Decode each code", "sync + ID + checksum → panel ID"),
        ("3 · Raycast to the surface", "detected plane or LiDAR depth → 3D point"),
        ("4 · Fit the cluster pose", "match discovery layout · 6-DoF · metres"),
    ]
    for i, (t, s) in enumerate(steps):
        y = 24 + i * 78
        o.append(f'<rect x="520" y="{y}" width="410" height="54" rx="6" class="box{" box-key" if i == 3 else ""}"/>')
        o.append(text(536, y + 23, t, "t-title"))
        o.append(text(536, y + 42, s, "t-sm t-muted"))
        if i < 3:
            o.append(f'<line x1="725" y1="{y+54}" x2="725" y2="{y+76}" class="w-ink" marker-end="url(#f9-ink)"/>')
    o.append('<line x1="446" y1="51" x2="516" y2="51" class="w-ink" marker-end="url(#f9-ink)"/>')
    o.append(text(481, 43, "video", "t-xs t-muted", "middle"))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- figure 10: flow between rooms
FW, FH = 60, 30
SRC = (8, 7)
FLOW_PANELS = [("A1", [(x, 1) for x in range(12, 18)]), ("B1", [(31, y) for y in range(4, 11)]),
               ("B2", [(x, 1) for x in range(42, 49)]), ("B3", [(58, y) for y in range(12, 19)])]


def floor_walls():
    wall = [[False] * FW for _ in range(FH)]
    for x in range(FW):
        wall[0][x] = wall[FH - 1][x] = True
    for y in range(FH):
        wall[y][0] = wall[y][FW - 1] = True
        if not (21 <= y <= 25):
            wall[y][30] = True
    return wall


def geodesic(wall):
    import heapq
    INF = float("inf")
    d = [[INF] * FW for _ in range(FH)]
    sx, sy = SRC
    d[sy][sx] = 0
    h = [(0, sx, sy)]
    while h:
        c, x, y = heapq.heappop(h)
        if c > d[y][x]:
            continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if not dx and not dy:
                    continue
                nx2, ny2 = x + dx, y + dy
                if not (0 <= nx2 < FW and 0 <= ny2 < FH) or wall[ny2][nx2]:
                    continue
                if dx and dy and (wall[y][nx2] or wall[ny2][x]):
                    continue
                nc = c + (1.4142 if dx and dy else 1)
                if nc < d[ny2][nx2]:
                    d[ny2][nx2] = nc
                    heapq.heappush(h, (nc, nx2, ny2))
    return d


def fig_flow():
    wall = floor_walls()
    geo = geodesic(wall)
    sx, sy = SRC
    euc = [[math.hypot(x - sx, y - sy) for x in range(FW)] for y in range(FH)]
    C = 7
    maps = [("Straight-line distance (walls ignored)", euc, 20), ("Voxel path distance (through the doorway)", geo, 500)]
    W, H = 960, 330
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Two floor plans of the same two rooms. With straight-line distance the light front passes through the wall and lights panels in room B too early. With voxel path distance the front bends through the doorway." id="flow-svg">']
    dists, pdist = [], []
    front0 = 30
    tail = 7
    for mi, (title, D, ox) in enumerate(maps):
        oy = 46
        o.append(text(ox, 30, title, "t-title"))
        o.append(f'<rect x="{ox}" y="{oy}" width="{FW*C}" height="{FH*C}" class="floor"/>')
        for y in range(FH):
            for x in range(FW):
                if wall[y][x]:
                    o.append(f'<rect x="{ox+x*C}" y="{oy+y*C}" width="{C}" height="{C}" class="wallcell"/>')
                else:
                    dd = D[y][x]
                    dists.append(round(dd, 1))
                    delta = front0 - dd
                    op = (1 - delta / tail) * 0.85 if 0 <= delta < tail else 0
                    o.append(f'<rect x="{ox+x*C}" y="{oy+y*C}" width="{C}" height="{C}" class="cell" fill-opacity="{op:.2f}"/>')
        for name, cells in FLOW_PANELS:
            pd = sum(D[y][x] for x, y in cells) / len(cells)
            pdist.append(round(pd, 1))
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            lit = " lit" if 0 <= front0 - pd < tail * 1.5 else ""
            o.append(f'<rect x="{ox+min(xs)*C}" y="{oy+min(ys)*C}" width="{(max(xs)-min(xs)+1)*C}" height="{(max(ys)-min(ys)+1)*C}" rx="2" class="pmark{lit}"/>')
            lx = ox + (min(xs) + max(xs) + 1) / 2 * C
            ly = oy + (min(ys) + max(ys) + 1) / 2 * C
            if name == "B1":
                o.append(text(lx + 10, ly + 4, name, "t-xs t-strong"))
            elif name == "B3":
                o.append(text(lx - 10, ly + 4, name, "t-xs t-strong", "end"))
            else:
                o.append(text(lx, ly + 18, name, "t-xs t-strong", "middle"))
        o.append(f'<circle cx="{ox+(sx+.5)*C}" cy="{oy+(sy+.5)*C}" r="6" class="src"/>')
        o.append(text(ox + (sx + .5) * C, oy + (sy + .5) * C + 20, "effect starts", "t-xs", "middle"))
        o.append(text(ox + 15 * C, oy + FH * C + 18, "Room A", "t-sm t-muted", "middle"))
        o.append(text(ox + 45 * C, oy + FH * C + 18, "Room B", "t-sm t-muted", "middle"))
        o.append(text(ox + 30.5 * C, oy + 26 * C + 14, "door", "t-xs t-muted", "middle"))
    o.append(text(20, 316, "▬ panel clusters on the walls light up as the front reaches them · 1 cell = 20 cm", "t-xs t-muted"))
    o.append("</svg>")
    maxd = max(v for row in geo for v in row if v != float("inf"))
    return "".join(o), dists, pdist, round(maxd, 1)


# ---------------------------------------------------------------- figure 11: cost ranges
HEX_COST = [
    ("LEDs (12–18 × SKC6812RGBW)", 1.56, 2.88, "2–3 per edge at $0.13–0.16 each, RGBW"),
    ("5 V rail (24 V buck, LED switch, level shifter)", 0.80, 1.10, "TPS54360B, P-MOSFET, AHCT1G125, extended-part fees"),
    ("Bridges (share of 1.5–2.5)", 1.05, 3.00, "20 × LCSC BW0019 springs + PCB + carrier ≈ $0.70–1.20 each"),
    ("PCBs (6 short edge boards + 1 small controller board)", 1.50, 3.20, "edge 2-layer $0.20–0.40 each, controller 4-layer $0.30–0.80"),
    ("Controller board parts", 1.00, 1.50, "MCU, TCAN1044V, crystal, LDO, TVS"),
    ("PETG frame + back plate", 0.80, 1.40, "55–70 g at $15–20/kg"),
    ("Controller + coordinator share", 0.60, 1.20, "≈$8 per controller, 10–20 panels each"),
    ("Power share (PSU, fuses, wire)", 0.50, 1.00, "one 24 V supply per ≈23 panels at full output, more when brightness-capped"),
    ("PCB assembly fees, amortized", 0.40, 0.90, "two orders (edge boards, controller boards); joints hand-soldered"),
    ("Diffuser film", 0.15, 0.60, "LCD-style PET/PC diffuser film, 1–2 layers"),
    ("Mounting hardware", 0.20, 0.60, ""),
    ("Corner jumpers + wire", 0.10, 0.30, ""),
    ("LED decoupling + passives", 0.05, 0.15, ""),
]


def fig_cost():
    rows = sorted(HEX_COST, key=lambda r: -r[2])
    W = 960
    H = 40 + len(rows) * 30 + 40
    x0, x1, vmax = 300, 860, 4
    sx = lambda v: x0 + (x1 - x0) * v / vmax
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Cost range per hexagon panel by item. No single item dominates any more; edge PCBs, bridges and LEDs lead.">']
    for v in range(0, vmax + 1, 1):
        o.append(f'<line x1="{n(sx(v))}" y1="24" x2="{n(sx(v))}" y2="{H-34}" class="grid"/>')
        o.append(text(sx(v), H - 16, f"${v}", "t-xs t-muted", "middle"))
    for i, (name, lo, hi, basis) in enumerate(rows):
        y = 40 + i * 30
        tip = f"{name}: ${lo:.2f}–{hi:.2f}" + (f" ({basis})" if basis else "")
        o.append(f'<g class="rrow"><title>{tip}</title>')
        o.append(f'<rect x="0" y="{y-14}" width="{W}" height="28" class="hit"/>')
        o.append(text(286, y + 4, name, "t-sm", "end"))
        o.append(f'<rect x="{n(sx(lo))}" y="{y-6}" width="{n(max(sx(hi)-sx(lo), 4))}" height="12" rx="4" class="rbar"/>')
        o.append(text(sx(hi) + 8, y + 4, f"${lo:.2f}–{hi:.2f}", "t-xs t-muted"))
        o.append("</g>")
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- page
CSS = r"""
:root{
  /* Layout: single reading column, figures break out wider; legend chips encode the same 4 net colours used in every diagram */
  --bg:#f3f5f8; --surface:#ffffff; --surface-2:#eef1f6; --ink:#17202e; --muted:#5b6678; --line:#d3d9e3;
  --board:#3e4b61; --board-on:#f3f5f8; --power:#b5602a; --gnd:#4a5568; --can:#2463d1; --can2:#8fb0ea;
  --led:#d89a00; --led-ink:#8f6500; --sense:#7b44cc; --gold:#d9b44a; --clip:#b9c2cf; --diffuser:#e9edf3;
  --stage:#0e121a; --stage-hex:#1a2130; --stage-ink:#e7ebf2; --stage-muted:#8f9ab0; --key:#17202e;
  --display:"Space Grotesk", "Segoe UI", system-ui, sans-serif;
  --body:"IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, "Cascadia Mono", Consolas, monospace;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#0f131a; --surface:#161c26; --surface-2:#1c2330; --ink:#e6eaf1; --muted:#9aa4b6; --line:#2b3444;
  --board:#8d9cb6; --board-on:#0f131a; --power:#e48c50; --gnd:#8592a8; --can:#5b9bff; --can2:#3a5f9e;
  --led:#f2b630; --led-ink:#f2b630; --sense:#b38af4; --gold:#c9a640; --clip:#3a4456; --diffuser:#232b38;
  --stage:#0a0d13; --stage-hex:#161c28; --key:#e6eaf1; color-scheme:dark; } }
:root[data-theme="dark"]{
  --bg:#0f131a; --surface:#161c26; --surface-2:#1c2330; --ink:#e6eaf1; --muted:#9aa4b6; --line:#2b3444;
  --board:#8d9cb6; --board-on:#0f131a; --power:#e48c50; --gnd:#8592a8; --can:#5b9bff; --can2:#3a5f9e;
  --led:#f2b630; --led-ink:#f2b630; --sense:#b38af4; --gold:#c9a640; --clip:#3a4456; --diffuser:#232b38;
  --stage:#0a0d13; --stage-hex:#161c28; --key:#e6eaf1; color-scheme:dark; }

*{box-sizing:border-box}
body{background:var(--bg); color:var(--ink); font-family:var(--body); font-size:16px; line-height:1.6;
  padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); padding-block:0}
main{max-width:1040px; margin:0 auto; padding-block:48px 80px; display:flex; flex-direction:column; gap:64px}
header{display:flex; flex-direction:column; gap:14px; max-width:68ch}
.eyebrow{font-family:var(--mono); font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted)}
h1{font-family:var(--display); font-weight:600; font-size:clamp(32px, 5vw, 48px); line-height:1.08; margin:0; text-wrap:balance; letter-spacing:-.01em}
h2{font-family:var(--display); font-weight:600; font-size:24px; line-height:1.2; margin:0; text-wrap:balance}
p{margin:0}
.lede{font-size:18px; color:var(--muted)}
section{display:flex; flex-direction:column; gap:16px}
section > p, .prose{max-width:68ch}
.num{font-family:var(--mono); font-size:13px; color:var(--muted); letter-spacing:.04em}
.legend{display:flex; flex-wrap:wrap; gap:8px 20px; font-size:14px; color:var(--muted)}
.legend span{display:inline-flex; align-items:center; gap:8px}
.legend i{display:inline-block; width:22px; height:4px; border-radius:2px}
.lg-power{background:var(--power)} .lg-can{background:var(--can)} .lg-led{background:var(--led)} .lg-sense{background:var(--sense)}
.lg-wifi{background:repeating-linear-gradient(90deg, var(--muted) 0 5px, transparent 5px 9px)}
.parts{display:grid; grid-template-columns:repeat(auto-fill, minmax(230px, 1fr)); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:8px; overflow:hidden}
.parts div{background:var(--surface); padding:14px 16px; display:flex; flex-direction:column; gap:4px; min-width:0}
.parts b{font-family:var(--display); font-weight:600; font-size:15px}
.parts span{font-size:14px; color:var(--muted); line-height:1.45}
figure{margin:0; display:flex; flex-direction:column; gap:10px}
.fig-scroll{overflow-x:auto; background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:12px}
.fig-scroll svg{display:block; width:100%; min-width:700px; height:auto}
figcaption{font-size:14px; color:var(--muted); max-width:75ch}
.step-wrap{display:grid; grid-template-columns:minmax(0, 1.25fr) minmax(0, 1fr); gap:16px; align-items:start}
.step-wrap .fig-scroll svg{min-width:420px}
@media (max-width:760px){ .step-wrap{grid-template-columns:1fr} }
.step-panel{background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:16px; display:flex; flex-direction:column; gap:12px; min-width:0}
.step-turn{font-family:var(--display); font-weight:600; font-size:17px}
.step-desc{font-size:14px; color:var(--muted)}
.controls{display:flex; gap:8px; flex-wrap:wrap}
button{font:500 14px/1 var(--body); color:var(--ink); background:var(--surface-2); border:1px solid var(--line); border-radius:6px; padding:9px 14px; cursor:pointer}
button:hover{border-color:var(--muted)}
button:focus-visible{outline:2px solid var(--can); outline-offset:2px}
button.primary{background:var(--key); color:var(--bg); border-color:var(--key)}
table{border-collapse:collapse; width:100%; font-family:var(--mono); font-size:13px; font-variant-numeric:tabular-nums}
th{font:500 11px var(--mono); text-transform:uppercase; letter-spacing:.08em; color:var(--muted); text-align:left; padding:6px 4px; border-bottom:1px solid var(--line)}
td{padding:6px 4px; border-bottom:1px solid var(--line)}
td.unk{color:var(--muted)}
tr.done td.st{color:var(--can)}
.render-bar{display:flex; gap:12px; align-items:center; flex-wrap:wrap}

/* svg */
svg text{font-family:var(--mono); font-size:12px; fill:var(--ink)}
svg .t-title{font-family:var(--display); font-size:15px; font-weight:600}
svg .t-sm{font-size:12px} svg .t-xs{font-size:10.5px}
svg .t-muted{fill:var(--muted)} svg .t-strong{font-weight:600}
svg .t-led{fill:var(--led-ink)} svg .t-can{fill:var(--can)} svg .t-power{fill:var(--power)} svg .t-sense{fill:var(--sense)}
svg .t-chip{fill:var(--bg); font-weight:600}
svg .t-body-on{fill:var(--board-on); font-size:12.5px; font-weight:500}
svg .t-hexid{font-family:var(--display); font-size:22px; font-weight:600}
svg .t-note{fill:var(--sense); font-weight:600}
svg .t-stage{fill:var(--stage-ink)} svg .t-stage-muted{fill:var(--stage-muted)}
.box{fill:var(--surface); stroke:var(--ink); stroke-width:1.25}
.box-key{stroke-width:2.25}
.w-ink{stroke:var(--ink); stroke-width:1.5; fill:none}
.w-leader{stroke:var(--muted); stroke-width:1; fill:none}
.w-wifi{stroke:var(--muted); stroke-width:1.5; stroke-dasharray:6 5; fill:none}
.w-can{stroke:var(--can); stroke-width:3; fill:none}
.w-power{stroke:var(--power); stroke-width:3; fill:none}
.w-sense{stroke:var(--sense); stroke-width:2.5; fill:none}
.w-led-dash{stroke:var(--led); stroke-width:2; stroke-dasharray:7 5; fill:none}
.arrow-sense{stroke:var(--sense); stroke-width:2; fill:none}
.mk-ink{fill:var(--ink)} .mk-led{fill:var(--led)} .mk-can{fill:var(--can)} .mk-muted{fill:var(--muted)} .mk-sense{fill:var(--sense)}
.dot-ink{fill:var(--ink)} .dot-can{fill:var(--can)}
.hex{fill:var(--surface-2); stroke:var(--board); stroke-width:1.25}
.hex-face{fill:var(--surface-2); stroke:none}
.edge-active-sm{stroke:var(--led); stroke-width:4; stroke-linecap:round}
.board{stroke:var(--board); stroke-width:12; stroke-linecap:butt}
.board-active{stroke:var(--led)}
.led{fill:var(--led)}
.chip{fill:var(--ink)}
.corner{fill:var(--surface); stroke:var(--ink); stroke-width:2}
.rule{stroke:var(--line); stroke-width:1}
.sw-power{fill:var(--power)} .sw-gnd{fill:var(--gnd)} .sw-led{fill:var(--led)} .sw-can{fill:var(--can)} .sw-can2{fill:var(--can2)}
.sw-sense{fill:var(--sense)} .sw-drive{fill:var(--surface); stroke:var(--sense); stroke-width:2.5}
.pcb-body{fill:var(--board)}
.mate{stroke:var(--line); stroke-width:1.5}
.mate-cross{stroke:var(--sense); stroke-width:3}
.label-bg{fill:var(--surface)}
.wall{fill:var(--line)}
.diffuser{fill:var(--diffuser); stroke:var(--muted); stroke-width:1}
.ray{stroke:var(--led); stroke-width:1.25; opacity:.55}
.pcb{fill:var(--board)}
.finger{fill:var(--gold)}
.copper{fill:var(--power)}
.clip{fill:var(--clip); stroke:var(--muted); stroke-width:1}
.spring{stroke:var(--power); stroke-width:2; fill:none}
.seam{stroke:var(--muted); stroke-width:1; stroke-dasharray:3 4}
.sedge{stroke:var(--board); stroke-width:6; stroke-linecap:round; transition:stroke .2s}
.sedge-active{stroke:var(--led)}
.sedge.drive{stroke:var(--sense)}
.sedge.heard{stroke:var(--sense); stroke-width:9}
.hex.driver{fill:color-mix(in srgb, var(--sense) 16%, var(--surface-2))}
.stage{fill:var(--stage)}
.hex-stage{fill:var(--stage-hex); stroke:#2a3346; stroke-width:1}
.msg{fill:none; stroke:var(--stage-muted); stroke-width:1; stroke-dasharray:4 4}
.stage-gap{stroke:var(--stage-muted); stroke-width:1; stroke-dasharray:3 6}
.panel-box{fill:var(--surface-2); stroke:var(--board); stroke-width:1.25}
.bridge{fill:var(--ink)}
.bridge-iso{fill:var(--surface); stroke:var(--ink); stroke-width:1.5; stroke-dasharray:3 2}
.fuse{fill:var(--surface); stroke:var(--power); stroke-width:2}
@media (prefers-reduced-motion: reduce){ .sedge{transition:none} }

/* added: status tiers, AR symbols, flow map, cost chart, gap + commercial sections */
:root{ --crit:#b8322a; --warn:#9a5b00; --info:#2463d1; --sym-r:#e5484d; --sym-g:#2f9e62; --sym-b:#3e63dd; --sym-w:#f4f4f0 }
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ --crit:#ff7466; --warn:#f0a43a; --info:#5b9bff } }
:root[data-theme="dark"]{ --crit:#ff7466; --warn:#f0a43a; --info:#5b9bff }
nav.toc{display:flex; flex-wrap:wrap; gap:6px 16px; font-size:14px}
nav.toc a{color:var(--muted); text-decoration:none; border-bottom:1px solid var(--line)}
nav.toc a:hover{color:var(--ink); border-color:var(--ink)}
.sym-r{fill:var(--sym-r)} .sym-g{fill:var(--sym-g)} .sym-b{fill:var(--sym-b)}
.sym-off{fill:none; stroke:var(--muted); stroke-width:1.25; stroke-dasharray:3 2}
.sym-w{fill:var(--sym-w); stroke:var(--ink); stroke-width:1.25}
.floor{fill:var(--surface-2)}
.wallcell{fill:var(--ink)}
.cell{fill:var(--led)}
.pmark{fill:var(--board); stroke:var(--surface); stroke-width:1}
.pmark.lit{fill:var(--led); stroke:var(--ink); stroke-width:1.5}
.src{fill:var(--sense); stroke:var(--surface); stroke-width:2}
.grid{stroke:var(--line); stroke-width:1}
.rbar{fill:var(--can)}
.hit{fill:transparent}
.rrow:hover .rbar{fill:var(--ink)}
.rrow:hover text{fill:var(--ink)}
.facts{display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px}
.fact{background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:14px 16px; display:flex; flex-direction:column; gap:2px; min-width:0}
.fact b{font-family:var(--display); font-size:26px; font-weight:600; font-variant-numeric:tabular-nums}
.fact span{font-size:13px; color:var(--muted)}
.tier{display:flex; flex-direction:column; gap:12px}
.tier-head{display:flex; align-items:baseline; gap:12px; flex-wrap:wrap}
.tier-head h3{font-family:var(--display); font-size:18px; margin:0}
.chip{font:600 11px var(--mono); letter-spacing:.06em; text-transform:uppercase; padding:3px 8px; border-radius:999px; border:1.5px solid currentColor}
.chip-a{color:var(--crit)} .chip-b{color:var(--warn)} .chip-c{color:var(--info)}
.gaps{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:12px}
.gap{background:var(--surface); border:1px solid var(--line); border-left:4px solid var(--stripe, var(--line)); border-radius:6px; padding:14px 16px; display:flex; flex-direction:column; gap:8px; min-width:0}
.tier-a .gap{--stripe:var(--crit)} .tier-b .gap{--stripe:var(--warn)} .tier-c .gap{--stripe:var(--info)}
.gap h4{margin:0; font-family:var(--display); font-size:16px; font-weight:600}
.gap p{font-size:14px; color:var(--muted); line-height:1.5}
.gap p b{color:var(--ink); font-weight:600}
.tbl-wrap{overflow-x:auto; background:var(--surface); border:1px solid var(--line); border-radius:8px}
.tbl-wrap table{font-family:var(--body); font-size:14px}
.tbl-wrap th, .tbl-wrap td{padding:10px 14px; vertical-align:top}
.tbl-wrap td.num{font-family:var(--mono); text-align:right; white-space:nowrap}
.tbl-wrap tr.total td{font-weight:600; border-bottom:none}
details{font-size:14px}
details summary{cursor:pointer; color:var(--muted)}
details[open] summary{margin-bottom:10px}
ul.plain{margin:0; padding-left:20px; display:flex; flex-direction:column; gap:6px; max-width:75ch}
.gallery{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:20px; margin-top:8px}
.gallery figure.wide{grid-column:1 / -1}
.gallery img{width:100%; height:auto; display:block; border:1px solid var(--line); border-radius:8px; background:#f8f8f8}
.gallery .src{display:block; font-size:12px; opacity:.75; font-family:ui-monospace, monospace; margin-top:2px}
.gallery video{width:100%; height:auto; display:block; border:1px solid var(--line); border-radius:8px; background:#000}
.gallery img.alpha{background:transparent; border:none}
.cols{display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:16px}
.cols > div{min-width:0; display:flex; flex-direction:column; gap:8px}
h3.sub{font-family:var(--display); font-size:18px; margin:0}
.encl{fill:none; stroke:var(--muted); stroke-width:1.25; stroke-dasharray:5 4}
.bpcb{fill:var(--board)}
.bpcb-band{fill:var(--surface-2); stroke:var(--board); stroke-width:1.25}
.socket{fill:var(--ink)}
.slot{fill:var(--surface)}
.contact{fill:var(--power)}
.sw-spare{fill:none; stroke:var(--muted); stroke-width:1.25; stroke-dasharray:3 2}
.spring-sig{stroke:var(--can); stroke-width:2; fill:none}
.diode{fill:var(--sense)}
.route{stroke:var(--muted); stroke-width:1.5}
.ghost{fill:none; stroke:var(--muted); stroke-width:1.25; stroke-dasharray:4 3}
.whitemask{fill:#f7f7f2; stroke:var(--board); stroke-width:1}
.whitemask-box{fill:#f7f7f2; stroke:var(--board); stroke-width:1.5}
.whitemask-box + text, .t-on-white{fill:#17202e}
.bead-row{fill:var(--gold)}
.bclip{fill:var(--can2); stroke:var(--can); stroke-width:1.25}
.print{fill:var(--clip); stroke:var(--muted); stroke-width:1}
.ring{fill:none; stroke:var(--board); stroke-width:3}
.gapfill{fill:var(--surface)}
.dim{stroke:var(--muted); stroke-width:1; fill:none}
.hatch{fill:none; stroke:var(--muted); stroke-width:1; stroke-dasharray:2 3}
.floorline{stroke:var(--board-on); stroke-width:1; stroke-dasharray:4 3}
.boardline-thin{stroke:var(--board); stroke-width:5; stroke-linecap:round}
.lane5v{stroke:var(--power); stroke-opacity:.6; stroke-width:16; fill:none}
.thin{stroke-width:2}
section.proposal{border:2px dashed var(--warn); border-radius:10px; padding:20px; padding-left:max(20px, env(safe-area-inset-left, 0px))}
.sw-5v{fill:var(--power); opacity:.6}
.seamline{fill:none; stroke:var(--muted); stroke-width:1.25; stroke-dasharray:5 4}
.boardline{fill:var(--surface-2); stroke:var(--board); stroke-width:5}
.rbar-ours{fill:var(--led)}
.mid-dot{fill:var(--ink); stroke:var(--surface); stroke-width:2}
.rrow:hover .rbar-ours{fill:var(--ink)}
.plane{fill:var(--power); opacity:.25}
.via{fill:var(--surface); stroke:var(--board-on); stroke-width:1.5}
.zone{fill:none; stroke:var(--board-on); stroke-width:1.25; stroke-dasharray:4 3}
.chip-on{fill:var(--board-on); opacity:.55}
.bead{fill:var(--gold); stroke:var(--ink); stroke-width:1}
.strap{stroke:var(--power); stroke-width:4; fill:none; stroke-linecap:round}
.seg-b2{fill:var(--can2)} .seg-f{fill:none; stroke:var(--muted); stroke-width:1.25; stroke-dasharray:3 2}
.view{display:flex; flex-direction:column; gap:64px}
.view[hidden]{display:none !important}
.view > .lede{margin-bottom:-40px}
nav.tabs{display:flex; gap:4px; border-bottom:1px solid var(--line); flex-wrap:wrap}
nav.tabs a{font-family:var(--display); font-weight:600; font-size:17px; color:var(--muted); text-decoration:none; padding:10px 16px; border-bottom:3px solid transparent; margin-bottom:-1px}
nav.tabs a:hover{color:var(--ink)}
nav.tabs a[aria-current="page"]{color:var(--ink); border-bottom-color:var(--ink)}
nav.tabs a:focus-visible{outline:2px solid var(--can); outline-offset:2px}
main a{color:var(--can)}
nav.toc a, nav.tabs a{color:var(--muted)}
nav.tabs a[aria-current="page"]{color:var(--ink)}
pre.code{margin:0; font-family:var(--mono); font-size:12.5px; line-height:1.55; background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:14px 16px; overflow-x:auto; max-width:100%}
ol.plain{margin:0; padding-left:22px; display:flex; flex-direction:column; gap:6px; max-width:75ch}
.seg-a{fill:var(--board)} .seg-b{fill:var(--can)} .seg-c{fill:var(--led)} .seg-d{fill:var(--sense)} .seg-e{fill:var(--muted)}
.compute{fill:var(--surface-2); stroke:var(--board); stroke-width:1}
.shown{fill:var(--led); opacity:.35}
.latch{stroke:var(--ink); stroke-width:1.5; stroke-dasharray:4 3}
.svc{fill:var(--surface-2); stroke:var(--board); stroke-width:1}
.w-led-solid{stroke:var(--led); stroke-width:2.5; fill:none}
"""

PARTS = [
    ("Edge board", "One straight passive PCB, one side of a panel: LEDs, ID circuit, contacts and lanes. All are identical; only the length depends on the panel shape."),
    ("Controller board", "A small 4-layer board at the rear of each panel: MCU, CAN transceiver, 24 → 5 V converter, LED switch, 3.3 V regulator. Drag-soldered to the code-0 edge board."),
    ("Panel", "A closed polygon of edge boards behind a thin diffuser film. Edges are ≈100 mm."),
    ("Corner connection", "The internal joint between two edge boards at a panel corner."),
    ("Edge contacts", "Ten plated pads on each board's exterior face, along the wall edge: power and signals."),
    ("Bridge", "A thin PCB standing upright in the seam, with $0.02 springs on both faces pressing on two panels' edge contacts. A 3D-printed carrier holds it to the wall."),
    ("Cluster", "Panels joined by bridges on one flat surface, sharing one CAN bus."),
    ("Cluster controller", "Snap-on ESP32 per cluster. Runs the CAN bus and talks Wi-Fi."),
    ("Coordinator", "The system brain. Holds the room layout and schedules effects in room space."),
]


GAPS = {
    "a": ("Tier A", "Could force a redesign: prototype before ordering custom boards", [
        ("Optics are unproven", "With only 2–3 LEDs per edge shining across an air gap, a thin diffuser film is likely to show a bright spot near each LED and a dimmer centre. Film spreads light less than thick opal acrylic. Panel depth, LED aim, back reflectance and film choice are all open.",
         "A test box with a 100 mm-edge hexagon and cut 5 V SK6812 RGBW strip: 15 / 25 / 35 mm depth, white matte vs. foil back, LEDs aimed across vs. at the back, and one vs. two film layers."),
        ("Seam bridge and carrier", "The bridge is a thin PCB standing in the seam, with 20 low-cost LCSC top-contact springs (BW0019 series, ≈$0.02) pressing on pads on each panel's exterior face, held by a printed carrier. Unproven: the springs' current rating and force (not yet confirmed from the datasheet), whether a panel slides in without snagging them, seam width, carrier retention, and tolerance to a few mm of wall unevenness.",
         "Prototype the bridge and carrier. Measure contact resistance, current per spring, insertion and seam width. The Harwin flat bridge (decision 0001) is the fallback."),
        ("Corner joints are a large hand job", "100 hexagons need about 4,800 corner joints. The pads are all SMD now (signals on the inward face, power on the exterior face), but they are still joined by hand with solder beads and a bent strap across each outside corner. With 100 mm panels a wall needs about 2.25× as many panels as with 150 mm ones, so the joint count per wall goes up too. Corner angles differ by shape, and each board needs its own ID resistor.",
         "Cut the nets that cross corners, use solder-bead castellations or a corner jumper PCB per shape, and panelize a \"hex kit\" with ID codes 0–5 pre-assembled."),
        ("Standby power", "With only 12–18 LEDs per panel, idle draw is now mostly the MCU and CAN transceiver: about 0.3–0.5 W per panel, or 30–50 W for 100 panels with the lights off.",
         "Sleep the MCU, put the CAN transceiver in standby with wake on bus activity, and switch the LED rail off with the controller board's P-MOSFET; or switch whole domains off at the supply."),
        ("Printing logistics", "Bed size is solved: a 100 mm-edge hexagon is 200 mm across its corners and fits common 220–256 mm beds in one piece. Print time is still large, roughly 1–2 h per panel, or 100–450 printer-hours for 100–225 panels. PETG is not flame-retardant.",
         "Print several frames per plate and budget the printer time."),
        ("Mounting, especially ceilings", "The spec has no mounting method. Ceiling panels need positive retention, walls are not flat, and a panel in the middle of a cluster must be removable for repair.",
         "Design a mounting plate that also takes the bridge insertion force."),
    ]),
    "b": ("Tier B", "Spec decisions to make before schematic capture", [
        ("Panel shape: auto-detect or setting", "One firmware image serves every shape. The last LED's data output loops back to the MCU, so firmware can count its own LEDs and work out the edge count; a stored setting is the alternative. No strap resistor.",
         "Route the last LED's output back to a 5 V-tolerant timer-capture pin through a series resistor. Later, decide whether auto-detect or the stored setting is primary."),
        ("Exposed contacts need protection", "Bare pads get touched (ESD), hot-plugging charges the LED and bulk capacitors through the springs, and a board sliding in can briefly touch the wrong spring.",
         "Staggered pad heights (GND first) stay. Decision 0011 makes every bus line survive a sustained 24 V short: TCAN1044V (±58 V), NUP3105 CAN TVS, 10 k SENSE resistor, open-drain DRIVE through 470 Ω, TLV431 3V3 clamp, and a per-panel PTC. Verify on the prototype."),
        ("CAN loops and termination", "Three hexagons meeting at a vertex close a loop in the bus, and the electrically farthest node isn't known until after discovery.",
         "Run a 10–20 node loop test at 125 / 250 / 500 kbps. Consider MCU-switchable split termination."),
        ("RGBW dim levels and flicker", "RGBW is decided (SKC6812RGBW, neutral white). Still open: 8-bit PWM bands at night-time brightness, and the PWM frequency for camera and phone flicker.",
         "Plan temporal dithering in node firmware. Measure low-level dimming and flicker in the optics test."),
        ("AR app platform", "iPhone Safari has no WebXR AR, so an iPhone needs a native ARKit app (a Mac with Xcode). RoomPlan needs a LiDAR iPhone. Android ARCore is easier.",
         "Pick the scanning phone. Build a manual-placement fallback in the coordinator UI."),
        ("Flash safety", "AR codes and some effects flash. Rapid high-contrast or saturated-red flashing can trigger photosensitive seizures.",
         "Keep AR codes at low brightness with near-equal-luminance colour steps, at most about 3 changes per second. Cap flash rates in the effect engine and add a calm mode."),
        ("Programming and test", "100+ MCUs need a first flash, and every board should be tested before it is glued into a panel.",
         "SWD pads, a pogo-pin jig with a WCH-LinkE, an LED and ID test fixture, and about 5% spare boards."),
        ("Discovery robustness", "LED PWM currents add noise on GND, and a half-seated bridge reads between valid codes.",
         "Discover with LEDs off, average many samples, reject between-band readings, and re-run when the node count changes."),
        ("Missing target numbers", "Brightness, maximum power per panel, board height (panel depth), contact-pad position, weight, frame rate, latency, maximum cluster size and boot time are all unset.",
         "Set them once the optics test is done."),
    ]),
    "c": ("Tier C", "Software and project planning", [
        ("Build the simulator first", "Layouts, discovery, the CAN protocol and effects can all be developed before hardware exists.",
         "The simulator later becomes the coordinator UI's preview."),
        ("Write the CAN protocol down", "Message IDs, enumeration, discovery, time sync, frame latch, effect descriptors and the bootloader are shared by nodes and controllers.",
         "Keep it in firmware/common/protocol/."),
        ("Firmware lockstep", "Every node in a cluster must run a compatible effect library.",
         "Add a version handshake; the controller refuses effects on mismatched nodes."),
        ("Coordinator choices", "The host (Pi or ESP32), integrations (Home Assistant, MQTT) and effect authoring (built-in library or scripting) are undecided.",
         "Decide alongside the simulator work."),
        ("Provisioning and OTA", "Several controllers need Wi-Fi setup, and both controllers and nodes need safe updates.",
         "Signed updates with rollback."),
        ("Phasing", "Ordering 100+ panels before the risky parts are proven wastes money.",
         "Phase 0 prototypes (optics, bridge, corners, CAN loops), then one bench kit, a 5–10 panel cluster, multi-cluster with AR, and only then volume."),
    ]),
}

COMMERCIAL_CHANGES = [
    ("Enclosure", "3D-printed PETG", "Injection-moulded PC or PC/ABS rated UL94 V-0. Tooling is roughly $15–60k per part family."),
    ("Assembly", "Hand-soldered corner joints", "No hand soldering: a one-piece ring PCB, board-to-board connectors, or a moulded frame that captures the boards."),
    ("Diffuser", "LCD-style diffuser film in a printed frame", "Film held in a moulded frame, or a moulded diffuser."),
    ("Panel connections", "Seam bridge PCB with $0.02 LCSC springs in a printed carrier", "Same approach with a moulded carrier and springs qualified for mating cycles."),
    ("Power", "24 V bench supplies, user-wired", "Listed plug-in adapters. In the US, Class 2 limits each circuit to about 100 W, so domains are sized to that."),
    ("Standby", "≈0.3–0.5 W per panel idle", "EU standby limits (roughly 0.5 W, or about 2 W networked) apply to the product, so per-panel sleep and supply gating are required."),
    ("LED count", "2–3 per edge", "Same, once the optics test confirms it."),
    ("Setup", "AR scan by the builder", "Guided app onboarding that works without AR (one surface) and improves with it."),
    ("Updates", "Personal OTA over CAN", "Signed OTA, rollback, staged rollouts, and security updates for a stated support period."),
]

CERTS = [
    ("FCC Part 15B (US)", "Panels and controller", "Unintentional emissions. Fast LED data edges and CAN must pass."),
    ("FCC 15C / EU RED (radio)", "Controller", "Use a pre-certified ESP32 module so the product inherits its radio grant."),
    ("CE: EMC, RED, RoHS, REACH, WEEE (EU)", "Whole system", "Declaration of conformity and a technical file. 24 V is below the Low Voltage Directive, but the adapter is not."),
    ("UL / ETL safety listing", "Panels and supply", "Most retailers require it. Flame-rated plastics and a listed supply."),
    ("IEC 62471 photobiological safety", "Panels", "Blue-light hazard classification."),
    ("Energy rules", "System and adapter", "EU Ecodesign standby and networked standby; US DoE adapter efficiency."),
    ("Cybersecurity", "Controller and app", "UK PSTI (in force), EU Cyber Resilience Act (phasing in), US Cyber Trust Mark (voluntary). No default passwords, a disclosure policy, secure updates."),
    ("Matter (optional)", "Controller", "Expected by smart-home buyers. Alliance membership and test fees apply."),
]


def gap_html():
    out = []
    for key in ("a", "b", "c"):
        label, desc, items = GAPS[key]
        cards = "".join(f'<article class="gap"><h4>{t}</h4><p>{p}</p><p><b>Next step:</b> {nx}</p></article>' for t, p, nx in items)
        out.append(f'<div class="tier tier-{key}"><div class="tier-head"><span class="chip chip-{key}">{label}</span><h3>{desc}</h3></div><div class="gaps">{cards}</div></div>')
    return "".join(out)


def build():
    stepper_svg, stepper = fig_stepper()
    render_svg, leds = fig_render()
    flow_svg, flow_d, flow_p, flow_max = fig_flow()
    cost_rows = "".join(f'<tr><td>{a}</td><td class="num">${lo:.2f}</td><td class="num">${hi:.2f}</td><td>{b}</td></tr>' for a, lo, hi, b in HEX_COST)
    lo_sum = sum(r[1] for r in HEX_COST)
    hi_sum = sum(r[2] for r in HEX_COST)
    change_rows = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in COMMERCIAL_CHANGES)
    cert_rows = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in CERTS)
    nvolts = [round(v, 2) for v in VOLTS]
    parts = "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in PARTS)
    js = """
(function(){
  const P = __STEP__;
  const V = __VOLTS__;
  const byId = Object.fromEntries(P.map(p => [p.id, p]));
  // every physical link, listed once
  const links = [];
  P.forEach(p => Object.entries(p.nb).forEach(([e, [q, eq]]) => {
    if (p.id < q) links.push({a: p.id, ea: +e, b: q, eb: eq});
  }));
  const order = P.map(p => p.id);
  let turn = 0;
  const $ = id => document.getElementById(id);
  function render(){
    const d = P[turn];
    P.forEach(p => {
      $('hx-' + p.id).classList.toggle('driver', p.id === d.id);
      for (let e = 0; e < 6; e++){
        const el = $('ed-' + p.id + '-' + e);
        el.classList.remove('drive', 'heard');
        if (p.id === d.id) el.classList.add('drive');
      }
      $('nt-' + p.id).textContent = p.id === d.id ? 'DRIVE low' : '';
    });
    Object.entries(d.nb).forEach(([e, [q, eq]]) => {
      const code = byId[q].codes[eq];
      $('ed-' + q + '-' + eq).classList.add('heard');
      $('nt-' + q).textContent = V[code].toFixed(2) + ' V → edge ' + code;
    });
    $('step-turn').textContent = 'Turn ' + (turn + 1) + ' of ' + P.length + ': panel ' + d.id + ' drives';
    const heard = Object.values(d.nb).map(([q, eq]) => q + ' (edge ' + byId[q].codes[eq] + ')');
    $('step-desc').textContent = 'Panel ' + d.id + ' pulls DRIVE low on all its edges. ' +
      (heard.length ? heard.join(', ') + ' heard it and report which of their own edges faces ' + d.id + '.' : 'No neighbours heard it.');
    const known = id => order.indexOf(id) <= turn;   // a half is learned on the OTHER panel's turn
    const rows = links.map(l => {
      const ha = known(l.b), hb = known(l.a);
      const ca = byId[l.a].codes[l.ea], cb = byId[l.b].codes[l.eb];
      const done = ha && hb;
      return '<tr class="' + (done ? 'done' : '') + '"><td>' + l.a + '</td><td class="' + (ha ? '' : 'unk') + '">' + (ha ? 'edge ' + ca : '?') +
        '</td><td>↔</td><td>' + l.b + '</td><td class="' + (hb ? '' : 'unk') + '">' + (hb ? 'edge ' + cb : '?') +
        '</td><td class="st">' + (done ? 'known' : '') + '</td></tr>';
    }).join('');
    $('step-rows').innerHTML = rows;
    $('step-prev').disabled = turn === 0;
    $('step-next').textContent = turn === P.length - 1 ? 'Start over' : 'Next turn';
  }
  $('step-next').addEventListener('click', () => { turn = (turn + 1) % P.length; render(); });
  $('step-prev').addEventListener('click', () => { if (turn > 0) { turn--; render(); } });
  render();

  // rendering animation
  const L = __LEDS__;
  const PAL = __PAL__;
  const W = __WAVE__;
  const px = document.querySelectorAll('#render-svg .px');
  function pal(v){
    v = Math.max(0, Math.min(1, v)) * (PAL.length - 1);
    const i = Math.min(Math.floor(v), PAL.length - 2), t = v - i, a = PAL[i], b = PAL[i + 1];
    return 'rgb(' + [0,1,2].map(k => Math.round(a[k] + (b[k] - a[k]) * t)).join(',') + ')';
  }
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let playing = !reduce, t0 = performance.now(), tPause = 0, raf = 0;
  const btn = $('render-toggle');
  const rview = document.getElementById('render-svg').closest('.view');
  function frame(now){
    const t = (now - t0) / 1000;
    if (rview.getClientRects().length) for (let i = 0; i < L.length; i++){
      const v = 0.5 + 0.5 * Math.sin(W.w * t - (W.kx * L[i][0] + W.ky * L[i][1]));
      px[i].setAttribute('fill', pal(v));
    }
    if (playing) raf = requestAnimationFrame(frame);
  }
  function sync(){ btn.textContent = playing ? 'Pause' : 'Play'; btn.setAttribute('aria-pressed', String(!playing)); }
  btn.addEventListener('click', () => {
    playing = !playing;
    if (playing){ t0 = performance.now() - tPause * 1000; raf = requestAnimationFrame(frame); }
    else { tPause = (performance.now() - t0) / 1000; cancelAnimationFrame(raf); }
    sync();
  });
  sync();
  if (playing) raf = requestAnimationFrame(frame);

  // flow between rooms
  const FD = __FLOWD__, FP = __FLOWP__, FMAX = __FLOWMAX__;
  const cells = document.querySelectorAll('#flow-svg .cell');
  const pms = document.querySelectorAll('#flow-svg .pmark');
  const TAIL = 7, SPEED = 12, SPAN = FMAX + TAIL + 12;
  let fPlay = !reduce, fOff = 30 / SPEED * 1000, fStart = performance.now() - fOff, fPaused = 0, fRaf = 0, last = 0;
  const fbtn = $('flow-toggle');
  const fview = document.getElementById('flow-svg').closest('.view');
  function fframe(now){
    if (now - last > 33 && fview.getClientRects().length){
      last = now;
      const front = ((now - fStart) / 1000 * SPEED) % SPAN;
      for (let i = 0; i < cells.length; i++){
        const d = front - FD[i];
        cells[i].setAttribute('fill-opacity', d >= 0 && d < TAIL ? ((1 - d / TAIL) * 0.85).toFixed(2) : '0');
      }
      for (let i = 0; i < pms.length; i++){
        const d = front - FP[i];
        pms[i].classList.toggle('lit', d >= 0 && d < TAIL * 1.5);
      }
    }
    if (fPlay) fRaf = requestAnimationFrame(fframe);
  }
  function fsync(){ fbtn.textContent = fPlay ? 'Pause' : 'Play'; fbtn.setAttribute('aria-pressed', String(!fPlay)); }
  fbtn.addEventListener('click', () => {
    fPlay = !fPlay;
    if (fPlay){ fStart = performance.now() - fPaused; fRaf = requestAnimationFrame(fframe); }
    else { fPaused = performance.now() - fStart; cancelAnimationFrame(fRaf); }
    fsync();
  });
  fsync();
  if (fPlay) fRaf = requestAnimationFrame(fframe);
})();
"""
    js = (js.replace("__FLOWD__", json.dumps(flow_d))
            .replace("__FLOWP__", json.dumps(flow_p))
            .replace("__FLOWMAX__", json.dumps(flow_max))
            .replace("__STEP__", json.dumps(stepper))
            .replace("__VOLTS__", json.dumps(nvolts))
            .replace("__LEDS__", json.dumps(leds))
            .replace("__PAL__", json.dumps(PALETTE))
            .replace("__WAVE__", json.dumps(WAVE)))

    old = f"""<title>Modular Smart Light Panels</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Space+Grotesk:wght@500;600&display=swap">
<style>{CSS}</style>
<main>
<header>
  <div class="eyebrow">System explainer · spec V6.5</div>
  <h1>Modular Smart Light Panels</h1>
  <p class="lede">Edge-lit panels that snap together in any layout, work out their own arrangement, and play effects that are placed in the room rather than along a strip. This page walks from the whole system down to a single wire.</p>
  <div class="legend" aria-label="Colour key used in every diagram">
    <span><i class="lg-power"></i>+24V power</span>
    <span><i class="lg-can"></i>CAN bus</span>
    <span><i class="lg-led"></i>LEDs and LED data</span>
    <span><i class="lg-sense"></i>SENSE / DRIVE ID lines</span>
    <span><i class="lg-wifi"></i>Wi-Fi</span>
  </div>
  <nav class="toc" aria-label="Sections">
    <a href="#s1">System</a><a href="#s2">Panel</a><a href="#s3">Seam</a><a href="#s4">Connector</a><a href="#s5">Discovery</a>
    <a href="#s6">Rendering</a><a href="#s8">AR placement</a><a href="#s9">Between rooms</a><a href="#s7">Power</a>
    <a href="#s10">Cost</a><a href="#s11">Gaps</a><a href="#s12">Commercial</a>
  </nav>
</header>

<section aria-labelledby="s-parts">
  <h2 id="s-parts">The parts</h2>
  <div class="parts">{parts}</div>
</section>

<section aria-labelledby="s1">
  <div class="num">1 · Whole system</div>
  <h2 id="s1">Three layers: coordinator, cluster controllers, panels</h2>
  <p>Each flat surface is its own cluster with its own ESP32 controller and CAN bus. Clusters never connect electrically. The coordinator ties them together over Wi-Fi, and the AR app tells it where each cluster sits in the room.</p>
  <figure>
    <div class="fig-scroll">{fig_system()}</div>
    <figcaption>Effects go down from the coordinator; discovered topology goes up. The amber edge on each hexagon is that panel's code-0 edge, where its rear controller board joins.</figcaption>
  </figure>
</section>

<section aria-labelledby="s2">
  <div class="num">2 · One panel</div>
  <h2 id="s2">Six identical boards, a controller behind them</h2>
  <p>A hexagon is six copies of the same passive edge board. They carry the LEDs and pass power, CAN and the ID lines around the corners. The controller board sits at the rear of the chamber and joins the code-0 board. Each board's ID resistor gives it a number, counted clockwise from the code-0 board.</p>
  <figure>
    <div class="fig-scroll">{fig_panel()}</div>
    <figcaption>LEDs face inward into an air gap and light the diffuser from the edges. The LED data chain starts at the controller (through the code-0 board), runs through all six boards, and loops back to it across the last corner, so firmware can count its LEDs.</figcaption>
  </figure>
</section>

<section aria-labelledby="s3">
  <div class="num">3 · The seam</div>
  <h2 id="s3">Where two panels meet</h2>
  <p>Neighbouring panels stand back to back. Their exterior faces carry the contact pads and the +24V and GND lanes; other lanes may use either face. Each board's exterior face carries a strip of contact pads along its wall edge. A thin bridge PCB stands upright in the seam between the two boards, with cheap top-contact springs on both of its faces pressing on those pads. A 3D-printed carrier anchors the bridge to the wall and the panels snap onto it, so the springs carry no load. Every part on the bridge is machine-placed.</p>
  <figure>
    <div class="fig-scroll">{fig_seam()}</div>
    <figcaption>One row of springs on each face of the bridge presses on one panel. The rows sit at the same positions, so the bridge is balanced between the two boards; each board is pushed toward its own panel and held by its frame. The seam is about 6–8 mm. No crossover jumpers: the power pads are on the power-plane face itself.</figcaption>
  </figure>
</section>

<section aria-labelledby="s4">
  <div class="num">4 · Edge connector</div>
  <h2 id="s4">The bridge does the cross-wiring</h2>
  <p>All ten contact pads sit on the exterior face, along the wall edge: three GND, two +24V and five signals. Signal nets reach them through vias, and the power planes keep clear of them. The pads stop at different distances from the wall edge, so as a panel slides in GND touches first, then +24V, then the signals. The bridge PCB routes each net with its own traces, including the SENSE ↔ DRIVE cross that discovery needs, and its 180° symmetric layout means it can't be fitted the wrong way round.</p>
  <figure>
    <div class="fig-scroll">{fig_mirror()}</div>
    <figcaption>Pads ≈3 mm wide at ≈5 mm pitch, centred and symmetric so the springs on both faces of the bridge balance. Springs: LCSC BW0019CG-L3.5W1.5H4.3, ≈$0.024 each, 10 per board. The spare pad (X8) is reserved for a switched LED rail. Not to scale; the edge gaps are exaggerated.</figcaption>
  </figure>
</section>

<section aria-labelledby="s5">
  <div class="num">5 · Discovery</div>
  <h2 id="s5">How a panel learns which edge touches which neighbour</h2>
  <p>Each panel has a SENSE bus (pulled up, read by the ADC) and a DRIVE bus (driven by a GPIO). When panel B pulls DRIVE low, current flows only through the one diode and ID resistor on A's edge that touches B. A's reading names that edge. The diode stops a sneak path: without it, current could flow from a reading panel's SENSE bus into an idle neighbour's floating DRIVE bus and on to a third panel, which happens in any group of four hexagons and shifts readings across code thresholds.</p>
  <figure>
    <div class="fig-scroll">{fig_circuit()}</div>
    <figcaption>The diode adds roughly 0.55 V to every reading. The closest codes are about 0.23 V (≈280 ADC counts) apart. These are expected values; the thresholds get calibrated on real hardware. DRIVE is an open-drain MOSFET through 470 Ω, so a 24 V short on the bus is survivable.</figcaption>
  </figure>
  <p>The cluster controller gives every panel a turn. After one round it has the complete map: which edge of every panel faces which edge of its neighbour, regardless of how each panel was rotated when it was mounted.</p>
  <figure>
    <div class="step-wrap">
      <div class="fig-scroll">{stepper_svg}</div>
      <div class="step-panel">
        <div class="step-turn" id="step-turn">Turn 1 of 5</div>
        <p class="step-desc" id="step-desc"></p>
        <div class="controls">
          <button type="button" id="step-prev">Previous</button>
          <button type="button" class="primary" id="step-next">Next turn</button>
        </div>
        <table aria-label="Links discovered so far">
          <thead><tr><th>Panel</th><th>Edge</th><th></th><th>Panel</th><th>Edge</th><th></th></tr></thead>
          <tbody id="step-rows"></tbody>
        </table>
      </div>
    </div>
    <figcaption>Small numbers are each panel's edge codes; the amber edge is code 0, where the controller board joins. Panels are deliberately mounted at different rotations. Each half of a link is learned on the other panel's turn.</figcaption>
  </figure>
</section>

<section aria-labelledby="s6">
  <div class="num">6 · Rendering</div>
  <h2 id="s6">The bus carries a recipe, not pixels</h2>
  <p>Every node knows where each of its LEDs sits in room coordinates. The coordinator broadcasts one short effect description and a shared clock, and every node evaluates it locally. Streaming raw RGBW colour to one 20-panel cluster (360 LEDs) at 30 fps would need about 350 kbps of payload, more than a 250 kbps CAN bus delivers after overhead. The recipe is a few bytes.</p>
  <figure>
    <div class="fig-scroll">{render_svg}</div>
    <div class="render-bar"><button type="button" id="render-toggle" aria-pressed="false">Pause</button>
    <span class="step-desc">Colour = palette( sin(ωt − k·r) ), evaluated per LED at its room position r.</span></div>
    <figcaption>The two clusters share no wiring, only a clock. Because both evaluate the same formula in the same coordinates, the wave crosses the gap unbroken.</figcaption>
  </figure>
</section>

<section aria-labelledby="s8">
  <div class="num">7 · Room placement</div>
  <h2 id="s8">How the phone finds every panel in 3D</h2>
  <p>Discovery already gives the exact shape of each cluster, but not where it sits in the room. The AR app supplies that. The coordinator makes every panel flash a unique colour sequence at the same time, on the shared clock. The phone watches through ARKit, which knows its own position and which way is down on every camera frame.</p>
  <figure>
    <div class="fig-scroll">{fig_ar()}</div>
    <figcaption>Each code is a sync symbol, a 6-symbol panel ID (4,096 possible IDs) and a checksum. The code is spread over time, so one camera view decodes every visible panel at once, and partly hidden panels can be picked up from another angle.</figcaption>
  </figure>
  <div class="cols">
    <div>
      <h3 class="sub">Why a cluster only needs a few panels seen</h3>
      <ul class="plain">
        <li>Discovery already gives the panel positions inside each cluster, in millimetres.</li>
        <li>Three or more decoded panels fix the cluster's 6-DoF pose. Extra panels give a least-squares fit, and a large residual flags a misread code.</li>
        <li>ARKit's world frame is gravity-aligned and metric, so "down" and scale come for free.</li>
        <li>Moving a cluster later means re-scanning only that cluster.</li>
      </ul>
    </div>
    <div>
      <h3 class="sub">Joining rooms into one frame</h3>
      <ul class="plain">
        <li><b>One walk-through:</b> scan room to room in one session. ARKit keeps a single world frame, with small drift that grows with distance.</li>
        <li><b>Per-room scans:</b> save each room's ARWorldMap and join rooms through a shared anchor seen from both sides, such as a cluster visible through the doorway or a marker on the door frame.</li>
        <li><b>RoomPlan</b> (LiDAR iPhones) returns walls, doors and openings. These become the walls and portals of the voxel model in the next section.</li>
        <li>Output: one building frame in metres, stored in the Room Layout JSON.</li>
      </ul>
    </div>
  </div>
  <p class="prose">Flash safety: codes run at about 4 symbols per second at low brightness, using colour steps of similar brightness rather than bright on/off flashes. Section 11 has the details.</p>
</section>

<section aria-labelledby="s9">
  <div class="num">8 · Between rooms</div>
  <h2 id="s9">Voxels let effects travel the way a person would</h2>
  <p>If effects used plain straight-line distance, a ripple starting in room A would light the far side of the shared wall almost immediately, as if the wall weren't there. The coordinator keeps a sparse voxel model of the building, built from RoomPlan walls and doors. It computes distance <i>through free space</i>, so wavefronts bend through doorways and reach the next room in the right order.</p>
  <figure>
    <div class="fig-scroll">{flow_svg}</div>
    <div class="render-bar"><button type="button" id="flow-toggle" aria-pressed="false">Pause</button>
    <span class="step-desc">Same start point, same speed. Watch cluster B1, just behind the wall.</span></div>
    <figcaption>Left: B1 lights while the front is still in room A. Right: the front reaches B1 only after passing through the door. Distances come from a shortest-path search over 20 cm voxels.</figcaption>
  </figure>
  <div class="cols">
    <div>
      <h3 class="sub">Field effects run on the nodes</h3>
      <p class="prose">Waves, gradients and ripples are formulas. For building-scale effects the coordinator precomputes each panel's path distance from a few named sources (front door, each room's centre) and sends it once: a value at the panel centre plus a gradient across the panel. Nodes then evaluate colour = f(distance − speed × t) locally, with no ongoing traffic.</p>
    </div>
    <div>
      <h3 class="sub">Simulated effects run on the coordinator</h3>
      <p class="prose">Smoke, fire, particles bouncing off walls and flocks moving between rooms need state, so the coordinator simulates them on the voxel grid and sends low-resolution samples: one colour per edge, about 20 times a second. 100 hexagons × 6 edges × 4 bytes (RGBW) × 20 Hz is about 385 kbps in total, spread across ~10 clusters, or about 40 kbps per CAN bus.</p>
    </div>
  </div>
</section>

<section aria-labelledby="s7">
  <div class="num">9 · Power</div>
  <h2 id="s7">Power domains keep supplies apart</h2>
  <p>A large install needs several power supplies. Each feeds its own domain through an injection bridge: a bridge PCB variant with a supply input and a fuse. An isolating bridge, a variant whose PCB leaves the +24V traces unconnected, joins domains so CAN and ground stay continuous but the supplies never push current into each other.</p>
  <figure>
    <div class="fig-scroll">{fig_power()}</div>
    <figcaption>The coordinator scales brightness per domain so no supply is asked for more than it can deliver. An 18-LED hexagon at full output draws about 0.73 A on its 5 V rail, or about 0.18 A from the 24 V bus through the buck, so one 100 W supply feeds roughly 23 of them.</figcaption>
  </figure>
</section>

<section aria-labelledby="s10">
  <div class="num">10 · Cost</div>
  <h2 id="s10">About $9–18 per hexagon</h2>
  <p>Estimate for the personal build: PETG frame and back plate, LCD-style diffuser film, 100 mm edges with 2–3 RGBW LEDs each, about 100 panels. Prices are typical 2025–26 hobby-volume figures, not quotes. Shipping, import duties, tools, prototypes and spares are excluded.</p>
  <div class="facts">
    <div class="fact"><b>${lo_sum:.0f}–{hi_sum:.0f}</b><span>per hexagon (12–18 LEDs)</span></div>
    <div class="fact"><b>${lo_sum/0.026:.0f}–{hi_sum/0.026:.0f}</b><span>per m² of hexagons (one is 0.026 m²)</span></div>
    <div class="fact"><b>$6–13</b><span>per square (8–12 LEDs)</span></div>
    <div class="fact"><b>$6–12</b><span>per triangle (6–9 LEDs), about 3× the hexagon per m²</span></div>
    <div class="fact"><b>${lo_sum/10:.1f}–{hi_sum/10:.1f}k</b><span>for 100 hexagons (2.6 m²)</span></div>
  </div>
  <figure>
    <div class="fig-scroll">{fig_cost()}</div>
    <figcaption>Cost range per hexagon by item, low to high estimate. LEDs and the diffuser are about half the total. Hover a row for its basis.</figcaption>
  </figure>
  <details>
    <summary>Show as a table</summary>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Item</th><th>Low</th><th>High</th><th>Basis</th></tr></thead>
      <tbody>{cost_rows}<tr class="total"><td>Total per hexagon</td><td class="num">${lo_sum:.2f}</td><td class="num">${hi_sum:.2f}</td><td>mid-estimate ≈$13</td></tr></tbody>
    </table></div>
  </details>
  <ul class="plain">
    <li><b>Bridges are cheap now.</b> The seam bridge uses $0.02 springs, so a bridge costs about $0.70–1.20 instead of $3.40–7.15 with Harwin springs. What's left is spread across the edge PCBs, LEDs, the controller board and bridges.</li>
    <li><b>Size trade-off:</b> with the same 2–3 LEDs per edge, a 150 mm hexagon would cost about $11–22, roughly 45% less per m², because the per-panel parts don't shrink. But it is 300 mm across and won't fit a common print bed in one piece. Covering a wall with 100 mm panels takes about 2.25× as many panels, MCUs, bridges and corner joints.</li>
    <li><b>Running cost:</b> idle draw of about 0.3–0.5 W per panel is roughly $40–65 a year for 100 panels unless panels sleep (see Tier A).</li>
  </ul>
</section>

<section aria-labelledby="s11">
  <div class="num">11 · Gaps</div>
  <h2 id="s11">What the plan is still missing</h2>
  <p>Ordered by how much damage each does if it is found late. Tier A items can force a PCB or mechanical redesign, so each one gets a cheap prototype before any custom boards are ordered.</p>
  {gap_html()}
</section>

<section aria-labelledby="s12">
  <div class="num">12 · Commercial</div>
  <h2 id="s12">What it would take to sell this</h2>
  <p>The personal-build design works as a prototype for a product, but a product changes the economics and the paperwork. The core problem is price: comparable modular panel kits sell for very roughly $15–25 per panel, and retail is typically 3–4× the landed cost of materials. That puts the target material cost near $5–8 per hexagon, against about $7–17 today. The gap is spread across the fixed per-panel parts: edge PCBs, the controller board, LEDs and bridges.</p>
  <div class="facts">
    <div class="fact"><b>${lo_sum:.0f}–{hi_sum:.0f}</b><span>material cost per hexagon now</span></div>
    <div class="fact"><b>≈$5–8</b><span>target material cost for retail pricing</span></div>
    <div class="fact"><b>$15–60k</b><span>moulding tooling per part family (rough)</span></div>
    <div class="fact"><b>$15–40k</b><span>certification testing, one-time (rough)</span></div>
  </div>
  <h3 class="sub">Design changes from personal build to product</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Area</th><th>Personal build</th><th>Product</th></tr></thead>
    <tbody>{change_rows}</tbody>
  </table></div>
  <h3 class="sub">Certification and compliance</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Requirement</th><th>Applies to</th><th>What it means here</th></tr></thead>
    <tbody>{cert_rows}</tbody>
  </table></div>
  <p class="step-desc">A starting map, not legal advice. Confirm scope with a test lab before design freeze.</p>
  <div class="cols">
    <div>
      <h3 class="sub">Software and service</h3>
      <ul class="plain">
        <li>Native iOS and Android apps with guided setup; AR placement as an upgrade, not a requirement.</li>
        <li>Local-first control, with optional cloud for remote access.</li>
        <li>Integrations buyers expect: Matter, Apple Home, Google, Alexa, Home Assistant.</li>
        <li>Signed OTA pipeline, crash reporting, and a stated security-support period.</li>
        <li>Customer support, warranty returns and replacement panels.</li>
      </ul>
    </div>
    <div>
      <h3 class="sub">Reliability testing</h3>
      <ul class="plain">
        <li>Connector mating cycles and contact resistance over life.</li>
        <li>Thermal cycling at full white in a closed panel.</li>
        <li>LED failure rate against the warranty period.</li>
        <li>Mounting on painted drywall, plaster, tile and textured walls; ceiling pull-out force.</li>
        <li>Shipping drop tests and packaging.</li>
      </ul>
    </div>
    <div>
      <h3 class="sub">Business and legal</h3>
      <ul class="plain">
        <li><b>Patent freedom-to-operate search before any investment.</b> Established brands hold patents on connectable light panels and layout detection.</li>
        <li>Trademark, company formation, product liability insurance.</li>
        <li>Minimum order quantities and the cash to hold inventory.</li>
        <li>Validate demand first, for example with a crowdfunding campaign.</li>
        <li>Sales channels, returns handling and retailer requirements.</li>
      </ul>
    </div>
  </div>
  <p class="prose"><b>Where it could stand out:</b> most current products map a layout in 2D on one surface. Room-scale effects that run continuously across walls, ceilings and rooms, placed by an AR scan, are the differentiator worth protecting and demonstrating early.</p>
</section>
</main>
<script>{js}</script>
"""
    ref_html, plan_html = assemble(old, js, lo_sum, hi_sum, parts, cert_rows)
    for path, html in ((OUT_REF, ref_html), (OUT_PLAN, plan_html)):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print("wrote", path, len(html), "bytes")



# ---------------------------------------------------------------- V5.2 figures
def fig_edge_board():
    o = ['<svg viewBox="0 0 960 340" role="img" aria-label="An edge board has two faces. The inward face carries three LEDs, the MCU section (active board only), the ID resistor and diode, and six corner signal pads at each end. The exterior face is mostly power planes, with corner power pads at each end and ten edge-contact pads along the wall edge.">']
    o.append(text(40, 26, "Inward face · inside the panel", "t-title"))
    o.append('<rect x="40" y="38" width="880" height="96" rx="3" class="pcb-body"/>')
    for x in (40, 912):
        for k in range(5):
            o.append(f'<rect x="{x}" y="{48 + k * 16}" width="8" height="10" class="finger"/>')
    for x in (190, 470, 760):
        o.append(f'<rect x="{x}" y="56" width="26" height="26" rx="3" class="led"/>')
    o.append(text(483, 104, "3 × SKC6812RGBW (RGBW), facing into the panel", "t-xs t-body-on", "middle"))
    o.append('<rect x="270" y="48" width="160" height="76" rx="4" class="zone"/>')
    o.append(text(350, 70, "MCU section", "t-xs t-body-on t-strong", "middle"))
    o.append(text(350, 85, "active board only", "t-xs t-body-on", "middle"))
    for cx in (290, 330, 370):
        o.append(f'<rect x="{cx}" y="96" width="28" height="16" rx="2" class="chip-on"/>')
    o.append('<rect x="560" y="60" width="96" height="40" rx="3" class="zone"/>')
    o.append(text(608, 78, "R_ID + diode", "t-xs t-body-on", "middle"))
    o.append(text(608, 92, "one per board", "t-xs t-body-on", "middle"))
    o.append(text(40, 152, "◀ corner IN (CornerJoint_L)", "t-xs t-muted"))
    o.append(text(920, 152, "corner OUT (CornerJoint_R) ▶", "t-xs t-muted", "end"))
    o.append(text(480, 152, "wall edge ▼", "t-xs t-muted", "middle"))
    o.append(text(40, 188, "Exterior face · outside the panel, seen from outside (ends swapped)", "t-title"))
    o.append('<rect x="40" y="200" width="880" height="96" rx="3" class="pcb-body"/>')
    o.append('<rect x="56" y="206" width="848" height="40" class="plane"/>')
    o.append(text(480, 230, "+24V and GND lanes (others on either face)", "t-xs t-body-on", "middle"))
    for x in (40, 912):
        o.append(f'<rect x="{x}" y="208" width="8" height="10" class="sw-5v"/>')
        o.append(f'<rect x="{x}" y="222" width="8" height="10" class="sw-gnd"/>')
        o.append(f'<rect x="{x}" y="236" width="8" height="10" class="sw-power"/>')
    nets = [("GND", "sw-gnd", 3), ("+24V", "sw-power", 6), ("GND", "sw-gnd", 3), ("CANH", "sw-can", 9), ("CANL", "sw-can2", 9),
            ("DRIVE", "sw-drive", 9), ("SENSE", "sw-sense", 9), ("SPARE", "sw-spare", 9), ("+24V", "sw-power", 6), ("GND", "sw-gnd", 3)]
    for i, (nm, sw, gap) in enumerate(nets):
        x = 269 + i * 44
        o.append(f'<rect x="{x}" y="252" width="26" height="{296 - gap - 252}" class="{sw}"/>')
        o.append(text(x + 13, 314, nm, "t-xs", "middle"))
    o.append(text(40, 314, "◀ corner OUT", "t-xs t-muted"))
    o.append(text(920, 314, "corner IN ▶", "t-xs t-muted", "end"))
    o.append(text(480, 332, "edge contacts X1–X10, centred, ≈5 mm pitch · wall edge ▼", "t-xs t-muted", "middle"))
    o.append("</svg>")
    return "".join(o)


def fig_insert():
    p = "fi"
    o = [f'<svg viewBox="0 0 960 310" role="img" aria-label="Three steps: the bridge sits in its carrier on the wall next to panel A; panel B slides toward the wall and its bevelled edge rides over the springs; when seated, the springs on both faces of the bridge are compressed and the seam is about 6 to 8 mm.">', defs(p)]
    titles = ["1 · Bridge in its carrier, panel A seated", "2 · Panel B slides toward the wall", "3 · Seated: both spring rows compressed"]
    left_comp = "M148,206 L140,206 Q126,214 125,226 L134,238"
    right_free = "M152,206 L160,206 Q182,214 184,228 L172,240"
    right_mid = "M152,206 L160,206 Q178,214 180,227 L170,239"
    right_comp = "M152,206 L160,206 Q174,214 175,226 L166,238"

    def shift(path, dx):
        out, num = [], ""
        toks = path.replace(",", " , ").split()
        res = []
        xturn = True
        for t in toks:
            if t[0].isalpha():
                res.append(t[0])
                rest = t[1:]
                if rest:
                    res.append(str(float(rest) + dx))
                    xturn = False
                else:
                    xturn = True
            elif t == ",":
                res.append(",")
            else:
                if xturn:
                    res.append(str(float(t) + dx))
                else:
                    res.append(t)
                xturn = not xturn
        return " ".join(res).replace(" , ", ",")

    def board(ox, x, y_top, y_bot, label):
        o.append(f'<polygon points="{ox+x},{y_top} {ox+x+12},{y_top} {ox+x+12},{y_bot} {ox+x+3},{y_bot} {ox+x},{y_bot-4}" class="pcb"/>' if x > 150 else
                 f'<polygon points="{ox+x},{y_top} {ox+x+12},{y_top} {ox+x+12},{y_bot-4} {ox+x+9},{y_bot} {ox+x},{y_bot}" class="pcb"/>')
        face = ox + x if x > 150 else ox + x + 12
        o.append(f'<rect x="{face - (0 if x > 150 else 2)}" y="{y_bot - 40}" width="2" height="34" class="finger"/>')
        o.append(text(ox + x + 6, y_top - 6, label, "t-xs t-strong", "middle"))

    for i, t in enumerate(titles):
        ox = i * 320
        o.append(text(ox + 16, 22, t, "t-sm t-strong"))
        o.append(f'<rect x="{ox+10}" y="266" width="300" height="12" class="wall"/>')
        o.append(f'<rect x="{ox+128}" y="232" width="44" height="34" rx="2" class="encl"/>')
        o.append(f'<rect x="{ox+148}" y="196" width="4" height="68" class="bpcb"/>')
        board(ox, 110, 50, 262, "A")
        o.append(f'<path d="{shift(left_comp, ox)}" class="spring"/>')
        if i == 0:
            o.append(f'<path d="{shift(right_free, ox)}" class="spring"/>')
            o.append(f'<line x1="{ox+212}" y1="246" x2="{ox+176}" y2="240" class="w-leader"/>')
            o.append(text(ox + 216, 250, "free end", "t-xs"))
            o.append(text(ox + 216, 262, "toward wall", "t-xs"))
        elif i == 1:
            board(ox, 178, 6 + 30, 218, "B")
            o.append(f'<path d="{shift(right_mid, ox)}" class="spring"/>')
            o.append(f'<line x1="{ox+240}" y1="60" x2="{ox+240}" y2="130" class="w-ink" marker-end="url(#{p}-ink)"/>')
            o.append(text(ox + 248, 100, "push", "t-xs t-strong"))
            o.append(text(ox + 200, 200, "bevel rides", "t-xs"))
            o.append(text(ox + 200, 212, "over spring", "t-xs"))
        else:
            board(ox, 178, 50, 262, "B")
            o.append(f'<path d="{shift(right_comp, ox)}" class="spring"/>')
            o.append(f'<path d="M{ox+124},288 V296 M{ox+124},292 H{ox+178} M{ox+178},288 V296" class="w-ink"/>')
            o.append(text(ox + 151, 306, "seam ≈6–8 mm", "t-xs", "middle"))
    o.append("</svg>")
    return "".join(o)


def fig_corner():
    o = ['<svg viewBox="0 0 960 300" role="img" aria-label="Top view of a corner inside a hexagon panel: a solder bead joins five signal pads across the inner corner on the inward face, and a bent strap joins the power pads across the outside corner. Beside it, the end of a board shows five signal pads on the inward face and +24V, +5V and GND pads on the exterior face.">']
    o.append(text(40, 26, "Corner seen from above", "t-title"))
    o.append('<polygon points="70,214 380,214 380,226 70,226" class="pcb"/>')
    ux, uy = 0.5, -0.866
    nx2, ny2 = 0.866, 0.5
    a = (380, 214)
    b = (380 + 150 * ux, 214 + 150 * uy)
    o.append(f'<polygon points="{n(a[0])},{n(a[1])} {n(b[0])},{n(b[1])} {n(b[0]+12*nx2)},{n(b[1]+12*ny2)} {n(a[0]+12*nx2)},{n(a[1]+12*ny2)}" class="pcb"/>')
    o.append('<circle cx="382" cy="210" r="7" class="bead"/>')
    o.append('<path d="M370,228 Q392,244 392,222" class="strap"/>')
    o.append(text(230, 120, "inside the panel", "t-sm t-muted", "middle"))
    o.append(text(230, 262, "outside", "t-sm t-muted", "middle"))
    o.append('<line x1="300" y1="176" x2="374" y2="206" class="w-leader"/>')
    o.append(text(296, 166, "solder bead joins the 5 signal pads", "t-xs", "end"))
    o.append(text(296, 180, "(inward face)", "t-xs t-muted", "end"))
    o.append('<line x1="414" y1="262" x2="390" y2="238" class="w-leader"/>')
    o.append(text(418, 262, "bent strap or solder bridge joins", "t-xs"))
    o.append(text(418, 276, "+24V, +5V and GND (exterior face)", "t-xs"))
    o.append(text(120, 244, "corner OUT end", "t-xs t-muted", "middle"))
    o.append(text(474, 104, "next board, corner IN end", "t-xs t-muted"))
    o.append(text(570, 26, "Board end, inward face", "t-title"))
    o.append('<rect x="570" y="40" width="160" height="200" rx="3" class="pcb-body"/>')
    for k, nm in enumerate(["LED D", "CANH", "CANL", "SENSE", "DRIVE"]):
        y = 52 + k * 30
        o.append(f'<rect x="714" y="{y}" width="16" height="18" class="finger"/>')
        o.append(text(706, y + 13, nm, "t-xs t-body-on", "end"))
    o.append(text(570, 258, "CornerJoint_R (corner OUT); _L is its mirror", "t-xs t-muted"))
    o.append(text(780, 26, "Same end, exterior face", "t-title"))
    o.append('<rect x="780" y="40" width="150" height="200" rx="3" class="pcb-body"/>')
    for y, cls, nm in ((64, "sw-5v", "+5V"), (124, "sw-gnd", "GND"), (184, "sw-power", "+24V")):
        o.append(f'<rect x="780" y="{y}" width="16" height="34" class="{cls}"/>')
        o.append(text(804, y + 21, nm, "t-xs t-body-on"))
    o.append(text(780, 278, "seen from outside, so the end is on the left", "t-xs t-muted"))
    o.append("</svg>")
    return "".join(o)


def fig_active():
    p = "fa2"
    o = [f'<svg viewBox="0 0 960 400" role="img" aria-label="The controller board: 24 V comes in through the joint and an SMAJ28A, a TPS54360B makes an always-on 5 V rail, an HT7533 makes 3.3 V, and a TCAN1044V handles CAN. The CH32V203 switches the LED rail with a P-MOSFET, drives LED data through a level shifter, counts the loopback on PA6 and runs the SENSE and DRIVE buses. Everything reaches the edge boards through the joint on the code-0 board.">', defs(p)]
    o.append(box(30, 20, 250, 56, "24 V in", "PTC (60 V) · SMAJ28A TVS"))
    o.append(box(30, 95, 250, 56, "TPS54360B", "24 → 5 V buck · always on"))
    o.append(box(30, 170, 250, 56, "HT7533", "5 → 3.3 V · TLV431 overvoltage clamp"))
    o.append(box(30, 245, 250, 56, "TCAN1044V", "CAN · survives ±58 V faults"))
    o.append('<rect x="360" y="110" width="220" height="130" rx="8" class="box box-key"/>')
    o.append(text(470, 168, "CH32V203F6P6", "t-title", "middle"))
    o.append(text(470, 188, "RISC-V · CAN · 224 KB flash", "t-xs t-muted", "middle"))
    o.append(text(470, 204, "8 MHz crystal", "t-xs t-muted", "middle"))
    o.append(box(660, 20, 270, 56, "LED rail switch", "AO3401A → +5V_LED · gate from PA0"))
    o.append(box(660, 95, 270, 56, "LED data out", "PA7 → AHCT shifter → 33 Ω"))
    o.append(box(660, 170, 270, 56, "Loopback in", "PA6 · 2.2k/3.3k divider · 32 bits/LED"))
    o.append(box(660, 245, 270, 56, "SENSE / DRIVE", "10 k + clamp · open-drain DRIVE, 470 Ω"))
    o.append('<rect x="150" y="330" width="660" height="56" rx="6" class="box"/>')
    o.append(text(166, 354, "Joint to the code-0 edge board · ≈10 drag-soldered pads", "t-title"))
    o.append(text(166, 373, "+24V · GND · +5V_LED · LED return · LED data · spare · CANH · CANL · SENSE · DRIVE", "t-xs t-muted"))
    o.append(arrow(155, 76, 155, 91, p, "w-power", "ink"))
    o.append(arrow(155, 151, 155, 166, p))
    o.append(text(163, 162, "5 V", "t-xs t-muted"))
    o.append(f'<path d="M280,112 C 420,70 520,48 656,44" class="w-power" marker-end="url(#{p}-ink)"/>')
    o.append(text(470, 64, "+5V", "t-xs t-muted", "middle"))
    o.append(arrow(280, 198, 356, 178, p))
    o.append(text(318, 180, "3.3 V", "t-xs t-muted", "middle"))
    o.append(arrow(280, 273, 356, 226, p, both=True))
    o.append(text(316, 262, "PA11/12", "t-xs t-muted", "middle"))
    o.append(arrow(580, 130, 656, 62, p))
    o.append(text(612, 88, "PA0", "t-xs t-muted"))
    o.append(arrow(580, 160, 656, 123, p, "w-led-solid", "led"))
    o.append(arrow(656, 198, 584, 190, p, "w-led-solid", "led"))
    o.append(arrow(580, 225, 656, 273, p, "w-sense", "sense", both=True))
    o.append(arrow(155, 301, 155, 326, p, "w-can", "can", both=True))
    o.append(arrow(795, 301, 795, 326, p, "w-sense", "sense", both=True))
    o.append("</svg>")
    return "".join(o)



COMPARE = [
    # name, $/m2 lo, hi, $/100lm lo, hi, mid $/100lm (None if single rating), ours?
    ("Ours (parts only)", 335, 690, 3, 36, 10, True),
    ("Nanoleaf Shapes Hexagon", 620, 830, 21, 29, None, False),
    ("Nanoleaf Canvas", 490, 640, 25, 33, None, False),
]


def fig_compare():
    o = ['<svg viewBox="0 0 960 230" role="img" aria-label="Price per square metre: ours about 335 to 690 dollars in parts, Nanoleaf Shapes about 620 to 830 retail, Canvas about 490 to 640. Price per 100 lumens: ours about 3 to 36 dollars with a middle estimate near 10, Nanoleaf Shapes about 21 to 29, Canvas about 25 to 33.">']
    panels = [("Price per m²", 1, 2, 1000, 200, "$", ""), ("Price per 100 lumens", 3, 4, 40, 5, "$", "")]
    for k, (title, lo_i, hi_i, vmax, step, pre, suf) in enumerate(panels):
        ox = 20 + k * 470
        x0, x1 = ox + 190, ox + 440
        sx = lambda v, x0=x0, x1=x1, vmax=vmax: x0 + (x1 - x0) * v / vmax
        o.append(text(ox, 24, title, "t-title"))
        for v in range(0, vmax + 1, step):
            o.append(f'<line x1="{n(sx(v))}" y1="40" x2="{n(sx(v))}" y2="178" class="grid"/>')
            o.append(text(sx(v), 196, f"{pre}{v}{suf}", "t-xs t-muted", "middle"))
        for i, row in enumerate(COMPARE):
            name, lo, hi, mid, ours = row[0], row[lo_i], row[hi_i], row[5], row[6]
            y = 62 + i * 44
            tip = f"{name}: {pre}{lo}–{hi}{suf}" + (" (parts only, excludes shipping, duties and labour)" if ours else " (retail kit price)")
            o.append(f'<g class="rrow"><title>{tip}</title>')
            o.append(f'<rect x="{ox}" y="{y-18}" width="440" height="36" class="hit"/>')
            o.append(text(x0 - 10, y + 4, name, "t-sm" + (" t-strong" if ours else ""), "end"))
            o.append(f'<rect x="{n(sx(lo))}" y="{y-6}" width="{n(max(sx(hi)-sx(lo), 4))}" height="12" rx="4" class="{"rbar-ours" if ours else "rbar"}"/>')
            if ours and k == 1 and mid:
                o.append(f'<circle cx="{n(sx(mid))}" cy="{y}" r="5" class="mid-dot"/>')
            o.append(text(sx(hi) + 8, y + 4, f"{pre}{lo}–{hi}{suf}", "t-xs t-muted"))
            o.append("</g>")
    o.append(text(510, 222, "● middle estimate for ours (≈130 lm per panel) · Nanoleaf brightness is the rated figure", "t-xs t-muted"))
    o.append("</svg>")
    return "".join(o)


def fig_geometry():
    o = ['<svg viewBox="0 0 960 380" role="img" aria-label="Three panels drawn on their seam centrelines, 100 mm per side. The edge boards sit a fixed distance inside that line on every shape, so their lengths differ: about 94.1 mm on a hexagon, 89.8 mm on a square and 82.3 mm on a triangle.">']
    scale, dv = 1.3, 12
    for name, ns, cx, cy, blen, rot in (("Hexagon", 6, 170, 180, "≈94.1 mm", 0), ("Square", 4, 480, 180, "≈89.8 mm", 45), ("Triangle", 3, 790, 196, "≈82.3 mm", -90)):
        R = 100 * scale / (2 * math.sin(math.pi / ns))
        r = R * math.cos(math.pi / ns)
        Ri = (r - dv) / math.cos(math.pi / ns)
        outer = [(cx + R * math.cos(math.radians(rot + 360 * k / ns)), cy + R * math.sin(math.radians(rot + 360 * k / ns))) for k in range(ns)]
        inner = [(cx + Ri * math.cos(math.radians(rot + 360 * k / ns)), cy + Ri * math.sin(math.radians(rot + 360 * k / ns))) for k in range(ns)]
        o.append(f'<polygon points="{pts(outer)}" class="seamline"/>')
        o.append(f'<polygon points="{pts(inner)}" class="boardline"/>')
        o.append(text(cx, 334, name, "t-title", "middle"))
        o.append(text(cx, 354, f"board {blen}", "t-sm", "middle"))
        if ns == 6:
            yb = cy + r
            o.append(f'<path d="M{cx},{n(yb - dv)} V{n(yb)} M{cx - 4},{n(yb - dv)} H{cx + 4} M{cx - 4},{n(yb)} H{cx + 4}" class="w-ink"/>')
            o.append(text(cx + 10, yb - 2, "d = seam/2, fixed", "t-xs"))
            o.append(text(cx, cy - r - 8, "L = 100 mm on the seam centreline", "t-xs t-muted", "middle"))
    o.append("</svg>")
    return "".join(o)


def fig_lanes():
    o = ['<svg viewBox="0 0 960 300" role="img" aria-label="Left: the exterior face from the wall edge up, to scale: contact strip 0 to 8.5 mm, +12V lane, GND lane, +5V lane, then the signal bus at about 18.5 to 20.3 mm, on a 22 mm tall board. Right: the active board has four copper layers and the passive board two.">']
    k = 10  # px per mm
    y0 = 260  # wall edge
    yy = lambda mm: y0 - mm * k
    o.append(text(30, 24, "Exterior face (B.Cu), from the wall edge up", "t-title"))
    o.append(f'<rect x="60" y="{yy(22)}" width="320" height="{22*k}" rx="3" class="pcb-body"/>')
    for i in range(6):
        x = 82 + i * 50
        o.append(f'<rect x="{x}" y="{yy(8.0)}" width="26" height="{7.3*k}" class="finger"/>')
    bands = [(9.5, 12.5, "sw-power", "+12V lane", "9.5–12.5 mm"), (13, 16, "sw-gnd", "GND lane", "13–16 mm"), (16.5, 18, "sw-5v", "+5V lane", "16.5–18 mm")]
    for a, b, cls, nm, rng in bands:
        o.append(f'<rect x="64" y="{yy(b)}" width="312" height="{(b-a)*k}" class="{cls}"/>')
        o.append(text(392, yy((a + b) / 2) + 4, f"{nm} · {rng}", "t-xs"))
    for i, (cls, nm) in enumerate([("sw-can", "CANH"), ("sw-can2", "CANL"), ("sw-drive", "DRIVE"), ("sw-sense", "SENSE")]):
        yb = 18.6 + i * 0.45
        o.append(f'<rect x="64" y="{n(yy(yb + 0.3))}" width="312" height="3" class="{cls}"/>')
    o.append(text(392, yy(19.4) + 4, "signal bus · ≈18.5–20.3 mm", "t-xs t-strong"))
    o.append(text(392, yy(19.4) + 18, "CANH, CANL, DRIVE, SENSE (outermost)", "t-xs t-muted"))
    o.append(text(392, yy(4.2) + 4, "contact strip · 0–8.5 mm", "t-xs"))
    o.append(text(392, yy(4.2) + 18, "no pour, no vias", "t-xs t-muted"))
    o.append(text(392, yy(22) + 8, "top · H = 22 mm", "t-xs t-muted"))
    o.append(f'<line x1="50" y1="{y0}" x2="390" y2="{y0}" class="w-ink"/>')
    o.append(text(60, y0 + 18, "wall edge ▼", "t-xs t-muted"))
    # layer stacks
    o.append(text(600, 24, "Layer stacks", "t-title"))
    o.append(text(680, 50, "Active · 1 per panel", "t-sm t-strong", "middle"))
    o.append(text(860, 50, "Passive · N−1 per panel", "t-sm t-strong", "middle"))
    act = [("F.Cu", "parts, signals"), ("In1", "solid GND"), ("In2", "+12V │ GND │ +5V │ GND"), ("B.Cu", "contacts, bus, routing")]
    pas = [("F.Cu", "3 LEDs, ID diode + R"), ("B.Cu", "lanes, bus, contacts")]
    for i, (lay, desc) in enumerate(act):
        y = 66 + i * 46
        o.append(f'<rect x="595" y="{y}" width="170" height="36" rx="3" class="{"svc" if lay.startswith("In") else "box"}"/>')
        o.append(text(605, y + 15, lay, "t-xs t-strong"))
        o.append(text(605, y + 29, desc, "t-xs t-muted"))
    for i, (lay, desc) in enumerate(pas):
        y = 66 + i * 138
        o.append(f'<rect x="775" y="{y}" width="170" height="36" rx="3" class="box"/>')
        o.append(text(785, y + 15, lay, "t-xs t-strong"))
        o.append(text(785, y + 29, desc, "t-xs t-muted"))
    o.append(text(860, 170, "1.6 mm board,", "t-xs t-muted", "middle"))
    o.append(text(860, 184, "same outline and pads", "t-xs t-muted", "middle"))
    o.append(text(680, 268, "all 67 parts", "t-xs t-muted", "middle"))
    o.append(text(860, 268, "≈10 parts", "t-xs t-muted", "middle"))
    o.append("</svg>")
    return "".join(o)


def fig_prop_side():
    k = 8  # px per mm, heights to scale
    wall = 286
    z = lambda mm: wall - mm * k
    o = ['<svg viewBox="0 0 960 330" role="img" aria-label="Side cut through a panel, heights to scale: passive edge boards 13.5 mm tall at both sides; the controller board lies at the rear with its parts facing the wall in a pocket of the printed back plate, its white top forming the chamber floor about 6.6 mm above the wall; it is joined to one edge board by a hand-soldered 90 degree joint at its underside; the LEDs sit just above the floor. A dashed outline shows the old 22 mm board.">']
    o.append(f'<rect x="0" y="{wall}" width="960" height="14" class="wall"/>')
    o.append(text(632, 297, "wall", "t-xs t-muted"))
    for x in (100, 600):
        o.append(f'<rect x="{x}" y="{n(z(22))}" width="12" height="{n(22*k)}" class="ghost"/>')
        o.append(f'<rect x="{x}" y="{n(z(13.5))}" width="12" height="{n(13.5*k)}" class="pcb"/>')
    o.append(text(76, z(22) + 6, "old 22 mm", "t-xs t-muted", "end"))
    o.append(f'<path d="M84,{n(z(13.5))} V{wall} M80,{n(z(13.5))} H88 M80,{wall} H88" class="w-ink"/>')
    o.append(text(76, z(6.5) + 4, "13.5 mm", "t-xs t-strong", "end"))
    o.append(f'<rect x="100" y="{n(z(14.2))}" width="512" height="4" class="diffuser"/>')
    o.append(f'<line x1="628" y1="{n(z(13.95))}" x2="613" y2="{n(z(13.95))}" class="w-leader"/>')
    o.append(text(632, z(13.95) + 4, "diffuser film (height adjustable)", "t-xs"))
    yl = z(9.8)
    for (sx, sy), tg in (((120, yl), [(240, z(14)), (360, z(14))]), ((592, yl), [(480, z(14)), (360, z(14))])):
        for tx, ty in tg:
            o.append(f'<line x1="{sx}" y1="{n(sy)}" x2="{tx}" y2="{n(ty)}" class="ray"/>')
    o.append(f'<rect x="112" y="{n(z(12.3))}" width="8" height="{n(5*k)}" rx="2" class="led"/>')
    o.append(f'<rect x="592" y="{n(z(12.3))}" width="8" height="{n(5*k)}" rx="2" class="led"/>')
    o.append(f'<line x1="628" y1="{n(yl)}" x2="601" y2="{n(yl)}" class="w-leader"/>')
    o.append(text(632, yl + 4, "LEDs centred above the floor (9.8 mm)", "t-xs"))
    # back plate (top = chamber floor at 6.6 mm) with a pocket under the controller
    o.append(f'<rect x="330" y="{n(z(6.6))}" width="270" height="{n(6.6*k)}" class="clip"/>')
    o.append(f'<rect x="112" y="{n(z(5.0))}" width="38" height="{n(5.0*k)}" class="clip"/>')
    o.append(f'<rect x="310" y="{n(z(5.0))}" width="20" height="{n(5.0*k)}" class="clip"/>')
    for cx, w, h in ((180, 25, 1.75), (232, 32, 4.5), (282, 20, 2.3)):
        o.append(f'<rect x="{cx}" y="{n(z(5.0))}" width="{w}" height="{n(h*k)}" rx="1" class="chip"/>')
    o.append(f'<rect x="112" y="{n(z(6.6))}" width="218" height="{n(1.6*k)}" class="whitemask"/>')
    o.append(f'<polygon points="112,{n(z(5.0))} 124,{n(z(5.0))} 112,{n(z(3.6))}" class="bead"/>')
    o.append(text(350, z(9.6), "white controller top = chamber floor, ≈6.6 mm", "t-xs t-muted"))
    o.append(text(350, z(8.0), "controller board", "t-sm t-strong"))
    o.append(text(350, z(8.0) + 14, "MCU · CAN · 24→5 V buck · LED switch · LDO", "t-xs t-muted"))
    o.append(f'<line x1="346" y1="{n(z(8.0) - 4)}" x2="322" y2="{n(z(6.6) + 2)}" class="w-leader"/>')
    o.append(f'<line x1="150" y1="156" x2="116" y2="{n(z(4.4))}" class="w-leader"/>')
    o.append(text(140, 150, "hand-soldered 90° joint at the controller's underside (≈5 mm)", "t-xs"))
    o.append(f'<line x1="248" y1="306" x2="248" y2="{n(z(0.6))}" class="w-leader"/>')
    o.append(text(150, 320, "parts face the wall; pocket ≥2.8 mm, open to the wall under the 4.5 mm inductor", "t-xs"))
    o.append(f'<line x1="628" y1="{n(z(3))}" x2="613" y2="{n(z(3))}" class="w-leader"/>')
    o.append(text(632, z(3) - 2, "all edge boards passive", "t-sm t-strong"))
    o.append(text(632, z(3) + 13, "2-layer: LEDs, ID diode + R, lanes", "t-xs t-muted"))
    o.append(text(936, 24, "not to scale across; heights to scale", "t-xs t-muted", "end"))
    o.append("</svg>")
    return "".join(o)


def fig_prop_top():
    k = 1.35  # px per mm, to scale
    o = ['<svg viewBox="0 0 960 300" role="img" aria-label="Seen from the front, to scale: the same trapezoid controller board, about 72 mm at the base and 22 mm deep with 60 degree sides, fits inside a triangle panel and a hexagon panel, joined to the code-0 edge board along the bottom.">']
    base, depth, clr = 72 * k, 22 * k, 3 * k
    top = base - 2 * depth / math.tan(math.radians(60))

    def trap(cx, yb):
        y0 = yb - clr
        pts_ = [(cx - base / 2, y0), (cx + base / 2, y0), (cx + top / 2, y0 - depth), (cx - top / 2, y0 - depth)]
        o.append(f'<polygon points="{pts(pts_)}" class="whitemask-box"/>')
        o.append(f'<rect x="{n(cx - 16)}" y="{n(y0 - 3)}" width="32" height="3" class="bead-row"/>')
        o.append(text(cx, y0 - depth / 2 + 3, "controller", "t-xs t-strong t-on-white", "middle"))

    def boards(P):
        for a in range(len(P)):
            p1, p2 = shrink(P[a], P[(a + 1) % len(P)], 3)
            o.append(f'<line x1="{n(p1[0])}" y1="{n(p1[1])}" x2="{n(p2[0])}" y2="{n(p2[1])}" class="boardline-thin"/>')

    yb = 250
    # triangle (inner side 82.3 mm)
    st = 82.3 * k
    cxt = 140
    tri = [(cxt - st / 2, yb), (cxt + st / 2, yb), (cxt, yb - st * math.sqrt(3) / 2)]
    o.append(f'<polygon points="{pts(tri)}" class="hex-face"/>')
    boards(tri)
    trap(cxt, yb)
    o.append(f'<path d="M{n(cxt - base/2)},{yb + 12} H{n(cxt + base/2)} M{n(cxt - base/2)},{yb + 8} V{yb + 16} M{n(cxt + base/2)},{yb + 8} V{yb + 16}" class="w-ink"/>')
    o.append(text(cxt, yb + 28, "≈72 mm base · 60° sides", "t-xs", "middle"))
    o.append(text(cxt, 22, "Triangle: the tightest fit", "t-sm t-strong", "middle"))
    # hexagon (inner side 94.1 mm), flat-top so the code-0 edge is the bottom edge
    sh = 94.1 * k
    cxh = 420
    cyh = yb - sh * math.sqrt(3) / 2
    hexp = [(cxh + sh * math.cos(math.radians(60 * a)), cyh + sh * math.sin(math.radians(60 * a))) for a in range(6)]
    o.append(f'<polygon points="{pts(hexp)}" class="hex-face"/>')
    boards(hexp)
    trap(cxh, yb)
    o.append(text(cxh, 22, "Hexagon: same board, more room", "t-sm t-strong", "middle"))
    o.append(text(cxh, yb + 28, "code-0 edge board (joint, chain start/end)", "t-xs t-muted", "middle"))
    # joint nets
    o.append(text(600, 40, "Joint pads 1–10 (2.54 mm, drag-soldered)", "t-title"))
    nets = [("1 +24V", "sw-power"), ("2 GND", "sw-gnd"), ("3 +5V_LED", "sw-5v"), ("4 LED return", "sw-led"), ("5 LED data out", "sw-led"),
            ("6 spare", "sw-spare"), ("7 CANH", "sw-can"), ("8 CANL", "sw-can2"), ("9 SENSE", "sw-sense"), ("10 DRIVE", "sw-drive")]
    for i, (nm, sw) in enumerate(nets):
        col, row = divmod(i, 5)
        x, y = 600 + col * 175, 72 + row * 30
        o.append(f'<rect x="{x}" y="{y-11}" width="14" height="14" rx="2" class="{sw}"/>')
        o.append(text(x + 22, y + 1, nm, "t-sm"))
    o.append(text(600, 236, "The bus, ID lines and LED rail still run around the", "t-xs t-muted"))
    o.append(text(600, 252, "perimeter through the corner joints; the controller", "t-xs t-muted"))
    o.append(text(600, 268, "board taps in at one point.", "t-xs t-muted"))
    o.append("</svg>")
    return "".join(o)


def fig_prop_board():
    k = 12  # px per mm, heights to scale
    H = 13.5
    o = ['<svg viewBox="0 0 960 420" role="img" aria-label="Rev A passive edge board, 13.5 mm tall, heights to scale. Inward face: +5V_LED lane and signal bus low, the controller joint pads around 3.5 to 6.5 mm in the middle, LEDs just above the 6.6 mm chamber floor. Exterior face: contact strip 0 to 6 mm, +24V lane, GND lane.">']
    def face(y_top, title):
        o.append(text(60, y_top - 12, title, "t-title"))
        o.append(f'<rect x="60" y="{y_top}" width="600" height="{H*k}" rx="3" class="pcb-body"/>')
    yy_in = lambda mm: 40 + H * k - mm * k
    yy_ex = lambda mm: 250 + H * k - mm * k
    face(40, "Inward face (rev A)")
    o.append(f'<line x1="64" y1="{n(yy_in(6.6))}" x2="656" y2="{n(yy_in(6.6))}" class="floorline"/>')
    o.append(f'<rect x="64" y="{n(yy_in(2.5))}" width="592" height="{n(2.0*k)}" class="sw-5v"/>')
    for i, cls in enumerate(["w-can", "w-can", "w-sense", "w-sense", "w-led-solid"]):
        y = yy_in(2.9 + i * 0.5)
        o.append(f'<line x1="64" y1="{n(y)}" x2="656" y2="{n(y)}" class="{cls} thin"/>')
    for i in range(10):
        o.append(f'<rect x="{318 + i * 9}" y="{n(yy_in(5.7))}" width="6" height="{n(2.2*k)}" class="finger"/>')
    for x in (130, 330, 530):
        o.append(f'<rect x="{x}" y="{n(yy_in(12.3))}" width="60" height="{5*k}" rx="4" class="led"/>')
    o.append(f'<rect x="440" y="{n(yy_in(11.0))}" width="40" height="30" rx="3" class="zone"/>')
    o.append(text(460, yy_in(9.2), "ID", "t-xs t-body-on", "middle"))
    for x in (60, 652):
        for j in range(5):
            o.append(f'<rect x="{x}" y="{n(yy_in(12.4 - j * 2.4))}" width="8" height="18" class="finger"/>')
    lx = 676
    o.append(text(lx, yy_in(9.8) + 4, "LEDs · centres 9.8 mm, x 0 / ±31.2", "t-xs"))
    o.append(text(lx, yy_in(6.6) + 4, "chamber floor · 6.6 mm (dashed)", "t-xs t-muted"))
    o.append(text(lx, yy_in(5.0) + 4, "controller joint J4 · 3.5–5.7 mm, centred", "t-xs"))
    o.append(text(lx, yy_in(3.6) + 4, "signal bus + LED data · ≈2.9–4.9 mm", "t-xs"))
    o.append(text(lx, yy_in(1.5) + 4, "+5V_LED lane · ≈0.5–2.5 mm", "t-xs"))
    face(250, "Exterior face (rev A)")
    nets = [("sw-gnd", 3), ("sw-power", 6), ("sw-gnd", 3), ("sw-can", 9), ("sw-can2", 9), ("sw-drive", 9), ("sw-sense", 9), ("sw-spare", 9), ("sw-power", 6), ("sw-gnd", 3)]
    for i, (cls, gap) in enumerate(nets):
        x = 215 + i * 30
        o.append(f'<rect x="{x}" y="{n(yy_ex(6.0))}" width="20" height="{n(6.0*k - gap)}" class="{cls}"/>')
    o.append(f'<rect x="64" y="{n(yy_ex(9.0))}" width="592" height="{n(2.5*k)}" class="sw-power"/>')
    o.append(f'<rect x="64" y="{n(yy_ex(12.0))}" width="592" height="{n(2.5*k)}" class="sw-gnd"/>')
    o.append(text(lx, yy_ex(10.75) + 4, "GND lane · ≈9.5–12 mm", "t-xs"))
    o.append(text(lx, yy_ex(7.75) + 4, "+24V lane · ≈6.5–9 mm", "t-xs"))
    o.append(text(lx, yy_ex(3.0) + 4, "contact strip · 0–6 mm, X1–X10 at 5 mm pitch", "t-xs"))
    o.append(text(lx, yy_ex(3.0) + 18, "springs touch at 3.5 mm (≤5.0 with tolerance)", "t-xs t-muted"))
    for base in (40, 250):
        o.append(f'<path d="M44,{base} V{n(base + H*k)} M40,{base} H48 M40,{n(base + H*k)} H48" class="w-ink"/>')
        o.append(text(36, base + 6, "13.5", "t-xs t-muted", "end"))
        o.append(text(36, base + H * k + 4, "0 mm", "t-xs t-muted", "end"))
    o.append("</svg>")
    return "".join(o)

# ================================================================ three-page layout (hardware / firmware / software)
def box(x, y, w, h, title, sub="", key=False):
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="box{" box-key" if key else ""}"/>']
    if sub:
        o.append(text(x + 12, y + h / 2 - 3, title, "t-title"))
        o.append(text(x + 12, y + h / 2 + 15, sub, "t-xs t-muted"))
    else:
        o.append(text(x + 12, y + h / 2 + 5, title, "t-title"))
    return "".join(o)


def arrow(x1, y1, x2, y2, p, cls="w-ink", mk="ink", both=False):
    start = f' marker-start="url(#{p}-{mk})"' if both else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" marker-end="url(#{p}-{mk})"{start}/>'


def fig_fw_arch():
    p = "fa"
    o = [f'<svg viewBox="0 0 960 350" role="img" aria-label="Node firmware data path: CAN frames go through the driver to a protocol dispatcher, which feeds discovery, the effect VM and time sync. The effect VM produces colours, the frame builder applies gamma and caps, and a timer-plus-DMA driver sends them to the LEDs at the shared latch time. A separate bootloader handles updates.">', defs(p)]
    o.append(box(20, 40, 120, 50, "CAN bus"))
    o.append(box(180, 40, 160, 50, "CAN driver", "hardware filters"))
    o.append(box(400, 40, 190, 50, "Dispatcher", "routes by message class", key=True))
    o.append(box(660, 40, 280, 50, "Bootloader", "own flash region · CAN updates"))
    o.append(box(180, 150, 160, 50, "Discovery", "ADC sampling · DRIVE"))
    o.append(box(400, 150, 190, 50, "Effect VM", "bytecode per LED · fixed-point"))
    o.append(box(630, 150, 170, 50, "Time sync", "clock disciplined by SYNC"))
    o.append(box(830, 150, 110, 50, "Power", "sleep · standby"))
    o.append(box(20, 260, 140, 50, "SENSE / DRIVE", "edge contacts"))
    o.append(box(400, 260, 190, 50, "Frame builder", "gamma · dither · caps"))
    o.append(box(630, 260, 170, 50, "LED driver", "SPI + DMA"))
    o.append(arrow(140, 65, 176, 65, p))
    o.append(arrow(340, 65, 396, 65, p))
    o.append(text(368, 58, "frames", "t-xs t-muted", "middle"))
    o.append(arrow(590, 65, 656, 65, p))
    o.append(text(623, 58, "update", "t-xs t-muted", "middle"))
    o.append(arrow(430, 90, 300, 146, p, both=True))
    o.append(text(336, 112, "DISCOVER / reports", "t-xs t-muted", "end"))
    o.append(arrow(495, 90, 495, 146, p))
    o.append(text(503, 122, "effects, params", "t-xs t-muted"))
    o.append(arrow(570, 90, 700, 146, p))
    o.append(text(654, 112, "SYNC", "t-xs t-muted"))
    o.append(arrow(220, 200, 110, 256, p, "w-sense", "sense", both=True))
    o.append(arrow(495, 200, 495, 256, p, "w-led-solid", "led"))
    o.append(text(503, 232, "colours", "t-xs t-muted"))
    o.append(arrow(690, 200, 560, 256, p))
    o.append(text(640, 232, "LATCH at T", "t-xs t-muted"))
    o.append(arrow(590, 285, 626, 285, p, "w-led-solid", "led"))
    o.append(arrow(800, 285, 846, 285, p, "w-led-solid", "led"))
    o.append(text(852, 289, "LEDs", "t-strong t-led"))
    o.append(f'<path d="M885,200 V230 H760 V256" class="w-wifi" marker-end="url(#{p}-muted)"/>')
    o.append(text(820, 224, "LED rail on/off", "t-xs t-muted", "middle"))
    o.append("</svg>")
    return "".join(o)


def fig_flash():
    segs = [("Bootloader", 8, "seg-a", "immutable"), ("App, fast", 24, "seg-b", "CAN · VM · LED driver"),
            ("App, rest", 32, "seg-b2", "discovery · protocol · diagnostics"), ("Effect slots", 32, "seg-c", "installed effect bytecode"),
            ("Config", 4, "seg-d", "address, shape"), ("Log", 4, "seg-e", ""), ("Free", 120, "seg-f", "room to grow")]
    x0, x1 = 40, 920
    sx = (x1 - x0) / 224
    o = ['<svg viewBox="0 0 960 170" role="img" aria-label="Flash layout of the CH32V203F6P6 (224 KB): an 8 KB bootloader and 24 KB of hot application code in the first 32 KB, which runs without wait states, then 32 KB more application, 32 KB effect slots, 4 KB config, 4 KB log and 120 KB free.">']
    x = x0
    for i, (name, kb, cls, sub) in enumerate(segs):
        w = kb * sx
        o.append(f'<rect x="{n(x)}" y="60" width="{n(w-2)}" height="40" rx="3" class="{cls}"/>')
        mid = name == "Free"
        lx = x + w / 2 if mid else x
        anc = "middle" if mid else "start"
        o.append(text(lx, 26 if i % 2 == 0 else 46, f"{name} · {kb} KB", "t-sm t-strong", anc))
        if sub:
            o.append(text(lx, 118 if i % 2 == 0 else 134, sub, "t-xs t-muted", anc))
        x += w
    o.append(f'<line x1="{x0}" y1="104" x2="{n(x0 + 32 * sx - 2)}" y2="104" class="w-ink"/>')
    o.append(text(x0, 156, "▲ the first 32 KB runs without wait states", "t-xs"))
    o.append("</svg>")
    return "".join(o)


def fig_sync():
    p = "fs"
    o = [f'<svg viewBox="0 0 960 250" role="img" aria-label="The controller sends SYNC frames that keep every node clock aligned. Each node finishes computing its next frame at a different moment, but all of them show it at the same LATCH time.">', defs(p)]
    rows = [("Controller", 50), ("Node A", 110), ("Node B", 160), ("Node C", 210)]
    for name, y in rows:
        o.append(text(100, y + 4, name, "t-sm t-strong", "end"))
        o.append(f'<line x1="120" y1="{y}" x2="930" y2="{y}" class="rule"/>')
    for x in (150, 470, 790):
        o.append(f'<line x1="{x}" y1="34" x2="{x}" y2="66" class="w-can"/>')
        o.append(text(x, 26, "SYNC", "t-xs t-can", "middle"))
    latch = [310, 630, 900]
    for x in latch:
        o.append(f'<line x1="{x}" y1="86" x2="{x}" y2="226" class="latch"/>')
        o.append(text(x, 242, "LATCH", "t-xs t-strong", "middle"))
    for y, spans in ((110, [(222, 62), (544, 66), (814, 70)]), (160, [(236, 44), (556, 52), (826, 50)]), (210, [(214, 80), (536, 84), (808, 84)])):
        for (x, w), lx in zip(spans, latch):
            o.append(f'<rect x="{x}" y="{y-9}" width="{w}" height="18" rx="3" class="compute"/>')
            o.append(f'<rect x="{lx}" y="{y-9}" width="{min(150, 930-lx)}" height="18" rx="3" class="shown"/>')
    o.append(text(222, 92, "compute next frame", "t-xs t-muted"))
    o.append(text(316, 92, "frame on the LEDs", "t-xs t-led"))
    o.append("</svg>")
    return "".join(o)


def fig_sw_arch():
    p = "sa"
    o = [f'<svg viewBox="0 0 960 420" role="img" aria-label="Phone app, desktop studio and home automation all talk to the coordinator. The coordinator runs the API, layout store, voxel engine, effect compiler, scheduler, package store, device gateway and safety checker. It talks to cluster controllers over Wi-Fi and optionally to a cloud gallery.">', defs(p)]
    o.append(box(40, 30, 250, 66, "Phone app", "AR scan · setup · quick control"))
    o.append(box(355, 30, 250, 66, "Desktop studio", "browser · effect editor · preview"))
    o.append(box(670, 30, 250, 66, "Home automation", "Home Assistant · Matter · MQTT"))
    o.append('<rect x="40" y="146" width="880" height="156" rx="8" class="box box-key"/>')
    o.append(text(56, 168, "Coordinator · Raspberry Pi or ESP32", "t-title"))
    svc = [["API gateway", "Layout store", "Voxel engine", "Effect compiler"], ["Scheduler + sim", "Package store", "Device gateway", "Safety checker"]]
    for r, row in enumerate(svc):
        for c, name in enumerate(row):
            x = 56 + c * 216
            y = 180 + r * 58
            o.append(f'<rect x="{x}" y="{y}" width="200" height="46" rx="5" class="svc"/>')
            o.append(text(x + 100, y + 28, name, "t-sm t-strong", "middle"))
    o.append(arrow(165, 96, 165, 142, p, both=True))
    o.append(text(173, 124, "layout, commands", "t-xs t-muted"))
    o.append(arrow(480, 96, 480, 142, p, both=True))
    o.append(text(488, 124, "effects, live preview", "t-xs t-muted"))
    o.append(arrow(795, 96, 795, 142, p, both=True))
    o.append(text(803, 124, "scenes, states", "t-xs t-muted"))
    o.append(box(40, 346, 260, 56, "Effect gallery", "optional cloud · share and install"))
    o.append(box(660, 346, 260, 56, "Cluster controllers", "ESP32 · one per cluster"))
    o.append(arrow(170, 302, 170, 342, p, both=True))
    o.append(text(178, 328, "publish / install", "t-xs t-muted"))
    o.append(f'<line x1="790" y1="302" x2="790" y2="342" class="w-wifi" marker-end="url(#{p}-muted)" marker-start="url(#{p}-muted)"/>')
    o.append(text(798, 328, "Wi-Fi: effects, clock, samples", "t-xs t-muted"))
    o.append(text(480, 368, "Local-first: everything except the", "t-xs t-muted", "middle"))
    o.append(text(480, 384, "gallery works without internet", "t-xs t-muted", "middle"))
    o.append("</svg>")
    return "".join(o)


def fig_pipeline():
    p = "pl"
    steps = [("Author", "studio editor", ["presets · graph · script", "preview on your room", "or sample rooms"]),
             ("Compile", "node or coordinator", ["fields → node bytecode", "stateful → coordinator sim"]),
             ("Check", "safety + budget", ["flash rate, red flashes", "instruction budget", "VM version"]),
             ("Package", ".lfx bundle", ["manifest + bytecode", "parameter schema", "preview clip"]),
             ("Publish", "gallery or file", ["signed by author", "versions, remixes"]),
             ("Install & run", "on the coordinator", ["checked again locally", "sent to nodes over CAN"])]
    o = [f'<svg viewBox="0 0 960 200" role="img" aria-label="An effect is authored in the studio, compiled, checked for flash safety and budget, packaged, published to the gallery or a file, and installed on a coordinator, which checks it again before sending it to the nodes.">', defs(p)]
    w, g, x0 = 136, 24, 12
    for i, (t, s, det) in enumerate(steps):
        x = x0 + i * (w + g)
        o.append(f'<rect x="{x}" y="30" width="{w}" height="56" rx="6" class="box{" box-key" if i == 2 else ""}"/>')
        o.append(text(x + w / 2, 54, t, "t-title", "middle"))
        o.append(text(x + w / 2, 72, s, "t-xs t-muted", "middle"))
        for k, d in enumerate(det):
            o.append(text(x + w / 2, 110 + k * 16, d, "t-xs", "middle"))
        if i < len(steps) - 1:
            o.append(arrow(x + w, 58, x + w + g - 3, 58, p))
    o.append("</svg>")
    return "".join(o)


MANIFEST = """{
  "id": "aurora-drift",
  "version": "1.2.0",
  "runtime": { "kind": "node-field", "vm": ">=1.0", "budget": 180 },
  "anchors": ["floor", "ceiling", "room-centre"],
  "params": {
    "speed":   { "type": "number", "min": 0.05, "max": 2, "default": 0.4, "unit": "m/s" },
    "palette": { "type": "palette", "default": "aurora" },
    "spread":  { "type": "enum", "values": ["room", "building"], "default": "room" }
  },
  "safety":  { "maxFlashHz": 1.5, "redFlash": false },
  "preview": "preview.webm",
  "license": "CC-BY-4.0"
}"""

FW_PARTS = [
    ("Node firmware", "The application on each panel's CH32V203: CAN, discovery, effect VM, LED driver."),
    ("Bootloader", "A small, never-updated program that installs new node firmware over CAN."),
    ("Effect VM", "A tiny sandboxed interpreter that runs effect bytecode once per LED per frame."),
    ("Effect descriptor", "A few bytes naming an effect, its parameters, palette and start time."),
    ("SYNC / LATCH", "Clock-sync messages, and the shared moment every panel shows a new frame."),
    ("Controller firmware", "ESP-IDF application on each cluster controller: CAN gateway, Wi-Fi, orchestration."),
]
SW_PARTS = [
    ("Coordinator", "The always-on service that holds the room model and runs effects for the whole home."),
    ("Room model", "Clusters, panels, walls, doors and a voxel grid, all in one building frame in metres."),
    ("Anchor", "A named place in the room model (floor, ceiling, a doorway, a room centre) that effects refer to."),
    ("Effect", "A recipe for light over space and time, written against the room rather than a layout."),
    ("Effect package", "A signed .lfx bundle: manifest, bytecode or script, parameters and a preview."),
    ("Studio", "The desktop editor for building, previewing and publishing effects."),
    ("Phone app", "Setup, AR placement and everyday control."),
    ("Gallery", "An optional online library for sharing and installing effects."),
]

PAGE_GAPS = {
    "hardware": {
        "tiers": {"a": "Could force a redesign: prototype before ordering custom boards", "b": "Decide before schematic capture", "c": "Planning"},
        "items": [("a", "Optics are unproven"), ("a", "Seam bridge and carrier"), ("a", "Corner joints are a large hand job"), ("a", "Standby power"),
                  ("a", "Printing logistics"), ("a", "Mounting, especially ceilings"), ("b", "Panel shape: auto-detect or setting"), ("b", "Exposed contacts need protection"),
                  ("b", "CAN loops and termination"), ("b", "RGBW dim levels and flicker"), ("b", "Programming and test"), ("b", "Missing target numbers"), ("c", "Phasing")],
    },
    "firmware": {
        "tiers": {"a": "Needs hardware support: settle before the schematic", "b": "Design before writing code", "c": "Planning"},
        "items": [("a", "Sleep and wake"), ("a", "Diagnostics"), ("a", "Bootloader safety"), ("b", "Enumeration and addressing"), ("b", "Time sync accuracy"),
                  ("b", "Discovery robustness"), ("b", "Write the CAN protocol down"), ("c", "Firmware lockstep"), ("c", "Provisioning and OTA")],
    },
    "software": {
        "tiers": {"a": "Platform decisions", "b": "Design before building", "c": "Planning"},
        "items": [("a", "AR app platform"), ("a", "Local-first vs. cloud"), ("b", "Flash safety"), ("b", "Gallery trust and moderation"), ("b", "Effect portability"),
                  ("c", "Build the simulator first"), ("c", "Coordinator choices")],
    },
}

EXTRA_GAPS = {
    "Sleep and wake": ("Idle draw of 0.3–0.5 W per panel comes mostly from the MCU and CAN transceiver. Rev A has the transceiver's Rs pin on a GPIO (standby keeps the receiver on, so it can wake on bus traffic), and a P-MOSFET on the controller board now switches the LED rail (the 24 → 5 V buck stays on).",
                       "Write and measure the sleep sequence: on an OFF broadcast, buck off, MCU deep sleep, transceiver standby; wake on any bus activity."),
    "Diagnostics": ("Installed panels are hard to inspect. Each node should report supply voltage, temperature, CAN error counters and LED chain health. Supply voltage needs a resistor divider on a spare ADC pin.",
                    "Add the divider footprint. The apps then show a voltage-drop and fault map of every wall."),
    "Bootloader safety": ("A power cut during an update must never brick a panel inside a wall. The bootloader has to be immutable, check a CRC or signature before starting the app, and stay in update mode if the app is invalid. That needs flash headroom.",
                          "The CH32V203F6P6 has 224 KB of flash, of which only the first 32 KB runs without wait states. Keep the bootloader (about 8 KB) and hot code there, and the effect slots further up."),
    "Enumeration and addressing": ("Nodes start with only a 96-bit chip ID. The controller needs a collision-free way to find them on a shared bus and hand out short addresses.",
                                   "Use CAN arbitration on the chip ID (lowest ID wins, repeat until none are left) and store the address in flash so it survives reboots."),
    "Time sync accuracy": ("Effects that cross walls and rooms only look continuous if every cluster agrees on time.",
                           "Timestamp SYNC frames in hardware at start-of-frame. Target ≤ 0.1 ms within a cluster and ≤ 2 ms across clusters, and measure it with a photodiode on two panels."),
    "Local-first vs. cloud": ("Accounts, remote access and the gallery need a server. Nothing else should.",
                              "Run all control on the coordinator. Make the gallery optional, and allow installing an effect from a file."),
    "Gallery trust and moderation": ("Published effects come from strangers. A careless or malicious effect could flash dangerously or exhaust node resources.",
                                     "Sign packages, re-run the safety and budget checks on install, keep effects sandboxed with no network or file access, and support reports and takedowns."),
    "Effect portability": ("An effect written in one home has to work in another with different rooms and layouts.",
                           "Write effects against anchors and path distance, with fallbacks when an anchor is missing. Preview on sample rooms before publishing."),
}


def page_gaps(page):
    base = {t: (pr, nx) for key in GAPS for t, pr, nx in GAPS[key][2]}
    base.update(EXTRA_GAPS)
    cfg = PAGE_GAPS[page]
    out = []
    for tier in ("a", "b", "c"):
        items = [t for k, t in cfg["items"] if k == tier]
        if not items:
            continue
        cards = "".join(f'<article class="gap"><h4>{t}</h4><p>{base[t][0]}</p><p><b>Next step:</b> {base[t][1]}</p></article>' for t in items)
        out.append(f'<div class="tier tier-{tier}"><div class="tier-head"><span class="chip chip-{tier}">Tier {tier.upper()}</span><h3>{cfg["tiers"][tier]}</h3></div><div class="gaps">{cards}</div></div>')
    return "".join(out)


RENDERS = [
    # (path from the project root, caption, wide)
    ("mechanical/archive/openscad-panel/png/assembly_exploded_color.png", "Exploded hexagon panel, top to bottom: bezel, diffuser film, riser, frame (crown) with the six edge boards, back plate, then the seam bridge in its carrier. The controller sits under the back plate.", False),
    ("mechanical/archive/openscad-panel/png/assembly_panel_color.png", "One assembled hexagon with the film fitted. The two dimples in the middle are the plugged screw-access holes for the wall puck.", False),
    ("mechanical/archive/openscad-panel/png/assembly_cluster_color.png", "The rev A prototype: three hexagons on the wall, joined by seam bridges. The left panel is shown without its film.", False),
    ("mechanical/archive/openscad-panel/png/section_seam.png", "Cut through a seam, heights to scale: the bridge stands in its carrier between two edge boards, its springs touching at z 3.5 mm, below the 6.6 mm floor. The frame wall starts at 7.5 mm, clear of the bridge top at 7.0.", False),
    ("mechanical/archive/openscad-panel/png/section_controller.png", "Cut through the controller edge: the controller (blue) lies under the floor, parts facing the wall, its pocket open through to the wall. It meets the code-0 edge board at 90°.", False),
    ("mechanical/archive/openscad-panel/png/frame_corner.png", "Frame corner from inside: only the 2 mm cap spans the corner, so the corner joints are soldered with the boards held in the frame. The tall tabs are the snap legs.", False),
    ("mechanical/archive/openscad-panel/png/bridge_carrier.png", "Bridge carrier: the bridge (gold) stands in its slot. The carrier floats, trapped between the wall and the two panels and centred by the springs.", False),
    ("mechanical/archive/openscad-panel/png/wall_puck.png", "Wall puck: two countersunk screws into the wall, two split-tube snap posts that the panel's back plate clicks onto. One per panel.", False),
    ("hardware/edge-board/output/fab-hex/edge-board-hex_render_top.png", "Edge board, inward face (94.1 × 13.5 mm): hexagon version: three SK6812 RGBW LEDs at x 0 and ±31.2 mm. All three shapes share this layout; only the outer LEDs and the board ends move, the 10 controller-joint pads J4 in the middle, the ID resistor and diode, and the corner signal pads at both ends.", True),
    ("hardware/edge-board/output/fab-hex/edge-board-hex_render_bottom.png", "Edge board, exterior face: the 10 gold contact pads X1–X10 along the wall edge (mask opened as one strip), the +24V and GND lanes, and the corner power pads at both ends.", True),
    ("hardware/edge-board/output/fab-square/edge-board-square_render_top.png", "Square edge board (89.8 × 13.5 mm): the same layout as the hexagon and triangle, with LEDs at x 0 and ±29.9 mm.", True),
    ("hardware/edge-board/output/fab-triangle/edge-board-triangle_render_top.png", "Triangle edge board (82.33 × 13.5 mm), the rev A test board: the same layout, with LEDs at x 0 and ±27.4 mm.", True),
    ("hardware/bridge/output/fab/bridge_render_top.png", "Seam bridge, 56 × 9 × 0.8 mm (injection variant): 10 spring pads per face at 5 mm pitch, wire pads at both ends and the 5 A slow-blow fuse. Face B is the 180° image with the SENSE/DRIVE cross.", True),
    ("hardware/controller-board/output/layout/final_F.png", "Controller board, wall side (72 × 24 mm trapezoid): buck converter and inductor L1 on the left, the CH32V203 and CAN in the middle, test pads TP1–TP9 on the right, and the joint pads J1 along the base.", True),
    ("hardware/bridge/coupon/output/fab/spring-coupon_render_top.png", "Spring test coupon (28 × 30 mm): four springs on one half, four contact pads on the other. The halves snap apart and stack face to face to measure force, resistance and the right seam width.", False),
]


def render_gallery(kind="boards"):
    import base64
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    figs = []
    for rel, cap, wide in RENDERS:
        if (kind == "boards") != rel.startswith("hardware/"):
            continue
        fp = os.path.join(root, *rel.split("/"))
        if not os.path.exists(fp):
            print("render missing:", rel)
            continue
        b64 = base64.b64encode(open(fp, "rb").read()).decode("ascii")
        cls = ' class="wide"' if wide else ""
        figs.append(f'<figure{cls}><img src="data:image/png;base64,{b64}" alt="{cap}" loading="lazy"><figcaption>{cap} <span class="src">{rel}</span></figcaption></figure>')
    if kind == "boards":
        body = ('<p>The rev A boards as laid out in KiCad. These are the files the JLCPCB order is made from; '
                'the design review checks them before ordering. Since V6.9.2 the J4 joint pads reach down to z 2.5 (2.5 mm of fillet land '
                'below the controller) and R3 is an 0402 just under LED1, so nothing on the inward face sits below z 6.8.</p>'
                f'<div class="gallery">{"".join(figs)}</div>')
        return sec("hw-boards", "Rev A · Boards", "What the rev A boards look like", body)
    body = ('<p><b>Superseded concept.</b> The first mechanical model, made in OpenSCAD (<code>mechanical/archive/openscad-panel/</code>). '
            'It used a floating bridge carrier, a screwed wall puck and plugged screw holes. Decisions 0013 and 0014 replaced those parts; '
            'the frame, back plate and diffuser ideas carry over into the SolidCraft redesign planned above.</p>'
            f'<div class="gallery">{"".join(figs)}</div>')
    return sec("mech-old", "Earlier concept", "The first mechanical model (OpenSCAD, superseded)", body)



# ======================= media: Blender showcase, KiCad 3D renders, SolidCraft CAD =======================
RO = "mechanical/solidcraft/render/out/"
MEDIA = {
    "show": [
        ("video", RO + "penthouse_panels.mp4", "Showcase video (8 s, 1440p, Cycles): about 750 panels on four walls of a penthouse loft. A colour wave travels through the room in 3D, so it flows round the corners, with a slow breathing pulse; the camera pushes in from the window corner.", True),
        ("video", RO + "penthouse_closeup.mp4", "Close-up video (8 s, 1440p): a slow arc round the outside corner where the ribbon wraps from the painting wall onto the stair-side wall. Bezels, the 7 mm seams and the glow spilling onto the wall are visible.", True),
        ("img", RO + "penthouse_still.png", "Still from the wide shot: one ribbon runs from the corner over the TV, round the inside corner over the painting and round the outside corner; a fourth cluster sits high on the double-height kitchen wall. Every panel is placed on bare wall by ray casting.", True),
        ("img", RO + "penthouse_closeup.png", "Close-up still at the outside corner (depth of field on the corner).", True),
    ],
    "boards3d": [
        ("img", "hardware/edge-board/output/3d/edge-board-triangle_top_iso.png", "Triangle edge board (82.33 mm), inward face: three SK6812 RGBW LEDs, the 10 J4 joint pads in the middle (now reaching down to z 2.5), the ID resistor and diode, and the corner signal pads at both ends.", False),
        ("img", "hardware/edge-board/output/3d/edge-board-triangle_bottom_iso.png", "Triangle edge board, exterior face: the 10 gold contact pads along the wall edge that the bridge springs press on, and the corner power pads.", False),
        ("img", "hardware/edge-board/output/3d/edge-board-hex_top_iso.png", "Hexagon edge board (94.1 mm): the same layout with the outer LEDs at ±31.2 mm.", False),
        ("img", "hardware/edge-board/output/3d/edge-board-square_top_iso.png", "Square edge board (89.8 mm): LEDs at ±29.9 mm.", False),
        ("img", "hardware/controller-board/output/3d/controller-board_top_iso.png", "Controller board, parts side (faces the wall): buck converter and L1, CH32V203, CAN transceiver, test pads and the J1 joint pads along the base.", False),
        ("img", "hardware/controller-board/output/3d/controller-board_bottom_iso.png", "Controller board, chamber side: no parts or pads, so it can be painted white as part of the reflector.", False),
        ("img", "hardware/bridge/output/3d/bridge_top_iso.png", "Seam bridge (56 × 9 × 0.8 mm), face A: 10 BW0019CG springs at 5 mm pitch; injection variant with the fuse and wire pads.", False),
        ("img", "hardware/bridge/output/3d/bridge_bottom_iso.png", "Seam bridge, face B: the 180° image of face A.", False),
        ("img", "hardware/bridge/coupon/output/3d/spring-coupon_top_iso.png", "Spring test coupon: four springs on one half, four contact pads on the other, snapped apart and stacked to measure force, resistance and seam width.", False),
    ],
    "cad": [
        ("img", "mechanical/solidcraft/png/assembly_front.png", "SolidCraft assembly of a mixed cluster (2 hexagons, a square, 2 triangles): frames, bezels and diffuser film, with every board as its KiCad STEP model. No interference between parts.", True),
        ("img", "mechanical/solidcraft/png/assembly_back.png", "The same cluster from the back: back plates with Dual Lock bosses, the controllers in their pockets and a bridge clip across each seam.", True),
        ("img", "mechanical/solidcraft/png/back_plate_triangle.png", "Back plate (Triangle configuration), chamber side: floor, rim and the open controller pocket with its cross-bar.", False),
        ("img", "mechanical/solidcraft/png/back_plate_triangle_back.png", "Back plate, wall side: the clip recesses with key grooves and tooth notches, the hook pockets for the frame legs and the Dual Lock boss.", False),
        ("img", "mechanical/solidcraft/png/frame_triangle.png", "Frame (crown): cap, closed corners with corner pins, and two snap legs per side that hook under the back-plate tabs.", False),
        ("img", "mechanical/solidcraft/png/bezel_triangle.png", "Bezel and diffuser film: the bezel clamps the film on the frame cap.", False),
        ("img", "mechanical/solidcraft/png/bridge_clip.png", "Bridge clip (universal, 59 × 20 mm, 3.0 mm base): the bridge slot, two straight-sided keys (2.5 mm deep in the back-plate grooves) and four snap arms (1.8 × 15.5 mm).", False),
        ("img", "mechanical/solidcraft/png/edge_cover.png", "Edge cover for free cluster edges: half a clip plus a wall over the exposed contact pads.", False),
        ("img", "mechanical/solidcraft/png/section_seam_spring.png", "Cross-section across the seam between two hexagons, through a bridge spring (x 2.5, looking along the seam; cut faces hatched by part). Both edge boards stand in the frame groove; the bridge stands in the clip with a spring touching each board's contact pad; the clip's straight keys sit in the back-plate grooves; both controllers meet their code-0 boards at the J4 joint.", True),
        ("img", "mechanical/solidcraft/png/section_seam_tooth.png", "Cross-section through a clip tooth (x 23): the snap arms at the clip edges with their teeth (60° lead-in, 45° latch) in the back-plate notches.", True),
        ("img", "mechanical/solidcraft/png/section_seam_hook.png", "Cross-section through a frame snap leg (x 33): the hooks reach 1.2 mm under the back-plate tabs on the latch plane z −2.3.", True),
        ("img", "mechanical/solidcraft/png/edge_board_standin.png", "Printable stand-in edge board for fit tests (board block with LED and part envelopes).", False),
        ("img", "mechanical/solidcraft/png/bridge_standin.png", "Printable stand-in bridge with spring envelopes (0.2 mm short of the pads).", False),
    ],
}


def embed_img(fp, max_w=1600):
    import base64
    import io
    from PIL import Image
    im = Image.open(fp)
    alpha = im.mode in ("RGBA", "LA") and im.getchannel("A").getextrema()[0] < 250
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if alpha:
        im.save(buf, "PNG", optimize=True)
        mime = "image/png"
    else:
        im.convert("RGB").save(buf, "JPEG", quality=86, optimize=True)
        mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode("ascii"), alpha


def video_poster(fp, at=0.4, max_w=1600):
    import base64
    import io
    try:
        import cv2
        from PIL import Image
    except ImportError:
        return ""
    cap = cv2.VideoCapture(fp)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * at))
    ok, fr = cap.read()
    if not ok:
        return ""
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def media_gallery(kind):
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    figs = []
    for typ, rel, cap, wide in MEDIA[kind]:
        fp = os.path.join(root, *rel.split("/"))
        if not os.path.exists(fp):
            print("media missing:", rel)
            continue
        cls = ' class="wide"' if wide else ""
        if typ == "video":     # played from the project folder (relative path); the poster frame is embedded
            figs.append(f'<figure{cls}><video controls loop muted playsinline preload="metadata" poster="{video_poster(fp)}">'
                        f'<source src="../../{rel}" type="video/mp4"></video>'
                        f'<figcaption>{cap} <span class="src">{rel}</span></figcaption></figure>')
        else:
            data, alpha = embed_img(fp)
            acls = ' class="alpha"' if alpha else ""
            figs.append(f'<figure{cls}><img{acls} src="{data}" alt="{cap}" loading="lazy">'
                        f'<figcaption>{cap} <span class="src">{rel}</span></figcaption></figure>')
    gal = f'<div class="gallery">{"".join(figs)}</div>'
    if kind == "show":
        return sec("hw-show", "Showcase", "What it looks like on the wall",
                   "<p>Path-traced renders in Blender (<code>mechanical/solidcraft/render/penthouse_scene.py</code>) of the real panel "
                   "models exported from SolidCraft, in a free penthouse scene from BlenderKit. The videos play from the project folder, "
                   "so open this page from there.</p>" + gal)
    if kind == "boards3d":
        return sec("hw-boards3d", "Rev A · Boards in 3D", "The boards in 3D (KiCad)",
                   "<p>Raytraced views from KiCad (<code>docs/diagrams/render_boards_3d.py</code>) with the parts' 3D models, "
                   "both faces of each board.</p>" + gal)
    return sec("mech-cad", "CAD · First pass", "The panel parts in SolidCraft",
               "<p>The rev A mechanical CAD (<code>mechanical/solidcraft/</code>): parametric back plate, frame and bezel with "
               "Hexagon / Square / Triangle configurations, the universal clip and edge cover, and the mixed-cluster assembly with "
               "all board STEP models. Shown in the Triangle configuration, the rev A test model. Snapshots by "
               "<code>docs/diagrams/snap_cad.py</code>.</p>" + gal)


# ======================= planning: mechanical concept figures (decision 0014) =======================
SEAM_K = 13.0


def wrapped_notes(o, lx, ly, notes, width=40, gap=24):
    for head, body in notes:
        o.append(text(lx, ly, head, "t-sm t-strong"))
        yy = ly + 16; line = ""
        for w in body.split(" "):
            if line and len(line) + len(w) > width:
                o.append(text(lx, yy, line.strip(), "t-xs t-muted")); yy += 14; line = ""
            line += w + " "
        o.append(text(lx, yy, line.strip(), "t-xs t-muted"))
        ly = yy + gap
    return ly


def key_pts(X, Z, sg, y0=6.4, y1=8.4, top=1.2, ch=0.3):
    """Straight-sided key on the clip top (z -1.3 up to `top`), |y| y0..y1 on side sg, with a lead-in chamfer at the top."""
    f = lambda y: sg * y
    return (f"{n(X(f(y0)))},{n(Z(-1.3))} {n(X(f(y1)))},{n(Z(-1.3))} "
            f"{n(X(f(y1)))},{n(Z(top - ch))} {n(X(f(y1 - ch)))},{n(Z(top))} "
            f"{n(X(f(y0 + ch)))},{n(Z(top))} {n(X(f(y0)))},{n(Z(top - ch))}")


def fig_plan_seam():
    k = SEAM_K
    X = lambda y: 60 + (y + 16) * k
    Z = lambda z: 24 + (19 - z) * k
    o = ['<svg viewBox="0 0 960 440" role="img" aria-label="Planned cross-section through a seam between two panels, heights to scale: two edge boards 13.5 mm tall with LEDs, frames with caps and lips, back plates with grooves and lugs underneath, and a rigid bridge clip holding the bridge PCB upright. Straight-sided keys on the clip sit in the back-plate grooves and hold the panels together; snap teeth in the lug windows keep the clip on. Dual Lock pads sit between the panel back and the wall.">',
         defs("ps")]

    def R(y0, y1, z0, z1, cls, extra=""):
        a, b = sorted((y0, y1)); c, d = sorted((z0, z1))
        o.append(f'<rect x="{n(X(a))}" y="{n(Z(d))}" width="{n((b - a) * k)}" height="{n((d - c) * k)}" class="{cls}"{extra}/>')

    # wall and Dual Lock
    R(-16, 16, -11.4, -10.0, "wall")
    R(-16, -12.5, -10.0, -4.3, "hatch")
    R(12.5, 16, -10.0, -4.3, "hatch")
    for sg in (-1, 1):
        f = lambda y: sg * y
        # back plate (body + tab under the board)
        R(f(16), f(5.35), -1.3, 6.6, "print")
        R(f(5.35), f(3.6), -1.3, 0.0, "print")
        # lug with window (tooth fills the window)
        R(f(11.5), f(10.0), -1.9, -1.3, "print")
        R(f(11.5), f(10.0), -4.3, -3.3, "print")
        R(f(10.8), f(10.0), -3.3, -1.9, "bclip")
        # edge board, contact pad, LED
        R(f(5.1), f(3.5), 0, 13.5, "pcb")
        R(f(3.5), f(3.38), 0.3, 6.0, "finger")
        R(f(6.7), f(5.1), 7.37, 12.23, "led")
        # frame: exterior wall, cap, lip
        R(f(3.35), f(0.3), 7.5, 13.65, "print")
        R(f(6.1), f(0.3), 13.65, 15.65, "print")
        R(f(6.1), f(5.25), 12.8, 13.65, "print")
        # film and bezel
        R(f(16), f(0.8), 15.65, 15.95, "diffuser")
        R(f(6.1), f(0.3), 15.95, 17.95, "print")
        # spring on the bridge face
        o.append(f'<polygon points="{n(X(f(0.4)))},{n(Z(2.4))} {n(X(f(3.45)))},{n(Z(3.5))} {n(X(f(0.4)))},{n(Z(4.6))}" class="bead"/>')
    # chamber floor line
    o.append(f'<line x1="{n(X(-16))}" y1="{n(Z(6.6))}" x2="{n(X(-6.7))}" y2="{n(Z(6.6))}" class="floorline"/>')
    # clip: plate, arm slots (gaps), spine
    R(-10, 10, -4.3, -1.3, "bclip")
    R(-8.5, -7.5, -4.3, -1.3, "gapfill")
    R(7.5, 8.5, -4.3, -1.3, "gapfill")
    R(-1.7, 1.7, -1.3, 2.0, "bclip")
    for sg in (-1, 1):
        o.append(f'<polygon points="{key_pts(X, Z, sg)}" class="bclip"/>')
    # bridge PCB standing in the slot
    R(-0.4, 0.4, -2.0, 7.0, "pcb")
    # insertion arrow (clip pushed onto the seam from the wall side)
    o.append(arrow(X(0), Z(-9.4), X(0), Z(-5.0), "ps", "w-ink", "ink"))
    o.append(text(X(0.8), Z(-6.6), "clip pushed on", "t-xs"))
    o.append(text(X(0.8), Z(-6.6) + 13, "from the back", "t-xs"))
    o.append(text(X(-14.25), Z(-6.4), "Dual", "t-xs t-muted", "middle"))
    o.append(text(X(-14.25), Z(-6.4) + 13, "Lock", "t-xs t-muted", "middle"))
    o.append(text(X(14.25), Z(-6.4), "Dual", "t-xs t-muted", "middle"))
    o.append(text(X(14.25), Z(-6.4) + 13, "Lock", "t-xs t-muted", "middle"))
    o.append(text(X(-3), Z(-10.7) + 4, "wall (not a part)", "t-xs t-muted", "middle"))
    # height scale
    for zz in (-4.3, 0, 6.6, 13.5, 15.65):
        o.append(f'<line x1="{n(X(-16) - 6)}" y1="{n(Z(zz))}" x2="{n(X(-16))}" y2="{n(Z(zz))}" class="dim"/>')
        o.append(text(X(-16) - 9, Z(zz) + 4, f"{zz:g}", "t-xs t-muted", "end"))
    o.append(text(X(-16) - 9, Z(19) + 4, "z mm", "t-xs t-muted", "end"))
    # labels (right), with leaders to panel B features
    lx = 520
    labels = [
        (17.0, 3.2, "bezel clamps the film onto the frame cap"),
        (14.6, 3.0, "frame: cap, lip and groove hold the board tops"),
        (9.8, 5.9, "LEDs, centred at z 9.8"),
        (11.0, 4.3, "edge board, 13.5 mm"),
        (6.6, 8.0, "back plate: chamber floor at z 6.6"),
        (3.5, 2.2, "spring on the bridge presses the contact pad"),
        (5.0, 0.4, "bridge PCB, standing in the clip's slot"),
        (0.2, 6.8, "straight key in a back-plate groove: holds the panels together"),
        (-2.6, 10.4, "snap tooth in the lug window: keeps the clip on"),
        (-3.0, 4.0, "bridge clip: one rigid plate across the seam"),
        (-5.0, 15.6, "Dual Lock pad, only on some panels"),
    ]
    ly = 36
    for z, y, t in labels:
        o.append(f'<line x1="{n(lx - 4)}" y1="{n(ly - 4)}" x2="{n(X(y))}" y2="{n(Z(z))}" class="w-leader"/>')
        o.append(text(lx, ly, t, "t-xs"))
        ly += 35
    o.append(text(X(-8), Z(18.6), "panel A", "t-sm t-strong", "middle"))
    o.append(text(X(8), Z(18.6), "panel B", "t-sm t-strong", "middle"))
    o.append("</svg>")
    return "".join(o)


def fig_plan_clip():
    k = 7.0
    X = lambda x: 330 + x * k
    Y = lambda y: 150 - y * k
    o = ['<svg viewBox="0 0 960 330" role="img" aria-label="Planned bridge clip seen from the wall side: a 59 by 20 mm plate across the seam, with two straight-sided key ribs on its far face that sit in back-plate grooves and hold the panels together, and four snap arms cut into its long edges. A tooth near each arm end clicks into a window in a lug on each panel\'s back plate. The bridge slot runs along the seam. The frame\'s snap legs sit just beyond the clip ends.">']

    def R(x0, x1, y0, y1, cls, rx=0):
        a, b = sorted((x0, x1)); c, d = sorted((y0, y1))
        o.append(f'<rect x="{n(X(a))}" y="{n(Y(d))}" width="{n((b - a) * k)}" height="{n((d - c) * k)}" rx="{rx}" class="{cls}"/>')

    # back plates (seen from behind) and the seam gap
    R(-40, 40, 3.6, 19, "print")
    R(-40, 40, -19, -3.6, "print")
    o.append(f'<line x1="{n(X(-40))}" y1="{n(Y(0))}" x2="{n(X(40))}" y2="{n(Y(0))}" class="ghost"/>')
    # frame snap legs in the seam band
    for sx in (-1, 1):
        for sy in (-1, 1):
            R(sx * 30.5, sx * 36.5, sy * 2.2, sy * 3.5, "print")
    # clip
    R(-29.5, 29.5, -10, 10, "bclip", rx=n(3 * k))
    for sy in (-1, 1):
        for sx in (-1, 1):
            R(sx * 12, sx * 30, sy * 7.5, sy * 8.5, "gapfill")
            # lug + window + tooth
            R(sx * 19, sx * 27, sy * 10, sy * 11.5, "print")
            R(sx * 20, sx * 26, sy * 10, sy * 10.8, "bclip")
    # straight keys on the far side of the clip (they sit in the back-plate grooves)
    for y0 in (5.8, -7.8):
        o.append(f'<rect x="{n(X(-26))}" y="{n(Y(y0 + 2.0))}" width="{n(52 * k)}" height="{n(2.0 * k)}" class="zone"/>')
    # bridge slot (on the far side of the clip)
    o.append(f'<rect x="{n(X(-28.2))}" y="{n(Y(0.45))}" width="{n(56.4 * k)}" height="{n(0.9 * k)}" class="zone"/>')
    # dimensions
    o.append(f'<path d="M{n(X(-29.5))},{n(Y(-13.5))} H{n(X(29.5))} M{n(X(-29.5))},{n(Y(-12.5))} V{n(Y(-14.5))} M{n(X(29.5))},{n(Y(-12.5))} V{n(Y(-14.5))}" class="dim"/>')
    o.append(text(X(0), Y(-13.5) + 14, "≈59 mm (holds the 56 mm bridge)", "t-xs t-muted", "middle"))
    o.append(f'<path d="M{n(X(-33))},{n(Y(10))} V{n(Y(-10))} M{n(X(-34))},{n(Y(10))} H{n(X(-32))} M{n(X(-34))},{n(Y(-10))} H{n(X(-32))}" class="dim"/>')
    o.append(text(X(-34) - 4, Y(5) + 4, "20 mm", "t-xs t-muted", "end"))
    o.append(text(X(0), Y(16.5), "panel A back plate", "t-xs t-muted", "middle"))
    o.append(text(X(0), Y(-16.5) + 6, "panel B back plate", "t-xs t-muted", "middle"))
    lx = 650
    notes = [
        ("Keys (dashed)", "straight-sided ribs with a chamfered top sit in grooves in both back plates and carry the pull between panels"),
        ("Snap arms and teeth", "only keep the clip on; they carry no sideways load"),
        ("No play, no pop-off", "keys are a close fit in their grooves (tuned on a test print); straight sides mean a pull never pushes the clip off, even with one panel"),
        ("Lugs", "within 27 mm of the centre and 11.5 mm of the seam, so every shape has them"),
        ("Legs", "the frame's snap legs sit just past the clip ends"),
    ]
    wrapped_notes(o, lx, 30, notes, width=40, gap=14)
    o.append("</svg>")
    return "".join(o)


def fig_plan_shapes():
    import math
    s_ = 3.0
    seam, cy = 230, 200
    X = lambda u: seam + u * s_          # u: mm from the seam, + into the triangle
    Y = lambda v: cy - v * s_
    o = ['<svg viewBox="0 0 960 400" role="img" aria-label="Planned universal clip, zoomed in on a seam between a hexagon (left) and a triangle (right), seen from the front, to scale. The clip and its four lugs fit inside both shapes, near the triangle’s narrow corners. On the triangle the controller sits along this seam, so a thin cross-bar across the bottom of its pocket carries the lugs.">',
         '<defs><clipPath id="shapes-win"><rect x="20" y="20" width="480" height="360"/></clipPath></defs>',
         '<g clip-path="url(#shapes-win)">']

    def poly_pts(cu, R, angles):
        return " ".join(f"{n(X(cu + R * math.cos(math.radians(a_))))},{n(Y(R * math.sin(math.radians(a_))))}" for a_ in angles)

    hex_a = [30 + 60 * i for i in range(6)]
    tri_a = [0, 120, 240]
    o.append(f'<polygon points="{poly_pts(-86.6, 100, hex_a)}" class="ghost"/>')
    o.append(f'<polygon points="{poly_pts(28.87, 57.74, tri_a)}" class="ghost"/>')
    o.append(f'<polygon points="{poly_pts(-86.6, (86.6 - 4.3) / math.cos(math.radians(30)), hex_a)}" class="ring"/>')
    o.append(f'<polygon points="{poly_pts(28.87, (28.87 - 4.3) / math.cos(math.radians(60)), tri_a)}" class="ring"/>')

    def R(u0, u1, v0, v1, cls, extra=""):
        a_, b_ = sorted((u0, u1)); c_, d_ = sorted((v0, v1))
        o.append(f'<rect x="{n(X(a_))}" y="{n(Y(d_))}" width="{n((b_ - a_) * s_)}" height="{n((d_ - c_) * s_)}" class="{cls}"{extra}/>')

    base, top = 36.0, 22.14
    o.append(f'<polygon points="{n(X(5.3))},{n(Y(base))} {n(X(5.3))},{n(Y(-base))} {n(X(29.3))},{n(Y(-top))} {n(X(29.3))},{n(Y(top))}" class="pcb" opacity="0.45"/>')
    R(5.6, 12.0, -32.5, 32.5, "print")
    R(-10, 10, -29.5, 29.5, "bclip")
    for su in (-1, 1):
        for sv in (-1, 1):
            R(su * 10, su * 11.5, sv * 19, sv * 27, "chip")
    o.append(f'<line x1="{n(X(0))}" y1="{n(Y(70))}" x2="{n(X(0))}" y2="{n(Y(-70))}" class="ghost"/>')
    o.append("</g>")
    o.append('<rect x="20" y="20" width="480" height="360" class="hatch"/>')
    o.append(text(X(-40), Y(-40), "hexagon", "t-sm t-muted", "middle"))
    o.append(text(X(40), Y(-48), "triangle", "t-sm t-muted", "middle"))
    o.append(text(X(20), Y(-2), "controller", "t-xs t-muted", "middle"))
    for (u, v, t) in [(10.75, 23, "lug"), (10.75, 32.5, "cross-bar")]:
        o.append(f'<line x1="{n(X(u))}" y1="{n(Y(v))}" x2="{n(X(u) + 60)}" y2="{n(Y(v) - 14 if v > 30 else Y(v) + 14)}" class="w-leader"/>')
        o.append(text(X(u) + 64, (Y(v) - 14 if v > 30 else Y(v) + 14) + 4, t, "t-xs"))
    notes = [
        ("One clip for every pair", "lugs within 27 mm of the seam centre and 11.5 mm of the seam fit even the triangle, whose corners close in here"),
        ("Controller side", "the pocket is open to the wall, so a cross-bar (z −1.3 to 2.2) carries the key groove and the tooth notches"),
        ("Clear of the parts", "the joint is soldered before the back plate goes in; parts above the bar end at z ≥ 2.5 (to confirm), and the inductor is far away"),
        ("Snap legs", "the frame's legs (|x| 30–36.5) sit beyond the 59 mm clip, so both stay"),
    ]
    wrapped_notes(o, 540, 50, notes, width=44, gap=20)
    o.append("</svg>")
    return "".join(o)


def fig_plan_edge():
    k = SEAM_K
    X = lambda y: 160 + (y + 16) * k
    Z = lambda z: 20 + (17 - z) * k
    o = ['<svg viewBox="0 0 960 330" role="img" aria-label="Planned edge cover on a free edge of a cluster: it snaps into the same lugs as a bridge clip and rises in the seam band to cover the exposed contact pads, up to just below the frame\'s exterior wall.">']

    def R(y0, y1, z0, z1, cls):
        a, b = sorted((y0, y1)); c, d = sorted((z0, z1))
        o.append(f'<rect x="{n(X(a))}" y="{n(Z(d))}" width="{n((b - a) * k)}" height="{n((d - c) * k)}" class="{cls}"/>')

    R(-16, -5.35, -1.3, 6.6, "print"); R(-5.35, -3.6, -1.3, 0, "print")
    R(-11.5, -10, -1.9, -1.3, "print"); R(-11.5, -10, -4.3, -3.3, "print"); R(-10.8, -10, -3.3, -1.9, "bclip")
    R(-5.1, -3.5, 0, 13.5, "pcb"); R(-3.5, -3.38, 0.3, 6.0, "finger"); R(-6.7, -5.1, 7.37, 12.23, "led")
    R(-3.35, -0.3, 7.5, 13.65, "print"); R(-6.1, -0.3, 13.65, 15.65, "print"); R(-6.1, -5.25, 12.8, 13.65, "print")
    # edge cover: plate + wall in the seam band
    R(-10, -0.3, -4.3, -1.3, "bclip"); R(-8.5, -7.5, -4.3, -1.3, "gapfill"); R(-1.9, -0.3, -1.3, 7.4, "bclip")
    o.append(f'<polygon points="{key_pts(X, Z, -1)}" class="bclip"/>')
    lx = 520
    for i, (z, y, t) in enumerate([(3.0, -1.1, "cover wall closes the seam band below the frame wall"),
                                   (3.2, -3.44, "exposed contact pads, +24V among them"),
                                   (-2.6, -10.4, "same lugs as a bridge clip"),
                                   (-3.0, -6.0, "edge cover snaps on like half a clip")]):
        ly = 60 + i * 50
        o.append(f'<line x1="{n(lx - 4)}" y1="{n(ly - 4)}" x2="{n(X(y))}" y2="{n(Z(z))}" class="w-leader"/>')
        o.append(text(lx, ly, t, "t-xs"))
    o.append(text(X(-8), Z(16.6), "panel on a free edge", "t-sm t-strong", "middle"))
    o.append("</svg>")
    return "".join(o)


def mech_plan():
    stack = "".join(f"<tr><td class=\"num\">{a}</td><td>{b}</td></tr>" for a, b in [
        ("−4.3", "Back of the panel: bottoms of the clips and lugs. Dual Lock pads stick here."),
        ("−2.0 → 7.0", "Bridge PCB, standing in the seam."),
        ("−1.3 → 1.2", "Clip-recess ceiling and the clip's top face (3.0 mm clip base); the clip's straight-sided keys rise 2.5 mm into grooves, up to z 1.2."),
        ("0 → 13.5", "Edge boards, a soldered ring of six."),
        ("3.5", "Spring contact point on the pads (no vias below 5.3)."),
        ("5.0 → 6.6", "Controller board, its top flush with the floor."),
        ("6.6", "Chamber floor (back-plate top)."),
        ("7.4 → 12.2", "LEDs."),
        ("12.8 → 15.65", "Frame lip and groove, then the 2 mm cap. The film sits on top, clamped by the bezel (no riser)."),
    ])
    return "".join([
        sec("mech-1", "1 · How it fits together", "The planned panel and cluster mechanics",
            f"""<p>Planned in decisions 0012–0014 and accepted by the user on 2026-11-21; the parts get modelled in SolidCraft next (<code>mechanical/solidcraft/</code>). Inside a panel, the six edge boards are sandwiched between the frame's groove at the top and the back plate's tabs at the bottom. Between panels, a rigid <b>bridge clip</b> holds them together: straight-sided keys on the clip sit in grooves in both back plates and carry the pull between panels, while small snaps only keep the clip on. The clip sets the seam width exactly; the bridge springs only make contact. A few panels hold the whole cluster on the wall with Dual Lock.</p>
  <figure><div class="fig-scroll">{fig_plan_seam()}</div>
  <figcaption>Section through a seam at a snap tooth, heights to scale. The grey band at the bottom is the wall; the dotted boxes are Dual Lock pads (in reality on the panel's back plate, away from the clip; drawn close here). The clip goes on from the back, so the springs wipe the pads from the wall edge and GND still mates first.</figcaption></figure>
  <div class="tbl-wrap"><table><thead><tr><th>z (mm)</th><th>What</th></tr></thead><tbody>{stack}</tbody></table></div>"""),
        sec("mech-2", "2 · The bridge clip", "Snap-fit, no screws, no play",
            f"""<p>Same principle as Nanoleaf's linkers: something rigid sitting in slots in both panels takes the pull, and a light snap only keeps it in. Here the rigid part is a pair of straight-sided keys (chamfered at the top for lead-in) in back-plate grooves; the snap teeth in the lug windows keep the clip on and come free with a small screwdriver. The clip goes on from the back, because the bridge springs must slide onto the pads from the wall edge.</p>
  <p class="step-desc">Corrected on 2026-11-21: the first version located the panels only through the snap arms, which pushed the panels apart and let them slide off the teeth. The keys fix that.</p>
  <p class="step-desc">Printing: the back plate prints floor-down (lugs pointing up) and the clip prints bottom-down. The tooth and window latch faces slope about 25° from horizontal, so nothing needs support trapped inside the part (rule: overhangs up to 70°; steeper only with support standing on the bed). Keys are straight-sided, not tapered, so a pull between panels never pushes the clip off (a taper would, especially with only one panel attached). Zero play comes from a close key-in-groove fit, tuned on a test print.</p>
  <figure><div class="fig-scroll">{fig_plan_clip()}</div>
  <figcaption>Seen from the wall side. The first SolidCraft pass (88 mm, lugs at |x| 34–44) only fit a hexagon; the planned clip is about 59 mm long so it fits every shape.</figcaption></figure>"""),
        sec("mech-3", "3 · Every shape, and the controller side", "One clip for any pair of shapes",
            f"""<figure><div class="fig-scroll">{fig_plan_shapes()}</div>
  <figcaption>Zoomed in on a seam between a hexagon and a triangle, seen from the front, to scale. Blue: the clip; small marks: its four lugs; grey bar: the cross-bar that carries the lugs where the triangle's controller pocket is open to the wall; shaded trapezoid: the triangle's controller.</figcaption></figure>"""),
        sec("mech-4", "4 · Free edges", "Covering the pads on the outside of a cluster",
            f"""<figure><div class="fig-scroll">{fig_plan_edge()}</div>
  <figcaption>Without a neighbour, a panel's contact pads (including +24V) would sit uncovered below the frame wall. An edge cover uses the same lugs as a clip and closes the seam band.</figcaption></figure>"""),
        sec("mech-5", "5 · Build order", "From a ring of boards to a cluster on the wall", """<ol class="plain">
    <li><b>Ring:</b> solder the six edge boards into a ring, with the frame as the jig.</li>
    <li><b>Controller:</b> solder it at 90° to the code-0 board and seat it in the back-plate pocket.</li>
    <li><b>Close the panel:</b> snap the back plate into the frame's legs, then fit the film and the bezel (no riser).</li>
    <li><b>Join panels:</b> lay the panels face down, set each bridge in its clip and push the clip onto the seam until all four teeth click. Fit edge covers on free edges.</li>
    <li><b>Hang:</b> press the finished cluster onto Dual Lock pads on the wall. To add a panel later, take the cluster down first (accepted by the user).</li>
  </ol>
  <p class="step-desc">Still to design: the injection bridge's fuse relief and supply-wire exit through its clip, and how the bridge is held in the slot (snug fit or glue). Soldering and assembly jigs are roadmap item 2.3.</p>"""),
    ])


ROUTER = """
(function(){
  const VIEWS = __VIEWS__;
  function readHash(){ try { return decodeURIComponent((location.hash || '').slice(1)); } catch (e) { return ''; } }
  function writeHash(h){
    // Webviews and preview panes may block or ignore history changes; switching pages must not depend on them.
    try { history.replaceState(null, '', '#' + h); } catch (e) {}
  }
  function show(h, scroll){
    let v = VIEWS.includes(h) ? h : null, target = null;
    if (!v && h){ target = document.getElementById(h); const vw = target && target.closest('.view'); if (vw) v = vw.dataset.view; }
    v = v || VIEWS[0];
    document.querySelectorAll('.view').forEach(el => { el.hidden = el.dataset.view !== v; });
    document.querySelectorAll('.tabs a').forEach(a => a.setAttribute('aria-current', a.dataset.view === v ? 'page' : 'false'));
    if (!scroll) return;
    if (target) target.scrollIntoView(); else window.scrollTo(0, 0);
  }
  // Handle every in-page link directly, so tabs and cross-page links work without hash navigation.
  document.addEventListener('click', function(ev){
    const a = ev.target.closest && ev.target.closest('a[href^="#"]');
    if (!a || ev.defaultPrevented || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    const h = decodeURIComponent(a.getAttribute('href').slice(1));
    if (!h || !(VIEWS.includes(h) || document.getElementById(h))) return;
    ev.preventDefault();
    show(h, true);
    writeHash(h);
  });
  window.addEventListener('hashchange', function(){ show(readHash(), true); });
  show(readHash(), !!readHash());
})();
"""


def sec(sid, num, title, body):
    return f'<section aria-labelledby="{sid}">\n  <div class="num">{num}</div>\n  <h2 id="{sid}">{title}</h2>\n  {body}\n</section>\n'


def retag(s, old_id, new_id, num):
    s = s.replace(f'aria-labelledby="{old_id}"', f'aria-labelledby="{new_id}"').replace(f'id="{old_id}"', f'id="{new_id}"')
    return re.sub(r'<div class="num">[^<]*</div>', f'<div class="num">{num}</div>', s, count=1)


def toc(items):
    return '<nav class="toc" aria-label="Sections on this page">' + "".join(f'<a href="#{i}">{t}</a>' for i, t in items) + "</nav>"


def assemble(old, js, lo_sum, hi_sum, parts, cert_rows):
    S = {m.group(2): m.group(1) for m in re.finditer(r'(<section aria-labelledby="([^"]+)">.*?</section>)', old, re.S)}
    head = old[: old.index("<main>")]

    # ---------------- hardware
    disc = S["s5"]
    cut = disc.index("<p>The cluster controller gives every panel a turn.")
    disc_hw = disc[:cut] + '<p class="prose">How the controller will run a full discovery round is planned on the <a href="planning.html#fw-3">planning page</a> (firmware).</p>\n</section>'
    disc_fw = disc[cut:]
    hw_changes = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in COMMERCIAL_CHANGES if a not in ("Setup", "Updates"))
    hw_product = f"""<p>The personal-build design works as a prototype for a product, but a product changes the economics and the paperwork. The core problem is price: comparable modular panel kits sell for very roughly $15–25 per panel, and retail is typically 3–4× the landed cost of materials. That puts the target material cost near $5–8 per hexagon, against about ${lo_sum:.0f}–{hi_sum:.0f} today. The gap is spread across the fixed per-panel parts: edge PCBs, the controller board, LEDs and bridges.</p>
  <div class="facts">
    <div class="fact"><b>${lo_sum:.0f}–{hi_sum:.0f}</b><span>material cost per hexagon now</span></div>
    <div class="fact"><b>≈$5–8</b><span>target material cost for retail pricing</span></div>
    <div class="fact"><b>$15–60k</b><span>moulding tooling per part family (rough)</span></div>
    <div class="fact"><b>$15–40k</b><span>certification testing, one-time (rough)</span></div>
  </div>
  <h3 class="sub">Hardware changes from personal build to product</h3>
  <div class="tbl-wrap"><table><thead><tr><th>Area</th><th>Personal build</th><th>Product</th></tr></thead><tbody>{hw_changes}</tbody></table></div>
  <h3 class="sub">Certification and compliance</h3>
  <div class="tbl-wrap"><table><thead><tr><th>Requirement</th><th>Applies to</th><th>What it means here</th></tr></thead><tbody>{cert_rows}</tbody></table></div>
  <p class="step-desc">A starting map, not legal advice. Confirm scope with a test lab before design freeze. Firmware and software obligations are on their own pages.</p>
  <div class="cols">
    <div><h3 class="sub">Reliability testing</h3><ul class="plain">
      <li>Connector mating cycles and contact resistance over life.</li>
      <li>Thermal cycling at full white in a closed panel.</li>
      <li>LED failure rate against the warranty period.</li>
      <li>Mounting on painted drywall, plaster, tile and textured walls; ceiling pull-out force.</li>
      <li>Shipping drop tests and packaging.</li></ul></div>
    <div><h3 class="sub">Business and legal</h3><ul class="plain">
      <li><b>Patent freedom-to-operate search before any investment.</b> Established brands hold patents on connectable light panels and layout detection.</li>
      <li>Trademark, company formation, product liability insurance.</li>
      <li>Minimum order quantities and the cash to hold inventory.</li>
      <li>Validate demand first, for example with a crowdfunding campaign.</li>
      <li>Sales channels, returns handling and retailer requirements.</li></ul></div>
  </div>
  <p class="prose"><b>Where it could stand out:</b> most current products map a layout in 2D on one surface. Room-scale effects that run continuously across walls, ceilings and rooms, placed by an AR scan, are the differentiator worth protecting and demonstrating early.</p>"""
    hw_items = [
        '<p class="lede">What you can hold: the panels, the boards inside them, the bridges between them, power, and what it all costs.</p>',
        toc([("hw-parts", "Parts"), ("hw-1", "System"), ("hw-2", "Panel"), ("hw-proposal", "Edge + controller"), ("hw-reva", "Rev A renders"), ("hw-3", "Seam"), ("hw-insert", "Snapping in"), ("hw-geom", "Shapes"), ("hw-4", "Contacts"),
             ("hw-corner", "Corners"), ("hw-active", "Controller board"), ("hw-5", "ID circuit"), ("hw-6", "Power"), ("hw-7", "Cost"), ("hw-compare", "vs Nanoleaf"), ("hw-8", "Gaps"), ("hw-9", "Product")]),
        S["s-parts"].replace('aria-labelledby="s-parts"', 'aria-labelledby="hw-parts"').replace('id="s-parts"', 'id="hw-parts"').replace("<div class=\"parts\">", '<div class="parts">'),
        retag(S["s1"], "s1", "hw-1", "1 · Whole system"),
        retag(S["s2"], "s2", "hw-2", "2 · One panel"),
        f"""<section aria-labelledby="hw-proposal">
  <div class="num">3 · Edge boards and controller</div>
  <h2 id="hw-proposal">Passive edge boards, controller at the rear</h2>
  <p>Decided on 2026-11-16 (decisions 0009 and 0010). The controller moves off the edge boards onto a small board at the rear of the light chamber, and the supply bus goes from 12 V to 24 V.</p>
  <ul class="plain">
    <li><b>All edge boards become identical passive 2-layer boards:</b> LEDs, ID diode and resistor, contact pads and lanes. No MCU on any edge board.</li>
    <li><b>A small controller daughter board</b> (MCU, CAN transceiver, 24 → 5 V converter, LED-rail switch, level shifter, 3.3 V regulator, protection) lies flat at the rear of the light chamber, inside the enclosure, on the printed back plate. The same board serves every shape, so it is a trapezoid sized to fit the triangle.</li>
    <li><b>It joins one edge board (the code-0 board) at 90°</b> with a row of about 10 pads, drag-soldered by hand. Small parts on both boards are still pasted and reflowed.</li>
    <li><b>With only LEDs left on the edge boards,</b> the lanes and bus can be split across both faces. The rev A edge board is 13.5 mm tall, down from 22 mm.</li>
    <li><b>24 V bus:</b> half the current through the bridge springs and lanes. The 24 → 5 V converter (TPS54360B) stays on; a small switch turns the LEDs off for standby. The CAN transceiver becomes a TCAN1044V that survives ±58 V faults.</li>
    <li><b>Minimum constraints:</b> lanes and the bus may run on either face. Only rules with a stated reason remain: contact pads in the springs' zone, GND mating first, DRIVE never next to +24V, +24V kept apart from +5V, and shared LED positions.</li>
  </ul>
  <figure><div class="fig-scroll">{fig_prop_side()}</div>
  <figcaption>Side cut through a panel, heights to scale. The controller's parts face the wall in a pocket of the back plate that is open through to the wall (its 4.5 mm inductor is the tallest part). Its white top is the chamber floor, ≈6.6 mm above the wall, and part of the reflector. The LEDs are centred in the 6.9 mm of board above it (centres at 9.8 mm), and the joint is soldered at the controller's underside.</figcaption></figure>
  <figure><div class="fig-scroll">{fig_prop_top()}</div>
  <figcaption>Seen from the front, to scale. One controller design serves every shape, so it is sized for the triangle: a trapezoid with 60° sides, about 72 mm at the base and 20–25 mm deep. A rectangle as long as the edge board would hit the triangle's walls. Squares and hexagons fit the same board with room to spare.</figcaption></figure>
  <figure><div class="fig-scroll">{fig_prop_board()}</div>
  <figcaption>Edge board target layout, heights to scale (length compressed). Contact pads stay on the exterior face. The +5V_LED lane, signal bus and controller joint use the inward face below the LEDs. Pad, LED and joint heights are from the rev A layout; lane positions are drawn schematically (exact copper: hardware/edge-board/LAYOUT-NOTES.md).</figcaption></figure>
  <div class="cols">
    <div><h3 class="sub">What it replaced</h3><ul class="plain">
      <li>Decision 0006 (4-layer active edge board) is replaced: the 4-layer stack moves to the daughter board, and all edge boards are one 2-layer design per shape.</li>
      <li>Decision 0005 (22 mm height, bus on the exterior face) is replaced by the split-face layout above.</li>
      <li>The shared layout core no longer has to fit an MCU into the 82 mm triangle board.</li>
      <li>The PCB session's active-board routing stops and restarts on the new boards.</li>
    </ul></div>
    <div><h3 class="sub">Still to verify</h3><ul class="plain">
      <li>The contact strip shrinks from 8.5 to about 6 mm, so the bridge springs must touch lower; the bridge prototype checks it.</li>
      <li>A shallower chamber makes hot spots more likely. The frame could hold the diffuser a little above the boards if the optics test needs more mixing distance.</li>
      <li>Height: 13.5 mm (rev A layout). The controller's 4.5 mm inductor sets a ≈6.6 mm chamber floor; the LEDs are centred above it, at 9.8 mm. 13 mm left the bus unroutable past the controller joint.</li>
      <li>Cost: about $9–18 per hexagon. Cheaper edge boards roughly offset the 24 V parts.</li>
    </ul></div>
  </div>
</section>""",
        render_gallery("boards"),
        retag(S["s3"], "s3", "hw-3", "4 · The seam"),
        sec("hw-insert", "5 · Snapping in", "How a panel joins its neighbour", f"""<p>Bridges go into their carriers on the wall first. Each panel is then pushed straight toward the wall. Its bevelled bottom edge rides over the springs, which are mounted with their free ends toward the wall so they fold out of the way instead of snagging.</p>
  <figure><div class="fig-scroll">{fig_insert()}</div>
  <figcaption>The GND pads reach closest to the wall edge, so they meet their springs first and the signals connect last. The carrier and the panel's snap fit take the force; the springs only carry current.</figcaption></figure>"""),
        sec("hw-geom", "6 · Panel shapes", "Why each shape has its own board length", f"""<p>The seam bridge needs a fixed gap, so on every panel the boards' exterior faces sit the same distance d (half the seam, ≈3.5 mm) inside the seam centreline. Pulling a side in by a fixed distance shortens it more at sharp corners than at wide ones, so the board length depends on the shape: L_board = L − 2(d + t) / tan(α/2), where t is the board thickness and α the corner angle.</p>
  <figure><div class="fig-scroll">{fig_geometry()}</div>
  <figcaption>Dashed: the seam centreline, 100 mm per side on every shape. Solid: the edge boards, inset by d, drawn about three times too large so it's visible. Lengths assume d = 3.5 mm and get recalculated once the spring stack is measured.</figcaption></figure>
  <ul class="plain">
    <li><b>One design, three outlines.</b> The contacts, LEDs, ID circuit and controller-joint pads sit in a layout core centred on the board and sized to fit the triangle. Longer boards just extend their ends to the corner joints.</li>
    <li><b>Bridges stay universal.</b> Each contact strip is centred on its side, and the middle of every inset side lands on the middle of its seam, so contacts line up between any two shapes.</li>
    <li><b>Board height: 13.5 mm in rev A</b> (target was 10–15 mm, decision 0009). With the controller on its own board, the edge boards carry only LEDs, the ID circuit and lanes. The optics test confirms the depth.</li>
    <li><b>Hexagons first.</b> Rev A builds only the ≈94.1 mm hexagon board. Square and triangle outlines come later from the same core.</li>
  </ul>"""),
        retag(S["s4"], "s4", "hw-4", "7 · Edge contacts"),
        sec("hw-corner", "8 · Corners", "Corner joints inside a panel", f"""<p>Where two boards of the same panel meet, each board end has SMD pads that touch the end of the board: five signal pads on the inward face, and +5V, GND and +24V on the exterior face, in that order so GND always separates the two supplies (a +24V-to-+5V short would destroy the panel's LEDs). A solder bead bridges the signal pads across the inner corner, and a bent strap or solder bridge joins the power pads across the outside corner. The left end (corner IN) and right end (corner OUT) use mirror-image footprints.</p>
  <figure><div class="fig-scroll">{fig_corner()}</div>
  <figcaption>On the code-0 board, the corner-IN data pad feeds the controller's loopback input instead of LED1. Corner joints are still finished by hand; designing that out is gap A3.</figcaption></figure>"""),
        sec("hw-active", "9 · Controller board", "What the controller board does", f"""<p>One small 4-layer board per panel, at the rear of the light chamber. It makes 5 V and 3.3 V from the 24 V bus, switches the LED rail, talks CAN, drives the LEDs, counts the loopback, and runs discovery. It joins the code-0 edge board through ≈10 drag-soldered pads.</p>
  <figure><div class="fig-scroll">{fig_active()}</div>
  <figcaption>Parts and pins from SPEC V6.0 §3.2. Every bus line survives a sustained 24 V short (decision 0011).</figcaption></figure>"""),
        retag(disc_hw, "s5", "hw-5", "10 · ID circuit"),
        retag(S["s7"], "s7", "hw-6", "11 · Power"),
        retag(S["s10"], "s10", "hw-7", "12 · Cost"),
        sec("hw-compare", "13 · Compared with Nanoleaf", "Parts cost and brightness against Nanoleaf", f"""<p>Our numbers are parts cost for a personal build; Nanoleaf's are retail kit prices, which include a controller, power supply, app, warranty and support. On parts alone we come in at roughly half to the same price per m², and likely 2–3× cheaper per unit of light, because 12–18 full-size LEDs per panel put out more raw light than Nanoleaf's 1–2 W panels. Our brightness is an estimate until the optics test measures it.</p>
  <figure><div class="fig-scroll">{fig_compare()}</div>
  <figcaption>Ranges, not single prices: ours spans the cost estimate and the brightness uncertainty; Nanoleaf's spans retailer and kit-size pricing. Hover a row for details.</figcaption></figure>
  <div class="tbl-wrap"><table>
    <thead><tr><th></th><th>Ours (100 mm hexagon, parts)</th><th>Nanoleaf Shapes Hexagon</th><th>Nanoleaf Canvas (square)</th></tr></thead>
    <tbody>
      <tr><td><b>Panel size</b></td><td>0.026 m²</td><td>0.034 m² (23 × 20 cm)</td><td>0.0225 m² (15 × 15 cm)</td></tr>
      <tr><td><b>Price per panel</b></td><td class="num">$9–18</td><td class="num">≈$21–29</td><td class="num">≈$11–14</td></tr>
      <tr><td><b>Price per m²</b></td><td class="num">≈$335–690</td><td class="num">≈$620–830</td><td class="num">≈$490–640</td></tr>
      <tr><td><b>Light per panel</b></td><td class="num">≈50–250 lm (est.)</td><td class="num">100 lm (rated)</td><td class="num">44 lm (rated)</td></tr>
      <tr><td><b>Light per m²</b></td><td class="num">≈1,900–9,700 lm</td><td class="num">≈2,900 lm</td><td class="num">≈2,000 lm</td></tr>
      <tr><td><b>Price per 100 lm</b></td><td class="num">≈$3–36 (mid ≈$10)</td><td class="num">≈$21–29</td><td class="num">≈$25–33</td></tr>
      <tr><td><b>Power per panel, full white</b></td><td class="num">≈4 W</td><td class="num">2 W</td><td class="num">1 W</td></tr>
    </tbody>
  </table></div>
  <div class="cols">
    <div><h3 class="sub">Why our brightness range is wide</h3><ul class="plain">
      <li>No full-white lumen rating exists for the SKC6812RGBW. Its white channel is rated about 2.5 cd (roughly 8 lm), and vendor claims for similar 5050 chips are about 20 lm per LED. The estimate uses 8–20 lm per LED.</li>
      <li>Edge lighting through diffuser film loses light; the estimate assumes 50–70% gets out.</li>
      <li>Nanoleaf gets more light per watt (≈50 lm/W against our rough 15–60 lm/W); the RGBW white channel narrows the gap compared with mixing white from RGB.</li>
    </ul></div>
    <div><h3 class="sub">What our numbers leave out</h3><ul class="plain">
      <li>Shipping and import duties, often 15–40% more.</li>
      <li>Assembly time, printer hours, prototypes and spares.</li>
      <li>The risk of a first-generation design, against a finished product with an app, warranty and support.</li>
    </ul></div>
  </div>
  <p class="step-desc">Nanoleaf prices vary by region and date. Sources: <a href="https://www.bestbuy.com/product/nanoleaf-shapes-hexagons-smarter-kit-7-panels-multicolor/J39HJ954F2">Best Buy (Shapes kit)</a>, <a href="https://www.techadvisor.com/article/721788/nanoleaf-shapes-hexagons-review-2.html">Tech Advisor</a>, <a href="https://www.crutchfield.com/ISEO-rCCBcSPD/p_700NLHXEXP/Nanoleaf-Shapes-Expansion-Pack-6-Hexagons.html">Crutchfield</a>, <a href="https://www.adorama.com/nl293sw9pkb.html">Adorama (Canvas kit)</a>, <a href="https://jbhifi.com.au/products/nanoleaf-canvas-smarter-kit-9-panels">JB Hi-Fi</a>, <a href="https://mobilesyrup.com/2020/06/21/nanoleaf-light-panels-canvas-review/">MobileSyrup</a>, <a href="https://www.superlightingled.com/dc12v-rt1809-300ledssimilar-to-ws2815-individually-addressable-breakpoint-continue-5050-rgb-flexible-led-digital-strip-light-p-3954.html">Superlighting (5050 lumens claim)</a>, <a href="https://superlightingled.com/ws2815-individually-addressable-dream-color-rgb-led-strip-12v-p-2132.html">Superlighting (WS2815 power)</a>.</p>"""),
        sec("hw-8", "14 · Gaps", "What the hardware plan is still missing", '<p>Ordered by how much damage each does if it is found late. Tier A items get a cheap prototype before any custom boards are ordered.</p>' + page_gaps("hardware")),
        sec("hw-9", "15 · Product", "What it would take to sell this: hardware and business", hw_product),
    ]

    # ---------------- firmware
    fw_parts = "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in FW_PARTS)
    can_rows = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td></tr>" for a, b, c, d, e in [
        ("SYNC / LATCH", "1 (highest)", "controller → all", "SYNC 10 Hz; LATCH per frame", "timestamp; frame number"),
        ("Discovery", "2", "both", "during discovery", "DRIVE command; SENSE report (edge code, voltage)"),
        ("Effect descriptor", "3", "controller → all or a group", "on change", "effect slot, parameters, palette, t₀"),
        ("Stream samples", "4", "controller → node", "≤ 20 Hz", "one RGBW colour (4 bytes) per edge for simulated effects"),
        ("Config", "5", "controller → node", "rare", "address, shape, termination, brightness cap"),
        ("Node status", "6", "node → controller", "1 Hz", "supply voltage, temperature, errors, firmware version"),
        ("Bootloader", "7 (lowest)", "both", "during updates", "image chunks, CRC, acknowledgements"),
    ])
    fw = [
        '<p class="lede">The code on the chips: each panel\'s CH32V203 node firmware, its bootloader, and the ESP32 cluster controllers that run each CAN bus.</p>',
        toc([("fw-parts", "Parts"), ("fw-1", "Node firmware"), ("fw-2", "CAN protocol"), ("fw-3", "Discovery round"), ("fw-4", "Rendering"), ("fw-5", "Time sync"),
             ("fw-6", "Updates"), ("fw-7", "Controller"), ("fw-8", "Power modes"), ("fw-9", "Gaps"), ("fw-10", "Product")]),
        f'<section aria-labelledby="fw-parts"><h2 id="fw-parts">The pieces</h2><div class="parts">{fw_parts}</div></section>',
        sec("fw-1", "1 · Node firmware", "One small program per panel", f"""<p>Each panel runs the same firmware. It listens on CAN, takes part in discovery, evaluates the current effect for its 12–18 LEDs, and pushes colours out on the shared latch time. Everything is interrupt- and DMA-driven, so the CPU spends most of its time asleep or idle.</p>
  <figure><div class="fig-scroll">{fig_fw_arch()}</div>
  <figcaption>The bootloader is separate and never changes, so a failed update can always be retried. The dashed line is the LED-rail switch used for standby.</figcaption></figure>
  <div class="cols">
    <div><h3 class="sub">LED driver</h3><p class="prose">SPI1 with DMA generates the SK6812 bit timing on PA7 straight from the frame buffer, and an AHCT level shifter lifts it to the LEDs' 5 V logic. Each RGBW LED takes 32 bits, so sending 18 LEDs takes about 0.7 ms and almost no CPU.</p><p class="prose">The chain's end loops back to PA0 through a 2.2 kΩ / 3.3 kΩ divider (PA0 is not 5 V tolerant), where TIM2 counts the returned bits. Sending extra colour data and counting what returns (32 bits per LED) gives the LED count, the panel's edge count, and the position of any break. There is no backup data line, so a dead LED cuts the chain at that point.</p></div>
    <div><h3 class="sub">Frame builder</h3><p class="prose">Applies gamma, temporal dithering for smooth low-level fades, the per-panel brightness cap from the power budget, a flash limiter that caps how fast brightness may change, and splits each colour into RGB plus white for the RGBW LEDs.</p></div>
  </div>"""),
        sec("fw-2", "2 · CAN protocol", "Message classes, ordered by priority", f"""<p>Messages use 29-bit CAN IDs with the priority and class in the top bits, so bus arbitration always favours sync over bulk data. The target address or group sits in the low bits, so each node's hardware filters drop traffic that isn't for it. An 8 MHz crystal gives the clock accuracy CAN bit timing needs. CAN frames carry 8 bytes, so effect bytecode and firmware images are sent in numbered fragments.</p>
  <div class="tbl-wrap"><table><thead><tr><th>Class</th><th>Priority</th><th>Direction</th><th>Rate</th><th>Contents</th></tr></thead><tbody>{can_rows}</tbody></table></div>
  <p class="step-desc">A proposal for the protocol document in firmware/common/protocol/.</p>"""),
        retag(f'<section aria-labelledby="s5">\n  <div class="num">x</div>\n  <h2 id="s5">How the controller maps a whole cluster</h2>\n  <p>Before discovery, the controller enumerates nodes: each node bids with its 96-bit chip ID using CAN arbitration, the lowest ID wins and gets a short address, and the round repeats until no one is left. The <a href="#hw-5">ID circuit</a> on the Hardware page does the sensing.</p>\n  ' + disc_fw, "s5", "fw-3", "3 · Discovery round"),
        retag(S["s6"], "s6", "fw-4", "4 · Rendering").replace("</section>", f"""<div class="cols">
    <div><h3 class="sub">Effect VM</h3><ul class="plain">
      <li>Stack-based bytecode, Q16.16 fixed point; no FPU needed.</li>
      <li>Inputs: time, the LED's room position, path distance and gradient to named anchors, parameters, a random seed.</li>
      <li>Operations: arithmetic, sine and noise lookups, clamp, mix, palette lookup.</li>
      <li>Verified when loaded: bounded stack and loops, no memory access outside its sandbox, and an instruction budget per LED.</li>
    </ul></div>
    <div><h3 class="sub">Budget</h3><p class="prose">18 LEDs × 60 fps × 200 instructions is about 0.2 million instructions per second, a small fraction of a 144 MHz core. The same VM source is compiled to WebAssembly for the studio preview, so previews match the panels exactly.</p></div>
  </div>
</section>""", 1),
        sec("fw-5", "5 · Time sync", "Every panel changes on the same frame", f"""<p>The controller broadcasts SYNC with its clock about ten times a second, timestamped by the CAN hardware at start-of-frame. Each node trims its local clock to match. A node may finish computing a frame early or late, but it holds the result until the shared LATCH time.</p>
  <figure><div class="fig-scroll">{fig_sync()}</div>
  <figcaption>Target alignment is about 0.1 ms within a cluster and 2 ms across clusters. The coordinator keeps the controllers' clocks aligned over Wi-Fi.</figcaption></figure>"""),
        sec("fw-6", "6 · Updates", "Updating every panel at once", f"""<figure><div class="fig-scroll">{fig_flash()}</div>
  <figcaption>The bootloader is immutable. The application has a single slot; if it fails its check, the bootloader stays in update mode and asks again.</figcaption></figure>
  <ol class="plain">
    <li>The controller announces an image: version, size, CRC or signature.</li>
    <li>Nodes that need it acknowledge.</li>
    <li>The controller broadcasts the chunks once to all of them at the same time; nodes request any chunks they missed.</li>
    <li>Each node checks the image, writes it, and reboots.</li>
    <li>The bootloader checks again before starting the app.</li>
  </ol>
  <p class="prose">A 40 KB image broadcast over a 250 kbps bus takes a few seconds, whether the cluster has 5 panels or 50.</p>"""),
        sec("fw-7", "7 · Controller", "ESP32 cluster controller firmware", """<p>Built on ESP-IDF (FreeRTOS). One controller owns each cluster's CAN bus and is the cluster's link to the coordinator.</p>
  <div class="cols">
    <div><ul class="plain">
      <li><b>CAN gateway</b> on the built-in TWAI controller.</li>
      <li><b>Coordinator link</b> over Wi-Fi: effects and samples down, topology and status up.</li>
      <li><b>Discovery</b>: enumeration, turn scheduling, building the cluster map.</li>
      <li><b>Time-sync relay</b>: coordinator clock in, CAN SYNC out.</li>
    </ul></div>
    <div><ul class="plain">
      <li><b>Termination manager</b>: enables the far-end terminator once the topology is known.</li>
      <li><b>Power budget</b>: sets per-panel brightness caps so each domain stays within its supply.</li>
      <li><b>Updates</b>: stores node images and runs broadcast updates; updates itself with ESP-IDF's two-partition OTA.</li>
      <li><b>Setup and offline mode</b>: Wi-Fi setup over Bluetooth from the phone app; keeps playing the last scene, and a button cycles scenes, if the coordinator is unreachable.</li>
    </ul></div>
  </div>"""),
        sec("fw-8", "8 · Power modes", "From full brightness to nearly off", """<div class="tbl-wrap"><table><thead><tr><th>Mode</th><th>Node MCU</th><th>CAN transceiver</th><th>LED rail</th><th>Wakes on</th></tr></thead><tbody>
    <tr><td><b>Active</b></td><td>running</td><td>on</td><td>on</td><td>—</td></tr>
    <tr><td><b>Idle</b> (lights dark, ready)</td><td>sleeping between frames</td><td>on</td><td>on</td><td>any message</td></tr>
    <tr><td><b>Standby</b></td><td>deep sleep</td><td>standby</td><td>off</td><td>CAN bus activity</td></tr>
    <tr><td><b>Off</b></td><td>unpowered</td><td>unpowered</td><td>off</td><td>supply switched on</td></tr>
  </tbody></table></div>
  <p class="prose">Standby is what brings idle draw down from about 0.3–0.5 W per panel. The CAN transceiver's standby pin is on a GPIO, and a P-MOSFET switches the LED rail off; the 24 → 5 V buck stays on for the MCU and CAN.</p>"""),
        sec("fw-9", "9 · Gaps", "What the firmware plan is still missing", page_gaps("firmware")),
        sec("fw-10", "10 · Product", "Firmware for a product", """<ul class="plain">
    <li>Signed firmware for nodes and controllers, with secure boot on the ESP32.</li>
    <li>Staged rollouts, automatic rollback on the controller, and a fail-safe bootloader on the nodes.</li>
    <li>No default passwords, a vulnerability disclosure policy, and a stated support period (UK PSTI and the EU Cyber Resilience Act).</li>
    <li>Fault logs that support staff can read remotely, with the owner's consent.</li>
  </ul>"""),
    ]
    firmware = "".join(fw)

    # ---------------- software
    sw_parts = "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in SW_PARTS)
    sw_product_rows = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in COMMERCIAL_CHANGES if a in ("Setup", "Updates"))
    sw = [
        '<p class="lede">Everything above the controllers: the coordinator, the room model and voxel effects, the phone and desktop apps, and how people create and share effects.</p>',
        toc([("sw-parts", "Parts"), ("sw-1", "Architecture"), ("sw-2", "AR placement"), ("sw-3", "Between rooms"), ("sw-4", "Creating effects"),
             ("sw-5", "Publishing"), ("sw-6", "Apps"), ("sw-7", "Integrations"), ("sw-8", "Gaps"), ("sw-9", "Product")]),
        f'<section aria-labelledby="sw-parts"><h2 id="sw-parts">The pieces</h2><div class="parts">{sw_parts}</div></section>',
        sec("sw-1", "1 · Architecture", "One coordinator, three kinds of client", f"""<p>The coordinator is the only always-on software. It keeps the room model, compiles and checks effects, runs stateful simulations, and talks to every cluster controller. The phone app, the desktop studio and home automation are all clients of its API.</p>
  <figure><div class="fig-scroll">{fig_sw_arch()}</div>
  <figcaption>The control UI is a web app served by the coordinator, so the same screens work in a desktop browser and inside the phone apps. Only AR needs native phone code.</figcaption></figure>"""),
        retag(S["s8"], "s8", "sw-2", "2 · Room placement").replace("Section 11 has the details.", 'See <a href="#sw-8">Gaps</a>.'),
        retag(S["s9"], "s9", "sw-3", "3 · Between rooms"),
        sec("sw-4", "4 · Creating effects", "Three ways to make an effect", """<p>Every effect is written against the room, not against a particular layout. It refers to anchors (floor, ceiling, walls, doorways, room centres, named points) and to path distance through the building, so one effect runs in any home.</p>
  <div class="gaps">
    <article class="gap"><h4>Presets</h4><p>Pick a built-in effect, set its sliders and palette, choose which rooms or surfaces it covers, and save it as a scene. No code.</p></article>
    <article class="gap"><h4>Visual graph</h4><p>Wire blocks together: inputs (time, position, distance from an anchor, path distance, audio level, noise), maths (sine, mix, clamp) and colour (palette, hue shift). The graph compiles to node bytecode and previews live on your room.</p></article>
    <article class="gap"><h4>Script</h4><p>For stateful effects (particles, smoke, games, reactions to events) a sandboxed script runs on the coordinator with access to the voxel grid, panels and events such as a door sensor or a music beat. It streams samples to the panels.</p></article>
  </div>
  <ul class="plain">
    <li><b>White channel:</b> effects can set the white LED directly for clean whites, pastels and warm light, or let the panels derive it from RGB.</li>
    <li><b>Scenes and timelines:</b> sequence effects with transitions, and trigger them by time, sunrise or sunset, or events.</li>
    <li><b>Preview:</b> on your scanned room, or on sample rooms to check that an effect travels well before sharing it.</li>
  </ul>"""),
        sec("sw-5", "5 · Publishing", "From the editor to someone else's wall", f"""<figure><div class="fig-scroll">{fig_pipeline()}</div>
  <figcaption>Safety and budget checks run twice: once when publishing, and again on every coordinator that installs the effect.</figcaption></figure>
  <div class="cols">
    <div><h3 class="sub">Package manifest (example)</h3><pre class="code">{MANIFEST}</pre></div>
    <div><h3 class="sub">Gallery</h3><ul class="plain">
      <li>Browse by room type, mood and motion level, with preview clips.</li>
      <li>Install in one tap from the phone or the studio; packages can also be shared as files.</li>
      <li>Versions and remixes keep a record of where an effect came from.</li>
      <li>Licence choice at publish time; reports and takedowns for problems.</li>
      <li>Packages are signed by their author and re-checked locally on install.</li>
    </ul></div>
  </div>"""),
        sec("sw-6", "6 · Apps", "Phone and desktop", """<div class="cols">
    <div><h3 class="sub">Phone app</h3><ul class="plain">
      <li>Guided setup: Wi-Fi for each controller over Bluetooth, then a live discovery view.</li>
      <li>AR scan and placement, room by room.</li>
      <li>Point the camera at a panel to identify it, or tap one to make it blink.</li>
      <li>Everyday control: scenes, brightness, colour, per room.</li>
      <li>Gallery browsing and installs; a fault map with voltage drop and offline panels.</li>
    </ul></div>
    <div><h3 class="sub">Desktop studio</h3><ul class="plain">
      <li>3D room view with a live preview that runs the real effect VM.</li>
      <li>Graph editor and script editor with instant reload.</li>
      <li>Timeline for scenes and transitions.</li>
      <li>Publishing, device management, firmware updates and logs.</li>
    </ul></div>
    <div><h3 class="sub">Suggested stack</h3><ul class="plain">
      <li>One web UI served by the coordinator, used by both the desktop and the phone apps.</li>
      <li>Native AR modules only: Swift with ARKit and RoomPlan on iPhone, Kotlin with ARCore on Android.</li>
      <li>The node effect VM in portable C, built for the CH32V203 and for WebAssembly.</li>
    </ul></div>
  </div>"""),
        sec("sw-7", "7 · Integrations", "Fitting into the rest of the home", """<ul class="plain">
    <li><b>Home Assistant:</b> a local integration or MQTT discovery, exposing rooms, scenes and effects.</li>
    <li><b>Matter:</b> a bridge exposing each room or cluster as a light (on/off, brightness, colour).</li>
    <li><b>Schedules:</b> sunrise, sunset and circadian colour temperature.</li>
    <li><b>Events:</b> a motion or door sensor can start a ripple from that doorway.</li>
    <li><b>Audio-reactive:</b> levels from a phone, desktop microphone or line-in, streamed to the coordinator.</li>
    <li><b>Screen sync:</b> the desktop app samples the screen edges and streams colours to nearby clusters.</li>
  </ul>"""),
        sec("sw-8", "8 · Gaps", "What the software plan is still missing", page_gaps("software")),
        sec("sw-9", "9 · Product", "Software and service for a product", f"""<div class="tbl-wrap"><table><thead><tr><th>Area</th><th>Personal build</th><th>Product</th></tr></thead><tbody>{sw_product_rows}</tbody></table></div>
  <ul class="plain">
    <li>Native iOS and Android apps in the stores, with guided setup; AR placement as an upgrade, not a requirement.</li>
    <li>Local-first control, with optional cloud for remote access and the gallery.</li>
    <li>Integrations buyers expect: Matter, Apple Home, Google, Alexa, Home Assistant.</li>
    <li>Accounts, privacy policy, and data handling for the gallery and remote access.</li>
    <li>Cybersecurity obligations: UK PSTI, the EU Cyber Resilience Act, and optionally the US Cyber Trust Mark.</li>
    <li>Customer support, crash reporting, warranty returns and replacement panels.</li>
  </ul>"""),
    ]
    software = "".join(sw)

    def by_id(items):
        out = {}
        for it in items:
            m = re.search(r'<section aria-labelledby="([^"]+)"', it)
            if m:
                out[m.group(1)] = it
        return out
    H = by_id(hw_items)
    import re as _re
    prop = _re.sub(r'\s*<div class="cols">\s*<div><h3 class="sub">What it replaced</h3>.*?</div>\s*</div>\s*(?=</section>)', "", H["hw-proposal"], flags=_re.S)
    H["hw-show"], H["hw-boards3d"] = media_gallery("show"), media_gallery("boards3d")
    ref_ids = [("hw-show", "Showcase"), ("hw-parts", "Parts"), ("hw-1", "System"), ("hw-2", "Panel"), ("hw-proposal", "Edge + controller"), ("hw-boards", "Rev A boards"), ("hw-boards3d", "Boards in 3D"),
               ("hw-3", "Seam"), ("hw-geom", "Shapes"), ("hw-4", "Contacts"), ("hw-corner", "Corners"), ("hw-active", "Controller board"),
               ("hw-5", "ID circuit"), ("hw-6", "Power")]
    ref_body = "".join(['<p class="lede">The finished technical design: the boards as laid out, their contacts and joints, the controller, the ID circuit and power. Concepts still being worked out live on the <a href="planning.html">planning page</a>.</p>',
                        toc(ref_ids)] + [prop if i_ == "hw-proposal" else H[i_] for i_, _ in ref_ids])
    biz_ids = [("hw-7", "Cost"), ("hw-compare", "vs Nanoleaf"), ("hw-8", "Hardware gaps"), ("hw-9", "Product")]
    biz_body = "".join(['<p class="lede">What it costs, how it compares, what the hardware plan is still missing, and what selling it would take.</p>', toc(biz_ids)] + [H[i_] for i_, _ in biz_ids])
    mech_body = "".join(['<p class="lede">The planned mechanics: how panels are held together, joined to each other and hung. Conceptual until modelled; finished parts move to the design reference.</p>',
                         toc([("mech-1", "Fit"), ("mech-2", "Clip"), ("mech-3", "Shapes"), ("mech-4", "Free edges"), ("mech-5", "Build order"), ("mech-cad", "CAD"), ("mech-old", "Earlier concept")]),
                         mech_plan(), media_gallery("cad"), render_gallery("mech")])

    def router(views):
        return ROUTER.replace("__VIEWS__", json.dumps(views))

    legend = """  <div class="legend" aria-label="Colour key used in the diagrams">
    <span><i class="lg-power"></i>+24V power</span>
    <span><i class="lg-can"></i>CAN bus</span>
    <span><i class="lg-led"></i>LEDs and LED data</span>
    <span><i class="lg-sense"></i>SENSE / DRIVE ID lines</span>
    <span><i class="lg-wifi"></i>Wi-Fi</span>
  </div>"""
    ref_head = head.replace("<title>Modular Smart Light Panels</title>", "<title>Light Panels Reference</title>")
    plan_head = head.replace("<title>Modular Smart Light Panels</title>", "<title>Light Panels Planning</title>")
    import re as _re2
    _spec = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "SPEC.md"), encoding="utf-8").read(400)
    SPEC_VER = (_re2.search(r"\*\*Version:\*\* (V[\d.]+)", _spec) or [None, "?"])[1]
    ref_html = f"""{ref_head}<main>
<header>
  <div class="eyebrow">Design reference · spec {SPEC_VER} · finished design only</div>
  <h1>Modular Smart Light Panels</h1>
  <p class="lede">Edge-lit panels that snap together in any layout, work out their own arrangement, and play effects placed in the room rather than along a strip. <a href="planning.html">Planning page →</a></p>
  <nav class="tabs" aria-label="Pages">
    <a href="#hardware" data-view="hardware">Hardware</a>
  </nav>
{legend}
</header>
<div class="view" data-view="hardware" id="view-hardware">{ref_body}</div>
</main>
<script>{router(["hardware"])}</script>
"""
    plan_html = f"""{plan_head}<main>
<header>
  <div class="eyebrow">Planning · concepts and status · spec {SPEC_VER}</div>
  <h1>Modular Smart Light Panels</h1>
  <p class="lede">Everything still conceptual: the planned mechanics, firmware and software, cost, gaps and the path to a product. Finished design lives in the <a href="design-reference.html">design reference →</a></p>
  <nav class="tabs" aria-label="Pages">
    <a href="#mechanics" data-view="mechanics">Mechanics</a><a href="#firmware" data-view="firmware">Firmware</a><a href="#software" data-view="software">Software</a><a href="#business" data-view="business">Cost &amp; product</a>
  </nav>
{legend}
</header>
<div class="view" data-view="mechanics" id="view-mechanics">{mech_body}</div>
<div class="view" data-view="firmware" id="view-firmware" hidden>{firmware}</div>
<div class="view" data-view="software" id="view-software" hidden>{software}</div>
<div class="view" data-view="business" id="view-business" hidden>{biz_body}</div>
</main>
<script>{router(["mechanics", "firmware", "software", "business"])}</script>
<script>{js}</script>
"""
    return ref_html, plan_html


if __name__ == "__main__":
    build()
