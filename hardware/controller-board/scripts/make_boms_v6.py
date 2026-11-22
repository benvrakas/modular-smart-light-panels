"""JLCPCB-format BOMs (Comment, Designator, Footprint, LCSC) for the V6 boards, plus a stock check.

  controller-board/bom/BOM_controller-board.csv
  edge-board/bom/BOM_edge_code0.csv ... BOM_edge_code5.csv   (one per edge-code variant)
  <project>/bom/stock-check.csv   JLC assembly stock (JLCPCB parts API), jlcsearch stock, LCSC store stock

Run with KiCad's Python. Use --no-stock to skip the network queries.
"""
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_v6_schematics as g  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
FLAG_BELOW = 500


def natkey(ref):
    head = ref.rstrip('0123456789')
    return head, int(ref[len(head):] or 0)


def bom_rows(parts, override=None, dnp=()):
    """override: {ref: catalogue key}; dnp: refs left unfitted in this variant."""
    groups = {}
    for p in parts:
        key = (override or {}).get(p['ref'], p['key'])
        lib_id, value, fp, lcsc, mpn, mfr, _ = g.CAT[key]
        if not lcsc or p['dnp'] or p['ref'] in dnp:
            continue
        groups.setdefault((value, fp.split(':')[-1], lcsc, mpn, mfr), []).append(p['ref'])
    rows = []
    for (value, fp, lcsc, mpn, mfr), refs in sorted(groups.items(), key=lambda kv: natkey(sorted(kv[1], key=natkey)[0])):
        rows.append(dict(Comment=value, Designator=','.join(sorted(refs, key=natkey)), Footprint=fp, LCSC=lcsc,
                         MPN=mpn, Manufacturer=mfr, Qty=len(refs)))
    return rows


def write_bom(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC'])
        for r in rows:
            w.writerow([r['Comment'], r['Designator'], r['Footprint'], r['LCSC']])
    print('wrote', path, len(rows), 'lines')


# ------------------------------------------------------------------------------------ stock
def _get_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=dict(UA, **(headers or {})))
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def jlc_stock(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 5}).encode()
    d = _get_json("https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList",
                  body, {"Content-Type": "application/json"})
    for c in ((d.get("data") or {}).get("componentPageInfo") or {}).get("list") or []:
        if c.get("componentCode") == code:
            return c.get("stockCount"), {'base': 'basic', 'expand': 'extended'}.get(c.get("componentLibraryType"),
                                                                                   c.get("componentLibraryType"))
    return None, None


def jlcsearch_stock(code, mpn):
    n = int(code[1:])
    for q in (code, mpn):
        try:
            d = _get_json("https://jlcsearch.tscircuit.com/api/search?" + urllib.parse.urlencode({"q": q, "limit": 10}))
        except Exception:
            continue
        for c in d.get("components", []):
            if c.get("lcsc") == n and c.get("stock") is not None:
                return c.get("stock")
        time.sleep(0.4)
    return None


def lcsc_stock(code):
    d = _get_json("https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=" + code)
    return (d.get("result") or {}).get("stockNumber")


def stock_report(path, rows_by_variant):
    seen = {}
    for rows in rows_by_variant:
        for r in rows:
            seen.setdefault(r['LCSC'], r)
    out = []
    for code, r in seen.items():
        js, typ = jlc_stock(code)
        time.sleep(0.4)
        jss = jlcsearch_stock(code, r['MPN'])
        time.sleep(0.4)
        try:
            ls = lcsc_stock(code)
        except Exception:
            ls = None
        time.sleep(0.4)
        flag = 'LOW' if (js is None or js < FLAG_BELOW) else ''
        out.append([code, r['MPN'], r['Manufacturer'], r['Comment'], typ, js, jss, ls, flag])
        print(f"  {code:<10} {r['MPN'][:24]:<24} JLC={js} ({typ}) jlcsearch={jss} LCSC={ls} {flag}")
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['LCSC', 'MPN', 'Manufacturer', 'Comment', 'JLC library', 'JLC assembly stock',
                    'jlcsearch stock', 'LCSC store stock', f'Flag (JLC stock < {FLAG_BELOW})'])
        w.writerows(out)
        w.writerow([])
        w.writerow([f'Checked {time.strftime("%Y-%m-%d %H:%M")} via the JLCPCB parts API, jlcsearch.tscircuit.com '
                    'and wmsc.lcsc.com. JLC assembly stock is what an assembly order draws from.'])
    print('wrote', path)


def main():
    cp, _ = g.controller_parts()
    pp, _ = g.passive_parts()
    ctl = bom_rows(cp)
    write_bom(os.path.join(g.HW, 'controller-board', 'bom', 'BOM_controller-board.csv'), ctl)
    edge = []
    for code, key in g.ID_CODES.items():
        rows = bom_rows(pp, override={'R1': key}, dnp=('R3',) if code == 0 else ())
        write_bom(os.path.join(g.HW, 'edge-board', 'bom', f'BOM_edge_code{code}.csv'), rows)
        edge.append(rows)
    if '--no-stock' not in sys.argv:
        print('controller stock:')
        stock_report(os.path.join(g.HW, 'controller-board', 'bom', 'stock-check.csv'), [ctl])
        print('edge board stock:')
        stock_report(os.path.join(g.HW, 'edge-board', 'bom', 'stock-check.csv'), edge)


if __name__ == '__main__':
    main()
