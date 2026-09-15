{%- set pkg = cookiecutter.__package_name -%}
//! Benchmarks for the pure-Rust core. Run with `mise run bench`; results land in `target/criterion`.
//!
{%- if cookiecutter.python_interop == 'embedded' %}
//! The scorer stays in Rust here; `crates/py/benches` runs the same shape through the interpreter.
{%- else %}
//! The scorer stays in Rust here, so this measures the core alone.
{%- endif %}

use std::hint::black_box;

use criterion::{BenchmarkId, Criterion, Throughput, criterion_group, criterion_main};
use {{pkg}}::{Scorer, best_score};

struct Doubler;

impl Scorer for Doubler {
    type Error = std::convert::Infallible;

    fn score(&self, x: f64) -> Result<f64, Self::Error> {
        Ok(x * 2.0)
    }
}

fn bench_best_score(c: &mut Criterion) {
    let mut group = c.benchmark_group("best_score");

    for size in [1_u32, 16, 256, 4096] {
        let xs: Vec<f64> = (0..size).map(f64::from).collect();
        group.throughput(Throughput::Elements(u64::from(size)));

        group.bench_with_input(BenchmarkId::from_parameter(size), &xs, |b, xs| {
            b.iter(|| best_score(&Doubler, black_box(xs)).unwrap());
        });
    }

    group.finish();
}

criterion_group!(benches, bench_best_score);
criterion_main!(benches);
