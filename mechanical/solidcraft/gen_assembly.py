"""Build script for mechanical/solidcraft/panel_assembly.sc: a mixed cluster (2 hexagons, 1 square, 2 triangles)."""
import json, math, sys

ROOT = "C:/Users/benvr/My Drive/Projects/Modular Smart Light Panels/mechanical/solidcraft/"
# boards/ = copper-free models (clean viewport); "--copper" builds from boards/with-copper/ instead
BOARDS = "boards/" if "--no-copper" in sys.argv else "boards/with-copper/"   # full copper models by default (user 2026-11-21)
EDGE_L, SEAM_D, BOARD_T, CTRL_GAP = 100.0, 3.5, 1.6, 0.2
SHAPE = {3: "Triangle", 4: "Square", 6: "Hexagon"}
STEP = {3: "edge-board-triangle", 4: "edge-board-square", 6: "edge-board-hex"}


def As(n):
    return EDGE_L / (2 * math.tan(math.pi / n))


def Lb(n):
    return EDGE_L - 2 * (SEAM_D + BOARD_T) * math.tan(math.pi / n)


def rz(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def tr(x, y, z=0):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def m34(m3x4):
    return [list(r) for r in m3x4] + [[0, 0, 0, 1]]


def flat(m):
    out = []
    for r in m[:3]:
        out += [round(v, 10) if abs(v) > 1e-12 else 0.0 for v in r]
    return out


# panels: name, sides, centre, rotation (deg)
a_hex, a_sq, a_tri = As(6), As(4), As(3)
P = {
    "A":  (6, (0.0, 0.0), 0.0),
    "B":  (6, (0.0, -2 * a_hex), 180.0),
    "S":  (4, ((a_hex + a_sq) * math.cos(math.radians(-30)), (a_hex + a_sq) * math.sin(math.radians(-30))), 60.0),
    "T1": (3, ((a_hex + a_tri) * math.cos(math.radians(30)), (a_hex + a_tri) * math.sin(math.radians(30))), 180.0),
}
t1 = P["T1"][1]
P["T2"] = (3, (t1[0], t1[1] + 2 * a_tri), 0.0)
SEAMS = [("A", 0, "B", 0), ("A", 1, "S", 2), ("A", 2, "T1", 1), ("T1", 0, "T2", 0)]
BEZEL = {"A", "B", "S", "T1", "T2"}


def side_frame(p, k):
    n, (cx, cy), phi = P[p]
    return mul(tr(cx, cy), rz(phi + k * 360.0 / n))


S = []
c = lambda cmd, **kw: S.append({"command": cmd, "params": kw})
placed = {}          # component key -> number of placements so far


def place_step(key, path, name, M):
    """First use inserts the STEP; later uses place another occurrence of the same component."""
    if key not in placed:
        c("file.insert_step", path=path, name=name, matrix=flat(M), flatten=True)
        placed[key] = 1
    else:
        placed[key] += 1
        c("occurrence.copy", occurrence=f"{name}:1")
        c("occurrence.move", occurrence=f"{name}:{placed[key]}", to_matrix=flat(M))


def place_design(file, config, M, name):
    c("component.insert_design", path=ROOT + file, configuration=config, matrix=flat(M), reuse=True, name=name)


for p, (n, (cx, cy), phi) in P.items():
    A_s = As(n)
    Ae, Ai = A_s - SEAM_D, A_s - SEAM_D - BOARD_T
    pf = mul(tr(cx, cy), rz(phi))
    place_design("back_plate.sc", SHAPE[n], pf, f"Back plate {SHAPE[n]}")
    place_design("frame.sc", SHAPE[n], pf, f"Frame {SHAPE[n]}")
    if p in BEZEL:
        place_design("diffuser.sc", SHAPE[n], pf, f"Bezel {SHAPE[n]}")
    for k in range(n):
        M = mul(side_frame(p, k), m34([[-1, 0, 0, Lb(n) / 2], [0, 0, 1, -Ae], [0, 1, 0, 0]]))
        place_step(f"edge{n}", ROOT + f"{BOARDS}{STEP[n]}.step", f"Edge board {SHAPE[n].lower()}", M)
    M = mul(pf, m34([[-1, 0, 0, 100], [0, 1, 0, 100 - Ai + CTRL_GAP], [0, 0, -1, 6.6]]))
    place_step("ctrl", ROOT + f"{BOARDS}controller-board.step", "Controller", M)

for (p, k, q, j) in SEAMS:
    n = P[p][0]
    F = side_frame(p, k)
    place_design("bridge_clip.sc", None, mul(F, tr(0, -As(n))), "Bridge clip")
    place_step("bridge", ROOT + f"{BOARDS}bridge.step", "Bridge",
               mul(F, m34([[-1, 0, 0, 28], [0, 0, 1, -As(n) - 0.355], [0, 1, 0, -2.0]])))

# white printed parts
c("appearance.assign", components=["Back plate Hexagon", "Back plate Square", "Back plate Triangle", "Frame Hexagon",
  "Frame Square", "Frame Triangle", "Bezel Hexagon", "Bezel Square", "Bezel Triangle", "Bridge clip"], color="#F2F2EF", name="White PETG")
c("inspect.measure", summary=True)
json.dump({"commands": S}, open(sys.argv[1], "w"), indent=1)
print(len(S), "steps;", {k: v for k, v in placed.items()})
for p, v in P.items():
    print(p, SHAPE[v[0]], [round(x, 3) for x in v[1]], v[2])
