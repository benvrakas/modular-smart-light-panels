"""Write the board design rules into a .kicad_pro (kicad-cli DRC reads them from there), keeping any
existing project content (sheets, schematic settings). Template: the V5 edge-board project's board section.

usage: python make_project.py PROJECT.kicad_pro [edge_clearance_mm]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.normpath(os.path.join(HERE, '..', '..', 'archive', 'edge-board-v5', 'edge-board.kicad_pro'))  # read only

dst = sys.argv[1]
edge = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
tpl = json.load(open(TEMPLATE, encoding='utf-8'))
cur = json.load(open(dst, encoding='utf-8')) if os.path.exists(dst) else {}

ds = tpl['board']['design_settings']
ds['rules'].update({'min_copper_edge_clearance': edge, 'min_via_diameter': 0.6, 'min_through_hole_diameter': 0.3,
                    'min_track_width': 0.15, 'min_clearance': 0.15, 'min_hole_clearance': 0.25,
                    'min_hole_to_hole': 0.25, 'min_text_height': 0.6})
ds['drc_exclusions'] = []
ds['track_widths'] = [0.0, 0.2, 0.25, 0.4, 0.6, 1.0]
ds['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.6, 'drill': 0.3}]
board = cur.get('board', {})
board['design_settings'] = ds
cur['board'] = board
default = [c for c in tpl['net_settings']['classes'] if c['name'] == 'Default'][0]
ns = cur.get('net_settings', {})
ns['classes'] = [default]
ns.setdefault('meta', {'version': 4})
ns['netclass_assignments'] = None
ns['netclass_patterns'] = []
cur['net_settings'] = ns
cur.setdefault('meta', {})['filename'] = os.path.basename(dst)
cur['meta'].setdefault('version', 3)
for k in ('libraries', 'schematic', 'sheets', 'text_variables', 'boards'):
    if k not in cur and k in tpl:
        cur[k] = tpl[k] if k != 'sheets' else []
with open(dst, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(cur, f, indent=2)
print('wrote', dst)
