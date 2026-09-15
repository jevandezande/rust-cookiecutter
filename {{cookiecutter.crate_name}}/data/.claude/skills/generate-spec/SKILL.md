---
name: generate-spec
description: Translates a method document into a concrete Rust software specification.
argument-hint: <math-doc-path>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
---

# Generate Specification from Theory

Use this skill to convert a method document (`docs/methods/*.md`, once one exists) into an
engineering blueprint (`specs/*.md`).

## Phase 1: Understand

1. Read the method document at `$ARGUMENTS`.
2. Work out the equations, the complexity, and whether the algorithm is compute-bound or
   memory-bound.

## Phase 2: Design

Design the Rust implementation details:

- {interop_rules}
- Memory layout: choose types that match how the data is walked. Call out ownership and borrowing.
- Function signatures: draft the core Rust traits, structs, and function signatures.

## Phase 3: Write Spec

Write the specification file to `specs/<module-name>.md`.
The spec must contain these sections:

```markdown
# Spec: <Module Name>

## Objective

What this module implements, in a sentence or two.

## Mathematical Mapping

How the documented steps map to variables and functions in code. Link back to the method doc.

## Data Structures & Memory Layout

Define the exact Rust structs, their fields, and ownership.

## Implementation Steps

An ordered list of small slices that build this module. Each slice must be testable on its own.

1. Define core structs.
2. Implement a straightforward reference version.
3. Add tests for the documented cases.
4. Optimize only after the tests pass.
```

## Phase 4: Update State

In `STATE.md` at the root, tick the "Spec Generated" box for this module and set Next Action to
implementing the spec.

Run `mise run md-fmt` and fix anything it reports.

---

If the method document at `$ARGUMENTS` is missing or incomplete, research the topic with
`plan-method-docs`, write it with `write-method-docs`, then return here.
