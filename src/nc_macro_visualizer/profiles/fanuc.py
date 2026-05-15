from __future__ import annotations


STANDARD_M_CODES: dict[str, str] = {
    "M0": "program_stop",
    "M1": "optional_stop",
    "M2": "program_end",
    "M3": "spindle_on_clockwise",
    "M4": "spindle_on_counterclockwise",
    "M5": "spindle_stop",
    "M6": "tool_change",
    "M8": "coolant_on",
    "M9": "coolant_off",
    "M30": "program_end_and_rewind",
    "M98": "subprogram_call",
    "M99": "subprogram_return",
}


def describe_m_code(code: str) -> dict[str, str]:
    description = STANDARD_M_CODES.get(code)
    if description is None:
        return {"description": "unknown", "category": "machine_specific"}
    return {"description": description, "category": "standard"}
