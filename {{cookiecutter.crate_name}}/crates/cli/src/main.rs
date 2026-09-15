{%- set pkg = cookiecutter.__package_name -%}
//! Command-line entry point for {{cookiecutter.project_name}}

use std::process::ExitCode;

use clap::Parser;
use tracing::info;
use {{pkg}}::{NativeScorer, NegativeInput, Scorer, best_score};

const DEFAULT_INPUT: [f64; 3] = [1.0, 16.0, 4.0];

/// Score values and print the highest.
#[derive(Debug, Parser)]
#[command(version, about)]
struct Args {
    /// Values to score.
    #[arg(allow_negative_numbers = true, default_values_t = DEFAULT_INPUT)]
    values: Vec<f64>,
}

fn init_tracing() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("warn")),
        )
        .init();
}

fn report<S: Scorer>(scorer: &S, xs: &[f64]) -> Result<(), S::Error> {
    let best = best_score(scorer, xs)?;
    info!(?best, n = xs.len(), "best score");
    match best {
        Some(best) => println!("best score: {best}"),
        None => println!("no values to score"),
    }
    Ok(())
}

fn run(args: &Args) -> Result<(), NegativeInput> {
    report(&NativeScorer, &args.values)
}

fn main() -> ExitCode {
    init_tracing();
    match run(&Args::parse()) {
        Ok(()) => ExitCode::SUCCESS,
        Err(err) => {
            eprintln!("error: {err}");
            ExitCode::FAILURE
        }
    }
}
