"""Hooks to run after generating project."""

import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, assert_never

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


type GitProtocol = Literal["git", "https"]
GITHUB_PRIVACY_OPTIONS = ("private", "internal", "public")

# Declared MSRV trails pinned toolchain by MSRV_LAG minors, and never goes below RUST_FLOOR,
# oldest release template's own dependencies build on
RUST_FLOOR = "1.90"
MSRV_LAG = 2
RUST_CHANNEL_PLACEHOLDER = "stable"
RUST_MSRV_PLACEHOLDER = "{rust_msrv}"

DEFAULT_BRANCH = "master"

BUNDLE_SCRIPTS = (
    "scripts/bundle.py",
    "scripts/test_bundle.py",
    "scripts/smoke_bundle.py",
    "scripts/test_smoke_bundle.py",
)

# Platforms mise.lock must cover: every runner generated CI and release workflows use. One
# missing from lockfile is a tool `mise install --locked` cannot verify
LOCK_PLATFORMS = "linux-x64,linux-arm64,macos-arm64,macos-x64,windows-x64"

# Invoking-environment variables that would otherwise capture uv or toolchain pin. Named one by
# one: a `UV_` prefix would also drop index, cache, and proxy settings user needs
INHERITED_ENV = (
    "VIRTUAL_ENV",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
    "UV_PROJECT_ENVIRONMENT",
    "UV_PYTHON",
    "UV_LOCKED",
    "UV_FROZEN",
    "UV_NO_SYNC",
    "RUSTUP_TOOLCHAIN",
    "CARGO_TARGET_DIR",
)

SUCCESS = "\x1b[1;32m"
TERMINATOR = "\x1b[0m"


class CrateType(StrEnum):
    """Workspace layouts: `LIB` is `crates/core` alone, `BOTH` adds CLI binary."""

    LIB = "lib"
    BOTH = "both"


class CodingAgent(StrEnum):
    """Coding agents supported, as lowercased `cookiecutter.json` choices."""

    NONE = "none"
    CLAUDE = "claude"
    CODEX = "codex"


class Interop(StrEnum):
    """Which way Rust and Python call each other, or `NONE` for neither."""

    EMBEDDED = "embedded"
    EXTENSION = "extension"
    NONE = "none"


class ReleaseCi(StrEnum):
    """Release workflows supported; `NONE` is spelled as `cookiecutter.json` writes it."""

    NONE = "None"
    BINARIES = "binaries"
    CRATES_IO = "crates.io"
    PYPI = "pypi"


# Doubles as coherence matrix: an unmapped pair is one `pre_gen_project.py` rejects, so the two
# cannot drift apart
RELEASE_WORKFLOWS = {
    # Only `embedded` ships an interpreter beside binary; rest release executable alone
    (ReleaseCi.BINARIES, Interop.EMBEDDED): "release-binaries.yml",
    (ReleaseCi.BINARIES, Interop.EXTENSION): "release-binaries-pure.yml",
    (ReleaseCi.BINARIES, Interop.NONE): "release-binaries-pure.yml",
    (ReleaseCi.CRATES_IO, Interop.EMBEDDED): "release-crates-io.yml",
    (ReleaseCi.CRATES_IO, Interop.EXTENSION): "release-crates-io.yml",
    (ReleaseCi.CRATES_IO, Interop.NONE): "release-crates-io.yml",
    # Other two `pypi` pairs stay unmapped: only `extension` builds a wheel, and pre-gen
    # rejects rest rather than leaving them to fall through to no release workflow
    (ReleaseCi.PYPI, Interop.EXTENSION): "release-pypi.yml",
}

# Prose that differs per interop mode: fragment file under data/interop/<mode>/fragments/ ->
# file it is substituted into and placeholder it fills. Targets under `data/` are sources
# `setup_coding_agent_files` copies out later, long after `set_interop` has run
INTEROP_FRAGMENTS = {
    "readme.md.in": ("README.md", "{interop_notes}"),
    "agents.md.in": ("data/AGENTS_README.md", "{interop_notes}"),
    "write-code.md.in": ("data/.claude/skills/write-code/SKILL.md", "{interop_rules}"),
    "test-code.md.in": ("data/.claude/skills/test-code/SKILL.md", "{interop_rules}"),
    "cleanup-code.md.in": ("data/.claude/skills/cleanup-code/SKILL.md", "{interop_rules}"),
    "generate-spec.md.in": ("data/.claude/skills/generate-spec/SKILL.md", "{interop_rules}"),
}


def call(cmd: str, check: bool = True, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
    """Run a shell command.

    `cmd` is split on whitespace; arguments containing spaces are not supported.

    Args:
        cmd: command to run
        check: whether to raise when command exits non-zero
        kwargs: keyword arguments to pass to `subprocess.run`

    Returns:
        Completed process
    """
    logger.debug(f"Calling: {cmd}")
    return subprocess.run(cmd.split(), check=check, **kwargs)


def clear_parent_env() -> None:
    """Drop inherited variables that would steer generated project elsewhere."""
    for name in INHERITED_ENV:
        if os.environ.pop(name, None) is not None:
            logger.debug(f"Unset inherited {name}")


def read_write(file_name: str, old: str, new: str) -> None:
    """Replace all occurrences of a substring in a file.

    Args:
        file_name: file to modify
        old: substring to replace
        new: replacement substring

    Raises:
        ValueError: `old` not in file, so a renamed placeholder cannot pass silently
    """
    path = Path(file_name)
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise ValueError(f"{old!r} not found in {file_name}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def rust_version() -> str:
    """Read version of toolchain rustup resolved for this project.

    Returns:
        Resolved rust version, e.g. "1.97.1"

    Raises:
        ValueError: version cannot be parsed from `rustc --version`
    """
    result = call("rustc --version", capture_output=True, text=True)
    if not (version := re.search(r"\d+\.\d+\.\d+", result.stdout)):
        raise ValueError(f"Unable to parse rust version from {result.stdout!r}")
    return version.group()


# `scripts/bump_toolchain.py:next_msrv` repeats this rule for generated projects; keep the two
# in agreement
def msrv(pinned: str, floor: str = RUST_FLOOR) -> str:
    """Derive MSRV to declare from toolchain being pinned.

    Args:
        pinned: exact version being pinned, e.g. "1.97.1"
        floor: oldest release template supports

    Returns:
        MSRV to declare, as `major.minor`

    Examples:
        >>> msrv("1.97.1", floor="1.90")
        '1.95'
        >>> msrv("1.91.0", floor="1.90")
        '1.90'
        >>> msrv("1.90.0", floor="1.90")
        '1.90'
        >>> msrv("2.0.0", floor="1.90")
        '2.0'
        >>> msrv("2.1.0", floor="1.90")
        '2.0'
    """
    major, minor, *_ = (int(part) for part in pinned.split("."))
    floor_parts = tuple(int(part) for part in floor.split("."))
    version = max((major, max(minor - MSRV_LAG, 0)), floor_parts)
    return f"{version[0]}.{version[1]}"


def set_rust_version() -> None:
    """Pin resolved toolchain, and declare an older MSRV alongside it."""
    version = rust_version()
    declared = msrv(version)
    logger.info(f"Pinning rust {version=} with msrv={declared}")

    read_write("rust-toolchain.toml", RUST_CHANNEL_PLACEHOLDER, version)
    read_write("Cargo.toml", RUST_MSRV_PLACEHOLDER, declared)
    read_write("README.md", RUST_MSRV_PLACEHOLDER, declared)


def set_license(license_name: str) -> None:
    """Copy selected license to LICENSE and fill in year and author.

    Args:
        license_name: SPDX license id, or "None" for no license

    Raises:
        ValueError: no matching license file
    """
    if license_name == "None":
        logger.debug("No license set")
        return

    licenses = {lic.name for lic in Path("data/licenses").iterdir()}
    if license_name not in licenses:
        raise ValueError(f"{license_name=} not available; select from:\n{licenses}")

    shutil.copy(Path("data/licenses") / license_name, "LICENSE")
    read_write("LICENSE", "{year}", f"{datetime.now().year}")
    read_write("LICENSE", "{author_name}", "{{cookiecutter.author_name}}")

    logger.debug(f"Set {license_name=}")


def set_interop(interop: str) -> None:
    """Copy interop mode's files over project root and substitute its prose fragments.

    Runs before `set_crate_type`, so crate-type prune sees materialized files.

    Args:
        interop: "embedded", "extension", or "none"
    """
    kind = Interop(interop.lower())
    logger.info(f"Setting up {kind.value} Python interop")

    mode = Path("data/interop") / kind.value
    # Fragments are substituted below, not shipped
    shutil.copytree(mode, ".", dirs_exist_ok=True, ignore=shutil.ignore_patterns("fragments"))

    for fragment, (target, placeholder) in INTEROP_FRAGMENTS.items():
        # Substituting placeholder's newline to let an empty fragment collapse
        body = (mode / "fragments" / fragment).read_text(encoding="utf-8").removesuffix("\n")
        read_write(target, f"{placeholder}\n", f"{body}\n" if body else "")


def set_crate_type(crate_type: str) -> None:
    """Drop CLI crate and bundle scripts from a library-only workspace.

    Args:
        crate_type: "lib" or "both"
    """
    kind = CrateType(crate_type.lower())
    logger.info(f"Setting up a {kind.value} workspace")

    if kind is CrateType.LIB:
        shutil.rmtree("crates/cli", ignore_errors=True)
        for script in BUNDLE_SCRIPTS:
            Path(script).unlink(missing_ok=True)


def set_release_ci(release_ci: str, python_interop: str) -> None:
    """Rename selected release workflow to release.yml and delete others.

    Args:
        release_ci: "binaries", "crates.io", "pypi", or "None"
        python_interop: "embedded", "extension", or "none"

    Raises:
        ValueError: release_ci or python_interop is not supported
    """
    kind = ReleaseCi(release_ci)
    interop = Interop(python_interop.lower())
    workflows = Path(".github/workflows")
    keep = RELEASE_WORKFLOWS.get((kind, interop))

    for name in set(RELEASE_WORKFLOWS.values()):
        if name != keep:
            (workflows / name).unlink(missing_ok=True)

    if keep:
        (workflows / keep).rename(workflows / "release.yml")


def add_dependencies(
    package: str = "{{cookiecutter.crate_name}}",
    dependencies: str = """{{cookiecutter.cargo_dependencies}} """.strip(),
    dev_dependencies: str = """{{cookiecutter.cargo_dev_dependencies}} """.strip(),
) -> None:
    """Add requested dependencies to core crate with `cargo add`.

    Args:
        package: workspace member to add to (`crates/core`)
        dependencies: space-separated `cargo add` spec
        dev_dependencies: space-separated `cargo add --dev` spec
    """
    if dependencies:
        call(f"cargo add -p {package} {dependencies}")
    if dev_dependencies:
        call(f"cargo add --dev -p {package} {dev_dependencies}")


def add_python_dependencies(
    dependencies: str = """{{cookiecutter.python_dependencies}} """.strip(),
) -> None:
    """Add requested runtime packages with `uv add --no-sync`.

    Lands in `[project.dependencies]`, which embedded interpreter imports and `scripts/bundle.py`
    vendors.

    Args:
        dependencies: space-separated `uv add` spec
    """
    if dependencies:
        logger.info(f"Adding Python dependencies: {dependencies}")
        call(f"uv add --no-sync {dependencies}")


def check_program(program: str, install_str: str, **run_kwargs: Any) -> None:
    """Check that a program is installed.

    Args:
        program: command that exits zero when program is installed, e.g. `rustup --version`
        install_str: where to get program from, for error message
        run_kwargs: keyword arguments to pass to subprocess.run

    Raises:
        OSError: program not installed
        RuntimeError: program exited non-zero
    """
    try:
        call(program, stdout=subprocess.DEVNULL, **run_kwargs)
    except FileNotFoundError as e:
        raise OSError(f"{program} is not installed; install with `{install_str}`") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"`{program}` exited with {e.returncode}") from e


def pinned_interpreter() -> str:
    """Find interpreter uv runs project with.

    Returns:
        Absolute path of interpreter
    """
    result = call("uv python find", capture_output=True, text=True)
    return result.stdout.strip()


def build_workspace(python_interop: str) -> None:
    """Build workspace, pinning interpreter `crates/py` links against under `embedded`.

    Args:
        python_interop: "embedded", "extension", or "none"

    Raises:
        ValueError: python_interop not supported
    """
    interop = Interop(python_interop.lower())

    match interop:
        case Interop.EMBEDDED:
            interpreter = pinned_interpreter()
            logger.info(f"Building workspace against {interpreter}")
            os.environ["PYO3_PYTHON"] = interpreter
        case Interop.EXTENSION | Interop.NONE:
            logger.info("Building workspace")
        case _:
            assert_never(interop)

    call("uv run cargo build --workspace")

    if interop is Interop.EXTENSION:
        logger.info("Building extension module into venv")
        call("uv run maturin develop --uv")


def check_prerequisites(github_setup: str = "{{cookiecutter.github_setup}}") -> None:
    """Check that tools generation needs are installed, before anything is built.

    Args:
        github_setup: repository privacy, or "None" to skip GitHub CLI check
    """
    check_program("rustup --version", "https://rustup.rs")
    check_program("uv --version", "https://docs.astral.sh/uv/getting-started/installation/")
    check_program("mise --version", "https://mise.jdx.dev/installing-mise.html")

    if github_setup != "None":
        check_program("gh --version", "https://cli.github.com/")


def trust_mise() -> None:
    """Trust mise.toml, so its tasks run and its environment applies."""
    call("mise trust")


def lock_dev_tools() -> None:
    """Resolve dev tools in mise.toml to exact versions and checksums in mise.lock."""
    logger.info(f"Locking dev tools for {LOCK_PLATFORMS}")
    call(f"mise lock --platform {LOCK_PLATFORMS}")


def setup_coding_agent_files(agent: str) -> None:
    """Write selected agent's files; AGENTS.md ships even when none was chosen.

    Args:
        agent: coding agent name ("claude", "codex", or "none")

    Raises:
        ValueError: agent not supported
    """
    coding_agent = CodingAgent(agent.lower())
    shutil.copy(Path("data/AGENTS_README.md"), Path("AGENTS.md"))

    if coding_agent is CodingAgent.NONE:
        return

    logger.info(f"Setting up files for {coding_agent.value}")
    shutil.copytree("data/.claude", ".claude")
    shutil.copy(Path("data/STATE.md"), Path("STATE.md"))

    match coding_agent:
        case CodingAgent.CLAUDE:
            Path("CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
            cmd = "claude /init"
        case CodingAgent.CODEX:
            Path(".claude/settings.json").unlink()
            cmd = "codex exec 'Read AGENTS.md and update it'"
        case _:
            assert_never(coding_agent)

    logger.info(f"Run `{cmd}` to finish agent setup.")


def format_sources() -> None:
    """Format generated sources, before project's own hooks check them."""
    call("cargo fmt --all")
    call("uv run ruff format")
    call("uv run rumdl fmt .")


def verify_generated_project() -> None:
    """Run generated project's hooks over tree, warning on failure.

    A raise would have cookiecutter delete an otherwise finished project.
    """
    call("git add .")
    if call("uv run prek run -a --stage pre-push", check=False).returncode:
        logger.warning("Generated project fails its own hooks; see above")


def git_initial_commit() -> None:
    """Make initial commit, skipping hooks `verify_generated_project` just ran."""
    call("git add .")
    call("git commit --no-verify -m Setup")


def setup_remote(
    remote: str = "origin",
    privacy: str = "{{cookiecutter.github_setup}}",
    url: str = "{{cookiecutter.project_url}}",
) -> None:
    """Add remote, creating repository on GitHub when a privacy level was chosen.

    Args:
        remote: name for remote
        privacy: repository privacy, or "None" to add remote alone
        url: URL of remote when no repository is created
    """
    if privacy != "None":
        github_setup(privacy, remote)
    else:
        git_add_remote(remote, url)


def git_add_remote(remote: str, url: str, protocol: GitProtocol = "git") -> None:
    """Add a remote to git repository.

    Args:
        remote: name for remote
        url: HTTPS URL of remote
        protocol: transport to address remote with
    """
    if protocol == "git":
        _, _, hostname, path = url.split("/", 3)
        url = f"{protocol}@{hostname}:{path}"

    call(f"git remote add {remote} {url}")


def github_setup(
    privacy: str,
    remote: str = "origin",
    default_branch: str = DEFAULT_BRANCH,
    owner: str = "{{cookiecutter.github_username}}",
    name: str = "{{cookiecutter.crate_name}}",
) -> None:
    """Create repository on GitHub with GitHub CLI.

    Failure is logged rather than raised: cookiecutter deletes output directory when a hook
    raises, and project itself is finished and committed by this point.

    Args:
        privacy: repository visibility, one of "private", "internal", or "public"
        remote: name of remote to add
        default_branch: name of default branch for upstream
        owner: user or organization to create repository under
        name: name of repository

    Raises:
        ValueError: privacy option is not valid
    """
    if privacy not in GITHUB_PRIVACY_OPTIONS:
        raise ValueError(f"{privacy=} not in {GITHUB_PRIVACY_OPTIONS}")

    create = f"gh repo create {owner}/{name} --{privacy} --remote {remote} --source . --push"

    try:
        call(create)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating GitHub repository: {e}\nRetry with: {create}")
        return

    try:
        call(f"git config branch.{default_branch}.remote {remote}")
        call(f"git config branch.{default_branch}.merge refs/heads/{default_branch}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting upstream to {default_branch}: {e}")


def notes(release_ci: str = "{{cookiecutter.release_ci}}") -> None:
    """Print follow-up steps a release workflow needs.

    Args:
        release_ci: selected release workflow
    """
    if release_ci == "crates.io":
        logger.info(
            """
Publishing uses Trusted Publishing (OIDC). Publish first version by hand with `cargo publish`,
then add this repository as a trusted publisher on crate at https://crates.io"""
        )
    elif release_ci == "pypi":
        logger.info(
            """
Publishing uses Trusted Publishing (OIDC). Add a pending publisher at
https://pypi.org/manage/account/publishing/ before first `v*` tag, naming this GitHub repository
and `release.yml` as workflow.

See https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
"""
        )


def main() -> None:
    """Run post-generation hooks."""
    clear_parent_env()
    check_prerequisites()
    set_license("{{cookiecutter.license}}")
    set_interop("{{cookiecutter.python_interop}}")
    set_crate_type("{{cookiecutter.crate_type}}")
    set_release_ci("{{cookiecutter.release_ci}}", "{{cookiecutter.python_interop}}")

    call(f"git init -b {DEFAULT_BRANCH}")

    set_rust_version()

    add_dependencies()
    call("cargo generate-lockfile")
    add_python_dependencies()
    call("uv sync")

    build_workspace("{{cookiecutter.python_interop}}")
    trust_mise()
    lock_dev_tools()

    call("uv run prek install")
    setup_coding_agent_files("{{cookiecutter.coding_agent}}")
    shutil.rmtree("data")

    format_sources()

    verify_generated_project()
    git_initial_commit()

    setup_remote()

    notes()
    logger.info(f"{SUCCESS}Project successfully initialized{TERMINATOR}")


if __name__ == "__main__":
    main()
