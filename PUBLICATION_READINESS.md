# Local delivery decision

**READY_WITH_LIMITATIONS** — runnable source experimental edition. Core engine, API, pytest integration, CLI/replay/reports, real ASGI request tests and fresh Windows/Linux installation are verified. The narrowly integrated workflow has engineering value; no new scheduler/detection/scientific contribution is claimed.

There is no known remaining P0/P1 in the tested scope after independent counterexample repair. Readiness remains qualified because:

1. Direct asyncio.Task construction/custom task factories bypass accounting/retention and are unsupported; no hard memory/descendant sandbox exists.
2. Child exception consumption cannot be inferred reliably; ambiguous outcomes remain INCONCLUSIVE unless explicitly acknowledged/contracted.
3. Ordinary event-loop/OS scheduling is not controlled; a matching source digest covers one module only.
4. Linux3.12, Trio/Hypothesis runtime baselines, hosted Actions and production/generalization evaluation are NOT RUN. Linux3.13 and Windows3.12/3.13 are actually verified.
5. Optional AnyIO4.15.1 still exhibits its known #1214 concurrent-cancel issue; its unreleased pinned fix was tested separately. The tool does not patch dependencies.
6. Clean venv/clone acceptance is not a claim of independent bare-metal environments or broad accuracy.

Public-source preparation includes MIT license, third-party notices, exact development wheel hashes/source commits, README/Chinese guide, scope warnings, inert example reports, safe validation summaries and a public file manifest. Raw research downloads, original issue snippets, local execution logs, private runtime/cache/venv directories and the user's pasted request remain outside the source distribution. No private application data was used.

No GitHub repository, push, Release, PyPI package or public service is created. Publication would require separate authorization; this delivery remains local. Feature development is frozen at the delivered candidate, with only evidence/document packaging after the tested implementation commit.
