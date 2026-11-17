---
name: test-python
description: Write or review pytest tests in this workspace. Use when writing new Python tests, reviewing them, or adding coverage.
argument-hint: [module or file to test]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Writing Python Tests

Use this skill for pytest. Rust tests are in `test-code`, code conventions in `write-python`,
and docstring conventions in `write-docstrings`.

## Core principles

- Test behavior and computed values. A test that only constructs an object or reads back an
  attribute it set tells nobody anything.
- Do not check types; ty does that. No `isinstance` or `type()` assertions, unless the type is
  the behavior.
- Prefer a concrete expected value when one is known; use a relation when the relation is the
  behavior.
- A test with branches is several tests. Split it or parametrize it.
- Delete a scaffolding test once it no longer protects lasting behavior.
- Write a doctest for how a function is called, and a test for what it must get right.

{interop_rules}

## Structure

Plain functions, never classes:

```python
"""Tests for the toolchain-bump helpers."""

from bump_toolchain import next_msrv

PINNED = "1.97.1"


def test_next_msrv_never_moves_backwards() -> None:
    """An MSRV already past the lagged pin stays where it is."""
    assert next_msrv(PINNED, "1.96") == "1.96"
```

- Every file has a module docstring saying what it tests and, when it matters, what it leaves
  out.
- Every test has a docstring whose summary states the behavior checked, not the function name.
- Name a test for the behavior: `test_next_msrv_never_moves_backwards`, not `test_next_msrv`.
- Shared inputs are module-level constants, built once and never mutated.
- A fake that one test needs is defined in that test.

## Imports

Import `pytest` as a module and reach through it: `pytest.approx`, `pytest.mark.parametrize`,
`pytest.raises`, `pytest.fixture`.

## Floats

Use `pytest.approx` at its default tolerance unless there is a reason not to, and give the
reason in a named constant with its unit:

```python
# Wall-clock jitter between two runs on a shared CI runner, in seconds
TIMING_TOLERANCE = 0.05

assert elapsed == pytest.approx(EXPECTED_SECONDS, abs=TIMING_TOLERANCE)
assert counts == [1, 2, 4]  # exact values need no approx
```

## Parametrize

Collapse tests that differ only in input and expected output:

```python
@pytest.mark.parametrize(
    ("pinned", "declared", "expected"),
    [("1.97.1", "1.90", "1.95"), ("1.91.0", "1.93", "1.93"), ("2.1.0", "1.90", "2.0")],
)
def test_msrv_trails_the_pin_without_falling(pinned: str, declared: str, expected: str) -> None:
    """The MSRV trails the pin, but never drops below the declared one."""
    assert next_msrv(pinned, declared) == expected
```

## Fixtures

A module-level constant serves most setup. Reach for `@pytest.fixture` when setup is expensive
and should run once (`scope="module"`), needs teardown, or needs `tmp_path` or `monkeypatch`.
Keep a fixture in the file that uses it; a `conftest.py` is for one shared across files.

## Exceptions

Assert the most specific exception class, not a base such as `Exception`, so the test also pins
which error the caller sees. Add `match=` only for the part of the message that is contract,
such as the name of the offending value, never the full wording.

## Tests that need what a machine may lack

Never check for a requirement and `return`: pytest counts that as a pass. Skip visibly instead:

- a platform or a program: `@pytest.mark.skipif(..., reason="...")`, with a reason a reader can
  act on
- an optional package: `pytest.importorskip`
- a whole module: `pytest.skip(..., allow_module_level=True)`

## Docstrings and comments

The summary states what is tested. Why goes in the following paragraph, with the issue or PR
number if there is one. Comments are rare: the value a broken build used to give, or why a
tolerance is loose, not what the next line does.

```python
def test_next_msrv_crosses_a_major_release() -> None:
    """A pin early in a new major release keeps the MSRV at that major's first minor.

    #NN found the lag subtracted across the major boundary, declaring `2.-1`.
    """
```

## What not to test

- types, which ty checks
- that a function returns something
- the full text of an error message
- the behavior of pytest or another library
- implementation details that should be free to change
