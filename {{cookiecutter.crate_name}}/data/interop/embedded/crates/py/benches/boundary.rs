{%- set pkg = cookiecutter.__package_name -%}
//! What crossing into Python costs. Run with `mise run bench`.
//!
//! The gap between `per_element` and `batched` at each size is the price of one Python call
//! per element versus one `list(map(...))` over the whole slice.

use std::hint::black_box;

use criterion::{BenchmarkId, Criterion, Throughput, criterion_group, criterion_main};
use pyo3::prelude::*;
use {{pkg}}::Scorer;
use {{pkg}}_python::{PyScorer, bootstrap};

/// Attaches and immediately detaches: the floor under every call into Python.
fn bench_attach(c: &mut Criterion) {
    // Nothing here goes through `PyScorer::new`, so the interpreter is not configured yet
    bootstrap().unwrap();

    c.bench_function("attach", |b| {
        b.iter(|| Python::attach(|py| black_box(py.None())));
    });
}

fn bench_call(c: &mut Criterion) {
    let scorer = PyScorer::new().unwrap();

    let mut group = c.benchmark_group("single_call");
    group.bench_function("cached_callable", |b| {
        b.iter(|| scorer.score(black_box(9.0)).unwrap());
    });
    group.bench_function("getattr_per_call", |b| {
        b.iter(|| {
            Python::attach(|py| {
                let module = PyModule::import(py, "math").unwrap();
                let sqrt = module.getattr("sqrt").unwrap();
                sqrt.call1((black_box(9.0),))
                    .unwrap()
                    .extract::<f64>()
                    .unwrap()
            })
        });
    });
    group.finish();
}

fn bench_batching(c: &mut Criterion) {
    let scorer = PyScorer::new().unwrap();

    let mut group = c.benchmark_group("batch");
    for size in [1_u32, 16, 256, 4096] {
        let xs: Vec<f64> = (0..size).map(f64::from).collect();
        group.throughput(Throughput::Elements(u64::from(size)));

        group.bench_with_input(BenchmarkId::new("per_element", size), &xs, |b, xs| {
            b.iter(|| {
                xs.iter()
                    .map(|&x| scorer.score(x).unwrap())
                    .collect::<Vec<_>>()
            });
        });
        group.bench_with_input(BenchmarkId::new("batched", size), &xs, |b, xs| {
            b.iter(|| scorer.score_all(black_box(xs)).unwrap());
        });
    }
    group.finish();
}

criterion_group!(benches, bench_attach, bench_call, bench_batching);
criterion_main!(benches);
