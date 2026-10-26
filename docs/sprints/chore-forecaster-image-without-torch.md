<!-- Agent: planning | Role: chore spec + closeout: the forecaster image drops FinBERT's stack; the record names the model that scored -->
# chore-forecaster-image-without-torch — the forecaster image installs only what its deployed leg runs, and a sentiment record names the model that actually scored

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `chore-forecaster-image-without-torch`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** work-queue 141 option A (the operator, 2026-10-26: *"do 141 A for CODEX"*) ·
[DL-316](../design-log.md) (amendment 2026-10-26) · [ADR-0002](../decisions/0002-sentiment-champion-challenger.md) (amended by this chore) ·
closes [DRIFT-116](../laws/drift-register.md)

> **Why a PATCH.** No new capability. The law and ADR-0002 say an injected FinBERT scores the sentiment
> leg; no caller injects one, and the forecaster image carries torch and transformers for it. This
> makes the image, the laws and the record say what is true. The fleet's behaviour is unchanged.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

| Element | Law file | Clauses to read first |
| --- | --- | --- |
| `agents/forecaster/Dockerfile`, `pyproject.toml` extras | [`agents/forecaster/laws/laws.md`](../../agents/forecaster/laws/laws.md) | `FORE-IDN-01`, `FORE-PERF-01`, `FORE-PERF-02`, `FORE-TRG-01` |
| `agents/forecaster/agent.py`, `model.py`, `finbert.py` (the `Model` node's `ref`) | the same | `FORE-IDN-01`, `FORE-IDN-02`, `FORE-OBS-*`, `FORE-OUT-*` (whichever names the `Model` node) |
| ADR-0002 | [`docs/decisions/0002-sentiment-champion-challenger.md`](../decisions/0002-sentiment-champion-challenger.md) | the 2026-10-24 amendment |

**Law-cycle question — does this chore change `contracts/` or add a guarantee?** It changes no
`contracts/` file. It **amends two clause texts** (`FORE-IDN-01`, `FORE-PERF-01`) to say what the code
does, so the law book goes **LOCKED v1.12 → v1.13** with a changelog line, and every new test cites
the clause it proves. No new guarantee is added.

---

## Goal

After this chore: the forecaster image installs the `runtime`, `azure` and a new `barrier` extra
(`arch` only), not torch, transformers or lightgbm; the `forecaster` extra is unchanged for offline
research (EXP-024 used it); a sentiment record's `Model` node names the model that produced the scores
(the neutral fake when none is injected), not `ProsusAI/finbert`; `FORE-IDN-01`, `FORE-PERF-01` and
ADR-0002 say FinBERT is an offline research scorer that no fleet path runs; DRIFT-116 reads CORRECTED.

## Why (context)

### Measured, 2026-10-26 — read these before designing

- `agents/forecaster/Dockerfile` installs `uv sync --frozen --extra runtime --extra azure --extra forecaster --no-dev`; its comment says the extra is for *"PyTorch + Transformers (FinBERT)"*. *[measured, file read]*
- `pyproject.toml:30`: `forecaster = ["torch>=2.13.0", "transformers>=5.14.1", "lightgbm>=4.7.0", "arch>=8.0.0"]`. *[measured]*
- `agents/forecaster/poll.py:50`: `DEPLOYED_CAPABILITIES = (BARRIER_CAPABILITY,)`: the deployed loop fires only `forecast_barrier`. *[measured]*
- `finbert.py`, `lightgbm_model.py` and `model_trainer.py` import their package lazily through `importlib`; `barrier_fit.py`'s adapter imports `arch`. *[measured, grep of every `torch|transformers|lightgbm|arch` import under `agents/forecaster`, `kernel`, `orchestration`, `scripts`]*
- No production path builds `FinBERTModel`: `agents/forecaster/entrypoint.py` and `orchestration/local_pipeline.py:85` build `ForecasterAgent` with no `model`, which falls back to `FakeSentimentModel` (neutral 0.5). *[measured 2026-10-26 closing work-queue 139]*
- `agent.py:94` writes `model_ref=self._settings.model_ref` (default `"ProsusAI/finbert"`, `settings.py:23`) whatever model scored, so the local pipeline's `Model` node labels the fake's readings `ProsusAI/finbert`. *[measured]* `agent.py:119` does the same for the return leg with `return_model_ref`. *[measured; whether the return leg also runs a fake under that label is NOT measured, see Out of scope]*
- Sizes in the main venv: torch 490 MB, transformers 57 MB, arch 3 MB. *[measured 2026-10-26]* torch and huggingface-hub are how the 2026-10-26 filelock and setuptools advisories reached the lock.
- `scripts/check_dependency_audit.py` audits the lock with `--all-extras` (line 39), so torch stays audited after this chore. *[measured, grep]*
- `mutants/` is git-ignored; its `Dockerfile` copy is not part of this chore. *[measured]*
- Line counts now: `agent.py` **169**, `model.py` **40**, `finbert.py` **46**, `tests/test_served_agent_images.py` **94**, `agents/forecaster/tests/test_forecaster_finbert.py` **73**. *[measured]*

## Scope — and what is deliberately NOT here

1. `pyproject.toml`: add `barrier = ["arch>=8.0.0"]` with a one-line comment (the deployed barrier leg). Leave `forecaster` as it is.
2. `agents/forecaster/Dockerfile`: `--extra barrier` in place of `--extra forecaster`; fix its comment.
3. `uv.lock`: re-lock for the new extra and the PATCH bump, staged with them.
4. The sentiment port names its model: `SentimentModel` gains a `ref: str` attribute; `FakeSentimentModel.ref` is a fixed name that says it is the neutral fake (builder picks the string; state it in the closeout); `FinBERTModel.ref` is the `model_ref` it loaded. `agent.py` writes `self._model.ref` (the injected or fallback model's) instead of `settings.model_ref`. `settings.model_ref` stays, as the name `FinBERTModel` loads.
5. Laws v1.13: `FORE-IDN-01`'s sentiment leg is *"the injected sentiment model; no fleet path injects one, so the leg scores with the neutral fake, and the deployed loop does not fire it (`FORE-TRG-01`); FinBERT is an offline research scorer (EXP-024)"*. `FORE-PERF-01`: *"an injected sentiment model runs locally (no network call at inference)"*. Changelog line citing this chore, work-queue 141 and DRIFT-116. Test-plan rows for the new tests.
6. ADR-0002: an amendment dated 2026-10-26 — FinBERT is an offline research scorer; the fleet image does not carry it; the challenger seat is empty until a sprint wires a model (work-queue 141 option B, not chosen).
7. `docs/laws/drift-register.md`: DRIFT-116 → `CORRECTED` with this chore's name.

### Out of scope (do NOT build this chore)

- Wiring FinBERT, or any sentiment model, into the fleet (option B, not chosen).
- Removing `finbert.py`, `lightgbm_model.py`, `model_trainer.py` or the `forecaster` extra.
- The return leg's label (`agent.py:119`). If you find it also labels a fake as `lightgbm-gbdt`, **record it in Return notes; do not fix it.**
- Any other Dockerfile, any `infra/` file, any deploy.

### The road not taken (LAW-06)

- **Option B (wire FinBERT as a fleet shadow leg):** cost in the fleet unmeasured; EXP-024 found no signal. Not chosen by the operator.
- **Option C (leave it):** keeps 547 MB of unused packages in an image and a law that says something false.
- **Drop `arch` from `forecaster` and make it include `barrier`:** a self-referencing extra adds a lock subtlety for no gain; the duplicate `arch` line is harmless.
- **Change `settings.model_ref`'s default instead of recording the model's own `ref`:** it would still lie whenever the injected model differs from the setting.

## Blast radius — measured 2026-10-26

| Area | Effect |
| --- | --- |
| Fidelity decision paths | **None.** `agents/forecaster/` is not one (`scripts/replay_fidelity_git.py`). The count holds. |
| Fleet behaviour | None: the deployed loop fires only `forecast_barrier`, whose packages (`arch` and its numpy/scipy/pandas dependencies) stay. |
| Graph | The local pipeline's sentiment `Model` node `ref` changes value. The deployed fleet writes no sentiment `Model` node. No new label or property. |
| Deploy | Image-only retag after merge, **on the operator's word**; not part of this chore. |
| Rollback | Retag to `s288`. |

## Steps, in order

1. `git worktree add ../ta-chore-forecaster-slim -b chore-forecaster-image-without-torch main`; work only there.
2. Fill the **Law reading record** below.
3. Write tests A1–A4, run them, paste the **red** output.
4. Make the change (scope 1–7), bump PATCH in `pyproject.toml`, then `uv lock --offline`. If that fails for want of the network, **stop that step only**, record the exact error, leave `uv.lock` untouched, and say so in the closeout: the planner re-locks before merging.
5. F1 (below), then `make ci > <file> 2>&1 ; echo $?` and read the file. Commit; do not push if the sandbox refuses (the planner pushes and runs `make gate-ran`).

## Test plan

| # | Test | Clause |
| --- | --- | --- |
| A1 | The forecaster Dockerfile's `uv sync` names `--extra barrier` and not `--extra forecaster` (pattern: `tests/test_served_agent_images.py`) | `FORE-PERF-01` |
| A2 | `pyproject.toml`'s `barrier` extra (read with `tomllib`) contains `arch` and no `torch`, `transformers` or `lightgbm` | `FORE-IDN-01` |
| A3 | An agent built with no model writes a `Model` node whose `ref` is `FakeSentimentModel.ref`; one built with a model whose `ref` is `"x"` writes `"x"` — never `settings.model_ref` | `FORE-IDN-01`, plus whichever clause names the `Model` node |
| A4 | `FinBERTModel(model_ref="m").ref == "m"`, with the fake `transformers` the existing tests use (no torch) | `FORE-PERF-01` |

**Breaks to plant (each must turn a test red, then restore):** put `--extra forecaster` back in the
Dockerfile (A1); add `torch` to `barrier` (A2); write `settings.model_ref` in `agent.py` again (A3).

**F1 — the image's closure, at no cost, no network:**

```bash
UV_PROJECT_ENVIRONMENT="$TMP/fslim" uv sync --frozen --offline --extra runtime --extra azure --extra barrier --no-dev
"$TMP/fslim/bin/python" -c "import agents.forecaster.entrypoint"                 # must succeed
"$TMP/fslim/bin/python" -c "import torch"        # must fail: ModuleNotFoundError
"$TMP/fslim/bin/python" -c "import transformers" # must fail
"$TMP/fslim/bin/python" -c "import lightgbm"     # must fail
```

Then one real `arch` fit through the `barrier_fit.py` adapter on 300 synthetic daily returns, in that
env (write the five-line script in the closeout). On Windows the interpreter is `Scripts/python.exe`.
`--offline` needs every locked wheel in the local uv cache *[assumed]*; if one is missing, record which
and stop F1 there.

## Success factors

- A1–A4 red first, then green; three breaks red then restored.
- F1: the import succeeds, the three heavy imports fail, the `arch` fit returns.
- `make ci` exit 0, all steps, 100.00 % coverage, read from the redirect file.
- Laws v1.13, ADR-0002 amendment, DRIFT-116 CORRECTED, this spec's **Status:** `BUILT` and its
  `README.md` row in the same commit.

## Traps

🪤 **The CI venv has every extra**, so a green `make ci` cannot show the image misses a package. Only F1 can.
🪤 **`uv sync --frozen` with a new extra and a stale lock fails**, and looks like an F1 failure. Re-lock first (step 4).
🪤 **A 40-hex SHA in a test trips detect-secrets.** Put `# pragma: allowlist nextline secret` on the line above (inline breaks E501).
🪤 **`agent.py` is 169 lines** (warn at 150): the change is one line; do not grow it past 170.

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it.
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**. Never measure it through a pipe.
- PATCH bump, `uv.lock` staged with it (or recorded as owed, step 4).
- A worktree has **no `.env`**; nothing here needs one. State which tree you ran in.

## Sequencing after merge

1. Planner: `make ci`, push, `make gate-ran` from the worktree (SHA checked against `git rev-parse HEAD`), CodeQL set-diff, merge, push.
2. The image build on merge: planner reads the forecaster image's size against `s288`'s.
3. Deploy: image-only retag, **on the operator's word**. F2 on the next scheduled run: the forecaster writes its barrier claims and settlements as before, no forecaster `error` fault.

---

## Handover — paste this to Codex

```text
Build the chore in docs/sprints/chore-forecaster-image-without-torch.md, in a new worktree
../ta-chore-forecaster-slim on branch chore-forecaster-image-without-torch from main. Never on main.

MUST RULE: before any code, read agents/forecaster/laws/laws.md (FORE-IDN-01, FORE-IDN-02,
FORE-PERF-01, FORE-PERF-02, FORE-TRG-01, and whichever clause names the Model node) and fill the
spec's Law reading record. Law-cycle answer: no contracts/ change; two clause texts are amended,
the book goes LOCKED v1.12 -> v1.13 with a changelog line; every new test cites its clause ID in
its docstring.

Order: tests A1-A4 first, run them red, paste the red output; then scope items 1-7; PATCH bump;
`uv lock --offline` (if it fails for want of network, record the error, leave uv.lock alone and
go on: the planner re-locks). Plant the three breaks, see each red, restore. Run F1 exactly as
written (it is the only proof the image's closure holds; CI's venv has every extra). Then
`make ci > <file> 2>&1 ; echo $?` and read the file — never through a pipe.

DO NOT: wire FinBERT into anything; delete finbert.py, lightgbm_model.py, model_trainer.py or the
forecaster extra; touch any other Dockerfile or infra/; fix the return leg's label (agent.py:119)
— report it in Return notes if it also mislabels a fake; grow agent.py past 170 lines.

Stop rule, two tiers: a wrong command, count or path whose intent is plain — fix it, record it in
Return notes, continue. Anything that would change the design or the scope — record it and stop.

Handback: fill Law reading record, Test plan results, Closeout (pasted output), Return notes;
set Status: BUILT and the README.md row's status to BUILT in the same commit. Write no Result for
work not done; say "not done" or "verified failing" plainly.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed:**

**Clauses that were ⬜ and are now proven:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Status:**

**Tree the proofs ran in (and `.env` present?):**

**Result:**

**Files changed:**

**`FakeSentimentModel.ref` chosen:**

**Proof — the red run first:**

**Proof — the green run:**

**Guards planted:**

**F1 (closure, offline):**

**Module line counts:**

**`uv lock --offline`:** done / owed (error pasted)

**`make ci`:**

**`make gate-ran`:** planner's step

**Not met / verified failing:**

---

## Return notes

-
