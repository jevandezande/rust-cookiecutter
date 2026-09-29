---
name: write-doc-comments
description: Writes and reviews rustdoc doc comments. Use when writing new doc comments, reviewing existing ones, or editing them.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Writing Doc Comments

Required for: every public item. `missing_docs = "warn"` in `[workspace.lints.rust]` and warnings
are errors, so a public module, struct, enum, trait, function, method, field, variant, type alias,
const, or macro without a doc comment fails `mise run clippy`.

## Format

1. `///` above an item; `//!` inside a crate root or module file, before any `use`. On a `mod`
   block, put `///` above the block rather than `//!` inside it
2. Summary is one sentence in third-person indicative, ending in a period: "Returns", "Creates",
   "Converts", "Parses". A type or iterator may take a noun phrase instead: "Scorer backed by ..."
3. Blank `///` line between the summary and anything after it. Only the first paragraph shows in
   the item list, so keep the summary to one line
4. Add `# Panics`, `# Errors`, and `# Safety` when they describe a real contract. Use
   `# Examples` on entry points where an example helps a caller. Other headings are fine when
   they clarify substantial behavior
5. Blank `///` line between a section heading and its body
6. Usually explain parameters and return values in prose near the summary. Add a dedicated
   section only when it makes a complex contract easier to understand
7. No pseudo-annotations: the signature carries the types, so never restate a parameter's type
   beside its name. When prose does name a generic type, write it in full, `Option<T>` rather than
   `Option`, except in a bound
8. Describe conditions in clear, complete language. A short fragment is fine when it reads well
9. Backtick code identifiers; link important public items when a link helps navigation

## Example

```rust
/// Sums spam counts by category, dropping categories that total below `threshold`.
///
/// Repeated categories merge, so ordering of `input` does not matter. Scores through
/// [`NativeScorer`], so a caller wanting different weighting supplies its own [`Scorer`].
///
/// # Errors
///
/// Returns [`NegativeThreshold`] if `threshold` is negative.
///
/// # Examples
///
/// ```
/// use spam::process_spam;
///
/// let counts = [("jalapeno", 5), ("regular", 3), ("jalapeno", 9), ("low sodium", 1)];
/// assert_eq!(process_spam(&counts, 2)?["jalapeno"], 14);
/// # Ok::<(), spam::NegativeThreshold>(())
/// ```
pub fn process_spam(
    input: &[(&str, i64)],
    threshold: i64,
) -> Result<HashMap<String, i64>, NegativeThreshold> {
```

## Incorrect example (do not do this!)

```rust
/// process spam counts                              // ❌ fragment, lowercase, no period
///
/// # Arguments                                      // ❌ adds a section for simple inputs
/// * `input` - A list of spam counts to process.    // ❌ repeats an obvious input
/// * `threshold` (i64) - The minimum count.         // ❌ type already in the signature
///
/// # Returns                                        // ❌ repeats a simple return type
/// A HashMap mapping categories to counts.          // ❌ unlinked type, repeats signature
///
/// # Errors
/// Returns an error if the threshold is negative.   // ❌ no blank line after the heading;
///                                                  //    name the error for the caller
///
/// # Example                                        // ❌ section is Examples, even for one
///
/// let out = process_spam(&counts, 2);              // ❌ unfenced, so rustdoc will not test it
```

## Sections

- `# Panics` — `clippy::missing_panics_doc` is `warn`, so any public function that can panic needs
  one. Explain the condition that can panic.
- `# Errors` — `clippy::missing_errors_doc` is `warn`, so every public `fn` returning `Result`
  needs one. Name the failures and what a wrapper propagates.
- `# Safety` — only on `unsafe fn`. `unsafe_code` is `deny` or `forbid` at the workspace, so this
  is rare; when it applies, state the invariant the caller must uphold. Do not add the section to
  a safe function, and keep it distinct from the `// SAFETY:` comment on an `unsafe` block, which
  argues why the call site is sound.
- `# Examples` — plural even with one example.

## Examples are tests

- Fenced code in `# Examples` compiles and runs under `mise run test`. A stale example is a test
  failure, not a typo.
- Hide a setup line from the rendered page by starting it with `#` and a space inside the fence.
- End a `?`-using example with a hidden `# Ok::<(), ErrType>(())` rather than switching to
  `unwrap`.
- `no_run` compiles without running; `ignore` does neither and hides breakage, so prefer `no_run`
  and give `ignore` a reason when it is unavoidable.
- Tag a fence that is not Rust with its language (`text`, `sh`, `python`), or rustdoc tries to
  compile it. A Rust fence needs no tag: rustdoc assumes Rust.
- Examples belong on the entry points a caller reaches for, not on every method.

## Links

- Link items by path: [`Scorer`], [`Scorer::score_all`], [`crate::best_score`].
- `rustdoc::broken_intra_doc_links` is `deny`, so `mise run docs` fails on a path that does not
  resolve. Run it after renaming or moving a public item.
- Link an item on its first useful mention in a doc block, not on every mention.
- Wrap a bare URL in `<>`. Use inline or reference-style links for external sources, whichever
  keeps the comment easier to read.

## Module and crate docs

- **Crate root:** `//!` at the top of `lib.rs`, before any `use`. State what the crate is, where
  its boundary sits, and link the two or three items that are the way in.
- **Module:** one sentence on what the module holds, plus what does not belong in it when that is
  not obvious.
- `main.rs` takes `//!` too: what the binary does, not how the library works.

## Doc comments that are not rustdoc

`clap` turns the doc comment on a `#[derive(Parser)]` struct, field, or variant into `--help`
text, and pyo3 turns the one on a `#[pyfunction]` or `#[pyclass]` into Python's `__doc__`. Those
follow their own conventions, not this file: keep CLI help short and imperative, and describe a
Python-facing signature the way a Python caller reads it.

## Miscellaneous

- Write from the caller's point of view.
- Line comments only. `//` and `///`, never `/* */`.
- Do not restate the signature: "Takes an `f64` and returns an `f64`" says nothing the reader
  cannot see.
- `///` is for what a caller needs; `//` is for why the implementation does it that way. Do not
  promote an implementation note into public docs.
- Private items need no doc comment, but a non-obvious one earns a `//` comment.
- Prefer Unicode superscripts for single digit superscripts, e.g. Å².
- Never add `#[allow(missing_docs)]`, `#[expect(missing_docs)]`, or a lint change in `Cargo.toml`
  to silence a docs warning without explicitly asking.
