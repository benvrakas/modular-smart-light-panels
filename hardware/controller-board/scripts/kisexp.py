"""Minimal KiCad S-expression reader/writer and symbol-library helpers (KiCad 9).

Quoted strings are kept as QStr so they are written back quoted; bare tokens stay plain str.
Used by gen_v6_schematics.py. Run with KiCad's bundled Python (no extra packages needed).
"""
import copy
import os
import re

_TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


class QStr(str):
    """A string that was (or must be) quoted in the S-expression."""


def parse(text):
    stack = [[]]
    for m in _TOK.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append([])
        elif t == ')':
            node = stack.pop()
            stack[-1].append(node)
        elif t.startswith('"'):
            stack[-1].append(QStr(t[1:-1].replace('\\"', '"').replace('\\\\', '\\')))
        else:
            stack[-1].append(t)
    return stack[0][0]


def q(s):
    return QStr(s)


def _atom(a):
    if isinstance(a, QStr):
        return '"' + a.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(a, float):
        s = f"{a:.4f}".rstrip('0').rstrip('.')
        return '0' if s in ('-0', '') else s
    return str(a)


def dump(node, indent=0):
    """Write a node. Short nodes on one line, long ones one child per line (tab indented)."""
    if not isinstance(node, list):
        return _atom(node)
    flat = '(' + ' '.join(dump(c, 0) for c in node) + ')'
    if len(flat) <= 100 and '\n' not in flat:
        return flat
    pad = '\t' * (indent + 1)
    head = []
    rest = []
    for c in node:
        if isinstance(c, list) or rest:
            rest.append(c)
        else:
            head.append(c)
    out = '(' + ' '.join(_atom(h) for h in head)
    for c in rest:
        out += '\n' + pad + dump(c, indent + 1)
    out += '\n' + '\t' * indent + ')'
    return out


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def first(node, key):
    f = find(node, key)
    return f[0] if f else None


def prop(node, name):
    for p in find(node, 'property'):
        if p[1] == name:
            return p
    return None


# ---------------------------------------------------------------- symbol libraries
KICAD_SYM = r"C:\Program Files\KiCad\9.0\share\kicad\symbols"
_cache = {}


def load_lib(path):
    if path not in _cache:
        with open(path, encoding='utf-8') as f:
            _cache[path] = parse(f.read())
    return _cache[path]


def _raw_symbol(libtree, name):
    for s in find(libtree, 'symbol'):
        if s[1] == name:
            return s
    raise KeyError(name)


def lib_symbol(libname, symname, project_lib=None):
    """Return the flattened symbol as embedded in a schematic's lib_symbols: (symbol "Lib:Name" ...)."""
    if libname == 'ModularLight':
        path = project_lib
    else:
        path = os.path.join(KICAD_SYM, libname + '.kicad_sym')
    tree = load_lib(path)
    sym = copy.deepcopy(_raw_symbol(tree, symname))
    ext = first(sym, 'extends')
    if ext is not None:
        parent = copy.deepcopy(_raw_symbol(tree, ext[1]))
        pname = parent[1]
        child_props = {p[1]: p for p in find(sym, 'property')}
        out = [parent[0], QStr(symname)]
        for c in parent[2:]:
            if isinstance(c, list) and c[0] == 'property' and c[1] in child_props:
                out.append(child_props.pop(c[1]))
            elif isinstance(c, list) and c[0] == 'symbol':
                sub = copy.deepcopy(c)
                sub[1] = QStr(str(sub[1]).replace(pname + '_', symname + '_', 1))
                out.append(sub)
            elif isinstance(c, list) and c[0] in ('in_bom', 'on_board', 'exclude_from_sim'):
                ch = first(sym, c[0])
                out.append(ch if ch is not None else c)
            else:
                out.append(c)
        # child-only properties go after the last parent property
        idx = max(i for i, c in enumerate(out) if isinstance(c, list) and c[0] == 'property')
        for p in child_props.values():
            idx += 1
            out.insert(idx, p)
        sym = out
    sym[1] = QStr(f"{libname}:{symname}")
    return sym


def symbol_pins(sym):
    """Pins of unit 1 / common unit, body style 1: list of dict(number,name,type,x,y,angle,length,hidden)."""
    base = str(sym[1]).split(':', 1)[1]
    pins = []
    for sub in find(sym, 'symbol'):
        m = re.match(re.escape(base) + r'_(\d+)_(\d+)$', str(sub[1]))
        if not m or int(m.group(1)) not in (0, 1) or int(m.group(2)) not in (0, 1):
            continue
        for p in find(sub, 'pin'):
            at = first(p, 'at')
            pins.append(dict(type=p[1], number=str(first(p, 'number')[1]), name=str(first(p, 'name')[1]),
                             x=float(at[1]), y=float(at[2]), angle=float(at[3]) if len(at) > 3 else 0.0,
                             length=float(first(p, 'length')[1]), hidden='hide' in p or any(
                                 isinstance(c, list) and c[0] == 'hide' for c in p)))
    return pins


def symbol_bbox(sym):
    """Rough body bbox in lib coordinates (y up) from rectangles/polylines/pins."""
    xs, ys = [], []
    for sub in find(sym, 'symbol'):
        for r in find(sub, 'rectangle'):
            for k in ('start', 'end'):
                pt = first(r, k)
                xs.append(float(pt[1])); ys.append(float(pt[2]))
        for pl in find(sub, 'polyline'):
            for xy in find(first(pl, 'pts'), 'xy'):
                xs.append(float(xy[1])); ys.append(float(xy[2]))
        for c in find(sub, 'circle'):
            ctr = first(c, 'center'); rad = float(first(c, 'radius')[1])
            xs += [float(ctr[1]) - rad, float(ctr[1]) + rad]; ys += [float(ctr[2]) - rad, float(ctr[2]) + rad]
    for p in symbol_pins(sym):
        xs.append(p['x']); ys.append(p['y'])
    if not xs:
        return (-2.54, -2.54, 2.54, 2.54)
    return (min(xs), min(ys), max(xs), max(ys))
