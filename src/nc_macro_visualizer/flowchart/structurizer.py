from __future__ import annotations

from nc_macro_visualizer.flowchart.cfg import CFGEdge, CFGNode, ControlFlowGraph
from nc_macro_visualizer.flowchart.models import (
    BeginnerFlow,
    BeginnerNode,
    StructuredBlock,
    StructuredNode,
    StructuredProgram,
    StructuredTree,
)
from nc_macro_visualizer.flowchart.terminology import (
    CALL_TITLE,
    IF_THEN_ELSE_TITLE,
    IF_THEN_TITLE,
    MACHINE_ACTION_TITLE,
    PROGRAM_END_TITLE,
    UNSTRUCTURED_JUMP_NOTE,
    UNKNOWN_M_CODE_MESSAGE,
    UNKNOWN_M_CODE_TITLE,
    WHILE_TITLE,
)
from nc_macro_visualizer.parser import find_m_codes, find_variable_dependencies


def structurize_beginner_flow(flow: BeginnerFlow) -> StructuredProgram:
    nodes = [node for node in flow.nodes if node.kind not in {"start", "end"}]
    node_by_id = {node.id: node for node in nodes}
    skip_ids: set[str] = set()
    blocks: list[StructuredBlock] = []

    for node in nodes:
        if node.id in skip_ids or node.kind == "jump_in":
            continue

        if node.kind == "decision":
            true_targets = [edge.target for edge in flow.edges if edge.source == node.id and edge.kind == "branch_true"]
            false_targets = [edge.target for edge in flow.edges if edge.source == node.id and edge.kind == "branch_false"]
            true_children: list[StructuredBlock] = []
            note = ""

            if true_targets:
                true_node = node_by_id.get(true_targets[0])
                if true_node is not None and true_node.id.endswith("_THEN"):
                    true_children.append(block_from_node(true_node))
                    skip_ids.add(true_node.id)
                else:
                    note = f"はいの場合は {true_targets[0]} へ進みます。"

            false_children = []
            if false_targets:
                note = f"{note} いいえの場合は {false_targets[0]} へ進みます。".strip()

            blocks.append(
                StructuredBlock(
                    kind="if",
                    title=node.title,
                    summary=node.summary,
                    source_line_no=node.source_line_no,
                    source_label=node.source_label,
                    source_text=node.source_text,
                    children=true_children,
                    false_children=false_children,
                    note=note,
                )
            )
            continue

        blocks.append(block_from_node(node))

    return StructuredProgram(source_name=flow.source_name, blocks=blocks)


def block_from_node(node: BeginnerNode) -> StructuredBlock:
    kind = node.kind
    if node.kind in {"jump_out", "jump_in"}:
        kind = "jump"
    elif node.kind == "needs_confirmation":
        kind = "warning"
    elif node.kind == "machine_action":
        kind = "machine"
    elif node.kind == "call":
        kind = "call"
    elif node.kind == "decision":
        kind = "if"
    else:
        kind = "process"

    return StructuredBlock(
        kind=kind,
        title=node.title,
        summary=node.summary,
        source_line_no=node.source_line_no,
        source_label=node.source_label,
        source_text=node.source_text,
    )


def structurize_cfg(cfg: ControlFlowGraph) -> StructuredTree:
    context = StructurizerContext(cfg)
    start = context.first_target(cfg.entry_node_id)
    children, _ = context.build_sequence(start, stop_ids=set())
    return StructuredTree(
        source_name=cfg.source_name,
        root=StructuredNode(
            id="ROOT",
            kind="sequence",
            title="",
            summary="",
            source_line_no=None,
            source_label=None,
            source_text=None,
            children=children,
        ),
    )


class StructurizerContext:
    def __init__(self, cfg: ControlFlowGraph) -> None:
        self.cfg = cfg
        self.nodes = {node.id: node for node in cfg.nodes}
        self.outgoing: dict[str, list[CFGEdge]] = {}
        self.incoming: dict[str, list[CFGEdge]] = {}
        for edge in cfg.edges:
            self.outgoing.setdefault(edge.source, []).append(edge)
            self.incoming.setdefault(edge.target, []).append(edge)
        self.visited: set[str] = set()

    def first_target(self, source: str) -> str | None:
        for edge in self.outgoing.get(source, []):
            if edge.kind == "forward":
                return edge.target
        return None

    def edge(self, source: str, kind: str) -> CFGEdge | None:
        for edge in self.outgoing.get(source, []):
            if edge.kind == kind:
                return edge
        return None

    def build_sequence(self, start_id: str | None, stop_ids: set[str]) -> tuple[list[StructuredNode], str | None]:
        result: list[StructuredNode] = []
        current_id = start_id

        while current_id and current_id not in stop_ids and current_id not in self.cfg.exit_node_ids:
            if current_id in self.visited:
                break
            node = self.nodes.get(current_id)
            if node is None:
                break

            for matcher in (
                self.try_match_while,
                self.try_match_if_then_else,
                self.try_match_if_then,
                self.try_match_sequence,
                self.try_match_call,
            ):
                matched = matcher(node, stop_ids)
                if matched is not None:
                    structured, next_id = matched
                    result.append(structured)
                    current_id = next_id
                    break
            else:
                structured, next_id = self.match_unstructured(node)
                result.append(structured)
                current_id = next_id

        return result, current_id

    def try_match_while(self, node: CFGNode, stop_ids: set[str]) -> tuple[StructuredNode, str | None] | None:
        true_edge = self.edge(node.id, "branch_true")
        false_edge = self.edge(node.id, "branch_false")
        if node.kind != "decision" or true_edge is None or false_edge is None:
            return None
        back_sources = [edge.source for edge in self.incoming.get(node.id, []) if edge.kind == "back"]
        if not back_sources:
            return None

        self.visited.add(node.id)
        body_stop = set(back_sources)
        children, _ = self.build_sequence(true_edge.target, stop_ids | body_stop)
        for source in back_sources:
            self.visited.add(source)
        return (
            structured_from_cfg_node(
                node,
                "while_loop",
                title=WHILE_TITLE,
                summary=f"{true_edge.condition} の間、処理をくり返します",
                children=children,
                condition=true_edge.condition,
            ),
            false_edge.target,
        )

    def try_match_if_then_else(self, node: CFGNode, stop_ids: set[str]) -> tuple[StructuredNode, str | None] | None:
        true_edge = self.edge(node.id, "branch_true")
        false_edge = self.edge(node.id, "branch_false")
        if node.kind != "decision" or true_edge is None or false_edge is None:
            return None
        true_next = self.linear_successor(true_edge.target)
        false_next = self.linear_successor(false_edge.target)
        if true_next is None or true_next != false_next:
            return None

        self.visited.add(node.id)
        then_children, _ = self.build_sequence(true_edge.target, stop_ids | {true_next})
        else_children, _ = self.build_sequence(false_edge.target, stop_ids | {true_next})
        return (
            structured_from_cfg_node(
                node,
                "if_then_else",
                title=IF_THEN_ELSE_TITLE,
                summary=f"{true_edge.condition} によって処理が変わります",
                children=[
                    sequence_node(f"{node.id}_THEN", then_children),
                    sequence_node(f"{node.id}_ELSE", else_children),
                ],
                condition=true_edge.condition,
            ),
            true_next,
        )

    def try_match_if_then(self, node: CFGNode, stop_ids: set[str]) -> tuple[StructuredNode, str | None] | None:
        true_edge = self.edge(node.id, "branch_true")
        false_edge = self.edge(node.id, "branch_false")
        if node.kind != "decision" or true_edge is None or false_edge is None:
            return None
        true_next = self.linear_successor(true_edge.target)
        if true_next != false_edge.target:
            return None

        self.visited.add(node.id)
        then_children, _ = self.build_sequence(true_edge.target, stop_ids | {false_edge.target})
        return (
            structured_from_cfg_node(
                node,
                "if_then",
                title=IF_THEN_TITLE,
                summary=f"{true_edge.condition} なら処理を行います",
                children=then_children,
                condition=true_edge.condition,
            ),
            false_edge.target,
        )

    def try_match_sequence(self, node: CFGNode, stop_ids: set[str]) -> tuple[StructuredNode, str | None] | None:
        if node.kind in {"decision", "call_site"}:
            return None
        if node.kind == "jump_source" or any(edge.kind == "jump" for edge in self.outgoing.get(node.id, [])):
            return None
        self.visited.add(node.id)
        return structured_process_node(node), self.first_target(node.id)

    def try_match_call(self, node: CFGNode, stop_ids: set[str]) -> tuple[StructuredNode, str | None] | None:
        if node.kind != "call_site":
            return None
        self.visited.add(node.id)
        return structured_from_cfg_node(node, "call", CALL_TITLE, CALL_TITLE), self.first_target(node.id)

    def match_unstructured(self, node: CFGNode) -> tuple[StructuredNode, str | None]:
        self.visited.add(node.id)
        edge = next(iter(self.outgoing.get(node.id, [])), None)
        target = edge.target if edge is not None else None
        summary = f"{target} へジャンプします" if target else "指定した場所へジャンプします"
        return (
            structured_from_cfg_node(
                node,
                "unstructured_jump",
                title="指定した場所へ進む",
                summary=summary,
                note=UNSTRUCTURED_JUMP_NOTE,
            ),
            target if edge is not None and edge.kind == "forward" else None,
        )

    def linear_successor(self, start_id: str) -> str | None:
        current = start_id
        seen: set[str] = set()
        while current not in seen:
            seen.add(current)
            outgoing = self.outgoing.get(current, [])
            forward = [edge for edge in outgoing if edge.kind == "forward"]
            if len(forward) != 1:
                return current
            target = forward[0].target
            if len(self.incoming.get(target, [])) > 1 or target in self.cfg.exit_node_ids:
                return target
            current = target
        return current


def structured_process_node(node: CFGNode) -> StructuredNode:
    if node.kind == "unresolved":
        return structured_from_cfg_node(
            node,
            "unstructured_jump",
            title="指定した場所へ進む",
            summary=f"N{node.source_label} へジャンプします",
            note=UNSTRUCTURED_JUMP_NOTE,
        )
    if any(hit.description == "unknown" for hit in m_codes_from_node(node)):
        return structured_from_cfg_node(node, "needs_confirmation", UNKNOWN_M_CODE_TITLE, UNKNOWN_M_CODE_MESSAGE)
    if m_codes_from_node(node):
        title = PROGRAM_END_TITLE if any(hit.code in {"M30", "M99"} for hit in m_codes_from_node(node)) else MACHINE_ACTION_TITLE
        kind = "end" if title == PROGRAM_END_TITLE else "machine_action"
        return structured_from_cfg_node(node, kind, title, title)
    return structured_from_cfg_node(node, "process", title_from_statement(node), summary_from_statement(node))


def structured_from_cfg_node(
    node: CFGNode,
    kind: str,
    title: str,
    summary: str,
    *,
    children: list[StructuredNode] | None = None,
    condition: str | None = None,
    note: str | None = None,
) -> StructuredNode:
    return StructuredNode(
        id=node.id,
        kind=kind,
        title=title,
        summary=summary,
        source_line_no=node.source_line_no,
        source_label=node.source_label,
        source_text=node.source_text,
        children=children or [],
        condition=condition,
        note=note,
    )


def sequence_node(node_id: str, children: list[StructuredNode]) -> StructuredNode:
    return StructuredNode(node_id, "sequence", "", "", None, None, None, children)


def m_codes_from_node(node: CFGNode):
    from nc_macro_visualizer.models import ParsedLine

    if node.source_text is None:
        return []
    return find_m_codes(ParsedLine(node.source_line_no or 0, node.source_text, node.source_text, node.source_label))


def title_from_statement(node: CFGNode) -> str:
    text = node.statements[0] if node.statements else ""
    if "=" in text:
        return "値を計算する" if find_variable_dependencies_from_text(node) else "値を入れる"
    return "処理する"


def summary_from_statement(node: CFGNode) -> str:
    return node.statements[0] if node.statements else ""


def find_variable_dependencies_from_text(node: CFGNode):
    from nc_macro_visualizer.models import ParsedLine

    if node.source_text is None:
        return []
    return find_variable_dependencies(ParsedLine(node.source_line_no or 0, node.source_text, node.source_text, node.source_label))
