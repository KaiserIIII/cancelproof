# Acceptance record

Tested implementation commit: `f8fd438ed0c6b1aaf68b2c5d6ca450be7578c725`. Final documentation/evidence packaging commits preserve these implementation files. See the final external delivery manifest for the final commit and ZIP/bundle/wheel hashes.

| Actual environment | Installation / pip check | Full pytest | Constructed CLI/API/report cases |
|---|---|---|---|
| Windows, CPython3.12.10 | PASS, new venv and clean local Git clone | **39 passed, 4 subtests passed**, 12.81s | 13/13 expected outcomes |
| Windows, CPython3.13.0 | PASS, new venv and clean local Git clone | **39 passed, 4 subtests passed**, 14.22s | 13/13 expected outcomes |
| Isolated WSL Linux, CPython3.13.16 | PASS, new directory/source ZIP/new venv | **39 passed, 4 subtests passed**, 5.09s | 13/13 expected outcomes |
| Linux, CPython3.12 | NOT RUN | NOT RUN | NOT RUN |
| Hosted GitHub Actions | Prepared 2 OS × 2 Python workflow, NOT RUN | No public repository/push authorized | NOT RUN |

Windows interpreters were separate real native runtimes; the3.12.10 installer was retrieved from python.org and its Authenticode signature was valid for Python Software Foundation. The isolated Linux interpreter was reused read-only; no previous project's source/environment was modified. The new source and venv do not rely on the development directory. These are clean Python installations of the tool, not a claim of virgin operating systems or independent hardware.

Portable commands executed with each venv's Python:

```sh
python --version
python -m pip install --no-index --find-links REVIEWED_WHEELHOUSE --require-hashes -r requirements-dev.lock
python -m pip install --no-build-isolation --no-deps .
python -m pip check
python -m pip freeze
python -m pytest -q
python scripts/acceptance.py NEW_EVIDENCE_DIRECTORY
```

Full actual command arrays, cwd, stdout/stderr, timestamps and return codes are preserved externally in `final-platforms/windows312-*.json`, `windows313-*.json`; Linux full command script is `final_linux.sh`, with stdout/stderr in `final-linux.log`. Linux startup emitted WSL proxy and termcap notices; installation/tests/cases exited0. An initial `bash` attempt was NOT RUN because the minimal isolated distribution has no bash; the successful execution used its available `sh`. No original log was replaced.

The thirteen cases include six intentional faults (lock, token, swallowed cancellation, pending request task, interrupted cleanup, broken ASGI cleanup), six corresponding controls and a normal TaskGroup cancellation control. Verdict/outcome, diagnostic details, invariants, task states and action-delivery results were exactly equal across all three environments. They are developer-constructed regression cases, **not an independent generalization dataset**. `validation/RESULTS.json` is the machine-readable summary.

The full tests also execute normal ASGI Unicode response and soft-timeout cleanup, exact CLI exits0/2/1/3, Unicode input/redirected output, inert report generation, replay and source mismatch, task/trace limits, invariant errors, business/file contracts, legitimate background exclusions, caller cancellation and hard-deadline controls. Each acceptance report checks source digest shape, checkpoint-event sequence references and direct worker reaping. Raw evidence is not silently counted as test assertions.

Independent Windows review separately confirmed caller cancellation3/3 with PID absence and hard deadlines24/24 with process reaped/workspace removed after fixes. These bounded repetitions are not a universal guarantee or performance benchmark.

Additional actual Windows3.13 API checks exercised a three-loop-turn delayed request (root cancelled after a declared advancement invariant became true) and two separately targeted worker cancellations in one plan (both conditional propagation contracts passed). Raw `ADDITIONAL_TIMING.json` retains these results; they are not counted as additional pytest tests or cross-platform cases.
