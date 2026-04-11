from __future__ import annotations

import re
from typing import Mapping, Sequence

COMPLETION_INTEGRITY_DIRECTIVE_RE = re.compile(r"^\s*-\s*(REQUIRE_EXISTING_TOUCH|MIN_EXISTING_NONTEST_TOUCHES|ALLOW_HELPER_ONLY):\s*(.+)$")
INTEGRATION_INTENT_RE = re.compile(
    r"\b(integrat(?:e|ion|ed)|wire(?:d|s|\s+into)?|live harness|session flow|artifact flow|existing flow|scorecard integration|completion integrity)\b",
    re.IGNORECASE,
)


def parse_completion_integrity_directives(task_text: str) -> dict[str, object]:
    required_existing: list[str] = []
    min_existing_nontest_touches = 0
    allow_helper_only: bool | None = None
    in_section = False
    for raw in str(task_text or '').splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith('##'):
            header = line.lstrip('#').strip().lower()
            in_section = 'completion integrity' in header
            continue
        if not in_section:
            continue
        m = COMPLETION_INTEGRITY_DIRECTIVE_RE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if key == 'REQUIRE_EXISTING_TOUCH':
            value = value.replace('\\', '/').strip()
            if value:
                required_existing.append(value)
        elif key == 'MIN_EXISTING_NONTEST_TOUCHES':
            try:
                min_existing_nontest_touches = max(0, int(value))
            except ValueError:
                min_existing_nontest_touches = 0
        elif key == 'ALLOW_HELPER_ONLY':
            allow_helper_only = value.lower() in {'1','true','yes','y'}
    return {
        'required_existing_touches': required_existing,
        'min_existing_nontest_touches': min_existing_nontest_touches,
        'allow_helper_only': allow_helper_only,
    }


def _is_task_or_test_or_doc(path: str) -> bool:
    p = path.replace('\\','/').lstrip('./')
    return p.startswith('tasks/') or p.startswith('tests/') or p.startswith('docs/') or p in {'README.md'}


def _existing_nontest_touches(bundle: Mapping[str, str], baseline: Mapping[str, str] | None) -> list[str]:
    base = dict(baseline or {})
    touches: list[str] = []
    for path in bundle:
        if path in base and not _is_task_or_test_or_doc(path):
            touches.append(path)
    return touches


def _new_nontest_paths(bundle: Mapping[str, str], baseline: Mapping[str, str] | None) -> list[str]:
    base = dict(baseline or {})
    paths: list[str] = []
    for path in bundle:
        if path not in base and not _is_task_or_test_or_doc(path):
            paths.append(path)
    return paths


def _integration_intent(task_text: str) -> bool:
    return bool(INTEGRATION_INTENT_RE.search(str(task_text or '')))


def evaluate_completion_integrity_gate(
    task_text: str,
    bundle: Mapping[str, str],
    *,
    baseline: Mapping[str, str] | None = None,
    required_paths: Sequence[str] | None = None,
) -> tuple[bool, str]:
    directives = parse_completion_integrity_directives(task_text)
    existing_touches = sorted(set(_existing_nontest_touches(bundle, baseline)))
    new_nontest_paths = sorted(set(_new_nontest_paths(bundle, baseline)))

    allow_helper_only = directives['allow_helper_only']
    if allow_helper_only is None:
        allow_helper_only = not _integration_intent(task_text)

    min_existing = int(directives.get('min_existing_nontest_touches', 0) or 0)
    if _integration_intent(task_text) and min_existing == 0 and not allow_helper_only:
        min_existing = 1

    issues: list[str] = []

    required_existing = [str(x) for x in directives.get('required_existing_touches', []) or []]
    missing_required = [p for p in required_existing if p not in existing_touches]
    if missing_required:
        issues.append(
            'required existing integration surfaces were not touched: ' + ', '.join(sorted(missing_required))
        )

    if len(existing_touches) < min_existing:
        issues.append(
            f'expected at least {min_existing} existing non-test/doc integration surface touch(es), found {len(existing_touches)}'
        )

    if not allow_helper_only and not existing_touches and new_nontest_paths:
        issues.append(
            'bundle appears helper-only or new-surface-only without touching an existing live integration surface: '
            + ', '.join(new_nontest_paths)
        )

    if issues:
        summary = [
            'Completion integrity gate failed:',
            *[f'- {issue}' for issue in issues],
        ]
        if existing_touches:
            summary.append('existing integration touches: ' + ', '.join(existing_touches))
        if new_nontest_paths:
            summary.append('new non-test/doc paths: ' + ', '.join(new_nontest_paths))
        if required_paths:
            summary.append('required paths: ' + ', '.join(str(x) for x in required_paths))
        return False, '\n'.join(summary)

    return True, ''
