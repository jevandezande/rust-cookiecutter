---
name: write-latex
description: >
  Standards for writing LaTeX math in markdown files. Use when writing or editing
  equations, mathematical notation, or scientific formulas in .md files. Covers
  unicode vs LaTeX conventions, markdown-safe escaping, and display math formatting.
argument-hint: [file path or topic]
---

# Writing LaTeX in Markdown

Use this skill when writing or editing mathematical notation in markdown files. Equations should
read well both as raw markdown, in a terminal or editor with a unicode-capable font, and as
MathJax output, which supports unicode fully.

## Core Principle

Use unicode for any character with a clear, visually correct code point. Keep LaTeX for
structure (fractions, environments, decorations, superscripts, subscripts), which has no adequate
unicode equivalent.

## Unicode Characters: Use These Instead of LaTeX Commands

### Greek Letters (lowercase)

| Unicode | LaTeX |
|---------|-------|
| α | `\alpha`    |
| β | `\beta`     |
| γ | `\gamma`    |
| δ | `\delta`    |
| ε | `\varepsilon` |
| ζ | `\zeta`     |
| η | `\eta` |
| θ | `\theta` |
| ι | `\iota` |
| κ | `\kappa` |
| λ | `\lambda` |
| μ | `\mu` |
| ν | `\nu` |
| ξ | `\xi` |
| π | `\pi` |
| ρ | `\rho` |
| σ | `\sigma` |
| τ | `\tau` |
| υ | `\upsilon` |
| φ | `\phi` |
| χ | `\chi` |
| ψ | `\psi` |
| ω | `\omega` |
| ϑ | `\vartheta` |

### Greek Letters (uppercase)

| Unicode | LaTeX |
|---------|-------|
| Γ | `\Gamma` |
| Δ | `\Delta` |
| Θ | `\Theta` |
| Λ | `\Lambda` |
| Ξ | `\Xi` |
| Π | `\Pi` |
| Σ | `\Sigma` |
| Υ | `\Upsilon` |
| Φ | `\Phi` |
| Ψ | `\Psi` |
| Ω | `\Omega` |

Uppercase Greek letters that look like Latin ones (A, B, E, Z, H, I, K, M, N, O, P, T, X) have
no separate code points. Use the Latin letter.

### Operators

| Unicode | LaTeX |
|---------|-------|
| ∫ | `\int` |
| ∬ | `\iint` |
| ∮ | `\oint` |
| Π | `\prod` |
| Σ | `\sum` |
| ⨁ | `\bigoplus` |
| ∪ | `\cup` |
| ∩ | `\cap` |
| ∖ | `\setminus` |

### Relations

| Unicode | LaTeX | Unicode | LaTeX |
|---------|-------|---------|-------|
| ∈ | `\in` | ∉ | `\notin` |
| ⊂ | `\subset` | ⊆ | `\subseteq` |
| ⊃ | `\supset` | ⊇ | `\supseteq` |
| ≤ | `\leq` | ≥ | `\geq` |
| ≠ | `\neq` | ≈ | `\approx` |
| ≡ | `\equiv` | ∝ | `\propto` |
| ≪ | `\ll` | ≫ | `\gg` |
| ≲ | `\lesssim` | ≳ | `\gtrsim` |
| ⊥ | `\perp` | ∥ | `\parallel` |
| ∼ | `\sim` | ≃ | `\simeq` |
| ≅ | `\cong` | ⊤ | `\top` |

Never use bare `<` or `>` in math mode. Markdown parsers turn them into `&lt;` and `&gt;` before
MathJax sees them, and the `&` raises a "Misplaced &" error. Use `\lt` and `\gt`:

```markdown
<!-- Wrong -->
$a < b$    $f(x) > 0$

<!-- Correct -->
$a \lt b$    $f(x) \gt 0$
```

### Arrows

| Unicode | LaTeX | Unicode | LaTeX |
|---------|-------|---------|-------|
| → | `\to` | ← | `\leftarrow` |
| ⇒ | `\Rightarrow` | ⇐ | `\Leftarrow` |
| ↔ | `\leftrightarrow` | ⇔ | `\Leftrightarrow` |
| ↑ | `\uparrow` | ↓ | `\downarrow` |
| ↦ | `\mapsto` | | |

### Miscellaneous Symbols

| Unicode | LaTeX |
|---------|-------|
| ∞ | `\infty` |
| ∓ | `\mp` |
| ∇ | `\nabla` |
| ℏ | `\hbar` |
| ‡ | `\ddagger` |
| ∀ | `\forall` |
| ¬ | `\neg` |
| ∨ | `\vee` |
| ⊕ | `\oplus` |
| ± | `\pm` |
| × | `\times` |
| ∂ | `\partial` |
| † | `\dagger` |
| ∅ | `\emptyset` |
| ∃ | `\exists` |
| ∧ | `\wedge` |
| ⊗ | `\otimes` |
| ℓ | `\ell` |
| ∘ | `\circ` |
| ∴ | `\therefore` |
| ∵ | `\because` |
| ∠ | `\angle` |
| ℜ | `\Re` |
| ℑ | `\Im` |

Prefer ℜ and ℑ to `\Re` and `\Im`, which the `physics` extension redefines.

### Brackets and Delimiters

| Unicode | LaTeX | Notes |
|---------|-------|-------|
| ⟨ | `\langle` | Use for bra-ket notation |
| ⟩ | `\rangle` | Use for bra-ket notation |
| `|` | `\vert`, `\lvert`, `\rvert` | Absolute values, divides; use `|` outside table cells, LaTeX inside |
| `‖` | `\lVert`, `\rVert` | Norms; use LaTeX when auto-sizing with `\left`/`\right` or inside table cells |
| ⌊ ⌋ | `\lfloor`, `\rfloor` | Floor; use LaTeX when auto-sizing with `\left`/`\right` |
| ⌈ ⌉ | `\lceil`, `\rceil` | Ceiling; use LaTeX when auto-sizing with `\left`/`\right` |

Bra-ket notation: `\ket{}` and `\bra{}` require the `braket` extension, which is not autoloaded.
Use portable alternatives:

```markdown
<!-- Portable (no extension needed) -->
$|ψ⟩$    $⟨φ|$    $⟨φ|ψ⟩$
```

### Dots

| Unicode | LaTeX | Usage |
|---------|-------|-------|
| · | `\cdot` | Multiplication dot |
| ⋯ | `\cdots` | Horizontal ellipsis (centered) |
| ⋮ | `\vdots` | Vertical ellipsis |
| ⋱ | `\ddots` | Diagonal ellipsis |

### Blackboard Bold

| Unicode | LaTeX |
|---------|-------|
| ℝ | `\mathbb{R}` |
| ℂ | `\mathbb{C}` |
| ℕ | `\mathbb{N}` |
| ℤ | `\mathbb{Z}` |
| ℚ | `\mathbb{Q}` |

Example: write `$\mathbf{F} ∈ ℝ^{K × K}$`, not `$\mathbf{F} \in \mathbb{R}^{K \times K}$`.

## What Must Stay as LaTeX

These constructs have no adequate unicode equivalent.

### Structural

| Command | Reason |
|---------|--------|
| `\frac{}{}`, `\dfrac{}{}`, `\tfrac{}{}` | Fraction layout; no unicode equivalent |
| `^{}` (superscripts) | Unicode superscripts are incomplete and visually inconsistent |
| `_{}` (subscripts) | Unicode subscripts are incomplete and visually inconsistent |
| `\sqrt{}`, `\sqrt[n]{}` | Proper radical rendering; never use `√` |
| `\lt`, `\gt` | Bare `<`/`>` are HTML-escaped by markdown parsers, causing "Misplaced &" errors |

### Decorations

| Command | Example |
|---------|---------|
| `\hat{}` | `$\hat{H}$` |
| `\tilde{}` | `$\tilde{ν}$` |
| `\bar{}` | `$\bar{E}$` |
| `\vec{}` | `$\vec{r}$` |
| `\dot{}`, `\ddot{}` | `$\dot{x}$`, `$\ddot{x}$` |

Combining unicode diacritics are unreliable in math contexts.

### Font Commands

| Command | Usage |
|---------|-------|
| `\mathbf{}` | Bold vectors and matrices: `$\mathbf{F}$` |
| `\mathrm{}` | Upright text in math: `$\mathrm{Tr}$` |
| `\mathcal{}` | Calligraphic: `$\mathcal{H}$` |
| `\boldsymbol{}` | Bold Greek: `$\boldsymbol{ε}$`. Never `\bm{}`, which MathJax does not define |
| `\text{}` | Prose inside math: `$E_\text{corr}$`. Escape `_` and `*` inside as `\_` and `\*`, or the markdown parser reads them as emphasis before MathJax sees them |

### Environments

All `\begin{}`/`\end{}` environments stay as LaTeX:
`pmatrix`, `bmatrix`, `vmatrix`, `aligned`, `align`, `cases`, `array`.

### Sizing and Delimiters

`\left`/`\right`, `\bigl`/`\bigr`/`\Bigl`/`\Bigr`, `\underbrace{}`, `\overbrace{}`.

## Extension-Dependent Commands

Some common commands need MathJax extensions that are not autoloaded. Use the portable
alternative unless the extension is configured.

| Command | Extension needed | Portable alternative |
|---------|-----------------|---------------------|
| `\grad`, `\curl`, `\div` | `physics` | `\nabla`, `\nabla\times`, `\nabla\cdot` |
| `\ket{}`, `\bra{}`, `\braket{}` | `braket` | `\|ψ⟩`, `⟨φ\|`, `⟨φ\|ψ⟩` |
| `\ce{}` (chemical equations) | `mhchem` | Manual notation: `\mathrm{H_2O}` |

The `physics` extension is not autoloaded because it redefines core macros (`\Re`, `\Im`,
`\div`). Avoid it unless you control the MathJax config.

## Vertical Bars

By default, use `|` for absolute values and divides and `‖` for norms. Both read cleanly in raw
text.

```markdown
<!-- Preferred outside tables -->
$|x|$    $|ψ⟩$    $⟨φ|ψ⟩$

<!-- Norms -->
$‖\mathbf{e}‖ \lt τ$
```

Inside table cells, use LaTeX instead. The table parser consumes a bare `|` inside `$ ... $`
before MathJax sees it and breaks the columns. Switch to `\lvert`/`\rvert` (absolute values) and
`\lVert`/`\rVert` (norms):

```markdown
| Absolute value | $\lvert x \rvert$ |
| Conditional | $p(y \vert x)$ |
| Norm bound | $\lVert \mathbf{e} \rVert \lt τ$ |
```

Use `\lvert`/`\rvert` rather than `\vert` for opening and closing bars, since they space correctly
in MathJax. Use `\vert` for interior bars (bra-ket inner products, conditional probabilities) and
inside `\left`/`\right`: `$\left\vert \frac{a}{b} \right\vert$`.

## Markdown-Specific Considerations

### Display vs Inline Math

- Inline: `$ ... $`, with no space inside the delimiters.
- Display: `$$ ... $$`, each `$$` on its own line. Unicode symbols are as valid here as in inline
  math.

```markdown
$$
E = Σ_i ⟨ φ_i | \hat{h} | φ_i ⟩
+ \frac{1}{2} Σ_{ij}\bigl[⟨ ij | ij ⟩ - ⟨ ij | ji ⟩\bigr]
$$
```

Do not put blank lines inside `$$ ... $$` blocks. Some renderers read them as paragraph breaks.

### Math in Tables

1. Use `\vert`/`\lvert`/`\rvert`/`\lVert`/`\rVert` for every vertical bar. A bare `|` breaks
   column parsing.
2. Keep cell expressions short. Define complex symbols outside the table.

```markdown
| Quantity | Definition |
|----------|-----------|
| Absolute value | $\lvert x \rvert$ |
| Conditional | $p(y \vert x)$ |
```

### Interaction with Markdown Formatting

Do not use markdown `**bold**` or `*italic*` inside math delimiters. Use
`\mathbf{}` or `\mathit{}` instead.

## Decision Checklist

When writing a symbol in math mode:

1. Greek letter, operator, relation, arrow, dot? → unicode
2. Blackboard bold (ℝ, ℂ, ℕ, ℤ, ℚ)? → unicode
3. Fraction, superscript, subscript, square root? → LaTeX (`\frac`, `^`, `_`, `\sqrt`)
4. Decoration (hat, tilde, bar, vec, dot)? → LaTeX
5. Font change (bold, roman, calligraphic)? → LaTeX
6. Vertical bar? → `|` or `‖`, or `\lvert`/`\rvert`/`\lVert`/`\rVert` inside markdown table cells
7. Environment (matrix, aligned, cases)? → LaTeX
