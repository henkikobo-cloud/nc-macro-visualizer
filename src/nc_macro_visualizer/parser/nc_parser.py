from __future__ import annotations

import re

from nc_macro_visualizer.models import CallHit, ControlHit, LoopEndHit, MCodeHit, ParsedLine, VariableDependency, VariableHit
from nc_macro_visualizer.profiles.fanuc import describe_m_code


VARIABLE_RE = re.compile(r"#(?:<[^>\s]+>|\d+)")
ASSIGNMENT_RE = re.compile(r"(#(?:<[^>\s]+>|\d+))\s*=")
IF_GOTO_RE = re.compile(r"\bIF\b\s*(?P<condition>.*?)\s*\bGOTO\s*(?P<target>\d+)", re.IGNORECASE)
IF_THEN_RE = re.compile(r"\bIF\b\s*(?P<condition>.*?)\s*\bTHEN\b(?P<then>.*)", re.IGNORECASE)
GOTO_RE = re.compile(r"\bGOTO\s*(?P<target>\d+)", re.IGNORECASE)
WHILE_RE = re.compile(r"\bWHILE\b\s*(?P<condition>.*?)\s*\bDO\s*(?P<target>\d*)", re.IGNORECASE)
END_RE = re.compile(r"(?<![A-Z0-9])END\s*(?P<target>\d*)(?![A-Z0-9])", re.IGNORECASE)
M_CODE_RE = re.compile(r"(?<![A-Z0-9])M\s*0*(?P<code>\d+)(?![A-Z0-9])", re.IGNORECASE)
M98_RE = re.compile(r"(?<![A-Z0-9])M\s*0*98\b.*?\bP\s*(?P<target>\d+)", re.IGNORECASE)
G65_RE = re.compile(r"(?<![A-Z0-9])G\s*0*65\b.*?\bP\s*(?P<target>\d+)", re.IGNORECASE)
LABEL_RE = re.compile(r"^\s*N\s*(?P<number>\d+)", re.IGNORECASE)


def strip_comments(line: str) -> str:
    """Remove common NC comments without trying to emulate controller parsing."""
    without_parens = re.sub(r"\([^)]*\)", " ", line)
    without_semicolon = without_parens.split(";", 1)[0].strip()
    return re.sub(r"\s+", " ", without_semicolon)


def parse_lines(text: str) -> list[ParsedLine]:
    parsed: list[ParsedLine] = []
    for line_no, raw_text in enumerate(text.splitlines(), start=1):
        code = strip_comments(raw_text)
        label_match = LABEL_RE.search(code)
        parsed.append(
            ParsedLine(
                line_no=line_no,
                raw_text=raw_text,
                code=code,
                label=label_match.group("number") if label_match else None,
            )
        )
    return parsed


def find_variables(line: ParsedLine) -> list[VariableHit]:
    if not line.code:
        return []

    assignment_positions = {match.start(1) for match in ASSIGNMENT_RE.finditer(line.code)}
    hits: list[VariableHit] = []
    for match in VARIABLE_RE.finditer(line.code):
        kind = "assignment" if match.start() in assignment_positions else "reference"
        hits.append(VariableHit(line.line_no, normalize_variable(match.group(0)), kind, line.code))
    return hits


def find_controls(line: ParsedLine) -> list[ControlHit]:
    if not line.code:
        return []

    if_match = IF_GOTO_RE.search(line.code)
    if if_match:
        return [
            ControlHit(
                line_no=line.line_no,
                kind="IF_GOTO",
                target=if_match.group("target"),
                condition=if_match.group("condition").strip(),
                text=line.code,
            )
        ]

    then_match = IF_THEN_RE.search(line.code)
    if then_match:
        return [
            ControlHit(
                line_no=line.line_no,
                kind="IF_THEN",
                target=None,
                condition=then_match.group("condition").strip(),
                text=line.code,
            )
        ]

    while_match = WHILE_RE.search(line.code)
    if while_match:
        target = while_match.group("target") or None
        return [
            ControlHit(
                line_no=line.line_no,
                kind="WHILE",
                target=target,
                condition=while_match.group("condition").strip(),
                text=line.code,
            )
        ]

    goto_match = GOTO_RE.search(line.code)
    if goto_match:
        return [
            ControlHit(
                line_no=line.line_no,
                kind="GOTO",
                target=goto_match.group("target"),
                condition="",
                text=line.code,
            )
        ]
    return []


def find_m_codes(line: ParsedLine) -> list[MCodeHit]:
    hits: list[MCodeHit] = []
    for match in M_CODE_RE.finditer(line.code):
        code = normalize_m_code(match.group("code"))
        profile = describe_m_code(code)
        hits.append(MCodeHit(line.line_no, code, profile["description"], profile["category"], line.code))
    return hits


def find_calls(line: ParsedLine) -> list[CallHit]:
    calls: list[CallHit] = []
    m98_match = M98_RE.search(line.code)
    if m98_match:
        calls.append(CallHit(line.line_no, "M98", m98_match.group("target"), line.code))

    g65_match = G65_RE.search(line.code)
    if g65_match:
        calls.append(CallHit(line.line_no, "G65", g65_match.group("target"), line.code))
    return calls


def find_loop_ends(line: ParsedLine) -> list[LoopEndHit]:
    hits: list[LoopEndHit] = []
    for match in END_RE.finditer(line.code):
        target = match.group("target") or None
        hits.append(LoopEndHit(line.line_no, target, line.code))
    return hits


def find_variable_dependencies(line: ParsedLine) -> list[VariableDependency]:
    dependencies: list[VariableDependency] = []
    for match in ASSIGNMENT_RE.finditer(line.code):
        target = normalize_variable(match.group(1))
        expression = line.code[match.end() :]
        sources = [
            normalize_variable(source.group(0))
            for source in VARIABLE_RE.finditer(expression)
            if normalize_variable(source.group(0)) != target
        ]
        if sources:
            dependencies.append(VariableDependency(line.line_no, target, dedupe(sources), line.code))
    return dependencies


def normalize_variable(name: str) -> str:
    if name.startswith("#<"):
        return name.upper()
    return "#" + str(int(name[1:]))


def normalize_m_code(code: str) -> str:
    return "M" + str(int(code))


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
