{%- set pkg = cookiecutter.__package_name -%}
{%- set crate = cookiecutter.crate_name -%}
# {{cookiecutter.project_name}}

{% if cookiecutter.license == "None" %}[![License](https://img.shields.io/badge/license-Proprietary-black)]({{cookiecutter.project_url}}/blob/master/LICENSE){% else %}[![License](https://img.shields.io/github/license/{{cookiecutter.github_username}}/{{crate}})]({{cookiecutter.project_url}}/blob/master/LICENSE){% endif %}
{% if cookiecutter.release_ci == 'crates.io' %}[![Crates.io](https://img.shields.io/crates/v/{{crate}}?logo=rust)](https://crates.io/crates/{{crate}})
[![Docs.rs](https://img.shields.io/docsrs/{{crate}}?logo=docsdotrs)](https://docs.rs/{{crate}})
{% elif cookiecutter.release_ci == 'pypi' %}[![PyPI](https://img.shields.io/pypi/v/{{crate}}?logo=pypi)](https://pypi.org/project/{{crate}}/)
{% endif %}[![Rust: {rust_msrv}+](https://img.shields.io/badge/rust-{rust_msrv}%2B-000000?logo=rust)](https://www.rust-lang.org)
[![Edition: 2024](https://img.shields.io/badge/edition-2024-000000?logo=rust)](https://doc.rust-lang.org/edition-guide/)
[![Code style: rustfmt](https://img.shields.io/badge/code%20style-rustfmt-000000.svg)](https://github.com/rust-lang/rustfmt)
[![Linting: clippy](https://img.shields.io/badge/linting-clippy-000000.svg)](https://github.com/rust-lang/rust-clippy)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://docs.astral.sh/uv/)
[![Linting: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://docs.astral.sh/ty/)
[![Markdown style: rumdl](https://img.shields.io/badge/md%20style-rumdl-000000.svg)](https://rumdl.dev)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/{{cookiecutter.github_username}}/{{crate}}/test.yml?branch=master&logo=github-actions)]({{cookiecutter.project_url}}/actions/)

## Layout

{% if cookiecutter.python_interop == 'embedded' -%}
A Rust workspace that calls Python through an embedded interpreter.
{%- elif cookiecutter.python_interop == 'extension' -%}
A Rust workspace that Python calls, compiled into a native extension module.
{%- else -%}
A pure-Rust workspace; nothing here links or imports Python.
{%- endif %}

| Crate | Purpose |
| --- | --- |
| `crates/core` | `{{crate}}`: pure Rust. No pyo3, no interpreter, fast to compile and test. |
{% if cookiecutter.python_interop == 'embedded' %}| `crates/py` | `{{crate}}-python`: the only crate that links libpython. |
{% elif cookiecutter.python_interop == 'extension' %}| `crates/py` | `{{crate}}-python`: the pyo3 extension module, imported as `{{pkg}}._core`. |
{% endif %}{% if cookiecutter.crate_type != 'lib' %}| `crates/cli` | `{{crate}}-cli`: thin binary, builds the `{{crate}}` executable. |
{% endif %}
## Where to start

The generated code is a working skeleton. It compiles, tests, and benchmarks a placeholder
operation (scoring an `f64` by taking its square root), so a fresh checkout proves
{% if cookiecutter.python_interop == 'embedded' -%}
the interpreter links and runs before you write anything.
{%- elif cookiecutter.python_interop == 'extension' -%}
the extension module builds and imports before you write anything.
{%- else -%}
the workspace builds, tests, and benchmarks before you write anything.
{%- endif %}

{% if cookiecutter.python_interop == 'embedded' -%}
Replace the placeholder operation: `uv add` the package, call it through `import_fn`, and keep
the Rust-visible surface small. `crates/py/benches` measures the trait's batching, and the tests
in `crates/py` catch a broken interpreter setup.
{%- elif cookiecutter.python_interop == 'extension' -%}
Replace the placeholder operation: put the work in `crates/core`, expose it through the
`#[pymodule]` in `crates/py`, and keep `python/{{pkg}}/_core.pyi` in step with it.
{%- else -%}
Replace the placeholder operation: implement `Scorer` for the real work and keep `best_score`
written against the trait, so a pure-Rust fake can still test it.
{%- endif %}

## Development

Prerequisites are [rustup](https://rustup.rs) and [mise](https://mise.jdx.dev).
`rust-toolchain.toml` pins the toolchain. `mise.toml` supplies uv, cargo-deny, and cargo-llvm-cov,
activates `.venv`, and defines every task. `cd` into the project and mise syncs the environment.

```sh
mise tasks               # list every task
mise run build           # cargo build --workspace
mise run test            # cargo test --workspace
{%- if cookiecutter.python_interop == 'extension' %}
mise run develop         # build the extension module into .venv, in place
mise run wheel           # release wheel into dist/
{%- endif %}
mise run clippy          # clippy over every target, warnings as errors
mise run docs            # cargo doc, warnings as errors
mise run msrv            # check against the MSRV in Cargo.toml
mise run bump-toolchain  # re-pin to current stable, moving the MSRV with it
mise run bench           # criterion benchmarks
mise run profile-build   # release build with debug symbols
mise run coverage        # line coverage, HTML report
{% if cookiecutter.python_interop == 'extension' -%}
mise run py-test         # pytest over python/, tests/, and scripts/
{%- else -%}
mise run py-test         # pytest over scripts/
{%- endif %}
mise run deny            # cargo-deny license and advisory audit
mise run check           # reports only, safe for CI
mise run all             # check + test + py-test
```

[prek](https://prek.j178.dev) runs formatting, linting, and markdown checks on `git commit` and
`git push`, and the test suites on `git push` alone.

{interop_notes}
## Performance

`[profile.release]` uses thin LTO and a single codegen unit. `mise run bench` runs criterion over
{% if cookiecutter.python_interop == 'embedded' -%}
the workspace: `crates/core/benches` measures the Rust core, and `crates/py/benches` measures
the cost of crossing into the interpreter.
{%- else -%}
the workspace; `crates/core/benches` measures the Rust core.
{%- endif %}
Results land in `target/criterion`.

[samply](https://github.com/mstange/samply) is not among the pinned tools. Once installed,
{% if cookiecutter.crate_type != 'lib' %}`samply record target/profiling/{{crate}}` reads the profiling build.{% else %}`samply record` over a bench binary reads the profiling build.{% endif %}

`.cargo/config.toml` has commented-out settings for a faster linker and `target-cpu=native`.

## Coverage

`mise run coverage` runs [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) over the
workspace and writes an HTML report to `target/llvm-cov/html/index.html`. It is a local task:
CI does not run it and nothing enforces a threshold.

```sh
mise run coverage          # HTML report in target/llvm-cov/html
mise run coverage-summary  # per-file table on stdout
```

Coverage builds use their own `RUSTFLAGS`, so the first run after an ordinary `cargo build`
recompiles the workspace, and the next plain build recompiles it back. Doctests are not counted:
`cargo llvm-cov --doctests` needs nightly, and `rust-toolchain.toml` pins stable.
{% if cookiecutter.release_ci == 'crates.io' %}
## Releasing

Tagging `v*` publishes every workspace member to crates.io, in dependency order, over Trusted
Publishing. The release workflow refuses a tag that disagrees with the workspace version, so bump
first and tag second:

```sh
cargo set-version --workspace 0.1.0   # cargo-edit; rewrites the path-dependency pins too
git commit -am "Release 0.1.0" && git tag v0.1.0 && git push --tags
```

The version appears twice: in `[workspace.package]` and again in the path-dependency pins in
`Cargo.toml`. That is why a tool does the bump rather than a hand edit.
{% elif cookiecutter.release_ci == 'binaries' %}
## Releasing

Tagging `v*` {% if cookiecutter.python_interop == 'embedded' %}runs `mise run bundle`{% else %}builds the release binary{% endif %} in CI across Linux, macOS, and Windows, and
attaches the archives, their checksums, and build provenance to a GitHub release.
{% elif cookiecutter.release_ci == 'pypi' %}
## Releasing

Tagging `v*` builds an abi3 wheel for Linux, macOS, and Windows plus an sdist, and publishes them
to PyPI over Trusted Publishing. The wheel's version is read from `Cargo.toml`, so bump first and
tag second:

```sh
cargo set-version --workspace 0.1.0   # cargo-edit; rewrites the path-dependency pins too
git commit -am "Release 0.1.0" && git tag v0.1.0 && git push --tags
```

Before the first tag, add a pending publisher at <https://pypi.org/manage/account/publishing/>
naming this repository and `release.yml`. PyPI accepts one for a project that does not exist yet,
so nothing needs uploading by hand.
{% endif %}
## Credits

Created with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) from the [jevandezande/rust-cookiecutter](https://github.com/jevandezande/rust-cookiecutter) template.
