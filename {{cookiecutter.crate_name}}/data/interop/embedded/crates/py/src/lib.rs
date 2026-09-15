{%- set pkg = cookiecutter.__package_name -%}
{%- set crate = cookiecutter.crate_name -%}
//! Embedded Python interop: the only crate that links libpython.
//!
//! Keep this layer thin. Logic belongs in `{{crate}}`, behind a trait this crate implements.
//!
//! Every [`Python::attach`] contends for the same GIL, so `rayon` over a [`PyScorer`] is slower
//! than a plain loop. Batch instead (see [`Scorer::score_all`]), which must pass the whole slice
//! in one call, not attach once and still call Python per element. Detach around Rust work, or
//! link a free-threaded interpreter.

use std::path::{Path, PathBuf};
use std::sync::OnceLock;

use pyo3::prelude::*;
use pyo3::types::{PyList, PyModule};
use {{pkg}}::Scorer;

static BOOTSTRAP: OnceLock<Result<(), String>> = OnceLock::new();

/// How the executable relates to a `mise run bundle` layout (`bin/` next to `python/`).
#[derive(Debug, Clone, PartialEq, Eq)]
enum BundleLayout {
    /// `../python` relative to the executable's `bin/` directory exists.
    Present(PathBuf),
    /// The executable sits in a `bin/` directory, but `../python` is missing.
    Missing,
    /// Not a bundle: cargo's `target/` layout, or any other location.
    NotABundle,
}

/// Sets `PYTHONHOME` and, in development only, `PYTHONPATH`; a no-op once it has succeeded.
///
/// Must run before the interpreter starts. [`PyScorer::new`] calls it; call it explicitly only
/// when reaching for [`import_fn`] or `Python::attach`.
///
/// A bundled binary (`dist/bin/<exe>` next to `dist/python/`) uses that interpreter alone and
/// ignores `$VIRTUAL_ENV`. Development builds restore the active venv's `site-packages`, because
/// `PYTHONHOME` would otherwise hide them.
///
/// Call it from `main` before spawning any thread. Mutating the environment corrupts silently,
/// without panicking, if another thread reads it concurrently, including libc doing so on its
/// own, and `OnceLock` cannot guarantee that.
///
/// # Errors
///
/// executable in a `bin/` directory without a sibling `../python`, or a missing build-time
/// `PYTHONHOME`
pub fn bootstrap() -> Result<(), PyError> {
    match BOOTSTRAP.get_or_init(configure_interpreter) {
        Ok(()) => Ok(()),
        Err(message) => Err(PyError(message.clone())),
    }
}

/// Decides the interpreter home and applies `PYTHONHOME` / `PYTHONPATH`.
///
/// The result is cached, so a failure is remembered rather than retried.
#[expect(
    unsafe_code,
    reason = "configuring the interpreter means setting environment variables before it starts"
)]
fn configure_interpreter() -> Result<(), String> {
    let plan = plan_home()?;

    // SAFETY: `OnceLock` runs this exactly once, before the interpreter starts and before this
    // crate spawns any thread.
    unsafe { std::env::set_var("PYTHONHOME", &plan.home) };

    if plan.inject_venv
        && let Some(site_packages) = active_venv_site_packages()
    {
        let path = match std::env::var_os("PYTHONPATH") {
            Some(existing) => {
                let sep = if cfg!(windows) { ";" } else { ":" };
                format!(
                    "{}{sep}{}",
                    site_packages.display(),
                    existing.to_string_lossy()
                )
            }
            None => site_packages.display().to_string(),
        };

        // SAFETY: as above.
        unsafe { std::env::set_var("PYTHONPATH", path) };
    }

    Ok(())
}

/// Interpreter home and whether to prepend `$VIRTUAL_ENV`'s `site-packages`.
struct HomePlan {
    home: PathBuf,
    inject_venv: bool,
}

/// Chooses the interpreter home from the executable's layout.
fn plan_home() -> Result<HomePlan, String> {
    match std::env::current_exe().ok().as_deref().map(classify_bundle) {
        Some(BundleLayout::Present(home)) => Ok(HomePlan {
            home,
            inject_venv: false,
        }),
        Some(BundleLayout::Missing) => {
            Err("bundled interpreter not found next to the executable; \
             expected python/ beside bin/"
                .into())
        }
        Some(BundleLayout::NotABundle) | None => {
            let home = PathBuf::from(env!("PYTHON_HOME"));
            if !home.is_dir() {
                return Err(format!(
                    "build-time PYTHONHOME {} is not a directory",
                    home.display()
                ));
            }
            Ok(HomePlan {
                home,
                inject_venv: true,
            })
        }
    }
}

/// Classifies an executable path against the `dist/bin` + `dist/python` bundle layout.
fn classify_bundle(exe: &Path) -> BundleLayout {
    let Some(bin_dir) = exe.parent() else {
        return BundleLayout::NotABundle;
    };
    if bin_dir.file_name() != Some(std::ffi::OsStr::new("bin")) {
        return BundleLayout::NotABundle;
    }
    let Some(root) = bin_dir.parent() else {
        return BundleLayout::Missing;
    };
    let home = root.join("python");
    if home.is_dir() {
        BundleLayout::Present(home)
    } else {
        BundleLayout::Missing
    }
}

/// Locates `site-packages` inside `$VIRTUAL_ENV`, which `PYTHONHOME` otherwise hides.
fn active_venv_site_packages() -> Option<PathBuf> {
    let venv = PathBuf::from(std::env::var_os("VIRTUAL_ENV")?);

    let candidate = if cfg!(windows) {
        venv.join("Lib").join("site-packages")
    } else {
        std::fs::read_dir(venv.join("lib"))
            .ok()?
            .filter_map(Result::ok)
            .find(|entry| entry.file_name().to_string_lossy().starts_with("python"))?
            .path()
            .join("site-packages")
    };

    candidate.is_dir().then_some(candidate)
}

/// An error raised by Python, with its traceback.
#[derive(Debug)]
pub struct PyError(String);

impl std::fmt::Display for PyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for PyError {}

impl PyError {
    fn new(py: Python<'_>, err: &PyErr) -> Self {
        let traceback = err
            .traceback(py)
            .and_then(|tb| tb.format().ok())
            .unwrap_or_default();
        Self(format!("{traceback}{err}"))
    }
}

/// Imports `module.attr` from the embedded interpreter.
///
/// Call [`bootstrap`] first, before any [`Python::attach`]. Add the package with `uv add` so it
/// lands in `[project.dependencies]` and on the venv's `sys.path` in development builds.
///
/// # Errors
///
/// unimportable `module`, or `module` without `attr`
pub fn import_fn(py: Python<'_>, module: &str, attr: &str) -> Result<Py<PyAny>, PyError> {
    PyModule::import(py, module)
        .and_then(|imported| imported.getattr(attr))
        .map(pyo3::Bound::unbind)
        .map_err(|err| PyError::new(py, &err))
}

/// A [`Scorer`] backed by the embedded interpreter.
///
/// Placeholder: calls `math.sqrt`. Point [`import_fn`] at a package from `[project.dependencies]`.
#[derive(Debug)]
pub struct PyScorer {
    /// Resolved once, to keep a `getattr` out of the hot path.
    score: Py<PyAny>,
}

impl PyScorer {
    /// Starts the interpreter and resolves the placeholder callable.
    ///
    /// # Errors
    ///
    /// unimportable `math`, or `math` without `sqrt`
    pub fn new() -> Result<Self, PyError> {
        bootstrap()?;

        Python::attach(|py| import_fn(py, "math", "sqrt").map(|score| Self { score }))
    }

    /// Calls the cached Python function with the interpreter already attached.
    fn call(&self, py: Python<'_>, x: f64) -> Result<f64, PyError> {
        self.score
            .bind(py)
            .call1((x,))
            .and_then(|value| value.extract())
            .map_err(|e| PyError::new(py, &e))
    }

    /// One Python call over the whole slice: `list(map(score, xs))`.
    ///
    /// Replace this with a vectorized import (`import_fn(py, "numpy", "sqrt")`) that
    /// accepts the array in one call.
    fn call_all(&self, py: Python<'_>, xs: &[f64]) -> Result<Vec<f64>, PyError> {
        let values = PyList::new(py, xs).map_err(|e| PyError::new(py, &e))?;
        PyModule::import(py, "builtins")
            .and_then(|builtins| {
                let mapped = builtins
                    .getattr("map")?
                    .call1((self.score.bind(py), &values))?;
                builtins.getattr("list")?.call1((mapped,))
            })
            .and_then(|value| value.extract())
            .map_err(|e| PyError::new(py, &e))
    }
}

impl Scorer for PyScorer {
    type Error = PyError;

    fn score(&self, x: f64) -> Result<f64, Self::Error> {
        Python::attach(|py| self.call(py, x))
    }

    /// Crosses into Python once for the whole batch, not once per element.
    fn score_all(&self, xs: &[f64]) -> Result<Vec<f64>, Self::Error> {
        Python::attach(|py| self.call_all(py, xs))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scores_through_python() {
        let scorer = PyScorer::new().unwrap();
        assert!((scorer.score(9.0).unwrap() - 3.0).abs() < f64::EPSILON);
    }

    #[test]
    fn reports_python_exceptions() {
        let scorer = PyScorer::new().unwrap();
        let err = scorer.score(-1.0).unwrap_err().to_string();

        assert!(err.contains("math domain error"), "{err}");
    }

    #[test]
    fn formats_a_python_traceback() {
        bootstrap().unwrap();

        let err = Python::attach(|py| {
            let src =
                std::ffi::CString::new("def boom():\n    raise ValueError('negative input')\n")
                    .expect("literal contains a nul byte");
            let file = std::ffi::CString::new("boom.py").expect("literal contains a nul byte");
            let name = std::ffi::CString::new("boom").expect("literal contains a nul byte");
            PyModule::from_code(py, &src, &file, &name)
                .and_then(|module| module.getattr("boom"))
                .and_then(|boom| boom.call0())
                .map_err(|e| PyError::new(py, &e))
                .unwrap_err()
        })
        .to_string();

        assert!(err.contains("negative input"), "{err}");
        assert!(err.contains("Traceback"), "{err}");
    }

    #[test]
    fn import_fn_reports_a_missing_module() {
        bootstrap().unwrap();

        let err = Python::attach(|py| import_fn(py, "definitely_not_a_module", "x").unwrap_err());

        assert!(err.to_string().contains("ModuleNotFoundError"), "{err}");
    }

    #[test]
    fn drives_the_core_logic() {
        let scorer = PyScorer::new().unwrap();
        let best = {{pkg}}::best_score(&scorer, &[1.0, 16.0, 4.0]).unwrap();

        assert_eq!(best, Some(4.0));
    }

    #[test]
    fn score_all_of_empty_is_empty() {
        let scorer = PyScorer::new().unwrap();
        assert_eq!(scorer.score_all(&[]).unwrap(), Vec::<f64>::new());
    }

    #[test]
    fn batching_matches_element_by_element() {
        let scorer = PyScorer::new().unwrap();
        let xs = [1.0, 16.0, 4.0];

        let batched = scorer.score_all(&xs).unwrap();
        let one_by_one: Vec<f64> = xs.iter().map(|&x| scorer.score(x).unwrap()).collect();

        assert_eq!(batched, one_by_one);
    }

    /// Several threads sharing one scorer must serialize on the GIL rather than deadlock or race.
    #[test]
    fn is_usable_from_several_threads() {
        let scorer = std::sync::Arc::new(PyScorer::new().unwrap());

        let workers: Vec<_> = (0..4)
            .map(|i| {
                let scorer = std::sync::Arc::clone(&scorer);
                std::thread::spawn(move || scorer.score(f64::from(i * i)).unwrap())
            })
            .collect();

        let results: Vec<f64> = workers.into_iter().map(|w| w.join().unwrap()).collect();

        assert_eq!(results, vec![0.0, 1.0, 2.0, 3.0]);
    }

    /// A directory of this test's own. The counter is what keeps concurrent tests apart: the
    /// clock alone can hand two of them the same reading, and then they share a tree.
    fn scratch_tree() -> PathBuf {
        static NEXT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

        let root = std::env::temp_dir().join(format!(
            "py-bundle-layout-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .expect("clock before UNIX_EPOCH")
                .as_nanos(),
            NEXT.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
        ));
        std::fs::create_dir_all(&root).unwrap();
        root
    }

    #[test]
    fn classify_bundle_finds_python_beside_bin() {
        let root = scratch_tree();
        let exe = root.join("bin").join("app");
        std::fs::create_dir_all(exe.parent().unwrap()).unwrap();
        std::fs::create_dir_all(root.join("python")).unwrap();

        assert_eq!(
            classify_bundle(&exe),
            BundleLayout::Present(root.join("python"))
        );
        std::fs::remove_dir_all(root).ok();
    }

    #[test]
    fn classify_bundle_reports_a_bin_without_python() {
        let root = scratch_tree();
        let exe = root.join("bin").join("app");
        std::fs::create_dir_all(exe.parent().unwrap()).unwrap();

        assert_eq!(classify_bundle(&exe), BundleLayout::Missing);
        std::fs::remove_dir_all(root).ok();
    }

    #[test]
    fn classify_bundle_ignores_cargo_target_layout() {
        assert_eq!(
            classify_bundle(Path::new("/tmp/target/release/app")),
            BundleLayout::NotABundle
        );
    }
}
