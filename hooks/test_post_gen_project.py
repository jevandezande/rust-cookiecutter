"""Tests for post_gen_project hook behavior."""

import ast
import functools
import json
import os
import re
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from enum import StrEnum
from itertools import product
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from jinja2 import Environment, Template

from hooks import post_gen_project, pre_gen_project

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "{{cookiecutter.crate_name}}"


@pytest.fixture
def crate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a generated-workspace skeleton and chdir into it."""
    for member in ("core", "py", "cli"):
        (tmp_path / "crates" / member / "src").mkdir(parents=True)
        (tmp_path / "crates" / member / "src" / "lib.rs").write_text("//! x\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_set_rust_version_pins_toolchain_and_declares_a_trailing_msrv(
    crate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin the resolved toolchain, and declare an MSRV that trails it."""
    msrv = "1.95"
    (crate / "Cargo.toml").write_text('rust-version = "{rust_msrv}"\n', encoding="utf-8")
    (crate / "rust-toolchain.toml").write_text('channel = "stable"\n', encoding="utf-8")
    (crate / "README.md").write_text("badge/rust-{rust_msrv}%2B\n", encoding="utf-8")

    calls: list[str] = []

    def fake_call(cmd: str, **_: object) -> SimpleNamespace:
        calls.append(cmd)
        return SimpleNamespace(stdout="rustc 1.97.1 (deadbeef 2026-01-01)\n")

    monkeypatch.setattr(post_gen_project, "call", fake_call)

    post_gen_project.set_rust_version()

    assert (crate / "Cargo.toml").read_text(encoding="utf-8") == f'rust-version = "{msrv}"\n'
    assert (crate / "rust-toolchain.toml").read_text(encoding="utf-8") == 'channel = "1.97.1"\n'
    assert (crate / "README.md").read_text(encoding="utf-8") == f"badge/rust-{msrv}%2B\n"
    assert calls == ["rustc --version"]


def test_read_write_rejects_a_missing_placeholder(crate: Path) -> None:
    """Raise rather than leave a renamed placeholder's replacement silently unapplied."""
    (crate / "Cargo.toml").write_text('rust-version = "1.90"\n', encoding="utf-8")

    with pytest.raises(ValueError, match=re.escape("'{rust_msrv}' not found in Cargo.toml")):
        post_gen_project.read_write("Cargo.toml", "{rust_msrv}", "1.95")


def test_rust_version_rejects_unparseable_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise when rustc output has no version in it."""
    monkeypatch.setattr(
        post_gen_project, "call", lambda *_, **__: SimpleNamespace(stdout="not a version")
    )

    with pytest.raises(ValueError, match="Unable to parse rust version"):
        post_gen_project.rust_version()


def interop_mode(crate: Path, readme_fragment: str) -> Path:
    """Build the `embedded` mode's sources, with the given body for its README fragment.

    Every fragment gets a file and a target carrying its placeholder, so the loop in
    `set_interop` finds what it expects; only the README's body varies per test.

    Args:
        crate: workspace root `crate` fixture chdir'd into
        readme_fragment: contents of `fragments/readme.md.in`

    Returns:
        Mode directory `set_interop` copies from
    """
    interop = crate / "data" / "interop" / "embedded"
    (interop / "fragments").mkdir(parents=True)

    for fragment, (target, placeholder) in post_gen_project.INTEROP_FRAGMENTS.items():
        body = readme_fragment if target == "README.md" else f"## {fragment}\n"
        (interop / "fragments" / fragment).write_text(body, encoding="utf-8")

        path = crate / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Title\n\n{placeholder}\n## Next\n", encoding="utf-8")

    return interop


def test_set_interop_copies_the_mode_over_the_root(crate: Path) -> None:
    """Materialize the selected mode's files, overwriting what the base template ships."""
    interop = interop_mode(crate, "## Boundary\n")
    (interop / "crates" / "py" / "src").mkdir(parents=True)
    (interop / "crates" / "py" / "src" / "lib.rs").write_text("//! embedded\n", encoding="utf-8")
    (interop / "scripts").mkdir()
    (interop / "scripts" / "bundle.py").write_text("bundle", encoding="utf-8")

    post_gen_project.set_interop("embedded")

    py_lib = crate / "crates" / "py" / "src" / "lib.rs"
    assert py_lib.read_text(encoding="utf-8") == "//! embedded\n"
    assert (crate / "scripts" / "bundle.py").read_text(encoding="utf-8") == "bundle"
    assert (crate / "crates" / "core" / "src" / "lib.rs").read_text(encoding="utf-8") == "//! x\n"
    assert not (crate / "fragments").exists(), "fragments are substituted, not materialized"


def test_set_interop_substitutes_the_fragment(crate: Path) -> None:
    """Fill placeholder with mode's fragment, whole lines and no more."""
    interop_mode(crate, "## Boundary\n\nEmbeds CPython.\n")

    post_gen_project.set_interop("embedded")

    assert (crate / "README.md").read_text(encoding="utf-8") == (
        "# Title\n\n## Boundary\n\nEmbeds CPython.\n## Next\n"
    )


def test_set_interop_collapses_an_empty_fragment(crate: Path) -> None:
    """Leave no blank line behind for a mode with nothing to say."""
    interop_mode(crate, "")

    post_gen_project.set_interop("embedded")

    assert (crate / "README.md").read_text(encoding="utf-8") == "# Title\n\n## Next\n"


@pytest.fixture
def template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Stage template's own substitution targets, then chdir into the copy.

    Skills ship verbatim (`_copy_without_render`), so template's file is character for
    character what a generated project gets, and rumdl runs over it there.
    """
    shutil.copytree(TEMPLATE / "data", tmp_path / "data")
    shutil.copy(TEMPLATE / "README.md", tmp_path / "README.md")

    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize("interop", [mode.value for mode in post_gen_project.Interop])
def test_every_mode_ships_a_fragment_for_every_site(template: Path, interop: str) -> None:
    """Leave no placeholder behind in any mode.

    A missing fragment raises from `read_text` and a drifted placeholder from `read_write`; this
    runs the real fragments against the real targets, mode by mode.
    """
    post_gen_project.set_interop(interop)

    for target, placeholder in post_gen_project.INTEROP_FRAGMENTS.values():
        text = (template / target).read_text(encoding="utf-8")
        assert placeholder not in text, target
        assert "\n\n\n" not in text, f"MD012: {target} gained a doubled blank line"


def test_set_interop_fails_on_a_missing_fragment(crate: Path) -> None:
    """Stop generation when a mode lacks a fragment, rather than leaving a placeholder behind."""
    interop = interop_mode(crate, "## Boundary\n")
    (interop / "fragments" / "agents.md.in").unlink()

    with pytest.raises(FileNotFoundError, match=r"agents\.md\.in"):
        post_gen_project.set_interop("embedded")


@pytest.mark.parametrize(
    ("crate_type", "expected"),
    [
        ("lib", {"core", "py"}),
        ("both", {"core", "py", "cli"}),
    ],
)
def test_set_crate_type_keeps_the_right_workspace_members(
    crate: Path, crate_type: str, expected: set[str]
) -> None:
    """Keep only workspace members the selected layout calls for."""
    scripts = crate / "scripts"
    scripts.mkdir()
    (scripts / "bundle.py").write_text("bundle", encoding="utf-8")
    (scripts / "test_bundle.py").write_text("tests", encoding="utf-8")
    (scripts / "smoke_bundle.py").write_text("smoke", encoding="utf-8")
    (scripts / "test_smoke_bundle.py").write_text("smoke tests", encoding="utf-8")

    post_gen_project.set_crate_type(crate_type)

    remaining = {p.name for p in (crate / "crates").iterdir() if p.is_dir()}
    assert remaining == expected
    assert (scripts / "bundle.py").exists() is (crate_type != "lib")
    assert (scripts / "test_bundle.py").exists() is (crate_type != "lib")
    assert (scripts / "smoke_bundle.py").exists() is (crate_type != "lib")
    assert (scripts / "test_smoke_bundle.py").exists() is (crate_type != "lib")


@pytest.mark.parametrize(
    ("release_ci", "python_interop", "kept"),
    [
        ("binaries", "embedded", "release-binaries.yml"),
        ("binaries", "none", "release-binaries-pure.yml"),
        ("pypi", "extension", "release-pypi.yml"),
        # Unmapped pairs leave no release workflow at all, rather than a broken one; pre-gen
        # rejects them before generation reaches here
        ("pypi", "embedded", None),
        ("None", "none", None),
    ],
)
def test_set_release_ci_keeps_one_workflow(
    crate: Path, release_ci: str, python_interop: str, kept: str | None
) -> None:
    """Rename workflow (release_ci, interop) pair selects and delete unused ones.

    Each workflow's contents are its own name, so release.yml identifies which one survived.
    """
    workflows = crate / ".github" / "workflows"
    workflows.mkdir(parents=True)
    for name in ("test.yml", *set(post_gen_project.RELEASE_WORKFLOWS.values())):
        (workflows / name).write_text(name, encoding="utf-8")

    post_gen_project.set_release_ci(release_ci, python_interop)

    expected = {"test.yml", "release.yml"} if kept else {"test.yml"}
    assert {p.name for p in workflows.iterdir()} == expected
    if kept:
        assert (workflows / "release.yml").read_text(encoding="utf-8") == kept


@pytest.mark.parametrize(
    ("release_ci", "interop"), list(product(post_gen_project.ReleaseCi, post_gen_project.Interop))
)
def test_release_workflows_and_pre_gen_agree(
    release_ci: post_gen_project.ReleaseCi, interop: post_gen_project.Interop
) -> None:
    """Map exactly the pairs pre-gen accepts; `None` alone is accepted with no workflow to keep."""
    mapped = (release_ci, interop) in post_gen_project.RELEASE_WORKFLOWS

    try:
        pre_gen_project.check_interop_compatibility(interop.value, release_ci.value, "")
    except ValueError:
        accepted = False
    else:
        accepted = True

    if release_ci is post_gen_project.ReleaseCi.NONE:
        assert accepted
        assert not mapped
    else:
        assert accepted is mapped


def test_set_license_copies_and_formats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Copy license file and fill its placeholders."""
    licenses_path = tmp_path / "data" / "licenses"
    licenses_path.mkdir(parents=True)
    (licenses_path / "MIT").write_text("Copyright {year} {author_name}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    fake_datetime = SimpleNamespace(now=lambda: SimpleNamespace(year=2026))
    monkeypatch.setattr(post_gen_project, "datetime", fake_datetime)

    post_gen_project.set_license("MIT")

    license_contents = (tmp_path / "LICENSE").read_text(encoding="utf-8")
    assert "2026" in license_contents
    assert "{{cookiecutter.author_name}}" in license_contents


@pytest.mark.parametrize(
    ("option", "enum", "normalize"),
    [
        ("crate_type", post_gen_project.CrateType, str),
        ("python_interop", post_gen_project.Interop, str),
        ("release_ci", post_gen_project.ReleaseCi, str),
        # `setup_coding_agent_files` lowercases before constructing the enum
        ("coding_agent", post_gen_project.CodingAgent, str.lower),
    ],
)
def test_every_option_choice_has_an_enum_member(
    option: str, enum: type[StrEnum], normalize: Callable[[str], str]
) -> None:
    """Offer exactly the choices the hooks can act on.

    An option added to `cookiecutter.json` alone fails at generation, where the hook constructs
    the enum; a member removed from an enum leaves a choice that cannot be selected.
    """
    choices = json.loads((ROOT / "cookiecutter.json").read_text(encoding="utf-8"))[option]

    assert {normalize(choice) for choice in choices} == {member.value for member in enum}


def test_every_license_choice_ships_a_file_set_license_can_format() -> None:
    """Ship a file per license choice, each carrying the placeholders `set_license` fills.

    `read_write` raises on a missing placeholder, so a license file without both is a hard
    generation failure for anyone who selects it.
    """
    choices = json.loads((ROOT / "cookiecutter.json").read_text(encoding="utf-8"))["license"]
    licenses = TEMPLATE / "data" / "licenses"

    expected = {choice for choice in choices if choice != "None"} | {post_gen_project.PROPRIETARY}

    assert expected == {path.name for path in licenses.iterdir()}

    for path in licenses.iterdir():
        contents = path.read_text(encoding="utf-8")
        assert "{year}" in contents, path.name
        assert "{author_name}" in contents, path.name


def test_set_license_rejects_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise on a license with no file to copy, listing what is available."""
    licenses_path = tmp_path / "data" / "licenses"
    licenses_path.mkdir(parents=True)
    (licenses_path / "MIT").write_text("MIT text", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="WTFPL"):
        post_gen_project.set_license("WTFPL")

    assert not (tmp_path / "LICENSE").exists()


def test_set_license_none_writes_proprietary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fall back to an all-rights-reserved notice when no license is selected."""
    licenses_path = tmp_path / "data" / "licenses"
    licenses_path.mkdir(parents=True)
    (licenses_path / post_gen_project.PROPRIETARY).write_text(
        "All rights reserved {year} {author_name}", encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)
    fake_datetime = SimpleNamespace(now=lambda: SimpleNamespace(year=2026))
    monkeypatch.setattr(post_gen_project, "datetime", fake_datetime)

    post_gen_project.set_license("None")

    assert "All rights reserved" in (tmp_path / "LICENSE").read_text(encoding="utf-8")


@pytest.fixture
def agent_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create `data/` payload the coding-agent setup copies from, and chdir into its parent."""
    (tmp_path / "data" / ".claude" / "skills").mkdir(parents=True)
    (tmp_path / "data" / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    (tmp_path / "data" / "AGENTS_README.md").write_text("agent notes", encoding="utf-8")
    (tmp_path / "data" / "STATE.md").write_text("progress tracker", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    ("agent", "settings"),
    [
        ("Claude", True),
        ("Codex", False),
    ],
)
def test_setup_coding_agent_files_writes_the_agents_own_file(
    agent_data: Path, agent: str, settings: bool
) -> None:
    """Always write AGENTS.md, which every agent reads; only Claude gets settings.json.

    Skills go to both agents, as reference, and `STATE.md` with them, since the spec skills read
    and update it; `settings.json` is Claude's settings and hooks.
    """
    post_gen_project.setup_coding_agent_files(agent)

    assert (agent_data / "AGENTS.md").read_text(encoding="utf-8") == "agent notes"
    assert not (agent_data / "CLAUDE.md").exists()
    assert (agent_data / ".claude" / "skills").is_dir()
    assert (agent_data / ".claude" / "settings.json").exists() is settings
    assert (agent_data / "STATE.md").read_text(encoding="utf-8") == "progress tracker"


def test_setup_coding_agent_files_none_still_writes_agents_md(agent_data: Path) -> None:
    """Ship AGENTS.md even when no agent is selected, so embedding rules land."""
    post_gen_project.setup_coding_agent_files("None")

    assert (agent_data / "AGENTS.md").read_text(encoding="utf-8") == "agent notes"
    assert not (agent_data / ".claude").exists()
    assert not (agent_data / "CLAUDE.md").exists()
    assert not (agent_data / "STATE.md").exists()


def test_setup_coding_agent_files_rejects_unknown(agent_data: Path) -> None:
    """Raise on an agent outside supported set, before anything is copied."""
    with pytest.raises(ValueError, match="cursor"):
        post_gen_project.setup_coding_agent_files("cursor")

    assert not (agent_data / ".claude").exists()


@pytest.mark.parametrize(
    ("python_interop", "expected", "pinned"),
    [
        ("embedded", ["uv python find", "uv run cargo build --workspace"], True),
        ("extension", ["uv run cargo build --workspace", "uv run maturin develop --uv"], False),
        ("none", ["uv run cargo build --workspace"], False),
    ],
)
def test_build_workspace_builds_what_the_mode_needs(
    monkeypatch: pytest.MonkeyPatch, python_interop: str, expected: list[str], pinned: bool
) -> None:
    """Build each mode the way its own `mise run build` would.

    Only `embedded` links libpython, so only it looks an interpreter up and pins PYO3_PYTHON.
    `extension` builds like `none` (maturin, not a default feature, enables `extension-module`)
    and follows up with editable install its tests import.
    """
    calls: list[str] = []

    def fake_call(cmd: str, **_: object) -> SimpleNamespace:
        calls.append(cmd)
        return SimpleNamespace(stdout="/tmp/.venv/bin/python\n")

    monkeypatch.setattr(post_gen_project, "call", fake_call)
    # setenv, not delenv, so monkeypatch restores it and pin cannot leak into other tests
    monkeypatch.setenv("PYO3_PYTHON", "")

    post_gen_project.build_workspace(python_interop)

    assert calls == expected
    assert os.environ["PYO3_PYTHON"] == ("/tmp/.venv/bin/python" if pinned else "")


def test_verify_generated_project_warns_rather_than_raising(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Report failing hooks without aborting; cookiecutter deletes project on a raise.

    Pre-push stage runs, since test suites are pre-push hooks that `prek run` alone skips.
    """
    calls: list[str] = []

    def fake_call(cmd: str, **_: object) -> SimpleNamespace:
        calls.append(cmd)
        return SimpleNamespace(returncode=int(cmd.startswith("uv run prek")))

    monkeypatch.setattr(post_gen_project, "call", fake_call)

    post_gen_project.verify_generated_project()

    # Staged first: `prek run -a` sees only what git knows about
    assert calls == ["git add .", "uv run prek run -a --stage pre-push"]
    assert "fails its own hooks" in caplog.text


def test_verify_generated_project_is_quiet_when_the_hooks_pass(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Say nothing when generated project already satisfies its own hooks."""
    monkeypatch.setattr(post_gen_project, "call", lambda *_, **__: SimpleNamespace(returncode=0))

    post_gen_project.verify_generated_project()

    assert not caplog.text


def test_git_initial_commit_skips_the_hooks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Commit with --no-verify: hooks already ran, where failing them is not fatal."""
    calls: list[str] = []
    monkeypatch.setattr(post_gen_project, "call", lambda cmd, **_: calls.append(cmd))

    post_gen_project.git_initial_commit()

    assert calls == ["git add .", "git commit --no-verify -m Setup"]


@pytest.mark.parametrize(
    ("github_setup", "expected"), [("None", False), ("private", True), ("public", True)]
)
def test_check_prerequisites_requires_gh_only_for_github_setup(
    github_setup: str, expected: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Check GitHub CLI up front, rather than after minutes of building."""
    calls: list[str] = []
    monkeypatch.setattr(post_gen_project, "call", lambda cmd, **_: calls.append(cmd))

    post_gen_project.check_prerequisites(github_setup)

    assert ("gh --version" in calls) is expected


def test_clear_parent_env_drops_inherited_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop invoking environment, which would otherwise capture generated project's uv.

    Only variables that redirect uv or cargo go; a user's index and cache settings survive.
    """
    monkeypatch.setenv("VIRTUAL_ENV", "/somewhere/else/.venv")
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", "/somewhere/else")
    monkeypatch.setenv("UV_LOCKED", "1")
    monkeypatch.setenv("CONDA_PREFIX", "/somewhere/else/conda")
    monkeypatch.setenv("RUSTUP_TOOLCHAIN", "1.70.0")
    monkeypatch.setenv("CARGO_TARGET_DIR", "/somewhere/else/target")
    monkeypatch.setenv("UV_INDEX_URL", "https://mirror.example.com/simple")
    monkeypatch.setenv("PATH", "/usr/bin")

    post_gen_project.clear_parent_env()

    for name in post_gen_project.INHERITED_ENV:
        assert name not in os.environ, name
    assert os.environ["UV_INDEX_URL"] == "https://mirror.example.com/simple"
    assert os.environ["PATH"] == "/usr/bin", "unrelated variables must survive"


def test_github_setup_rejects_unknown_privacy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise before touching gh, so a typo cannot create a repo with the wrong visibility."""
    calls: list[str] = []
    monkeypatch.setattr(post_gen_project, "call", lambda cmd, **_: calls.append(cmd))

    with pytest.raises(ValueError, match="privacy='pubic'"):
        post_gen_project.github_setup("pubic")

    assert calls == []


def test_github_setup_qualifies_the_repo_with_the_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Create `owner/name`, so repo matches URLs the project embeds."""
    calls: list[str] = []
    monkeypatch.setattr(post_gen_project, "call", lambda cmd, **_: calls.append(cmd))

    post_gen_project.github_setup("internal", owner="acme", name="scorer")

    assert calls[0] == ("gh repo create acme/scorer --internal --remote origin --source . --push")


def test_github_setup_survives_a_failing_gh(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Report a failed repo creation; raising would delete finished project.

    Nothing runs after failure: there is no remote to set upstream to.
    """
    calls: list[str] = []

    def fake_call(cmd: str, **_: object) -> None:
        calls.append(cmd)
        if cmd.startswith("gh repo create"):
            raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(post_gen_project, "call", fake_call)

    post_gen_project.github_setup("private", owner="acme", name="scorer")

    assert "Retry with: gh repo create acme/scorer --private" in caplog.text
    assert len(calls) == 1


def test_check_program_reports_the_install_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Turn a missing prerequisite into an error that says how to install it."""

    def missing(*_: object, **__: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(post_gen_project, "call", missing)

    with pytest.raises(OSError, match=re.escape("install with `https://rustup.rs`")):
        post_gen_project.check_program("cargo --version", "https://rustup.rs")


def test_check_program_reports_the_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tell a broken install apart from a missing one, and say what it exited with."""

    def broken(cmd: str, **_: object) -> None:
        raise subprocess.CalledProcessError(127, cmd)

    monkeypatch.setattr(post_gen_project, "call", broken)

    with pytest.raises(RuntimeError, match="`cargo --version` exited with 127"):
        post_gen_project.check_program("cargo --version", "https://rustup.rs")


@pytest.mark.parametrize(
    ("protocol", "expected"),
    [
        ("git", "git@github.com:user/repo.git"),
        ("https", "https://github.com/user/repo.git"),
    ],
)
def test_git_add_remote_formats_url(
    protocol: post_gen_project.GitProtocol,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rewrite HTTPS URL into `git@` form, or leave it alone for `https`."""
    calls: list[str] = []

    def fake_call(cmd: str, **_: object) -> None:
        calls.append(cmd)

    monkeypatch.setattr(post_gen_project, "call", fake_call)
    post_gen_project.git_add_remote("origin", "https://github.com/user/repo.git", protocol=protocol)
    assert calls == [f"git remote add origin {expected}"]


def test_add_dependencies_targets_the_core_package(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pass `-p` so cargo add can update a virtual workspace."""
    calls: list[str] = []
    monkeypatch.setattr(post_gen_project, "call", lambda cmd, **_: calls.append(cmd))

    post_gen_project.add_dependencies(
        package="demo", dependencies="serde@1.0 rayon", dev_dependencies="proptest"
    )

    assert calls == ["cargo add -p demo serde@1.0 rayon", "cargo add --dev -p demo proptest"]


def test_add_dependencies_skips_empty_specs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not invoke cargo when user left both dependency prompts blank."""
    calls: list[str] = []
    monkeypatch.setattr(post_gen_project, "call", lambda cmd, **_: calls.append(cmd))

    post_gen_project.add_dependencies(package="demo", dependencies="", dev_dependencies="")

    assert calls == []


def test_add_python_dependencies_runs_uv_add(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pass spec through to `uv add --no-sync`, which resolves without installing."""
    calls: list[str] = []
    monkeypatch.setattr(post_gen_project, "call", lambda cmd, **_: calls.append(cmd))

    post_gen_project.add_python_dependencies(dependencies="numpy scipy")

    assert calls == ["uv add --no-sync numpy scipy"]


def test_add_python_dependencies_skips_empty_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not invoke uv when user left prompt blank."""
    calls: list[str] = []
    monkeypatch.setattr(post_gen_project, "call", lambda cmd, **_: calls.append(cmd))

    post_gen_project.add_python_dependencies(dependencies="")

    assert calls == []


# What `_copy_without_render` ships verbatim; everything else goes through Jinja
VERBATIM = ("data/.claude/skills", ".github/workflows/release-")

# Options that select Jinja branches; rest render the same for every value
OPTION_COMBINATIONS = list(
    product(
        [mode.value for mode in post_gen_project.Interop],
        [kind.value for kind in post_gen_project.CrateType],
        ["MIT", "None"],
        [ci.value for ci in post_gen_project.ReleaseCi],
    )
)


def cookiecutter_context(**overrides: str) -> dict[str, str]:
    """Build the context cookiecutter would render with: `cookiecutter.json` defaults, overridden.

    Args:
        overrides: option values to replace defaults with

    Returns:
        `cookiecutter` namespace, with derived names resolved
    """
    raw = json.loads((ROOT / "cookiecutter.json").read_text(encoding="utf-8"))
    context = {
        key: value[0] if isinstance(value, list) else value
        for key, value in raw.items()
        if not key.startswith("_")
    } | overrides
    context["crate_name"] = "rust-project"
    context["__package_name"] = "rust_project"
    context["project_url"] = f"https://github.com/{context['github_username']}/rust-project"
    return context


@functools.cache
def compiled_templates() -> list[tuple[str, Template]]:
    """Compile every template file cookiecutter renders, hooks included.

    Compiling dominates rendering; runs once and every option combination renders same templates.

    Returns:
        Path relative to repo root and compiled template, per file
    """
    env = Environment(keep_trailing_newline=True)
    files = [p for p in TEMPLATE.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    files += (ROOT / "hooks").glob("*.py")
    return [
        (p.relative_to(ROOT).as_posix(), env.from_string(p.read_text(encoding="utf-8")))
        for p in files
        if not any(v in p.as_posix() for v in VERBATIM)
    ]


@pytest.mark.parametrize(
    ("interop", "crate_type", "license_name", "release_ci"), OPTION_COMBINATIONS
)
def test_template_renders_to_well_formed_files(
    interop: str, crate_type: str, license_name: str, release_ci: str
) -> None:
    """Render every file for option combination and parse what has a parser.

    Root `prek.toml` has to exclude Jinja-bearing TOML and YAML from `check-toml` and
    `check-yaml`; this is the only check short of CI that a comment edit did not take a Jinja
    tag with it.
    """
    context = cookiecutter_context(
        python_interop=interop,
        crate_type=crate_type,
        license=license_name,
        release_ci=release_ci,
        github_username="octocat",
        author_name="Octo Cat",
    )

    for name, template in compiled_templates():
        text = template.render(cookiecutter=context)
        match Path(name).suffix:
            case ".toml":
                tomllib.loads(text)
            case ".yml":
                assert yaml.safe_load(text), name
            case ".json":
                json.loads(text)
            case ".py" | ".pyi":
                ast.parse(text, filename=name)
            case _:
                pass
