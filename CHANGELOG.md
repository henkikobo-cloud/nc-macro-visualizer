# Changelog

## v0.3.0 - Unreleased

### Added

- CFG model and `cfg.json` output with `--cfg`.
- StructuredTree model generated from CFG for beginner-facing PAD-inspired views.
- PAD-inspired HTML output with `--pad-html` and PAD-inspired text output with `--pad-text`.
- `--all-views` to generate existing outputs plus beginner flow, structured views, PAD-inspired views, and CFG.
- JSON schemas for CFG and StructuredTree.
- Web demo tabs for beginner display, text view, and expert detail view using `sessionStorage`.

### Notes

- Existing v0.2.0 outputs remain unchanged by default.
- Mermaid remains available as an expert/detail representation.
- Unstructured jumps are shown as supplemental PAD nodes, not warnings.

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
