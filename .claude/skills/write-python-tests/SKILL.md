---
name: write-python-tests
description: Write or review unit tests for code in this repo. Use when writing new tests, reviewing existing tests, or adding test coverage.
argument-hint: "[module or file to test]"
---

# Writing Unit Tests

Follow these conventions when writing or modifying tests in this codebase.

## Core Principles

- **Only write tests that provide real information.** Avoid testing trivial things like object construction or obvious attribute access. Test behavior and computations.
- **Don't check types in tests.** Types are verified by the static type checker (`ty`). Avoid using `isinstance`, `type()`, or other type assertions in tests.
- **Write doctests to explain function usage.** Doctests are a quick way to show how to use a function and expected output; they also are quick smoke tests.

## File and Function Structure

Tests live in `hooks/` next to the modules they cover (`testpaths = ["hooks"]` in `pyproject.toml`).
Name files `test_<module>.py`.
Use plain functions, never classes:

```python
"""Tests for the Spam."""

from pytest import approx, mark, param, raises

from spam import Spam


def test_classic_spam() -> None:
    """Test classic spam values."""
    classic_spam = Spam("classic")
    assert classic_spam.weight == approx(3.14159265)
```

- Add a module-level docstring to every test file.
- Give each test function a Google-style one-line docstring.
- Define module-level constants for reuse across multiple tests. Don't rebuild them inside tests.

## Float Comparisons

Use default tolerance thresholds unless there is a specific, documented reason to override them.

| Use case | Tool | Import |
|---|---|---|
| Scalars and simple lists | `approx` | `from pytest import approx` |

```python
# Scalars
assert Spam("classic").weight == approx(3.14159265)

# Lists / tuples
assert Spam("jalapeno").scores == approx([1, 2, 3])

# Only override thresholds when truly necessary, with a comment explaining why
assert Spam("bacon").weight == approx(3.14, abs=0.005)  # loose: GitHub Actions results differ

# Exceptions
with raises(ValueError):
    Spam("classic").process(threshold=-1)
```

## Parametrize Similar Tests

Use `pytest.mark.parametrize` to collapse tests that differ only in inputs/outputs.

```python
@mark.parametrize(
    ("spam_type", "weight"),
    [
        ("classic", 3.14159265),
        ("maple", 4.1),
        param("low sodium", 2.9),
    ],
)
def test_weights(spam_type: str, weight: float) -> None:
    """Test weight for each spam type."""
    spam = Spam(spam_type)
    assert spam.weight == approx(weight)
```

When a test is related to a GitHub issue, link it in the docstring.

## Fixtures

Use pytest fixtures for any setup that is repeated across multiple tests. Place fixtures in `conftest.py`:

- **Within this repo:** `hooks/conftest.py` if shared fixtures appear
- **Shared across packages:** not currently applicable

## Documentation

Docstrings should concisely state what is being tested in the initial sentence.
Additional information about why should be placed in the follow-up paragraph.
If available, include the issue number.
Do not explain code in tests, only what is being tested

Comments should be used sparingly and only when targetted information is needed
(e.g. the value a test would be if something weren't working)

### Example

```python
def test_sum_on_negatives() -> None:
    """Sums of negative numbers should be negative.

    #153 found that sums of negative numbers were positive.
    """
    # previously 5
    assert sum(-2, -3) == -5
    assert sum(-1.3, -4.5) == -5.8
```

### Incorrect example (do not do this!)

```python
def test_sum() -> None:  #  ❌ not descriptive enough
    """Check negative sums.  # ❌ not descriptive enough

    Fixes #153  #  ❌ does not describe the problem
    """
    # The sum function adds two numbers  #  ❌ don't add code description as comments
    assert sum(-2, -3) == -5
    assert sum(-1.3, -4.5) == -5.8
```

## Imports

Prefer importing selectively from pytest for readability

```python
from pytest import approx, mark, param, raises
```

## What NOT to Test

- Type correctness (use `ty check` instead)
- That a function returns something (trivial)
- Exact exception message text (fragile)
- Behavior of external libraries
- Implementation details that should be free to change

Focus on observable behavior: computed values, raised exceptions for invalid inputs, and correct transformations.
