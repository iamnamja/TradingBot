from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from agents.lib.public_compat import compatibility_contract_snapshot, normalize_project_contract_payload
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
PROJECT_AUTHORITY_PROFILES = (
    'local_only',
    'local_plus_required_ci',
    'required_ci_only',
)
VALIDATION_SCOPES = (
    'focused',
    'full',
    'acceptance',
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
    seen: set[str] = set()
    for value in values or ():
        text = str(value or '').strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
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
    bootstrap_commands = _normalize_str_list(src.get('bootstrap_commands')) or list(workspace_contract.get('bootstrap_commands', []))
    verification_authority_profile = str(
        src.get('verification_authority_profile')
        or workspace_contract.get('merge_policy_constraints', {}).get('verification_authority_profile', 'local_plus_required_ci')
    ).strip() or 'local_plus_required_ci'
    if verification_authority_profile not in PROJECT_AUTHORITY_PROFILES:
        verification_authority_profile = 'local_plus_required_ci'
    repo_required_checks = _normalize_str_list(src.get('repo_required_checks'))
    repo_check_contract_source = str(src.get('repo_check_contract_source') or 'project_registry').strip() or 'project_registry'
    hosted_checks_source = str(src.get('hosted_checks_source') or 'gh_pr_checks').strip() or 'gh_pr_checks'
    bootstrap_required = bool(src.get('bootstrap_required', bool(bootstrap_commands)))
    return {
        'focused_validation_commands': focused_commands,
        'full_validation_commands': full_commands,
        'acceptance_evidence_commands': acceptance_commands,
        'bootstrap_required': bootstrap_required,
        'bootstrap_commands': bootstrap_commands,
        'verification_authority_profile': verification_authority_profile,
        'repo_required_checks': repo_required_checks,
        'repo_check_contract_source': repo_check_contract_source,
        'hosted_checks_source': hosted_checks_source,
        'validation_matrix_serializable': True,
    }


def project_validation_matrix(project_contract: Mapping[str, object] | None = None) -> dict[str, object]:
    contract = canonical_project_contract(project_contract)
    matrix = dict(contract.get('validation_contract') or {})
    return {
        'project_id': str(contract['project_id']),
        'focused_validation_commands': list(matrix.get('focused_validation_commands', [])),
        'full_validation_commands': list(matrix.get('full_validation_commands', [])),
        'acceptance_evidence_commands': list(matrix.get('acceptance_evidence_commands', [])),
        'bootstrap_required': bool(matrix.get('bootstrap_required', False)),
        'bootstrap_commands': list(matrix.get('bootstrap_commands', [])),
        'verification_authority_profile': str(matrix.get('verification_authority_profile') or 'local_plus_required_ci'),
        'repo_required_checks': list(matrix.get('repo_required_checks', [])),
        'repo_check_contract_source': str(matrix.get('repo_check_contract_source') or 'project_registry'),
        'hosted_checks_source': str(matrix.get('hosted_checks_source') or 'gh_pr_checks'),
        'validation_matrix_serializable': bool(matrix.get('validation_matrix_serializable', True)),
    }


def resolve_project_validation_plan(project_id: str = 'tradingbot_monorepo', *, validation_scope: str = 'full') -> dict[str, object]:
    contract = resolve_project_contract(project_id)
    matrix = project_validation_matrix(contract)
    scope = str(validation_scope or 'full').strip().lower()
    if scope not in VALIDATION_SCOPES:
        scope = 'full'
    if scope == 'focused':
        commands = list(matrix['focused_validation_commands'])
    elif scope == 'acceptance':
        commands = list(matrix['acceptance_evidence_commands'])
    else:
        scope = 'full'
        commands = list(matrix['full_validation_commands'])
    return {
        'project_id': str(matrix['project_id']),
        'validation_scope': scope,
        'commands': commands,
        'bootstrap_required': bool(matrix['bootstrap_required']),
        'bootstrap_commands': list(matrix['bootstrap_commands']),
        'verification_authority_profile': str(matrix['verification_authority_profile']),
        'repo_required_checks': list(matrix['repo_required_checks']),
        'repo_check_contract_source': str(matrix['repo_check_contract_source']),
        'hosted_checks_source': str(matrix['hosted_checks_source']),
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
            'bootstrap_required': False,
            'bootstrap_commands': [],
            'verification_authority_profile': 'local_plus_required_ci',
            'repo_required_checks': ['ci-required'],
            'repo_check_contract_source': 'project_registry',
            'hosted_checks_source': 'gh_pr_checks',
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
            'bootstrap_required': True,
            'bootstrap_commands': ['python -m pip install -r requirements.txt'],
            'verification_authority_profile': 'local_only',
            'repo_required_checks': [],
            'repo_check_contract_source': 'project_registry',
            'hosted_checks_source': 'gh_pr_checks',
        },
        branch_policy={
            'branch_naming_pattern': f'project/{project_id}/*',
            'default_base_branch': 'main',
            'require_clean_main_reset': True,
            'allow_autonomous_merge': False,
        },
        notes='External Python contract remains bounded and supervised; hosted authority is weaker than local evidence for this project profile.',
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
        'compatibility_contract': compatibility_contract_snapshot(),
        'portfolio_scheduler_mode': 'supervised_local_first',
        'portfolio_slice_bounded': True,
        'portfolio_reproof_claim': 'deterministic_local_supervised_only',
        'registered_project_ids': list(by_id.keys()),
        'registered_projects': by_id,
        'supported_workspace_types': list(PROJECT_WORKSPACE_TYPES),
        'autonomy_lanes': list(PROJECT_AUTONOMY_LANES),
        'supported_authority_profiles': list(PROJECT_AUTHORITY_PROFILES),
        'unattended_safe_project_ids': [project_id for project_id, entry in by_id.items() if bool(entry.get('allow_unattended_execution'))],
        'validation_matrix_by_project': {project_id: project_validation_matrix(entry) for project_id, entry in by_id.items()},
        'merge_eligibility_by_project': {project_id: project_merge_eligibility_contract(entry) for project_id, entry in by_id.items()},
        'schema_alias_normalization_enabled': bool(compatibility_contract_snapshot().get('schema_alias_normalization_enabled', False)),
    }


def project_merge_eligibility_contract(project_contract: Mapping[str, object] | None = None) -> dict[str, object]:
    contract = canonical_project_contract(project_contract)
    matrix = project_validation_matrix(contract)
    hosted_required = str(matrix['verification_authority_profile']) != 'local_only'
    return {
        'project_id': str(matrix['project_id']),
        'verification_authority_profile': str(matrix['verification_authority_profile']),
        'repo_required_checks': list(matrix['repo_required_checks']),
        'repo_check_contract_source': str(matrix['repo_check_contract_source']),
        'hosted_checks_source': str(matrix['hosted_checks_source']),
        'merge_requires_hosted_authority': hosted_required,
        'missing_required_checks_blocks_merge': hosted_required and bool(matrix['repo_required_checks']),
        'allow_unattended_execution': bool(contract.get('allow_unattended_execution', False)),
        'merge_contract_serializable': True,
    }


def resolve_project_contract(project_id: str = 'tradingbot_monorepo') -> dict[str, object]:
    registry = project_registry_snapshot()['registered_projects']
    try:
        contract = dict(registry[str(project_id)])
    except KeyError as exc:
        raise KeyError(f'Unknown project id: {project_id}') from exc

    identity = project_scope_identity(contract)
    workspace_contract = canonical_workspace_contract(contract.get('workspace_contract'))
    workspace_root = _normalize_repo_root(
        workspace_contract.get('workspace_root') or identity['project_workspace_root'] or contract.get('repo_root', '.')
    )
    contract = normalize_project_contract_payload(
        contract,
        workspace_root=workspace_root,
        branch_namespace=str(identity['project_branch_namespace']),
        state_namespace=str(identity['project_state_namespace']),
        checkpoint_namespace=str(identity['project_checkpoint_namespace']),
        carry_forward_memory_namespace=f"carry_forward/{identity['project_id']}",
        project_workspace_root=workspace_root,
        project_repo_root=str(identity['project_repo_root']),
        project_branch_namespace=str(identity['project_branch_namespace']),
        project_state_namespace=str(identity['project_state_namespace']),
        project_checkpoint_namespace=str(identity['project_checkpoint_namespace']),
    )
    return contract


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


def project_backlog_selection_contract(project_contract: Mapping[str, object] | None = None) -> dict[str, object]:
    contract = canonical_project_contract(project_contract)
    validation_contract = dict(contract.get('validation_contract') or {})
    return {
        'project_id': str(contract['project_id']),
        'allowed_autonomy_lane': str(contract['allowed_autonomy_lane']),
        'verification_authority_profile': str(validation_contract.get('verification_authority_profile') or 'local_plus_required_ci'),
        'supports_priority_ranking': True,
        'supports_readiness_gating': True,
        'supports_blocked_state_gating': True,
        'supports_carry_forward_memory_input': True,
        'supported_authority_prerequisites': ['none', 'hosted'],
        'hosted_authority_ready_default': False,
    }

def project_repo_check_contract(project_contract: Mapping[str, object]) -> dict[str, object]:
    matrix = project_validation_matrix(project_contract)
    required_checks = list(matrix.get("repo_required_checks", []) or [])

    return {
        "required_checks": required_checks,
        "repo_check_contract_source": str(project_contract.get("project_id", "") or "project_registry"),
    }
