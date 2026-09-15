---
name: write-code
description: Write idiomatic, high-performance Rust for this workspace.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Writing Code

Use this skill when writing or editing Rust in this workspace. Load `write-doc-comments` when
documenting public items, `test-code` when adding tests, and `cleanup-code` when the change is
done.

## Layout

- `crates/core` is pure Rust. No pyo3, no `Python::attach`, no `PYO3_*` env. Anything it needs
  from outside is a trait, implemented by the layer around it.
- `crates/cli` is a thin binary (`clap`, `tracing`). Logic does not live here.

## Rust

- Edition 2024. Warnings are errors (`mise run clippy`).
- Public items need docs; rustdoc intra-doc links must resolve (`mise run docs`). See
  `write-doc-comments`.
- Prefer `Result` and typed errors over `unwrap` outside tests.
- `unsafe` is denied or forbidden at the workspace; check `[workspace.lints.rust]`. Under `deny`,
  new `unsafe` needs `#[expect(unsafe_code)]` and a `// SAFETY:` comment. Under `forbid` no
  `allow` or `expect` can override it, so there is no `unsafe` to write.

{interop_rules}

## Commands

```sh
mise run check    # fmt, clippy, ruff, ty, rumdl, docs
mise run test     # the workspace's Rust tests
mise run py-test  # pytest
mise run all      # check + tests
```

Run the task, not the cargo or pytest command under it. The features it enables and the
directories it covers vary by interop mode.
