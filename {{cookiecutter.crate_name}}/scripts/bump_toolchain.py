"""Re-pin `rust-toolchain.toml` to current stable release, and move MSRV with it.

Run via `mise run bump-toolchain`.
MSRV trails pin by `MSRV_LAG` minor releases.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MSRV_LAG = 2

PINS = (("rust-toolchain.toml", r'(?m)^channel = "(\d+\.\d+\.\d+)"'),)
MSRVS = (
    ("Cargo.toml", r'(?m)^rust-version = "(\d+\.\d+)"'),
    ("README.md", r"Rust: (\d+\.\d+)\+"),
    ("README.md", r"badge/rust-(\d+\.\d+)%2B"),
)


def resolved_stable() -> str:
    """Install current stable release and report its exact version.

    Returns:
        Resolved version, e.g. "1.97.1"

    Raises:
        ValueError: version cannot be parsed from `rustc --version`
    """
    subprocess.run(["rustup", "update", "--no-self-update", "stable"], check=True)
    result = subprocess.run(
        ["rustup", "run", "stable", "rustc", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    if not (version := re.search(r"\d+\.\d+\.\d+", result.stdout)):
        raise ValueError(f"Unable to parse rust version from {result.stdout!r}")
    return version.group()


def next_msrv(pinned: str, declared: str, lag: int = MSRV_LAG) -> str:
    """Derive MSRV to declare beside a new pin, never moving it backwards.

    Args:
        pinned: version being pinned, e.g. "1.97.1"
        declared: MSRV currently declared, e.g. "1.93"
        lag: minor releases to trail pin by

    Returns:
        MSRV to declare, as `major.minor`

    Examples:
        >>> next_msrv("1.97.1", "1.90")
        '1.95'
        >>> next_msrv("1.91.0", "1.93")
        '1.93'
        >>> next_msrv("2.0.0", "1.90")
        '2.0'
        >>> next_msrv("2.1.0", "1.90")
        '2.0'
    """
    major, minor, *_ = (int(part) for part in pinned.split("."))
    current = tuple(int(part) for part in declared.split("."))
    version = max((major, max(minor - lag, 0)), current)
    return f"{version[0]}.{version[1]}"


def read_version(file_name: str, pattern: str) -> str:
    """Read version a pattern captures out of a file.

    Args:
        file_name: file to read, relative to project root
        pattern: regex whose first group is version

    Returns:
        Captured version

    Raises:
        ValueError: pattern matches nothing in file
    """
    text = (ROOT / file_name).read_text(encoding="utf-8")
    if not (match := re.search(pattern, text)):
        raise ValueError(f"{pattern!r} matches nothing in {file_name}")
    return match.group(1)


def write_version(file_name: str, pattern: str, version: str) -> None:
    """Replace every version a pattern captures in a file.

    Args:
        file_name: file to rewrite, relative to project root
        pattern: regex whose first group is version
        version: replacement version

    Raises:
        ValueError: pattern matches nothing, so file would keep a stale version
    """
    path = ROOT / file_name

    def replace(match: re.Match[str]) -> str:
        prefix = match.string[match.start() : match.start(1)]
        suffix = match.string[match.end(1) : match.end()]
        return f"{prefix}{version}{suffix}"

    text, count = re.subn(pattern, replace, path.read_text(encoding="utf-8"))
    if not count:
        raise ValueError(f"{pattern!r} matches nothing in {file_name}")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    """Re-pin toolchain and move MSRV to match."""
    pinned = resolved_stable()
    declared = read_version(*MSRVS[0])
    msrv = next_msrv(pinned, declared)

    print(f"pinning {pinned}, msrv {declared} -> {msrv}", flush=True)

    for file_name, pattern in PINS:
        write_version(file_name, pattern, pinned)
    for file_name, pattern in MSRVS:
        write_version(file_name, pattern, msrv)


if __name__ == "__main__":
    main()
