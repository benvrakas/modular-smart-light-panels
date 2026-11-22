"""SolidCraft batch that builds one complete panel of a shape and exports it as a GLB for Blender.

python gen_panel_glb.py hex|square|triangle OUT.json
Panel frame: centred on the origin, side 0 (controller) at -Y, Z out of the wall (z 0 = board wall edge).
Boards come from boards/with-copper/ so the pads are real geometry in renders.
"""
import json, math, sys

ROOT = "C:/Users/benvr/My Drive/Projects/Modular Smart Light Panels/mechanical/solidcraft/"
shape = sys.argv[1]
n = {"hex": 6, "square": 4, "triangle": 3}[shape]
CFG = {6: "Hexagon", 4: "Square", 3: "Triangle"}[n]
EDGE_L, SEAM_D, BOARD_T = 100.0, 3.5, 1.6
As = EDGE_L / (2 * math.tan(math.pi / n)); Ae = As - SEAM_D; Ai = Ae - BOARD_T
Lb = EDGE_L - 2 * (SEAM_D + BOARD_T) * math.tan(math.pi / n)


def rz(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def flat(m):
    return [round(v, 10) for r in m[:3] for v in r]


S = []
c = lambda cmd, **kw: S.append({"command": cmd, "params": kw})
I = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
for f, nm in (("back_plate.sc", "Back plate"), ("frame.sc", "Frame"), ("diffuser.sc", "Bezel")):
    c("component.insert_design", path=ROOT + f, configuration=CFG, matrix=flat(I), name=nm)
step = ROOT + f"boards/with-copper/edge-board-{ {'hex': 'hex', 'square': 'square', 'triangle': 'triangle'}[shape] }.step"
edge0 = [[-1, 0, 0, Lb / 2], [0, 0, 1, -Ae], [0, 1, 0, 0], [0, 0, 0, 1]]
for k in range(n):
    M = mul(rz(k * 360.0 / n), edge0)
    if k == 0:
        c("file.insert_step", path=step, name="Edge board", matrix=flat(M), flatten=True)
    else:
        c("occurrence.copy", occurrence="Edge board:1")
        c("occurrence.move", occurrence=f"Edge board:{k + 1}", to_matrix=flat(M))
c("file.insert_step", path=ROOT + "boards/with-copper/controller-board.step", name="Controller", flatten=True,
  matrix=flat([[-1, 0, 0, 100], [0, 1, 0, 100 - Ai + 0.2], [0, 0, -1, 6.6], [0, 0, 0, 1]]))
c("appearance.assign", components=["Back plate", "Frame", "Bezel"], color="#F2F2EF", name="White PETG")
c("appearance.assign", bodies=["Film"], color="#EEF1F5", name="Diffuser film")
c("appearance.assign", faces=[{"point": [0, -(Ai - 0.2) + 12, 6.6], "body": "controller-board_PCB"}], color="#F4F4F1", name="White mask")
c("export", path=ROOT + f"render/panel_{shape}.glb", format="glb")
json.dump({"commands": S}, open(sys.argv[2], "w"), indent=1)
print(len(S), "steps")
