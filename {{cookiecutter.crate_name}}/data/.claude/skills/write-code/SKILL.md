---
name: write-code
description: Write idiomatic Rust for this workspace, with clear APIs, ownership, errors, and boundaries.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Writing Code

Use this skill when writing or editing Rust in this workspace. Use `port-code` when rewriting
existing code in Rust, `write-doc-comments` when documenting public items, and `test-code` when
adding tests. Use `cleanup-code` for a final review when the change warrants one.

## Layout

- Keep domain logic in `crates/core`, free of pyo3 and interpreter state. Put Python conversion
  in `crates/py`. Introduce a trait at a real variation or test boundary; a concrete dependency
  is simpler when there is one implementation and no need to abstract it.
- Keep command-line parsing and process setup in `crates/cli`. Move reusable behavior into the
  core when a second caller or test needs it.

## Rust

- Edition 2024. Warnings are errors (`mise run clippy`).
- Public items need docs; rustdoc intra-doc links must resolve (`mise run docs`). See
  `write-doc-comments`.
- Give callers actionable errors. Use `Result` for recoverable failures, and reserve `unwrap` or
  `expect` for invariants that can be explained at the call site.
- `unsafe` is denied or forbidden at the workspace; check `[workspace.lints.rust]`. Under `deny`,
  new `unsafe` needs `#[expect(unsafe_code)]` and a `// SAFETY:` comment. Under `forbid` no
  `allow` or `expect` can override it, so there is no `unsafe` to write.

{interop_rules}

## Design review

- Check the public API from a caller's point of view: names, ownership, invalid inputs, error
  types, and compatibility with existing users.
- Prefer the simplest ownership model that meets the actual lifetimes and concurrency needs.
  Add generics, trait objects, interior mutability, or extra crates when they solve a concrete
  problem.
- Keep correctness and performance requirements explicit. Profile representative workloads
  before changing data layout or adding low-level optimization.

## Commands

```sh
mise run check    # fmt, clippy, ruff, ty, rumdl, docs
mise run test     # the workspace's Rust tests
mise run py-test  # pytest
mise run all      # check + tests
```

Use the mise tasks for the full project checks: features and directories vary by interop mode.
Focused `cargo` or `pytest` commands are useful during development.
