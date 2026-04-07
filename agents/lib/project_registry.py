from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from agents.lib.project_workspace_adapter import (
    canonical_workspace_contract,
    generic_python_workspace_contract,
    tradingbot_workspace_contract,
)

PROJECT_AUTONOMY_LANES = (
    'manual_only',
    'supervised_local_first',
    'bounded_ordinary_local_first',
)
PROJECT_WORKSPACE_TYPES = (
    'monorepo_python',
    'external_python',
)


@dataclass(frozen=True)
class ProjectRegistryEntry:
    project_id: str
    display_name: str
    repo_root: str
    workspace_type: str
    allowed_autonomy_lane: str
    allow_unattended_execution: bool
    workspace_contract: dict[str, object]
    validation_contract: dict[str, object]
    branch_policy: dict[str, object]
    notes: str = ''

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalize_str_list(values: Sequence[object] | None) -> list[str]:
    result: list[str] = []
    for value in values or ():
        text = str(value or '').strip()
        if text:
            result.append(text)
    return result


def _normalize_repo_root(value: object) -> str:
    text = str(value or '.').strip().replace('\\', '/')
    if text in {'', './'}:
        return '.'
    if text.startswith('./'):
        return text[2:]
    return text


def _normalize_validation_contract(payload: Mapping[str, object] | None, *, workspace_contract: Mapping[str, object]) -> dict[str, object]:
    src = dict(payload or {})
    full_commands = _normalize_str_list(src.get('full_validation_commands')) or list(workspace_contract.get('validation_commands', []))
    focused_commands = _normalize_str_list(src.get('focused_validation_commands'))
    if not focused_commands:
        focused_commands = [full_commands[-1]] if full_commands else []
    acceptance_commands = _normalize_str_list(src.get('acceptance_evidence_commands')) or list(
        workspace_contract.get('acceptance_evidence_commands', [])
    )
    verification_authority_profile = str(
        src.get('verification_authority_profile')
        or workspace_contract.get('merge_policy_constraints', {}).get('verification_authority_profile', 'local_plus_required_ci')
    ).strip() or 'local_plus_required_ci'
    return {
        'focused_validation_commands': focused_commands,
        'full_validation_commands': full_commands,
        'acceptance_evidence_commands': acceptance_commands,
        'verification_authority_profile': verification_authority_profile,
    }


def _normalize_branch_policy(payload: Mapping[str, object] | None, *, project_id: str) -> dict[str, object]:
    src = dict(payload or {})
    pattern = str(src.get('branch_naming_pattern') or f'project/{project_id}/*').strip() or f'project/{project_id}/*'
    return {
        'branch_naming_pattern': pattern,
        'default_base_branch': str(src.get('default_base_branch', 'main') or 'main'),
        'require_clean_main_reset': bool(src.get('require_clean_main_reset', True)),
        'allow_autonomous_merge': bool(src.get('allow_autonomous_merge', False)),
    }


def canonical_project_contract(payload: Mapping[str, object] | None = None, **overrides: object) -> dict[str, object]:
    src = dict(payload or {})
    src.update(overrides)

    project_id = str(src.get('project_id', 'tradingbot_monorepo') or 'tradingbot_monorepo').strip() or 'tradingbot_monorepo'
    display_name = str(src.get('display_name', project_id) or project_id).strip() or project_id
    repo_root = _normalize_repo_root(src.get('repo_root', '.'))
    workspace_type = str(src.get('workspace_type', 'monorepo_python') or 'monorepo_python').strip() or 'monorepo_python'
    if workspace_type not in PROJECT_WORKSPACE_TYPES:
        workspace_type = 'external_python' if 'external' in workspace_type else 'monorepo_python'
    allowed_lane = str(src.get('allowed_autonomy_lane', 'supervised_local_first') or 'supervised_local_first').strip()
    if allowed_lane not in PROJECT_AUTONOMY_LANES:
        allowed_lane = 'supervised_local_first'
    unattended = bool(src.get('allow_unattended_execution', False))

    workspace_payload = src.get('workspace_contract')
    if workspace_payload is None:
        if workspace_type == 'monorepo_python':
            workspace_payload = tradingbot_workspace_contract(repo_root)
        else:
            workspace_payload = generic_python_workspace_contract(repo_root)
    workspace_contract = canonical_workspace_contract(workspace_payload)
    validation_contract = _normalize_validation_contract(src.get('validation_contract'), workspace_contract=workspace_contract)
    branch_policy = _normalize_branch_policy(src.get('branch_policy'), project_id=project_id)

    entry = ProjectRegistryEntry(
        project_id=project_id,
        display_name=display_name,
        repo_root=repo_root,
        workspace_type=workspace_type,
        allowed_autonomy_lane=allowed_lane,
        allow_unattended_execution=unattended,
        workspace_contract=workspace_contract,
        validation_contract=validation_contract,
        branch_policy=branch_policy,
        notes=str(src.get('notes', '') or ''),
    )
    return entry.to_dict()


def tradingbot_project_contract(repo_root: str = '.') -> dict[str, object]:
    return canonical_project_contract(
        project_id='tradingbot_monorepo',
        display_name='TradingBot Monorepo',
        repo_root=repo_root,
        workspace_type='monorepo_python',
        allowed_autonomy_lane='supervised_local_first',
        allow_unattended_execution=False,
        workspace_contract=tradingbot_workspace_contract(repo_root),
        validation_contract={
            'focused_validation_commands': ['pytest -q tests/test_run_task_runtime_foundations.py'],
            'full_validation_commands': ['ruff check .', 'pytest -q'],
            'acceptance_evidence_commands': ['pytest -q tests/test_run_task_runtime_foundations.py'],
            'verification_authority_profile': 'local_plus_required_ci',
        },
        branch_policy={
            'branch_naming_pattern': 'feature/*',
            'default_base_branch': 'main',
            'require_clean_main_reset': True,
            'allow_autonomous_merge': False,
        },
        notes='Primary monorepo contract for bounded supervised local-first execution.',
    )


def generic_external_python_project_contract(project_id: str = 'generic_python_external', repo_root: str = 'external-app') -> dict[str, object]:
    return canonical_project_contract(
        project_id=project_id,
        display_name='Generic External Python Project',
        repo_root=repo_root,
        workspace_type='external_python',
        allowed_autonomy_lane='supervised_local_first',
        allow_unattended_execution=False,
        workspace_contract=generic_python_workspace_contract(repo_root),
        validation_contract={
            'focused_validation_commands': ['pytest -q'],
            'full_validation_commands': ['ruff check .', 'pytest -q'],
            'acceptance_evidence_commands': ['pytest -q'],
            'verification_authority_profile': 'local_plus_required_ci',
        },
        branch_policy={
            'branch_naming_pattern': f'project/{project_id}/*',
            'default_base_branch': 'main',
            'require_clean_main_reset': True,
            'allow_autonomous_merge': False,
        },
        notes='External Python contract remains bounded and supervised; not unattended-safe.',
    )


def registered_project_contracts() -> list[dict[str, object]]:
    return [
        tradingbot_project_contract('.'),
        generic_external_python_project_contract(),
    ]


def project_registry_snapshot() -> dict[str, object]:
    entries = registered_project_contracts()
    by_id = {str(entry['project_id']): dict(entry) for entry in entries}
    return {
        'deterministic_and_serializable': True,
        'registered_project_ids': list(by_id.keys()),
        'registered_projects': by_id,
        'supported_workspace_types': list(PROJECT_WORKSPACE_TYPES),
        'autonomy_lanes': list(PROJECT_AUTONOMY_LANES),
        'unattended_safe_project_ids': [project_id for project_id, entry in by_id.items() if bool(entry.get('allow_unattended_execution'))],
    }


def resolve_project_contract(project_id: str = 'tradingbot_monorepo') -> dict[str, object]:
    registry = project_registry_snapshot()['registered_projects']
    try:
        return dict(registry[str(project_id)])
    except KeyError as exc:
        raise KeyError(f'Unknown project id: {project_id}') from exc


PROJECT_SCOPE_AMBIGUOUS_ID = 'ambiguous_project'


def project_scope_identity(project_contract: Mapping[str, object] | None = None) -> dict[str, object]:
    payload = dict(project_contract or {})
    project_id = str(payload.get('project_id') or '').strip()
    repo_root = _normalize_repo_root(payload.get('repo_root', '.'))
    workspace_contract = canonical_workspace_contract(payload.get('workspace_contract'))
    workspace_root = _normalize_repo_root(workspace_contract.get('workspace_root', repo_root))
    branch_policy = _normalize_branch_policy(payload.get('branch_policy'), project_id=project_id or PROJECT_SCOPE_AMBIGUOUS_ID)
    ambiguous = not bool(project_id)
    stable_project_id = project_id or PROJECT_SCOPE_AMBIGUOUS_ID
    state_namespace = f'project_state/{stable_project_id}'
    checkpoint_namespace = f'project_checkpoint/{stable_project_id}'
    branch_namespace = f'project/{stable_project_id}'
    return {
        'project_id': stable_project_id,
        'project_identity_ambiguous': ambiguous,
        'project_repo_root': repo_root,
        'project_workspace_root': workspace_root,
        'project_state_namespace': state_namespace,
        'project_checkpoint_namespace': checkpoint_namespace,
        'project_branch_namespace': branch_namespace,
        'default_base_branch': str(branch_policy['default_base_branch']),
        'branch_naming_pattern': str(branch_policy['branch_naming_pattern']),
        'resume_allowed': not ambiguous,
    }


def project_scoped_branch_name(project_contract: Mapping[str, object] | None, branch_slug: str) -> str:
    identity = project_scope_identity(project_contract)
    slug = str(branch_slug or '').strip().strip('/').replace(' ', '-')
    if not slug:
        slug = 'task'
    pattern = str(identity.get('branch_naming_pattern') or '').strip()
    if '*' in pattern:
        branch_core = pattern.replace('*', slug)
    elif pattern:
        branch_core = f"{pattern.rstrip('/')}/{slug}"
    else:
        branch_core = slug
    branch_core = branch_core.replace('//', '/').strip('/')
    return f"{identity['project_branch_namespace']}/{branch_core}"


def project_workspace_metadata(project_contract: Mapping[str, object] | None) -> dict[str, object]:
    identity = project_scope_identity(project_contract)
    return {
        'project_id': str(identity['project_id']),
        'project_identity_ambiguous': bool(identity['project_identity_ambiguous']),
        'project_repo_root': str(identity['project_repo_root']),
        'project_workspace_root': str(identity['project_workspace_root']),
        'project_state_namespace': str(identity['project_state_namespace']),
        'project_checkpoint_namespace': str(identity['project_checkpoint_namespace']),
        'project_branch_namespace': str(identity['project_branch_namespace']),
    }
