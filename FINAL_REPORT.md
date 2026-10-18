# CancelProof local engineering delivery

Decision: **READY_WITH_LIMITATIONS** for a source experimental developer utility. No scientific novelty, universal race-freedom, production false-positive rate, or superiority claim is made. Existing tools can express the demonstrated tests; the delivered increment is the integrated cancellation-plan/invariant/evidence/process-deadline workflow.

## Implemented and actually run

- Python3.12+ installable standard-library engine; real Task.cancel at named checkpoints, logical task selection/occurrences, delayed/repeated requests, soft timeout/grace and independent worker deadline.
- Explicit lock/file/session/token/business predicates, cancellation-propagation and completion contracts, task tracking/exclusions and pre-cleanup observation. No manual raise CancelledError is used as fault injection.
- TaskGroup support, bounded task-factory creation/retention, conservative child-exception handling and explicit expected-error acknowledgement; cleanup events and redacted frame evidence.
- Synchronous/async Python APIs, pytest fixtures, run/explore/replay CLI, stable exit codes, editable JSON plans, source-digest mismatch handling and JSON/HTML/Markdown reports.
- Complete local HTTP ASGI service with real HTTPX ASGITransport requests: Unicode200 response, cancellation, timeout, background task and request-resource checks. This is a transport/service integration test, not a deployed server/load/lifespan test.

Actual constructed bugs distinguished from their fixed controls: acquired lock not released; token not returned and competing waiter stalled; cancellation swallowed contrary to contract; request background task not finished; second cancellation interrupts async cleanup; ASGI request resource/background cleanup omitted. Six faulty cases FAIL, six paired controls PASS, and normal TaskGroup cancellation PASS on each of three environments. They are designed faults, not claims about third-party applications.

## Verification

Tested implementation: `f8fd438ed0c6b1aaf68b2c5d6ca450be7578c725`. Final documentation/evidence commit and artifact checksums are recorded in the external `delivery/DELIVERY.json` to avoid a self-referential commit SHA inside source.

| Real environment | Full test result | Additional acceptance |
|---|---|---|
| Windows CPython3.12.10, fresh source clone/venv |39 passed +4 subtests|13 expected cases; CLI/Unicode/evidence checks PASS|
| Windows CPython3.13.0, fresh source clone/venv |39 passed +4 subtests|13 expected cases; CLI/Unicode/evidence checks PASS|
| Isolated Linux CPython3.13.16, fresh source ZIP/venv |39 passed +4 subtests|13 expected cases; CLI/Unicode/evidence checks PASS|

All13 canonical diagnostic sets match across those platforms. No real samples were added to inflate a generalization metric. Linux3.12 and hosted Actions are NOT RUN. Workflow configuration covers Windows/Linux×3.12/3.13 for future authorized publication. Actual commands, versions, dependencies, stdout/stderr and return codes are retained. [Acceptance details](ACCEPTANCE.md), [machine summary](validation/RESULTS.json).

## Historical and competitor evidence

Native Windows3.12.10 reproduced AnyIO #387 (3.3.4 locked versus3.4.0 unlocked), #947 (4.9.0 stranded versus4.10.0 progressed), and #1214 (4.14.1/4.15.1 suppress external cancel versus pinned unreleased merged source propagates). CPython#116720 original snippet ran natively on3.12.10/3.13.0: the post-await marker appears only on3.12.10; the synchronous marker still appears on both. No upstream expectation was edited. [Precise results and fixes](docs/HISTORICAL_REPRODUCTIONS.md).

Actual mature-tool controls: pytest-asyncio and simloop pass fixed lock and fail broken lock under explicit native cancellation+invariant; LoomCheck adapted scenario detects the same defect; pyleak raises on the intentionally pending task and passes cleanup. Thus basic bug detection is not unique. LoomCheck already has named schedules/replay/shrinking and simloop broader simulation capabilities. One cancellation-resistant LoomCheck cleanup did not exit its internal deadline and was terminated by our external1.5s watchdog; adding an external watchdog also solves this for that baseline. This demonstrates workflow packaging, not a fundamental advantage. Trio/pytest-trio/Hypothesis source reviewed, runtime comparisons NOT RUN. [Complete scope comparison](docs/COMPETITORS.md).

## Independent review and remaining limits

Independent read-only review found and independently rechecked fixes for Windows cleanup masking cancellation, lost completed-task exceptions, handled TaskGroup false positives, replay preflight bypass and null-limit traceback leakage. Independent retest:39 passed+4 subtests; caller cancel3/3 with PID absence; deadlines24/24 with worker reaped/workspace removed. Original failures are retained. [Disposition and residual R6](SECURITY_AND_QUALITY_REVIEW.md).

Residuals: direct Task constructors/custom factories bypass accounting; no arbitrary-await scheduler control; no memory/descendant sandbox; trusted import executes before replay digest check; module-only digest; explicit business assertions required; ambiguous child exceptions are INCONCLUSIVE; optional released AnyIO has known concurrent-cancel behavior beyond tested integration plans. No real-world false-positive, usability-cost or performance study. Persistent OS file locks may prevent private temp cleanup; failures are disclosed. These limits are reasons to keep an experimental label.

## Handoff and artifact locations

Source: `E:/final/cancelproof-20261018`. Full raw local evidence: `E:/final/cancelproof-evidence-20261018`; see portable [evidence hash index](validation/EVIDENCE_INDEX.json). Safe runnable example outputs are in [validation/examples](validation/examples). Installation/API/CLI: [README](README.md), [API contract](docs/API.md), [Chinese guide](docs/使用指南.md), [architecture](docs/ARCHITECTURE.md).

Final source ZIP, installable wheel, verified Git Bundle and SHA256/SHA/restore manifest are in external `delivery/`. Source ZIP contains only the Git-tracked public list; runtime, caches, research archives and original raw logs are excluded. Bundle contains this new project's local source history only. [Readiness decision](PUBLICATION_READINESS.md), [resume checkpoint](RESUME.md).

No remote repository/push/Release/PyPI/public service/upstream PR was created. No other project was modified. Development stops at this delivered candidate.
