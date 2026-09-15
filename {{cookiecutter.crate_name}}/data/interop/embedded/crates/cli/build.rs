{%- set pkg = cookiecutter.__package_name -%}
{%- set crate = cookiecutter.crate_name -%}
//! Points this binary at libpython, so the loader can find it at runtime.
//!
//! `{{crate}}-python` publishes the directory as metadata, since its link args do not reach here.

fn main() {
    if let Ok(lib_dir) = std::env::var("DEP_{{pkg.upper()}}_PYTHON_LIB_DIR") {
        println!("cargo::rustc-link-arg=-Wl,-rpath,{lib_dir}");
    }

    println!("cargo::rerun-if-changed=build.rs");
}
