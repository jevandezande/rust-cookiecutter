---
name: optimize-code
description: Guidelines for taking functional code and tuning it for CPU cycles and cache locality.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

When optimizing algorithms in this project, follow these principles to cut CPU cycles and improve
cache use.

### 1. Data-Oriented Design (DOD)

- AoS vs. SoA: when a linear pass over a large collection is slow, check whether an array of
  structs is the cause and switch to a struct of arrays if it is.
- Cache locality: keep hot data contiguous and avoid pointer chasing. Memory latency, not compute,
  is usually the bottleneck.

### 2. Inlining & Loop Unrolling

- `#[inline]`: mark small, hot functions called from tight loops, so the call disappears and the
  body is exposed to the caller. Use `#[inline(always)]` sparingly.
- Auto-vectorization: write loops LLVM can turn into SIMD. Keep branching and data dependencies
  out of the tightest loops.
- Explicit SIMD: if auto-vectorization fails on a critical bottleneck, consider `std::simd` or
  `wide`.

### 3. Mathematical Optimizations

- Reciprocals: replace a division (`x / y`) with a multiplication (`x * (1.0 / y)`) when `1.0 / y`
  can be precomputed or hoisted out of the loop.
- FMA: where the algorithm does not need bit-exact IEEE 754 results, `f32::mul_add` (fused
  multiply-add) is faster and slightly more precise.

---

Measure with the `benchmark-code` skill before and after. Confirm correctness with the `test-code`
skill.
