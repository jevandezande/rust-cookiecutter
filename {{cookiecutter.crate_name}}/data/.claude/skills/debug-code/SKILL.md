---
name: debug-code
description: Debugging workflow for runtime errors, panics, and Rust-specific issues.
argument-hint: [error description or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - Task
---

# Debug Code

Use this skill to diagnose and fix runtime panics, wrong results, and Rust-specific issues.

## Workflow

### Phase 1: Reproduce & Characterize

1. Read the error description or file at `$ARGUMENTS`.
2. Reproduce the error by running the failing test or command. Capture the full output,
   including backtraces (`RUST_BACKTRACE=1`).
3. Classify the error type:

| Category | Indicators |
|---|---|
| Panic / Assert | `thread panicked`, `assertion failed`, `unwrap()` on `None`/`Err` |
| Numerical | NaN, Inf, unexpected values, precision loss |
| Memory Safety | Segfault, use-after-free, data race (often in `unsafe` blocks) |
| Type / Borrow | Compile errors from borrow checker, lifetime issues, type mismatches |
| Logic | Wrong results with no crash |

---

### Phase 2: Isolate

1. Minimize the reproduction: find or write the smallest test that triggers the error. If the
   failure is in a large integration test, extract the failing sub-computation into a unit test.
2. Find the blast radius: `grep` for callers of the failing function and decide whether other
   modules are affected.
3. Check recent changes with `git log --oneline -20` and `git diff HEAD~3`.

---

### Phase 3: Diagnose

Pick the strategy for the error category:

#### Numerical Issues

- Insert `assert!(value.is_finite(), "...")` guards at intermediate steps to find where NaN or Inf
  first appears.
- Compare `f32` vs `f64` results to identify precision-sensitive operations.
- Check for division by zero or near-zero denominators (add epsilon guards).
- Check for catastrophic cancellation when subtracting nearly equal large numbers.
- Verify loop bounds and index calculations. If a spec or method doc exists, check against it.
- Check convergence criteria: is the threshold too tight for the precision used?

#### Memory Safety Issues

- Run under Miri where possible: `cargo +nightly miri test <test_name>`.
- Audit `unsafe` blocks in the failing code path. Verify every `// SAFETY:` comment still holds.
- Look for aliased mutable references or dangling pointers at FFI boundaries.

#### Logic Errors

- Compare against a known-good reference implementation or published reference values.
- Log or assert intermediate values and compare them with hand calculations on a minimal case.
- If a spec or method doc exists, verify the implementation against it step by step.
- Check index ordering: 0-indexed vs 1-indexed, off-by-one errors.

---

### Phase 4: Fix

1. Fix the root cause with the smallest change that does it.
2. Add a regression test for the bug.
3. Add or improve `// SAFETY:` comments, `debug_assert!` guards, or documentation.
4. If the fix changes observable behavior, note whether any spec or method doc needs updating. Do
   not update those docs in this skill.

---

### Phase 5: Verify

1. Run the previously failing test: confirm it passes.
2. Run the full test suite for the affected crate: `cargo test -p <crate>`.
3. Run clippy: `cargo clippy --workspace --all-targets -- -D warnings`.
4. If the bug was in a hot path, say that the benchmarks need rerunning (the `benchmark-code`
   skill).

For slow test suites, use the `async-workflows` skill to run verification in the background.
