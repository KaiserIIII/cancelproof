# Competitive engineering review

Research date: 2026-10-18. Actual pinned source archives, licenses, APIs and relevant implementation files were read. A current Context7 request hit its monthly quota; official repositories/docs and PyPI metadata were used instead. No usage/accuracy/novelty survey is implied.

| Tool | Inspected revision | Existing capability and boundary | Execution in this work |
|---|---|---|---|
| [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio/tree/6e14cd2af9292dca1fa2b027a06bbc40b0e0e425) 1.4.0 | `6e14cd2af9292dca1fa2b027a06bbc40b0e0e425` | Async pytest tests and loop fixtures; native cancellation plus assertions express our lock test directly. | PASS fixed, expected assertion FAIL broken. |
| [AnyIO](https://github.com/agronholm/anyio/tree/ffcd1542cd6d127980205f90a0100078849dd703) 4.15.1 | `ffcd1542cd6d127980205f90a0100078849dd703` | Structured task groups/cancel scopes and built-in pytest integration; multiple backends. No need to reimplement these. | Installed in ASGI tests; native historical version controls below. |
| [pytest-anyio](https://github.com/graingert/pytest-anyio/tree/07b610e9c31c566387cfbcbc1ba556a4cea7ca83) placeholder | `07b610e9c31c566387cfbcbc1ba556a4cea7ca83` | PyPI 0.0.0 directs users to AnyIO's built-in plugin. It is not a separate competing runner to install. | NOT RUN standalone placeholder. |
| [Trio](https://github.com/python-trio/trio/tree/b3fd421ab1ac7830ed7440b85331e4ae2ccaaba9) 0.34.0 | `b3fd421ab1ac7830ed7440b85331e4ae2ccaaba9` | Nursery ownership, cancel scopes and checkpoint semantics; different concurrency model. | Source/document review only; NOT RUN. |
| [pytest-trio](https://github.com/python-trio/pytest-trio/tree/250ec45f5d72eca78ab0ea2d1571667d2c51f8b5) 0.8.0 | `250ec45f5d72eca78ab0ea2d1571667d2c51f8b5` | Trio test/fixture support; not a stock-asyncio cancellation-plan API. | Source/document review only; NOT RUN. |
| [LoomCheck](https://github.com/Alqudimi/LoomCheck/tree/e4ad6c84a29c1495d151b68a1565dc5fda0dd30a) alpha source | `e4ad6c84a29c1495d151b68a1565dc5fda0dd30a` | Explicit named checkpoints, owned tasks, bounded deterministic schedules, replay, JSON/Markdown and failure shrinking already exist. | Adapted ordinary Task.cancel plus lock invariant: fixed success; broken AssertionError. |
| [simloop](https://github.com/dhruvl/simloop/tree/5175176b6905c7d83b0fe32a69d4095c1c8d33fa) 0.2.2 | `5175176b6905c7d83b0fe32a69d4095c1c8d33fa` | Simulated event loop, seeded schedules, virtual time/network/disk faults and replay/shrinking. Broader simulation controls than CancelProof. | Adapted lock cancellation: fixed passes 10 seeds, broken fails first seed. |
| [pyleak](https://github.com/deepankarm/pyleak/tree/0d0ec2f8745f133e1101f8c17da092884631a324) 0.2.0 | `0d0ec2f8745f133e1101f8c17da092884631a324` | Pending task/thread and event-loop-blocking detection, filtering and reporting. | With action=raise: pending task raises TaskLeakError; properly cleaned control passes. |
| [Hypothesis](https://github.com/HypothesisWorks/hypothesis/tree/718686d1e392968eb0953c043ef249c5d9d11a59) 6.170.1 | `718686d1e392968eb0953c043ef249c5d9d11a59` | Property-based input/state-machine generation and shrinking; can generate fault plans for an async runner. | Source/document review only; NOT RUN. |

## Fair executed comparison

The lock tests use a real lock, a real native cancellation and an explicit `not lock.locked()` assertion. No baseline is intentionally deprived of the invariant. pytest-asyncio and simloop report exactly the intended broken assertion failures (combined baseline suite exit1, **2 failed / 2 passed**; these are detection outcomes, not broken tool installations). LoomCheck receives explicit Task.cancel in its scenario and detects the same bug. pyleak is configured to raise rather than just warn, and receives the task-lifecycle problem it is designed to diagnose.

Full commands, source revisions, wheel hashes and outputs are in the external `competitors/` evidence folder: `pytest-simloop.log`, `EXECUTED_BASELINES.json`, `loom-pyleak.log`, scripts and manifests. The portable summary is in `validation/RESULTS.json`. These few constructed cases do not estimate comparative recall, false-positive rates, performance, or user effort.

One additional actual control placed a cancellation-resistant child inside LoomCheck with an internal0.05s timeout. It did not exit within the external1.5s parent deadline; subprocess.run killed and waited for it. CancelProof returns hard_timeout/INCONCLUSIVE for its corresponding resistant target. This is evidence for integrating an external watchdog, not proof that LoomCheck cannot be safely wrapped or a general performance comparison. Exact result: external `competitors/DEADLINE_CONTROL.json`.

## Increment and non-advantages

Existing compositions can detect every constructed defect demonstrated here when given the same cancellation and invariants. CancelProof has **not** established a new detection capability or scientific novelty. It packages named cancellation plans, conditional propagation contracts, pre-cleanup evidence, conservative unknown handling, stock-loop subprocess deadlines, replay digest checks, pytest fixtures and inert reports in one local workflow.

There is a concrete engineering convenience: a saved plan can be replayed through CLI/API while retaining delivered cancel requests, resource assertions and process-cleanup evidence. No user study or general reduction in authoring cost was performed. Standard pytest plus a subprocess/time-limit helper could provide this too. LoomCheck/simloop provide schedule exploration/shrinking that CancelProof deliberately does not implement. pyleak provides thread/blocking diagnostics that CancelProof does not replace.

Independent review found actual early false positives and missed exceptions; those were fixed or made explicitly INCONCLUSIVE. Unacknowledged child exceptions are ambiguous through public asyncio APIs; direct Task constructors bypass factory accounting. No real-world false-positive claim is warranted. This is a narrowly scoped experimental developer utility, not a necessary new framework for every async project.
