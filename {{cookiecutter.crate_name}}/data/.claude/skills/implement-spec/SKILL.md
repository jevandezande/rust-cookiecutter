---
name: implement-spec
description: Plans and implements Rust code from a specification file using a strict iterative workflow with git checkpoints.
argument-hint: <spec-file>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - Task
---

Implement code from the specification file: $ARGUMENTS

Follow this workflow exactly. Do not skip phases.

---

## Phase 1: Understand

1. Read `STATE.md` in the root directory.
2. Read the spec file at `$ARGUMENTS` in full.
3. Read any method documentation the spec links. Skip this if no method doc exists yet.
4. Explore the codebase with `glob` and `grep` to find existing utilities.

---

## Phase 2: Plan & Track

Write `PLAN.md` and `TODO.md` in the root (or target crate) directory.

`PLAN.md` must contain:

- Goal: brief summary.
- Spec Reference: path to the spec.
- Dependencies: any new crates. Do not add without user approval.
- Implementation Steps: break the spec's steps into smaller, isolated, testable slices.

`TODO.md` must be a flat checklist, one item per Implementation Step.

`TODO.md` and `TodoWrite` serve different purposes. Use both:

- `TODO.md` persists across sessions. Update it whenever you complete a step.
- `TodoWrite` shows the user live progress. Mirror the `TODO.md` items into it at the start of
  Phase 4, and update both as you go.

---

## Phase 3: Permissions

Summarize the planned actions: files to create or modify, shell commands, new dependencies.
Ask: "Do you approve these actions? Any changes before I begin?"
Wait for explicit approval.

---

## Phase 4: Execute & Checkpoint

Work through the `TODO.md` items one slice at a time.
For each item:

1. Write the code and unit tests. Public items get `///` rustdoc. If a method doc exists,
   reference the matching steps or equations.
2. Run the checks:
   - `cargo fmt --all`
   - `cargo clippy --workspace --all-targets -- -D warnings`
   - `cargo test` (or specific test path)
3. If tests fail, fix them before moving on. If a borrow-checker or link error has you stuck,
   `git reset --hard HEAD` and `git clean -fd` return you to the last checkpoint to try another
   approach.
4. If tests pass, commit immediately to save the checkpoint.
   - `git add .`
   - `git commit -m "Implement [slice name] for [module]"`
5. Mark the item `[x]` in `TODO.md`.

For slow tests or compiles, run them in the background with the `async-workflows` skill.

---

## Phase 5: Cleanup & State Update

1. Invoke the `cleanup-code` skill.
2. In `STATE.md`, check off "Code Implemented" and "Tests Passing" for this module, then update
   Current Focus and Next Action.
3. Delete `PLAN.md` and `TODO.md`.
4. Optionally, run `compare-code-to-spec` to verify the implementation satisfies the spec.
5. Tell the user the module is complete.
