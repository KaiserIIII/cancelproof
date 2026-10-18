# API and evidence contract (schema 1)

`run_scenario(target, plan=None, limits=None)` and `await arun_scenario(...)` return a dictionary. `target` is `module:async_callable`; it receives one Probe. Optional `expected_source_sha256` prevents callable execution on a source digest mismatch. Trusted module import precedes this comparison.

`campaign(target, max_runs=12, seed=0, repeats=1, limits=None)` first runs a baseline and selects reached checkpoints for separate fault runs. At most 64 runs, 8 repeats per point, and a 120-second estimated wall budget. Baseline counts toward max_runs. Unselected points are reported; no exhaustive coverage claim.

## Plans

```json
{"actions":[{"checkpoint":"granted","task":"worker","occurrence":1,"repeat":2,"delay_turns":0}],"expected":{"worker":"cancelled"}}
```

At most 32 actions. A task selector matches the checkpoint **caller** and cancels that same registered task. Omit `task` to use the first matching caller. Occurrence is counted independently per task and checkpoint (1..1000). Labels are nonempty, at most 128 characters. Repeat is 1..4 requests; delay is 0..10 loop turns. Zero-delay first cancel is immediate. A controller yields between additional requests. Ready-queue order is ordinary asyncio behavior. Unreached or incomplete actions produce INCONCLUSIVE; rejected cancellation of an already-finished task is disclosed. `expected` is an unconditional outcome contract (completed/cancelled); `expect_cancelled` is conditional on an accepted planned cancellation.

## Limits

| Key | Default | Range |
|---|---:|---:|
| timeout | 1 second | 0.05..30 |
| grace | 0.15 seconds | 0.01..5 |
| wall_timeout | 5 seconds | 0.2..60 |
| max_tasks | 32 | 1..128 |
| max_events | 2000 | 16..10000 |

Wall deadline must exceed timeout+grace+0.1. A soft deadline cancels the scenario, waits grace and records the timeout; successful declared cleanup may PASS with outcome timeout. Two ordinary loop turns then let queued completion callbacks/finalizers settle before observation; this is not cancellation cleanup. If worker shutdown does not exit, the parent terminates then kills/reaps it and reports hard_timeout/INCONCLUSIVE. Termination/reaping adds up to 1.5 seconds beyond the poll deadline plus OS scheduling overhead. Requests/files/logs are capped; output-size monitoring is polled, not a hard disk/memory quota. Raw stdout/stderr is not exported by default because targets may print secrets. Flushed explicit trace events survive hard timeout.

## Probe

- `await checkpoint(name)` logs task/name/occurrence and yields. Caller must be registered.
- `create_task(coro, name, must_finish=True)` or `track(task, name, must_finish=True)` registers application tasks on the current loop. Root is `scenario`. Never register framework tasks. A public task factory bounds cumulative created tasks, including unregistered application tasks and async-generator finalizers, excluding injection controllers. Root counts toward the budget. Trusted target code must not replace the task factory to bypass limits.
- `allow_background(task, reason)` records an intentional pending task exclusion. Harness still cleans it up. `require_no_pending()` declares all newly observed application tasks should finish; unregistered pending tasks without this contract are INCONCLUSIVE.
- `invariant(name, predicate, category="business", actual=None, expected=True)` evaluates a synchronous bool predicate **before** harness cleanup. False is FAIL; exceptions/nonbool/awaitable are INCONCLUSIVE. `actual` is optional JSON data or a synchronous callback. `expected` is display evidence; the predicate determines truth.
- `watch_lock(name, lock)` checks public `locked()`; token, file, connection, balance, commit and cleanup-count contracts use custom predicates. No automatic resource introspection or inferred business semantics.
- `expect_cancelled(name="scenario")` checks propagation when a planned request was accepted.
- `event(name, **details)` and `observe(name, value)` include user-approved JSON evidence. Each explicit value is limited to 16 KiB; trace truncation is INCONCLUSIVE.

## Reports and replay

Run fields include schema/version/environment/source_sha256, scenario, plan, limits, actions/deliveries, checkpoints, events, tasks, invariants, diagnostics, pre-cleanup observation flag and process reaping evidence. Each checkpoint refers to an event sequence index. Exception evidence contains class, basename, line and function; no default exception message, source lines, locals, environment dump or full local path. User-supplied labels, values and target names may still be sensitive.

JSON is authoritative. HTML is escaped, inert, contains no JavaScript/network resources. Markdown uses indented code. `replay.json` has target and bounded run list with plan, limits and module digest. Environment/dependency changes and uncontrolled scheduling are not prevented by a matching digest.

Verdicts: PASS = executed contracts passed; FAIL = observed contract/runtime error; INCONCLUSIVE = incomplete/ambiguous observations; NOT_RUN = target not executed. `outcome` is independent: completed, cancelled, exception, timeout, hard_timeout, not_run.
