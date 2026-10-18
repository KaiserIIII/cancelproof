# Security and privacy boundary

Only run trusted local scenarios and trusted dependencies. Importing `module:callable` executes its module (and package parents), even if a later source digest mismatch prevents callable execution. There is no eval endpoint or remote target loader, but executing Python is inherently arbitrary code execution with the caller's permissions. This is not a malicious-code sandbox.

The watchdog bounds a directly owned child, polls output size, terminates/kills/reaps it, and avoids raw stdout/stderr export. This does not impose OS memory quotas, prevent forked descendants, revoke filesystem/network access, or make native-code cleanup safe. Do not aim it at private production systems or run as administrator unnecessarily.

Default exception diagnostics omit messages, source lines, full paths and locals. Explicit event values, scenario names, labels, relative filenames and business evidence can still reveal secrets. Review reports before sharing. HTML is escaped and inert; no JavaScript, external CSS, image loads or telemetry. Output directories cannot overwrite existing evidence.

Dependency wheel hashes and source commits are recorded in the lock/manifest; hashes authenticate selected artifacts, not a proof against malicious maintainers. No automatic dependency execution before source/license review. Historical vulnerable dependencies are restricted to isolated reproduction environments and are not shipping runtime dependencies.
