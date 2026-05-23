# NC Macro Visualizer Project Policy, Specification, and Current Status

## Purpose of This Document

> Review note: this document records the v0.2.0 product policy and target
> structure as initially planned. After technical review, the implementation
> direction was narrowed. For v0.2.0 execution, see
> `docs/claude_code_v0.2_refactor_instructions.md` as the Single Source of Truth.
> Specifically:
>
> - `core/` is deferred and not introduced in v0.2.0.
> - `flowchart/` is added beside the existing `parser/`, `analyzer/`, `models/`, and `renderer/` packages.
> - `schemas/beginner_flow.schema.json` is defined before implementation.
> - Beginner output is opt-in via a CLI flag, not a default output.
> - `lp/demo/` and `web/` coexist throughout v0.2.0.
>
> Sections below describing a `core/` directory or treating beginner output as
> default should be read as historical context, not as v0.2.0 execution targets.
>
> Review note (v0.3.x): N 番号の位置づけを「traceability data（補足情報）」から
> 「識別子（タイトルの一部）」に変更した。現場での実用性を踏まえた判断であり、
> v0.2.0 当初の方針から意図的に修正したものである。
>
> Review note (v0.3.x): PAD 図風表示の start / end マーカーを視覚的に区別する
> 仕様を追加した。伝統的 PAD 図には start / end の専用記号は存在しないが、
> 本ツールは「PAD 図風」と位置づけており、現場での実用性を優先する判断
> として、▶（緑系）と ■（赤系）の角丸ボックスで明示する仕様とした。
> end ノード自体（N40 など）は通常の処理ボックスとして表示し、それとは
> 別にプログラム全体の終端マーカーを表示する。

This document summarizes the current project direction, product specification, architecture, implementation status, known limitations, and recommended next steps.

It is intended for external review by another coding agent or reviewer, including Claude Code.

## Project Summary

NC Macro Visualizer is a reading-support tool for FANUC-style NC macros.

The product direction is shifting from a CLI-centered NC analysis tool to a Web-first "NC macro understanding support app" for:

- NC beginners.
- People with limited macro reading experience.
- On-site workers who are not comfortable with command-line tools.
- Maintainers who need to understand legacy NC macro assets before asking an expert or checking machine documentation.

The main goal is:

> Translate NC macro code into a general, beginner-readable program flowchart.

The tool should explain the meaning of processing steps. In v0.3.x beginner-facing PAD-inspired views, `N` numbers are also shown as practical identifiers at the start of each title.

## Product Policy

### Primary Policy

- General users should enter through a Web screen, not the CLI.
- The main output should be a beginner-friendly flowchart.
- The flowchart should be a standard program flowchart, not an NC code connection diagram.
- The explanation should prioritize "what the process means".
- `N` numbers are included as identifiers in beginner-facing titles because they are the shared language used on site.
- `N` numbers must be paired with a meaning title, such as `N10: 値を計算する`; an `N` number alone is not enough.
- Lines without an `N` number use `line N` as the fallback identifier.
- CLI remains available for developers, automated tests, and internal verification.

### Safety and Scope Policy

The project must not claim to:

- Guarantee real machine behavior.
- Execute or emulate NC programs.
- Simulate machining.
- Generate or verify toolpaths.
- Estimate machining results, collision, interference, or cycle time.
- Reproduce PMC behavior.
- Infer machine-specific M code behavior.
- Validate that a program is safe to run on a real machine.

### M Code Policy

M codes are machine-dependent.

- Known common M codes may receive common explanations.
- Unknown M codes must not be guessed.
- Unknown or machine-specific M codes must be displayed as:
  - `意味の確認が必要なMコード`
- Supporting message:
  - `機械の説明書、PMC、ビルダー設定を確認してください。`
- The UI must never display unknown M codes as guaranteed behavior.

## Current Repository Status

Current package version:

- `pyproject.toml`: `0.1.0`

Current repository contains:

```text
src/nc_macro_visualizer/
├─ analyzer/
├─ cli/
├─ models/
├─ parser/
├─ profiles/
└─ renderer/

tests/
├─ test_analyzer.py
├─ test_cli.py
├─ test_parser.py
└─ test_renderer.py

samples/
├─ 01_simple_if.nc
├─ 02_goto_loop.nc
├─ 03_subprogram_call.nc
├─ 04_variables.nc
└─ 05_machine_mcode.nc

docs/
├─ design.md
├─ v0.2_design_plan.md
└─ project_policy_spec_status.md

lp/
├─ index.html
├─ style.css
├─ assets/
└─ demo/
```

Current CLI entry points:

- `nctool.py`
- `nc_macro_visualizer.cli.main:main`
- console script: `nctool`

Current primary CLI outputs:

```text
output/
├─ report.md
├─ analysis.json
└─ flow.mmd
```

Current user-facing Web demo exists under:

```text
lp/demo/
├─ index.html
├─ style.css
└─ app.js
```

The Web demo is currently a static browser demo and has its own simplified JavaScript analysis logic.

## Current Git Working Tree Notes

At the time this document was created, the working tree already contained unrelated uncommitted changes:

- `README.md` modified.
- `lp/` files untracked.

This document was added without reverting or modifying those existing changes.

## Current v0.1.0 Capabilities

The Python engine currently supports:

- Parsing line-based NC text.
- Removing simple comments.
- Extracting `N` labels.
- Extracting variables such as `#100` and `#<RESULT>`.
- Distinguishing variable assignments and references.
- Summarizing variable counts, assignments, and references.
- Extracting simple line-local variable dependencies.
- Detecting:
  - `IF ... GOTO`
  - `GOTO`
  - `IF ... THEN`
  - basic `WHILE ... DO`
  - basic `END`
- Detecting M codes.
- Detecting `M98 P...` subprogram calls.
- Detecting `G65 P...` macro calls.
- Warning on:
  - unsupported file extension
  - duplicate labels
  - unresolved `GOTO`
  - unmatched loop end
- Rendering:
  - Markdown report
  - JSON analysis
  - Mermaid flowchart

## Current Architecture

### `parser`

Location:

```text
src/nc_macro_visualizer/parser/nc_parser.py
```

Responsibilities:

- Strip simple comments.
- Parse lines into `ParsedLine`.
- Find variables, controls, M codes, calls, loop ends, and variable dependencies.

Implementation style:

- Regex-based MVP parser.
- No full AST.
- No machine execution semantics.

### `analyzer`

Location:

```text
src/nc_macro_visualizer/analyzer/analysis.py
```

Responsibilities:

- Convert parsed lines into an `AnalysisResult`.
- Summarize variables.
- Validate conservative warnings.
- Build basic flow edges for reading support.

### `models`

Location:

```text
src/nc_macro_visualizer/models/analysis.py
```

Current dataclasses include:

- `ParsedLine`
- `VariableHit`
- `VariableSummary`
- `ControlHit`
- `MCodeHit`
- `LabelHit`
- `CallHit`
- `LoopEndHit`
- `VariableDependency`
- `AnalysisWarning`
- `FlowEdge`
- `AnalysisResult`

### `renderer`

Location:

```text
src/nc_macro_visualizer/renderer/
```

Responsibilities:

- `markdown.py`: render `report.md`.
- `json_renderer.py`: render `analysis.json`.
- `mermaid.py`: render `flow.mmd`.

Current Mermaid output still uses NC source text and `N` labels prominently.

### `profiles`

Location:

```text
src/nc_macro_visualizer/profiles/fanuc.py
```

Responsibilities:

- Provide common M code descriptions.
- Return `unknown` / `machine_specific` for unknown M codes.

### `cli`

Location:

```text
src/nc_macro_visualizer/cli/main.py
```

Responsibilities:

- Accept an input file path.
- Write Markdown, JSON, and Mermaid outputs to an output directory.

## Current Problems

The current implementation works as a v0.1.0 CLI MVP, but it does not yet match the new product direction.

Main problems:

- CLI is still the primary stable interface.
- Mermaid output is source-code-centric.
- `N` labels and original NC lines are too prominent.
- There is no dedicated beginner-flow model.
- Web demo parsing logic is separate from the Python parser.
- Directory names do not yet match the desired v0.2.0 shape:
  - current: `parser`, `analyzer`, `renderer`, `models`
  - target: `core`, `flowchart`, `renderers`
- The existing flowchart shows code connections more than process meaning.
- The Web demo is under `lp/demo/`, while the desired general-user entry is `web/`.

## v0.2.0 Target Structure

Final target:

```text
src/nc_macro_visualizer/
├─ core/
│  ├─ __init__.py
│  ├─ analyzer.py
│  ├─ parser.py
│  └─ models.py
├─ flowchart/
│  ├─ __init__.py
│  ├─ builder.py
│  ├─ beginner_nodes.py
│  └─ terminology.py
├─ renderers/
│  ├─ __init__.py
│  ├─ json_renderer.py
│  ├─ markdown.py
│  └─ mermaid.py
├─ profiles/
│  ├─ __init__.py
│  └─ fanuc.py
└─ cli/
   ├─ __init__.py
   └─ main.py

web/
├─ index.html
├─ style.css
└─ app.js

lp/
├─ index.html
├─ style.css
└─ assets/
```

Migration-friendly intermediate target:

```text
src/nc_macro_visualizer/
├─ analyzer/      # keep during transition
├─ parser/        # keep during transition
├─ models/        # keep during transition
├─ renderer/      # keep during transition
├─ flowchart/     # add first
├─ renderers/     # add compatibility wrappers later
├─ profiles/
└─ cli/
```

## Python Engine and Web UI Separation

Python should be the source of truth for analysis behavior.

Python responsibilities:

- Parse NC text into structured facts.
- Extract labels, variables, controls, calls, M codes, warnings, and dependencies.
- Preserve uncertainty.
- Build beginner-facing flowchart nodes and edges.
- Export stable JSON for Web consumption.

Web responsibilities:

- Provide file selection, paste/edit, and a clear `解析する` action.
- Show beginner-friendly flowchart first.
- Show warnings in plain language.
- Show original source only as supporting detail.
- Avoid developer-oriented terminology in the first view.

Preferred data flow:

```text
NC text
  -> core analysis result
  -> beginner flowchart model
  -> JSON / Mermaid / Markdown renderers
  -> Web UI rendering
```

During v0.2.0, the static JavaScript demo can remain, but its schema and wording should move closer to Python output.

## Beginner Flowchart Specification

The beginner flowchart should be a standard program flowchart.

Node priority:

1. Meaning of the processing step.
2. Plain-language action or condition.
3. Original NC code as optional detail.
4. `N` label and source line number as traceability data.

Required node types:

| Type | Shape | Use |
| --- | --- | --- |
| `start` | rounded terminator | Start of reading flow |
| `end` | rounded terminator | Program end or return |
| `process` | rectangle | Calculation, assignment, ordinary command |
| `decision` | diamond | `IF`, `IF ... GOTO`, `IF ... THEN`, `WHILE` |
| `call` | predefined process | `M98`, `G65`, subprogram or macro call |
| `machine_action` | rectangle with caution style | Known common M code |
| `needs_confirmation` | rectangle with warning style | Unknown or machine-specific M code |
| `warning` | annotation | unresolved target, duplicate label, unsupported input |

Required edge labels:

| Case | Label |
| --- | --- |
| Sequential flow | `次へ` |
| True branch | `はい` |
| False branch | `いいえ` |
| Jump | `指定場所へ` |
| Loop body | `くり返す` |
| Loop exit | `終了` |
| Call | `呼び出し` |

Example conversions:

| NC code | Beginner label |
| --- | --- |
| `#500 = #100 + #101` | `値を計算する` |
| `IF [#100 GT 10] GOTO 80` | `条件で分かれる` |
| `IF [#100 EQ 1] THEN #101 = 5` | `条件が合うと処理する` |
| `GOTO 90` | `指定した場所へ進む` |
| `M98 P2000` | `別のプログラムを呼び出す` |
| `M30` | `プログラムを終了する` |
| `M123` | `意味の確認が必要なMコード` |

## Beginner Terminology Rules

| Technical term | Beginner-facing term |
| --- | --- |
| variable | 変数 / 値の入れ物 |
| assignment | 値を入れる |
| expression | 計算式 |
| dependency | 値のつながり |
| condition | 条件 |
| branch | 分かれ道 |
| `IF ... GOTO` | 条件で別の場所へ進む |
| `IF ... THEN` | 条件が合うと処理する |
| `GOTO` | 指定した場所へ進む |
| `WHILE` | 条件の間くり返す |
| subprogram | 別プログラム |
| macro call | マクロ呼び出し |
| standard M code | 一般的な意味が知られているMコード |
| unknown M code | 意味の確認が必要なMコード |
| warning | 確認が必要な点 |

## Web Demo Specification

Target location:

```text
web/
├─ index.html
├─ style.css
└─ app.js
```

Minimum required features:

- Open a sample NC macro immediately.
- Allow browser file selection.
- Allow paste/edit in a text area.
- Provide one clear primary action: `解析する`.
- Show beginner flowchart as the main result.
- Show `確認が必要な点` near the top when warnings exist.
- Show `値のつながり`, `条件分岐`, and `Mコード` as secondary sections.
- Provide a simple Markdown memo download.
- Work as static HTML/CSS/JavaScript for GitHub Pages.

UI requirements:

- Large buttons.
- Clear section titles.
- No command-line requirement.
- Avoid dense tables as the first view.
- Original NC code is secondary detail.
- Warning text should be calm and actionable.

Current Web demo status:

- Static demo exists under `lp/demo/`.
- It includes sample NC code.
- It can parse basic variables, controls, and M codes in JavaScript.
- It already uses beginner-oriented Japanese labels in some places.
- It is not yet integrated with Python output.

## CLI Positioning

CLI remains supported but is no longer the primary product entry.

CLI should be described as:

- Developer-facing.
- Useful for regression checks.
- Useful for generating raw artifacts.
- Useful for expert users.

Do not remove or break:

- `nctool.py`
- `nc_macro_visualizer.cli.main:main`
- console script `nctool`
- default output files:
  - `report.md`
  - `analysis.json`
  - `flow.mmd`
- existing test expectations

Possible v0.2.0 CLI addition:

```text
output/beginner_flow.json
```

This should be added as an extra output or behind an option. It should not replace current outputs.

## Existing Tests

Existing tests cover:

- Parser behavior.
- Analyzer behavior.
- Renderer output.
- CLI smoke behavior.

Known test files:

```text
tests/test_parser.py
tests/test_analyzer.py
tests/test_renderer.py
tests/test_cli.py
```

Current documented test commands:

```bash
python3 -m unittest discover -s tests
.venv/bin/python -m pytest
```

This document creation did not modify code and did not run tests.

## Known Limitations

The current parser is regex-based.

Known limitations:

- No full AST.
- No real expression evaluation.
- No full controller dialect support.
- No execution semantics.
- Variable dependencies are line-local.
- `M98` and `G65` parsing expects a `P` target.
- Flowchart is for reading, not exact machine execution.
- `%` and `O` header/footer lines may exist in `parsed_lines` JSON, though they are excluded from flow rendering.
- Warnings are conservative and do not prove safety.

## Recommended v0.2.0 Implementation Plan

The technical review after this document was first drafted narrowed the v0.2.0 scope. The accepted direction is:

- Do not introduce `core/` in v0.2.0.
- Keep existing `parser/`, `analyzer/`, `models/`, and `renderer/` packages stable.
- Add `flowchart/` beside the current engine.
- Keep beginner flow models separate from `AnalysisResult`.
- Define `schemas/beginner_flow.schema.json` before implementation.
- Add beginner output as opt-in first, for example `--beginner`.
- Copy `lp/demo/` to `web/` and keep both during v0.2.0.
- Add regression tests before structural changes.

Recommended order:

1. Add regression tests for existing v0.1.0 behavior.
2. Add `schemas/beginner_flow.schema.json`.
3. Add `src/nc_macro_visualizer/flowchart/terminology.py`.
4. Add `src/nc_macro_visualizer/flowchart/models.py`.
5. Add beginner flowchart tests for:
   - assignment label: `値を計算する`
   - IF label: `条件で分かれる`
   - unknown M code label: `意味の確認が必要なMコード`
   - branch edge labels: `はい` / `いいえ`
6. Add `src/nc_macro_visualizer/flowchart/builder.py`.
7. Add beginner JSON rendering.
8. Add CLI `--beginner` opt-in output.
9. Copy `lp/demo/` to `web/` in a separate change.
10. Update README after code and Web paths are stable.

The detailed Claude Code handoff is in `docs/claude_code_v0.2_refactor_instructions.md`.

## Migration Rules

To avoid breaking v0.1.0:

- Add modules before moving modules.
- Keep old imports working.
- Keep current CLI outputs unchanged.
- Add new outputs instead of replacing old ones.
- Use compatibility wrappers if `renderer` is renamed to `renderers`.
- Move Web files separately from Python engine changes.
- Run existing tests after each structural step.

Compatibility wrapper example:

```text
src/nc_macro_visualizer/renderers/markdown.py
  -> imports from src/nc_macro_visualizer/renderer/markdown.py
```

## Review Questions for Claude Code

Please check:

1. Whether the proposed structure preserves existing imports and tests.
2. Whether the beginner flowchart model should be added beside `AnalysisResult` or inside it.
3. Whether `core/` should be introduced immediately or delayed until after `flowchart/` is stable.
4. Whether `web/` should be copied from `lp/demo/` first or moved after README links are updated.
5. Whether the M code policy is strict enough to avoid unsafe claims.
6. Whether `beginner_flow.json` should be default CLI output or opt-in.
7. Whether any current tests should be expanded before refactoring directories.
