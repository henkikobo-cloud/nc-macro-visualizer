from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParsedLine:
    line_no: int
    raw_text: str
    code: str
    label: str | None = None


@dataclass(frozen=True)
class VariableHit:
    line_no: int
    name: str
    kind: str
    text: str


@dataclass(frozen=True)
class VariableSummary:
    name: str
    assignments: list[int] = field(default_factory=list)
    references: list[int] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.assignments) + len(self.references)


@dataclass(frozen=True)
class ControlHit:
    line_no: int
    kind: str
    target: str | None
    condition: str
    text: str


@dataclass(frozen=True)
class MCodeHit:
    line_no: int
    code: str
    description: str
    category: str
    text: str


@dataclass(frozen=True)
class LabelHit:
    line_no: int
    label: str
    text: str


@dataclass(frozen=True)
class CallHit:
    line_no: int
    kind: str
    target: str | None
    text: str


@dataclass(frozen=True)
class LoopEndHit:
    line_no: int
    target: str | None
    text: str


@dataclass(frozen=True)
class VariableDependency:
    line_no: int
    target: str
    sources: list[str]
    text: str


@dataclass(frozen=True)
class AnalysisWarning:
    line_no: int | None
    code: str
    message: str
    severity: str = "warning"


@dataclass(frozen=True)
class FlowEdge:
    source: str
    target: str
    label: str


@dataclass(frozen=True)
class AnalysisResult:
    source_name: str
    line_count: int
    parsed_lines: list[ParsedLine]
    variables: list[VariableHit]
    variable_summary: list[VariableSummary]
    controls: list[ControlHit]
    m_codes: list[MCodeHit]
    labels: list[LabelHit]
    calls: list[CallHit]
    loop_ends: list[LoopEndHit]
    variable_dependencies: list[VariableDependency]
    warnings: list[AnalysisWarning]
    flow_edges: list[FlowEdge]
