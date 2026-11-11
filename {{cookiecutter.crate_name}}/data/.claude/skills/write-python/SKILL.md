---
name: write-python
description: Write or review Python in this workspace. Use when writing new Python, reviewing it, or editing it.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Writing Python

Use this skill when writing or editing Python in this workspace. Use `write-docstrings` when
documenting it, `test-python` when adding tests, and `cleanup-code` for a final review. Rust has
its own skills, starting with `write-code`.

Python is 3.13 or newer (`requires-python` in `pyproject.toml`).

{interop_rules}

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

- f-strings for formatting; `pathlib.Path` for files, never `os.path`.
- Comprehensions over accumulate-in-a-loop when they read as clearly.
- `@dataclass(frozen=True, slots=True)` for records.
- `zip(..., strict=True)` and `itertools.batched(..., strict=True)`.
- Every `match` ends with `case _:`.
- Write `1`, not `1.0`, where an integer literal means the same thing.
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
- Do not add a dependency without asking. Adding one means editing `pyproject.toml`, running
  `mise run lock`, and committing `uv.lock`; see AGENTS.md "Lockfile discipline".

## Commands

```sh
mise run py-fmt     # ruff format
mise run py-lint    # ruff check
mise run py-types   # ty check
mise run py-test    # pytest
mise run check      # everything that reports, Rust and markdown included
```

Run the task, not the tool under it: `mise run` puts `.venv` on `PATH` and sets `UV_LOCKED`.
Never add a `# noqa`, a `# ty: ignore`, or an ignore in `pyproject.toml` without asking.
