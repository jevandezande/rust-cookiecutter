"""Tests for release-bundle helpers."""

from pathlib import Path

import pytest
from bundle import has_requirements, install_runtime_packages


def test_has_requirements_ignores_blank_and_comment_lines() -> None:
    """Treat an empty or comment-only export as nothing to install."""
    assert not has_requirements("")
    assert not has_requirements("# comment\n\n  \n")
    assert has_requirements("numpy==2.0.0\n")
    assert has_requirements("# header\nnumpy==2.0.0\n")


def test_install_runtime_packages_skips_empty_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not invoke the installer when `[project.dependencies]` is empty."""
    monkeypatch.setattr("bundle.export_runtime_requirements", lambda: "# none\n")
    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr("bundle.run", lambda *args, **_: calls.append(args))

    install_runtime_packages(tmp_path / "python")

    assert calls == []


def test_install_runtime_packages_installs_exported_requirements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pass the exported requirements file to `uv pip install --python`."""
    monkeypatch.setattr("bundle.export_runtime_requirements", lambda: "numpy==2.0.0\n")
    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr("bundle.run", lambda *args, **_: calls.append(args))

    executable = tmp_path / "python"
    install_runtime_packages(executable)

    assert len(calls) == 1
    assert calls[0][:5] == ("uv", "pip", "install", "--python", executable)
    assert "--strict" in calls[0]
    assert "-r" in calls[0]
    # Without it uv refuses: the bundled interpreter inherits uv's EXTERNALLY-MANAGED marker
    assert "--break-system-packages" in calls[0]
