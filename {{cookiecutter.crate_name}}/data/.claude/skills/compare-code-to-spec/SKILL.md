---
name: compare-code-to-spec
description: Audits existing code against its specification and method documentation, generating a drift report with suggested updates.
argument-hint: <spec-file-or-module-name>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Task
---

# Compare Code to Specification

Use this skill to audit an implementation against its specification and method documentation.
It makes no edits. It reports drift, missing features, and deviations, and suggests updates for
the user to approve.

## Workflow

### Phase 1: Locate Artifacts

`$ARGUMENTS` is a spec file path or a module name.

1. Find the spec in `specs/`. For a module name, look for `specs/<module-name>.md` or similar.
2. Find method documentation in `docs/methods/`, if that directory exists.
3. Find a research brief in `docs/methods/research/`, if that directory exists.
4. Find the source with `glob` and `grep`.
5. Check `STATE.md` for pipeline status, if that file exists.

Note any missing artifact in the report and continue with what exists.

---

### Phase 2: Parse Spec Requirements

Extract from the spec:

- Implementation steps - the ordered list of work items
- Data structures - struct names, field types, layout requirements
- Function signatures - public API surface
- Test requirements - expected test cases and validation criteria
- Dependency requirements - crates, features

---

### Phase 3: Parse Method Documentation

Extract from the method doc:

- Key equations and their variable definitions
- Algorithm description - expected computational procedure
- Numerical considerations - precision, stability requirements
- Performance characteristics - expected complexity, memory usage

---

### Phase 4: Audit Code Against Spec

For each spec requirement, determine its status in the codebase:

| Status | Meaning |
|---|---|
| Implemented | Code fully satisfies the requirement. |
| Partial | Code exists but is incomplete or differs in scope. |
| Missing | No corresponding code found. |
| Deviated | Code implements the requirement differently than specified. |
| Extra | Code that no spec requirement covers. |

Specific checks:

1. Compare struct definitions against spec data structures (field names, types, derives).
2. Compare function signatures against spec API surface.
3. Check that specified tests exist and cover the required cases.

---

### Phase 5: Audit Code Against Method Documentation

Verify mathematical correctness:

1. For each key equation in the method doc, find the corresponding code and check that it
   matches.
2. Check the numerical requirements: `f64` where required, stability guards where specified.
3. Check that the algorithm follows the documented procedure: loop nesting, summation order.
4. Check that `rustdoc` comments reference the correct equations.

---

### Phase 6: Generate Drift Report

Present findings in this format:

```markdown
## Drift Report: <Module Name>

**Spec:** `specs/<module>.md`
**Method Doc:** `docs/methods/<topic>.md`
**Source:** `src/<path>/`
**STATE.md status:** [current status]

### Summary

*One-paragraph overview of conformance.*

### Spec Conformance

| # | Spec Requirement | Status | Code Location | Notes |
|---|---|---|---|---|
| 1 | [requirement] | Implemented / Partial / Missing / Deviated | file:line | [details] |
| ... | ... | ... | ... | ... |

### Method Doc Conformance

| Equation / Section | Status | Code Location | Notes |
|---|---|---|---|
| Eq. (N): [description] | Correct / Incorrect / Missing | file:line | [details] |
| ... | ... | ... | ... |

### Undocumented Code

*Code that exists but has no corresponding spec or method doc coverage.*

| Code Location | Description | Suggested Action |
|---|---|---|
| file:line | [what the code does] | Add to spec / Remove / Investigate |

### Suggested Updates

*Prioritized list of changes. Each says whether to update the code, the spec,
or the method doc.*

1. **[Priority: High/Medium/Low]** [Description of change needed]. Update: [code / spec / method doc].
2. ...
```

---

### Phase 7: Suggest Next Steps

After presenting the report:

1. Make no edits.
2. Ask the user which suggestions to act on.
3. For code changes, suggest the `implement-spec` skill.
4. For spec changes, suggest the `generate-spec` skill.
5. For method doc changes, suggest the `write-method-docs` skill.
