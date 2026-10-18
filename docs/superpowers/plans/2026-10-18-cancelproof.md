# CancelProof engineering plan

Execute autonomously using subagent-driven-development for independent evidence/interface tasks and requesting-code-review before freeze. User explicitly declines intermediate approval/questions; skill review gates become file-based checkpoints, never hidden waiver of validation.

- [x] Task1 evidence: pinned actual source/docs/licenses, executable four required baselines, all four native fixed-version issue comparisons completed. Research agents collected disjoint sources; root completed executions after their quota interruption. Trio/Hypothesis runtime comparison explicitly NOT RUN.
- [x] Task2 engine: RED/GREEN tests, actual Task.cancel, invariants/ownership/limits/TaskGroup, fresh worker and deadline implemented with public APIs.
- [x] Task3 interfaces: root took over implementation after interface agent quota interruption, preserving RED/GREEN tests; agent later performed independent review instead. API, CLI, plugin and inert reports implemented.
- [x] Task4 integration: six real constructed defect/control pairs, TaskGroup, exclusions, soft/hard deadlines, actual HTTPX ASGI service, additional delayed/two-target plan executions completed.
- [x] Task5 acceptance: fresh Windows3.12.10/3.13.0 and isolated Linux3.13.16 installations each39 tests+4 subtests and13 acceptance cases. Linux3.12/hosted Actions NOT RUN. All raw commands/logs retained.
- [x] Task6 review/source freeze: independent counterexamples R1–R5 fixed/retested; R6 explicitly unsupported. Readiness READY_WITH_LIMITATIONS; full docs/evidence/manifest prepared. Final ZIP/bundle verification is recorded in the external delivery manifest after committing this source, avoiding self-referential hashes.

Recovery: raw E:/final/cancelproof-evidence-20261018. Source spec is authoritative and reviewed for conflicts before implementation. Fixture targets execute trusted local code in child processes, not a malicious sandbox. Prior projects stay frozen. Engine process guard permits all soft-deadline/cleanup observations but reaps an unresponsive child; no PASS before process exit.
