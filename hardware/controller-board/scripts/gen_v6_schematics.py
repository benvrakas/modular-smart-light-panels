"""Generate the V6 KiCad 9 schematics from one source (roadmap WP 1.1 and 1.2):

  hardware/controller-board/controller-board.kicad_sch   (new, decisions 0009/0010)
  hardware/edge-board/edge-board-{hex,square,triangle}.kicad_sch (V6: +24V, joint pads, code-0 option;
  one circuit, one schematic per board outline so each KiCad project has its own)

The circuits are written below as data (one dict per part: pins -> nets). The script places the
symbols automatically in labelled blocks, draws a short wire stub on every pin, and ends each stub in
a net label (signals) or a power symbol (GND, +24V, +5V, +5V_LED, +3V3). Unused pins get a no-connect
flag. Re-run after any change, then run ERC and check the netlist (verify_v6.py does both).

Run with KiCad's Python:  "C:/Program Files/KiCad/9.0/bin/python.exe" gen_v6_schematics.py
The part catalogue (values, LCSC numbers) is shared with make_boms_v6.py.
"""
import math
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kisexp import QStr, q, dump, lib_symbol, symbol_pins, symbol_bbox, prop, find  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, '..', '..'))
PROJECT_LIB = os.path.join(HW, 'lib', 'symbols', 'ModularLight.kicad_sym')
DATE = '2026-11-16'
POWER_NETS = {'GND': 'power:GND', '+24V': 'power:+24V', '+5V': 'power:+5V', '+3V3': 'power:+3V3',
              '+5V_LED': 'ModularLight:+5V_LED'}
G = 1.27  # connection grid

# ------------------------------------------------------------------------------------------ catalogue
# key: (lib_id, value, footprint, LCSC, MPN, manufacturer, description)
FP_R0603 = 'Resistor_SMD:R_0603_1608Metric'
FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
FP_R0402 = 'Resistor_SMD:R_0402_1005Metric'
CAT = {
    # resistors 0603 1 % UNI-ROYAL unless noted
    'R0': ('Device:R', '0R', FP_R0603, 'C21189', '0603WAF0000T5E', 'UNI-ROYAL', ''),
    'R0_0402': ('Device:R', '0R', FP_R0402, 'C17168', '0402WGF0000TCE', 'UNI-ROYAL', ''),  # edge R3: fits under LED1 (z 7.2)
    'R1k': ('Device:R', '1k', FP_R0603, 'C21190', '0603WAF1001T5E', 'UNI-ROYAL', ''),
    'R2k7': ('Device:R', '2k7', FP_R0603, 'C13167', '0603WAF2701T5E', 'UNI-ROYAL', ''),
    'R5k6': ('Device:R', '5k6', FP_R0603, 'C23189', '0603WAF5601T5E', 'UNI-ROYAL', ''),
    'R12k': ('Device:R', '12k', FP_R0603, 'C22790', '0603WAF1202T5E', 'UNI-ROYAL', ''),
    'R27k': ('Device:R', '27k', FP_R0603, 'C22967', '0603WAF2702T5E', 'UNI-ROYAL', ''),
    'R33': ('Device:R', '33R', FP_R0603, 'C23140', '0603WAF330JT5E', 'UNI-ROYAL', ''),
    'R2k2': ('Device:R', '2k2', FP_R0603, 'C4190', '0603WAF2201T5E', 'UNI-ROYAL', ''),
    'R3k3': ('Device:R', '3k3', FP_R0603, 'C22978', '0603WAF3301T5E', 'UNI-ROYAL', ''),
    'R120': ('Device:R', '120R', FP_R0603, 'C22787', '0603WAF1200T5E', 'UNI-ROYAL', ''),
    'R4k7': ('Device:R', '4k7', FP_R0603, 'C23162', '0603WAF4701T5E', 'UNI-ROYAL', ''),
    'R10k': ('Device:R', '10k', FP_R0603, 'C25804', '0603WAF1002T5E', 'UNI-ROYAL', ''),
    'R22k': ('Device:R', '22k', FP_R0603, 'C31850', '0603WAF2202T5E', 'UNI-ROYAL', ''),
    'R100k': ('Device:R', '100k', FP_R0603, 'C25803', '0603WAF1003T5E', 'UNI-ROYAL', ''),
    'R162k': ('Device:R', '162k', FP_R0603, 'C22815', '0603WAF1623T5E', 'UNI-ROYAL', 'TPS54360B RT: 600 kHz'),
    'R53k6': ('Device:R', '53k6', FP_R0603, 'C2930115', 'FRC0603F5362TS', 'FOJAN', 'Buck FB top (TI design example)'),
    'R10k2': ('Device:R', '10k2', FP_R0603, 'C22772', '0603WAF1022T5E', 'UNI-ROYAL', 'Buck FB bottom (TI design example)'),
    'R187k': ('Device:R', '187k', FP_R0603, 'C22896', '0603WAF1873T5E', 'UNI-ROYAL', ''),
    'R10k_0805': ('Device:R', '10k', 'Resistor_SMD:R_0805_2012Metric', 'C17414', '0805W8F1002T5E', 'UNI-ROYAL',
                  '0805 (125 mW): 61 mW in a sustained 28 V fault'),
    'R470_1206': ('Device:R', '470R', 'Resistor_SMD:R_1206_3216Metric', 'C4502', '1206W4F4700T5E', 'UNI-ROYAL',
                  '1206: pulse load while DRIVE is asserted into a 24 V fault'),
    # capacitors
    'C100n': ('Device:C', '100nF', FP_C0603, 'C14663', 'CC0603KRX7R9BB104', 'YAGEO', '50 V X7R'),
    'C15p': ('Device:C', '15pF', FP_C0603, 'C1644', 'CL10C150JB8NNNC', 'Samsung', 'C0G'),
    'C1u': ('Device:C', '1uF', FP_C0603, 'C15849', 'CL10A105KB8NNNC', 'Samsung', '50 V X5R'),
    'C10n': ('Device:C', '10nF', FP_C0603, 'C57112', '0603B103K500NT', 'FH', '50 V X7R'),
    'C22n': ('Device:C', '22nF', FP_C0603, 'C21122', 'CL10B223KB8NNNC', 'Samsung', '50 V X7R'),
    'C100p': ('Device:C', '100pF', FP_C0603, 'C14858', 'CL10C101JB8NNNC', 'Samsung', 'C0G'),
    'C10u': ('Device:C', '10uF', 'Capacitor_SMD:C_0805_2012Metric', 'C15850', 'CL21A106KAYNNNE', 'Samsung', '25 V X5R'),
    'C10u50': ('Device:C', '10uF/50V', 'Capacitor_SMD:C_1206_3216Metric', 'C13585', 'CL31A106KBHNNNE', 'Samsung',
               '50 V X5R 1206 (rated above the 45 V clamp)'),
    'C22u': ('Device:C', '22uF/25V', 'Capacitor_SMD:C_0805_2012Metric', 'C45783', 'CL21A226MAQNNNE', 'Samsung', '25 V X5R'),
    # semiconductors
    'CH32': ('MCU_WCH_RiscV:CH32V203F6P6', 'CH32V203F6P6', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', 'C3040880',
             'CH32V203F6P6', 'WCH', ''),
    'XTAL': ('Device:Crystal_GND24', '8MHz', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', 'C2973805',
             'XL2EL89COI-111YLC-8M', 'YXC', '12 pF, +-10 ppm'),
    'TCAN': ('ModularLight:TCAN1044V', 'TCAN1044VDRQ1', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'C1852061',
             'TCAN1044VDRQ1', 'Texas Instruments', ''),
    'HT7533': ('Regulator_Linear:HT75xx-1-SOT89', 'HT7533-1', 'Package_TO_SOT_SMD:SOT-89-3', 'C14289', 'HT7533-1',
               'Holtek', ''),
    'AHCT': ('74xGxx:74AHCT1G125', 'SN74AHCT1G125', 'Package_TO_SOT_SMD:SOT-23-5', 'C20617903',
             'SN74AHCT1G125DBVR', 'UMW', ''),
    'TPS54360B': ('Regulator_Switching:TPS54360DDA', 'TPS54360BDDAR', 'Package_SO:TI_SO-PowerPAD-8_ThermalVias',
                  'C524806', 'TPS54360BDDAR', 'Texas Instruments', '60 V 3.5 A buck, same pinout as TPS54360DDA'),
    'TLV431': ('ModularLight:TLV431_DBZ', 'TLV431A', 'Package_TO_SOT_SMD:SOT-23', 'C56765', 'TLV431AIDBZR',
               'Texas Instruments', ''),
    'L22u': ('Device:L', '22uH', 'Inductor_SMD:L_Changjiang_FNR6045S', 'C168080', 'FNR6045S220MT', 'cjiang',
             '22 uH, Isat 2.2 A, 116 mOhm, 6x6x4.5 mm shielded'),
    'SS36': ('Device:D_Schottky', 'SS36', 'Diode_SMD:D_SMA', 'C2891719', 'SS36', 'KUU', '60 V 3 A Schottky'),
    'PTC050': ('Device:Polyfuse', '0.5A/60V', 'Fuse:Fuse_1812_4532Metric', 'C70113', 'mSMD050-60V', 'TECHFUSE',
               'PPTC 1812: hold 0.50 A (0.35 A at 60 C), trip 1.0 A, 60 V, 100 A max'),
    'SMAJ28A': ('Diode:SMAJ28A', 'SMAJ28A', 'Diode_SMD:D_SMA', 'C134977', 'SMAJ28A-13-F', 'Diodes Inc',
                '28 V standoff, 45.4 V max clamp'),
    'NUP3105': ('Power_Protection:NUP2105L', 'NUP3105LT1G', 'Package_TO_SOT_SMD:SOT-23', 'C22390031', 'NUP3105LT1G',
                'DOWO', 'dual bidirectional TVS, VRWM 36 V, VBR >= 40 V, 12-16 pF; NUP2105L pinout'),
    'BAT54S': ('Diode:BAT54S', 'BAT54S', 'Package_TO_SOT_SMD:SOT-23', 'C47546', 'BAT54S,215', 'Nexperia', ''),
    '1N4148WS': ('Diode:1N4148WS', '1N4148WS', 'Diode_SMD:D_SOD-323', 'C2128', '1N4148WS', 'JSCJ', ''),
    'AO3401A': ('Transistor_FET:AO3401A', 'AO3401A', 'Package_TO_SOT_SMD:SOT-23', 'C15127', 'AO3401A', 'AOS',
                'P-MOSFET -30 V -4 A, 60 mOhm at -4.5 V'),
    '2N7002': ('Transistor_FET:2N7002', '2N7002', 'Package_TO_SOT_SMD:SOT-23', 'C8545', '2N7002', 'JSCJ',
               'N-MOSFET 60 V 115 mA'),
    'LED': ('ModularLight:SK6812RGBW', 'SKC6812RGBW-NW', 'ModularLight:LED_SKC6812RGBW_5050-4', 'C5348912',
            'SKC6812RGBW-NW', 'OPSCO', ''),
    # no-BOM items (pads, jumpers, connectors made of copper only)
    'TP': ('Connector:TestPoint', 'TP', 'TestPoint:TestPoint_Pad_D1.5mm', '', '', '', ''),
    'JP': ('Jumper:SolderJumper_2_Open', 'TERM', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', '', '', '', ''),
    'JOINT_CTL': ('ModularLight:ControllerJoint', 'ControllerJoint', 'ModularLight:ControllerJoint_ControllerEdge',
                  '', '', '', ''),
    'JOINT_EDGE': ('ModularLight:ControllerJoint', 'ControllerJoint', 'ModularLight:ControllerJoint_EdgeBoard',
                   '', '', '', ''),
    'EDGE': ('ModularLight:EdgeContacts24V', 'EdgeContacts', 'ModularLight:EdgeContacts_SpringPads', '', '', '', ''),
    'CORNER_L': ('ModularLight:CornerJoint24V', 'Corner IN', 'ModularLight:CornerJoint_L', '', '', '', ''),
    'CORNER_R': ('ModularLight:CornerJoint24V', 'Corner OUT', 'ModularLight:CornerJoint_R', '', '', '', ''),
    'FLAG': ('power:PWR_FLAG', 'PWR_FLAG', '', '', '', '', ''),
}

# R_ID per edge code (SPEC 4.2). Code 0 = 0 R and the code-0 link variant (R3 DNP).
ID_CODES = {0: 'R0', 1: 'R1k', 2: 'R2k7', 3: 'R5k6', 4: 'R12k', 5: 'R27k'}

NC = None


def P(ref, key, nets, block, pop='ALL', note='', value=None, dnp=False, fields=None):
    return dict(ref=ref, key=key, nets=nets, block=block, pop=pop, note=note, value=value, dnp=dnp,
                fields=fields or {})


# ------------------------------------------------------------------------------- controller board
def controller_parts():
    B_MCU, B_CAN, B_JNT, B_BUCK, B_3V3, B_LED, B_DISC, B_TP, B_PF = (
        'MCU (CH32V203F6P6, decision 0008 pins)', 'CAN (TCAN1044V, +-58 V bus pins)',
        'Controller joint (10 pads, drag-soldered at 90 deg to the code-0 edge board)',
        '24 V input and 5 V buck (TPS54360B, always on; TI datasheet 8.2.2 procedure)',
        '3.3 V logic supply (HT7533 from +5V) and 3V3 over-voltage shunt',
        'LED rail switch (default OFF) and LED data / loop-back',
        'Discovery SENSE / DRIVE (24 V fault tolerant)', 'Test pads (pogo jig)', 'Power flags (ERC)')
    p = []
    a = p.append
    # MCU
    a(P('U1', 'CH32', {'1': 'BOOT0', '2': 'OSC_IN', '3': 'OSC_OUT', '4': 'NRST', '5': '+3V3', '6': 'LED_EN',
                       '7': 'SENSE_ADC', '8': 'UART_TX', '9': 'UART_RX', '10': 'DRIVE_EN', '11': 'CAN_STB',
                       '12': 'LED_RET', '13': 'LED_DATA', '14': 'GPIO_SPARE', '15': 'GND', '16': '+3V3',
                       '17': 'CAN_RX', '18': 'CAN_TX', '19': 'SWDIO', '20': 'SWCLK'}, B_MCU))
    a(P('Y1', 'XTAL', {'1': 'OSC_IN', '3': 'OSC_OUT', '2': 'GND', '4': 'GND'}, B_MCU))
    a(P('C5', 'C15p', {'1': 'OSC_IN', '2': 'GND'}, B_MCU))
    a(P('C6', 'C15p', {'1': 'OSC_OUT', '2': 'GND'}, B_MCU))
    a(P('C7', 'C100n', {'1': '+3V3', '2': 'GND'}, B_MCU, note='at U1 VDD pin 16'))
    a(P('C8', 'C100n', {'1': '+3V3', '2': 'GND'}, B_MCU, note='at U1 VDDA pin 5'))
    a(P('C9', 'C1u', {'1': '+3V3', '2': 'GND'}, B_MCU))
    a(P('C10', 'C100n', {'1': 'NRST', '2': 'GND'}, B_MCU))
    a(P('R15', 'R4k7', {'1': 'BOOT0', '2': 'GND'}, B_MCU))
    # CAN
    a(P('U2', 'TCAN', {'1': 'CAN_TX', '2': 'GND', '3': '+5V', '4': 'CAN_RX', '5': '+3V3', '6': 'CANL', '7': 'CANH',
                       '8': 'CAN_STB'}, B_CAN, note='STB has an internal pull-up: standby until firmware drives PA5 low'))
    a(P('C11', 'C100n', {'1': '+5V', '2': 'GND'}, B_CAN, note='U2 VCC'))
    a(P('C24', 'C100n', {'1': '+3V3', '2': 'GND'}, B_CAN, note='U2 VIO'))
    a(P('D4', 'NUP3105', {'1': 'CANH', '2': 'CANL', '3': 'GND'}, B_CAN))
    a(P('R12', 'R120', {'1': 'CANH', '2': 'CAN_TERM'}, B_CAN))
    a(P('JP1', 'JP', {'1': 'CAN_TERM', '2': 'CANL'}, B_CAN, note='open; close only on the segment far-end node'))
    # joint
    a(P('J1', 'JOINT_CTL', {'1': '+24V_IN', '2': 'GND', '3': '+5V_LED', '4': 'LED_RETURN', '5': 'LED_DATA_OUT',
                            '6': 'SPARE', '7': 'CANH', '8': 'CANL', '9': 'SENSE', '10': 'DRIVE'}, B_JNT))
    a(P('R26', 'R10k', {'1': 'SPARE', '2': 'GPIO_SPARE'}, B_JNT, pop='DNP', dnp=True,
        note='DNP option: SPARE to PB1. 10k keeps a 24 V fault at 2 mA / 58 mW'))
    # buck
    a(P('F1', 'PTC050', {'1': '+24V_IN', '2': '+24V'}, B_BUCK,
        note='per-panel PTC upstream of D5: a shorted TVS or controller trips F1, not the domain fuse'))
    a(P('D5', 'SMAJ28A', {'1': '+24V', '2': 'GND'}, B_BUCK))
    a(P('C16', 'C10u50', {'1': '+24V', '2': 'GND'}, B_BUCK))
    a(P('C23', 'C10u50', {'1': '+24V', '2': 'GND'}, B_BUCK))
    a(P('C17', 'C100n', {'1': '+24V', '2': 'GND'}, B_BUCK, note='at U5 VIN'))
    a(P('U5', 'TPS54360B', {'1': 'BUCK_BOOT', '2': '+24V', '3': NC, '4': 'BUCK_RT', '5': 'BUCK_FB', '6': 'BUCK_COMP',
                            '7': 'GND', '8': 'BUCK_SW', '9': 'GND'}, B_BUCK,
        note='EN left open: internal pull-up enables it (always on), internal UVLO 4.3 V'))
    a(P('R19', 'R162k', {'1': 'BUCK_RT', '2': 'GND'}, B_BUCK))
    a(P('C18', 'C100n', {'1': 'BUCK_BOOT', '2': 'BUCK_SW'}, B_BUCK))
    a(P('D7', 'SS36', {'1': 'BUCK_SW', '2': 'GND'}, B_BUCK))
    a(P('L1', 'L22u', {'1': 'BUCK_SW', '2': '+5V'}, B_BUCK))
    a(P('C19', 'C22u', {'1': '+5V', '2': 'GND'}, B_BUCK))
    a(P('C20', 'C22u', {'1': '+5V', '2': 'GND'}, B_BUCK))
    a(P('R16', 'R53k6', {'1': '+5V', '2': 'BUCK_FB'}, B_BUCK))
    a(P('R17', 'R10k2', {'1': 'BUCK_FB', '2': 'GND'}, B_BUCK))
    a(P('R20', 'R4k7', {'1': 'BUCK_COMP', '2': 'BUCK_CZ'}, B_BUCK))
    a(P('C21', 'C22n', {'1': 'BUCK_CZ', '2': 'GND'}, B_BUCK))
    a(P('C22', 'C100p', {'1': 'BUCK_COMP', '2': 'GND'}, B_BUCK))
    # 3.3 V
    a(P('U3', 'HT7533', {'1': 'GND', '2': '+5V', '3': '+3V3'}, B_3V3))
    a(P('C12', 'C10u', {'1': '+5V', '2': 'GND'}, B_3V3))
    a(P('C13', 'C10u', {'1': '+3V3', '2': 'GND'}, B_3V3))
    a(P('U6', 'TLV431', {'1': 'V3_SHUNT_REF', '2': '+3V3', '3': 'GND'}, B_3V3,
        note='Sinks fault current injected into 3V3 (SENSE short to 24 V): trips at ~3.56 V'))
    a(P('R24', 'R187k', {'1': '+3V3', '2': 'V3_SHUNT_REF'}, B_3V3))
    a(P('R25', 'R100k', {'1': 'V3_SHUNT_REF', '2': 'GND'}, B_3V3))
    # LED switch + data
    a(P('Q1', 'AO3401A', {'1': 'LED_GATE', '2': '+5V', '3': '+5V_LED'}, B_LED))
    a(P('R21', 'R100k', {'1': '+5V', '2': 'LED_GATE'}, B_LED, note='gate pull-up: rail OFF by default'))
    a(P('R22', 'R22k', {'1': 'LED_GATE', '2': 'LED_PD'}, B_LED))
    a(P('C25', 'C22n', {'1': 'LED_GATE', '2': '+5V_LED'}, B_LED, note='gate-drain slew cap: ~0.9 ms ramp, ~0.2 A inrush'))
    a(P('Q2', '2N7002', {'1': 'LED_EN', '2': 'GND', '3': 'LED_PD'}, B_LED))
    a(P('R18', 'R100k', {'1': 'LED_EN', '2': 'GND'}, B_LED, note='holds the rail off while PA0 floats (reset/boot)'))
    a(P('U4', 'AHCT', {'1': 'GND', '2': 'LED_DATA', '3': 'GND', '4': 'LED_DATA_5V', '5': '+5V_LED'}, B_LED,
        note='powered from the switched rail: cannot back-power unpowered LEDs'))
    a(P('C15', 'C100n', {'1': '+5V_LED', '2': 'GND'}, B_LED))
    a(P('R5', 'R33', {'1': 'LED_DATA_5V', '2': 'LED_DATA_OUT'}, B_LED))
    a(P('R7', 'R2k2', {'1': 'LED_RETURN', '2': 'LED_RET'}, B_LED))
    a(P('R8', 'R3k3', {'1': 'LED_RET', '2': 'GND'}, B_LED))
    # discovery
    a(P('R9', 'R10k_0805', {'1': '+3V3', '2': 'SENSE'}, B_DISC, note='SENSE pull-up R_pu (SPEC 4.1)'))
    a(P('R10', 'R10k_0805', {'1': 'SENSE', '2': 'SENSE_ADC'}, B_DISC))
    a(P('C14', 'C10n', {'1': 'SENSE_ADC', '2': 'GND'}, B_DISC))
    a(P('D2', 'BAT54S', {'1': 'GND', '2': '+3V3', '3': 'SENSE_ADC'}, B_DISC))
    a(P('Q3', '2N7002', {'1': 'DRIVE_EN', '2': 'GND', '3': 'DRIVE_SW'}, B_DISC,
        note='open-drain DRIVE: off = Hi-Z (60 V), on = pull low'))
    a(P('R11', 'R470_1206', {'1': 'DRIVE_SW', '2': 'DRIVE'}, B_DISC))
    a(P('R23', 'R100k', {'1': 'DRIVE_EN', '2': 'GND'}, B_DISC))
    a(P('D6', 'NUP3105', {'1': 'SENSE', '2': 'DRIVE', '3': 'GND'}, B_DISC, note='ESD on the SENSE/DRIVE buses'))
    # test pads
    for ref, net in [('TP1', 'SPARE'), ('TP2', '+3V3'), ('TP3', 'GND'), ('TP4', 'SWDIO'), ('TP5', 'SWCLK'),
                     ('TP6', 'NRST'), ('TP7', 'UART_TX'), ('TP8', 'UART_RX'), ('TP9', 'GPIO_SPARE'),
                     ('TP10', '+24V_IN'), ('TP11', '+5V'), ('TP12', '+5V_LED'), ('TP13', '+24V')]:
        a(P(ref, 'TP', {'1': net}, B_TP, value=net))
    # power flags: nets that carry power_in pins but no power_out pin
    for i, net in enumerate(['+24V', 'GND', '+5V', '+5V_LED'], 1):
        a(P(f'#FLG{i:02d}', 'FLAG', {'1': net}, B_PF))
    blocks = [B_MCU, B_CAN, B_JNT, B_BUCK, B_3V3, B_LED, B_DISC, B_TP, B_PF]
    return p, blocks


# ---------------------------------------------------------------------------------- passive board
def passive_parts():
    B_LED, B_ID, B_EDGE, B_JNT, B_TP, B_PF = (
        'LEDs on the switched +5V_LED rail', 'Edge ID (SPEC 4.1): D1 + R_ID',
        'Seam-bridge contacts and corner joints', 'Controller joint pads + code-0 population option',
        'Test pads', 'Power flags (ERC)')
    p = []
    a = p.append
    a(P('LED1', 'LED', {'2': 'LED1_DI', '4': 'LED_D1', '3': '+5V_LED', '1': 'GND'}, B_LED))
    a(P('LED2', 'LED', {'2': 'LED_D1', '4': 'LED_D2', '3': '+5V_LED', '1': 'GND'}, B_LED))
    a(P('LED3', 'LED', {'2': 'LED_D2', '4': 'D_OUT', '3': '+5V_LED', '1': 'GND'}, B_LED))
    for r in ('C1', 'C2', 'C3'):
        a(P(r, 'C100n', {'1': '+5V_LED', '2': 'GND'}, B_LED, note='one per LED, at VDD/GND'))
    a(P('C4', 'C10u', {'1': '+5V_LED', '2': 'GND'}, B_LED))
    a(P('D1', '1N4148WS', {'2': 'SENSE', '1': 'ID_K'}, B_ID))
    a(P('R1', 'R1k', {'1': 'ID_K', '2': 'SENSE_EDGE'}, B_ID, pop='PER-CODE', value='R_ID',
        note='BOM variant: code 0 = 0R, 1 = 1k, 2 = 2k7, 3 = 5k6, 4 = 12k, 5 = 27k'))
    a(P('R2', 'R0', {'1': 'ID_K', '2': 'SENSE'}, B_ID, pop='DNP', dnp=True, note='DNP: diode bypass'))
    a(P('J1', 'EDGE', {'X1': 'GND', 'X2': '+24V', 'X3': 'GND', 'X4': 'CANH', 'X5': 'CANL', 'X6': 'DRIVE',
                       'X7': 'SENSE_EDGE', 'X8': 'SPARE', 'X9': '+24V', 'X10': 'GND'}, B_EDGE))
    a(P('J2', 'CORNER_L', {'1': 'D_IN', '2': 'CANH', '3': 'CANL', '4': 'SENSE', '5': 'DRIVE', '6': '+24V',
                           '7': '+5V_LED', '8': 'GND'}, B_EDGE))
    a(P('J3', 'CORNER_R', {'1': 'D_OUT', '2': 'CANH', '3': 'CANL', '4': 'SENSE', '5': 'DRIVE', '6': '+24V',
                           '7': '+5V_LED', '8': 'GND'}, B_EDGE))
    a(P('J4', 'JOINT_EDGE', {'1': '+24V', '2': 'GND', '3': '+5V_LED', '4': 'D_IN', '5': 'LED1_DI', '6': 'SPARE',
                             '7': 'CANH', '8': 'CANL', '9': 'SENSE', '10': 'DRIVE'}, B_JNT,
        note='used only on the code-0 board'))
    a(P('R3', 'R0_0402', {'1': 'D_IN', '2': 'LED1_DI'}, B_JNT, pop='NOT-CODE0',
        note='code-0 link: fitted on codes 1-5, DNP on code 0'))
    for ref, net in [('TP1', 'SPARE'), ('TP3', 'GND'), ('TP10', '+24V'), ('TP11', '+5V_LED')]:
        a(P(ref, 'TP', {'1': net}, B_TP, value=net))
    for i, net in enumerate(['GND', '+5V_LED', '+24V'], 1):
        a(P(f'#FLG{i:02d}', 'FLAG', {'1': net}, B_PF))
    blocks = [B_LED, B_ID, B_EDGE, B_JNT, B_TP, B_PF]
    return p, blocks


# ----------------------------------------------------------------------------------- geometry
def uid(*parts):
    return QStr(str(uuid.uuid5(uuid.NAMESPACE_URL, 'modular-light/v6/' + '/'.join(parts))))


def snap(v, g=2.54):
    return round(math.ceil(v / g - 1e-9) * g, 4)


def rnd(v):
    return round(v + 0.0, 4)


DIRS = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}  # sch-space unit vectors for an outward angle


def text_w(s):
    return 1.05 * len(s) + 1.0


class Sheet:
    def __init__(self, name, root_uuid, paper, title, comments):
        self.name, self.root, self.paper, self.title, self.comments = name, QStr(root_uuid), paper, title, comments
        self.libs = {}
        self.items = []
        self.pwr_n = 0

    def lib(self, lib_id):
        if lib_id not in self.libs:
            l, n = lib_id.split(':')
            self.libs[lib_id] = lib_symbol(l, n, PROJECT_LIB)
        return self.libs[lib_id]

    # extents of a part in sch coords relative to its origin: (xmin, ymin, xmax, ymax)
    def extents(self, part):
        sym = self.lib(CAT[part['key']][0])
        bx0, by0, bx1, by1 = symbol_bbox(sym)
        xs = [bx0, bx1]
        ys = [-by1, -by0]
        for pin in symbol_pins(sym):
            net = part['nets'].get(pin['number'], NC)
            ang = int(pin['angle'] + 180) % 360
            dx, dy = DIRS[ang]
            ex, ey = pin['x'], -pin['y']
            sx, sy = ex + dx * 2.54, ey + dy * 2.54
            if net is None:
                ln = 1.5
            elif net in POWER_NETS:
                ln = 6.5 if dx == 0 else 3.3 + text_w(net)
            else:
                ln = text_w(net)
            xs += [sx + dx * ln, sx]
            ys += [sy + dy * ln, sy]
            if dx == 0:
                xs += [sx - 1.5, sx + 1.5]
            else:
                ys += [sy - 1.5, sy + 1.5]
        right_pins = any(int(p['angle']) == 180 for p in symbol_pins(sym))
        val = part['value'] or CAT[part['key']][1]
        if part['key'] == 'FLAG' or part['ref'].startswith('#'):
            pass
        elif not right_pins:
            xs.append(bx1 + 2.0 + text_w(max(part['ref'], val, key=len)))
        else:
            ys.append(max(ys) + 6.0)
            xs.append(text_w(val) / 2)
        return min(xs), min(ys), max(xs), max(ys)

    def place_blocks(self, parts, blocks, x0, y0, page_w, gap=7.62):
        """Shelf-pack parts inside blocks, blocks flow across the page."""
        bx, by, row_h = x0, y0, 0.0
        for b in blocks:
            members = [p for p in parts if p['block'] == b]
            width = 190 if len(members) > 6 else 120
            if any(p['key'] in ('CH32',) for p in members):
                width = 175
            # pack
            cx, cy, rh, used_w = 0.0, 8.0, 0.0, 0.0
            pos = []
            for p in members:
                e = self.extents(p)
                w, h = e[2] - e[0], e[3] - e[1]
                if cx > 0 and cx + w > width:
                    cx, cy, rh = 0.0, cy + rh + gap, 0.0
                pos.append((p, cx - e[0], cy - e[1]))
                cx += w + gap
                rh = max(rh, h)
                used_w = max(used_w, cx)
            bw, bh = max(used_w, 1.7 * len(b) + 4), cy + rh + 4
            if bx > x0 and bx + bw > x0 + page_w:
                bx, by, row_h = x0, by + row_h + 12.7, 0.0
            ox, oy = snap(bx), snap(by)
            self.items.append(('text', b, ox, oy + 2.54, 2.0))
            self.items.append(('rect', ox - 2.54, oy - 1.27, ox + bw, oy + bh))
            for p, rx, ry in pos:
                p['at'] = (snap(ox + rx), snap(oy + ry))
            bx += bw + 12.7
            row_h = max(row_h, bh)
        return by + row_h + 12.7

    # ------------------------------------------------------------------------------ emitters
    def emit_part(self, p, project):
        lib_id, val, fp, lcsc, mpn, mfr, desc = CAT[p['key']]
        sym = self.lib(lib_id)
        X, Y = p['at']
        ref = p['ref']
        value = p['value'] or val
        is_flag = p['key'] == 'FLAG'
        pins = symbol_pins(sym)
        names = {pin['number'] for pin in pins}
        missing = names - set(p['nets'])
        assert not missing, f"{ref}: pins without a net or NC: {sorted(missing)}"
        extra = set(p['nets']) - names
        assert not extra, f"{ref}: unknown pins {extra}"
        bx0, by0, bx1, by1 = symbol_bbox(sym)
        right_pins = any(int(pp['angle']) == 180 for pp in pins)
        if is_flag:
            rpos, vpos, just = (X, Y + 2.54), (X, Y - 3.81), None
        elif not right_pins:
            rpos, vpos, just = (X + bx1 + 1.27, Y - 1.27), (X + bx1 + 1.27, Y + 1.27), 'left'
        else:
            e = self.extents(p)
            rpos, vpos, just = (X, Y + e[3] - 3.81), (X, Y + e[3] - 1.27), None
        fields = [('Reference', ref, rpos, is_flag), ('Value', value, vpos, False),
                  ('Footprint', fp, (X, Y), True), ('Datasheet', str(prop(sym, 'Datasheet')[2]) if prop(sym, 'Datasheet') else '', (X, Y), True),
                  ('Description', desc or (str(prop(sym, 'Description')[2]) if prop(sym, 'Description') else ''), (X, Y), True)]
        if not is_flag:
            fields += [('LCSC', lcsc, (X, Y), True), ('MPN', mpn, (X, Y), True), ('Manufacturer', mfr, (X, Y), True),
                       ('Pop', p['pop'], (X, Y), True)]
            if p['note']:
                fields.append(('Note', p['note'], (X, Y), True))
        node = ['symbol', ['lib_id', q(lib_id)], ['at', rnd(X), rnd(Y), 0], ['unit', 1],
                ['exclude_from_sim', 'no'], ['in_bom', 'no' if is_flag else 'yes'], ['on_board', 'no' if is_flag else 'yes'],
                ['dnp', 'yes' if p['dnp'] else 'no'], ['uuid', uid(self.name, ref)]]
        for k, v, (fx, fy), hide in fields:
            eff = ['effects', ['font', ['size', 1.27, 1.27]]]
            if just:
                eff.append(['justify', just])
            if hide:
                eff.append(['hide', 'yes'])
            node.append(['property', q(k), q(v), ['at', rnd(fx), rnd(fy), 0], eff])
        for pin in pins:
            node.append(['pin', q(pin['number']), ['uuid', uid(self.name, ref, 'pin', pin['number'])]])
        node.append(['instances', ['project', q(project), ['path', q('/' + self.root), ['reference', q(ref)], ['unit', 1]]]])
        self.items.append(('raw', node))
        # stubs, labels, power symbols, no-connects
        for pin in pins:
            net = p['nets'][pin['number']]
            ex, ey = rnd(X + pin['x']), rnd(Y - pin['y'])
            ang = int(pin['angle'] + 180) % 360
            if net is None:
                self.items.append(('raw', ['no_connect', ['at', ex, ey], ['uuid', uid(self.name, ref, 'nc', pin['number'])]]))
                continue
            dx, dy = DIRS[ang]
            sx, sy = rnd(ex + dx * 2.54), rnd(ey + dy * 2.54)
            self.items.append(('raw', ['wire', ['pts', ['xy', ex, ey], ['xy', sx, sy]],
                                       ['stroke', ['width', 0], ['type', 'default']],
                                       ['uuid', uid(self.name, ref, 'w', pin['number'])]]))
            if net in POWER_NETS:
                self.emit_power(net, sx, sy, f"{ref}.{pin['number']}", (dx, dy))
            else:
                just = {0: 'left', 180: 'right', 90: 'left', 270: 'right'}[ang]
                self.items.append(('raw', ['label', q(net), ['at', sx, sy, {0: 0, 180: 180, 90: 90, 270: 270}[ang]],
                                           ['fields_autoplaced', 'yes'],
                                           ['effects', ['font', ['size', 1.27, 1.27]], ['justify', just, 'bottom']],
                                           ['uuid', uid(self.name, ref, 'lbl', pin['number'])]]))

    def emit_power(self, net, x, y, tag, d=(0, -1)):
        """Power symbol whose body points along the stub direction d (sch coords, y down)."""
        lib_id = POWER_NETS[net]
        sym = self.lib(lib_id)
        self.pwr_n += 1
        ref = f"#PWR{self.pwr_n:03d}"
        gnd = net == 'GND'
        # KiCad rotation is counter-clockwise on screen. +V bodies point up at 0 deg, GND bodies point down.
        rot = ({(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270} if gnd else
               {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270})[d]
        if d[0] == 0:
            off = 5.08 if gnd else 3.81
        else:
            off = 3.3 + 0.5 * text_w(net)
        vx, vy = x + d[0] * off, y + d[1] * off
        node = ['symbol', ['lib_id', q(lib_id)], ['at', rnd(x), rnd(y), rot], ['unit', 1], ['exclude_from_sim', 'no'],
                ['in_bom', 'yes'], ['on_board', 'yes'], ['dnp', 'no'], ['uuid', uid(self.name, 'pwr', tag)],
                ['property', q('Reference'), q(ref), ['at', rnd(x), rnd(y), 0],
                 ['effects', ['font', ['size', 1.27, 1.27]], ['hide', 'yes']]],
                ['property', q('Value'), q(net), ['at', rnd(vx), rnd(vy), 90 if rot in (90, 270) else 0],
                 ['effects', ['font', ['size', 1.0, 1.0]]]],
                ['property', q('Footprint'), q(''), ['at', rnd(x), rnd(y), 0], ['effects', ['font', ['size', 1.27, 1.27]], ['hide', 'yes']]],
                ['property', q('Datasheet'), q(''), ['at', rnd(x), rnd(y), 0], ['effects', ['font', ['size', 1.27, 1.27]], ['hide', 'yes']]],
                ['property', q('Description'), q(str(prop(sym, 'Description')[2])), ['at', rnd(x), rnd(y), 0],
                 ['effects', ['font', ['size', 1.27, 1.27]], ['hide', 'yes']]],
                ['pin', q('1'), ['uuid', uid(self.name, 'pwr', tag, 'pin')]],
                ['instances', ['project', q(self.project), ['path', q('/' + self.root), ['reference', q(ref)], ['unit', 1]]]]]
        self.items.append(('raw', node))

    def write(self, path, project, parts, notes):
        self.project = project
        body = []
        for p in parts:
            self.emit_part(p, project)
        out = ['kicad_sch', ['version', 20250114], ['generator', q('eeschema')], ['generator_version', q('9.0')],
               ['uuid', self.root], ['paper', q(self.paper)],
               ['title_block', ['title', q(self.title)], ['date', q(DATE)], ['rev', q('B')],
                ['company', q('Modular Smart Light Panels')]] + [['comment', i + 1, q(c)] for i, c in enumerate(self.comments)],
               ['lib_symbols'] + [self.libs[k] for k in sorted(self.libs)]]
        n = 0
        for it in self.items:
            if it[0] == 'raw':
                body.append(it[1])
            elif it[0] == 'text':
                n += 1
                _, s, x, y, size = it
                body.append(['text', q(s), ['exclude_from_sim', 'no'], ['at', rnd(x), rnd(y), 0],
                             ['effects', ['font', ['size', size, size], ['bold', 'yes']], ['justify', 'left', 'bottom']],
                             ['uuid', uid(self.name, 'text', str(n))]])
            elif it[0] == 'rect':
                n += 1
                _, x0, y0, x1, y1 = it
                body.append(['rectangle', ['start', rnd(x0), rnd(y0)], ['end', rnd(x1), rnd(y1)],
                             ['stroke', ['width', 0], ['type', 'dash']], ['fill', ['type', 'none']],
                             ['uuid', uid(self.name, 'rect', str(n))]])
        for i, (x, y, s) in enumerate(notes):
            body.append(['text', q(s), ['exclude_from_sim', 'no'], ['at', rnd(x), rnd(y), 0],
                         ['effects', ['font', ['size', 1.27, 1.27]], ['justify', 'left', 'top']],
                         ['uuid', uid(self.name, 'note', str(i))]])
        out += body
        out += [['sheet_instances', ['path', q('/'), ['page', q('1')]]], ['embedded_fonts', 'no']]
        text = dump(out) + '\n'
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        return path


# --------------------------------------------------------------------------------------- notes
CTRL_NOTES = """DESIGN NOTES (details and calculations: hardware/controller-board/SCHEMATIC-NOTES.md)
1. All parts on ONE side (F.Cu = wall side). B.Cu is plain white solder mask (back reflector). Joint J1 pads on F.Cu only.
2. Joint pin order 1..10: +24V GND +5V_LED LED_RETURN LED_DATA_OUT SPARE CANH CANL SENSE DRIVE.
   +24V sits at the end next to GND only (a bridge to anything else would put 24 V on a 5 V or 3.3 V net);
   DRIVE is at the far end; +5V_LED and +24V are separated by GND. Pad n meets pad n on the edge board.
3. Buck U5: 24 V -> 5 V, fsw 600 kHz (RT 162k), L 22 uH, Cout 2 x 22 uF, FB 53k6/10k2 (5.00 V), Rc 4k7 + Cc 22 nF + Chf 100 pF.
   EN open = always on. Everything on +24V is rated >= 50 V (SMAJ28A clamps at <= 45.4 V).
   F1 (PTC 0.5 A hold / 1 A trip / 60 V) sits between joint pad 1 (+24V_IN) and +24V, upstream of D5:
   a failed TVS or a controller short trips F1 instead of the domain fuse. TP10 = +24V_IN (jig feeds through F1), TP13 = +24V.
4. LED rail: Q1 P-MOSFET, default OFF (R21 pull-up, R18 holds Q2 off while PA0 floats). C25 sets a ~0.9 ms soft start.
   U4 runs from +5V_LED, so LED data cannot back-power unlit LEDs.
   Firmware: blank the LEDs before switching the rail off (the off-ramp is ~3-6 ms).
5. DRIVE: Q3 open-drain + R11 470R. With Q3 off, a sustained 24 V short on DRIVE draws no current. While Q3 pulls low into such
   a fault, R11 takes 51 mA / 1.2 W (1.7 W at 28 V): firmware limits DRIVE assertion to <= 5 ms per discovery slot.
6. SENSE: R9/R10 10k 0805 survive a sustained 28 V short (61 mW each). The ~4.9 mA they inject into 3V3 is sunk by the
   U6 shunt (trips ~3.56 V; CH32V203 VDD abs max 4.0 V).
7. CAN TVS D4 NUP3105L: 36 V standoff (> 28 V bus maximum), 60 V max clamp at 6 A, 12-16 pF. TCAN1044V bus pins: +-58 V.
8. R26 (SPARE -> PB1) is DNP. JP1 CAN termination is open, closed only on the segment's far-end node."""

PASSIVE_NOTES = """DESIGN NOTES (V6, decisions 0009/0010; details: hardware/controller-board/SCHEMATIC-NOTES.md)
1. All edge boards are this one passive design. +12V is now +24V. The LEDs and their decoupling sit on +5V_LED, the switched rail
   made on the controller board.
2. J4 = controller-joint pads on the inward face (F.Cu), used only on the code-0 board. Pad n meets the controller's pad n:
   seen from each board's F.Cu side with the joint edge at the bottom (wall edge here), pad 1 (+24V) is leftmost on both.
3. Code-0 population option: J4.4 (LED_RETURN) is wired to D_IN (corner-IN D pad) and J4.5 (LED_DATA_OUT) to LED1 DIN.
   R3 (0R) joins D_IN to LED1 DIN.
   - Codes 1-5: R3 fitted. The corner-IN data feeds LED1. J4 is unused (bare pads).
   - Code 0: R3 DNP. LED1 is fed from the controller (J4.5), and the corner-IN data (the last LED of the panel) returns
     to the controller (J4.4).
4. R1 (R_ID) per BOM variant: code 0 = 0R, 1 = 1k, 2 = 2k7, 3 = 5k6, 4 = 12k, 5 = 27k (SPEC 4.2). R2 DNP (diode bypass).
5. Corner power pads keep the order +5V_LED / GND / +24V (GND between the supplies; a bead joining +24V to +5V_LED would put 24 V
   on every LED)."""


def main():
    os.makedirs(os.path.join(HW, 'controller-board'), exist_ok=True)
    parts, blocks = controller_parts()
    sh = Sheet('controller', 'b6f0e2a4-5c1d-4e7a-9a63-2f1c0d6e7b10', 'A2',
               'Controller Board (4-layer, rear of panel)',
               ['SPEC V6.1.1, decisions 0008/0009/0010. One design for every shape.',
                'Trapezoid, 60 deg sides, base <= 72 mm. Parts on F.Cu (wall side) only.',
                'Generated by scripts/gen_v6_schematics.py: edit the script.'])
    ybot = sh.place_blocks(parts, blocks, 25.4, 20.32, 540)
    out1 = sh.write(os.path.join(HW, 'controller-board', 'controller-board.kicad_sch'), 'controller-board', parts,
                    [(25.4, snap(ybot), CTRL_NOTES)])
    pparts, pblocks = passive_parts()
    sh2 = Sheet('passive', '31d76450-c938-4aab-b2a4-f089ddd32585', 'A3',
                'Edge Board - PASSIVE (2-layer), V6',
                ['SPEC V6.1.1, decisions 0009/0010. Every edge; codes 0-5 = BOM variants.',
                 '24 V bus, LEDs on +5V_LED, controller-joint pads, code-0 option (R3).',
                 'Generated by controller-board/scripts/gen_v6_schematics.py.'])
    ybot2 = sh2.place_blocks(pparts, pblocks, 25.4, 20.32, 370)
    for shape in ('hex', 'square', 'triangle'):
        out2 = sh2.write(os.path.join(HW, 'edge-board', f'edge-board-{shape}.kicad_sch'), f'edge-board-{shape}',
                         pparts, [(25.4, snap(ybot2), PASSIVE_NOTES)])
    print('wrote', out1, 'height used', ybot)
    print('wrote', out2, 'height used', ybot2)


if __name__ == '__main__':
    main()
