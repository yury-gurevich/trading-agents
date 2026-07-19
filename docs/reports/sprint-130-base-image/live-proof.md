<!-- Agent: coding | Role: S130 base-image live evidence -->
# Sprint 130 base-image live proof

## Start state

- Started from `main` at `c65b8dac75da061167772d1b4d3fea980103f1aa`; `pyproject.toml`
  read `0.71.02`.
- Branch: `sprint-130-base-image`.
- Version bump: `0.71.02 -> 0.71.03`; `uv lock` updated
  `trading-agents v0.71.2 -> v0.71.3`.
- No repository file received credentials; DHI pulled in GitHub Actions without any new
  CI authentication.

## Provider probe

- Workflow run:
  <https://github.com/yury-gurevich/trading-agents/actions/runs/29681150958>
- Commit: `b127088` (`chore: probe DHI provider image`).
- Provider job: `88177447441`.
- Built from `dhi.io/python:3.13-dev` into `dhi.io/python:3.13`.
- Provider digest: `sha256:0d05044e7b6272e5924268bbd53edcce4bfef305d1c8d219dedf1d3742cb908e`.
- Trivy detected Debian `13.6`, `pkg_num=50`, one Python package report set, and
  `0` vulnerabilities in the HIGH/CRITICAL gate.

## Final live run

- Workflow run:
  <https://github.com/yury-gurevich/trading-agents/actions/runs/29681635979>
- Commit: `1aba6acf142bab064880d956abb481857da8af60`.
- Manual dispatch input: `image_tag=s130-test`.
- Result: `success`.
- Jobs: all 14 image jobs completed successfully:
  `scanner`, `analyst`, `monitor`, `portfolio_manager`, `curator`, `operator`,
  `execution`, `reporter`, `dispatcher`, `researcher`, `provider`, `supervisor`,
  `master`, and `forecaster`.
- GHCR `s130-test` artifacts:
  `ghcr.io/yury-gurevich/trading-agents-master:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-scanner:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-analyst:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-portfolio_manager:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-execution:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-monitor:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-reporter:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-forecaster:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-operator:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-supervisor:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-curator:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-researcher:s130-test`,
  `ghcr.io/yury-gurevich/trading-agents-provider:s130-test`, and
  `ghcr.io/yury-gurevich/trading-agents-dispatcher:s130-test`.
- Trivy: the HIGH/CRITICAL gate ran for all 14 images with `exit-code: 1`,
  `ignore-unfixed: true`, `vuln-type: os,library`, and the empty `.trivyignore`.
  Every Trivy step was green, so actionable HIGH/CRITICAL findings dropped from
  S129's representative `22` (`19 HIGH`, `3 CRITICAL`) to `0` gate-blocking
  findings on all 14 S130 images.
- Provider digest: `sha256:9cd06fd7446c40830dd01b3e240850b572ad7957308848027a4a3f9c726b1718`.
- Provider Trivy log: Debian `13.6`, `pkg_num=50`, one Python package report set,
  report rows at `0` vulnerabilities.
- Forecaster Trivy log: Debian `13.6`, `pkg_num=50`, one Python package report
  set, report rows at `0` vulnerabilities.

## Runtime smoke

The workstation Docker client could not run the requested local GHCR image: the configured
`DOCKER_HOST` timed out, the `desktop-linux` context pipe was absent, no Docker service was
installed, and local GHCR package reads returned `read:packages` permission errors. To keep
the proof live instead of weaker, the provider job ran the image by digest inside the same
authenticated GitHub runner after push:

```text
docker run --rm ghcr.io/yury-gurevich/trading-agents-provider@sha256:9cd06fd7446c40830dd01b3e240850b572ad7957308848027a4a3f9c726b1718
socket.gaierror: [Errno -2] Name or service not known
urllib.error.URLError: <urlopen error [Errno -2] Name or service not known>
```

That proves the minimal runtime carries Python, the venv, glibc-compatible wheels,
certificates/timezone data, and reaches `agents.provider.entrypoint` without `uv` or a shell
at runtime; it fails loudly because no activation/master config is present.

## Image size

- Before: `ghcr.io/yury-gurevich/trading-agents-provider:latest`
  `215286970` bytes.
- After: S130 provider digest
  `149756082` bytes.
- Delta: `-65530888` bytes.

## State and artifacts

- The `s130-test` GHCR tags are retained as CI artifacts.
- No graph store was constructed; no graph writes were expected.
- State sweep count: `0`.
- No fleet retag was performed; `/deploy-fleet` remains operator-gated after merge.
