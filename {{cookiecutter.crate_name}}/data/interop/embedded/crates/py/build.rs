//! Records the build-time interpreter's home for the embedded interpreter to use at runtime.

fn main() {
    let config = pyo3_build_config::get();

    // Only covers this package's binaries; link arguments do not reach dependent packages
    pyo3_build_config::add_libpython_rpath_link_args();
    if let (true, Some(lib_dir)) = (config.shared(), config.lib_dir()) {
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

    println!("cargo::rustc-env=PYTHON_HOME={home}");
    // Any `rerun-if` directive replaces cargo's default file tracking, so name every path here
    println!("cargo::rerun-if-env-changed=PYO3_PYTHON");
    println!("cargo::rerun-if-changed=build.rs");
    println!("cargo::rerun-if-changed={executable}");
}
