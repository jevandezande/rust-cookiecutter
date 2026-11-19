---
name: implement-spec
description: Implement an existing Rust specification, checking behavior and adapting design as evidence emerges.
argument-hint: <spec-file>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
---

# Implement a Specification

Use this skill when the task is to implement an existing spec. Use `port-code` instead when
rewriting an existing program in Rust and no spec is required.

## Understand the contract

1. Read the spec at `$ARGUMENTS`, related method docs when relevant, and the code it affects.
   Read `STATE.md` if the project uses it for this module.
2. Separate observable requirements and invariants from suggested structs, signatures, and
   implementation steps. Preserve the former; revise the latter when Rust or new evidence gives
   a better design. Check for callers that depend on a specified public API before changing it.
3. Identify the acceptance cases, error behavior, and any numerical or performance constraints.
   Resolve contradictions in the source material before relying on them.

## Implement

- For a small change, work directly. For work spanning several sessions or independent pieces,
  keep one concise plan in the project's existing tracker. Create a new plan file only when it
  will help someone resume the work.
- Build coherent slices that exercise useful behavior. Write tests for acceptance cases,
  boundaries, and regressions; do not add tests that merely repeat the implementation.
- Follow `write-code` for Rust conventions, `test-code` for test choices, and
  `write-doc-comments` for public API documentation.
- Run focused checks while working. Use `mise run all` when the implementation is ready for the
  full local gate. Run additional checks, such as `mise run msrv` or a benchmark, when the change
  affects those concerns. Use `async-workflows` for commands that need background execution.
- When a design changes, update the spec or record the reason for the deviation. If behavior
  changes, update the acceptance cases and any affected method documentation.

## Finish

Review the diff for API clarity, ownership, error handling, unsafe code, and accidental changes.
Use `cleanup-code` for the final polish. Update `STATE.md` if this module is tracked there, and
report what passed and what remains uncertain.

Do not discard uncommitted work with `git reset --hard` or `git clean`. Do not stage or commit as a
checkpoint; follow the project's Git instructions and the user's request for commits.
