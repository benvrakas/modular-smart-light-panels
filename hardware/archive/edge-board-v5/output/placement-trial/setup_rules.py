"""Net classes (in <project>.kicad_pro) and custom DRC rules (<project>.kicad_dru) for the edge board.
usage: python setup_rules.py <project>.kicad_pro      (plain Python; no pcbnew needed)
Re-runnable: overwrites the classes/patterns/rules it owns."""
import sys, json, os

pro = sys.argv[1]
p = json.load(open(pro, encoding='utf-8'))
ns = p.setdefault('net_settings', {})
ns.setdefault('meta', {'version': 4})
classes = ns.setdefault('classes', [])
default = next((c for c in classes if c['name'] == 'Default'), None)
if default is None:   # minimal project file: KiCad fills the remaining defaults on load
    default = {'name': 'Default', 'priority': 2147483647, 'bus_width': 12, 'wire_width': 6,
               'diff_pair_gap': 0.25, 'diff_pair_via_gap': 0.25, 'diff_pair_width': 0.2,
               'line_style': 0, 'microvia_diameter': 0.3, 'microvia_drill': 0.1,
               'pcb_color': 'rgba(0, 0, 0, 0.000)', 'schematic_color': 'rgba(0, 0, 0, 0.000)'}
default.update(track_width=0.25, clearance=0.2, via_diameter=0.6, via_drill=0.3)

def cls(name, track, clearance, prio):
    c = dict(default); c.update(name=name, track_width=track, clearance=clearance,
                               via_diameter=0.6, via_drill=0.3, priority=prio)
    return c

ns['classes'] = [default,
                 cls('Power', 0.6, 0.2, 0),      # +12V, GND, +5V: pad-to-via stubs, feed-through necks
                 cls('Supply', 0.4, 0.2, 1)]     # +3V3, VIN_LDO
ns['netclass_patterns'] = [
    {'netclass': 'Power', 'pattern': '+12V'}, {'netclass': 'Power', 'pattern': 'GND'},
    {'netclass': 'Power', 'pattern': '+5V'},
    {'netclass': 'Supply', 'pattern': '+3V3'}, {'netclass': 'Supply', 'pattern': '/VIN_LDO'},
]
ds = p.setdefault('board', {}).setdefault('design_settings', {})
ds['track_widths'] = [0.0, 0.25, 0.4, 0.6, 0.8, 1.0, 1.6]
ds['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.6, 'drill': 0.3}, {'diameter': 0.8, 'drill': 0.4}]
r = ds.setdefault('rules', {})
r.update(min_track_width=0.15, min_via_diameter=0.5, min_through_hole_diameter=0.3,
         min_copper_edge_clearance=0.5, min_hole_clearance=0.25)
json.dump(p, open(pro, 'w', encoding='utf-8'), indent=2)

dru = os.path.splitext(pro)[0] + '.kicad_dru'
open(dru, 'w', encoding='utf-8').write('''(version 1)

# Corner-joint pads touch the board end by design (LAYOUT-NOTES 8). Confirm with the fab.
(rule "corner pads at board end"
  (severity ignore)
  (constraint edge_clearance (min 0mm))
  (condition "A.Type == 'Pad' && (A.memberOfFootprint('J2') || A.memberOfFootprint('J3'))"))

# J1 GND contact pads reach 0.3 mm from the wall edge (SPEC 3.3 mating order).
(rule "contact pads at wall edge"
  (constraint edge_clearance (min 0.25mm))
  (condition "A.Type == 'Pad' && A.memberOfFootprint('J1')"))

# DRIVE <-> +12V is the one destructive short (LAYOUT-NOTES 5, 13); SENSE as margin.
(rule "DRIVE/SENSE vs +12V"
  (constraint clearance (min 0.5mm))
  (condition "(A.NetName == '/DRIVE' || A.NetName == '/SENSE') && B.NetName == '+12V'"))

# +12V copper never next to +5V copper (LAYOUT-NOTES 1.2, 5).
(rule "+12V vs +5V"
  (constraint clearance (min 0.5mm))
  (condition "A.NetName == '+12V' && B.NetName == '+5V'"))

# 3.3 V logic vias through the In2 supply regions: >= 0.5 mm plane clearance, so a short can't put +12V/+5V
# straight into the MCU (LAYOUT-NOTES 13.6)
(rule "logic via vs In2 supply"
  (constraint clearance (min 0.5mm))
  (condition "A.Type == 'Via' && B.Type == 'Zone' && B.Layer == 'In2.Cu' && (B.NetName == '+12V' || B.NetName == '+5V') && A.NetName != 'GND' && A.NetName != '+12V' && A.NetName != '+5V'"))
''')
print('net classes:', [c['name'] for c in ns['classes']], '| rules ->', os.path.basename(dru))
