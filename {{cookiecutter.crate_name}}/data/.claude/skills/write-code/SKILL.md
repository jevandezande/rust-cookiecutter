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
- Give callers actionable errors. Return `Option` when the cause of a failure is obvious and
  `Result` when the caller needs to know why. Panic only on a bug: a broken invariant the types
  cannot express.
- Outside tests, prefer `expect` to `unwrap`, with a message saying what should hold. Give
  `assert!` and `expect` messages context or the offending value
  (`"threshold must be non-negative, got {threshold}"`) rather than restating the condition.
- Annotate a binding whose type is not evident: the result of `.parse()`, `.into()`,
  `.collect()`, or a long iterator chain. Prefer `let x: T` to a turbofish.
- Keep iterator chains short. Bind a chain to a name rather than building it in a `for` header,
  and write a loop when the chain branches or mutates outside state.
- Reach for a function, type, or trait before a macro, and `macro_rules!` before a proc macro.
- `unsafe` is denied or forbidden at the workspace; check `[workspace.lints.rust]`. Under `deny`,
  new `unsafe` needs `#[expect(unsafe_code)]` and a `// SAFETY:` comment. Under `forbid` no
  `allow` or `expect` can override it, so there is no `unsafe` to write.

{interop_rules}

## Design review

- Check the public API from a caller's point of view: names, ownership, invalid inputs, error
  types, and compatibility with existing users. Follow the
  [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/) for naming, conversions,
  and common traits.
- Wrap values that are easy to confuse in a newtype (Bohr and Ångström, a row and a column
  index). Prefer named fields to multi-field tuples, and an enum to a `bool` parameter whose
  meaning is not obvious at the call site.
- Prefer the simplest ownership model that meets the actual lifetimes and concurrency needs.
  Borrow rather than `.clone()` to satisfy the borrow checker, and use `Rc` or `Arc` only for
  genuinely shared ownership. Add generics, trait objects, interior mutability, or extra crates
  when they solve a concrete problem.
- Flexibility such as `impl IntoIterator` parameters or iterator return types can pay off in
  `crates/core`'s public API. Elsewhere take and return concrete types; `impl Into<T>`
  parameters rarely earn their code size.
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
