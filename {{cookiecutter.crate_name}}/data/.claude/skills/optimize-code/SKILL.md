---
name: optimize-code
description: Improve Rust performance when a representative workload shows a meaningful bottleneck.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Optimize Rust Code

Start with a performance target and representative inputs. Profile or measure the current path
to identify where time or memory goes. Use `benchmark-code` to record a baseline and compare
the change; a faster microbenchmark is useful only if it improves the workload that matters.

Choose a change that addresses the measured cost. Possibilities include avoiding repeated work,
reducing allocations, improving data locality, batching boundary calls, or changing an algorithm.
Consider AoS versus SoA, inlining, vectorization, and concurrency only when the profile or data
size makes them relevant. `#[inline]` is a hint, and `#[inline(always)]` can increase code size.

Keep toolchain and numerical constraints in view:

- `std::simd` requires nightly. For a stable project, consider auto-vectorizable code, a suitable
  stable crate, or target-specific intrinsics with an explicit safety and portability review.
- Precomputed reciprocals and `mul_add` can change floating-point results. Check the required
  tolerance and measure on target hardware; fused multiply-add is not always faster.
- Preserve error behavior and public contracts while optimizing. Add a regression test when the
  change creates a realistic correctness risk.

Run the relevant tests and compare measurements before and after. Report the workload, baseline,
result, and any numerical or portability tradeoff. Keep a reference implementation only when it
helps test or explain the optimized code.
