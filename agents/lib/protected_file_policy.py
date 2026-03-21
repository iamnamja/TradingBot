from __future__ import annotations

from typing import Callable, Dict, List, Pattern, Tuple


def parse_harness_file_policies(
    *,
    task_text: str,
    iter_markdown_sections: Callable[[str], List[Tuple[str, List[str]]]],
    task_file_policy_re: Pattern[str],
    parse_task_file_attrs: Callable[[str], Dict[str, str]],
    normalize_anchor_token: Callable[[str], str],
    normalize_method_token: Callable[[str], str],
) -> Dict[str, Dict[str, object]]:
    policies: Dict[str, Dict[str, object]] = {}
    allowed_section_names = {
        "deliverables",
        "harness policy",
        "machine-readable contract directives",
    }

    for section_name, section_lines in iter_markdown_sections(task_text):
        parse_file_directives = section_name in allowed_section_names
        for raw_line in section_lines:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("HARNESS_POLICY:"):
                try:
                    _, rest = line.split("HARNESS_POLICY:", 1)
                    path_and_rule = rest.strip()
                    path, rule = path_and_rule.split(None, 1)
                except ValueError:
                    continue
                normalized_path = path.strip().replace("\\", "/")
                normalized_rule = rule.strip()
                if normalized_path and normalized_rule:
                    entry = policies.setdefault(normalized_path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(normalized_rule)
                continue

            if not parse_file_directives:
                continue

            m = task_file_policy_re.match(line)
            if not m:
                continue
            if "MODE=" not in line:
                continue
            path = m.group("path").strip().replace("\\", "/")
            attrs = parse_task_file_attrs((m.group("rest") or "").strip())
            mode = attrs.get("MODE", "").strip().upper()
            if not path or not mode:
                continue
            if mode == "PROTECTED_FORBID":
                entry = policies.setdefault(path, {"rules": []})
                rules = entry.setdefault("rules", [])
                if isinstance(rules, list):
                    rules.append("forbid")
            elif mode == "EXACT_COPY":
                entry = policies.setdefault(path, {"rules": []})
                rules = entry.setdefault("rules", [])
                if isinstance(rules, list):
                    rules.append("exact_copy")
            elif mode == "EXACT_COPY_PLUS_APPEND_METHOD":
                anchor = attrs.get("ANCHOR_BEFORE", "").strip()
                if anchor:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"append_before:{normalize_anchor_token(anchor)}")
                allow_method = normalize_method_token(attrs.get("ALLOW_NEW_METHOD", "").strip())
                if allow_method:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"allow_methods:{allow_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"max_changed_lines:{max_changed}")
            elif mode == "EXACT_COPY_PLUS_REPLACE_METHOD":
                replace_method = normalize_method_token(
                    attrs.get("TARGET_METHOD", "").strip()
                    or attrs.get("REPLACE_METHOD", "").strip()
                    or attrs.get("ALLOW_EXISTING_METHOD", "").strip()
                )
                if replace_method:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"replace_method:{replace_method}")
                        rules.append(f"allow_methods:{replace_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"max_changed_lines:{max_changed}")
            elif mode == "METHOD_ADD_ONLY":
                allow_method = normalize_method_token(attrs.get("ALLOW_NEW_METHOD", "").strip())
                if allow_method:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"allow_methods:{allow_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"max_changed_lines:{max_changed}")
    return policies


def extract_protected_method_targets(
    *,
    task_text: str,
    iter_markdown_sections: Callable[[str], List[Tuple[str, List[str]]]],
    task_file_policy_re: Pattern[str],
    parse_task_file_attrs: Callable[[str], Dict[str, str]],
    normalize_anchor_token: Callable[[str], str],
    normalize_method_token: Callable[[str], str],
) -> List[Dict[str, object]]:
    targets: List[Dict[str, object]] = []
    allowed_section_names = {
        "deliverables",
        "harness policy",
        "machine-readable contract directives",
    }

    for section_name, section_lines in iter_markdown_sections(task_text):
        if section_name not in allowed_section_names:
            continue

        for raw_line in section_lines:
            line = raw_line.strip()
            if not line:
                continue

            m = task_file_policy_re.match(line)
            if not m or "MODE=" not in line:
                continue

            path = m.group("path").strip().replace("\\", "/")
            attrs = parse_task_file_attrs((m.group("rest") or "").strip())
            mode = attrs.get("MODE", "").strip().upper()
            if not path or not mode:
                continue

            max_changed_lines = None
            raw_limit = attrs.get("MAX_CHANGED_LINES", "").strip()
            if raw_limit:
                try:
                    max_changed_lines = int(raw_limit)
                except ValueError:
                    max_changed_lines = None

            if mode == "EXACT_COPY_PLUS_REPLACE_METHOD":
                method_name = normalize_method_token(
                    attrs.get("TARGET_METHOD", "").strip()
                    or attrs.get("REPLACE_METHOD", "").strip()
                    or attrs.get("ALLOW_EXISTING_METHOD", "").strip()
                )
                if method_name:
                    targets.append(
                        {
                            "path": path,
                            "mode": "replace",
                            "method_name": method_name,
                            "max_changed_lines": max_changed_lines,
                        }
                    )
            elif mode == "EXACT_COPY_PLUS_APPEND_METHOD":
                method_name = normalize_method_token(attrs.get("ALLOW_NEW_METHOD", "").strip())
                anchor = attrs.get("ANCHOR_BEFORE", "").strip()
                if method_name and anchor:
                    targets.append(
                        {
                            "path": path,
                            "mode": "append",
                            "anchor": normalize_anchor_token(anchor),
                            "method_name": method_name,
                            "max_changed_lines": max_changed_lines,
                        }
                    )

    return targets
