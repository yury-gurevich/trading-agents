# Research: Ontology guardrails (RDFS / OWL) for the agent loop

**Source.** Frank Coyle (UC Berkeley), *"Why Agentic Systems Need Ontologies"* — AI Engineer
World's Fair 2026, Track 5 (Graphs), 2 July 2026.
<https://www.youtube.com/watch?v=Sir59K8ZDPU>

**Basis of this evaluation — stated plainly.** The talk was **not watched**; no transcript is
published. This assessment works from the talk's title, its documented thesis, and one slide
(*"RDFS infers. OWL constrains."*) supplied by the operator. The argument summarised below is
therefore reconstructed, not quoted. **What is *not* reconstructed is everything in "What this
platform already has" onward** — that is measured against this repository at commit `8a8ab9c`,
and every claim there carries its evidence.

---

## 0 · In plain language — what a reasoner is, and why it is refused

*Written for the person who has to live with this decision, not for someone who already
knows what entailment means.*

**A reasoner is software that reads rules and then writes new rows into your database that
nobody put there.**

Give it a rule — *anything that fills is a trade*. Record one fact — *ABT sell filled*. The
reasoner quietly adds a second row: *ABT sell is a trade*. You never wrote that row; it worked
it out.

That sounds useful. Here is the catch: a week later you read the database and **you cannot tell
which rows are things that actually happened and which rows the software worked out.** They look
identical.

### Why that is fatal here specifically

This graph is not a general database. It is an **evidence log** — a record of what actually
happened. The whole project runs on one rule: only believe what was proven (LAW-02).

Both of the expensive bugs of July 2026 were the same mistake:

| What was recorded | What it was then treated as | What it cost |
| --- | --- | --- |
| "decided to close MRVL" | "MRVL is closed" | Four positions invisible for days — unscoreable, unexitable |
| "profit at the moment we decided to sell" | "profit we made" | Profit factor and expectancy described trades that never happened |

In both, something only *intended* or *worked out* was treated as something that *happened*.
A reasoner is a machine for producing exactly that kind of row, automatically, at scale. Having
just paid for accidental versions of this bug, installing a device whose job is to generate them
deliberately would be a poor trade.

### The half worth taking

The constraint half never invents anything. It only says **no**:

- *an agent may only write the kinds of records it declared it writes*
- *an edge coming off a Fill must point at an Order*

Those add zero rows. They reject bad ones at the door — completely safe in an evidence log.

The short version: **constraints are a doorman checking IDs.** A **reasoner is someone inside
adding names to the guest list** because it reckons those people probably belong. Now the list
contains people who never showed up, and no way to tell which is which.

### Why "permanently", not "not yet"

This is not a maturity call — that would be a revisit trigger (§8), and the genuine ones are
listed there. It is a direct conflict with what the graph *is*. Inference only starts making
sense if the graph stops being a record of what happened, and that is not adopting a library —
it is changing the foundation the project's credibility rests on.

---

## 1 · The claim

An agent is an LLM with tools and a loop; that makes it Turing-complete, and therefore unbounded.
Coyle's argument is that unbounded probabilistic generation needs a deterministic tether, and that
formal ontologies — W3C RDFS and OWL — are that tether. Two halves:

- **RDFS infers.** `rdfs:domain` / `rdfs:range` let a reasoner derive facts nobody stated: from
  `teaches rdfs:domain Teacher` and `Bob teaches Scooter`, derive `Bob a Teacher`.
- **OWL constrains.** `TransitiveProperty` closes chains (`Sue ancestor Mary`, `Mary ancestor Anne`
  ⇒ `Sue ancestor Anne`); `FunctionalProperty` caps cardinality at one (two `hasFather` values
  ⇒ they must be the same individual).

The pitch is neuro-symbolic: probabilistic creativity, deterministic guardrails, catching
duplicate refunds, misrouted payouts, and semantically impossible status strings.

**The detail that decides this evaluation:** Coyle does not propose ontologies *instead of* type
validators — the published summary explicitly pairs OWL/RDFS **with Pydantic**. So the question
here is not "ontology or nothing." It is: *what does the ontology layer add on top of a codebase
that already has the Pydantic half built?*

---

## 2 · What this platform already has

| Coyle's device | Already present here | Evidence |
| --- | --- | --- |
| Type validation at the boundary | **Yes, pervasively** — frozen Pydantic DTOs on every contract | `contracts/`, `kernel/config.py::tunable` |
| "Semantically impossible status string" | **Caught at load, not at use** | `OperatorSettings.effort` is a `Literal["low","medium","high","xhigh","max"]`; a bad override raises `ValidationError` on construction rather than returning a 400 mid-run |
| Provenance / lineage graph | **Yes** — append-only, `DERIVED_FROM` / `PRODUCED` / `ANALYZED` / `CONTAINS` | `kernel/graph.py`; ~36 node labels in use |
| `owl:TransitiveProperty` closure | **Yes** — hand-rolled | `GraphStore.ancestors()` / `.descendants()` |
| Rule enforcement | **Yes** — but in CI, not in the graph | agent `laws/laws.md` clauses + tests citing clause IDs; `scripts/accept.py`; the drift register |

The constraint layer exists. It lives in Python and the CI gate rather than in the store. That is
a real architectural choice, not an omission — and it means the marginal value of an ontology is
much smaller here than in the codebase Coyle is implicitly addressing.

---

## 3 · The gap the talk does find — and it is real

Grep `labels_owned` across every `.py` in the repository: **zero hits.**

Grep it across `agents/*/laws/laws.md`: **eight agents declare it** — curator, forecaster, master,
monitor, operator, reporter, researcher, supervisor. For example, `agents/curator/laws/laws.md`:

```json
"labels_owned": ["Dataset", "TrainingExample", "Predictor", "PredictorPromotion"],
"labels_read":  ["Snapshot", "TradeNarrative", "Recommendation"]
```

**An ownership ontology was already authored, and nothing reads it.** No write path checks that an
agent only creates the labels it declared; no test asserts the declaration matches reality.

This is the same failure class the repo logged three separate times on 2026-07-27 (DL-65):
`-uv run pip-audit` could not fail; the Dependabot ignore rule blocked the wrong semver level; a
`directory: "/"` pointed at a file nothing built. **A declared-but-unenforced vocabulary is the
fourth instance of "a guard can be present, documented, and still not guard."**

Secondary, same root: labels and edge types are **bare string literals at every call site**
(`merge_node("Candidate", …)`, `add_edge(scan, market, "DERIVED_FROM")`). Nothing closes the
vocabulary, so a typo does not fail — `list_nodes("Postion")` returns an empty tuple, exactly the
silent-empty shape recorded in the P6 `list_nodes` gap.

---

## 4 · What each OWL/RDFS device would actually buy here

| Device | Concrete value on this codebase | Verdict |
| --- | --- | --- |
| `rdfs:domain` / `rdfs:range` | Nothing declares that `ANALYZED` runs `Candidate → AnalystRun`, or that a `Fill` hangs off an `OrderIntent`. A misattached edge is caught only where a test happens to look. | **Worth having** — as a checked declaration, not a reasoner |
| `owl:FunctionalProperty` ("at most one") | The closest thing to a cardinality rule this system has learned is DL-60: *a position is closed by a fill, not by a decision.* Getting that wrong made four positions invisible for days and cost real money. | **Worth having** — but expressible in Python |
| `owl:TransitiveProperty` | Already served by `ancestors()` / `descendants()`. | **No gain** |
| RDFS inference (deriving unasserted facts) | See §5. | **Actively unwanted** |

---

## 5 · Where it does not pay — the decisive part

**1 · Inference fights LAW-02.** This project's governing discipline is *success is proven, never
assumed*. A reasoner does the opposite: it **asserts facts nobody observed**. In an append-only
store whose entire purpose is evidence, a derived triple is indistinguishable at read time from an
observed one unless you also record provenance for the derivation — more machinery than the
constraint is worth.

This is not hypothetical. Every expensive bug this month was *an unasserted fact treated as
fact*: a `CloseDecision` treated as evidence of closure (DL-60, four stranded positions);
`pnl_cents` computed at decision time so profit factor rested on trades that never happened
(0.74.03). **Adding a reasoner would industrialise precisely that failure mode.**

**2 · Substrate cost.** ADR-0014 put the spine on Postgres, decided *after* ripping Neo4j out in
S118. RDF/OWL means a triple store, or a reasoner over exported triples plus a sync path.
Reopening the substrate is a large reversal for a benefit largely obtainable in Python.

**3 · The headline example is already covered.** "Semantically impossible status string" is caught
today by the Pydantic half of Coyle's own recipe.

---

## 6 · Recommendation — take the constraint half, skip the reasoner

Adopt the cheap 20 %, in plain Python, **no new dependency**:

1. **Close the vocabulary.** Node labels and edge types become a declared registry, so a typo is an
   error rather than an empty result.
2. **Wire `labels_owned`.** It is already authored in eight law files. Enforce it on write: an
   agent creating a label it never declared raises. This converts eight dormant declarations into
   a live guard and closes the §3 gap directly — the highest value-per-line change on this list.
3. **Declare edge domain/range as data**, checked in `add_edge`. Roughly 30 lines.
4. **Do not add a reasoner.** No RDFS entailment, no OWL inference, no triple store.

That is "OWL constrains" without "RDFS infers" — the half that fits an evidence store.

Sequencing note: (2) is worth doing on its own merits regardless of this evaluation, because it
closes a *known* documented-but-unenforced declaration. (1) and (3) are cheap once (2) forces a
registry to exist.

---

## 7 · Ruled out

- **Triple store / RDF spine** — reverses ADR-0014 months after the Neo4j ripout.
- **OWL reasoner over exported triples** — inference conflicts with LAW-02 (§5.1); the derived-fact
  ambiguity is the exact bug class the repo has been paying for.
- **`rdflib` / `owlready2` as a dependency** — a new supply-chain surface for constraints
  expressible in ~100 lines of first-party Python.

---

## 8 · Revisit triggers

- **A second pack lands.** ADR-0012's de-facto platform test. Two packs needing a shared,
  machine-checkable vocabulary is the strongest argument for a real ontology, because the
  vocabulary stops being one team's convention.
- **Derived classification becomes load-bearing** — i.e. a query needs a category the code does not
  compute and cannot cheaply be made to.
- **An external consumer requires RDF interchange.** Same answer shape as R004 (A2A): a boundary
  adapter in `surfaces/`, not an internal rewrite.
