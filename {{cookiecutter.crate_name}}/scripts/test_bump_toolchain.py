"""Tests for the toolchain-bump helpers."""

from pathlib import Path

import bump_toolchain
import pytest
from bump_toolchain import MSRVS, PINS, read_version, write_version

BADGES = "[![Rust: 1.90+](https://img.shields.io/badge/rust-1.90%2B)](https://www.rust-lang.org)\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the script at a skeleton holding every version it rewrites."""
    (tmp_path / "rust-toolchain.toml").write_text(
        'channel = "1.90.0"\ncomponents = ["rustfmt"]\n', encoding="utf-8"
    )
    (tmp_path / "Cargo.toml").write_text(
        'version = "0.0.1"\nrust-version = "1.90"\n', encoding="utf-8"
    )
    (tmp_path / "README.md").write_text(BADGES, encoding="utf-8")

    monkeypatch.setattr(bump_toolchain, "ROOT", tmp_path)
    return tmp_path


def test_write_version_repins_the_toolchain(project: Path) -> None:
    """Rewrite the channel without disturbing the components beside it."""
    for file_name, pattern in PINS:
        write_version(file_name, pattern, "1.97.1")

    assert (project / "rust-toolchain.toml").read_text(encoding="utf-8") == (
        'channel = "1.97.1"\ncomponents = ["rustfmt"]\n'
    )


def test_write_version_moves_every_msrv(project: Path) -> None:
    """Move the manifest's `rust-version` and both README badges, and nothing else."""
    for file_name, pattern in MSRVS:
        write_version(file_name, pattern, "1.95")

    assert (project / "Cargo.toml").read_text(encoding="utf-8") == (
        'version = "0.0.1"\nrust-version = "1.95"\n'
    )
    assert (project / "README.md").read_text(encoding="utf-8") == BADGES.replace("1.90", "1.95")


def test_write_version_rejects_a_file_without_one(project: Path) -> None:
    """Raise rather than report success over a file the pattern no longer matches."""
    (project / "README.md").write_text("no badge here\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"matches nothing in README\.md"):
        write_version(*MSRVS[1], "1.95")


def test_read_version_rejects_a_file_without_one(project: Path) -> None:
    """Raise rather than silently skip a file the pattern no longer matches."""
    (project / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"matches nothing in Cargo\.toml"):
        read_version(*MSRVS[0])
