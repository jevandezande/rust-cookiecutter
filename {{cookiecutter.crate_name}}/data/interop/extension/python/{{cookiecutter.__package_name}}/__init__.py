{%- set pkg = cookiecutter.__package_name -%}
"""{{cookiecutter.project_name}}.

Public API of the extension. `_core` is the compiled module built from `crates/py`; import from
this package rather than from it, so the Rust side can be reorganized without breaking callers.

Examples:
    >>> from {{pkg}} import best_score
    >>> best_score([1.0, 16.0, 4.0])
    4.0
"""

from ._core import ScoreError, best_score

__all__ = ["ScoreError", "best_score"]
