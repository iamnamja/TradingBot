from __future__ import annotations

from typing import Callable, Dict, List, Pattern, Tuple


def parse_task_contract_directives(
    *,
    task_text: str,
    iter_markdown_sections: Callable[[str], List[Tuple[str, List[str]]]],
    contract_directive_re: Pattern[str],
) -> Dict[str, List[str]]:
    directives: Dict[str, List[str]] = {}
    allowed_sections = {"", "machine-readable contract directives", "critical", "current runner baseline — must match exactly"}
    for section_name, section_lines in iter_markdown_sections(task_text):
        if section_name not in allowed_sections and "contract" not in section_name:
            continue
        for raw_line in section_lines:
            m = contract_directive_re.match(raw_line)
            if not m:
                continue
            key = m.group(1).strip().upper()
            value = m.group(2).strip()
            directives.setdefault(key, []).append(value)
    return directives
