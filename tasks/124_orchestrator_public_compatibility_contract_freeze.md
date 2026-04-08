# Task 124 — Orchestrator public compatibility contract freeze

## Goal
Freeze the public/tested compatibility surface so orchestrator repairs preserve aliases and stable payload keys instead of renaming seams ad hoc.

## Scope
- failure journal helper argument aliases
- project contract convenience keys
- manifest entry aliases
- merge/status/result truth fields

## Required changes
- add one canonical compatibility-contract module or table
- route helper coercion through that contract rather than scattered per-file alias handling
- add focused tests proving both canonical and compatibility spellings remain accepted

## Acceptance
- focused tests cover legacy and canonical forms
- no docs claim wider autonomy
- full `ruff check .` and `pytest -q` are green
