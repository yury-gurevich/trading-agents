# Deliberator Mission

Review PM-approved live orders before execution through a bounded three-role debate:
the manager gives identical evidence to a proponent and an opponent, gathers their
turns across configured rounds, then records a verdict, rationale, and transcript.

The deliberator may only subtract from the PM-approved set. It never originates,
resizes, or executes orders, never fetches market data directly, and never hides an
LLM failure; failure is recorded and trading remains fail-open.
