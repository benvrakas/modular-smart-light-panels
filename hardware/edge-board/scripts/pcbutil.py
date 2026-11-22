"""Small helpers shared by the V6 PCB build scripts (edge board, bridge, coupon). KiCad 9 Python.

Board coordinates: every script works in (x, z) mm. x runs along the board from its centre; z is the height
above the wall (bottom) edge. KiCad's y axis points down, so y = Y0 - z.
"""
import os
import re
import sys

try:
    import wx
    wx.DisableAsserts()          # no modal wx debug pop-ups (kicad-python-quirks)
except Exception:
    pass
import pcbnew  # noqa: E402

X0, Y0 = 100.0, 100.0
STDLIB = 'C:/Program Files/KiCad/9.0/share/kicad/footprints/'
HW = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
MLLIB = os.path.join(HW, 'lib', 'footprints', 'ModularLight.pretty')


LAYERS = {'F.Cu': 'F_Cu', 'B.Cu': 'B_Cu', 'Edge.Cuts': 'Edge_Cuts', 'Cmts.User': 'Cmts_User', 'Dwgs.User': 'Dwgs_User',
          'F.SilkS': 'F_SilkS', 'B.SilkS': 'B_SilkS', 'F.Fab': 'F_Fab', 'B.Fab': 'B_Fab', 'F.Mask': 'F_Mask',
          'B.Mask': 'B_Mask', 'F.Paste': 'F_Paste', 'B.Paste': 'B_Paste'}


def lid(board, name):
    """Layer id from a layer name; user layers via constants (GetLayerID needs the canonical names)."""
    if name in LAYERS:
        return getattr(pcbnew, LAYERS[name])
    i = board.GetLayerID(name)
    assert i >= 0, name
    return i


def P(x, z):
    return pcbnew.VECTOR2I(pcbnew.FromMM(X0 + x), pcbnew.FromMM(Y0 - z))


def mm(v):
    return pcbnew.FromMM(v)


def to_xz(v):
    return pcbnew.ToMM(v.x) - X0, Y0 - pcbnew.ToMM(v.y)


def libdir(lib):
    return MLLIB if lib == 'ModularLight' else STDLIB + lib + '.pretty'


def load_fp(fpid):
    lib, name = fpid.split(':')
    fp = pcbnew.FootprintLoad(libdir(lib), name)
    assert fp is not None, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ---------------------------------------------------------------- netlist (kicadsexpr)
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


def read_netlist(path):
    nl = parse(open(path, encoding='utf-8').read())
    comps = {}
    for c in find(find(nl, 'components')[0], 'comp'):
        ref = val(c, 'ref')
        props = {val(p, 'name'): val(p, 'value', '') for p in find(c, 'property')}
        sp = find(c, 'sheetpath')[0]
        comps[ref] = dict(value=val(c, 'value'), fpid=val(c, 'footprint'), props=props,
                          path=val(sp, 'tstamps') + val(c, 'tstamps'))
    pinnet = {}
    for n in find(find(nl, 'nets')[0], 'net'):
        name = val(n, 'name')
        for nd in find(n, 'node'):
            pinnet[(val(nd, 'ref'), val(nd, 'pin'))] = name
    return comps, pinnet


def net(board, name):
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
    return n


def add_footprints(board, comps, pinnet, skip_fields=('Sheetname', 'Sheetfile', 'ki_keywords', 'ki_fp_filters')):
    """Load every footprint first (SWIG quirk), then add, then assign nets."""
    loaded = {ref: load_fp(c['fpid']) for ref, c in sorted(comps.items())}
    for name in sorted(set(pinnet.values())):
        net(board, name)
    for ref, fp in loaded.items():
        c = comps[ref]
        fp.SetReference(ref)
        fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH(c['path']))
        for k, v in c['props'].items():
            if k in skip_fields or k in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description'):
                continue
            if k == 'dnp':
                fp.SetDNP(True)
                continue
            if k == 'exclude_from_bom':
                fp.SetExcludedFromBOM(True)
                continue
            fp.SetField(k, v)
            fld = fp.GetFieldByName(k)
            if fld:
                fld.SetVisible(False)
        board.Add(fp)
    for ref in loaded:
        fp = board.FindFootprintByReference(ref)
        for pd in fp.Pads():
            n = pinnet.get((ref, pd.GetNumber()))
            if n:
                pd.SetNet(board.FindNet(n))
    return loaded


def place(board, ref, x, z, rot=0, flip=False):
    fp = board.FindFootprintByReference(ref)
    if flip and not fp.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    # a LEFT_RIGHT flip is a mirror in x (seen from the front); KiCad expresses it as orientation 180 on B.Cu,
    # so keep that offset: rot is then the rotation as seen through the board from the front
    fp.SetOrientationDegrees(rot + 180 if flip else rot)
    fp.SetPosition(P(x, z))
    return fp


def track(board, pts, w, layer, netname, lock=True):
    layer_id = lid(board, layer)
    n = board.FindNet(netname)
    for (a, b) in zip(pts[:-1], pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(*a))
        t.SetEnd(P(*b))
        t.SetWidth(mm(w))
        t.SetLayer(layer_id)
        t.SetNet(n)
        t.SetLocked(lock)
        board.Add(t)


def via(board, x, z, netname, d=0.6, drill=0.3, lock=True):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, z))
    v.SetWidth(mm(d))
    v.SetDrill(mm(drill))
    v.SetNet(board.FindNet(netname))
    v.SetLocked(lock)
    board.Add(v)
    return v


def seg(board, a, b, layer='Edge.Cuts', w=0.05):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*a))
    s.SetEnd(P(*b))
    s.SetLayer(lid(board, layer))
    s.SetWidth(mm(w))
    board.Add(s)


def outline_poly(board, pts):
    for a, b in zip(pts, pts[1:] + pts[:1]):
        seg(board, a, b)


def text(board, s, x, z, layer, size=0.8, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(P(x, z))
    t.SetLayer(lid(board, layer))
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    if mirror:
        t.SetMirrored(True)
    board.Add(t)
    return t


def zone(board, netname, layer, pts, clearance=0.25, min_w=0.2, priority=0, name='', thermal=False):
    z = pcbnew.ZONE(board)
    z.SetLayer(lid(board, layer))
    if netname:
        z.SetNet(board.FindNet(netname))
    ol = z.Outline()
    ol.NewOutline()
    for (x, zz) in pts:
        ol.Append(mm(X0 + x), mm(Y0 - zz))
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_w))
    z.SetAssignedPriority(priority)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    if name:
        z.SetZoneName(name)
    board.Add(z)
    return z


def keepout(board, layers, pts, name, tracks=False, vias=False, pour=False, pads=True, fps=True):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(lid(board, l))
    z.SetLayerSet(ls)
    ol = z.Outline()
    ol.NewOutline()
    for (x, zz) in pts:
        ol.Append(mm(X0 + x), mm(Y0 - zz))
    z.SetDoNotAllowTracks(not tracks)
    z.SetDoNotAllowVias(not vias)
    z.SetDoNotAllowZoneFills(not pour)
    z.SetDoNotAllowPads(not pads)
    z.SetDoNotAllowFootprints(not fps)
    z.SetZoneName(name)
    board.Add(z)
    return z


def setup_rules(board, clearance=0.2, track_w=0.25, edge=0.3, thickness=1.6, min_track=0.15, min_clear=0.15):
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.SetBoardThickness(mm(thickness))
    ds.m_TrackMinWidth = mm(min_track)
    ds.m_MinClearance = mm(min_clear)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(edge)
    ds.m_HoleToHoleMin = mm(0.25)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(clearance))
    nc.SetTrackWidth(mm(track_w))
    nc.SetViaDiameter(mm(0.6))
    nc.SetViaDrill(mm(0.3))


def report_unconnected(board):
    board.BuildConnectivity()
    c = board.GetConnectivity()
    return c.GetUnconnectedCount(True)
