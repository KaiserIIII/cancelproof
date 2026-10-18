# Third-party materials

CancelProof source is MIT, Copyright 2026 KaiserIIII. No competitor, issue snippet, wheel, runtime, or copied third-party implementation is vendored in this source distribution. Constructed broken/fixed scenarios and the ASGI service are independently written test fixtures. Historical raw issue snippets, upstream source archives and environment logs remain outside the public source in the local evidence directory.

The runtime engine uses Python's standard library (PSF license). `DEPENDENCIES.json` pins development artifacts to source repository, exact commit, wheel SHA256 and review time. Install actions are recorded in external evidence. Selected libraries retain their own licenses in installed distributions:

| Development dependency | License / role |
|---|---|
| pytest, iniconfig, pluggy, setuptools | MIT; test runner/build backend (setuptools includes separate vendored notices) |
| packaging | Apache-2.0 OR BSD-2-Clause; package metadata |
| Pygments | BSD-2-Clause; pytest output |
| colorama | BSD-3-Clause; Windows console |
| HTTPX | BSD-3-Clause; ASGI transport demonstration |
| httpcore | BSD-3-Clause; HTTPX dependency, no remote service in tests |
| AnyIO | MIT; HTTPX dependency |
| idna | BSD-3-Clause; HTTPX/AnyIO dependency |
| h11 | MIT; HTTPX dependency |
| sniffio | MIT OR Apache-2.0; async library detection |
| typing_extensions | PSF-2.0; AnyIO types |
| certifi | MPL-2.0 certificate data and package notices; HTTPX dependency |

These libraries are installed, not relicensed as CancelProof. Dependency source/license inspection is not a full supply-chain security guarantee. Initially considered pytest8.4.2 and idna3.11 were rejected for current published advisories; selected versions are 9.1.1 and 3.20. Old AnyIO wheels are used only in isolated historical reproduction environments, not shipped or recommended as current dependencies.

Research-only source archives: pytest-asyncio (Apache-2.0), AnyIO (MIT), pytest-anyio placeholder (MIT), Trio (MIT OR Apache-2.0), pytest-trio (MIT OR Apache-2.0), LoomCheck (MIT), simloop (MIT), pyleak (Apache-2.0), Hypothesis (MPL-2.0). See `docs/COMPETITORS.md` for exact revisions and execution boundaries. No research archive is included in the package or public source ZIP.

GitHub Actions references are pinned to reviewed official actions commits in `.github/workflows/checks.yml`; licenses remain with the actions' repositories. No Actions execution is claimed until actual runs exist.
