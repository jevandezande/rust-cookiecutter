---
name: cleanup-code
description: Polishes recently written Rust for style, dead code, docs, and checks. Use when a coding task is done.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

Do a final cleanup pass on the code in $ARGUMENTS (or the current package if no argument is given).
Focus on the changed code and the project gate rather than rerunning every tool after every edit.

Use the `write-code` skill to understand code conventions.
Use the `test-code` skill to understand test conventions.
Use the `write-doc-comments` skill to understand doc comment conventions.

Review the diff for:

- Dead code, unused imports, commented-out code, and avoidable complexity.
- Public APIs whose names, ownership, errors, or documentation are unclear.
- New `unsafe` blocks. Check the workspace lint: `forbid` rules out unsafe; under `deny`, an
  explicit exception needs a sound `// SAFETY:` explanation.
{interop_rules}

Check changed public items against `write-doc-comments`. Run `mise run fmt` if formatting is
needed, then `mise run all` as the final local gate. It covers linting, docs, Rust tests, and the
mode's Python tests. Run a narrower check again only when its failure or a later edit calls for
it. Report any check that could not run.

If cleanup turns up a real bug, use `debug-code` to diagnose and test the fix.
