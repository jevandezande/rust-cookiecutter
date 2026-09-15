"""Prove the bundled binary ignores an ambient virtualenv.

Run after `mise run bundle`. Writes a `math.py` that raises into a fake venv, then launches
`dist/bin` with `VIRTUAL_ENV` pointing at it. Exit 0 means the bundle used its own interpreter
instead of the venv's `site-packages`.

`--import` needs the bundled python executable (`scripts/bundle.py --keep-python-executable`).
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from bundle import BIN_NAME, DIST, interpreter_executable


def poison_site_packages(venv: Path) -> Path:
    """Write a `math.py` that raises into the venv's `site-packages`.

    Args:
        venv: fake virtualenv root

    Returns:
        Path of the `site-packages` directory
    """
    site = (
        venv / "Lib" / "site-packages"
        if sys.platform == "win32"
        else venv / "lib" / "python3" / "site-packages"
    )
    site.mkdir(parents=True)
    (site / "math.py").write_text("raise RuntimeError('venv leaked')\n", encoding="utf-8")
    return site


def bundled_binary() -> Path:
    """Locate the bundled executable.

    Returns:
        Path to `dist/bin/<name>`

    Raises:
        FileNotFoundError: no executable in `dist/bin`
    """
    candidate = DIST / "bin" / BIN_NAME
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"no bundled executable at {candidate}")


def isolated_env(venv: Path) -> dict[str, str]:
    """Copy the process environment, pointing `VIRTUAL_ENV` at `venv` and dropping Python paths.

    Args:
        venv: fake virtualenv root

    Returns:
        Environment for the bundled process
    """
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(venv)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    return env


def smoke_binary(venv: Path) -> None:
    """Run the bundled executable against a venv that would break `import math`.

    Args:
        venv: fake virtualenv root
    """
    subprocess.run([bundled_binary()], check=True, env=isolated_env(venv))


def smoke_import(module: str) -> None:
    """Import `module` with the bundled interpreter in isolated mode.

    Args:
        module: module name to import
    """
    python = interpreter_executable(DIST / "python")
    subprocess.run([python, "-I", "-c", f"import {module}"], check=True)


def main() -> None:
    """Run the smoke checks.

    Raises:
        FileNotFoundError: the bundle or a requested interpreter is missing
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--import",
        dest="modules",
        action="append",
        default=[],
        help="import this module with the bundled interpreter (repeatable)",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        venv = Path(tmp)
        poison_site_packages(venv)
        smoke_binary(venv)
        for module in args.modules:
            smoke_import(module)

    print("bundle smoke ok", flush=True)


if __name__ == "__main__":
    main()
