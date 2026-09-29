---
name: benchmark-code
description: Guidelines for measuring performance with the workspace's criterion benches.
argument-hint: [directory or file]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Bash
---

# Benchmarking Guidelines

When measuring performance or verifying optimizations, use the criterion benches already in this
workspace. Run them with `mise run bench`; results land in `target/criterion`. Pick inputs that
represent actual workloads and record the baseline before changing code.

## 1. The Benchmarking Framework

The workspace already depends on criterion. Add benches next to the existing ones; do not
introduce a second harness.

- `crates/core/benches` measures the Rust core. Benchmark a crate through its own `benches/`
  directory; `crates/py/benches` exists only where the Python boundary is worth measuring.
- Use `criterion_group!` / `criterion_main!` as the existing files do.
- Use `std::hint::black_box` on inputs and outputs so LLVM cannot delete the work.

Use criterion for repeatable microbenchmarks. End-to-end timing may use other suitable tools when
it better captures startup, I/O, or boundary costs.

## 2. Parameter Sweeps

To see how cost grows with input size, sweep sizes with `BenchmarkId` and `Throughput`, as the
existing benches do.

```rust
use std::hint::black_box;

use criterion::{BenchmarkId, Criterion, Throughput};

fn scale(c: &mut Criterion) {
    let mut group = c.benchmark_group("score_all");
    for n in [16_u32, 256, 4096] {
        group.throughput(Throughput::Elements(u64::from(n)));
        group.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, &n| {
            let xs: Vec<f64> = (0..n).map(f64::from).collect();
            b.iter(|| black_box(score_all(black_box(&xs))));
        });
    }
    group.finish();
}
```

## 3. Baselines

Compare the new path against the previous behavior and against the performance target. Keep a
simple reference implementation when it helps validate results or explain a complex optimization.
Report measurement variance and any meaningful memory or correctness tradeoff.

---

For long-running benchmarks, use the `async-workflows` skill to run them in the background.
