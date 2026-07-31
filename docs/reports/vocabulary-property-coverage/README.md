# Vocabulary property coverage — what the guard can and cannot protect

**Chore:** `chore-vocabulary-property-completeness` (0.84.03) · **Date:** 2026-07-31

Prerequisite evidence for enabling S144 (`GRAPH_VOCABULARY_B64`) on the fleet. S149 taught
`Vocabulary.check_node` to reject undeclared node **properties**, but the completeness suite proved
supersets for labels, edge types and edge signatures only. This chore adds the property dimension
and reports what it found.

---

## The headline

| Dimension | Proven a superset of what code can write? |
| --- | --- |
| Labels | 🟩 since S144 |
| Edge types | 🟩 since S144 |
| Edge signatures | 🟩 since S144 |
| **Node properties** | 🟩 **for the 2 enforced labels, as of this chore** |

`check_node` enforces properties **only** for a label that declares a property list. The pack
declares **2 of 71** — `Fill` (45) and `Recommendation` (22). For every other label the property
check is a no-op, so the guard's property dimension currently covers **2 / 71 labels**.

Both enforced labels now pass with **zero undeclared properties and zero unresolved write sites**:

| Label | Declared | Recovered | Undeclared | Blind sites |
| --- | --- | --- | --- | --- |
| `Fill` | 45 | 34 | **0** | **0** |
| `Recommendation` | 22 | 21 | **0** | **0** |

Over-declaration (a declared property the code never writes) is safe — the guard rejects only
*undeclared* properties — so the 11 `Fill` and 1 `Recommendation` declared-but-unwritten names are
recorded, not failures.

## Why "zero undeclared" was nearly worthless

Before this chore's resolver hops, `Fill` recovered **7 of 45** properties and still reported zero
undeclared ones — because `write_fills` and `_write_stop_fill` hand their props to
`select_fill_attempt`, which stores the dict on a frozen `FillAttempt` and merges it back as
`attempt.props`. The scan could not read the argument, so it found nothing and reported nothing.

That is DL-57 exactly: *"didn't look"* rendering identically to *"looked and found nothing."*
It is why `test_property_enforced_labels_have_no_unresolved_write_sites` fails on a blind site
rather than trusting an empty undeclared set. Three resolver rules closed the chain — parameter
binding, the dataclass-field passthrough, and the `dict(props)` copy idiom — taking `Fill` from
7 to 34 recovered.

## The 51 labels the guard does not protect

51 labels write properties but declare none, so the guard is inert for them. **49 of the 51 resolve
totally**, meaning their property lists could be generated safely from the scan today. Only two
carry blind sites: `RegimeContext` (`_link_regime`) and `TrainingExample` (`_write_example`).

Largest by recovered property count: `Position` 17 · `Fault` 12 · `Escalation` 11 ·
`MonitorRun` 11 · `Predictor` 11 · `CloseDecision` 10 · `OrderIntent` 10 · `RemediationAttempt` 9.

Declaring these is **not** in this chore's scope (operator decision, 2026-07-31): it converts a
static under-approximation into a runtime fail-closed rule, and that trade is its own decision with
its own evidence. The scanner that would generate them now exists.

## Named limits — what this check still cannot see

1. **Four `merge_node` sites resolve no label at all** (of 77 with a props argument).
   Three are generic wrappers that forward rather than originate props — `GuardedGraphStore`,
   the dashboard read cache, and `kernel/claim_check.py`. The fourth is a real originating writer:
   `orchestration/resume.py:106` merges under `artifact.label` from a descriptor table, so its
   resume-clone properties are attributed to **no** label. Latent today because none of the resume
   chain labels are property-enforced; it becomes live the moment one is. **Declare properties for
   any resume-chain label and this must be resolved first.**
2. **The scan is a floor, not a ceiling.** A property name computed at runtime is invisible. The
   `total` flag is the mitigation: a dynamic key makes the site unresolved rather than silently
   partial, which is why blind sites fail the gate.
3. **It proves the pack covers the code, not that the pack is right.** A wrong-but-declared
   property name still passes.

## Evidence — both checks observed failing

Per DL-70, each check was planted with a violation and watched fail before being trusted:

| Check | Planted violation | Observed |
| --- | --- | --- |
| `test_every_property_the_code_can_write_is_declared` | removed `drop_reason` from the pack's `Fill` list | **FAILED** — `undeclared properties on Fill: ['drop_reason']` |
| `test_property_enforced_labels_have_no_unresolved_write_sites` | removed the `dict()` copy rule from the resolver | **FAILED** — blind sites `_write_stop_fill`, `write_fills` returned |
| `test_the_fill_attempt_passthrough_is_resolved` | same | **FAILED** — lost `ticker`, `side`, `quantity` |
| `test_the_property_scan_detects_a_prop_no_pack_declares` | planted writer package | passes on plant, detects `planted_undeclared_prop` |
| `test_the_property_scan_reports_an_unresolvable_props_argument` | planted opaque `payload.unresolvable` | passes, reports `write` as blind |

Both real-repo negatives were reverted and the tree verified clean afterwards.

## What this unblocks

S144's fleet enablement no longer risks a `VocabularyError` on the first `Fill` or `Recommendation`
write — the two labels whose properties are enforced are now proven supersets, and any future
regression fails `make ci`. The remaining S144 decisions are unchanged and unaddressed here:
whether to declare properties for the other 51 labels, and the dated build-and-retag itself.
