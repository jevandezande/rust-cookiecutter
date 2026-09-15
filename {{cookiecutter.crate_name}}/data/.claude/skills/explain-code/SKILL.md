---
name: explain-code
description: Explains existing code by identifying algorithms and cross-referencing docs and specs when they exist.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - WebFetch
  - Task
---

# Explain Code

Use this skill to work out what existing code does, name the algorithms it implements, and find
any documentation or specifications that cover it.

This skill is read-only and edits no files.

## Workflow

### Phase 1: Locate & Read

1. Read the target file(s) at `$ARGUMENTS` in full.
2. Identify which crate and module the code belongs to.
3. Read the surrounding context: the parent `mod.rs` or `lib.rs`, any re-exports, and closely
   related modules.
4. Check `Cargo.toml` for dependencies that inform the code's purpose.

### Phase 2: Identify Algorithms

1. Name the algorithm or procedure the code implements. Map loops and data transforms to that
   procedure.
2. Note constants, thresholds, and magic numbers, and explain where they come from.
3. If you do not recognize the algorithm, look up the method name, function name, or key patterns
   with `WebFetch`.

### Phase 3: Cross-Reference Documentation

If `docs/methods/`, `docs/methods/research/`, or `specs/` exist, search them for a matching
write-up. For each match, identify:

- Which documented steps correspond to which lines of code.
- Which functions or structs fulfil which spec requirements.
- Any discrepancies. Note them without fixing them, and suggest `compare-code-to-spec` for a formal
  audit.

If those directories are absent, skip this phase.

### Phase 4: Explain Design Decisions

1. Data layout: explain the choice of types and memory layout.
2. Performance: explain loop orderings, allocations, `unsafe` blocks, and caching.
3. Error handling: how the code treats errors and edge cases (panics, `Result` propagation,
   sentinel values).

---

## Required Output Structure

Present the explanation using this exact structure:

```markdown
## Overview

*One paragraph: what this code does and where it fits in the codebase.*

## Algorithm

*Name the algorithm(s) implemented. Provide a brief description and cite the
relevant paper or textbook if known.*

## Key Steps

*The core procedure the code implements, with file:line pointers.*

## Walkthrough

*Step-by-step walkthrough of the code's control flow, annotated with
what each section does.*

## Data Structures

*Explain the key data structures and why they are shaped this way.*

## Performance Notes

*Hot paths, allocations, and their performance implications.*

## Cross-References

*Method docs, research briefs, or specs if they exist; otherwise omit.*

## Gaps & Suggestions

*Any code that lacks documentation, unclear sections, or potential
improvements worth investigating.*
```
