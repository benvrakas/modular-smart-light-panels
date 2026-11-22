"""Edge ID code table (SPEC 4.2, decision 0020): worst-case windows and an exhaustive search for the R_k set.

usage: python edge_codes.py            -> table for the chosen set (R11 = 1 k)
       python edge_codes.py --search   -> best 8-code set from JLC basic E24 0603 values, for R11 = 470 / 680 / 1000

Model: SENSE pulled up to 3.3 V by R_pu = 10 k; the driving neighbour pulls its DRIVE low through Q3 (~20 R) and R11;
the reading panel's edge has D1 (1N4148WS) in series with R_k. V_ADC = Vf + I * (R_k + R11 + R_Q3).
Worst case: Vf +-80 mV (part +-30, 0-50 C +-50), R_k / R_pu / R11 +-1 %, ADC +-15 mV, idle >= 3.27 V (leakage).
"""
import itertools
import math
import sys
from collections import defaultdict

VDD, RPU, RQ = 3.3, 10e3, 20.0
NVT, IS = 0.049, 3.2e-9            # 1N4148: ~0.62 V at 1 mA, n ~ 1.9
IDLE_LO = VDD - 0.03
CHOSEN = [0, 2e3, 4.7e3, 9.1e3, 15e3, 27e3, 47e3, 100e3]
R11 = 1000.0
# JLC basic 0603 1 % (UNI-ROYAL 0603WAF), checked 2026-11-22 via the JLCPCB parts API
BASIC = [1e3, 1.2e3, 1.5e3, 1.8e3, 2e3, 2.2e3, 2.4e3, 2.7e3, 3e3, 3.3e3, 3.6e3, 3.9e3, 4.7e3, 5.1e3, 5.6e3, 6.2e3,
         6.8e3, 7.5e3, 8.2e3, 9.1e3, 10e3, 12e3, 13e3, 15e3, 18e3, 20e3, 22e3, 24e3, 27e3, 30e3, 33e3, 39e3, 47e3,
         51e3, 56e3, 68e3, 75e3, 82e3, 100e3, 120e3, 150e3, 200e3, 220e3]


def solve(rk, r11, rpu=RPU, dvf=0.0):
    r = rk + r11 + RQ
    vf = 0.55
    for _ in range(60):
        i = (VDD - vf) / (rpu + r)
        vf = NVT * math.log(i / IS) + dvf
    return vf + i * r, vf, i


def window(rk, r11, tol=0.01, dvf=0.08, adc=0.015):
    vs = [solve(rk * (1 + a * tol), r11 * (1 + c * tol), RPU * (1 + b * tol), d * dvf)[0]
          for a, b, c, d in itertools.product((-1, 1), repeat=4)]
    return min(vs) - adc, max(vs) + adc


def best(r11, values, ncodes=8):
    w = {r: window(r, r11) for r in [0] + values}
    order = [0] + sorted(values)
    table = defaultdict(dict)
    table[0][1] = (9.0, [0])
    for i, r in enumerate(order):
        for n, (mc, lst) in list(table[r].items()):
            if n == ncodes:
                continue
            for r2 in order[i + 1:]:
                m = min(mc, w[r2][0] - w[r][1])
                cur = table[r2].get(n + 1)
                if m > 0.02 and (cur is None or m > cur[0]):
                    table[r2][n + 1] = (m, lst + [r2])
    res = [(min(d[ncodes][0], IDLE_LO - w[r][1]), d[ncodes][1]) for r, d in table.items() if ncodes in d]
    return max(res)


def report(rs, r11):
    prev = None
    print(f'R11 = {r11:g} R')
    for k, r in enumerate(rs):
        v, vf, i = solve(r, r11)
        lo, hi = window(r, r11)
        gap = f'  gap {1000 * (lo - prev[1]):.0f} mV, threshold {(lo + prev[1]) / 2:.2f} V' if prev else ''
        print(f'  code {k}: {r / 1e3:6g} k  V {v:.3f}  window {lo:.3f}-{hi:.3f}  Vf {vf:.2f}  I {i * 1e6:.0f} uA{gap}')
        prev = (lo, hi)
    print(f'  idle >= {IDLE_LO:.2f} V  gap {1000 * (IDLE_LO - prev[1]):.0f} mV, threshold {(IDLE_LO + prev[1]) / 2:.2f} V')


if __name__ == '__main__':
    if '--search' in sys.argv:
        for r11 in (470.0, 680.0, 1000.0):
            m, l = best(r11, BASIC)
            print(f'R11 = {r11:g}: smallest gap {1000 * m:.0f} mV ->', ', '.join(f'{r / 1e3:g}k' for r in l))
    else:
        report(CHOSEN, R11)
        report([0, 1e3, 2.7e3, 5.6e3, 12e3, 27e3], 470.0)   # the V6.2-V6.9 six-code set, for comparison
