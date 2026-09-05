"""Replay recorded debates through the Message Batches API.

Agent: tooling
Role: submit one batch per debate round, cache every paid answer to disk, and
      write the resulting verdicts out for the metrics to read.
External I/O: Anthropic Batches API; reads the graph; writes only to --out.

Spending discipline: a batch costs real money and its results expire in 29 days.
Every round's answers are written to --out *before* the next round is planned, and
a round whose file already exists is replayed from disk instead of resubmitted, so
an interrupted sweep is never paid for twice.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:  # pragma: no cover - import-path shim
    sys.path.insert(0, str(_ROOT))

from orchestration.replay_batch import replay_debates  # noqa: E402
from orchestration.replay_chunks import chunk_by_bytes  # noqa: E402
from orchestration.replay_corpus import build_corpus  # noqa: E402
from orchestration.replay_types import Arm, BatchRequest, BatchResult  # noqa: E402

ARMS = {
    "control": Arm("control", "claude-opus-5", "high", 2),
    "effort": Arm("effort", "claude-opus-5", "medium", 2),
    "rounds": Arm("rounds", "claude-opus-5", "high", 1),
}
_POLL_SECONDS = 30
_CREATE_ATTEMPTS = 4


class AnthropicBatchGateway:
    """Submit one round as a batch, wait for it, and return its answers."""

    def __init__(self, out_dir: Path, *, api_key: str, dry_run: bool) -> None:
        """Build the gateway; a dry run plans and prices without submitting."""
        self._out = out_dir
        self._dry_run = dry_run
        self._round = 0
        self._client = None
        if not dry_run:
            import anthropic

            self._client = anthropic.Anthropic(api_key=api_key)

    def run(self, requests: list[BatchRequest]) -> tuple[BatchResult, ...]:
        """Return one answer per request, from cache when the round was paid for."""
        self._round += 1
        cached = self._out / f"round-{self._round:02d}.json"
        if cached.exists():
            print(f"round {self._round}: reusing {cached.name}", flush=True)
            return _load(cached)
        if self._dry_run:
            return tuple(
                BatchResult(request.custom_id, "succeeded", '{"ruling": "uphold"}')
                for request in requests
            )
        results = self._submit(requests)
        cached.write_text(
            json.dumps([asdict(result) for result in results], indent=2),
            encoding="utf-8",
        )
        return results

    def _submit(self, requests: list[BatchRequest]) -> tuple[BatchResult, ...]:
        """Submit the round as byte-bounded chunks, then wait for all of them.

        Every chunk is created before any is polled, because batches run in
        parallel server-side: submitting serially would multiply the wall clock
        by the number of chunks for no benefit.
        """
        chunks = chunk_by_bytes(requests)
        print(f"round {self._round}: {len(requests)} requests in {len(chunks)} chunks")
        ids = [self._create(chunk, index) for index, chunk in enumerate(chunks, 1)]
        results: list[BatchResult] = []
        for index, batch_id in enumerate(ids, 1):
            results.extend(self._collect(batch_id, index, len(ids)))
        return tuple(results)

    def _create(self, chunk: tuple[BatchRequest, ...], index: int) -> str:
        assert self._client is not None
        payload = [_wire(request) for request in chunk]
        for attempt in range(1, _CREATE_ATTEMPTS + 1):
            try:
                batch = self._client.messages.batches.create(requests=payload)
            except Exception as exc:
                if attempt == _CREATE_ATTEMPTS:
                    raise
                wait = _POLL_SECONDS * attempt
                print(f"  chunk {index}: create failed ({exc}); retrying in {wait}s")
                time.sleep(wait)
            else:
                print(f"  chunk {index}: {batch.id}, {len(chunk)} requests")
                return str(batch.id)
        raise RuntimeError("unreachable")

    def _collect(self, batch_id: str, index: int, total: int) -> list[BatchResult]:
        assert self._client is not None
        while True:
            batch = self._client.messages.batches.retrieve(batch_id)
            if batch.processing_status == "ended":
                break
            time.sleep(_POLL_SECONDS)
        found = [
            _result(entry) for entry in self._client.messages.batches.results(batch_id)
        ]
        print(f"  chunk {index}/{total} ended: {len(found)} results")
        return found


def _wire(request: BatchRequest) -> dict[str, object]:
    return {
        "custom_id": request.custom_id,
        "params": {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "output_config": {"effort": request.effort},
            "system": request.system,
            "messages": [{"role": "user", "content": request.user}],
        },
    }


def _result(entry: object) -> BatchResult:
    outcome = entry.result  # type: ignore[attr-defined]
    if outcome.type != "succeeded":
        return BatchResult(entry.custom_id, outcome.type)  # type: ignore[attr-defined]
    text = "\n".join(
        block.text for block in outcome.message.content if block.type == "text"
    )
    return BatchResult(entry.custom_id, "succeeded", text)  # type: ignore[attr-defined]


def _load(path: Path) -> tuple[BatchResult, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(BatchResult(**entry) for entry in raw)


def main(argv: list[str] | None = None) -> int:
    """Replay the selected corpus through the selected arms."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="directory for paid answers")
    parser.add_argument("--arm", action="append", default=[], choices=sorted(ARMS))
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0, help="cap subjects; 0 = all")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env

    load_dotenv(Path(args.env_file), override=False)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    corpus = build_corpus(build_graph_from_env(), run_ids=tuple(args.run_id))
    subjects = corpus.subjects[: args.limit] if args.limit else corpus.subjects
    arms = [ARMS[name] for name in (args.arm or ["control"])]
    print(f"{corpus.detail()}; replaying={len(subjects)}; arms={len(arms)}")

    gateway = AnthropicBatchGateway(
        out, api_key=os.environ.get("ANTHROPIC_API_KEY", ""), dry_run=args.dry_run
    )
    outcome = replay_debates(
        subjects,
        arms,
        args.repeats,
        gateway,
        on_round=lambda step, count: print(f"planning {step}: {count} requests"),
    )
    (out / "verdicts.json").write_text(
        json.dumps(_verdicts(outcome), indent=2), encoding="utf-8"
    )
    print(
        f"requests={outcome.requests_submitted}; completed={len(outcome.completed())}; "
        f"failed={len(outcome.failures())}"
    )
    return 0


def _verdicts(outcome: object) -> list[dict[str, object]]:
    return [
        {
            "pm_run": state.subject.pm_run,
            "ticker": state.subject.ticker,
            "repeat": state.repeat,
            "arm": state.arm.name,
            "ruling": state.verdict.ruling if state.verdict else None,
            "failure": state.failure,
        }
        for state in outcome.states  # type: ignore[attr-defined]
    ]


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
