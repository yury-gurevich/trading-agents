<!-- Agent: planning | Role: research folder landing page -->
# R005 — Container base image: what should the 14 agent images stand on?

**Date:** 2026-07-19 · **Status:** 🚧 Proposed (operator decision pending)
**Trigger:** backlog row H — the S129 Trivy gate found 22 HIGH/CRITICAL Debian CVEs per
representative image on `python:3.13-slim`; operator asked why we are tied to that image and
what the industry-standard free base is.

## Why we are on `python:3.13-slim` at all

No decision was ever taken — it is the Docker-official default every Python project starts
from. Its CVE count is a structural property, not negligence: Debian ships a full userland
(apt, perl, libs), Debian patches on its own cadence, and many scanner findings are
`will_not_fix`/no-fix-available in stable. Standard Debian-based Docker Hub images average
~280 known CVEs; ours showing 22 HIGH/CRITICAL is typical, and most are likely unfixable by
us via `apt upgrade` at all.

## The 2026 landscape (researched 2026-07-19)

| Option | CVE posture | Python fit | Free-tier catch |
| --- | --- | --- | --- |
| `python:3.13-slim` (Debian) — current | ~22 HIGH/CRIT typical; patches on Debian cadence | Perfect (glibc, manylinux wheels) | none — but the red gate is permanent noise |
| Alpine (`python:*-alpine`) | fewer, not zero | **Poor** — musl breaks manylinux wheels → source builds, perf issues; explicitly discouraged for Python | n/a — ruled out on fit |
| Google distroless (`gcr.io/distroless/python3`) | near zero | OK (glibc/Debian) but no shell/pip — hard to debug, awkward with uv | pinning/version lag; python3 image historically "experimental" |
| Chainguard (Wolfi) | zero/near-zero, rebuilt within hours | Good (glibc) | **free tier = `latest`/`latest-dev` tags only — version pinning is paid**, which fights our immutable-tag convention |
| **Docker Hardened Images (DHI)** — `dhi.io/python:3.13` | near zero, continuously rebuilt from source; SBOM + signatures | Good (Debian- and Alpine-based variants; pick Debian/glibc) | **None known — went free + open source (Apache 2.0, Dec 2025), 1,000+ images, full catalog, no usage restrictions**; paid tiers only add SLA/FIPS/customization |

Industry commentary (pythonspeed, Feb 2026) adds a complementary pattern: use **uv-managed
Python** on any stable LTS base, decoupling the distro from the Python version — we already
run uv inside the image, so this composes with any base choice.

## Recommendation (two steps, decoupled)

1. **Now (drains the red gate honestly):** add `ignore-unfixed: true` to the Trivy step —
   the industry-standard posture: fail only on CVEs that *have* a fix we can take. Findings
   with no Debian fix stop failing builds without being silently accepted (they remain in
   the scan report). Zero base-image risk change; likely turns `build-images` green today.
2. **Next chore (the real fix):** migrate the shared Dockerfile pattern to
   **`dhi.io/python:3.13` (Debian/glibc variant)**. Near-zero CVE, free, pinnable,
   drop-in-adjacent: the runtime image is minimal (no shell), so the single-stage
   `pip install uv && uv sync` build becomes a two-stage build (`-dev` variant builds,
   runtime variant runs). One template edit ×14 Dockerfiles; Trivy gate then enforces
   against a near-zero baseline, `.trivyignore` stays empty.

**Ruled out:** Alpine (musl vs Python wheels — hard fit problem); Chainguard free tier
(unpinnable tags break immutable-tag deploys + DL-46 currency evidence); staying put with a
permanently red gate (alarm fatigue erodes the gate's meaning); disabling the gate
(S129 shipped it for a reason).

## Sources

- [Docker press release — Hardened Images free/open (Apache 2.0)](https://www.docker.com/press-release/docker-makes-hardened-images-free-open-and-transparent-for-everyone/)
- [BleepingComputer — DHI now open source and free](https://www.bleepingcomputer.com/news/security/docker-hardened-images-now-open-source-and-available-for-free/)
- [TechTarget — Free DHI challenge Chainguard](https://www.techtarget.com/searchitoperations/news/366636656/Free-Docker-Hardened-Images-challenge-Chainguard)
- [pythonspeed — Best Docker base image for Python (Feb 2026)](https://pythonspeed.com/articles/base-image-python-docker-images/)
- [Chainguard — best Python Docker image compared](https://www.chainguard.dev/supply-chain-security-101/best-python-docker-image-top-options-compared)
- [Big Iron — distroless vs alpine vs debian-slim](https://www.bigiron.cc/guides/distroless-vs-alpine-vs-debian-slim-base-image-choice)
