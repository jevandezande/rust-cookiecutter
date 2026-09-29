---
name: port-code
description: Rewrite an existing program or module in Rust while preserving agreed behavior and choosing an idiomatic architecture.
argument-hint: <source-path-or-feature>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
---

# Port Existing Code to Rust

Use this skill for a rewrite from another language or another Rust design. Load `write-code` for
workspace conventions and `test-code` for test choices. A method document or formal spec is
optional; use `generate-spec` when complex behavior needs a durable agreement.

## Establish what must survive

1. Inventory the entry points and callers. Record observable outputs, error cases, ordering,
   file formats, numerical behavior, and platform assumptions that users rely on.
2. Run the original code or its tests when available. Save a small set of representative and
   boundary cases with expected results. When the original cannot run, identify the strongest
   available evidence and mark uncertain behavior.
3. Separate compatibility requirements from implementation accidents. Record deliberate changes
   to behavior or public APIs so reviewers can evaluate them.

## Choose the Rust design

- Sketch crate and module boundaries around responsibilities and callers. Keep Python interop at
  the boundary specified by this workspace.
- Decide who owns data, where conversion happens, what can fail, and which operations need
  concurrency. Use traits for genuine variation or useful dependency boundaries.
- Preserve algorithmic invariants without copying the source language's class structure or
  control flow line by line. Check integer overflow, text encoding, floating-point tolerance,
  iteration order, and panic behavior when the source language differs from Rust.
- Review the proposed API from a Rust caller's point of view before expanding it. Keep a brief
  design note only if it will help with a substantial or multi-session port.

## Port and verify

Implement coherent, externally useful slices. Compare Rust results with the original fixtures
or an independent reference, including errors and edge cases. Add focused tests that explain the
contract; use property tests or larger data sets when they can find failures ordinary examples
miss. Run focused checks as you work and `mise run all` for the final project gate.

Measure performance on representative inputs if the port has a performance target. Use
`benchmark-code` and `optimize-code` after correctness is established. Report behavioral changes,
test evidence, unresolved differences, and any compatibility or performance limits.
