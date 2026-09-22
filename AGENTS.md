# AI Agent Development Guide

Cookiecutter template for Rust projects (rustup, uv, mise). This repository is Python (>=3.13).
Generated projects are Rust crates with optional Python bindings and distribution.

## Skills

Load `.claude/skills/` before editing. Ignore `{{cookiecutter.crate_name}}/data/.claude/skills/`:
those are Rust skills that ship into generated projects. The exception is when editing the
template's own Rust - `write-code` and `write-doc-comments` there describe the conventions the
template body follows.

## Layout

- `{{cookiecutter.crate_name}}/` - template body (generated project)
  - `crates/` - shared by every mode: `core` always; `cli` unless `crate_type=lib`
  - `data/` - post-gen hook staging data (deleted in produced template)
  - `data/interop/<mode>/` - files `set_interop()` copies over the project root
  - `data/STATE.md` - progress-tracker scaffold, copied to the root only when an agent is set up
  - `scripts/` - `check_msrv.py` and `bump_toolchain.py`
- `hooks/` - cookiecutter hooks and their tests
- `.github/workflows/` - CI that generates projects and runs checks

`next_msrv()` in the scripts duplicates `hooks/post_gen_project.py:msrv()`. Keep the two in agreement.

`data/STATE.md` is the file `generate-spec`, `implement-spec`, and `compare-code-to-spec` read and
tick. Its headings (`Current Focus`, `Next Action`) and table columns (`Spec Generated`, `Code
Implemented`, `Tests Passing`) are named as those skills name them; rename in both places or not
at all.

## Rendering

`hooks/` is rendered. `post_gen_project.py` embeds `{{cookiecutter.*}}` in string literals and in
the defaults of `add_dependencies`/`add_python_dependencies`. Functions that need a cookiecutter
value take it as a parameter so tests can pass their own.

`_copy_without_render` covers `.github/workflows/release-*.yml` and `data/.claude/skills`, because
GitHub Actions `${{ ... }}` collides with Jinja. A release workflow cannot branch on an option:
`set_release_ci` copies one file and deletes the rest. `test.yml` is outside that glob so it can
branch on `python_interop`; wrap every `${{ ... }}` in `{% raw %}`. `data/.claude/settings.json` is
rendered: a literal `{{ ... }}` in it breaks generation.

`mise.toml` is rendered. Mise then applies Tera to `[env]` values, so wrap those `{{ ... }}` in
`{% raw %}{% endraw %}`. Task `run` strings are not Tera-templated.

In `mise.toml`, `depends` runs tasks in parallel; a `run` array runs them in series and stops at
the first failure. Chain tasks that rewrite the same files (`fmt` before `clippy-fix`) through a
`run` array.

The root `prek.toml` excludes Jinja-bearing `Cargo.toml`, `pyproject.toml`, `mise.toml`, and
`test.yml` under `{{cookiecutter.crate_name}}/` from `check-toml`/`check-yaml`.
The generated `prek.toml` has no such exclusions: its hooks call `mise run` tasks, so per-mode
details live in `mise.toml` alone.

## Options

- `crate_type` is `both` or `lib`. `set_crate_type()` runs after `set_interop()` and drops
  `crates/cli` plus the bundle scripts (`bundle.py`, `smoke_bundle.py`, and their tests). Those
  deletions are no-ops unless `embedded` copied the scripts in. `core` is always present; `py` is
  absent under `python_interop=none`. `members = ["crates/*"]` picks up whichever survive.
- `license=None` means proprietary, not unlicensed: `set_license` copies
  `data/licenses/Proprietary`, `Cargo.toml` declares `LicenseRef-Proprietary` (SPDX has no
  proprietary id) with `publish = false`, and `deny.toml` ignores private crates.
- `clippy::cargo_common_metadata` is allowed: it demands keywords, categories, and a license,
  which would force placeholder metadata into every project. Pre-gen requires the metadata a
  crates.io release publishes instead.
- Pre-gen rejects `lib` + `release_ci=binaries`, `license=None` + `release_ci=crates.io`,
  `python_interop=none` + non-empty `python_dependencies`, and `release_ci=pypi` without
  `python_interop=extension`. `RELEASE_WORKFLOWS` leaves `(pypi, embedded)` and `(pypi, none)`
  unmapped, so that last check and the table enforce each other.
- `Cargo.toml` ships `{rust_msrv}` and `rust-toolchain.toml` ships `channel = "stable"`.
  `set_rust_version()` rewrites both: the pin from `rustc --version`, the MSRV from `msrv()`,
  which trails the pin by `MSRV_LAG` minors and never goes below `RUST_FLOOR`. The channel must
  stay resolvable.

## Python interop

`set_interop()` copies `data/interop/<mode>/` over the project root, then substitutes each `.md.in`
fragment into `{interop_notes}` and `{interop_rules}` in `README.md`, `data/AGENTS_README.md`, and
the write-code, test-code, cleanup-code, and generate-spec skills. It runs before `set_crate_type()`.

Pick one of three mechanisms:

1. Files that differ wholesale by mode live under `data/interop/<mode>/` and override a shared
   file of the same name (`embedded`'s `crates/cli`)
2. Blocks of prose live in a `.md.in` fragment; only option for files `_copy_without_render`
   ships verbatim (skills, release workflows)
3. Flags or phrases in an otherwise shared file use inline `cookiecutter.python_interop` guards
   (`Cargo.toml`, `mise.toml`, `test.yml`); bind repeated guards once with `{%- set -%}` at the
   top

- Fragments replace the placeholder and its trailing newline, so an empty fragment (`none`'s
  `cleanup-code.md.in`) collapses the line. Every mode needs a fragment for every placeholder; a
  missing file fails at `read_text`, and a renamed or dropped placeholder fails in `read_write()`,
  which raises when the substring is absent.
- `embedded`: `crates/py` links libpython (pyo3 with `auto-initialize`, never `extension-module`).
  No maturin, no wheel, no `cdylib`. Import third-party packages with `import_fn`; do not embed
  first-party `.py` via `include_str!`.
- `none`: no `crates/py`, no pyo3. `crates/cli` is the shared pure-Rust binary at the template
  root (no `build.rs`, no `python` feature, no `Error` enum). `embedded`'s CLI is a separate copy
  that overrides it.
- `extension`: `crates/py` is an abi3 `cdylib` named `_core`, built into a wheel by maturin. The
  importable package is `python/<pkg>/`; boundary tests are in `tests/`. Do not make
  `extension-module` a default feature of `crates/py`: maturin enables it through
  `[tool.maturin] features`. A default would force `--no-default-features` onto every cargo task,
  which cargo applies to every crate. Its CLI is the shared pure-Rust one, like `none`.
- Under `embedded`, `crates/cli` has a default-on `python` feature; `--no-default-features` is a
  pure-Rust binary. The shared CLI has no such feature.
- `NativeScorer` and `NegativeInput` live in `crates/core`. Every consumer reuses them; do not
  copy them per crate.
- `[project.dependencies]` is what the embedded interpreter imports; `scripts/bundle.py` vendors
  them into `dist/python`. Under `none` that list must be empty.
- The generated `pyproject.toml` has no `[build-system]` and sets `[tool.uv] package = false`,
  except under `extension`, where a wheel is the point.
- `stage_python_dlls()` in `embedded`'s `crates/py/build.rs` copies `python3*.dll` beside cargo
  binaries. It is a no-op off Windows and looks removable; it is not. Windows has no rpath.
  `extension`'s `crates/py` sets `test = false` and `doctest = false`, so nothing there loads
  libpython at test time and `test.yml` puts the interpreter on `PATH` under `embedded` alone.

## Testing

Hooks: `mise run all`, or `prek run -a` (same plus whitespace and TOML/YAML).

`test_template_renders_to_well_formed_files` in `hooks/test_post_gen_project.py` renders every
non-verbatim template file for each option combination and parses the TOML, YAML, JSON, and
Python. It is the only local check that a comment edit did not take a Jinja tag with it, since the
root `prek.toml` has to exclude those files from `check-toml`/`check-yaml`.

Template body: generate a project. `license` and `release_ci` select different
Jinja branches and files. Match the Linux CI legs locally:

- `lib`/proprietary
- `both`/MIT/binaries
- `both`/Apache-2.0/crates.io with dependencies
- `both`/none/binaries
- `both`/extension/pypi (builds the wheel and imports it outside the project venv)
- `lib`/BSD-3-Clause/extension/pypi (a wheel with no CLI crate, and the only leg that copies
  BSD-3-Clause)

Windows and macOS exercise bundling (`both`/MIT/binaries). Windows also runs
`both`/extension/pypi, where no test executable loads libpython. Every leg runs `mise run all`
plus `uv run prek run -a`.

The dependencies leg also runs `mise run msrv` and `mise run deny`. It is the only one with
external crates, so it is the only one where a dependency raising its own `rust-version` past
`MSRV_LAG` can show up.

Generation needs `rustup`, `uv`, and `mise` on `PATH`; `check_prerequisites()` probes all three up
front. The post-gen hook resolves the toolchain with `rustc`, runs `uv sync`, builds the workspace,
and trusts and locks the generated `mise.toml`. On hook failure cookiecutter deletes the output;
pass `--keep-project-on-failure` to inspect it.

## Commits

Agents are banned from being authors on commits or PR messages.
Commits or PRs that contravene this directive will be rejected.

Do not leave comments in the code detailing what was changed.
