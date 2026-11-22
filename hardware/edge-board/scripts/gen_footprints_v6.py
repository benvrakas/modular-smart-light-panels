"""Write the V6 layout footprints into hardware/lib/footprints/ModularLight.pretty (WP 1.3 / 1.5).

  EdgeContacts_SpringPads   strip shortened to 6.0 mm (V5: 8.0), rule area to 6.2 mm, +36V labels
  ControllerJoint_EdgeBoard pads 1.3 x 2.85 mm, row z 2.5..5.35 (2.5 mm fillet land below the controller, 2026-11-21)
  CornerJoint_L / _R        re-laid out for a 13 mm board (pad numbers unchanged)
  Spring_BW0019CG           BAT Wireless BW0019CG-L3.5W1.5H4.3 (LCSC C2826517), origin = contact point

Coordinates in every footprint: +y points toward the WALL edge (PCB y is down; the boards are drawn
with the wall edge at the bottom). z in the notes = height above the wall edge = -y on the board.
Run with any Python 3:  python gen_footprints_v6.py
"""
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.normpath(os.path.join(HERE, '..', '..', 'lib', 'footprints', 'ModularLight.pretty'))


def u(*k):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'modular-light/fp-v6/' + '/'.join(map(str, k))))


def f(v):
    s = f'{v:.4f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


class FP:
    def __init__(self, name, descr, tags, attr='smd exclude_from_pos_files'):
        self.name, self.lines, self.n = name, [], 0
        self.head = [f'(footprint "{name}"', '\t(version 20241229)', '\t(generator "pcbnew")',
                     '\t(generator_version "9.0")', '\t(layer "F.Cu")', f'\t(descr "{descr}")', f'\t(tags "{tags}")']
        self.attr = attr

    def k(self):
        self.n += 1
        return u(self.name, self.n)

    def prop(self, key, val, x, y, layer, hide=False, size=1.0):
        h = ' (hide yes)' if hide else ''
        self.lines.append(f'\t(property "{key}" "{val}" (at {f(x)} {f(y)} 0) (layer "{layer}"){h} (uuid "{self.k()}") '
                          f'(effects (font (size {size} {size}) (thickness {f(size * 0.15)}))))')

    def pad(self, num, x, y, w, h, layers, shape='rect', extra=''):
        ls = ' '.join(f'"{l}"' for l in layers)
        self.lines.append(f'\t(pad "{num}" smd {shape} (at {f(x)} {f(y)}) (size {f(w)} {f(h)}) (layers {ls}){extra} '
                          f'(uuid "{self.k()}"))')

    def rect(self, x0, y0, x1, y1, layer, width=0.1, fill='no'):
        self.lines.append(f'\t(fp_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width {f(width)}) '
                          f'(type solid)) (fill {fill}) (layer "{layer}") (uuid "{self.k()}"))')

    def line(self, x0, y0, x1, y1, layer, width=0.1, typ='solid'):
        self.lines.append(f'\t(fp_line (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width {f(width)}) '
                          f'(type {typ})) (layer "{layer}") (uuid "{self.k()}"))')

    def circle(self, x, y, r, layer, width=0.1, fill='no'):
        self.lines.append(f'\t(fp_circle (center {f(x)} {f(y)}) (end {f(x + r)} {f(y)}) (stroke (width {f(width)}) '
                          f'(type solid)) (fill {fill}) (layer "{layer}") (uuid "{self.k()}"))')

    def text(self, s, x, y, layer, size=0.6, just='left'):
        j = f' (justify {just})' if just else ''
        self.lines.append(f'\t(fp_text user "{s}" (at {f(x)} {f(y)} 0) (layer "{layer}") (uuid "{self.k()}") '
                          f'(effects (font (size {f(size)} {f(size)}) (thickness {f(size * 0.15)})){j}))')

    def raw(self, s):
        self.lines.append('\t' + s)

    def write(self):
        body = self.head[:]
        body += [l for l in self.lines if l.startswith('\t(property')]
        body.append(f'\t(attr {self.attr})')
        body += [l for l in self.lines if not l.startswith('\t(property')]
        body += ['\t(embedded_fonts no)', ')']
        path = os.path.join(LIB, self.name + '.kicad_mod')
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(body) + '\n')
        print('wrote', path)


# ------------------------------------------------------------------ edge contacts (exterior face, B.Cu)
STRIP_TOP = 6.0     # pad tops, z (mm above the wall edge)
RULE_TOP = 5.3      # no-via / no-pour rule area (springs touch at z <= 5.0 incl. tolerances)
MASK_TOP = 6.1      # gold-finger style mask opening over the whole strip
NETS = ['GND', '+36V', 'GND', 'CANH', 'CANL', 'DRIVE', 'SENSE_EDGE', 'SPARE', '+36V', 'GND']
START = {'GND': 0.3, '+36V': 0.6}   # mating stagger; signals 0.9


def edge_contacts():
    fp = FP('EdgeContacts_SpringPads',
            'Seam-bridge contact pads (SPEC V6 3.3): 10 pads on the exterior face B.Cu, 3.0 mm wide at 5.0 mm pitch, '
            'centred. X1..X10 = GND +36V GND CANH CANL DRIVE SENSE_EDGE SPARE +36V GND. Pads start 0.3 (GND) / 0.6 (+36V) / '
            '0.9 mm (signals) from the wall edge and end at z 6.0 mm (V6; V5 was 8.0). The BW0019CG bridge spring touches '
            'at z 3.5 nominal (<= 5.0 incl. tolerances). B.Cu rule area (no pour, no vias, tracks allowed) up to z 5.3, so '
            'each pad may carry vias in its top end (z 5.4-6.0, decision 0007 method); full mask opening up to z 6.1.',
            'edge contact spring seam bridge', attr='smd exclude_from_pos_files allow_soldermask_bridges')
    fp.prop('Reference', 'REF**', 0, -7.2, 'B.SilkS', hide=True)
    fp.prop('Value', 'EdgeContacts_SpringPads', 0, 1.2, 'B.Fab', hide=True)
    for i, net in enumerate(NETS):
        x = -22.5 + 5 * i
        z0 = START.get(net, 0.9)
        h = STRIP_TOP - z0
        fp.pad(f'X{i + 1}', x, -(z0 + h / 2), 3.0, h, ['B.Cu', 'B.Mask'])
    fp.rect(-25, -MASK_TOP, 25, 0, 'B.Mask', width=0, fill='yes')
    fp.raw(f'(zone (net 0) (net_name "") (layers "B.Cu") (uuid "{fp.k()}") (name "contact-strip keepout") (hatch edge 0.5) '
           '(connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no) (keepout (tracks allowed) '
           '(vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) (placement (enabled no) '
           f'(sheetname "")) (fill (thermal_gap 0.5) (thermal_bridge_width 0.5)) (polygon (pts (xy -25 0.2) (xy 25 0.2) '
           f'(xy 25 {f(-RULE_TOP)}) (xy -25 {f(-RULE_TOP)}))))')
    fp.line(-26, 0, 26, 0, 'Dwgs.User')
    fp.line(-26, -3.5, 26, -3.5, 'Dwgs.User', typ='dash')
    fp.text('wall edge (z=0). ENIG, bevel the wall edge. Exterior face (B.Cu) only.', -26, 1.2, 'Cmts.User', 0.8)
    fp.text('dashed line: bridge spring contact point z 3.5 nominal (BW0019CG, bridge base on the wall)', -26, 2.4,
            'Cmts.User', 0.8)
    fp.text('upper dashed line z 5.3: top of the no-via area; in-pad vias allowed above it', -26, 4.8, 'Cmts.User', 0.8)
    fp.text('X1 GND X2 +36V X3 GND X4 CANH X5 CANL X6 DRIVE X7 SENSE_EDGE X8 SPARE X9 +36V X10 GND', -26, 3.6,
            'Cmts.User', 0.8)
    fp.line(-26, -RULE_TOP, 26, -RULE_TOP, 'Dwgs.User', typ='dash')
    fp.rect(-25.5, -(MASK_TOP + 0.3), 25.5, 0.1, 'B.CrtYd', width=0.05)
    fp.write()


# ------------------------------------------------------------------ controller joint, edge-board side
def controller_joint():
    # footprint origin: z 5.25 on the board. Dwgs lines: controller wall face y +0.25 (z 5.0), chamber face y -1.35 (z 6.6)
    top_y, bot_y = -0.1, 2.75           # pad z 5.35 .. 2.5 (roadmap 2.0, user 2026-11-21)
    h = bot_y - top_y
    cy = (top_y + bot_y) / 2
    fp = FP('ControllerJoint_EdgeBoard',
            'Controller joint, edge-board side (SPEC V6.2 3.2/3.5, decision 0009). 10 SMD pads on the inward face (F.Cu), '
            '2.54 mm pitch, 1.3 x 2.85 mm. Place the origin at z 5.25 (the controller underside, z 5.0, is the y = +0.25 '
            'Dwgs line). Pads span z 2.5..5.35: 2.5 mm of exposed fillet land below the controller underside plus 0.35 mm '
            'behind its edge so solder wicks into the gap (2026-11-21; was z 3.5..5.7, only 1.5 mm exposed). Pad n meets the '
            'controller pad n: from the F.Cu side with the wall edge at the bottom, pad 1 is leftmost. Order 1..10: +36V GND '
            '+5V_LED LED_RETURN LED_DATA_OUT SPARE CANH CANL SENSE DRIVE. Pasted so reflow pre-tins them.',
            'controller joint right angle board-to-board drag solder')
    fp.prop('Reference', 'REF**', 0, -2.4, 'F.SilkS', hide=True)
    fp.prop('Value', 'ControllerJoint_EdgeBoard', 0, 3.5, 'F.Fab', hide=True)
    for i in range(10):
        fp.pad(str(i + 1), -11.43 + 2.54 * i, cy, 1.3, h, ['F.Cu', 'F.Paste', 'F.Mask'])
    fp.circle(-12.6, bot_y + 0.5, 0.25, 'F.SilkS', width=0.15, fill='yes')
    fp.line(-13, 0.25, 13, 0.25, 'Dwgs.User', typ='dash')
    fp.line(-13, -1.35, 13, -1.35, 'Dwgs.User', typ='dash')
    fp.text('controller wall-side face (z 5.0); fillet lands below this line', -13.5, 0.9, 'Cmts.User')
    fp.text('controller chamber-side face (z 6.6, 1.6 mm board)', -13.5, -2.0, 'Cmts.User')
    fp.text('WALL EDGE IS BELOW (+y). Pad 1 = +36V (left).', 0, 2.9, 'Cmts.User', just=None)
    fp.rect(-12.33, top_y, 12.33, bot_y, 'F.Fab')
    fp.rect(-12.6, top_y - 0.25, 12.6, bot_y + 0.25, 'F.CrtYd', width=0.05)
    fp.write()


# ------------------------------------------------------------------ corner joints
SIG = [(1, 1.5), (2, 4.0), (3, 6.5), (5, 9.0), (4, 11.5)]      # pad, z centre (F.Cu, 2.0 x 1.3)
PWR = [(6, 0.5, 3.5), (8, 6.0, 8.5), (7, 11.0, 12.6)]           # pad, z0, z1 (B.Cu, 3.0 wide): +36V, GND, +5V_LED


def corner(side):
    s = 1 if side == 'L' else -1
    name = f'CornerJoint_{side}'
    end = 'left' if side == 'L' else 'right'
    fp = FP(name,
            f'Polygon corner joint at the {end} end of a V6 edge board (13 mm tall). Origin = board end (x = 0) on the wall '
            f'edge (y = 0); pads extend {"+" if s > 0 else "-"}x. 5 SMD signal pads on the inward face (F.Cu), 2.0 x 1.3 mm at '
            '2.5 mm pitch (1.2 mm gaps, like the 2.54 mm controller joint): from the wall edge up 1 D (z 1.5), 2 CANH (4.0), '
            '3 CANL (6.5), 5 DRIVE (9.0), 4 SENSE (11.5); this order lets the LED data and the bus reach their pads '
            'without crossing. 3 SMD power pads on the exterior face (B.Cu), 3.0 mm wide: 6 +36V (z 0.5-3.5), '
            '8 GND (z 6.0-8.5), 7 +5V_LED (z 11.0-12.6). GND sits between the supplies with 2.5 mm gaps, so a bead can '
            f'never join +36V to +5V_LED. All pads touch the board end. Mirror of CornerJoint_{"R" if s > 0 else "L"}.',
            'corner joint solder bridge')
    fp.prop('Reference', 'REF**', s * 3.0, -13.8, 'F.SilkS', hide=True)
    fp.prop('Value', name, s * 3.0, 1.2, 'F.Fab', hide=True)
    for num, z in SIG:
        fp.pad(str(num), s * 1.0, -z, 2.0, 1.3, ['F.Cu', 'F.Paste', 'F.Mask'])
    for num, z0, z1 in PWR:
        fp.pad(str(num), s * 1.5, -(z0 + z1) / 2, 3.0, z1 - z0, ['B.Cu', 'B.Mask'])
    fp.line(0, 0.5, 0, -13.5, 'Dwgs.User')
    fp.text('board end (x=0); wall edge at y=0', s * 0.5, 1.0, 'Cmts.User', 0.5, just='left' if s > 0 else 'right')
    xa, xb = sorted((-0.2 * s, 3.3 * s))
    fp.rect(xa, -12.4, xb, 0.1, 'F.CrtYd', width=0.05)
    fp.rect(xa, -12.85, xb, 0.1, 'B.CrtYd', width=0.05)
    fp.write()


# ------------------------------------------------------------------ bridge spring
def spring():
    # datasheet 681-0019C-3 (BW0019CG.pdf p.6): body 3.5 x 1.5, land 2.10 x 1.50 at the contact end,
    # contact dome 0.90 +-0.15 from that end, C-shaped root bend over the other 1.4 mm (0.33 above the PCB).
    # Origin = body centre (the assembly centroid for the JLC CPL). Contact point = (0, +0.85).
    fp = FP('Spring_BW0019CG',
            'BAT Wireless BW0019CG-L3.5W1.5H4.3 SMT antenna spring (LCSC C2826517; BW0019BG-L3.5W1.5H3.8 C2826516 fits). '
            'Drawing 681-0019C-3: body 3.5 x 1.5 mm, free height 4.3, working height 3.0-3.5, land 2.10 x 1.50 at the '
            'contact end. ORIGIN = BODY CENTRE; CONTACT POINT (dome) = (0, +0.85), 0.90 +-0.15 mm from the contact end. '
            'The contact end (free end of the cantilever) points +y: place +y toward the wall so a panel sliding toward the '
            'wall rides over the spring from its root bend. The root bend overhangs the board (y -1.75..-0.35) at 0.33 mm.',
            'spring contact antenna BW0019 seam bridge', attr='smd')
    fp.prop('Reference', 'REF**', 0, -2.4, 'F.SilkS', hide=True, size=0.6)
    fp.prop('Value', 'BW0019CG-L3.5W1.5H4.3', 0, 2.6, 'F.Fab', hide=True, size=0.5)
    fp.pad('1', 0, 0.7, 1.5, 2.1, ['F.Cu', 'F.Paste', 'F.Mask'])
    fp.rect(-0.75, -1.75, 0.75, 1.75, 'F.Fab')
    fp.line(-0.5, 0.85, 0.5, 0.85, 'F.Fab', 0.05)
    fp.line(0, 0.35, 0, 1.35, 'F.Fab', 0.05)
    fp.text('contact', 0.9, 0.85, 'F.Fab', 0.3)
    fp.line(-0.95, -1.9, 0.95, -1.9, 'F.SilkS', 0.12)
    fp.rect(-1.0, -2.0, 1.0, 2.0, 'F.CrtYd', width=0.05)
    fp.raw('(model "${KIPRJMOD}/../lib/3dmodels/Spring_BW0019CG.step"\n\t\t(offset (xyz 0 0 0))\n\t\t(scale (xyz 1 1 1))'
           '\n\t\t(rotate (xyz 0 0 0))\n\t)')
    fp.write()


# ------------------------------------------------------------------ spring test coupon: plated mating pad
def contact_pad():
    fp = FP('ContactPad_3x6',
            'Spring test coupon mating pad: one ENIG pad 3.0 x 6.0 mm on F.Cu (same width as the edge-board contact pads), '
            'no paste. Origin = pad centre = nominal spring contact point. Long axis along y.',
            'spring coupon contact pad ENIG')
    fp.prop('Reference', 'REF**', 0, -3.8, 'F.SilkS', hide=True, size=0.6)
    fp.prop('Value', 'ContactPad_3x6', 0, 3.8, 'F.Fab', hide=True, size=0.5)
    fp.pad('1', 0, 0, 3.0, 6.0, ['F.Cu', 'F.Mask'])
    fp.rect(-1.75, -3.25, 1.75, 3.25, 'F.CrtYd', width=0.05)
    fp.write()


def npth_small():
    fp = FP('NPTH_0.5mm', 'Plain 0.5 mm non-plated hole: mouse-bite breakaway tabs (spring coupon).',
            'npth mouse bite', attr='exclude_from_pos_files exclude_from_bom allow_missing_courtyard board_only')
    fp.prop('Reference', 'REF**', 0, -0.8, 'F.Fab', hide=True, size=0.3)
    fp.prop('Value', 'NPTH_0.5mm', 0, 0.8, 'F.Fab', hide=True, size=0.3)
    fp.raw(f'(pad "" np_thru_hole circle (at 0 0) (size 0.5 0.5) (drill 0.5) (layers "*.Cu" "*.Mask") '
           f'(uuid "{fp.k()}"))')
    fp.write()


if __name__ == '__main__':
    edge_contacts()
    controller_joint()
    corner('L')
    corner('R')
    spring()
    contact_pad()
    npth_small()
