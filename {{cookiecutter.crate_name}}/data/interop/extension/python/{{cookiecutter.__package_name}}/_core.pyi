# Stubs for the compiled module: `py.typed` alone says nothing about its contents, and a cdylib
# carries no types. Keep this in step with `crates/py/src/lib.rs`; `tests/test_stubs.py` checks the
# names, not the signatures.

from collections.abc import Sequence

class ScoreError(Exception): ...

def best_score(xs: Sequence[float]) -> float | None: ...
