"""Controller board: finish the connections Freerouting left open, on In2.Cu, with a small grid A* router;
then stitch any F.Cu GND pour island that has no via. Runs after layout_finish.py.

usage (KiCad 9 python):  python layout_fixups.py      (edits controller-board.kicad_pcb in place)

Each job is (net, endpoint A, endpoint B). An endpoint is an existing via of that net (x, y), or
('pad', 'REF.N', (x, y)): a new via at (x, y) (checked free on all layers) plus a short F.Cu stub to the pad.
The router keeps every In2 track >= 0.2 mm from other-net copper (tracks, vias, through-pads) and 0.5 mm from
the board edge; GND pour copper is ignored (it is refilled around the new tracks).
"""
import heapq
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_quiet  # noqa: F401
import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, '..', '..', 'controller-board.kicad_pcb'))
X0, Y0 = 100.0, 100.0
BASE, DEPTH = 72.0, 24.0
TAN30 = math.tan(math.radians(30))
TOPHALF = BASE / 2 - DEPTH * TAN30
G = 0.1                       # grid (mm)
TW, CL, VD = 0.2, 0.2, 0.6    # track width, clearance, via diameter

b = pcbnew.LoadBoard(PCB)
tm = lambda v: (pcbnew.ToMM(v.x) - X0, Y0 - pcbnew.ToMM(v.y))


def P(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(float(X0 + x)), pcbnew.FromMM(float(Y0 - y)))


# ------------------------------------------------------------------------------ obstacle model
# shapes: ('seg', net, layer, (x0,y0), (x1,y1), halfwidth) | ('circ', net, layers, (x,y), r) | ('rect', net, layer, x0,y0,x1,y1)
shapes = []
ALL = {'F', 'In2'}
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        shapes.append(('circ', t.GetNetname(), ALL, tm(t.GetPosition()), pcbnew.ToMM(t.GetWidth()) / 2))
    elif t.GetLayer() in (pcbnew.F_Cu, pcbnew.In2_Cu):
        shapes.append(('seg', t.GetNetname(), 'F' if t.GetLayer() == pcbnew.F_Cu else 'In2', tm(t.GetStart()),
                       tm(t.GetEnd()), pcbnew.ToMM(t.GetWidth()) / 2))
for fp in b.GetFootprints():
    for pd in fp.Pads():
        bb = pd.GetBoundingBox()
        x0, y1 = tm(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
        x1, y0 = tm(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
        if pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            shapes.append(('circ', pd.GetNetname(), ALL, tm(pd.GetPosition()), (x1 - x0) / 2))
        elif pd.IsOnLayer(pcbnew.F_Cu):
            shapes.append(('rect', pd.GetNetname(), 'F', x0, y0, x1, y1))


def dist_seg(px, py, a, c):
    ax, ay = a
    cx, cy = c
    dx, dy = cx - ax, cy - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def dist_shape(px, py, s):
    if s[0] == 'seg':
        return dist_seg(px, py, s[3], s[4]) - s[5]
    if s[0] == 'circ':
        return math.hypot(px - s[3][0], py - s[3][1]) - s[4]
    x0, y0, x1, y1 = s[3:]
    dx = max(x0 - px, 0, px - x1)
    dy = max(y0 - py, 0, py - y1)
    return math.hypot(dx, dy)


def on_layer(s, lay):
    return lay in s[2] if s[0] == 'circ' else s[2] == lay


def inside_board(x, y, m):
    if y < m or y > DEPTH - m:
        return False
    hw = BASE / 2 - y * TAN30 - m / math.cos(math.radians(30))
    return abs(x) <= hw


def via_free(x, y, net):
    if not inside_board(x, y, 0.8):
        return False
    for s in shapes:
        if s[1] == net:
            continue
        lay_hit = s[0] == 'circ' or s[2] in ('F', 'In2')
        if lay_hit and dist_shape(x, y, s) < VD / 2 + CL + 0.02:
            return False
    return True


# ------------------------------------------------------------------------------ grid router (In2)
NX, NY = int((BASE + 4) / G), int((DEPTH + 2) / G)
gx = lambda x: int(round((x + BASE / 2 + 2) / G))
gy = lambda y: int(round((y + 1) / G))
wx = lambda i: i * G - BASE / 2 - 2
wy = lambda j: j * G - 1


def blocked_grid(net, layer, keep):
    """True where a copper centre (track centreline / via centre) of `net` may NOT go on `layer` ('F' or 'In2'):
    within `keep` of other-net copper on that layer, or near the board edge."""
    blk = np.zeros((NX, NY), dtype=bool)
    xs = np.array([wx(i) for i in range(NX)])
    ys = np.array([wy(j) for j in range(NY)])
    XX, YY = np.meshgrid(xs, ys, indexing='ij')
    m = 0.4 + keep - CL
    hw = BASE / 2 - YY * TAN30 - m / math.cos(math.radians(30))
    blk |= (YY < m) | (YY > DEPTH - m) | (np.abs(XX) > hw)
    for s in shapes:
        if s[1] == net or not on_layer(s, layer):
            continue
        if s[0] == 'circ':
            (cx, cy), r = s[3], s[4]
            sel = (np.abs(XX - cx) < r + keep + 0.1) & (np.abs(YY - cy) < r + keep + 0.1)
            blk[sel] |= np.hypot(XX[sel] - cx, YY[sel] - cy) < r + keep
        elif s[0] == 'seg':
            (ax, ay), (cx, cy), hwid = s[3], s[4], s[5]
            sel = ((XX > min(ax, cx) - hwid - keep - 0.1) & (XX < max(ax, cx) + hwid + keep + 0.1) &
                   (YY > min(ay, cy) - hwid - keep - 0.1) & (YY < max(ay, cy) + hwid + keep + 0.1))
            dx, dy = cx - ax, cy - ay
            L2 = dx * dx + dy * dy
            X_, Y_ = XX[sel], YY[sel]
            t = np.zeros_like(X_) if L2 == 0 else np.clip(((X_ - ax) * dx + (Y_ - ay) * dy) / L2, 0, 1)
            blk[sel] |= np.hypot(X_ - (ax + t * dx), Y_ - (ay + t * dy)) < hwid + keep
        else:
            x0, y0, x1, y1 = s[3:]
            ddx = np.maximum(np.maximum(x0 - XX, 0), XX - x1)
            ddy = np.maximum(np.maximum(y0 - YY, 0), YY - y1)
            blk |= np.hypot(ddx, ddy) < keep
    return blk


VIA_COST = 25.0   # grid steps (2.5 mm) per layer change: prefer few vias


def astar(a, a_lay, c, c_lay, net):
    """Two-layer A* (0 = F.Cu, 1 = In2.Cu). a/c: (x, y); *_lay: allowed start/end layers (sets)."""
    kt = TW / 2 + CL + 0.01
    trk = [blocked_grid(net, 'F', kt), blocked_grid(net, 'In2', kt)]
    via = blocked_grid(net, 'F', VD / 2 + CL + 0.01) | blocked_grid(net, 'In2', VD / 2 + CL + 0.01)
    sa, sc = (gx(a[0]), gy(a[1])), (gx(c[0]), gy(c[1]))
    for (i, j), lays in ((sa, a_lay), (sc, c_lay)):  # endpoints sit on this net's copper: clear a small disc
        for di in range(-3, 4):
            for dj in range(-3, 4):
                if di * di + dj * dj <= 9:
                    for L in lays:
                        trk[L][i + di, j + dj] = False
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    h = lambda p: math.hypot(p[0] - sc[0], p[1] - sc[1])
    openq = [(h(sa), 0.0, (sa[0], sa[1], L), None, None) for L in a_lay]
    heapq.heapify(openq)
    came, best = {}, {}
    goal = None
    while openq:
        f, g, p, par, d = heapq.heappop(openq)
        if p in came:
            continue
        came[p] = (par, d)
        if (p[0], p[1]) == sc and p[2] in c_lay:
            goal = p
            break
        L = p[2]
        for mx, my, cost in moves:
            q = (p[0] + mx, p[1] + my, L)
            if not (0 <= q[0] < NX and 0 <= q[1] < NY) or trk[L][q[0], q[1]]:
                continue
            ng = g + cost + (0.6 if d is not None and d != (mx, my) else 0)
            if ng < best.get(q, 1e18):
                best[q] = ng
                heapq.heappush(openq, (ng + h(q), ng, q, p, (mx, my)))
        if not via[p[0], p[1]]:
            q = (p[0], p[1], 1 - L)
            if not trk[1 - L][p[0], p[1]]:
                ng = g + VIA_COST
                if ng < best.get(q, 1e18):
                    best[q] = ng
                    heapq.heappush(openq, (ng + h(q), ng, q, p, None))
    if goal is None:
        return None
    path, p = [], goal
    while p is not None:
        path.append(p)
        p = came[p][0]
    path.reverse()
    # split into (layer, points) runs; a layer change = via at that point
    runs, cur = [], [path[0]]
    for q in path[1:]:
        if q[2] != cur[-1][2]:
            runs.append(cur)
            cur = [q]
        else:
            cur.append(q)
    runs.append(cur)
    out = []
    for r in runs:
        pts = [r[0]]
        for k in range(1, len(r) - 1):
            d1 = (r[k][0] - r[k - 1][0], r[k][1] - r[k - 1][1])
            d2 = (r[k + 1][0] - r[k][0], r[k + 1][1] - r[k][1])
            if d1 != d2:
                pts.append(r[k])
        if len(r) > 1:
            pts.append(r[-1])
        out.append((r[0][2], [(round(wx(i), 3), round(wy(j), 3)) for i, j, _ in pts]))
    return out


def add_track(net, a, c, layer, w=TW):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(P(*a))
    t.SetEnd(P(*c))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(b.FindNet(net))
    b.Add(t)
    shapes.append(('seg', net, 'F' if layer == pcbnew.F_Cu else 'In2', a, c, w / 2))


def add_via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(P(x, y))
    v.SetWidth(pcbnew.FromMM(VD))
    v.SetDrill(pcbnew.FromMM(0.3))
    v.SetNet(b.FindNet(net))
    b.Add(v)
    shapes.append(('circ', net, ALL, (x, y), VD / 2))


def pad_xy(spec):
    ref, num = spec.split('.')
    for pd in b.FindFootprintByReference(ref).Pads():
        if pd.GetNumber() == num:
            return tm(pd.GetPosition())
    raise KeyError(spec)


def endpoint(net, e):
    """-> ((x, y), allowed layers). Existing via: both layers. ('pad', spec, near): start on F.Cu at the pad."""
    if e[0] == 'pad' and e[2] is None:
        return pad_xy(e[1]), {0}
    if e[0] != 'pad':
        return e, {0, 1}
    _, spec, (vx, vy) = e
    # nearest free via site around the suggested spot
    best = None
    for r in np.arange(0, 1.6, 0.1):
        for ang in range(0, 360, 15):
            x, y = vx + r * math.cos(math.radians(ang)), vy + r * math.sin(math.radians(ang))
            if via_free(x, y, net):
                best = (round(float(x), 2), round(float(y), 2))
                break
        if best:
            break
    assert best, f'no via site for {net} near {(vx, vy)}'
    add_via(net, *best)
    add_track(net, best, pad_xy(spec), pcbnew.F_Cu)
    return best, {0, 1}


def open_connections():
    """Unconnected items from a kicad-cli DRC run on a temporary copy -> [(net, (xy, layers), (xy, layers))]."""
    import json
    import re
    import subprocess
    import tempfile
    tmpd = tempfile.mkdtemp()
    tmp = os.path.join(tmpd, 'fixup.kicad_pcb')
    pcbnew.SaveBoard(tmp, b)
    rep = os.path.join(tmpd, 'drc.json')
    subprocess.run(['C:/Program Files/KiCad/9.0/bin/kicad-cli.exe', 'pcb', 'drc', '--format', 'json', '-o', rep, tmp],
                   capture_output=True)
    d = json.load(open(rep, encoding='utf-8'))
    jobs = []
    for u in d['unconnected_items']:
        ends, net = [], None
        for it in u['items']:
            desc = it['description']
            xy = (it['pos']['x'] - X0, Y0 - it['pos']['y'])
            m = re.match(r'Pad (\S+) \[(.*?)\] of (\S+) on (\S+)', desc)
            if m:
                net = m.group(2)
                ends.append(('pad', f'{m.group(3)}.{m.group(1)}', None))
                continue
            m = re.match(r'Via \[(.*?)\]', desc)
            if m:
                net = m.group(1)
                ends.append(xy)
                continue
            m = re.match(r'Track \[(.*?)\] on (\S+)', desc)
            if m:
                net = m.group(1)
                ends.append(('trk', xy, 0 if m.group(2).rstrip(',') == 'F.Cu' else 1))
                continue
            ends = None   # zone islands: handled by the island stitching below
            break
        if ends and len(ends) == 2:
            jobs.append((net, ends[0], ends[1]))
    return jobs


def track_end(e, other_xy):
    """('trk', pos, layer): pick the end of that track nearest the other endpoint."""
    _, pos, lay = e
    best = None
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_TRACK' and (t.GetLayer() == pcbnew.F_Cu) == (lay == 0):
            s0, s1 = tm(t.GetStart()), tm(t.GetEnd())
            if dist_seg(pos[0], pos[1], s0, s1) < 0.02:
                for q in (s0, s1):
                    dd = math.hypot(q[0] - other_xy[0], q[1] - other_xy[1])
                    if best is None or dd < best[0]:
                        best = (dd, q)
    return best[1], {lay}


def resolve(net, e, other):
    if isinstance(e, tuple) and e and e[0] == 'trk':
        ox = other[1] if isinstance(other, tuple) and other[0] == 'trk' else (
            pad_xy(other[1]) if isinstance(other, tuple) and other[0] == 'pad' else other)
        return track_end(e, ox)
    return endpoint(net, e)


JOBS = open_connections()
for j in JOBS:
    print("  job", j)
print('open connections after Freerouting:', len(JOBS))
resolved = []
for net, ea, ec in JOBS:
    resolved.append((net, resolve(net, ea, ec), resolve(net, ec, ea)))
resolved.sort(key=lambda j: -math.hypot(j[1][0][0] - j[2][0][0], j[1][0][1] - j[2][0][1]))  # longest first
for net, (a, al), (c, cl) in resolved:
    runs = astar(a, al, c, cl, net)
    assert runs, f'no path for {net}'
    runs[0][1][0] = a
    runs[-1][1][-1] = c
    L, nv = 0.0, 0
    for k, (lay, pts) in enumerate(runs):
        if k > 0:
            add_via(net, *pts[0])
            nv += 1
        for p, q in zip(pts, pts[1:]):
            add_track(net, p, q, pcbnew.F_Cu if lay == 0 else pcbnew.In2_Cu)
            L += math.hypot(q[0] - p[0], q[1] - p[1])
    print(f'{net}: {L:.1f} mm, {nv} vias, layers {[r[0] for r in runs]}')

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())

# ------------------------------------------------------------------ F.Cu GND islands without a via
zf = next(z for z in b.Zones() if z.GetZoneName() == 'GND F')
fill = zf.GetFilledPolysList(pcbnew.F_Cu)
gnd_holes = [s[3] for s in shapes if s[0] == 'circ' and s[1] == 'GND']
added = 0
for k in range(fill.OutlineCount()):
    one = pcbnew.SHAPE_POLY_SET()
    one.AddOutline(fill.Outline(k))
    if any(one.Contains(P(x, y)) for x, y in gnd_holes):
        continue
    inner = one.CloneDropTriangulation()
    inner.Inflate(pcbnew.FromMM(-0.35), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.05))
    if inner.OutlineCount() == 0:
        continue
    bb = inner.BBox()
    x0, y1 = tm(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
    x1, y0 = tm(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
    done = False
    for x in np.arange(x0, x1, 0.1):
        for y in np.arange(y0, y1, 0.1):
            if inner.Contains(P(x, y)) and via_free(x, y, 'GND'):
                add_via('GND', round(float(x), 2), round(float(y), 2))
                gnd_holes.append((x, y))
                added += 1
                done = True
                break
        if done:
            break
print('island stitching vias:', added)
filler.Fill(b.Zones())
# last step (nothing typed is used after a Remove): drop zero-length leftovers of the SES import
def free_end(t):
    """True if one end of t touches no other copper of its net (track, via or pad)."""
    net, lay = t.GetNetname(), t.GetLayer()
    for e in (t.GetStart(), t.GetEnd()):
        ex, ey = tm(e)
        hit = False
        for o in b.GetTracks():
            if o is t or o.GetNetname() != net or o.m_Uuid.AsString() == t.m_Uuid.AsString():
                continue
            if o.GetClass() == 'PCB_VIA':
                hit |= math.hypot(ex - tm(o.GetPosition())[0], ey - tm(o.GetPosition())[1]) < pcbnew.ToMM(o.GetWidth()) / 2
            elif o.GetLayer() == lay:
                hit |= dist_seg(ex, ey, tm(o.GetStart()), tm(o.GetEnd())) < 0.01
        for fp in b.GetFootprints():
            for pd in fp.Pads():
                if pd.GetNetname() == net and pd.IsOnLayer(lay) and pd.HitTest(e):
                    hit = True
        if not hit:
            return True
    return False


def covered(t):
    """True if t lies entirely on another, at-least-as-wide track of its net and layer (redundant overlap)."""
    a, c = tm(t.GetStart()), tm(t.GetEnd())
    for o in b.GetTracks():
        if (o.GetClass() == 'PCB_TRACK' and o.m_Uuid.AsString() != t.m_Uuid.AsString() and o.GetNetname() == t.GetNetname()
                and o.GetLayer() == t.GetLayer() and o.GetWidth() >= t.GetWidth() and o.GetLength() > t.GetLength()):
            if all(dist_seg(p[0], p[1], tm(o.GetStart()), tm(o.GetEnd())) < 0.01 for p in (a, c)):
                return True
    return False


stubs = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and
         (t.GetLength() < pcbnew.FromMM(0.05) or
          (t.GetLength() < pcbnew.FromMM(0.5) and (free_end(t) or covered(t))))]
for t in stubs:
    b.Remove(t)
print('removed stub tracks:', len(stubs))
pcbnew.SaveBoard(PCB, b)
