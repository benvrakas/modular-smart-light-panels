"""Netlist -> PCB sync for the edge board (equivalent of F8 'Update PCB from
Schematic' with 'replace footprints' + 'delete extra footprints', and
'Update footprints from library' for FORCE refs).
usage (KiCad 9 python):
  python sync.py board.kicad_pcb netlist.net modularlight_lib_dir FORCE_REFS(comma)
New parts are dropped at (150, 150) mm for placement afterwards."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kicad_quiet  # no wx assert pop-ups
import sys, re, pcbnew

STDLIB = "C:/Program Files/KiCad/9.0/share/kicad/footprints/"


def parse(s):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', s)
    stack = [[]]
    for t in toks:
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return stack[0][0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def val(node, key, default=None):
    r = find(node, key)
    return r[0][1] if r and len(r[0]) > 1 else default


board_path, net_path, mllib = sys.argv[1], sys.argv[2], sys.argv[3]
force = set(sys.argv[4].split(',')) if len(sys.argv) > 4 and sys.argv[4] else set()
libdir = lambda lib: mllib if lib == 'ModularLight' else STDLIB + lib + '.pretty'

nl = parse(open(net_path, encoding='utf-8').read())
comps = {}
for c in find(find(nl, 'components')[0], 'comp'):
    ref = val(c, 'ref')
    fields = {}
    for fl in find(c, 'fields'):
        for f in find(fl, 'field'):
            fields[val(f, 'name')] = f[2] if len(f) > 2 else ''
    props = {val(p, 'name'): val(p, 'value', '') for p in find(c, 'property')}
    path = val(find(c, 'sheetpath')[0], 'tstamps') + val(c, 'tstamps')
    comps[ref] = dict(value=val(c, 'value'), fpid=val(c, 'footprint'), fields=fields,
                      path=path, dnp='dnp' in props, xbom='exclude_from_bom' in props)
pinnet, netnames = {}, []
for n in find(find(nl, 'nets')[0], 'net'):
    name = val(n, 'name'); netnames.append(name)
    for nd in find(n, 'node'):
        pinnet[(val(nd, 'ref'), val(nd, 'pin'))] = name

b = pcbnew.LoadBoard(board_path)
log = []
old = {fp.GetReference(): fp for fp in b.GetFootprints()}   # iterate ONCE, before any removal

# 1. load every new / replacement footprint first (SWIG breaks after Remove/Delete)
new = {}
for ref, c in sorted(comps.items()):
    cur = old.get(ref)
    if cur is None or cur.GetFPIDAsString() != c['fpid'] or ref in force:
        lib, name = c['fpid'].split(':')
        fp = pcbnew.FootprintLoad(libdir(lib), name)
        assert fp is not None, c['fpid']
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        if cur is not None:
            fp.SetPosition(cur.GetPosition()); fp.SetOrientation(cur.GetOrientation())
            for k, v in cur.GetFieldsText().items():
                if k not in ('Reference', 'Value', 'Footprint') and not fp.HasFieldByName(k):
                    fp.SetField(k, v)
            log.append(f"{ref}: {cur.GetFPIDAsString()} -> {c['fpid']} (reloaded)")
        else:
            fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(150), pcbnew.FromMM(150)))
            log.append(f"{ref}: added {c['fpid']}")
        new[ref] = fp
# 2. delete replaced and extra footprints
for ref, fp in old.items():
    if ref not in comps and fp.IsBoardOnly():
        continue                      # board-only (e.g. H1/H2 tooling holes): F8 leaves these alone too
    if ref in new or ref not in comps:
        if ref not in comps:
            log.append(f"{ref}: deleted (not in schematic)")
        b.Delete(fp)
# 3. add new ones
for ref, fp in new.items():
    fp.SetReference(ref); b.Add(fp)
# 4. nets
for name in netnames:
    if b.FindNet(name) is None:
        b.Add(pcbnew.NETINFO_ITEM(b, name)); log.append(f"add net {name}")
# 5. per-component data + pad nets
for ref, c in sorted(comps.items()):
    fp = b.FindFootprintByReference(ref)
    if fp.GetValue() != c['value']:
        log.append(f"{ref}: value {fp.GetValue()!r} -> {c['value']!r}"); fp.SetValue(c['value'])
    if fp.GetPath().AsString() != c['path']:
        if ref in new:
            fp.SetPath(pcbnew.KIID_PATH(c['path']))
        else:
            log.append(f"!! {ref}: PATH MISMATCH board={fp.GetPath().AsString()} sch={c['path']}")
    for k, v in c['fields'].items():
        if k in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description'):
            continue
        if not fp.HasFieldByName(k) or fp.GetFieldText(k) != v:
            log.append(f"{ref}: field {k} -> {v!r}"); fp.SetField(k, v)
            fp.GetFieldByName(k).SetVisible(False)   # BOM fields never on silk
    if fp.IsDNP() != c['dnp']:
        log.append(f"{ref}: dnp -> {c['dnp']}"); fp.SetDNP(c['dnp'])
    if fp.IsExcludedFromBOM() != c['xbom']:
        log.append(f"{ref}: exclude_from_bom -> {c['xbom']}"); fp.SetExcludedFromBOM(c['xbom'])
    pads = {pd.GetNumber() for pd in fp.Pads()}
    for pd in fp.Pads():
        want, have = pinnet.get((ref, pd.GetNumber())), pd.GetNetname()
        if want is None:
            if pd.GetNetCode() != 0:
                log.append(f"{ref}.{pd.GetNumber()}: {have} -> <no net>"); pd.SetNetCode(0)
        elif want != have:
            pd.SetNet(b.FindNet(want)); log.append(f"{ref}.{pd.GetNumber()}: {have!r} -> {want}")
    missing = [p for (r, p) in pinnet if r == ref and p not in pads]
    if missing:
        log.append(f"!! {ref}: schematic pins with no pad: {missing}")
# 6. drop nets no pad uses any more
used = set()
for ref in comps:
    used |= {pd.GetNetname() for pd in b.FindFootprintByReference(ref).Pads()}
for name, ni in list(b.GetNetsByName().items()):
    s = str(name)
    if s and s not in used and s not in netnames:
        b.Remove(ni); log.append(f"remove net {s}")
b.BuildConnectivity()
pcbnew.SaveBoard(board_path, b)
print("\n".join(log)); print(f"{len(log)} changes")
