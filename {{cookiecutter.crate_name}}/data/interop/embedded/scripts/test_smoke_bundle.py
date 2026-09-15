"""Tests for bundle smoke helpers."""

from pathlib import Path

import pytest
from smoke_bundle import isolated_env, poison_site_packages


def test_poison_site_packages_writes_a_raising_math(tmp_path: Path) -> None:
    """Place `math.py` where bootstrap would look for venv site-packages."""
    site = poison_site_packages(tmp_path)

    assert (site / "math.py").read_text(encoding="utf-8") == "raise RuntimeError('venv leaked')\n"
    assert site.is_relative_to(tmp_path)


def test_isolated_env_points_at_the_venv_and_drops_python_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Point VIRTUAL_ENV at the venv and drop PYTHONHOME and PYTHONPATH."""
    monkeypatch.setenv("PYTHONHOME", "/old")
    monkeypatch.setenv("PYTHONPATH", "/also")
    monkeypatch.setenv("PATH", "/bin")

    env = isolated_env(tmp_path)

    assert env["VIRTUAL_ENV"] == str(tmp_path)
    assert "PYTHONHOME" not in env
    assert "PYTHONPATH" not in env
    assert env["PATH"] == "/bin"
