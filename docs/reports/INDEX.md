<!-- Agent: planning | Role: reports folder map -->
# Reports index — sprint live-check evidence

**How to use:** every folder here is the committed evidence bundle for one sprint's
real-environment functionality check (proof docs, transcripts, screenshots). The narrative
row for each check lives in [../laws/functionality-checks.md](../laws/functionality-checks.md);
the sprint doc in [../sprints/](../sprints/INDEX.md) links here from its closeout. Start with
the folder's landing file (`live-proof.md` / `live-check.md` / `README.md`), then open the
supporting artifacts it cites.

**Convention:** one folder per sprint, named `sprint-NN-<slug>/` (matching the sprint doc's
slug). It holds only evidence for that sprint's live check — never live code or config.
Earlier sprints (≤ S118) recorded evidence inline in `functionality-checks.md` and the sprint
docs; committed bundles start at S119.

| Folder | Sprint | Evidence |
| --- | --- | --- |
| [sprint-119-deliberation-roles/](sprint-119-deliberation-roles/README.md) | S119 (DL-42) | DSPy role-prompt compile: README + golden-firewall/load-path/live-report proofs + probe/report transcripts per role |
| [sprint-121-judge-promotion-challenger-recompile/](sprint-121-judge-promotion-challenger-recompile/README.md) | S121 (DL-42 resolution) | Judge promotion + challenger recompile: README + compile/refreeze/firewall/default-deliberation proofs + transcripts |
| [sprint-123-dashboard-fleet-infra/](sprint-123-dashboard-fleet-infra/) | S123 (DL-47 slice 2) | Screenshots: infrastructure section, fleet vitals, execution log drawer |
| [sprint-124-dashboard-verdict/](sprint-124-dashboard-verdict/) | S124 (DL-47 slice 3) | Screenshots: GREEN `NO_TRADE` verdict, RED incomplete-run verdict |
| [sprint-125-operator-chat/](sprint-125-operator-chat/) | S125 (DL-47 slice 4) | Screenshots (grounded answer, not-connected state) + `priced-ledger.json` cost proof |
| [sprint-126-resume-and-tripwire/](sprint-126-resume-and-tripwire/live-proof.md) | S126 (DL-47 slice 5) | `live-proof.md` + screenshots (resume child run, bus unverified) |
| [sprint-127-fixpack/](sprint-127-fixpack/live-proof.md) | S127 (fixpack) | `live-proof.md` + 5 screenshots (flag ack flow, template currency, warning links) |
| [sprint-128-feed-resilience/](sprint-128-feed-resilience/live-check.md) | S128 (DRIFT-021) | `live-check.md` (2026-07-19 pass) + `code-and-live-preflight.md` (2026-07-16 blocked preflight, DRIFT-023) |
| [sprint-129-fixpack/](sprint-129-fixpack/live-proof.md) | S129 (fixpack) | `live-proof.md`: deliberation quant-metrics, TTL-cache egress proof, GitHub hardening D/E, teardown |
| [sprint-130-base-image/](sprint-130-base-image/live-proof.md) | S130 (R005 / backlog H) | `live-proof.md`: DHI migration run `29681635979`, all-14 Trivy green, runtime smoke, image size |
| [sprint-131-blast-radius/](sprint-131-blast-radius/live-proof.md) | S131 (blast radius) | `live-proof.md`: per-agent Postgres role provisioning, Container Apps secret-backed env flip, role activity audit, canary revocation, dispatcher image-slim proof |
| [sprint-132-mutation-testing/](sprint-132-mutation-testing/README.md) | S132 (backlog G) | `README.md` + `actionable-mutants.csv`: scoped manual `mutmut` run over decision engines; 5,376/6,731 killed (79.87%), 1,355 documented-equivalent actionable rows |
