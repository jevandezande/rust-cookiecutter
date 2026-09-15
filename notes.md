# Notes

Supplement to the [README](README.md): configuration, how generated projects work, and optional
tools.

## Prerequisites

Install `mise`, `rustup`, and `uv` following the README [Setup](README.md#setup) section.

- The generated project cannot supply mise: the hook has to trust `mise.toml` before the
  project can install its own tools. See [Mise](#mise)
- The generated `mise.toml` pins uv, but the hook runs `uv sync` before that config is trusted,
  so a global uv is required; README uses `mise use -g uv`
- mise does not manage rustup; rust-analyzer, CI, and contributors without mise all read
  `rust-toolchain.toml`, so it stays the single toolchain pin

## Cookiecutter

Use `uvx` to fetch and run cookiecutter on demand:

```sh
uvx cookiecutter gh:jevandezande/rust-cookiecutter
```

To keep it around:

```sh
uv tool install cookiecutter
```

## When generation fails

Cookiecutter deletes the output directory when a hook raises. Keep it with:

```sh
uvx cookiecutter gh:jevandezande/rust-cookiecutter --keep-project-on-failure
```

## Configuring Rust Cookiecutter

Make a [config file](https://cookiecutter.readthedocs.io/en/stable/advanced/user_config.html)
with default settings (see [template_config.yml](template_config.yml)). Save it as
`.cookiecutterrc`, or pass it with `--config-file template_config.yml`.

## Adding project dependencies

Rust dependencies go to `cargo add -p <crate_name>` and land in `crates/core`. Use cargo's own
syntax: a space-separated list where `@` pins a version, e.g. `serde@1.0 rayon anyhow@^1`. Bare
names resolve to the latest compatible release. To select features, pass `tokio@1 --features full`
for a single dependency, or edit `Cargo.toml` afterward.

Python packages go to `uv add --no-sync` and land in `[project.dependencies]`. Use `uv add`
syntax, e.g. `numpy scipy mace-torch>=0.3`. The generated `PyScorer` still calls `math.sqrt`;
point `import_fn` at the package after generation.

## Git remote and GitHub

Generation initializes a repository, commits, and adds an `origin` remote. With `github_setup`
set, the GitHub CLI creates `github_username/crate_name`, adds it as `origin`, and pushes.
Otherwise `origin` is `project_url` in its `git@` form, and nothing is pushed.

## Python in a Rust project

`python_interop` picks which direction Rust and Python call each other, and the answer changes
what a generated project is.

- `none`: pure Rust
- `embedded`: Rust starts a CPython interpreter and imports third-party packages through
  `crates/py`, the only crate that links libpython
- `extension`: `crates/py` compiles to an abi3 `cdylib` named `_core`, which `python/<package>/`
  imports and a wheel ships. `pyproject.toml` gains a maturin `[build-system]`, `package = true`,
  and a version read from `Cargo.toml`. `mise run develop` builds the module into `.venv` and
  `mise run wheel` produces the wheel.

In every mode `crates/*/tests/` belongs to cargo, not pytest.

## Project Tools

### Act

[act](https://github.com/nektos/act) runs GitHub Actions locally in Docker:

```sh
act push
act pull_request
act schedule
```

Install with `brew install act`, or as a GitHub CLI extension:

```sh
gh extension install nektos/gh-act
```

### GitHub CLI

[GitHub CLI](https://cli.github.com/) creates the repository on GitHub. Useful extensions:

- [copilot](https://github.com/github/gh-copilot) - chat interface for questions about the command line
- [dash](https://github.com/dlvhdr/gh-dash) - displays a dashboard with pull requests and issues
- [gh-f](https://github.com/gennaro-tedesco/gh-f) - fuzzy finder for gh-cli
- [gh-notify](https://github.com/meiji163/gh-notify) - shows your GitHub notifications
- [markdown-preview](https://github.com/yusukebe/gh-markdown-preview) - renders markdown documents in your browser
- [poi](https://github.com/seachicken/gh-poi) - safely cleans up old local branches

The README Setup section installs it with webi. Package-manager alternatives are under
[Alternative installation methods](#alternative-installation-methods).

### Mise

[mise](https://mise.jdx.dev) handles:

- Dev environment
- Task running
- Tool provisioning

It needs a shell hook in your `.zshrc`, `.bashrc`, or `.profile` (swap `zsh` for your shell):

```sh
eval "$(mise activate zsh)"
```

`mise.lock` pins the resolved version of every tool. The post-generation hook writes it for each
platform the generated CI and release workflows run on. To take newer tools:

```sh
mise lock --bump   # re-resolve `latest` against current releases
```

### Prek

[prek](https://prek.j178.dev) runs formatting, linting, and other hooks on `git commit` and
`git push`, and the test suites on `git push` alone. `default_install_hook_types` in the generated
`prek.toml` makes `prek install` write the pre-push shim as well as the pre-commit one.

It ships in the generated project's dev dependency group, so it needs no global install. If you
want one anyway:

```sh
uv tool install prek
```

### Performance tooling

Wired in:

- [criterion](https://github.com/bheisler/criterion.rs): benchmarks in `crates/core/benches`,
  plus `crates/py/benches` under `python_interop=embedded`, via `mise run bench`
- `[profile.release]`: thin LTO and `codegen-units = 1`
- `[profile.profiling]`: release plus debug symbols, via `mise run profile-build`
- `.cargo/config.toml`: commented-out fast-linker and `target-cpu=native` settings
- [cargo-deny](https://github.com/EmbarkStudios/cargo-deny): license and advisory auditing in CI
  (`mise run deny` locally); pinned in the generated `mise.toml`
- [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov): coverage, via `mise run coverage`

Not wired in, but easy to add:

- [samply](https://github.com/mstange/samply): sampling profiler that reads the profiling profile
- [cargo-nextest](https://nexte.st/): faster test runner
- [cargo-machete](https://github.com/bnjbvr/cargo-machete): finds unused dependencies

### Alternative installation methods

Use these instead of the README's `curl` and `mise use -g` commands.

#### Cookiecutter

```sh
# Apt
apt install cookiecutter
# Brew
brew install cookiecutter
```

#### GitHub CLI

```sh
# Apt
apt install gh
# Brew
brew install gh
```

#### Mise

```sh
# Brew
brew install mise
# Apt (Debian/Ubuntu), see https://mise.jdx.dev/installing-mise.html for the apt repo setup
apt install mise
```

#### Prek

```sh
# Brew
brew install prek
```

#### Uv

```sh
# Brew
brew install uv
```
