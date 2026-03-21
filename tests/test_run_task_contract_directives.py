import importlib.util
from pathlib import Path


def _load_run_task_module():
    module_path = Path("agents/run_task.py")
    spec = importlib.util.spec_from_file_location("agents.run_task", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_task = _load_run_task_module()


def test_parse_task_contract_directives_parses_constructor_and_forbidden_items():
    task_text = """
## Machine-readable contract directives

- CONSTRUCTOR: builder.orchestrator.runner.OrchestratorRunner(config, backlog_tracker, initial_state)
- CONFIG_WRAPPER: builder.orchestrator.runner.OrchestratorRunner first_arg_requires=.config unless=ProjectConfig
- ALLOWED_METHODS: builder.orchestrator.runner.OrchestratorRunner run_next_task run_loop
- FORBID_IMPORTS: builder.orchestrator.backlog BacklogTask BacklogItem BacklogStore TaskRecord
- FORBID_CALLS: runner.run runner.run_all_tasks
- RESULT_KEYS: run_loop processed_tasks stopped_reason final_status approval_required planned_actions
""".strip()

    directives = run_task.parse_task_contract_directives(task_text)

    assert directives["CONSTRUCTOR"] == [
        "builder.orchestrator.runner.OrchestratorRunner(config, backlog_tracker, initial_state)"
    ]
    assert directives["CONFIG_WRAPPER"] == [
        "builder.orchestrator.runner.OrchestratorRunner first_arg_requires=.config unless=ProjectConfig"
    ]
    assert directives["ALLOWED_METHODS"] == [
        "builder.orchestrator.runner.OrchestratorRunner run_next_task run_loop"
    ]
    assert directives["FORBID_IMPORTS"] == [
        "builder.orchestrator.backlog BacklogTask BacklogItem BacklogStore TaskRecord"
    ]
    assert directives["FORBID_CALLS"] == ["runner.run runner.run_all_tasks"]
    assert directives["RESULT_KEYS"] == [
        "run_loop processed_tasks stopped_reason final_status approval_required planned_actions"
    ]


def test_validate_static_bundle_contracts_enforces_forbid_imports_and_forbid_calls(monkeypatch):
    task_text = """
## Machine-readable contract directives

- FORBID_IMPORTS: builder.orchestrator.backlog BacklogTask BacklogItem BacklogStore TaskRecord
- FORBID_CALLS: runner.run runner.run_all_tasks
""".strip()

    bundle = {
        "tests/test_generated_contract_directives.py": (
            "from builder.orchestrator.backlog import BacklogTask\n"
            "\n"
            "def test_runner():\n"
            "    runner.run_all_tasks()\n"
        )
    }

    monkeypatch.setattr(run_task, "_module_source_for_name", lambda name: "")
    monkeypatch.setattr(run_task, "_class_methods_from_source", lambda source, class_name: [])
    monkeypatch.setattr(run_task, "_class_init_arity_from_source", lambda source, class_name: None)

    ok, message = run_task.validate_static_bundle_contracts(bundle, task_text)

    assert ok is False
    assert "violates FORBID_IMPORTS" in message or "violates FORBID_CALLS" in message


def test_validate_static_bundle_contracts_enforces_config_wrapper(monkeypatch):
    task_text = """
## Machine-readable contract directives

- CONSTRUCTOR: builder.orchestrator.runner.OrchestratorRunner(config, backlog_tracker, initial_state)
- CONFIG_WRAPPER: builder.orchestrator.runner.OrchestratorRunner first_arg_requires=.config unless=ProjectConfig
""".strip()

    bundle = {
        "tests/test_generated_contract_directives.py": (
            "from types import SimpleNamespace\n"
            "from builder.orchestrator.runner import OrchestratorRunner\n"
            "\n"
            "runner = OrchestratorRunner(SimpleNamespace(), object(), object())\n"
        )
    }

    monkeypatch.setattr(run_task, "_module_source_for_name", lambda name: "")
    monkeypatch.setattr(run_task, "_class_methods_from_source", lambda source, class_name: [])
    monkeypatch.setattr(run_task, "_class_init_arity_from_source", lambda source, class_name: 3)

    ok, message = run_task.validate_static_bundle_contracts(bundle, task_text)

    assert ok is False
    assert "must satisfy CONFIG_WRAPPER" in message


def test_validate_static_bundle_contracts_enforces_result_keys(monkeypatch):
    task_text = """
## Machine-readable contract directives

- RESULT_KEYS: run_loop processed_tasks stopped_reason final_status approval_required planned_actions
""".strip()

    bundle = {
        "tests/test_generated_contract_directives.py": (
            "def some_test():\n"
            "    run_loop_result = run_loop()\n"
            '    assert "processed_tasks" in run_loop_result\n'
        )
    }

    monkeypatch.setattr(run_task, "_module_source_for_name", lambda name: "")
    monkeypatch.setattr(run_task, "_class_methods_from_source", lambda source, class_name: [])
    monkeypatch.setattr(run_task, "_class_init_arity_from_source", lambda source, class_name: None)

    ok, message = run_task.validate_static_bundle_contracts(bundle, task_text)

    assert ok is False
    assert "missing RESULT_KEYS contract token" in message


def test_validate_static_bundle_contracts_allows_no_directives(monkeypatch):
    task_text = """
## Regular task

No machine-readable directives are present here.
""".strip()

    bundle = {
        "tests/test_generated_contract_directives.py": (
            "def some_test():\n"
            "    assert 1 + 1 == 2\n"
        )
    }

    monkeypatch.setattr(run_task, "_module_source_for_name", lambda name: "")
    monkeypatch.setattr(run_task, "_class_methods_from_source", lambda source, class_name: [])
    monkeypatch.setattr(run_task, "_class_init_arity_from_source", lambda source, class_name: None)

    directives = run_task.parse_task_contract_directives(task_text)
    ok, message = run_task.validate_static_bundle_contracts(bundle, task_text)

    assert directives == {}
    assert ok is True
    assert message == ""
