{%- set pkg = cookiecutter.__package_name -%}
"""The stub declares exactly the names the compiled module exports."""

import ast
from pathlib import Path

from {{pkg}} import _core

STUB = Path(__file__).parent.parent / "python" / "{{pkg}}" / "_core.pyi"


def declared_names(stub: Path) -> set[str]:
    """Collect the names a stub file declares at module level.

    Args:
        stub: `.pyi` file to parse

    Returns:
        Names of the module-level functions, classes, and annotated variables
    """
    names: set[str] = set()
    for node in ast.parse(stub.read_text(encoding="utf-8")).body:
        match node:
            case ast.FunctionDef(name=name) | ast.ClassDef(name=name):
                names.add(name)
            case ast.AnnAssign(target=ast.Name(id=name)):
                names.add(name)
            case _:
                pass
    return names


def test_stub_matches_the_module() -> None:
    """Declare every public name `_core` exports, and nothing it does not.

    Signatures are not compared; keep those in step by hand.
    """
    exported = {name for name in dir(_core) if not name.startswith("_")}
    assert declared_names(STUB) == exported
