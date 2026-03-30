from builder import orchestrator


def test_orchestrator_package_surface_exports_expected_symbols():
    expected_exports = {
        "ProjectConfig",
        "GenericProjectConfig",
        "load_project_config",
        "bootstrap_project_config_scaffold",
        "ProjectAdapter",
        "load_project_adapter",
        "bootstrap_project_adapter_scaffold",
        "build_bootstrap_starter_docs_text",
        "build_bootstrap_task_template_text",
    }

    package_all = set(orchestrator.__all__)
    assert expected_exports == package_all

    for symbol in expected_exports:
        assert hasattr(orchestrator, symbol)


def test_orchestrator_package_surface_does_not_export_tradingbot_symbols():
    disallowed_exports = {
        "run_paper_cycle",
        "RiskGate",
        "StrategyV1",
        "AlpacaBroker",
    }

    package_all = set(orchestrator.__all__)
    assert package_all.isdisjoint(disallowed_exports)
