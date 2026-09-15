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

## 1. Test Organization

- Inline unit tests: isolated logic and private helpers go in a `#[cfg(test)] mod tests` block at
  the bottom of the source file.
- Integration tests: public API workflows belong in `tests/` at the crate root.
- Fallible setup may return `Result` and use `?`. `.unwrap()` is acceptable in tests.

## 2. Floating-Point

`assert_eq!` is correct for exact values. Use `approx` (if you add it) only when the result is
inexact: iterative solvers, transcendentals, or comparisons across implementations.

```rust
assert_eq!(best_score(&scorer, &[1.0, 16.0, 4.0]).unwrap(), Some(4.0));
assert!((scorer.score(9.0).unwrap() - 3.0).abs() < f64::EPSILON);
```

{interop_rules}

## 4. Optional Crates

`rstest` and `proptest` are not dependencies. Add them when a table of cases or a property earns
them, not for a single extra `#[test]`.
