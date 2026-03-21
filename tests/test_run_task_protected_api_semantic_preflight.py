import importlib.util
from pathlib import Path
import sys



def _load_run_task_module():
    module_path = Path("agents") / "run_task.py"
    spec = importlib.util.spec_from_file_location("agents.run_task", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


run_task = _load_run_task_module()


def _patch_semantic_helpers(monkeypatch):
    def fake_module_source_for_name(module_name, bundle=None):
        if module_name == "builder.orchestrator.runner":
            return (
                "class OrchestratorRunner:\n"
                "    def __init__(self, config, backlog_tracker, initial_state):\n"
                "        self.config = config.config if hasattr(config, \"config\") else config\n\n"
                "    def run_next_task(self):\n"
                "        return None\n\n"
                "    def run_loop(self):\n"
                "        return None\n"
            )
        if module_name == "builder.orchestrator.project_config":
            return "class ProjectConfig:\n    pass\n"
        return None

    def fake_class_methods_from_source(source, class_name):
        if class_name == "OrchestratorRunner":
            return {"__init__", "run_next_task", "run_loop"}
        if class_name == "ProjectConfig":
            return set()
        return set()

    def fake_class_init_arity_from_source(source, class_name):
        if class_name == "OrchestratorRunner":
            return (3, 3)
        if class_name == "ProjectConfig":
            return (0, 0)
        return None

    monkeypatch.setattr(run_task, "_module_source_for_name", fake_module_source_for_name)
    monkeypatch.setattr(run_task, "_class_methods_from_source", fake_class_methods_from_source)
    monkeypatch.setattr(run_task, "_class_init_arity_from_source", fake_class_init_arity_from_source)


def test_valid_protected_constructor_usage_passes(monkeypatch):
    _patch_semantic_helpers(monkeypatch)
    bundle = {
        "tests/test_generated_semantic_contract.py": (
            "from builder.orchestrator.project_config import ProjectConfig\n"
            "from builder.orchestrator.runner import OrchestratorRunner\n\n"
            "config = ProjectConfig()\n"
            "runner = OrchestratorRunner(config, object(), object())\n"
            "runner.run_next_task()\n"
            "runner.run_loop()\n"
        )
    }

    ok, message = run_task.validate_static_bundle_contracts(bundle, "protected preflight")
    assert ok is True
    assert message == ""


def test_zero_arg_orchestrator_runner_is_rejected(monkeypatch):
    _patch_semantic_helpers(monkeypatch)
    bundle = {
        "tests/test_generated_semantic_contract.py": (
            "from builder.orchestrator.runner import OrchestratorRunner\n\n"
            "runner = OrchestratorRunner()\n"
        )
    }

    ok, message = run_task.validate_static_bundle_contracts(bundle, "protected preflight")
    assert ok is False
    assert "OrchestratorRunner() is called with 0 args" in message


def test_missing_protected_method_call_is_rejected(monkeypatch):
    _patch_semantic_helpers(monkeypatch)
    bundle = {
        "tests/test_generated_semantic_contract.py": (
            "from builder.orchestrator.project_config import ProjectConfig\n"
            "from builder.orchestrator.runner import OrchestratorRunner\n\n"
            "config = ProjectConfig()\n"
            "runner = OrchestratorRunner(config, object(), object())\n"
            "runner.run_all_tasks()\n"
        )
    }

    ok, message = run_task.validate_static_bundle_contracts(bundle, "protected preflight")
    assert ok is False
    assert "has no method 'run_all_tasks'" in message


def test_missing_protected_import_symbol_is_rejected(monkeypatch):
    _patch_semantic_helpers(monkeypatch)
    bundle = {
        "tests/test_generated_semantic_contract.py": (
            "from builder.orchestrator.runner import MissingSymbol\n"
        )
    }

    ok, message = run_task.validate_static_bundle_contracts(bundle, "protected preflight")
    assert ok is False
    assert "imports missing symbol" in message


def test_bare_simple_namespace_first_arg_is_rejected(monkeypatch):
    _patch_semantic_helpers(monkeypatch)
    bundle = {
        "tests/test_generated_semantic_contract.py": (
            "from types import SimpleNamespace\n"
            "from builder.orchestrator.runner import OrchestratorRunner\n\n"
            "runner = OrchestratorRunner(SimpleNamespace(), object(), object())\n"
        )
    }

    ok, message = run_task.validate_static_bundle_contracts(bundle, "protected preflight")
    assert ok is False
    assert "first arg must be ProjectConfig or object with .config" in message


def test_non_protected_modules_are_ignored_by_validator(monkeypatch):
    _patch_semantic_helpers(monkeypatch)
    bundle = {
        "tests/test_generated_semantic_contract.py": (
            "from types import SimpleNamespace\n\n"
            "value = SimpleNamespace(answer=42)\n"
        )
    }

    ok, message = run_task.validate_static_bundle_contracts(bundle, "protected preflight")
    assert ok is True
    assert message == ""
