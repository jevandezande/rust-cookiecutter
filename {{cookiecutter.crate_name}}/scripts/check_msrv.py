"""Check that the workspace builds on the MSRV declared in Cargo.toml.

Installs that toolchain via rustup if it is missing.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def declared_msrv() -> str:
    """Read `rust-version` from the workspace manifest.

    Returns:
        Declared MSRV, e.g. "1.90"

    Raises:
        ValueError: manifest declares no rust-version
    """
    manifest = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    if not (match := re.search(r'^rust-version\s*=\s*"([^"]+)"', manifest, re.MULTILINE)):
        raise ValueError("no rust-version in Cargo.toml")
    return match.group(1)


def main() -> int:
    """Install the MSRV toolchain and check the workspace against it.

    Returns:
        Process exit code
    """
    msrv = declared_msrv()
    print(f"checking against MSRV {msrv}", flush=True)

    subprocess.run(["rustup", "toolchain", "install", "--no-self-update", msrv], check=True)
    result = subprocess.run(
        ["cargo", f"+{msrv}", "check", "--workspace", "--all-targets", "--locked"],
        cwd=ROOT,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
