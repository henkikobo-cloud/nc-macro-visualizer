# NC Macro Visualizer Report: 04_variables.nc

## Summary

- Lines: 7
- Labels: 4
- Variables: 7
- IF/GOTO/WHILE/THEN: 1
- M codes: 1
- Calls: 0
- Warnings: 0

> This report is for understanding NC macro assets. It does not guarantee real machine behavior.

## Warnings

No warnings found.

## Variable Summary

| Variable | Count | Assignments | References |
| --- | ---: | --- | --- |
| `#100` | 1 | - | 3 |
| `#101` | 1 | - | 3 |
| `#102` | 1 | 5 | - |
| `#500` | 2 | 3 | 4 |
| `#<RESULT>` | 2 | 4 | 5 |

## Variable Dependencies

| Line | Target | Sources | Code |
| ---: | --- | --- | --- |
| 3 | `#500` | `#100`, `#101` | `N10 #500 = #100 + #101` |
| 4 | `#<RESULT>` | `#500` | `N20 #<RESULT> = #500` |

## Variable Occurrences

| Line | Variable | Kind | Code |
| ---: | --- | --- | --- |
| 3 | `#500` | assignment | `N10 #500 = #100 + #101` |
| 3 | `#100` | reference | `N10 #500 = #100 + #101` |
| 3 | `#101` | reference | `N10 #500 = #100 + #101` |
| 4 | `#<RESULT>` | assignment | `N20 #<RESULT> = #500` |
| 4 | `#500` | reference | `N20 #<RESULT> = #500` |
| 5 | `#<RESULT>` | reference | `N30 IF [#<RESULT> GT 0] THEN #102 = 1` |
| 5 | `#102` | assignment | `N30 IF [#<RESULT> GT 0] THEN #102 = 1` |

## Flow Controls

| Line | Type | Target | Condition | Code |
| ---: | --- | --- | --- | --- |
| 5 | IF_THEN | - | `[#<RESULT> GT 0]` | `N30 IF [#<RESULT> GT 0] THEN #102 = 1` |

## M Codes

| Line | M Code | Description | Category | Code |
| ---: | --- | --- | --- | --- |
| 6 | `M30` | program_end_and_rewind | standard | `N40 M30` |

## Subprogram / Macro Calls

No M98 or G65 calls found.
