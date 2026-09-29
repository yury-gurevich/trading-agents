"""The agent's EHLO budget and master's replay window agree (S244, DL-249 D1/D3).

Agent: master
Role: prove the kernel's resend budget fits inside master's replay lifetime, the
      listen backlog holds a whole activation wave, and the lifetime is capped by
      the credential TTLs.
External I/O: reads orchestration/packs/trading_grants.json.
"""

from __future__ import annotations

from agents.master.activation_replay import replay_lifetime_seconds
from agents.master.settings import MasterSettings
from agents.master.tests.helpers import trading_policy
from kernel.ehlo_settings import EhloSettings


def test_the_kernel_budget_fits_inside_the_replay_window() -> None:
    """MST-IDM-03 / MST-TRG-01: every resend of one boot lands inside the replay.

    C10 — the default EHLO budget is <= the default replay lifetime, and the
    worst case of the default envelope (every attempt a full timeout, every
    backoff at its ceiling) is <= the budget.
    """
    ehlo = EhloSettings()
    lifetime = replay_lifetime_seconds(MasterSettings())
    worst = ehlo.ehlo_max_attempts * ehlo.ehlo_attempt_timeout_seconds + sum(
        min(ehlo.ehlo_backoff_cap_seconds, ehlo.ehlo_backoff_base_seconds * 2**n)
        for n in range(ehlo.ehlo_max_attempts - 1)
    )

    assert ehlo.ehlo_budget_seconds <= lifetime == 300.0
    assert worst == 211.0 <= ehlo.ehlo_budget_seconds


def test_the_listen_backlog_holds_one_wave() -> None:
    """MST-ORD-03: the default backlog holds every agent type waking at once.

    C10 — one wave is the grant policy's agent types (15 today).
    """
    assert MasterSettings().ehlo_listen_backlog >= len(trading_policy()) == 15


def test_the_replay_never_outlives_a_credential_pass_or_a_cached_secret() -> None:
    """MST-IDM-03 / MST-NEV-06: the lifetime is the smallest non-zero bound."""
    assert (
        replay_lifetime_seconds(MasterSettings(credential_pass_cache_ttl_minutes=2))
        == 120.0
    )
    assert replay_lifetime_seconds(MasterSettings(secret_cache_ttl_minutes=1)) == 60.0
    never = MasterSettings(
        credential_pass_cache_ttl_minutes=0, secret_cache_ttl_minutes=0
    )
    assert replay_lifetime_seconds(never) == 300.0
