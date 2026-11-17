---
name: compare-code-to-spec
description: Review Rust behavior against an existing spec and report meaningful gaps or changed assumptions.
argument-hint: <spec-file-or-module-name>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Compare Code to a Specification

Use this skill to review an implementation against its spec. Report findings without editing.

1. Locate the spec in `specs/`, the source, its tests, related method docs if relevant, and
   `STATE.md` if it tracks the module. Continue when an optional artifact is absent.
2. Extract observable requirements: public behavior, errors, invariants, compatibility,
   numerical tolerances, performance targets, and acceptance cases. Mark exact types, fields,
   signatures, or algorithms as binding only when the spec says why they must be preserved.
3. Trace each requirement through code and tests. Run focused checks if inspection cannot
   establish the result. Check important edge cases and what callers can observe.
4. Compare method equations and numerical requirements where the module implements a documented
   method. Equivalent formulations are acceptable when they satisfy the stated constraints.

Report each finding with a code location and one of these statuses:

| Status | Meaning |
| --- | --- |
| Satisfied | Evidence shows the behavior or constraint holds. |
| Unverified | The evidence is insufficient; name the check needed. |
| Mismatch | Observable behavior or a binding constraint differs. |
| Spec outdated | The implementation changed intentionally and the spec needs revision. |

Prioritize mismatches by impact. Explain suggested code, test, or spec updates and the evidence
for each. Do not flag extra code, private struct layout, or a different loop order as drift by
itself. If a changed loop order affects numerical results or a specified performance bound,
report that effect. State which checks ran and what remains unverified.
