import textwrap

from agents import run_task
from agents.lib import semantic_preflight


def _bundle(content: str) -> dict[str, str]:
    return {"tests/test_generated_semantic_contract.py": textwrap.dedent(content).lstrip("\n")}


def test_valid_protected_constructor_usage() -> None:
    runner_src = """
class OrchestratorRunner:
    def __init__(self, config, a, b):
        _ = config.config
    def run_next_task(self):
        return None
    def run_loop(self):
        return None
"""
    project_config_src = """
class ProjectConfig:
    pass
"""
    bundle = _bundle(
        """
from builder.orchestrator.project_config import ProjectConfig
from builder.orchestrator.runner import OrchestratorRunner
config = ProjectConfig()
runner = OrchestratorRunner(config, object(), object())
runner.run_next_task()
runner.run_loop()
"""
    )
    bundle["src/builder/orchestrator/runner.py"] = textwrap.dedent(runner_src).lstrip("\n")
    bundle["src/builder/orchestrator/project_config.py"] = textwrap.dedent(project_config_src).lstrip("\n")

    issues = semantic_preflight._protected_python_semantic_issues(bundle, "")
    assert issues == []


def test_zero_arg_constructor_rejection() -> None:
    runner_src = """
class OrchestratorRunner:
    def __init__(self, config):
        self.config = config
"""
    bundle = _bundle(
        """
from builder.orchestrator.runner import OrchestratorRunner
runner = OrchestratorRunner()
"""
    )
    bundle["src/builder/orchestrator/runner.py"] = textwrap.dedent(runner_src).lstrip("\n")
    issues = semantic_preflight._protected_python_semantic_issues(bundle, "")
    assert any("called with 0 args" in x for x in issues)


def test_missing_protected_method_call_rejection() -> None:
    runner_src = """
class OrchestratorRunner:
    def __init__(self, config):
        self.config = config
    def run_next_task(self):
        return None
"""
    bundle = _bundle(
        """
from builder.orchestrator.runner import OrchestratorRunner
runner = OrchestratorRunner(object())
runner.run_loop()
"""
    )
    bundle["src/builder/orchestrator/runner.py"] = textwrap.dedent(runner_src).lstrip("\n")
    issues = semantic_preflight._protected_python_semantic_issues(bundle, "")
    assert any("protected API has no method 'run_loop'" in x for x in issues)


def test_missing_protected_import_symbol_rejection(monkeypatch) -> None:
    monkeypatch.setattr(semantic_preflight, "_module_source_for_name", lambda mod, bundle: "class X:\n    pass\n" if mod == "builder.orchestrator.runner" else None)
    monkeypatch.setattr(semantic_preflight, "_module_exports_from_source", lambda src: {"OrchestratorRunner"})
    issues = semantic_preflight._protected_python_semantic_issues(
        _bundle(
            """
from builder.orchestrator.runner import MissingSymbol
"""
        ),
        "",
    )
    assert any("imports missing symbol 'MissingSymbol'" in x for x in issues)


def test_config_wrapper_misuse_rejection(monkeypatch) -> None:
    runner_src = """
class OrchestratorRunner:
    def __init__(self, cfg):
        _ = cfg.config
    def run_next_task(self):
        return None
"""
    monkeypatch.setattr(semantic_preflight, "_module_source_for_name", lambda mod, bundle: runner_src if mod == "builder.orchestrator.runner" else None)
    issues = semantic_preflight._protected_python_semantic_issues(
        _bundle(
            """
from types import SimpleNamespace
from builder.orchestrator.runner import OrchestratorRunner
cfg = SimpleNamespace()
runner = OrchestratorRunner(cfg)
"""
        ),
        "",
    )
    assert any("first arg must be ProjectConfig or object with .config" in x for x in issues)


def test_non_protected_code_ignored() -> None:
    issues = semantic_preflight._protected_python_semantic_issues(
        _bundle(
            """
class LocalRunner:
    def run(self):
        return 1
x = LocalRunner()
x.run()
"""
        ),
        "",
    )
    assert issues == []


def test_monkeypatch_shape_compatibility_for_exports(monkeypatch) -> None:
    monkeypatch.setattr(
        run_task,
        "_semantic_preflight_exports",
        lambda: {
            "_module_source_for_name": lambda mod, bundle: "S",
            "_module_exports_from_source": lambda src: {"E"},
            "_class_methods_from_source": lambda src, cls: {"m"},
            "_class_init_arity_from_source": lambda src, cls: (1, 1),
            "_protected_python_semantic_issues": lambda bundle, task_text: ["I"],
            "validate_static_bundle_contracts": lambda bundle, task_text: (False, "X"),
        },
    )
    assert run_task._module_source_for_name("a.b", {}) == "S"
    assert run_task._module_exports_from_source("src") == {"E"}
    assert run_task._class_methods_from_source("src", "C") == {"m"}
    assert run_task._class_init_arity_from_source("src", "C") == (1, 1)
    assert run_task._protected_python_semantic_issues({}, "") == ["I"]
    assert run_task.validate_static_bundle_contracts({}, "") == (False, "X")
