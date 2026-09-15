---
name: write-python-code
description: Write or review code in this repo. Use when writing new code, reviewing existing code, or editing code.
argument-hint: "[source code]"
---

# Writing Code

Use this skill when writing, reviewing, or editing code.

## Purpose

The goal of this document is to provide guidance when coding in this repository. All code should be pythonic and easy to read.

Python version: >=3.13

## Before every commit

- Ensure all code has type annotations
- Add Google-style docstrings (NO types, NO leading articles)
- Run checks: `uv run prek -a`
- Prek hooks will run automatically and must pass

## Code conventions

### Docstrings

See skill `write-python-docstrings`

### Type annotations

- All functions must have complete type annotations
- Import types from `typing` only when necessary (prefer built-ins)
- Use modern syntax: `list[str]`, `dict[str, int]` (not `List[str]`, `Dict[str, int]`)
- Do not use a bare `dict`, always annotate the type of the `dict` (e.g. `dict[str, float]`)
- Use `Any` in `dict` annotations only if absolutely necessary
- Use `|` for union types: `str | None`
- Avoid `from __future__ import annotations`

### Code formatting

Via ruff

- Line length: 100
- Indentation: 4 spaces (no tabs except Makefiles)

### Naming conventions

- Functions/methods: snake_case
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Classes: PascalCase
- Modules: snake_case
- Private attributes/methods: _leading_underscore

### Imports

- Absolute imports preferred
- Group imports: standard library, third-party, local
- No wildcard imports (`from module import *`) except in `__init__.py`
- Import sorting handled by ruff (isort)
- Do not use import statements within a function unless absolutely necessary

### Error handling

- Prefer specific exceptions; define custom exceptions for domain errors
  (e.g. `SpamTypeError(ValueError)`, `SpamEatingError(RuntimeError)`)
- Avoid bare `except:` clauses

### General style

- Use f-strings for string formatting
- Prefer list/dict comprehensions over loops when appropriate
- Use `pathlib.Path` for file operations instead of `os.path`
- Use dataclasses and prefer the settings `slots=True` and `frozen=True`.
- Don't use `.0` to indicate floats
- Prefer `strict=True` in `zip` and `itertools.batched`
- Use a guard case in all `match`/`case` statements (i.e. `case _:`)

## Essential commands

Code quality tools (ruff, ty, pytest) are configured per-package in `pyproject.toml`.

```bash
uv run ruff format .  # Format code
uv run ruff check .   # Lint code
uv run ty check       # Type check
uv run pytest         # Run tests
uv run prek -a        # Run all prek hooks
```

Mise auto-activates the dev environment on `cd`; run `mise trust` if you see permission errors.

## Testing

Use pytest; tests live in `hooks/` (`testpaths = ["hooks"]`); doctests are auto-discovered in source.
See the skill `write-python-tests` when actively writing tests.

## Git development guidelines

- Create a new branch for all new work (avoid developing on master); offer a worktree if Claude is
  already working in this directory (`git worktree add ../{package}-{feature}`).
- Break work into manageable commits; use conventional commit prefixes (`feat:`, `fix:`, `docs:`,
  `test:`, `refactor:`, `chore:`). Never include Claude as a co-author.
- When complete, open a descriptive PR (`gh pr create`) breaking down what changed; clean up any
  worktree afterward.

### Documentation

Use skill `write-python-docstrings`

## Troubleshooting

- Formatting/lint failures: usually auto-fixed by ruff; re-stage and retry. For a lint rule that
  needs `# noqa: <rule>`, ask before adding.
- Type failures: fix annotations/mismatches, verify with `uv run ty check`.
- Test failures: fix the test or code, use `uv run pytest -v` for detail.

## Miscellaneous

Do not add new packages without explicitly asking first.
Never add ignores to the pyproject.toml formatting, linting, or type checking without explicitly asking
