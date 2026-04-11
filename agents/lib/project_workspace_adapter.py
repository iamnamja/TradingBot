from __future__ import annotations

from typing import Mapping, Sequence

WORKSPACE_BOOTSTRAP_STATUSES = (
    'not_started',
    'succeeded',
    'blocked',
)
CONSUMER_BRIDGE_REQUIRED_FIELDS = (
    'workspace_root',
    'consumer_name',
    'validation_commands',
    'acceptance_evidence_commands',
    'protected_paths',
)
CONSUMER_BRIDGE_OPTIONAL_FIELDS = (
    'bootstrap_commands',
    'artifact_output_paths',
    'merge_policy_constraints',
    'optional_consumer_policies',
)


def _normalize_str_list(values: Sequence[object] | None) -> list[str]:
    result: list[str] = []
    for value in values or ():
        text = str(value or '').strip()
        if text:
            result.append(text)
    return result


def _normalize_path_list(values: Sequence[object] | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values or ():
        text = str(value or '').strip().replace('\\', '/')
        text = text.lstrip('./') if text not in {'.', './'} else '.'
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _normalize_merge_policy_constraints(value: Mapping[str, object] | None) -> dict[str, object]:
    payload = dict(value or {})
    return {
        'allow_autonomous_merge': bool(payload.get('allow_autonomous_merge', False)),
        'require_clean_main_reset': bool(payload.get('require_clean_main_reset', True)),
        'verification_authority_profile': str(payload.get('verification_authority_profile', 'local_plus_required_ci') or 'local_plus_required_ci'),
        'block_merge_on_missing_required_checks': bool(payload.get('block_merge_on_missing_required_checks', True)),
        'protected_merge_requires_manual_review': bool(payload.get('protected_merge_requires_manual_review', True)),
    }


def canonical_workspace_contract(payload: Mapping[str, object] | None = None, **overrides: object) -> dict[str, object]:
    src = dict(payload or {})
    src.update(overrides)

    workspace_root = str(src.get('workspace_root', '.') or '.').strip() or '.'
    consumer = str(src.get('consumer_name', 'generic_python') or 'generic_python').strip() or 'generic_python'
    contract_name = str(src.get('contract_name', f'{consumer}_workspace') or f'{consumer}_workspace').strip()
    bootstrap_commands = _normalize_str_list(src.get('bootstrap_commands'))
    validation_commands = _normalize_str_list(src.get('validation_commands'))
    acceptance_evidence_commands = _normalize_str_list(src.get('acceptance_evidence_commands'))
    protected_paths = _normalize_path_list(src.get('protected_paths'))
    artifact_output_paths = _normalize_path_list(src.get('artifact_output_paths'))
    optional_consumer_policies = _normalize_str_list(src.get('optional_consumer_policies'))
    merge_policy_constraints = _normalize_merge_policy_constraints(src.get('merge_policy_constraints'))

    return {
        'workspace_root': workspace_root,
        'consumer_name': consumer,
        'contract_name': contract_name,
        'python_first_scope_only': True,
        'bootstrap_commands': bootstrap_commands,
        'validation_commands': validation_commands,
        'acceptance_evidence_commands': acceptance_evidence_commands,
        'protected_paths': protected_paths,
        'artifact_output_paths': artifact_output_paths,
        'optional_consumer_policies': optional_consumer_policies,
        'merge_policy_constraints': merge_policy_constraints,
    }


def generic_python_workspace_contract(workspace_root: str = '.') -> dict[str, object]:
    return canonical_workspace_contract(
        workspace_root=workspace_root,
        consumer_name='generic_python',
        contract_name='generic_python_workspace',
        bootstrap_commands=['python -m pip install -r requirements.txt'],
        validation_commands=['ruff check .', 'pytest -q'],
        acceptance_evidence_commands=['pytest -q'],
        protected_paths=['.github/workflows', 'docs', 'tasks'],
        artifact_output_paths=['artifacts', 'dist', 'build'],
        optional_consumer_policies=[],
        merge_policy_constraints={
            'allow_autonomous_merge': True,
            'require_clean_main_reset': True,
            'verification_authority_profile': 'local_plus_required_ci',
            'block_merge_on_missing_required_checks': True,
            'protected_merge_requires_manual_review': True,
        },
    )


def tradingbot_workspace_contract(workspace_root: str = '.') -> dict[str, object]:
    return canonical_workspace_contract(
        workspace_root=workspace_root,
        consumer_name='tradingbot',
        contract_name='tradingbot_workspace',
        bootstrap_commands=['python -m pip install -r requirements.txt'],
        validation_commands=['ruff check .', 'pytest -q'],
        acceptance_evidence_commands=['pytest -q tests/test_run_task_runtime_foundations.py'],
        protected_paths=['agents', 'docs', 'tasks', 'src/tradingbot', 'src/builder/orchestrator'],
        artifact_output_paths=['artifacts', 'tasks/state.json', '_last_agent_model_output.txt', '_last_agent_file_bundle.txt', '_last_agent_file_bundle_error.txt', '_last_subset_preservation.json'],
        optional_consumer_policies=['tradingbot_domain_runtime', 'tradingbot_consumer_policy'],
        merge_policy_constraints={
            'allow_autonomous_merge': True,
            'require_clean_main_reset': True,
            'verification_authority_profile': 'local_plus_required_ci',
            'block_merge_on_missing_required_checks': True,
            'protected_merge_requires_manual_review': True,
        },
    )


def canonical_workspace_bootstrap_truth(payload: Mapping[str, object] | None = None, **overrides: object) -> dict[str, object]:
    src = dict(payload or {})
    src.update(overrides)
    contract = canonical_workspace_contract(src)

    bootstrap_attempted = bool(src.get('bootstrap_attempted', False))
    bootstrap_succeeded = bool(src.get('bootstrap_succeeded', False))
    bootstrap_blocked = bool(src.get('bootstrap_blocked', False))
    bootstrap_error = str(src.get('bootstrap_error', '') or '').strip()
    bootstrap_status = str(src.get('bootstrap_status', '') or '').strip()

    if bootstrap_succeeded:
        bootstrap_status = 'succeeded'
        bootstrap_blocked = False
    elif bootstrap_blocked or bootstrap_error:
        bootstrap_status = 'blocked'
        bootstrap_blocked = True
        bootstrap_succeeded = False
    elif bootstrap_attempted:
        bootstrap_status = 'not_started'
        bootstrap_succeeded = False
    else:
        bootstrap_status = 'not_started'

    if bootstrap_status not in WORKSPACE_BOOTSTRAP_STATUSES:
        bootstrap_status = 'blocked' if bootstrap_error else 'not_started'

    return {
        **contract,
        'bootstrap_attempted': bootstrap_attempted,
        'bootstrap_succeeded': bootstrap_succeeded,
        'bootstrap_blocked': bootstrap_blocked,
        'bootstrap_status': bootstrap_status,
        'bootstrap_error': bootstrap_error,
        'resume_safe_after_bootstrap_failure': bool(bootstrap_blocked),
        'workspace_ready_for_validation': bool(bootstrap_succeeded and not bootstrap_blocked),
    }


def evaluate_workspace_bootstrap_result(contract: Mapping[str, object] | None, *, bootstrap_ok: bool, bootstrap_error: str = '') -> dict[str, object]:
    return canonical_workspace_bootstrap_truth(
        contract,
        bootstrap_attempted=True,
        bootstrap_succeeded=bootstrap_ok,
        bootstrap_blocked=(not bootstrap_ok),
        bootstrap_error=bootstrap_error,
    )



def recover_workspace_bootstrap_truth(
    truth: Mapping[str, object] | None,
    *,
    bootstrap_ok: bool,
    bootstrap_error: str = '',
) -> dict[str, object]:
    previous = canonical_workspace_bootstrap_truth(truth)
    recovered = evaluate_workspace_bootstrap_result(previous, bootstrap_ok=bootstrap_ok, bootstrap_error=bootstrap_error)
    return {
        **recovered,
        'previous_bootstrap_status': str(previous.get('bootstrap_status') or 'not_started'),
        'recovery_attempted': True,
        'resumed_from_bootstrap_blocked_state': bool(previous.get('bootstrap_status') == 'blocked'),
        'bootstrap_recovered': bool(previous.get('bootstrap_status') == 'blocked' and recovered.get('bootstrap_status') == 'succeeded'),
    }


def bootstrap_recovery_proof_snapshot() -> dict[str, object]:
    return {
        'python_first_scope_only': True,
        'bootstrap_statuses': list(WORKSPACE_BOOTSTRAP_STATUSES),
        'recovery_proof_scope': 'simple_external_python_workspace',
        'supports_truthful_blocked_then_recovered_state': True,
    }

def workspace_validation_commands(contract: Mapping[str, object] | None) -> list[str]:
    return canonical_workspace_contract(contract).get('validation_commands', [])  # type: ignore[return-value]


def workspace_acceptance_evidence_commands(contract: Mapping[str, object] | None) -> list[str]:
    return canonical_workspace_contract(contract).get('acceptance_evidence_commands', [])  # type: ignore[return-value]


def workspace_can_resume_after_bootstrap_failure(truth: Mapping[str, object] | None) -> bool:
    payload = canonical_workspace_bootstrap_truth(truth)
    return bool(payload['resume_safe_after_bootstrap_failure'])


def workspace_adapter_snapshot() -> dict[str, object]:
    return {
        'python_first_scope_only': True,
        'supported_consumers': ['tradingbot', 'generic_python'],
        'workspace_contracts': {
            'tradingbot': tradingbot_workspace_contract('.'),
            'generic_python': generic_python_workspace_contract('.'),
        },
    }


def consumer_bridge_contract(contract: Mapping[str, object] | None = None) -> dict[str, object]:
    payload = canonical_workspace_contract(contract)
    return {
        'workspace_root': str(payload['workspace_root']),
        'consumer_name': str(payload['consumer_name']),
        'validation_commands': list(payload['validation_commands']),
        'acceptance_evidence_commands': list(payload['acceptance_evidence_commands']),
        'protected_paths': list(payload['protected_paths']),
        'bootstrap_commands': list(payload['bootstrap_commands']),
        'artifact_output_paths': list(payload['artifact_output_paths']),
        'merge_policy_constraints': dict(payload['merge_policy_constraints']),
        'optional_consumer_policies': list(payload.get('optional_consumer_policies', [])),
        'required_bridge_fields': list(CONSUMER_BRIDGE_REQUIRED_FIELDS),
        'optional_bridge_fields': list(CONSUMER_BRIDGE_OPTIONAL_FIELDS),
        'full_standalone_extraction_completed': False,
    }


def consumer_bridge_snapshot() -> dict[str, object]:
    return {
        'supported_consumers': ['tradingbot', 'generic_python'],
        'required_bridge_fields': list(CONSUMER_BRIDGE_REQUIRED_FIELDS),
        'optional_bridge_fields': list(CONSUMER_BRIDGE_OPTIONAL_FIELDS),
        'full_standalone_extraction_completed': False,
        'tradingbot': consumer_bridge_contract(tradingbot_workspace_contract('.')),
        'generic_python': consumer_bridge_contract(generic_python_workspace_contract('.')),
    }


def orchestrator_package_boundary_snapshot() -> dict[str, object]:
    from agents.lib.multi_agent_contract import orchestrator_package_boundary_snapshot as _impl

    return dict(_impl())


def workspace_contract_from_project_contract(project_contract: Mapping[str, object] | None) -> dict[str, object]:
    payload = dict(project_contract or {})
    return canonical_workspace_contract(payload.get('workspace_contract'))


def project_validation_contract(project_contract: Mapping[str, object] | None) -> dict[str, object]:
    payload = dict(project_contract or {})
    validation = dict(payload.get('validation_contract') or {})
    workspace = workspace_contract_from_project_contract(payload)
    focused = _normalize_str_list(validation.get('focused_validation_commands'))
    full_commands = _normalize_str_list(validation.get('full_validation_commands')) or list(workspace.get('validation_commands', []))
    acceptance = _normalize_str_list(validation.get('acceptance_evidence_commands')) or list(workspace.get('acceptance_evidence_commands', []))
    authority = str(
        validation.get('verification_authority_profile')
        or workspace.get('merge_policy_constraints', {}).get('verification_authority_profile', 'local_plus_required_ci')
    ).strip() or 'local_plus_required_ci'
    if not focused:
        focused = [full_commands[-1]] if full_commands else []
    return {
        'focused_validation_commands': focused,
        'full_validation_commands': full_commands,
        'acceptance_evidence_commands': acceptance,
        'verification_authority_profile': authority,
    }
