# SolidCraft feedback (for GitHub issues)

Things that got in the way while building this project's parts headless with `solidcraft-cli` (version 0.45.0, file format solidcraft/63). Each entry has what happened, a minimal repro or where it showed up, and what would help. Append as new ones come up; mark an entry with the issue link once it is filed.

Entries 1–10 were re-tested on 0.46.2 and filed on 2026-11-22 in [tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft/issues). The status line under each entry gives the result.

## Configurations and assemblies

1. **No configuration column for a child component's configuration.** `config.column` / `config.configure` take only `param`, `feature` (suppress), `material` and `appearance` targets. An assembly can't have rows that switch which configuration of an inserted design it uses (e.g. a panel assembly whose Hexagon/Square/Triangle rows pick the matching configuration of `back_plate.sc`). Workaround: insert every variant and suppress the unused inserts per row. *Wanted:* a `component_configuration:<component>` column.
   *Status:* still open in 0.46.2 (`component.insert_design` now takes a `configuration`, but `config.column` has no target for it). Added as a [comment on #11653](https://github.com/tangency-labs/solidcraft/issues/11653#issuecomment-7084133140).
2. **Nested inserts lose the child's component tree.** `component.insert_design` of a design that itself contains components brings it in as one component with the child's parts as bodies. Sub-components, their names and their own occurrences don't carry through. *Wanted:* keep the hierarchy (sub-assemblies).
   *Status:* still open in 0.46.2. Added as a [comment on #5526](https://github.com/tangency-labs/solidcraft/issues/5526#issuecomment-7084133356) (linked sub-assemblies proposal).
3. **A configuration-dependent point pick doesn't follow the configuration.** A profile point picked on a face in one configuration failed to resolve once another row was active (the face moved with `n_sides`). Workaround: drive every profile point from parameter expressions.
   *Status:* not filed; I haven't built a minimal repro yet.

## Modelling

4. **`sketch.polygon.circumscribed` needs numeric `sides` and `radius`.** A regular polygon can't follow a parameter (`n_sides`, an inradius expression). Workaround: one sector per side and a circular pattern with `count: "n_sides"`. *Wanted:* expressions for both fields.
   *Status:* in 0.46.2 `sides` accepts an expression but reads it only once (no update when the parameter changes), and `radius` still refuses one. Filed as [#20920](https://github.com/tangency-labs/solidcraft/issues/20920).
5. **A pattern of a new-body feature makes one body per copy.** `solid.pattern.circular` of a feature with `operation: new` gives n separate bodies, even where the copies touch. Workaround: make the first feature a `join` (with `body_name`) so each copy merges with the one it touches. *Wanted:* a "merge copies into the source body" option, or merge touching copies by default.
   *Status:* filed as [#20921](https://github.com/tangency-labs/solidcraft/issues/20921).
6. **The automatic name of a new body depends on history.** After `timeline.delete` of everything, the first new body was `Body1` in one file and `Body2` in another (the file's `reserved_body_names` keeps old names), so a scripted `body.rename body: "Body1"` failed. Workaround: pass `body_name` on the creating feature. *Wanted:* a rename by "the body feature X created", or reset reserved names when no feature uses them.
   *Status:* filed as [#20922](https://github.com/tangency-labs/solidcraft/issues/20922).

## CLI

7. **No command reference in the CLI.** The command list and parameter schemas (`list_commands`, `describe_command`) are only available through the MCP server, and no docs are installed with the app. Errors don't name the allowed values: `config.column` with a wrong key says "give exactly one configuration target" without listing `param` / `feature` / `material` / `appearance`. *Wanted:* `solidcraft-cli commands [filter]` and `solidcraft-cli describe <command>`, and errors that list the valid keys.
   *Status:* 0.46.2 has `solidcraft-cli commands`, but it prints the whole catalogue and ignores a filter, and there is no `describe`. Filed as [#20923](https://github.com/tangency-labs/solidcraft/issues/20923); the error message as [#20924](https://github.com/tangency-labs/solidcraft/issues/20924).
8. **MCP aliases are rejected by the CLI.** `set_parameter` and `measure` (MCP tool names) fail in `run` scripts; the engine names are `parameters.change` / `parameters.add` and `inspect.measure`. *Wanted:* accept the aliases, or say "did you mean `parameters.change`?".
   *Status:* in 0.46.2, `measure` now suggests `inspect.measure` (#10678), but `set_parameter` gets no suggestion. Filed as [#20925](https://github.com/tangency-labs/solidcraft/issues/20925).
9. **Option sets differ between subcommands.** `eval` rejects `--quiet` ("eval doesn't take --quiet"), which `run` takes. *Wanted:* accept the common flags everywhere, even when they are no-ops.
   *Status:* filed as [#20926](https://github.com/tangency-labs/solidcraft/issues/20926).

## Inspection

10. **Interference reports are flooded by overlaps inside one imported component.** On the panel assembly, 405 interferences were reported; about 380 were pads overlapping pads (or pins in one package) inside the same KiCad STEP model. *Wanted:* an option to skip pairs within one component or occurrence, and to group results by component pair.
    *Status:* not filed; 0.46.2 handles it. `inspect.interference {"exclude_pairs": [["<occurrence>", "<occurrence>"]]}` skips every pair inside that occurrence (pass one pair per STEP model).
