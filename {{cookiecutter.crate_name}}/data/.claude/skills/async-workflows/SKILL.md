---
name: async-workflows
description: Runs long commands (compiles, tests, profiling) in the background so agent turns do not time out.
argument-hint: None
allowed-tools:
  - Read
  - Bash
  - Task
---

# Async Workflows for Long-Running Tasks

Workspace builds, `mise run bench`, and full test suites can run long enough to time out an agent
turn. Run any command expected to take more than 30 seconds in the background.

## 1. Launching Background Tasks

Start a slow test, compile, or profile with `nohup` and save its PID:

```bash
nohup mise run bench > bench_output.log 2>&1 &
echo $! > current_task.pid
```

## 2. Polling and Multitasking

Do not sit and wait. While the process runs, spawn sub-agents with the `Task` tool for parallel
work:

- Launch an `explore` sub-agent to audit the codebase for `unsafe` blocks.
- Launch a `general` sub-agent to draft or review nearby documentation.

To check on the task, read the tail of the log and see whether the process is still alive:

```bash
tail -n 20 bench_output.log
ps -p $(cat current_task.pid) || echo "Process finished"
```

## 3. Profiling

Never read a raw binary profile. Generate text output.

`samply` is optional and not among the pinned tools. If you add it, script it (or `perf`) to
emit a flamegraph or text summary you can read.

## Summary Rule

Never run `cargo build --release`, `mise run bench`, or a full `cargo test --workspace` in the
foreground if it may exceed 30 seconds. Background it, log the output, and work in parallel with
the `Task` tool.
