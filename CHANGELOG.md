# Changelog

## v0.1.0 - 2026-05-15

MVP stage 1 release.

### Added

- CLI entry point: `nctool.py`
- Markdown report output: `report.md`
- JSON output: `analysis.json`
- Mermaid flowchart output: `flow.mmd`
- `N` label extraction
- Numeric and named macro variable extraction
- Variable assignment/reference classification
- Variable occurrence summary
- Line-local variable dependency extraction
- `IF ... GOTO`, `GOTO`, `IF ... THEN`, and basic `WHILE ... DO` / `END` detection
- `M98` and `G65` call detection
- Common M-code profile with conservative fallback to `unknown` / `machine_specific`
- Warnings for unresolved `GOTO`, duplicate labels, and unsupported input extensions
- Sample NC files under `samples/`
- Unit and pytest test coverage split by parser, analyzer, renderer, and CLI smoke tests
- Public documentation:
  - `README.md`
  - `docs/design.md`
  - `limitations.md`

### Notes

- This release is a reading aid, not an NC emulator.
- It does not guarantee real machine behavior.
- It does not infer machine-specific M-code meanings.

