{%- set pkg = cookiecutter.__package_name -%}
{%- set crate = cookiecutter.crate_name -%}
//! Python extension module: this crate compiles to `{{pkg}}._core`.
//!
//! Keep this layer thin. Logic belongs in `{{crate}}`, including the [`{{pkg}}::Scorer`]
//! implementation; this crate converts, calls in, and converts back.
//!
//! Python holds the GIL across a call in, so anything doing real Rust work should hand it back
//! with [`Python::detach`], as `best_score` does. Cross the boundary once per batch rather than
//! once per element: a `for` loop in Python around a `#[pyfunction]` pays the crossing every time.
//!
//! The tests for this crate are the pytest suite in `tests/`: the Rust half is `{{crate}}`'s and
//! has its own `#[test]`s.

use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use {{pkg}}::{NativeScorer, NegativeInput};

// The first argument is the `__module__` Python reports, so a traceback reads
// `{{pkg}}._core.ScoreError` rather than the bare `_core.ScoreError` the crate name would give.
create_exception!(
    {{pkg}}._core,
    ScoreError,
    PyException,
    "Raised when a value cannot be scored."
);

/// Crosses a core error into Python as `ScoreError`.
///
/// A `From` impl is not an option, since both types are foreign to this crate. Give each new core
/// error a function like this one rather than raising a bare `PyException`.
fn score_error(err: NegativeInput) -> PyErr {
    ScoreError::new_err(err.to_string())
}

/// Returns the highest score across `xs`, or `None` if `xs` is empty.
///
/// Raises `ScoreError` if any value is negative.
#[pyfunction]
fn best_score(py: Python<'_>, xs: Vec<f64>) -> PyResult<Option<f64>> {
    py.detach(move || {{pkg}}::best_score(&NativeScorer, &xs))
        .map_err(score_error)
}

/// The module Python imports as `{{pkg}}._core`.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("ScoreError", m.py().get_type::<ScoreError>())?;
    m.add_function(wrap_pyfunction!(best_score, m)?)
}
