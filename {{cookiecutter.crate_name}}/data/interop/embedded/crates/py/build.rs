//! Records the build-time interpreter's home for the embedded interpreter to use at runtime.

use std::path::{Path, PathBuf};

fn main() {
    let config = pyo3_build_config::get();

    // Only covers this package's binaries; link arguments do not reach dependent packages
    pyo3_build_config::add_libpython_rpath_link_args();
    let target_os = std::env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    let rpath_capable = !matches!(target_os.as_str(), "windows" | "cygwin");
    if let (true, true, Some(lib_dir)) = (config.shared(), rpath_capable, config.lib_dir()) {
        println!("cargo::metadata=lib_dir={lib_dir}");
    }

    let executable = config
        .executable()
        .expect("pyo3 found no interpreter; set PYO3_PYTHON to the one you want to link against")
        .to_owned();

    let output = std::process::Command::new(&executable)
        .args(["-c", "import sys; print(sys.base_prefix)"])
        .output()
        .unwrap_or_else(|e| panic!("failed to run the build-time interpreter {executable}: {e}"));

    assert!(
        output.status.success(),
        "the build-time interpreter {executable} exited with {}",
        output.status
    );

    let home = String::from_utf8(output.stdout)
        .expect("interpreter printed a non-UTF-8 prefix")
        .trim()
        .to_owned();

    if target_os == "windows" {
        stage_python_dlls(Path::new(&home));
    }

    println!("cargo::rustc-env=PYTHON_HOME={home}");
    // Any `rerun-if` directive replaces cargo's default file tracking, so name every path here
    println!("cargo::rerun-if-env-changed=PYO3_PYTHON");
    println!("cargo::rerun-if-changed=build.rs");
    println!("cargo::rerun-if-changed={executable}");
}

/// Copies the interpreter's DLLs beside the binaries cargo produces, for Windows only.
///
/// Windows has no rpath. It resolves imports at load time from the executable's own directory or
/// `PATH`, and cargo's test, bench, and bin outputs have neither the DLL beside them nor a search
/// path leading to it, so they die with `STATUS_DLL_NOT_FOUND` before `main` runs.
///
/// Failure here is a warning rather than a panic: the copy is a convenience, and the DLL may
/// legitimately be locked by a binary that is already running.
fn stage_python_dlls(home: &Path) {
    let Some(profile_dir) = profile_dir() else {
        println!("cargo::warning=no OUT_DIR to derive the target directory from; DLLs not staged");
        return;
    };

    let dlls: Vec<PathBuf> = std::fs::read_dir(home)
        .ok()
        .into_iter()
        .flatten()
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| is_python_dll(path))
        .collect();

    if dlls.is_empty() {
        println!("cargo::warning=no python3*.dll under {}", home.display());
        return;
    }

    // Bins land in the profile directory, test and bench executables in its `deps`
    for directory in [profile_dir.clone(), profile_dir.join("deps")] {
        if let Err(e) = std::fs::create_dir_all(&directory) {
            println!(
                "cargo::warning=could not create {}: {e}",
                directory.display()
            );
            continue;
        }

        for dll in &dlls {
            let Some(name) = dll.file_name() else {
                continue;
            };
            let destination = directory.join(name);

            if same_size(dll, &destination) {
                continue;
            }
            if let Err(e) = std::fs::copy(dll, &destination) {
                println!(
                    "cargo::warning=could not copy {} to {}: {e}",
                    dll.display(),
                    directory.display()
                );
            }
        }
    }
}

/// Locates `target/[<triple>/]<profile>`, which holds the binaries cargo is building.
fn profile_dir() -> Option<PathBuf> {
    // OUT_DIR is `<target>/[<triple>/]<profile>/build/<package>-<hash>/out`
    let out_dir = PathBuf::from(std::env::var_os("OUT_DIR")?);
    Some(out_dir.ancestors().nth(3)?.to_path_buf())
}

/// Whether a path names one of the interpreter's DLLs, e.g. `python313.dll` or `python3.dll`.
fn is_python_dll(path: &Path) -> bool {
    let is_dll = path
        .extension()
        .is_some_and(|extension| extension.eq_ignore_ascii_case("dll"));

    let is_interpreter = path
        .file_stem()
        .and_then(|stem| stem.to_str())
        .is_some_and(|stem| stem.to_ascii_lowercase().starts_with("python3"));

    is_dll && is_interpreter
}

/// Whether both paths exist with the same length, used to skip copies that would be no-ops.
fn same_size(source: &Path, destination: &Path) -> bool {
    match (source.metadata(), destination.metadata()) {
        (Ok(source), Ok(destination)) => source.len() == destination.len(),
        _ => false,
    }
}
