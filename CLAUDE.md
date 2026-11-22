# Instructions for Claude sessions in this project

## Sources of truth: read the live files
- **SPEC.md** is the master spec; its header gives the current version. **docs/decisions/NNNN-*.md** records why each decision was made.
- At the start of any design, hardware, or firmware task, read `SPEC.md` and the relevant `docs/decisions/` files **from the project folder with the Read tool**. Don't rely on memory, earlier summaries, or output captured earlier in a session.
- **Never treat files under `~/.claude/projects/**/tool-results/` as project documents.** They are frozen snapshots of old command output and go stale as soon as the real file changes. If a tool result points you to one, open the real file in the project folder instead.
- Read documents one at a time with the Read tool. Don't `cat` several large files in one shell command: the combined output gets saved as a tool-results snapshot, which then gets read later in place of the live file.
- Several Claude sessions work in this folder at once. Re-read a file right before editing it, because another session may have changed it.

## Keep the spec in sync with decisions
- When a decision changes anything in the spec, do all of these in the same session:
  1. Write or update a decision record in `docs/decisions/`.
  2. Update `SPEC.md`: bump the version and add a changelog entry.
  3. Update the status table at the top of `docs/gap-analysis.md` if an item there is affected.
- Never leave `SPEC.md` contradicting a decision record. If you can't update the spec, tell the user it is out of date.
- **One source of truth (user, 2026-11-21):** `SPEC.md` and `docs/decisions/` are the only written description of the design. The README and `docs/figures/` only link or show generated pictures (re-run `docs/figures/make_figures.py`); don't restate design numbers anywhere else. The old HTML explainer is retired in `docs/archive/explainer/`.
- Before relying on the spec, check `docs/decisions/` for records dated later than the spec version. If one exists, the spec is stale: say so.

## Project conventions
- Hardware is KiCad 9. The edge boards are `hardware/edge-board/` (projects `edge-board-hex`, `edge-board-square`, `edge-board-triangle`: one circuit, one outline each); the controller is `hardware/controller-board/` and the seam bridge `hardware/bridge/`. Superseded designs are in `hardware/archive/` and `mechanical/archive/`; the project library "ModularLight" is in `hardware/lib/`. The `.kicad_sch` file is the source of truth for the schematic.
- Parts must be machine-placeable (tape and reel, JLCPCB assembly). Avoid anything that has to be hand-placed. Snap fits carry the mechanical loads.
- **CAD symmetry (user, 2026-11-22):** model a repeated feature once and derive its copies with a mirror, a rotational pattern (e.g. 180° about the part axis) or a linear/circular pattern; never hand-copy a sketch or feature into an `…L`/`…R`, `A`/`B` or `+`/`-` twin. Only genuinely different instances get their own features. Check a restructure by volume and bounding box: both must stay the same.
- Keep everything in this project folder (Google Drive has room): datasheets in `docs/datasheets/`, KiCad reports and scratch exports in `hardware/<board>/output/`, and build output next to its source. **Ask the user before adding anything about 10 GB or more.**
