---
name: test-code
description: Guidelines for testing Rust in this workspace, including the Python boundary.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Testing Guidelines

This skill covers Rust tests. pytest has its own skill, `test-python`.

## 1. Test Organization

- Inline unit tests: isolated logic and private helpers go in a `#[cfg(test)] mod tests` block at
  the bottom of the source file.
- Integration tests: public API workflows belong in `tests/` at the crate root.
- Fallible setup may return `Result` and use `?`. `.unwrap()` is acceptable in tests.
- Prefer tests of observable behavior and invariants over tests that duplicate private code.
  For a rewrite, compare representative results and errors with the original program or an
  independent reference.

## 2. Floating-Point

`assert_eq!` is correct when the contract requires exact values. For inexact results, choose
absolute and/or relative tolerances from the problem's scale and error budget. `f64::EPSILON` is
the spacing near 1.0, not a general-purpose tolerance. Add `approx` when it makes those
comparisons clearer.

```rust
assert_eq!(best_score(&scorer, &[1.0, 16.0, 4.0]).unwrap(), Some(4.0));
assert!((scorer.score(9.0).unwrap() - 3.0).abs() < 1e-12);
```

{interop_rules}

## 4. Optional Crates

`rstest` and `proptest` are not dependencies. Add them when a table of cases or a property earns
them, not for a single extra `#[test]`.

## 5. Tests That Need What a Machine May Lack

A test never checks for a device, a program, or a file and returns early: libtest counts that as
a pass, so a machine that cannot run the test reports it green. Gate it so the run shows what it
skipped, and give the reason a reader can act on:

- a platform or an optional feature:
  `#[cfg_attr(not(target_os = "linux"), ignore = "needs Linux")]`. Use `#[cfg(...)]` only when
  the test does not compile elsewhere
- an external program, the network, or a large fixture: `#[ignore = "needs <what>"]`, run with
  `cargo test -- --ignored` where it is available
- a release build: `#[cfg_attr(debug_assertions, ignore = "too slow unoptimized")]`
