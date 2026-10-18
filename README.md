# CancelProof

Cancellation fault injection and explicit invariant checks for trusted local Python async scenarios.

CancelProof calls real `asyncio.Task.cancel()` at checkpoints you name, observes application state before harness cleanup, and writes portable JSON, HTML and Markdown reports. Each run uses a fresh subprocess with a parent deadline. Python 3.12+; standard asyncio; Windows and Linux.

**Source experimental edition.** It controls named checkpoints, not arbitrary awaits or bytecode. It does not prove race freedom, infer business correctness, or sandbox malicious Python code. Imports and scenarios execute with your permissions. Run only trusted local targets. Reports can contain values you explicitly share.

## Install

From this source directory, create a virtual environment and use its Python:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install --require-hashes -r requirements-dev.lock
.venv\Scripts\python -m pip install --no-build-isolation --no-deps .
.venv\Scripts\python -m pytest -q
```

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python -m pytest -q
```

The engine has no runtime third-party dependencies. The pinned development environment includes pytest, the build backend, and HTTPX for the ASGI example. No hosted API, cloud service, telemetry, database, or network listener is required.

## Run a real cancellation

```sh
python -m cancelproof run cancelproof.examples:lock_broken --plan examples/plans/lock.json --output output/broken
python -m cancelproof run cancelproof.examples:lock_fixed --plan examples/plans/lock.json --output output/fixed
python -m cancelproof explore cancelproof.examples:lock_fixed --max-runs 8 --seed 7 --output output/explore
python -m cancelproof replay output/fixed/replay.json --output output/replayed
```

Output directories must be new. The broken lock example leaves its lock acquired and returns FAIL (exit 2); the fixed example releases it in an async context manager and returns PASS (exit 0). Open `output/fixed/report.html` locally. HTML contains no scripts or remote assets.

CLI exit codes: `0` PASS, `2` FAIL, `3` INCONCLUSIVE/NOT_RUN, `1` input/import/output error. Argparse syntax errors use `2`. stdout is machine-readable JSON; Unicode is losslessly escaped for legacy Windows terminals.

## Write your own scenario

```python
# my_scenarios.py, importable from the current directory
import asyncio

async def transaction(probe):
    lock = asyncio.Lock()
    probe.watch_lock("released", lock)
    probe.expect_cancelled("scenario")  # only enforced when a planned cancel is accepted
    async with lock:
        await probe.checkpoint("after_lock")
```

```python
from cancelproof import run_scenario

report = run_scenario("my_scenarios:transaction", {
    "actions": [{"checkpoint": "after_lock"}]
})
assert report["verdict"] == "PASS"
```

In an async test, use `await arun_scenario(...)`. The pytest plugin exposes `cancelproof` and `cancelproof_async` fixtures; neither changes the caller's loop policy. The target runs in another process: use an importable module, not a closure or a live object. Explicitly pass business evidence through events or invariant `actual` callbacks; parent memory is not shared.

See [API and input contract](docs/API.md), [architecture](docs/ARCHITECTURE.md), [Chinese guide](docs/使用指南.md), [security](SECURITY.md), and [third-party notes](THIRD_PARTY_NOTICES.md). Final measured results and remaining acceptance gaps are recorded in [FINAL_REPORT.md](FINAL_REPORT.md).

## Honest scope

- Normal cancellation is not automatically a bug. FAIL requires a false invariant, declared lifecycle/propagation contract violation, or observed runtime error.
- Pending application tasks without a declared finish contract are INCONCLUSIVE candidates. Explicit legitimate background exclusions are supported and still cleaned before worker exit.
- Plans, source digest and checkpoint sequence support controlled replay. A seed changes selected checkpoint order, not the OS or stock event-loop scheduler. Repeated runs can differ.
- Source digest covers the scenario module, not imported dependencies. A mismatch prevents the target callable from running; importing its trusted module still occurs.
- Hard timeouts are INCONCLUSIVE: no reliable final state is invented. Processes are reaped, but descendants, native resources and memory are not sandboxed.
- LoomCheck already offers checkpoint schedules, replay and shrinking; pyleak already diagnoses pending tasks; direct `Task.cancel()` plus assertions can express these tests. Our increment is a cancellation-oriented request/report contract with separate-process deadline handling, not a new scheduler or scientific innovation.

## Local ASGI integration

```sh
python -m cancelproof run cancelproof.examples:asgi_fixed --plan examples/plans/asgi.json --output output/asgi
```

This executes HTTPX `ASGITransport` against the included request handler, sends a real in-process HTTP test request, cancels the request task and checks request resources, background tasks and absence of a cancelled commit. It is not a production server/socket/load test, and HTTPX ASGITransport does not drive ASGI lifespan.

MIT license. No public repository, package upload, or release is created by this local delivery.
