from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set


@dataclass(frozen=True)
class DeliverableContract:
    deliverables: List[str]
    requires_existing_surface: bool
    raw_text_excerpt: str


def _extract_bullet_block(lines: Sequence[str], start_idx: int) -> List[str]:
    items: List[str] = []
    for i in range(start_idx, len(lines)):
        line = lines[i].rstrip()
        if not line:
            # allow blank lines inside block; continue until non-bullet line
            continue
        if re.match(r"^\s*-\s+", line):
            # take bullet content after the dash
            content = re.sub(r"^\s*-\s+", "", line).strip()
            if content:
                items.append(content)
            continue
        # first non-bullet, non-empty line stops the block
        if items:
            break
        # if no items yet and we hit a non-bullet, it means no block here
        break
    return items


def parse_explicit_deliverable_contract(task_text: str) -> DeliverableContract:
    """
    Parse an explicit deliverable contract from a task text.

    - Collects deliverables that appear under a "Create or update these exact files" section.
    - Detects whether the task explicitly requires touching existing surfaces (existing files)
      via phrases like "existing-surface", "existing surface", or "existing live surface".
    """
    lines = task_text.splitlines()
    deliverables: List[str] = []
    excerpt_lines: List[str] = []

    # Find "Create or update these exact files" header and capture following bullet list
    header_pattern = re.compile(r"^\s*Create or update these exact files\s*$", re.IGNORECASE)
    for idx, line in enumerate(lines):
        if header_pattern.match(line.strip()):
            excerpt_lines.append(line)
            block = _extract_bullet_block(lines, idx + 1)
            if block:
                deliverables.extend(block)
                excerpt_lines.extend(lines[idx + 1 : idx + 1 + len(block)])

    # Normalize deliverables (strip trailing punctuation that can follow in some docs)
    normalized: List[str] = []
    for d in deliverables:
        # keep exact path; just remove trailing commas/backticks/periods
        nd = d.strip().strip("`").rstrip(",.")
        normalized.append(nd)

    # Detect existing-surface requirement with robust phrase variants
    text_lower = task_text.lower()
    requires_existing_surface = any(
        phrase in text_lower
        for phrase in [
            "existing-surface",
            "existing surface",
            "existing live surface",
            "existing-surface touch",
            "touch the existing surface",
            "required existing-surface",
        ]
    )

    return DeliverableContract(
        deliverables=normalized,
        requires_existing_surface=requires_existing_surface,
        raw_text_excerpt="\n".join(excerpt_lines).strip(),
    )


def evaluate_existing_surface_touch(
    contract: DeliverableContract,
    bundle_paths: Iterable[str],
    existing_repo_paths: Optional[Set[str]] = None,
) -> Dict[str, object]:
    """
    Evaluate whether completion touches existing surfaces as mandated by the contract.

    - existing_repo_paths: the known set of repository files that already exist.
      If omitted, only membership in the contract.deliverables is considered an "existing surface".
    """
    bundle = list(bundle_paths)
    existing_set: Set[str] = set(existing_repo_paths or [])
    contract_set: Set[str] = set(contract.deliverables)

    # An "existing-surface" touch means the bundle modified a file that:
    # - is in the existing repository set (if provided), and
    # - is one of the exact deliverables
    if existing_set:
        existing_surface_touches: List[str] = [
            p for p in bundle if p in existing_set and p in contract_set
        ]
    else:
        # Fallback: treat deliverables as the definition of "existing surface"
        existing_surface_touches = [p for p in bundle if p in contract_set]

    requires_touch = contract.requires_existing_surface
    helper_only = requires_touch and len(existing_surface_touches) == 0

    missing_required = sorted(p for p in contract.deliverables if p not in bundle)

    status = "reject" if helper_only else "ok"

    return {
        "status": status,
        "reason": "helper_only" if helper_only else "ok",
        "requires_existing_surface": requires_touch,
        "existing_surface_touches": existing_surface_touches,
        "bundle_paths": list(bundle),
        "required_deliverables": list(contract.deliverables),
        "missing_required": missing_required,
    }


def build_completion_repair_feedback(
    contract: DeliverableContract,
    evaluation: Dict[str, object],
) -> str:
    """
    Build explicit, mechanical feedback appended after a completion-integrity failure.

    The feedback emphasizes:
    - exact deliverables
    - explicit requirement to touch existing surfaces when mandated
    - concrete differences between what was changed vs what was required
    """
    status = str(evaluation.get("status", "ok"))
    reason = str(evaluation.get("reason", "ok"))
    requires_touch = bool(evaluation.get("requires_existing_surface", False))

    if status != "reject" or reason != "helper_only":
        # No feedback needed on success or non-helper-only rejections.
        return ""

    bundle_paths = [str(x) for x in evaluation.get("bundle_paths", [])]
    required = [str(x) for x in evaluation.get("required_deliverables", [])]
    touches = [str(x) for x in evaluation.get("existing_surface_touches", [])]
    missing = [str(x) for x in evaluation.get("missing_required", [])]

    lines: List[str] = []
    lines.append("COMPLETION-INTEGRITY REPAIR INSTRUCTIONS")
    lines.append("")
    lines.append("Your bundle modified only new/helper files and did not update the required existing surfaces.")
    if requires_touch:
        lines.append("This task explicitly requires touching existing surfaces.")
    if contract.raw_text_excerpt:
        lines.append("Deliverable contract excerpt:")
        lines.append(contract.raw_text_excerpt)
    lines.append("")
    lines.append("You MUST update these exact existing-surface files:")
    for path in required:
        lines.append(f"- {path}")
    lines.append("")
    lines.append("Files you changed in the rejected bundle:")
    if bundle_paths:
        for path in bundle_paths:
            lines.append(f"- {path}")
    else:
        lines.append("- (no files reported)")

    if touches:
        lines.append("")
        lines.append("Note: Some changes touched deliverables but did not satisfy the existing-surface requirement:")
        for path in touches:
            lines.append(f"- {path}")

    if missing:
        lines.append("")
        lines.append("Missing required deliverables from your bundle:")
        for path in missing:
            lines.append(f"- {path}")

    lines.append("")
    lines.append("Repair steps:")
    lines.append("- Modify at least one of the required existing-surface files listed above.")
    lines.append("- Keep changes deterministic and limited to the specified files.")
    lines.append("- Re-run with a bundle that includes those exact file paths.")

    return "\n".join(lines)


__all__ = [
    "DeliverableContract",
    "parse_explicit_deliverable_contract",
    "evaluate_existing_surface_touch",
    "build_completion_repair_feedback",
]
