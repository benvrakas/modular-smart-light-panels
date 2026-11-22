"""Controller board: net classes and board rules (into controller-board.kicad_pro) and custom DRC rules
(controller-board.kicad_dru). Plain Python, re-runnable; only touches the keys it owns.

usage:  python layout_rules.py            (paths are fixed relative to this script)

JLCPCB 4-layer limits used (JLC04161H-7628, 1.6 mm, 1 oz outer / 0.5 oz inner):
  track/space >= 0.09 mm (we use 0.2 nominal; 0.1 mm minimum for autorouter neck-downs), via drill >= 0.15 (we use 0.3 / 0.6 pad), copper to edge >= 0.2-0.3 mm.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.normpath(os.path.join(HERE, '..', '..'))
PRO = os.path.join(PRJ, 'controller-board.kicad_pro')
DRU = os.path.join(PRJ, 'controller-board.kicad_dru')

# Nets that may sit next to +36V copper (SPEC 2, decision 0011): GND and the 36 V-tolerant nets.
# BUCK_SW / BUCK_BOOT swing to 24-29 V themselves (they are the U5 pins beside VIN).
TOLERANT = ['GND', '/CANH', '/CANL', '/SPARE', '/SENSE', '/DRIVE', '/BUCK_SW', '/BUCK_BOOT',
            'unconnected-(U5-EN-Pad3)']  # U5 EN is open; it sits beside VIN inside the IC pinout, no copper on it
HV = ['+36V', '/+36V_IN']

with open(PRO, encoding='utf-8') as f:
    p = json.load(f)
ns = p.setdefault('net_settings', {})
ns.setdefault('meta', {'version': 4})
classes = ns.setdefault('classes', [])
default = next((c for c in classes if c['name'] == 'Default'), None)
default.update(track_width=0.2, clearance=0.2, via_diameter=0.6, via_drill=0.3)


def cls(name, track, clearance=0.2, prio=0):
    c = dict(default)
    c.update(name=name, track_width=track, clearance=clearance, via_diameter=0.6, via_drill=0.3, priority=prio)
    return c


ns['classes'] = [default,
                 cls('HV36', 0.6, prio=0),     # +36V, +36V_IN: <= 0.3 A, but short and wide (TVS / C_IN paths)
                 cls('Power', 0.5, prio=1),    # GND, +5V (1 A), +5V_LED (0.73 A)
                 cls('Supply', 0.3, prio=2),   # +3V3 (< 0.1 A)
                 cls('Switch', 0.8, prio=3)]   # BUCK_SW: hand-routed / poured, kept small
ns['netclass_patterns'] = (
    [{'netclass': 'HV36', 'pattern': n} for n in HV] +
    [{'netclass': 'Power', 'pattern': n} for n in ('GND', '+5V', '+5V_LED')] +
    [{'netclass': 'Supply', 'pattern': '+3V3'}, {'netclass': 'Switch', 'pattern': '/BUCK_SW'}])
ns['netclass_assignments'] = None

ds = p.setdefault('board', {}).setdefault('design_settings', {})
ds['track_widths'] = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
ds['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.6, 'drill': 0.3}]
r = ds.setdefault('rules', {})
r.update(min_track_width=0.1,   # JLC 4-layer: 0.09 mm; Freerouting necks LED_RET to 0.1 mm for 0.25 mm at R8
          min_clearance=0.15, min_via_diameter=0.5, min_via_annular_width=0.1,
         min_through_hole_diameter=0.3, min_copper_edge_clearance=0.3, min_hole_clearance=0.25,
         min_hole_to_hole=0.25, min_silk_clearance=0.0, min_text_height=0.8, min_text_thickness=0.12,
         solder_mask_to_copper_clearance=0.0, use_height_for_length_calcs=True)
sev = ds.setdefault('rule_severities', {})
sev.update({'lib_footprint_issues': 'ignore', 'lib_footprint_mismatch': 'ignore'})
with open(PRO, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(p, f, indent=2)
    f.write('\n')

tol = ' && '.join(f"B.NetName != '{n}'" for n in TOLERANT + HV)
with open(DRU, 'w', encoding='utf-8', newline='\n') as f:
    f.write(f'''(version 1)

# J1 joint pads run to the trapezoid base by design: the fillet to the code-0 edge board's J4 forms there
# (SCHEMATIC-NOTES 6.2, footprint ControllerJoint_ControllerEdge). Everything else keeps >= 0.3 mm.
(rule "J1 joint pads at the base edge"
  (severity ignore)
  (constraint edge_clearance (min 0mm))
  (condition "A.Type == 'Pad' && A.memberOfFootprint('J1')"))

# SPEC 2 / decision 0011: +36V copper may only sit next to GND or 36 V-tolerant nets. Everything else
# keeps >= 1.0 mm, which leaves room for the GND pour (0.25 clearance + 0.25 min width) to fill between.
(rule "+36V neighbours: GND or 36 V-tolerant only"
  (constraint clearance (min 1.0mm))
  (condition "A.NetClass == 'HV36' && {tol}"))

# Buck switch node: the TI layout rules (SCHEMATIC-NOTES 12) keep it away from the crystal and the ADC node.
(rule "SW node away from crystal / ADC"
  (constraint clearance (min 10mm))
  (condition "A.NetName == '/BUCK_SW' && (B.NetName == '/OSC_IN' || B.NetName == '/OSC_OUT' || B.NetName == '/SENSE_ADC')"))
''')
print('wrote', PRO, 'and', DRU)
