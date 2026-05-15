# TODO

## Current Status

- Project structure follows the intended MVP split:
  - `src/nc_macro_visualizer/parser`
  - `src/nc_macro_visualizer/analyzer`
  - `src/nc_macro_visualizer/renderer`
  - `src/nc_macro_visualizer/models`
  - `src/nc_macro_visualizer/profiles`
  - `src/nc_macro_visualizer/cli`
- CLI starts successfully:
  - `python3 nctool.py --help`
  - `python3 nctool.py samples/01_simple_if.nc -o output`
- Sample files exist:
  - `samples/01_simple_if.nc`
  - `samples/02_goto_loop.nc`
  - `samples/03_subprogram_call.nc`
  - `samples/04_variables.nc`
  - `samples/05_machine_mcode.nc`
- Output generation works:
  - `output/report.md`
  - `output/analysis.json`
  - `output/flow.mmd`
- Current test fallback works:
  - `python3 -m unittest discover -s tests`
  - Result: `OK`, 13 tests.
- `pytest` is configured in `pyproject.toml` and installed in the local `.venv`.
  - `.venv/bin/python -m pytest`
  - Result: `13 passed`.

## Confirmed Implemented

- Variable extraction:
  - Numeric variables such as `#100`, `#500`.
  - Named variables such as `#<RESULT>`.
  - Assignment/reference classification.
  - Per-variable counts in `analysis.json` and `report.md`.
- IF/GOTO extraction:
  - `IF [condition] GOTO N`.
  - Plain `GOTO N`.
  - Basic `IF ... THEN`.
  - Basic `WHILE ... DO`.
- M-code extraction:
  - Standard M codes get shared descriptions.
  - Unknown M codes are reported as `unknown` / `machine_specific`.
  - Example confirmed: `M50`.
- Call extraction:
  - `M98 P...`.
  - `G65 P...`.
- Mermaid output:
  - Sequential flow.
  - Basic conditional YES/NO edges for `IF_GOTO`.
  - Basic jump edge for `GOTO`.
  - Dotted call edges for `M98` and `G65`.
  - Basic `WHILE ... DOn` / `ENDn` loop-back and loop-exit edges.
- Validation warnings:
  - unresolved `GOTO` target.
  - duplicate `N` label.
  - unsupported input extension.
- Variable dependency extraction:
  - line-local dependencies such as `#500 <- #100, #101`.
- Tests are split by responsibility:
  - parser tests
  - analyzer tests
  - renderer tests
  - CLI smoke tests

## Known Gaps / Bugs

- Parser is regex-based and does not build a real AST yet.
- `M98` and `G65` call parsing currently expects a `P` target.
- `analysis.json` includes `%` and `O` program header/footer lines in `parsed_lines`.
  - These are excluded from flow generation, but still visible in parsed line output.
- Validation is intentionally conservative:
  - unresolved `GOTO` / duplicate label / unsupported extension are warnings, not hard failures.
  - `WHILE ... DO` / `END` matching is based on numeric DO/END ids only.
- Variable dependency extraction is line-local assignment dependency extraction, not a full expression AST.

## Next Implementation Priority

1. Expand call handling:
   - support `M98` repeat counts and alternate controller formats where needed.
   - distinguish in-file calls from external program calls.
2. Improve expression parsing:
   - replace line-local dependency regexes with expression-aware parsing.
3. Add stricter validation modes:
   - optional non-zero CLI exit on warnings.
   - configurable supported input extensions.
4. Consider replacing regex-only parsing with `pyparsing` or `lark` once MVP behavior is stable.

## Not In Scope

- Real machine behavior guarantee.
- NC execution or emulation.
- Toolpath simulation.
- Collision detection.
- Machine-specific M-code meaning inference.
- Web UI before CLI and output quality are stable.
