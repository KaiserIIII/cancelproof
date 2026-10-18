# Security and quality review disposition

An independent read-only reviewer inspected source and executed its own local counterexamples. Original findings, failed traces, source hashes, fixed-case retests and independent full pytest output are preserved externally under `independent-review/`. This document is a bounded disposition summary; it does not replace the original review or imply formal verification.

| Finding | Priority | Actual problem | Final disposition |
|---|---|---|---|
| R1 | P1 | Windows transient file handles caused workspace PermissionError to mask caller cancellation or hard-timeout reports | Fixed: bounded removal retries preserve original exception. Independent caller cancel3/3 correct/PID absent and deadlines24/24 returned with reaped+workspace_removed. |
| R2 | P1 | Completed unregistered errors could disappear, especially with retained references, producing PASS | Fixed: bounded created-task retention via public factory. Both retained/dropped error cases now INCONCLUSIVE/CHILD_EXCEPTION_UNCLASSIFIED, never PASS. |
| R3 | P2 | Registered, handled TaskGroup child exception was falsely classified as definite bug | Fixed: conservative unknown by default and explicit allow_exception acknowledgement; tracked/untracked recovery INCONCLUSIVE, acknowledged control PASS. |
| R4 | P1 | Invalid negative budget tail bypassed aggregate check and earlier replay targets ran before validation | Fixed: entire batch normalized/validated before execution and monotonic aggregate budget. Independent marker count0 for same malformed request. The unsafe180s slow prefix was never actually run. |
| R5 | P2 | Null replay limits escaped input handler, printed traceback/local paths | Fixed: object/type checks and concise CLI ValueError; independent marker count0. |
| R6 | P2 scope limit | Direct public asyncio.Task construction bypasses factory accounting and completed-task retention | Accepted **residual limitation**, disclosed in runtime limitations, README and API. Probe/loop-factory creation paths are required; no global task/hard resource cap claim. |

Additional verified fixes: invalid must_finish validated before scheduling/closing a task; late cleanup exceptions become FAIL; baseline/framework tasks cannot be registered as application cancellation targets; two queued loop turns prevent a false pending-task verdict from HTTPX async-generator finalization. Lower report-contract gaps (aggregate version, concise stderr status) were fixed and covered by interface regression tests. The reviewer independently ran39 tests+4 subtests successfully; the primary then verified final contract fields and the complete clean-platform matrix.

Safety review boundaries:

- Actual targets and dependencies are trusted local code. No malicious target or real attack system was used. Importing targets executes code; process isolation is not an arbitrary-code sandbox.
- Parent deadline tests include synchronous loop blocking and cancellation-resistant shutdown. Only directly owned child processes are reaped; descendant processes/native remote side effects and memory are not constrained.
- Caller task survives normal runs without cancellation; cancellation of the async API propagates after child recovery. Public loop factory/exception handler are restored on exit.
- Exception messages, full paths, locals and raw stdout/stderr are omitted from default report. User-approved values/labels can still be sensitive. Private temporary cleanup can fail under persistent external locks; that is disclosed with INCONCLUSIVE/warning rather than hidden.
- HTML escapes payload and has a restrictive CSP; Markdown indents payload. No scripts/network resources or report evaluation. Output directories cannot overwrite existing evidence.
- Dependency commits/hashes/licenses were reviewed before installing. Old pytest8.4.2/idna3.11 were rejected for published advisories. This is not a comprehensive vulnerability scan or supply-chain attestation.
- Default child exception ambiguity is deliberately INCONCLUSIVE because public APIs cannot reliably infer application exception consumption. Explicit contracts are essential; missing invariants cannot prove correct business behavior.
- Extremely unusual OS termination failures, malicious factory replacement, direct Task construction, broad dependency combinations, real workload false positives and long aggregate-budget expiry were NOT RUN or unsupported. No blanket production assurance is claimed.
