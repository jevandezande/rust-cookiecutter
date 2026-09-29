---
name: generate-spec
description: Write a Rust implementation spec when behavior, constraints, and acceptance cases need a durable agreement.
argument-hint: <method-doc-or-feature>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
---

# Generate a Specification

Use this skill when a substantial feature or numerical method benefits from a durable spec.
Small changes and straightforward ports can use `write-code` or `port-code` directly. A method
document is useful for scientific work but is not a prerequisite for every module.

## Gather evidence

Read the method document at `$ARGUMENTS` if one exists. For a new feature, gather intended user
workflows, callers, project constraints, and acceptance examples; identify choices that still
need a decision. For a rewrite, inspect the original program's observable behavior, its callers,
and existing tests. Record unclear behavior rather than guessing. Research a method with
`plan-method-docs` when the available evidence cannot establish its requirements.

## Design the contract

{interop_rules}

- Define inputs, outputs, error behavior, and invariants. Include numerical tolerances, ordering,
  concurrency, and performance targets where they matter.
- State which public interfaces or file formats must remain compatible.
- Give representative acceptance cases, edge cases, and a way to compare a rewrite with its
  source. Prefer externally visible behavior over private implementation details.
- Discuss ownership, data layout, and crate boundaries as design options. Specify an exact
  struct or algorithm only when compatibility or a measured constraint requires it.

Write `specs/<module-name>.md` with the objective, behavioral contract, acceptance cases,
constraints, and design decisions. Link relevant method docs or source references. Add an
implementation outline only if it helps sequence substantial work; allow the implementer to
revise it as evidence emerges.

If `STATE.md` tracks this module, mark the spec complete and name the next action. Run
`mise run md-fmt` after writing the spec.
