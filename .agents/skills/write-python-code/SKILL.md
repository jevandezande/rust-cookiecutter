---
name: write-python-code
description: Writes and reviews Python. Use when writing new code, reviewing it, or editing it.
argument-hint: "[directory or file]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Writing Code

Use this skill when writing or editing code. Use `write-python-docstrings` when documenting it,
`write-python-tests` when adding tests, and `cleanup-python-code` for a final review.

Python version: >=3.13

## Before every commit

- Annotate every function and method completely
- Write Google-style docstrings; see `write-python-docstrings`
- Run `prek run -a --stage pre-push`; tests run at pre-push, not pre-commit. Hooks must pass

## Type annotations

- Annotate every function and method completely, return type included (`-> None` too).
- Built-in generics: `list[str]`, `dict[str, float]`, `tuple[int, ...]`; never `typing.List`.
- Never a bare `dict` or `list`; give the element types. Use `Any` only when nothing narrower
  fits.
- `TypedDict` over `dict[str, Any]` when the keys are known, as for a JSON record.
- `X | None`, not `Optional[X]`. `Self` for methods returning their own class.
- Abstract parameter types from `collections.abc` (`Sequence`, `Mapping`, `Iterable`) when the
  function only reads them; concrete return types.
- No `from __future__ import annotations`; quote a forward reference instead.
- Avoid `cast`. If ty cannot see a type, fix the annotation that hides it.

## Style

- ruff formats: 4-space indentation, line length from `line-length` in `pyproject.toml`.
- f-strings for formatting; `pathlib.Path` for files, never `os.path`.
- Comprehensions over accumulate-in-a-loop when they read as clearly.
- `@dataclass(frozen=True, slots=True)` for records.
- `zip(..., strict=True)` and `itertools.batched(..., strict=True)`.
- Every `match` ends with `case _:`.
- Write `1`, not `1.0`, where an integer literal means the same thing.
- Names: `snake_case` for functions, variables, and modules; `PascalCase` for classes;
  `UPPER_SNAKE_CASE` for constants; `_leading_underscore` for private attributes and methods.
- Constants are `UPPER_SNAKE_CASE` at module level, with a `#` comment giving their unit when
  they have one.
- Comments say why, sparingly. Never narrate a change or restate the code.
- Never name a module after one in the standard library, such as `types.py`; it shadows it.

## Errors

- Raise the most specific built-in exception that fits, or a domain exception derived from one:
  `ValueError` for invalid input, `RuntimeError` for a failed operation. Never a bare
  `Exception`.
- No bare `except:`, and no `except Exception:` that swallows the error.

## Imports

- Absolute imports, grouped and sorted by ruff. No wildcard imports.
- Imports go at the top of the module, not inside a function.
- Do not add a dependency without asking.

## Essential commands

```bash
mise run fmt                    # Format code
mise run lint                   # Lint code
mise run types                  # Type check
mise run test                   # Run tests
mise run all                    # Every check, then the tests
prek run -a --stage pre-push    # Run all prek hooks, tests included
```

## Mise integration

Mise auto-activates the dev environment on `cd`; run `mise trust` if you see permission errors.

## Testing

Use pytest; tests live in `hooks/`; doctests are auto-discovered in source. See `write-python-tests`
when writing tests.

## CI/CD

CI runs `mise run all` and prek's TOML, YAML, and whitespace hooks via GitHub Actions. Run
`prek run -a --stage pre-push` to reproduce the whole set locally.

## Troubleshooting

- Formatting and lint failures: usually auto-fixed by ruff; re-stage and retry.
- Type failures: fix the annotation or the mismatch; verify with `mise run types`.
- Test failures: fix the test or the code; `uv run pytest -v` for detail,
  `uv run pytest hooks/test_file.py::test_name` for one test.

Never add a `# noqa`, a `# ty: ignore`, or an ignore in `pyproject.toml` without asking.

## Additional resources

- [uv](https://docs.astral.sh/uv)
- [ruff](https://docs.astral.sh/ruff)
- [ty](https://github.com/astral-sh/ty)
- [pytest](https://docs.pytest.org)
- [prek](https://prek.j178.dev)
- [Google docstring style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
