# Render assets and how the renders are made

## Scene

`penthouse_scene.py` dresses `assets/penthouse/modern_loft_apartment.blend`: "Modern Loft Apartment" by Matteo Pascale, BlenderKit, free plan, royalty-free licence. It was downloaded on 2026-11-21 through BlenderKit's public download API for free assets. The .blend (334 MB) isn't in git; re-download it into `assets/penthouse/` if it's missing (BlenderKit search "Modern Loft Apartment", asset base id `05057669-22df-4e62-a03a-b665524c7135`).

Panels: `panel_hex.glb` and `panel_triangle.glb`, exported from SolidCraft by `gen_panel_glb.py` (boards with copper, white parts, opaque film).

## Running

```
python render_batch.py                 # every render below, one after another, at below-normal priority
python render_batch.py max_night video # just these jobs
```

| Job | Output (`out/`) | What |
|---|---|---|
| `still` / `closeup` | `penthouse_still.png`, `penthouse_closeup.png` | Evening, colour-wave effect |
| `max_day`, `max_day_close` | `penthouse_max_day*.png` | Panels at maximum estimated brightness (full white), daylight |
| `max_night`, `max_night_close` | `penthouse_max_night*.png` | Maximum brightness, room lamps off: the panels light the room |
| `fx_aurora`, `fx_sunset`, `fx_ocean`, `fx_confetti`, `fx_warm`, `fx_fire` | `penthouse_fx_*.png` | The wide shot with other effects (`EFFECT=`) |
| `v_corner`, `v_wall`, `v_inside` | `penthouse_vertical_*.png` | 9:16 portrait shots (1440 × 2560): the outside corner, the painting wall, the inside corner |
| `video` / `video_close` | `penthouse_panels.mp4`, `penthouse_closeup.mp4` | 8 s colour-wave videos |

Everything renders at 1440p (2560 × 1440). The .blend is third-party, so Blender opens it with `--disable-autoexec` (no embedded scripts run).

Environment knobs for `penthouse_scene.py`: `SHOT` (wide | close | vcorner | vwall | vinside), `EFFECT` (wave | aurora | sunset | ocean | confetti | warm | fire), `CLEAR` (gap kept round paintings, the TV and furniture, 0.06 m), `LIGHT` (day | evening | night), `MAXWHITE=1`, `GLOW`, `DIM`, `WORLD`, `VIEW` ("transform|look|exposure"), `SPP` (video samples, 160), `DENOISER`, `CLAMP`, `ADAPT`, `RANGE` (frame slice, e.g. 120-131), `STATIC=1`, `T` (still time), `BLOOM_T`, `BLOOM_MIX`, `WAVE_K`, `FSTOP`.

## Maximum brightness

Every panel's maximum is normalised to the shape with the fewest LEDs per area: the hexagon (18 LEDs on 0.0255 m² of film). The datasheet gives about 10.7 lm per SKC6812RGBW at full RGBW; with about 65 % getting through the diffuser and chamber (an estimate), that is about 4,900 lm/m² leaving the film (≈1,570 cd/m²). The film emits that in every max-brightness render, on every shape.

## Layout

Four walls seen from the scene's Camera.008: the west (TV) wall, the white wall with the painting, the narrow wall by the stairs (one ribbon wraps from the TV wall round the inside corner, over the painting and round the outside corner), and the double-height kitchen wall. Panels grow on a triangular lattice of 100 mm edges, so each neighbour shares a full edge. Every candidate panel is ray-cast against its wall and kept only on bare wall, at least 6 cm from the painting, the TV, shelves and furniture; on the kitchen wall it must also be in clear view of the camera (the mezzanine floor's edge cuts across that wall).

## Video quality

160 samples per frame, OpenImageDenoise in its accurate mode, clamped indirect light and no caustics. At 48 samples with OptiX denoising, the reflections in the floor and window shimmered from frame to frame.
