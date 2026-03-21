from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Callable, Dict, List, Tuple

RUNNER_METHOD_HEADER_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
CONTRACT_DIRECTIVE_RE = re.compile(r"^\s*-\s*(CONSTRUCTOR|CONFIG_WRAPPER|ALLOWED_METHODS|FORBID_IMPORTS|FORBID_CALLS|RESULT_KEYS):\s*(.+)$")


def normalize_newlines(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"^\ufeff", "", s)


def parse_required_runner_methods(task_text: str) -> List[str]:
    lower = normalize_newlines(task_text).lower()
    methods: List[str] = []
    for method in [
        "select_next_task",
        "run_next_task",
        "execute_task",
        "process_execution_result",
        "simulate_backlog",
        "translate_to_orchestrator_behavior",
    ]:
        if method in lower:
            methods.append(method)

    seen = set()
    out: List[str] = []
    for method in methods:
        if method not in seen:
            out.append(method)
            seen.add(method)
    return out


def _iter_markdown_sections(task_text: str) -> List[Tuple[str, List[str]]]:
    text = normalize_newlines(task_text)
    lines = text.split("\n")
    sections: List[Tuple[str, List[str]]] = []
    current_name = ""
    current_lines: List[str] = []
    for line in lines:
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*$", line)
        if heading:
            sections.append((current_name, current_lines))
            current_name = heading.group(1).strip().lower()
            current_lines = []
        else:
            current_lines.append(line)
    sections.append((current_name, current_lines))
    return sections


def parse_task_contract_directives(task_text: str) -> Dict[str, List[str]]:
    directives: Dict[str, List[str]] = {}
    allowed_sections = {"", "machine-readable contract directives", "critical", "current runner baseline — must match exactly"}
    for section_name, section_lines in _iter_markdown_sections(task_text):
        if section_name not in allowed_sections and "contract" not in section_name:
            continue
        for raw_line in section_lines:
            m = CONTRACT_DIRECTIVE_RE.match(raw_line)
            if not m:
                continue
            key = m.group(1).strip().upper()
            value = m.group(2).strip()
            directives.setdefault(key, []).append(value)
    return directives


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _is_simplenamespace_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and ((_call_name(node.func) or "").endswith("SimpleNamespace"))


def _result_keys_contract_applies(rel: str, tree: ast.AST, result_fn: str) -> bool:
    p = Path(rel)
    if p.stem == result_fn:
        return True
    if p.name == "__init__.py" and p.parent.name == result_fn:
        return True
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == result_fn:
            return True
    return False


def _module_source_for_name(mod: str, bundle: Dict[str, str]) -> str | None:
    mod = mod.strip()
    if mod.startswith("src."):
        mod = mod[4:]
    parts = mod.split(".")
    if len(parts) < 2:
        return None
    file_rel = (Path("src") / Path(*parts)).with_suffix(".py").as_posix()
    pkg_rel = (Path("src") / Path(*parts) / "__init__.py").as_posix()
    if file_rel in bundle:
        return bundle[file_rel]
    if pkg_rel in bundle:
        return bundle[pkg_rel]
    fp = Path(file_rel)
    pp = Path(pkg_rel)
    if fp.exists():
        return fp.read_text(encoding="utf-8", errors="replace")
    if pp.exists():
        return pp.read_text(encoding="utf-8", errors="replace")
    return None


def _module_exports_from_source(source: str) -> set[str]:
    try:
        tree = ast.parse(normalize_newlines(source))
    except Exception:
        return set()
    exports: set[str] = set()
    explicit_all: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            exports.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if isinstance(target, ast.Name):
                    exports.add(target.id)
                    if target.id == "__all__" and isinstance(value, (ast.List, ast.Tuple, ast.Set)):
                        for elt in value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                explicit_all.add(elt.value)
    return explicit_all or exports


def _class_methods_from_source(source: str, class_name: str) -> set[str]:
    try:
        tree = ast.parse(normalize_newlines(source))
    except Exception:
        return set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return set()


def _class_init_arity_from_source(source: str, class_name: str) -> Tuple[int, int | None] | None:
    try:
        tree = ast.parse(normalize_newlines(source))
    except Exception:
        return None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                    total = len(getattr(item.args, "posonlyargs", [])) + len(item.args.args)
                    defaults = len(item.args.defaults)
                    min_args = max(0, total - defaults - 1)
                    max_args = None if item.args.vararg is not None else max(0, total - 1)
                    return min_args, max_args
    return None


def _normalize_ctor_arity_spec(spec: object) -> Tuple[int, int | None] | None:
    if spec is None:
        return None
    if isinstance(spec, int):
        return spec, spec
    if (
        isinstance(spec, tuple)
        and len(spec) == 2
        and isinstance(spec[0], int)
        and (isinstance(spec[1], int) or spec[1] is None)
    ):
        return spec[0], spec[1]
    return None


def _directive_contract_issues(
    bundle: Dict[str, str],
    task_text: str,
    *,
    module_source_for_name: Callable[[str, Dict[str, str]], str | None] = _module_source_for_name,
    module_exports_from_source: Callable[[str], set[str]] = _module_exports_from_source,
) -> List[str]:
    directives = parse_task_contract_directives(task_text)
    if not directives:
        return []

    issues: List[str] = []
    forbid_import_specs: List[Tuple[str, set[str]]] = []
    for entry in directives.get("FORBID_IMPORTS", []):
        tokens = entry.split()
        if len(tokens) >= 2:
            module = tokens[0].strip()
            symbols = {tok.strip() for tok in tokens[1:] if tok.strip()}
            if symbols:
                forbid_import_specs.append((module, symbols))

    forbid_calls = {
        token.strip()
        for entry in directives.get("FORBID_CALLS", [])
        for token in entry.split()
        if token.strip()
    }

    allowed_method_specs: Dict[str, set[str]] = {}
    short_class_names: Dict[str, str] = {}
    for entry in directives.get("ALLOWED_METHODS", []):
        tokens = entry.split()
        if len(tokens) >= 2:
            fqcn = tokens[0].strip()
            short_class_names[fqcn.split(".")[-1]] = fqcn
            allowed_method_specs[fqcn] = {tok.strip() for tok in tokens[1:] if tok.strip()}

    constructor_specs: Dict[str, int] = {}
    for entry in directives.get("CONSTRUCTOR", []):
        match = re.match(r"(\S+)\((.*)\)$", entry.strip())
        if not match:
            continue
        fqcn = match.group(1).strip()
        arglist = [x.strip() for x in match.group(2).split(",") if x.strip()]
        short_class_names[fqcn.split(".")[-1]] = fqcn
        constructor_specs[fqcn] = len(arglist)

    config_wrapper_specs: Dict[str, Dict[str, str]] = {}
    for entry in directives.get("CONFIG_WRAPPER", []):
        tokens = entry.split()
        if not tokens:
            continue
        fqcn = tokens[0].strip()
        short_class_names[fqcn.split(".")[-1]] = fqcn
        spec: Dict[str, str] = {}
        for token in tokens[1:]:
            if "=" in token:
                key, value = token.split("=", 1)
                spec[key.strip()] = value.strip()
        if spec:
            config_wrapper_specs[fqcn] = spec

    result_key_specs: Dict[str, set[str]] = {}
    for entry in directives.get("RESULT_KEYS", []):
        tokens = entry.split()
        if len(tokens) >= 2:
            result_key_specs[tokens[0].strip()] = {tok.strip() for tok in tokens[1:] if tok.strip()}

    for rel, content in bundle.items():
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(normalize_newlines(content), filename=rel)
        except Exception:
            continue

        imported_names: Dict[str, str] = {}
        var_types: Dict[str, str] = {}
        var_has_config: Dict[str, bool] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").strip()
                if module.startswith("src."):
                    module = module[4:]
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    imported_names[alias.asname or alias.name] = f"{module}.{alias.name}" if module else alias.name
                for forbid_module, forbid_symbols in forbid_import_specs:
                    if module == forbid_module:
                        for alias in node.names:
                            if alias.name in forbid_symbols:
                                issues.append(f"{rel}: violates FORBID_IMPORTS via `{module}.{alias.name}`")

        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target = node.targets[0].id
                value = node.value
                if isinstance(value, ast.Call):
                    call_name = _call_name(value.func) or ""
                    resolved = imported_names.get(call_name, short_class_names.get(call_name, call_name))
                    if call_name in short_class_names:
                        resolved = short_class_names[call_name]
                    if resolved in constructor_specs:
                        var_types[target] = resolved
                        argc = len(value.args) + len([kw for kw in value.keywords if kw.arg is not None])
                        expected = constructor_specs[resolved]
                        if argc != expected:
                            issues.append(f"{rel}: {resolved.split('.')[-1]}() is called with {argc} args but CONSTRUCTOR requires {expected}")
                        wrapper = config_wrapper_specs.get(resolved)
                        if wrapper and value.args:
                            first = value.args[0]
                            unless = wrapper.get("unless", "").lstrip(".")
                            first_name = _call_name(first) or ""
                            resolved_first = imported_names.get(first_name, first_name)
                            if unless and (resolved_first.endswith("." + unless) or first_name == unless):
                                pass
                            elif wrapper.get("first_arg_requires") == ".config":
                                bad_wrapper = False
                                if _is_simplenamespace_call(first):
                                    bad_wrapper = not any((kw.arg == "config") for kw in first.keywords if kw.arg)
                                elif isinstance(first, ast.Name) and first.id in var_has_config:
                                    bad_wrapper = not var_has_config[first.id]
                                if bad_wrapper:
                                    issues.append(f"{rel}: {resolved.split('.')[-1]} first arg must satisfy CONFIG_WRAPPER")
                    elif _is_simplenamespace_call(value):
                        var_has_config[target] = any((kw.arg == "config") for kw in value.keywords if kw.arg)
                elif isinstance(value, ast.Name) and value.id in var_has_config:
                    var_has_config[target] = var_has_config[value.id]

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = _call_name(node.func) or ""
                if call_name in forbid_calls:
                    issues.append(f"{rel}: violates FORBID_CALLS via `{call_name}`")
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    fqcn = var_types.get(node.func.value.id)
                    if fqcn and fqcn in allowed_method_specs and node.func.attr not in allowed_method_specs[fqcn]:
                        issues.append(f"{rel}: `{node.func.value.id}.{node.func.attr}()` violates ALLOWED_METHODS for `{fqcn}`")

        for result_fn, keys in result_key_specs.items():
            if _result_keys_contract_applies(rel, tree, result_fn):
                for key in keys:
                    if key not in content:
                        issues.append(f"{rel}: missing RESULT_KEYS contract token `{key}` for `{result_fn}`")

    deduped: List[str] = []
    seen: set[str] = set()
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            deduped.append(issue)
    return deduped


def _protected_python_semantic_issues(
    bundle: Dict[str, str],
    task_text: str,
    *,
    module_source_for_name: Callable[[str, Dict[str, str]], str | None] = _module_source_for_name,
    module_exports_from_source: Callable[[str], set[str]] = _module_exports_from_source,
    class_methods_from_source: Callable[[str, str], set[str]] = _class_methods_from_source,
    class_init_arity_from_source: Callable[[str, str], Tuple[int, int | None] | None] = _class_init_arity_from_source,
) -> List[str]:
    protected_modules = {
        "builder.orchestrator.runner",
        "builder.orchestrator.project_config",
        "builder.orchestrator.cli",
        "builder.orchestrator.backlog",
        "builder.orchestrator.execution_result",
    }
    runner_source = module_source_for_name("builder.orchestrator.runner", bundle) or ""
    runner_methods = class_methods_from_source(runner_source, "OrchestratorRunner")
    runner_ctor = _normalize_ctor_arity_spec(class_init_arity_from_source(runner_source, "OrchestratorRunner"))
    config_requires_wrapper = ("config.config" in runner_source) or ("cfg.config" in runner_source)
    issues: List[str] = []

    for rel, content in bundle.items():
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(normalize_newlines(content), filename=rel)
        except Exception:
            continue

        imported_names: Dict[str, str] = {}
        var_types: Dict[str, str] = {}
        var_has_config: Dict[str, bool] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").strip()
                if module.startswith("src."):
                    module = module[4:]
                if module in protected_modules:
                    source = module_source_for_name(module, bundle)
                    exports_set = module_exports_from_source(source or "") if source is not None else set()
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        imported_names[alias.asname or alias.name] = f"{module}.{alias.name}"
                        if source is not None and alias.name not in exports_set and module_source_for_name(f"{module}.{alias.name}", bundle) is None:
                            issues.append(f"{rel}: imports missing symbol '{alias.name}' from '{module}'")

        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target = node.targets[0].id
                value = node.value
                if isinstance(value, ast.Call):
                    call_name = _call_name(value.func) or ""
                    resolved = imported_names.get(call_name, call_name)
                    if resolved.endswith("OrchestratorRunner") or call_name == "OrchestratorRunner":
                        var_types[target] = "OrchestratorRunner"
                        argc = len(value.args) + len([kw for kw in value.keywords if kw.arg is not None])
                        if runner_ctor is not None:
                            min_args, max_args = runner_ctor
                            if argc < min_args or (max_args is not None and argc > max_args):
                                req = str(min_args) if min_args == max_args else f"{min_args}-{max_args if max_args is not None else 'n'}"
                                issues.append(f"{rel}: OrchestratorRunner() is called with {argc} args but protected constructor requires {req}")
                        if config_requires_wrapper and value.args:
                            first = value.args[0]
                            bad_wrapper = False
                            if _is_simplenamespace_call(first):
                                bad_wrapper = not any((kw.arg == "config") for kw in first.keywords if kw.arg)
                            elif isinstance(first, ast.Name) and first.id in var_has_config:
                                bad_wrapper = not var_has_config[first.id]
                            elif isinstance(first, ast.Call):
                                first_name = _call_name(first.func) or ""
                                if first_name.endswith("ProjectConfig"):
                                    bad_wrapper = False
                            if bad_wrapper:
                                issues.append(f"{rel}: OrchestratorRunner first arg must be ProjectConfig or object with .config")
                    elif _is_simplenamespace_call(value):
                        var_has_config[target] = any((kw.arg == "config") for kw in value.keywords if kw.arg)
                elif isinstance(value, ast.Name) and value.id in var_has_config:
                    var_has_config[target] = var_has_config[value.id]

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                obj = node.func.value.id
                attr = node.func.attr
                if var_types.get(obj) == "OrchestratorRunner" and runner_methods and attr not in runner_methods:
                    issues.append(f"{rel}: variable '{obj}' is an OrchestratorRunner; protected API has no method '{attr}'")

    deduped: List[str] = []
    seen: set[str] = set()
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            deduped.append(issue)
    return deduped


def validate_static_bundle_contracts(
    bundle: Dict[str, str],
    task_text: str,
    *,
    protected_python_semantic_issues: Callable[[Dict[str, str], str], List[str]] | None = None,
    directive_contract_issues: Callable[[Dict[str, str], str], List[str]] | None = None,
) -> Tuple[bool, str]:
    issues: List[str] = []

    runner_path = "src/builder/orchestrator/runner.py"
    runner = bundle.get(runner_path, "")
    if runner:
        defined_methods = set(RUNNER_METHOD_HEADER_RE.findall(runner))
        for method in parse_required_runner_methods(task_text):
            if method in {"select_next_task", "run_next_task", "execute_task", "process_execution_result", "simulate_backlog"} and method not in defined_methods:
                issues.append(f"`{runner_path}` is missing required method `{method}`.")
        lower_task = normalize_newlines(task_text).lower()
        if "processed_tasks" in lower_task and "simulate_backlog" in defined_methods:
            for key in ["processed_tasks", "stopped_reason", "final_status", "approval_required", "planned_actions"]:
                if key not in runner:
                    issues.append(f"`{runner_path}` appears to be missing simulation return key `{key}`.")

    project_config_path = "src/builder/orchestrator/project_config.py"
    project_config = bundle.get(project_config_path, "")
    if "@dataclass(frozen=True)" in project_config:
        issues.append(f"`{project_config_path}` uses frozen dataclasses, but the task requires mutable config objects.")

    cli_path = "src/builder/orchestrator/cli.py"
    cli = bundle.get(cli_path, "")
    if "default_task_runner" in cli:
        issues.append(f"`{cli_path}` invents `default_task_runner`, but the task requires no fallback command.")
    if "run_next_task(" in cli and "real_execution=" in cli:
        issues.append(f"`{cli_path}` calls `run_next_task(..., real_execution=...)`, but the task requires the legacy public signature.")

    directive_checker = directive_contract_issues or _directive_contract_issues
    protected_checker = protected_python_semantic_issues or _protected_python_semantic_issues
    issues.extend(directive_checker(bundle, task_text))
    issues.extend(protected_checker(bundle, task_text))

    if issues:
        deduped: List[str] = []
        seen: set[str] = set()
        for issue in issues:
            if issue not in seen:
                seen.add(issue)
                deduped.append(issue)
        return False, "Static bundle contract violations detected:\n" + "\n".join(f"- {x}" for x in deduped)
    return True, ""
