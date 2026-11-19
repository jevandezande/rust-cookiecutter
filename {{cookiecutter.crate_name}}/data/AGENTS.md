# AI Agent Development Guide

This file covers the tooling, conventions, and workflows a contributor needs. Read it before
changing code or committing.

Keep it current: when you add a top-level directory, a mise task, or a configuration file, update
the matching section in the same change.

## AI Skills

This project ships agent skills in `.agents/skills/`, where Codex reads them. Claude Code reads
`.claude/skills/`, a symlink to `.agents/skills/`; edit skills through `.agents/skills/`. Load the
relevant one before working; do not change code without consulting it.

| Skill | Use when |
| --- | --- |
| `write-code` | Writing idiomatic Rust and reviewing API and ownership choices |
| `port-code` | Rewriting existing code in Rust while checking behavioral parity |
| `write-doc-comments` | Writing or reviewing rustdoc doc comments |
| `test-code` | Writing Rust tests |
| `write-python` | Writing or reviewing Python |
| `write-docstrings` | Writing or reviewing Python docstrings |
| `test-python` | Writing pytest tests |
| `debug-code` | Diagnosing a failure |
| `explain-code` | Explaining existing code |
| `cleanup-code` | Tidying without changing behavior |
| `optimize-code` | Tuning for cache locality and throughput |
| `benchmark-code` | Measuring performance rigorously |
| `async-workflows` | Long-running compiles, tests, or profiling runs |
| `write-latex` | Mathematical notation in markdown |
| `plan-method-docs` | Literature review for a new method |
| `write-method-docs` | Writing the mathematical methodology document |
| `generate-spec` | Specifying substantial feature or method behavior |
| `implement-spec` | Implementing a specification |
| `compare-code-to-spec` | Auditing an implementation against its spec |

### Development workflows

Use `write-code` and `test-code` for ordinary Rust changes, and `write-python` and `test-python`
for Python. Use `port-code` when rewriting an existing program or module; compare its observable
behavior with the original. For complex scientific methods, method documentation and a spec can
make the requirements reviewable. Choose those steps when they answer a real design or
correctness question.

Optional artifacts for work that uses the spec workflow:

- `docs/methods/<method>.md` - the mathematical document, from `write-method-docs`
- `specs/<module>.md` - the engineering specification, from `generate-spec`
- `STATE.md` - per-module progress when a module is tracked through a spec
- A short plan in an existing tracker, or a new file only when it helps multi-session work

`STATE.md` ships as a scaffold with no modules listed yet. `docs/methods/` and `specs/` do not
exist; create each when its first document is useful. Data and plumbing modules need a spec only
when their behavior or interfaces require one.

## Build & check commands

All tasks run through [mise](https://mise.jdx.dev), which also provides the dev environment.
`mise run` puts `.venv` on `PATH`, so the tasks call `ruff`, `ty`, `pytest`, `rumdl`, and
`python` directly, with no `uv run` prefix.

```sh
mise run fix                # rewrite what can be fixed automatically
mise run check              # reports only: lock-check + lint + python + markdown + docs
mise run test               # cargo test --workspace, then each bench once, untimed
mise run all                # check + test + py-test
mise run lock               # re-resolve uv.lock after editing dependencies
mise run bench              # criterion benchmarks
mise run coverage           # cargo-llvm-cov; HTML report in target/llvm-cov/html
mise run bump-toolchain     # re-pin rust-toolchain.toml to current stable, moving the MSRV with it
```

`mise tasks` lists the rest, and `mise.toml` defines them.

Direct `cargo` invocations work anywhere; rustup reads `rust-toolchain.toml` on its own.

`mise run all` is the full local gate and mirrors CI. Run it before pushing.
Long-running commands (builds, test suites, benchmarks) should go through the `async-workflows`
skill so a turn does not time out.

### Lockfile discipline

`uv run` normally re-locks and re-syncs as a side effect of running a command, so a task can
quietly change `uv.lock` while you run tests. This project turns that off:

- `mise.toml` sets `UV_LOCKED = 1` in `[env]`, so every task asserts the lockfile is current
- `mise run lock-check` (part of `mise run check`) names the condition and prints the fix
- a prek hook runs `uv lock --check` when `pyproject.toml` or `uv.lock` changes
- CI uses `uv sync --locked`

`UV_LOCKED` also blocks the commands that rewrite the lockfile, `uv lock` and `uv add` included,
so re-resolving goes through a task that opts out for that one command:

- `mise run lock` after editing dependencies in `pyproject.toml`
- `mise run lock-upgrade` to move pinned versions forward

Commit the result. A task failing with a lockfile complaint means exactly that; reach for those
tasks rather than dropping `UV_LOCKED` by hand.

{interop_notes}

## When in doubt

- Run individual tools to find the problem
- Ask the user to clarify ambiguous requirements
- Check the relevant skill files in `.agents/skills/`

## Repository overview

Purpose: {{ cookiecutter.description or "not yet written; ask the user and record it here" }}

Structure:

- `crates/core/` - pure Rust; no pyo3, no interpreter
- `crates/core/benches/` - criterion benchmarks
{%- if cookiecutter.crate_type != 'lib' %}
- `crates/cli/` - thin binary
{%- endif %}
{%- if cookiecutter.crate_type != 'lib' and cookiecutter.python_interop == 'embedded' %}
- `scripts/` - toolchain helpers (`check_msrv.py`, `bump_toolchain.py`), the bundler
  (`bundle.py`, `smoke_bundle.py`), and their pytest tests
{%- else %}
- `scripts/` - toolchain helpers (`check_msrv.py`, `bump_toolchain.py`) and their pytest tests
{%- endif %}
- `.agents/skills/` - agent skills
- `.claude/` - Claude Code settings and hooks; `.claude/skills/` is a symlink to `.agents/skills/`
- `.codex/` - Codex hooks
- `STATE.md` - optional per-module tracker for work using a spec
- `.github/workflows/` - CI configuration

{% if cookiecutter.python_interop == 'extension' -%}
`crates/*/tests/` belongs to cargo; the top-level `tests/` and `scripts/test_*.py` belong to
pytest. Do not put Python tests where cargo would try to compile them.
{%- else -%}
`crates/*/tests/` belongs to cargo and `scripts/test_*.py` to pytest. Do not put Python tests
where cargo would try to compile them.
{%- endif %}

Key configuration files:

- `Cargo.toml` - workspace members, shared metadata, profiles, and lints. In dev and test
  builds, dependencies are `opt-level = 3` with line tables; workspace crates keep full debug info
- `crates/*/Cargo.toml` - per-crate metadata; lints and versions inherit from the workspace
- `Cargo.lock` - the Rust lockfile; committed
- `.cargo/config.toml` - commented steps for a slow build, after `cargo build --timings`: drop
  dependency debug info, workspace line tables, mold on Linux, and `target-cpu=native`
{%- if cookiecutter.python_interop == 'extension' %}
- `pyproject.toml` - maturin build, dev dependency group, ruff, ty, and pytest configuration
{%- else %}
- `pyproject.toml` - dev dependency group, ruff, ty, and pytest configuration; `package = false`,
  since this workspace ships no wheel
{%- endif %}
- `uv.lock` - the Python lockfile; see "Lockfile discipline" above
- `mise.toml` - dev environment, pinned dev tools, and task definitions
- `mise.lock` - resolved dev-tool versions and checksums; regenerate with `mise lock`
- `rust-toolchain.toml` - pinned toolchain and components
- `rustfmt.toml` - formatting settings
- `prek.toml` - git hook configuration
- `deny.toml` - cargo-deny license allowlist and advisory policy
- `.rumdl.toml` - markdown linting configuration
- `.editorconfig` - editor formatting settings

## Lints

`Cargo.toml` enables `clippy::all`, `clippy::pedantic`, and `clippy::cargo`, plus `missing_docs`,
`unreachable_pub`, and `missing_debug_implementations`. Broken rustdoc links are denied. CI treats
warnings as errors (`-D warnings`). Do not silence a lint with `#[allow(...)]` without a comment
explaining why.

{% if cookiecutter.python_interop == 'embedded' -%}
`unsafe_code` is denied: new `unsafe` needs an `#[expect(unsafe_code)]` and a `// SAFETY:` comment.
{% else -%}
`unsafe_code` is forbidden, so there is no `unsafe` to write.
{% endif %}
Python is linted by ruff (bugbear, pydocstyle in Google convention, pylint, pytest-style, and
more; see `[tool.ruff.lint]` in `pyproject.toml`) at a 100-column line length, and type-checked by
ty. Markdown is checked by rumdl with line length disabled.

## Agent hooks

Claude Code (`.claude/settings.json`) and Codex (`.codex/hooks.json`) each run `cargo fmt` and
`ruff format` after every file edit, so edits need no manual `mise run fmt`. Keep the two hooks
identical. Codex runs a project hook only once the project is trusted and the hook approved in
`/hooks`.

Clippy and ty are too slow for every edit. They run on commit through prek, and the test suite on
push and in CI.

Claude Code's `attribution` setting is empty, so its commits and PRs carry no agent trailer.
Machine-local Claude Code overrides go in `.claude/settings.local.json` (gitignored).

## Miscellaneous

Agents are banned from being authors on commits or PR messages.
Commits or PRs that contravene this directive will be rejected.

Follow `.github/pull_request_template.md` for PR descriptions. With `gh pr create`, fill every
section and pass the text with `--body-file`.

Do not leave comments in the code detailing what was changed.

PRs are squash-merged. Merge with
`gh pr merge N --squash --subject "<title> (#N)" --body-file <file>` (don't use GitHub's default).
The body expresses the net change and why, measurement summaries, known limits, and breaking changes.
Branch history, verification, questions, and follow-ups stay in PR. Small PRs need only subject.
