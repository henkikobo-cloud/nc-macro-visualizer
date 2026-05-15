# Release Notes: v0.1.0

NC Macro Visualizer v0.1.0 is the first MVP release.

This release focuses on helping people read and review FANUC-style NC macro assets. It is a reading aid, not an NC emulator or machine behavior validator.

## Highlights

- Generates three output artifacts:
  - `report.md` for human review
  - `analysis.json` for structured inspection and tool integration
  - `flow.mmd` for Mermaid-based flow visualization
- Extracts `N` labels, macro variables, assignments, references, and occurrence counts.
- Extracts line-local variable dependencies such as `#500 <- #100, #101`.
- Detects common flow constructs:
  - `IF ... GOTO`
  - `GOTO`
  - `IF ... THEN`
  - basic `WHILE ... DO` / `END`
- Detects `M98` and `G65` calls.
- Reports warnings for unresolved `GOTO` targets, duplicate labels, and unsupported input extensions.
- Treats unknown M codes conservatively as `unknown` / `machine_specific`.

## Safety And Scope

This tool does not guarantee real machine behavior.

It does not execute NC programs, simulate machining, infer toolpaths, estimate cycle time, check collisions, or interpret machine-specific M-code meanings.

M codes are machine-dependent. Unknown M codes are intentionally left as unknown.

## Included Documentation

- `README.md`: project overview, usage, and output examples
- `docs/design.md`: design philosophy and v0.1.0 boundary
- `limitations.md`: known limitations and non-goals
- `CHANGELOG.md`: release history
- `LICENSE`: MIT License

## Verification

The v0.1.0 codebase includes parser, analyzer, renderer, and CLI smoke tests.

Expected checks:

```bash
python3 -m unittest discover -s tests
.venv/bin/python -m pytest
```

At release preparation time, both suites passed with 13 tests.
