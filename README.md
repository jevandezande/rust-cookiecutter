# Rust Cookiecutter

[![License](https://img.shields.io/github/license/jevandezande/rust-cookiecutter)](https://github.com/jevandezande/rust-cookiecutter/blob/master/LICENSE)
[![Rust: 1.90+](https://img.shields.io/badge/rust-1.90%2B-000000?logo=rust)](https://www.rust-lang.org)
[![Edition: 2024](https://img.shields.io/badge/edition-2024-000000?logo=rust)](https://doc.rust-lang.org/edition-guide/rust-2024/index.html)
[![Code style: rustfmt](https://img.shields.io/badge/code%20style-rustfmt-000000.svg)](https://github.com/rust-lang/rustfmt)
[![Linting: clippy](https://img.shields.io/badge/linting-clippy-000000.svg)](https://github.com/rust-lang/rust-clippy)
[![Python: uv](https://img.shields.io/badge/python-uv-261230?logo=uv)](https://docs.astral.sh/uv/)
[![Linting: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checking: ty](https://img.shields.io/badge/types-ty-261230)](https://docs.astral.sh/ty/)
[![Markdown style: rumdl](https://img.shields.io/badge/md%20style-rumdl-000000.svg)](https://rumdl.dev)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/jevandezande/rust-cookiecutter/test.yml?branch=master&logo=github-actions)](https://github.com/jevandezande/rust-cookiecutter/actions/)

[Cookiecutter](https://github.com/cookiecutter/cookiecutter) template for a Rust project, with
optional Python interop:

- `none` - pure Rust
- `extension` - Rust compiled into a native module that Python imports
- `embedded` - a Python interpreter embedded in the binary, for calling third-party packages

A generated project has `crates/core` (pure Rust), `crates/py` (the Python boundary) under
`embedded` and `extension`, and optionally `crates/cli`.

## Features

- Toolchain pinning with [rustup](https://rustup.rs) and `rust-toolchain.toml`
- Dev environment, task running, and version-pinned tooling with [mise](https://mise.jdx.dev)
- Rust:
  - Formatting with [rustfmt](https://github.com/rust-lang/rustfmt)
  - Linting with [clippy](https://github.com/rust-lang/rust-clippy)
  - Benchmarking with [criterion](https://bheisler.github.io/criterion.rs/book/)
- Python:
  - Environment management with [uv](https://docs.astral.sh/uv/)
  - Interop with [pyo3](https://pyo3.rs)
  - Abi3 extension module with [maturin](https://maturin.rs)
  - Formatting and linting with [ruff](https://docs.astral.sh/ruff/)
  - Type checking with [ty](https://docs.astral.sh/ty/)
  - Testing with [pytest](https://docs.pytest.org)
- Markdown formatting and linting with [rumdl](https://rumdl.dev)
- Documentation with `cargo doc`, `missing_docs`, and denied broken intra-doc links
- License and advisory auditing with [cargo-deny](https://embarkstudios.github.io/cargo-deny/)
- Local coverage with [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) (`mise run coverage`)
- Git hooks with [prek](https://prek.j178.dev)
- Continuous integration with [GitHub Actions](https://github.com/features/actions)
- Optional release workflow (tagged binaries, crates.io publish, or PyPI wheels)
- Optional coding agent setup, including a full set of Rust [skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)

## Setup

Install `mise`, `rustup`, and `uv`.

```sh
curl https://mise.run | sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Generation needs uv; generated projects get their own from mise.toml
mise use -g uv

# Optional
curl -sS https://webi.sh/gh | sh
```

mise supplies the generated project's dev environment and task runner. It needs a shell hook
(`eval "$(mise activate zsh)"`) to activate on `cd`; see [notes.md](notes.md#mise).

[notes.md](notes.md#project-tools) covers optional tools and [alternative installation methods](notes.md#alternative-installation-methods).

```sh
# Use cookiecutter to create a project from this template
uvx cookiecutter gh:jevandezande/rust-cookiecutter
```

The cookiecutter will automagically:

- Writes the project from the answers
- Initializes git
- Pins the Rust version rustup resolved, and declares an older MSRV
- Adds requested Rust dependencies with `cargo add`, and Python packages with `uv add`
- Creates the Python environment with `uv sync`
- Builds the workspace, pinning the interpreter pyo3 links against
- Trusts `mise.toml` and pins the dev tools in `mise.lock`
- Installs pre-commit and pre-push hooks with prek
- Sets up the chosen coding agent, if any
- Runs the project's own commit and push hooks, tests included, and reports anything they flag
- Makes the initial commit
- Adds the `origin` remote and, if requested, creates the GitHub repo and pushes

## Options

| Option | Description |
| --- | --- |
| `crate_name` | kebab-case package name, defaulting to `project_name` lowercased with `-` for spaces. Names the repository, the output directory, the core crate, the `crate_name-cli` and `crate_name-python` crates, and the binary. Cargo's rule (`_` for `-`) derives the snake_case identifier that code imports; there is no prompt for it |
| `project_url` | Repository URL, defaulting to the GitHub one built from `github_username` and `crate_name`. Written into `Cargo.toml`, and used as the `origin` remote only when `github_setup=None` (see [notes.md](notes.md#git-remote-and-github)) |
| `crate_type` | `both` (library + CLI binary) or `lib` (library only: no `crates/cli`, and no bundle scripts under `python_interop=embedded`) |
| `python_interop` | Which direction Rust and Python call each other. `none` (default) is pure Rust with no pyo3 and no `crates/py`. `extension` lets Python import Rust: `crates/py` is an abi3 `cdylib` that maturin builds into a wheel. `embedded` lets Rust call Python: `crates/py` links an interpreter |
| `cargo_dependencies` | Space-separated, `cargo add` syntax (e.g. `serde@1.0 rayon`). Added to `crates/core` |
| `cargo_dev_dependencies` | Same, added with `cargo add --dev` |
| `python_dependencies` | Space-separated, `uv add` syntax (e.g. `numpy scipy`). Under `embedded` they land in `[project.dependencies]` for the interpreter to import, though the skeleton still calls `math.sqrt`. Under `extension` they are the wheel's runtime dependencies. Under `none` pre-gen rejects them, since nothing imports them |
| `description` | One-line crate description; falls back to `project_name` |
| `keywords` | Space-separated crates.io keywords, max 5 |
| `license` | `MIT`, `Apache-2.0`, `BSD-3-Clause`, or `None`. `None` is proprietary, not unlicensed: `LICENSE` is an all-rights-reserved notice, `Cargo.toml` declares `LicenseRef-Proprietary`, and the crates are `publish = false` |
| `github_setup` | Create the GitHub repo as `private`, `internal`, `public`, or `None`. The repo is `github_username/crate_name`, so `internal` needs `github_username` to be an organization |
| `release_ci` | `binaries` (tagged GitHub release with checksums and provenance), `crates.io` (Trusted Publishing), `pypi` (maturin wheels and an sdist, Trusted Publishing), or `None`. `binaries` requires `crate_type=both`; `crates.io` requires an open-source license; `pypi` requires `python_interop=extension` |
| `coding_agent` | `Claude`, `Codex`, or `None`. `AGENTS.md` is always written, and every agent reads it; `Claude` additionally gets `.claude/settings.json`. The skills land in `.claude/skills/` either way |

`author_name` and `github_username` are required; generation fails if either is blank.
`description` and `keywords` are required when `release_ci=crates.io`.

`release_ci=crates.io` publishes through Trusted Publishing (OIDC). Publish the first version by
hand with `cargo publish`, then add the GitHub repository as a trusted publisher on the crate.

`release_ci=pypi` requires `python_interop=extension` and publishes through PyPI Trusted
Publishing. PyPI accepts a pending publisher for a project that does not exist yet, so the first
release can come from the workflow.

## Recommendations

- Make a custom config file (see [template_config.yml](template_config.yml))
- Install [act](https://github.com/nektos/act) to run GitHub Actions locally

[notes.md](notes.md) has more tips.

For Python projects, see the [uv-cookiecutter](https://github.com/jevandezande/uv-cookiecutter) and [pixi-cookiecutter](https://github.com/jevandezande/pixi-cookiecutter).
