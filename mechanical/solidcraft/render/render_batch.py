"""Run the penthouse renders one after another (CPU priority: PRIORITY env) (python render_batch.py [job ...]).

Each job is (output name, mode, frames/samples, environment). Outputs land in out/; logs in out/logs/.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
SCENE = os.path.join(HERE, "assets", "penthouse", "modern_loft_apartment.blend")
# CPU priority of the Blender runs: PRIORITY=high (default since 2026-11-21, user) | normal | below (when the user is
# watching video on another monitor). Rendering itself runs on the GPU.
PRIORITY = {"high": 0x00000080, "normal": 0x00000020, "below": 0x00004000}[os.environ.get("PRIORITY", "high")]
W, H = 2560, 1440                      # 1440p for every render (user, 2026-11-21)

JOBS = {
    # name: (output, mode, samples or frames, environment[, (width, height)])
    "still":            ("penthouse_still.png", "still", 256, {"SHOT": "wide"}),
    "closeup":          ("penthouse_closeup.png", "still", 256, {"SHOT": "close"}),
    "max_day":          ("penthouse_max_day.png", "still", 256, {"SHOT": "wide", "MAXWHITE": "1", "LIGHT": "day"}),
    "max_day_close":    ("penthouse_max_day_closeup.png", "still", 256, {"SHOT": "close", "MAXWHITE": "1", "LIGHT": "day"}),
    "max_night":        ("penthouse_max_night.png", "still", 256, {"SHOT": "wide", "MAXWHITE": "1", "LIGHT": "night"}),
    "max_night_close":  ("penthouse_max_night_closeup.png", "still", 256, {"SHOT": "close", "MAXWHITE": "1", "LIGHT": "night"}),
    "video":            ("penthouse_panels.mp4", "video", 240, {"SHOT": "wide"}),
    "video_close":      ("penthouse_closeup.mp4", "video", 240, {"SHOT": "close"}),
}
for fx in ("aurora", "sunset", "ocean", "confetti", "warm", "fire"):          # effect variations (stills)
    JOBS["fx_" + fx] = (f"penthouse_fx_{fx}.png", "still", 256, {"SHOT": "wide", "EFFECT": fx})
for shot in ("vcorner", "vwall", "vinside"):                                   # 9:16 vertical stills
    JOBS["v_" + shot[1:]] = (f"penthouse_vertical_{shot[1:]}.png", "still", 256, {"SHOT": shot}, (1440, 2560))
DEFAULT = (["still", "closeup", "max_day", "max_day_close", "max_night", "max_night_close"]
           + ["fx_" + f for f in ("aurora", "sunset", "ocean", "confetti", "warm", "fire")]
           + ["v_corner", "v_wall", "v_inside", "video", "video_close"])


def run(name):
    out, mode, num, env_add = JOBS[name][:4]
    w, h = JOBS[name][4] if len(JOBS[name]) > 4 else (W, H)
    os.makedirs(os.path.join(HERE, "out", "logs"), exist_ok=True)
    target = os.path.join(HERE, "out", out)
    tmp = target + (".part.mp4" if mode == "video" else ".part.png")     # renamed only when complete
    env = dict(os.environ, **env_add)
    args = [BLENDER, "-b", SCENE, "--disable-autoexec", "-P", os.path.join(HERE, "penthouse_scene.py"), "--",
            mode, tmp, str(w), str(h), str(num)]
    t0 = time.time()
    with open(os.path.join(HERE, "out", "logs", name + ".log"), "w", encoding="utf-8", errors="replace") as log:
        r = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, env=env, creationflags=PRIORITY)
    produced = [f for f in os.listdir(os.path.join(HERE, "out")) if f.startswith(os.path.basename(tmp).rsplit(".", 1)[0])]
    if r.returncode == 0 and produced:
        os.replace(os.path.join(HERE, "out", produced[0]), target)
        print(f"{name}: {out} in {(time.time() - t0) / 60:.1f} min", flush=True)
    else:
        print(f"{name}: FAILED (exit {r.returncode}), see out/logs/{name}.log", flush=True)


if __name__ == "__main__":
    for n in sys.argv[1:] or DEFAULT:
        run(n)
