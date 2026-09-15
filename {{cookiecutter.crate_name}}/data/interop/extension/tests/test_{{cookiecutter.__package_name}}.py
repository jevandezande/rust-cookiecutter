{%- set pkg = cookiecutter.__package_name -%}
"""Tests of the boundary from the Python side: what a caller of the wheel sees.

The Rust half lives in `crates/core`, with its own `#[test]`s. These cover the crossing itself,
which Rust tests cannot reach: conversion, exceptions, and releasing the interpreter.
"""

import threading

import pytest
from {{pkg}} import ScoreError, best_score


def test_best_score_picks_the_maximum() -> None:
    """Run the core logic in Rust and bring the result back."""
    assert best_score([1.0, 16.0, 4.0]) == 4.0


def test_best_score_of_empty_is_none() -> None:
    """Return `None` rather than raising, matching `Option` on the Rust side."""
    assert best_score([]) is None


def test_an_int_is_accepted() -> None:
    """pyo3 converts a Python `int` to the `f64` the signature asks for."""
    assert best_score([9]) == 3.0


def test_rejects_a_negative_value() -> None:
    """A Rust error surfaces as this module's own exception type, not a panic."""
    with pytest.raises(ScoreError, match="cannot score a negative value: -1"):
        best_score([-1.0])


def test_score_error_reports_its_package() -> None:
    """A traceback names `{{pkg}}._core.ScoreError`, not the bare crate name `_core`."""
    assert ScoreError.__module__ == "{{pkg}}._core"


def test_is_usable_from_several_threads() -> None:
    """Survive concurrent calls from several threads."""
    scores: dict[int, float | None] = {}

    def score(i: int) -> None:
        scores[i] = best_score([float(i * i)])

    workers = [threading.Thread(target=score, args=(i,)) for i in range(4)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    assert [scores[i] for i in range(4)] == [0.0, 1.0, 2.0, 3.0]
