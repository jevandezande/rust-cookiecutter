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

Use the `write-code` skill to understand code conventions.
Use the `test-code` skill to understand test conventions.
Use the `write-doc-comments` skill to understand doc comment conventions.

Work through this checklist:

1. Formatting:
   - Run `mise run fmt` to format the codebase.

2. Linting:
   - Run `mise run clippy` and fix all warnings.

3. Safety:
   - Scan the diff for new `unsafe` blocks. Each needs `#[expect(unsafe_code)]` and a `// SAFETY:`
     comment.

4. Code Polish:
   - Remove dead code, unused imports, and commented-out code.
{interop_rules}

5. Documentation:
   - Check every public item the diff added or changed against `write-doc-comments`.
   - Run `mise run docs` and fix broken intra-doc links.

6. Tests:
   - Run `mise run test` and `mise run py-test`.

7. Final Check:
   - `mise run check` must pass before finishing.

If cleanup turns up a real bug rather than a style or lint issue, switch to the `debug-code` skill.
