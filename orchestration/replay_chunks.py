"""Split one round into batches small enough to actually reach the provider.

Agent: orchestration
Role: bound a submission by payload bytes, not by request count, and keep the
      round's answers whole across the chunks it was split into.
External I/O: none.

🪤 Measured 2026-09-05, on the first funded sweep: round 1 (2,961 requests, no
transcript yet) posted fine, and round 2 — the same 2,961 requests each now
carrying round 1's ~1,873-character answer — died with `APIConnectionError` on a
single ~74 MB POST. The Batch API's documented ceilings (100k requests, 256 MB)
were both far away; what failed was one HTTP upload, not a quota. So the chunk
size cannot be a request count fixed in advance: a judge-round request is several
times the size of a first-defender request, and the same count that works for one
round is what kills the other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from orchestration.replay_types import BatchRequest

__all__ = ["DEFAULT_CHUNK_BYTES", "chunk_by_bytes", "request_bytes"]

# Comfortably under the measured failure and well under the documented 256 MB, so
# a chunk is never the thing being tested.
DEFAULT_CHUNK_BYTES = 12_000_000
_MAX_CHUNK_REQUESTS = 1_000


def request_bytes(request: BatchRequest) -> int:
    """The wire cost of one request, near enough for splitting."""
    return len(request.system.encode("utf-8")) + len(request.user.encode("utf-8"))


def chunk_by_bytes(
    requests: Sequence[BatchRequest],
    *,
    max_bytes: int = DEFAULT_CHUNK_BYTES,
    max_requests: int = _MAX_CHUNK_REQUESTS,
) -> tuple[tuple[BatchRequest, ...], ...]:
    """Split a round into submittable chunks, losing and duplicating nothing.

    A single request larger than ``max_bytes`` still gets its own chunk rather
    than being dropped: refusing to send it would silently shrink the sample,
    which is the failure this whole sprint exists to make impossible.
    """
    chunks: list[tuple[BatchRequest, ...]] = []
    current: list[BatchRequest] = []
    size = 0
    for request in requests:
        cost = request_bytes(request)
        too_big = current and (size + cost > max_bytes or len(current) >= max_requests)
        if too_big:
            chunks.append(tuple(current))
            current, size = [], 0
        current.append(request)
        size += cost
    if current:
        chunks.append(tuple(current))
    return tuple(chunks)
