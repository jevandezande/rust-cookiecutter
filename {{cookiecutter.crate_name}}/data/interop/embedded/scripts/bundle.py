{%- set pkg = cookiecutter.__package_name -%}
{%- set crate = cookiecutter.crate_name -%}
"""Assemble a self-contained release bundle: binary plus its own Python interpreter.

Run via `mise run bundle`. Produces `dist/` laid out as the runtime bootstrap in `crates/py`
expects:

    dist/bin/{{crate}}: the executable
    dist/python/: a relocatable CPython install, plus `[project.dependencies]`

Rewrites the libpython reference relative to the executable, since the paths uv's install records
mean nothing on another machine.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
STAGING = DIST / "_python"
BIN_NAME = "{{crate}}" + (".exe" if sys.platform == "win32" else "")

# Removed from the bundled interpreter, as globs relative to its root, covering both the POSIX
# (`lib/pythonX.Y`) and Windows (`Lib`) layouts. Drop the tcl/tk entries if the Python you call
# draws a GUI.
TRIM_PATTERNS = (
    # Headers and build config: for compiling extension modules, not running them
    "include",
    "libs",
    "share",
    "BUILD",
    "lib/pkgconfig",
    # Safe to drop: `_sysconfigdata_*.py` sits beside `config-*/`, not inside it, so `sysconfig`
    # keeps working without it
    "lib/python*/config-*",
    # Tcl/Tk and the extension module that loads it
    "lib/itcl*",
    "lib/tcl*",
    "lib/tk*",
    "lib/thread*",
    "lib/libtcl*",
    "lib/libtk*",
    "tcl",
    "DLLs/_tkinter*",
    "DLLs/tcl*",
    "DLLs/tk*",
    "lib/python*/lib-dynload/_tkinter*",
    "lib/python*/tkinter",
    "lib/python*/turtle.py",
    "lib/python*/turtledemo",
    "Lib/tkinter",
    "Lib/turtle.py",
    "Lib/turtledemo",
    # IDLE, help() topic data, and the package installer
    "lib/python*/idlelib",
    "lib/python*/pydoc_data",
    "lib/python*/ensurepip",
    "lib/python*/site-packages/pip*",
    "Lib/idlelib",
    "Lib/pydoc_data",
    "Lib/ensurepip",
    "Lib/site-packages/pip*",
    "bin/idle*",
    "bin/pip*",
    "bin/pydoc*",
    "Scripts/idle*",
    "Scripts/pip*",
)

# The interpreter executable statically links libpython (doubling the runtime); keep it only
# if the Python you call re-launches an interpreter, as `multiprocessing` can
TRIM_PATTERNS_EXECUTABLE = (
    "bin/python*",
    "python.exe",
    "pythonw.exe",
)


def run(*cmd: str | Path, env: dict[str, str] | None = None, capture: bool = False) -> str:
    """Run a command, echoing it first, and fail loudly.

    Args:
        cmd: command and arguments
        env: replacement environment, or None to inherit
        capture: whether to capture and return stdout

    Returns:
        Captured stdout, or the empty string
    """
    print("+", " ".join(str(c) for c in cmd), flush=True)
    result = subprocess.run(
        [str(c) for c in cmd], check=True, text=True, env=env, capture_output=capture
    )
    return result.stdout if capture else ""


def python_version() -> str:
    """Read the interpreter version to bundle from .python-version.

    Returns:
        Version string such as "3.13"
    """
    return (ROOT / ".python-version").read_text(encoding="utf-8").strip()


def install_interpreter(version: str) -> Path:
    """Download a relocatable CPython into a staging directory.

    Staging lets the move into `dist/` happen after linking, which it must: `sysconfig`'s LIBDIR is
    baked in at install time and pyo3 passes it to the linker.

    Args:
        version: interpreter version to install

    Returns:
        Path to the installed interpreter root

    Raises:
        RuntimeError: the install did not produce exactly one interpreter
    """
    run("uv", "python", "install", "--install-dir", STAGING, "--managed-python", version)

    # uv leaves a shorter alias and a .temp directory beside the real install. The alias is a
    # symlink on Unix but a junction on Windows, which pathlib does not report as a symlink, so
    # dedupe by resolved target rather than filtering links.
    installs = {p.resolve() for p in STAGING.iterdir() if p.is_dir() and not p.name.startswith(".")}
    if len(installs) != 1:
        raise RuntimeError(
            f"expected exactly one interpreter in {STAGING}, found {sorted(installs)}"
        )

    return installs.pop()


def interpreter_executable(home: Path) -> Path:
    """Locate the interpreter binary inside an installed tree.

    Args:
        home: interpreter root

    Returns:
        Path to the Python executable

    Raises:
        FileNotFoundError: no executable found
    """
    candidates = [home / "python.exe", *sorted(home.glob("bin/python3.*"))]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"no python executable under {home}")


def build(python: Path) -> Path:
    """Build the release binary against the bundled interpreter.

    Args:
        python: interpreter to link against

    Returns:
        Path to the built executable
    """
    env: dict[str, str] = {**os.environ, "PYO3_PYTHON": str(python)}
    # pyo3-build-config falls back to VIRTUAL_ENV; the bundled interpreter is the one to link
    env.pop("VIRTUAL_ENV", None)
    run("cargo", "build", "--release", "--locked", "-p", "{{crate}}-cli", env=env)
    return ROOT / "target" / "release" / BIN_NAME


def relocate_macos(binary: Path, home: Path) -> None:
    """Rewrite the libpython reference to be relative to the executable.

    Args:
        binary: copied executable inside dist/bin
        home: bundled interpreter root

    Raises:
        RuntimeError: the binary does not link libpython
    """
    linked = run("otool", "-L", binary, capture=True)
    recorded = next(
        (line.split()[0] for line in linked.splitlines() if "libpython" in line), None
    )
    if recorded is None:
        raise RuntimeError(f"{binary} does not link libpython; nothing to relocate")
    dylib_name = Path(recorded).name
    dylib = home / "lib" / dylib_name

    run("install_name_tool", "-id", f"@rpath/{dylib_name}", dylib)
    run("install_name_tool", "-change", recorded, f"@rpath/{dylib_name}", binary)
    run("install_name_tool", "-add_rpath", "@executable_path/../python/lib", binary)

    # Drop the rpath crates/py records for development builds: it points into the staging tree
    build_rpath = str(Path(recorded).parent)
    if build_rpath in run("otool", "-l", binary, capture=True):
        run("install_name_tool", "-delete_rpath", build_rpath, binary)

    # install_name_tool invalidates the signature, which arm64 macOS refuses to load
    run("codesign", "--force", "--sign", "-", dylib)
    run("codesign", "--force", "--sign", "-", binary)


def relocate_linux(binary: Path) -> None:
    """Point the runtime search path at the bundled interpreter.

    Args:
        binary: copied executable inside dist/bin

    Raises:
        RuntimeError: patchelf is not installed
    """
    if shutil.which("patchelf") is None:
        raise RuntimeError("patchelf is required to bundle on Linux")
    run("patchelf", "--set-rpath", "$ORIGIN/../python/lib", binary)


def relocate_windows(binary: Path, home: Path) -> None:
    """Place the Python DLL beside the executable, where Windows looks for it.

    Args:
        binary: copied executable inside dist/bin
        home: bundled interpreter root

    Raises:
        RuntimeError: no python DLL in the bundled interpreter
    """
    dlls = list(home.glob("python3*.dll"))
    if not dlls:
        raise RuntimeError(f"no python DLL found in {home}")
    for dll in dlls:
        shutil.copy2(dll, binary.parent / dll.name)


def has_requirements(export_text: str) -> bool:
    """Report whether `uv export` output has any installable requirement lines.

    Args:
        export_text: stdout from `uv export`

    Returns:
        True if at least one non-comment, non-blank line is present
    """
    return any(
        line.strip() and not line.lstrip().startswith("#") for line in export_text.splitlines()
    )


def export_runtime_requirements() -> str:
    """Export locked `[project.dependencies]` as requirements text.

    Returns:
        `uv export --no-dev` stdout
    """
    return run(
        "uv",
        "export",
        "--no-dev",
        "--locked",
        "--no-emit-project",
        "--no-annotate",
        "--no-header",
        capture=True,
    )


def install_runtime_packages(executable: Path) -> None:
    """Install locked `[project.dependencies]` into the bundled interpreter.

    Args:
        executable: interpreter binary inside the bundle
    """
    requirements = export_runtime_requirements()
    if not has_requirements(requirements):
        print("no runtime Python packages to vendor")
        return

    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as req_file:
        req_file.write(requirements)
        req_path = Path(req_file.name)

    try:
        # The interpreter is a copy of a uv-managed CPython, so it carries uv's EXTERNALLY-MANAGED
        # marker. Vendoring packages into it is the point of the bundle, so override the refusal
        run(
            "uv",
            "pip",
            "install",
            "--python",
            executable,
            "--break-system-packages",
            "--strict",
            "-r",
            req_path,
        )
    finally:
        req_path.unlink(missing_ok=True)


def directory_size(path: Path) -> int:
    """Sum the sizes of every file under a directory.

    Args:
        path: directory to measure

    Returns:
        Size in bytes
    """
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def trim_interpreter(home: Path, keep_executable: bool = False) -> None:
    """Delete the parts of the interpreter a headless embedded process cannot use.

    Args:
        home: bundled interpreter root
        keep_executable: whether to keep the bundled python executable
    """
    before = directory_size(home)

    patterns = TRIM_PATTERNS if keep_executable else TRIM_PATTERNS + TRIM_PATTERNS_EXECUTABLE

    for pattern in patterns:
        for path in sorted(home.glob(pattern)):
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()

    for path in sorted(home.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not path.is_symlink() and not any(path.iterdir()):
            path.rmdir()

    after = directory_size(home)
    print(f"\ntrimmed interpreter: {before // 1_000_000} MB -> {after // 1_000_000} MB")


def main() -> None:
    """Build the bundle.

    Raises:
        RuntimeError: the host platform has no relocation strategy
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=None, help="interpreter version (default: pinned)")
    parser.add_argument("--no-trim", action="store_true", help="keep the full interpreter")
    parser.add_argument(
        "--keep-python-executable",
        action="store_true",
        help="retain python itself, for code that re-launches an interpreter",
    )
    args = parser.parse_args()

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "bin").mkdir(parents=True)

    staged = install_interpreter(args.version or python_version())
    built = build(interpreter_executable(staged))

    home = DIST / "python"
    shutil.move(staged, home)
    shutil.rmtree(STAGING, ignore_errors=True)

    # Before trim: `uv pip install --python` needs the bundled executable, which trim may drop
    install_runtime_packages(interpreter_executable(home))

    if not args.no_trim:
        trim_interpreter(home, keep_executable=args.keep_python_executable)

    binary = DIST / "bin" / BIN_NAME
    shutil.copy2(built, binary)

    match platform.system():
        case "Darwin":
            relocate_macos(binary, home)
        case "Linux":
            relocate_linux(binary)
        case "Windows":
            relocate_windows(binary, home)
        case other:
            raise RuntimeError(f"unsupported platform: {other}")

    print(f"\nbundle ready: {DIST}")


if __name__ == "__main__":
    main()
