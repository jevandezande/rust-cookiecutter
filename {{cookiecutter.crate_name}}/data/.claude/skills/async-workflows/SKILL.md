---
name: async-workflows
description: Run and monitor long builds, tests, benchmarks, or profiles without losing their results.
argument-hint: None
allowed-tools:
  - Read
  - Bash
---

# Long-Running Commands

Use the command environment's asynchronous session or background facility when a build, test,
benchmark, or profile will outlast the current tool call. Short commands can run in the
foreground. Choose based on the actual tool timeout and likely command duration.

Keep the process handle, complete output, and exit status. Poll at useful intervals and report
the final result, including failures. Put temporary logs outside the source tree when possible
and remove them when done. If a tool already supports yielding and resuming a process, use that
instead of hand-written `nohup` and PID files.

Do independent work while a command runs when it advances the same task. Parallel agents are
optional and should be used only when the task or project instructions call for them.
