{%- set pkg = cookiecutter.__package_name -%}
{%- set crate = cookiecutter.crate_name -%}
//! {{cookiecutter.project_name}}
//!
{%- if cookiecutter.python_interop == 'embedded' %}
//! Pure Rust: no Python dependency, compiles without an interpreter. Anything this crate needs
//! from Python is expressed as a trait and implemented in `{{crate}}-python`.
{%- elif cookiecutter.python_interop == 'extension' %}
//! Pure Rust: no Python dependency, compiles without an interpreter. `{{crate}}-python` wraps
//! this crate as a Python extension module.
{%- else %}
//! Pure Rust: no Python dependency, compiles without an interpreter. Anything expensive or
//! swappable is expressed as a trait and implemented by the caller.
{%- endif %}
//!
//! [`Scorer`] and [`best_score`] are the skeleton of that split, over a placeholder operation, and
//! [`NativeScorer`] is the one placeholder implementation every consumer shares.

/// Something that scores a value.
///
/// Implementations that cross an expensive boundary should override [`Scorer::score_all`] to cross
/// it once per batch.
pub trait Scorer {
    /// How the implementation reports failure.
    type Error;

    /// Scores a single value.
    ///
    /// # Errors
    ///
    /// whatever the implementation considers a failure
    fn score(&self, x: f64) -> Result<f64, Self::Error>;

    /// Scores every value in `xs`.
    ///
    /// The default implementation calls [`Scorer::score`] once per element.
    ///
    /// # Errors
    ///
    /// first error the scorer returns
    fn score_all(&self, xs: &[f64]) -> Result<Vec<f64>, Self::Error> {
        xs.iter().map(|&x| self.score(x)).collect()
    }
}

/// Returns the highest score across `xs`, or `None` if `xs` is empty.
///
/// Scores through [`Scorer::score_all`], so an expensive boundary is crossed once.
///
/// # Errors
///
/// first error the scorer returns
///
/// # Examples
///
/// ```
/// use {{pkg}}::{Scorer, best_score};
///
/// struct Doubler;
/// impl Scorer for Doubler {
///     type Error = std::convert::Infallible;
///     fn score(&self, x: f64) -> Result<f64, Self::Error> {
///         Ok(x * 2.0)
///     }
/// }
///
/// assert_eq!(best_score(&Doubler, &[1.0, 4.0, 2.0])?, Some(8.0));
/// # Ok::<(), std::convert::Infallible>(())
/// ```
pub fn best_score<S: Scorer>(scorer: &S, xs: &[f64]) -> Result<Option<f64>, S::Error> {
    Ok(scorer.score_all(xs)?.into_iter().reduce(f64::max))
}

/// Pure-Rust placeholder implementation of [`Scorer`]: `f64::sqrt`, rejecting negative input.
///
/// The CLI and the Python boundary both score through this one type, so there is a single answer
/// to what a negative value does. Replace the body with the real work.
#[derive(Debug, Clone, Copy, Default)]
pub struct NativeScorer;

impl Scorer for NativeScorer {
    type Error = NegativeInput;

    fn score(&self, x: f64) -> Result<f64, Self::Error> {
        if x < 0.0 {
            Err(NegativeInput(x))
        } else {
            Ok(x.sqrt())
        }
    }
}

/// A value [`NativeScorer`] cannot score.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct NegativeInput(pub f64);

impl std::fmt::Display for NegativeInput {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "cannot score a negative value: {}", self.0)
    }
}

impl std::error::Error for NegativeInput {}

#[cfg(test)]
mod tests {
    use super::*;

    struct Doubler;

    impl Scorer for Doubler {
        type Error = std::convert::Infallible;

        fn score(&self, x: f64) -> Result<f64, Self::Error> {
            Ok(x * 2.0)
        }
    }

    #[test]
    fn best_score_of_empty_is_none() {
        assert_eq!(best_score(&Doubler, &[]).unwrap(), None);
    }

    #[test]
    fn best_score_picks_the_maximum() {
        assert_eq!(best_score(&Doubler, &[1.0, 4.0, 2.0]).unwrap(), Some(8.0));
    }

    #[test]
    fn native_scorer_takes_the_square_root() {
        assert!((NativeScorer.score(9.0).unwrap() - 3.0).abs() < f64::EPSILON);
    }

    #[test]
    fn native_scorer_rejects_a_negative_value() {
        assert_eq!(NativeScorer.score(-1.0), Err(NegativeInput(-1.0)));
    }

    #[test]
    fn negative_input_names_the_value() {
        assert_eq!(
            NegativeInput(-1.0).to_string(),
            "cannot score a negative value: -1"
        );
    }

    #[test]
    fn best_score_stops_at_the_first_error() {
        assert_eq!(
            best_score(&NativeScorer, &[1.0, -4.0, 16.0]),
            Err(NegativeInput(-4.0))
        );
    }
}
