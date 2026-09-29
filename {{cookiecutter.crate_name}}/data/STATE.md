# State

Optional progress tracker for {{cookiecutter.project_name}}. Use it for modules that need a
durable spec or span several sessions. Keep it short: what is done, what is next, and any
unresolved difference between the code and its behavioral contract. Method-level detail belongs
in `docs/methods/` and `specs/` when those documents exist.

## Current Focus

Nothing yet. Name the module under way, and its state in a sentence or two.

## Next Action

Nothing yet. Name the next concrete step, specific enough to start from cold.

## Modules

One row per tracked module. `Spec Generated` is `n/a` when no spec is needed; tick a box once
that phase is done and green.

| # | Module | Spec Generated | Code Implemented | Tests Passing |
| --- | --- | --- | --- | --- |

## Deviations

Behavioral differences from a spec or method document, and intentional changes that need the
document updated. Private design changes need no entry unless they affect a stated constraint.
