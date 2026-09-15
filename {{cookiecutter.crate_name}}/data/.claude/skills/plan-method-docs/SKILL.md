---
name: plan-method-docs
description: Conducts an exhaustive literature review, analyzes algorithmic tradeoffs, identifies key optimizations with citations, and generates a comprehensive Markdown research brief for complex scientific or mathematical methods.
argument-hint: <method-or-topic-name>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - WebFetch
  - Task
---

# Research and Plan Scientific Method Documentation

Use this skill to research a scientific, mathematical, or numerical method and write a research
brief before the method documentation. The brief grounds the implementation in the most robust
and efficient algorithms available.

## Workflow

### Phase 1: Literature Review

1. Use `WebFetch` to find and read textbooks, peer-reviewed papers, arXiv preprints, and recent
   algorithmic reviews on the topic (`$ARGUMENTS`).
2. Read the methodology sections, not just the abstracts, to understand the math and the
   complexity. Where approaches compete, research all of them.
3. If the literature is large, use the `Task` tool to read papers in parallel.
4. Reading PDFs:
   - The `Read` tool reads local PDFs. Download papers to `docs/papers/` and read them there.
   - To extract text with the LaTeX equations intact, run
     `uvx marker_pdf docs/papers/paper.pdf docs/papers/`, which writes a markdown file beside
     the PDF. `uvx` needs no installation.
   - arXiv papers often have an HTML version at `https://arxiv.org/html/XXXX.XXXXX`. Prefer it
     with `WebFetch` when it exists.
5. Paywalled papers. Before declaring a source inaccessible, check these in order:
   - arXiv or a field preprint server: search by title or author.
   - Unpaywall: fetch `https://api.unpaywall.org/v2/{DOI}?email=user@example.com` with
     `WebFetch` for URLs of legal open-access copies.
   - Semantic Scholar: fetch
     `https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf` for direct
     PDF links.
   - PubMed Central, for NIH-funded work.
   - The author's lab or institution page, which often hosts a PDF.

   If the paper is still inaccessible, take what the abstract and preview offer, record the DOI
   and citation, and move on.
6. `WebFetch` limitations:
   - It may truncate long pages. Fetch specific sections through anchored URLs
     (e.g. `https://en.wikipedia.org/wiki/Topic#Section`) rather than whole pages.
   - It cannot fetch PDF URLs. Download the PDF to `docs/papers/` and use `Read`.
   - For large topics, make one targeted fetch per sub-topic or algorithm variant rather than one
     broad fetch.

### Phase 2: Key Principles

Extract the governing equations, objective functions, or principles that define the method. Note
its inputs and outputs.

### Phase 3: Algorithmic Variants & Optimizations

1. Identify how the method is solved in practice (recursive vs. iterative, naive vs. screened).
2. Identify the domain optimizations (spatial partitioning, screening bounds, sparsity, low-rank
   approximations).
3. Cite every optimization with a link or DOI to the paper that introduced or popularized it.

### Phase 4: Computational Mapping

1. Note whether the method is typically compute-bound or memory-bound.
2. Note memory access patterns (contiguous vs. scattered) and any obvious parallelism.

### Phase 5: Numerical Considerations

Identify numerical hazards (catastrophic cancellation, ill-conditioned matrices, division by
small numbers) and precision requirements (where `f64` is required and where `f32` suffices).

### Phase 6: Document Generation

Write the findings to `docs/methods/research/<topic>-research.md`.

Run `mise run md-fmt` and fix anything it reports.

---

## Required Output Structure

The brief must follow this structure:

```markdown
# Research Brief: <Method Name>

## 1. Literature Review & Sources

*Every paper, book, and resource read. Each entry includes:*

- *DOI or Link*
- *One or two sentences on what the source contributes.*

## 2. Core Mathematical Principles

*The equations and theory that define the method.*

## 3. Algorithmic Variants

*The algorithms used to implement the method, with their time and space complexities.*

## 4. Key Optimizations

*The optimizations that make the method feasible in practice.*

- [Optimization Name]: [Description of how it reduces complexity or time]. Reference: [DOI/Link]
- [Optimization Name]: [Description]. Reference: [DOI/Link]

## 5. Computational Mapping

*Whether the method is compute-bound or memory-bound, and any obvious parallelism or locality
constraints.*

## 6. Numerical Considerations

*Floating-point stability, precision constraints, and error accumulation.*

## 7. Proposed Documentation Outline

*An outline for `docs/methods/<topic>.md`, ready for the `write-method-docs` skill.*
```

### Phase 7: Final Check

Confirm that `docs/methods/research/<topic>-research.md` was written. Tell the user the brief is
ready for review before moving on to `write-method-docs`.
