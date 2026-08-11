<!-- Agent: kernel | Role: sprint spec — finish moving the LLM vendor layer into the substrate -->
# S170 — one LLM adapter set, in the plumbing, for every agent that calls a model

**Closes:** [DL-101](../design-log.md) · **Type:** fix (consolidation; no new capability) ·
**Target version:** 0.90.03 (PATCH; retargeted 2026-08-11) ·
**Branch:** `sprint-170-one-llm-adapter-in-the-plumbing`

> Handover to a delegated coding agent. Everything under **Measured** was observed on
> 2026-08-08 while executing `chore-openai-cutover`. Everything marked **Assumed** has *not*
> been verified — check it before building on it.

## Why

**The LLM layer is half in the substrate.** The port and the audit ledger are kernel; the vendor
adapters and provider selection are not, and they are duplicated per agent.

**Measured — what is already correct:**

| In `kernel/` | What it does |
| --- | --- |
| [`llm.py`](../../kernel/llm.py) | `LLMClient` protocol + `FakeLLMClient` — the port |
| [`llm_ledger.py`](../../kernel/llm_ledger.py) | `record_llm_call` / `write_llm_call` — the append-only `LLMCall` audit node |

Both model-calling agents **do** route through the ledger — the deliberator directly
([`agent.py:131`](../../agents/deliberator/agent.py#L131)), the operator through a thin wrapper
([`agents/operator/ledger.py`](../../agents/operator/ledger.py)). So "calls go through the
plumbing" is already true for the *audit* path. This sprint is not about that.

**Measured — what is not:**

| Still in an agent | Duplicate of |
| --- | --- |
| [`agents/deliberator/llm_anthropic.py`](../../agents/deliberator/llm_anthropic.py) | — |
| [`agents/deliberator/llm_openai.py`](../../agents/deliberator/llm_openai.py) | — |
| [`agents/deliberator/llm_factory.py`](../../agents/deliberator/llm_factory.py) | — |
| [`agents/operator/llm_anthropic.py`](../../agents/operator/llm_anthropic.py) | **the deliberator's** |

The two `AnthropicLLMClient` classes share a name, a `ConfigurationError`, a constructor
signature, the `importlib` SDK load and the empty-key guard. They differ in **one method**:
`complete()` is free-text for the deliberator and tool-use for the operator. One method's worth of
difference is being paid for with two classes.

**The consequence that makes this a fix rather than tidying.** S168 added the OpenAI fallback to
`llm_factory`, which **only the deliberator has**. The operator has no factory, no `llm_provider`
tunable and no OpenAI client, so it can call Anthropic and nothing else — while the Anthropic key
is usage-limited until **2026-09-01**. "We have a vendor fallback now" is true for one of the two
model-calling agents. And [`surfaces/dashboard/chat_binding.py:13`](../../surfaces/dashboard/chat_binding.py#L13)
imports `agents.operator.llm_anthropic` directly, so a **surface** is wired to a specific agent's
vendor adapter, and the dashboard chat inherits the same single-vendor exposure.

🪤 **Why this is not merely "move the files".** A vendor adapter is plumbing (I/O), so kernel is its
correct home — but `complete()`'s *shape* is not: free-text vs tool-use is a real difference in what
the caller needs back. Moving both clients under one name without preserving that distinction would
silently change what the operator receives. The split must survive the move.

**Assumed, unverified:** that nothing outside these four modules constructs a vendor client
directly. Grep before moving — `chat_binding.py` was found only by reading imports.

## Steps, in order

1. **Move the vendor adapters into `kernel/`,** keeping the two response shapes explicit and named
   (free-text completion vs tool-use completion) rather than collapsing them.
2. **Move `llm_factory` into `kernel/`,** with `KEY_ENV` and the provider→default-model table it
   gains in [S169](sprint-169-one-switch-and-a-deploy-that-keeps-it.md). If S169 has not shipped,
   do that first — this sprint moves the file, it does not redesign it.
3. **Give the operator the same provider switch** the deliberator has: an `llm_provider` tunable
   resolved through the shared factory. Grant `openai-api-key` to `operator` in
   `orchestration/packs/trading_secrets.json` — the deliberator entries are the pattern
   (`chore-openai-cutover`, 2026-08-08).
4. **Stop the surface importing an agent's adapter.** `chat_binding.py` builds its client from the
   kernel factory.
5. **Delete the duplicates** — no compatibility shim. Two names for one thing is the defect.

## Success factors

- [ ] `agents/` contains **no** vendor SDK adapter; `grep -rn "import_module(\"anthropic\"\|import_module(\"openai\")" agents/` returns nothing.
- [ ] The operator's tool-use path returns the **same** structured result as today, asserted by its
      existing tests unchanged in intent — a moved adapter that quietly alters the operator's
      response shape is the one regression that matters.
- [ ] `DELIBERATOR_LLM_PROVIDER=openai` and `OPERATOR_LLM_PROVIDER=openai` each select OpenAI
      through the **one** kernel factory.
- [ ] `LLMCall` nodes still record `calling_agent` distinctly for operator and each deliberator
      role — consolidating the client must not blur who called.
- [ ] Import-linter passes: `kernel` still imports nothing from `agents`/`contracts`, and the
      surface no longer reaches into `agents.operator`.
- [ ] `make ci` exit 0, unpiped to a file; each behaviour watched rejecting a planted violation
      before restoration (DL-70).

## Traps

- The deliberator image installs `--extra llm` deliberately ([Dockerfile](../../agents/deliberator/Dockerfile)),
  because the SDK is resolved through `importlib` at call time and a missing package would fail at
  the first debate turn rather than at import — DL-80's exact shape. **Every image whose agent can
  now call a model needs that extra**, and the operator's Dockerfile must be checked, not assumed.
- Granting `operator` an OpenAI key changes `trading_secrets.json`, which reaches the fleet only via
  `MASTER_SECRET_MAP_B64` on a **full `up`** — an image-only retag ships the code and not the grant,
  and the failure is silent (`chore-openai-cutover`, 2026-08-08).
- `kernel` may not import `contracts`, `agents`, `orchestration` or `surfaces`. If an adapter needs
  a type that lives above the kernel, that is a signal the type is in the wrong place — do not
  weaken the contract to complete the move.

## Closeout — evidence

_To be filled before handback; a handback with placeholders unfilled is not accepted._

**Move.** _The grep proving no adapter remains under `agents/`, and import-linter output._

**Operator.** _A real OpenAI-backed operator call, and its `LLMCall` node's `calling_agent`._

**Not proven.** _State plainly what this does NOT establish._
