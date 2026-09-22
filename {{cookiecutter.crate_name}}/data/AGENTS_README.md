# AI Agent Development Guide

This file is agent onboarding, not finished project documentation. A coding agent rewrites the
`{AGENT: ...}` placeholders on first use. Until then, treat the checklist as instructions for
that agent.

It covers the tooling, conventions, and workflows a contributor needs.

## How to use this document

### When to read this file

- First time working on this repository
- Before making any code changes or commits
- When unsure about code conventions or tooling

### Understanding {AGENT: ...} directives

- Directives in curly braces starting with "AGENT:" are instructions for you
- Execute them when first reading this file
- Replace each directive with the actual information
- Directives marked "must" are required; others are recommended
- A cookiecutter template generated this file and pre-filled some configuration. Treat it as the
  start of a new project, not as a template, and ask questions where needed

## Initial setup checklist

Generation already created `.venv` with `uv sync`, built the workspace, installed the prek hooks,
and ran them over the tree, so the environment needs no verification.

1. {AGENT: You will update this file. Follow the directives; do not simplify or delete, only improve}
2. {AGENT: Read README.md and confirm the project purpose with the user}
3. {AGENT: Read Cargo.toml, pyproject.toml, and mise.toml, and update the repository-specific information below}
4. {AGENT: After setup, tell the user about any discrepancies found}
5. {AGENT: Delete this checklist and the "Understanding {AGENT: ...} directives" section}

{% if cookiecutter.coding_agent != 'None' -%}

## AI Skills

This project ships agent skills in `.claude/skills/`. Load the relevant one before working;
do not change code without consulting it.

| Skill | Use when |
| --- | --- |
| `write-code` | Writing idiomatic, high-performance Rust |
| `write-doc-comments` | Writing or reviewing rustdoc doc comments |
| `test-code` | Writing tests |
| `debug-code` | Diagnosing a failure |
| `explain-code` | Explaining existing code |
| `cleanup-code` | Tidying without changing behavior |
| `optimize-code` | Tuning for cache locality and throughput |
| `benchmark-code` | Measuring performance rigorously |
| `async-workflows` | Long-running compiles, tests, or profiling runs |
| `write-latex` | Mathematical notation in markdown |
| `plan-method-docs` | Literature review for a new method |
| `write-method-docs` | Writing the mathematical methodology document |
| `generate-spec` | Turning a method doc into a software specification |
| `implement-spec` | Implementing a specification |
| `compare-code-to-spec` | Auditing an implementation against its spec |

### Development pipeline

For non-trivial numerical work, each module follows: Math Doc → Spec → Tests → Code. The skills
above handle each phase in order. {AGENT: if this project is not mathematical or numerical, note
that this pipeline does not apply and the spec and method-doc skills are unused}

What each phase reads and writes:

- `docs/methods/<method>.md` - the mathematical document, from `write-method-docs`
- `specs/<module>.md` - the engineering specification, from `generate-spec`
- `STATE.md` - per-module progress; `generate-spec` and `implement-spec` both update it
- `PLAN.md` and `TODO.md` - scratch files `implement-spec` writes at the root and deletes once
  the module is done

`STATE.md` ships as a scaffold with no modules listed yet. `docs/methods/` and `specs/` do not
exist; create each when its first document lands. Data and plumbing modules skip the method
document and go straight to a spec.

{% endif -%}

## Build & check commands

All tasks run through [mise](https://mise.jdx.dev), which also provides the dev environment.
`mise run` puts `.venv` on `PATH`, so the tasks call `ruff`, `ty`, `pytest`, `rumdl`, and
`python` directly, with no `uv run` prefix.

```sh
mise tasks                  # list every task
mise run build              # cargo build --workspace
mise run test               # cargo test --workspace
mise run fmt                # cargo fmt --all
mise run fmt-check          # cargo fmt --all --check
mise run clippy             # cargo clippy --workspace --all-targets -- -D warnings
mise run clippy-fix         # clippy with --fix
mise run docs               # cargo doc --workspace --no-deps, warnings as errors
mise run msrv               # check the workspace against the MSRV in Cargo.toml
mise run bump-toolchain     # re-pin rust-toolchain.toml to current stable, moving the MSRV with it
mise run lint               # fmt + clippy
mise run bench              # criterion benchmarks
mise run profile-build      # release build with debug symbols, for perf/samply
mise run coverage           # cargo-llvm-cov; HTML report in target/llvm-cov/html
mise run coverage-summary   # coverage as a table on stdout
mise run lock-check         # uv lock --check
mise run lock               # re-resolve uv.lock after editing dependencies
mise run lock-upgrade       # bump uv.lock to the newest compatible versions
{% if cookiecutter.crate_type != 'lib' and cookiecutter.python_interop == 'embedded' -%}
mise run bundle             # self-contained bundle in dist/: the binary plus its interpreter
mise run smoke-bundle       # prove the bundle ignores an ambient VIRTUAL_ENV
{% endif -%}
{% if cookiecutter.python_interop == 'extension' -%}
mise run develop            # maturin develop --uv; build the extension module into .venv
mise run wheel              # maturin build --release --out dist
{% endif -%}
mise run py-fmt             # ruff format
mise run py-fmt-check       # ruff format --check
mise run py-lint            # ruff check
mise run py-types           # ty check
{% if cookiecutter.python_interop == 'extension' -%}
mise run py-test            # pytest (depends on develop)
{% else -%}
mise run py-test            # pytest
{% endif -%}
mise run md-fmt             # rumdl fmt .
mise run md-fmt-check       # rumdl fmt --check .
mise run md-check           # rumdl check .
mise run deny               # cargo-deny; the binary comes from mise.toml
mise run fix                # rewrite what can be fixed automatically
mise run check              # reports only: lock-check + lint + python + markdown + docs
mise run all                # check + test + py-test
```

Direct `cargo` invocations work anywhere; rustup reads `rust-toolchain.toml` on its own.

`mise run all` is the full local gate and mirrors CI. Run it before pushing.
{%- if cookiecutter.coding_agent != 'None' %}
Long-running commands (builds, test suites, benchmarks) should go through the `async-workflows`
skill so a turn does not time out.
{%- endif %}

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
{%- if cookiecutter.coding_agent != 'None' %}
- Check the skills loaded with the `skill` tool
{%- endif %}

## Repository overview

Purpose: {AGENT must read from README.md and confirm with user}

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
{%- if cookiecutter.coding_agent != 'None' %}
- `.claude/skills/` - agent skills
- `STATE.md` - per-module progress tracker; `generate-spec` and `implement-spec` read and update it
{%- endif %}
- `.github/workflows/` - CI configuration
- {AGENT: list other important folders and confirm with user}

{% if cookiecutter.python_interop == 'extension' -%}
`crates/*/tests/` belongs to cargo; the top-level `tests/` and `scripts/test_*.py` belong to
pytest. Do not put Python tests where cargo would try to compile them.
{%- else -%}
`crates/*/tests/` belongs to cargo and `scripts/test_*.py` to pytest. Do not put Python tests
where cargo would try to compile them.
{%- endif %}

Key configuration files:

- `Cargo.toml` - workspace members, shared metadata, profiles, and lint configuration
- `crates/*/Cargo.toml` - per-crate metadata; lints and versions inherit from the workspace
- `Cargo.lock` - the Rust lockfile; committed
- `.cargo/config.toml` - commented-out linker and target-cpu settings
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

{% if cookiecutter.coding_agent == 'Claude' -%}

## Claude Code integration

### Auto-formatting hooks

A PostToolUse hook runs `cargo fmt` and `ruff format` after every Edit or Write, so edits are
formatted automatically.

Clippy and ty are not in that hook, since they are too slow to run on every edit. They run on
commit through prek and in CI.

To change the shared hooks, or to pre-approve permissions for this project, edit
`.claude/settings.json`. Machine-local overrides go in `.claude/settings.local.json` (gitignored).

### Workflow impact

1. File edits are formatted automatically; no manual `mise run fmt` needed
2. Pre-commit checks still run on commit, and the test suite on push
3. `includeCoAuthoredBy` is off, so commits carry no agent co-author trailer

{% endif -%}

## Miscellaneous

Agents are banned from being authors on commits or PR messages.
Commits or PRs that contravene this directive will be rejected.

Do not leave comments in the code detailing what was changed.
