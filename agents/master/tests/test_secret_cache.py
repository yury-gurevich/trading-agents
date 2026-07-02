"""CachingSecretStore — TTL cache over fetched Key Vault secrets (S105).

Agent: master
Role: verify the master caches fetched secrets for repeated references (TTL minutes,
      0 = never expires) and re-fetches a missing one.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agents.master.key_vault import CachingSecretStore


class _Counting:
    """Inner SecretStore that counts fetches and returns from a dict."""

    def __init__(self, secrets: dict[str, str]) -> None:
        self._s = secrets
        self.calls: list[str] = []

    def get_secret(self, name: str) -> str:
        self.calls.append(name)
        return self._s.get(name, "")


def test_repeated_reference_is_served_from_cache() -> None:
    inner = _Counting({"a": "v1"})
    cache = CachingSecretStore(inner, ttl_minutes=5)
    assert cache.get_secret("a") == "v1"
    assert cache.get_secret("a") == "v1"
    assert inner.calls == ["a"]  # fetched once; the second reference hit the cache


def test_cache_expires_after_ttl() -> None:
    now = [datetime(2026, 7, 1, tzinfo=UTC)]
    inner = _Counting({"a": "v1"})
    cache = CachingSecretStore(inner, ttl_minutes=5, clock=lambda: now[0])
    cache.get_secret("a")
    now[0] += timedelta(minutes=6)
    cache.get_secret("a")
    assert inner.calls == ["a", "a"]  # re-fetched after the TTL lapsed


def test_ttl_zero_never_expires() -> None:
    now = [datetime(2026, 7, 1, tzinfo=UTC)]
    inner = _Counting({"a": "v1"})
    cache = CachingSecretStore(inner, ttl_minutes=0, clock=lambda: now[0])
    cache.get_secret("a")
    now[0] += timedelta(days=365)
    assert cache.get_secret("a") == "v1"
    assert inner.calls == ["a"]  # 0 = never expires -> never re-fetched


def test_missing_secret_is_not_cached_and_is_refetched() -> None:
    inner = _Counting({})  # "a" absent -> "" (a miss)
    cache = CachingSecretStore(inner, ttl_minutes=0)
    assert cache.get_secret("a") == ""
    assert cache.get_secret("a") == ""
    assert inner.calls == ["a", "a"]  # misses are not cached, so a new secret is seen
