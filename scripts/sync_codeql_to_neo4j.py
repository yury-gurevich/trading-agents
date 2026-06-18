"""Sync CodeQL SARIF findings into the Neo4j provenance graph.

Agent: tooling
Role: ingest CodeQL SARIF output and store scan runs/findings/rules in Neo4j.
External I/O: filesystem (SARIF input) and Neo4j database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kernel import Neo4jGraphStore  # noqa: E402


@dataclass(frozen=True)
class FindingRecord:
    """Normalized view of one CodeQL finding extracted from SARIF."""

    key: str
    rule_id: str
    level: str
    message: str
    file_uri: str
    start_line: int | None
    end_line: int | None
    cwe: str | None
    security_severity: str | None
    precision: str | None


@dataclass(frozen=True)
class RuleRecord:
    """Normalized view of one CodeQL rule extracted from SARIF."""

    rule_id: str
    name: str | None
    short_description: str | None


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk and fail fast on invalid payloads."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("SARIF root must be a JSON object")
    return payload


def _message_text(result: dict[str, Any]) -> str:
    """Return the best available human-readable finding message."""
    message = result.get("message")
    if isinstance(message, dict):
        text = message.get("text") or message.get("markdown")
        if isinstance(text, str) and text.strip():
            return text.strip()
    return "CodeQL finding"


def _primary_location(result: dict[str, Any]) -> tuple[str, int | None, int | None]:
    """Extract primary file URI and line range from a SARIF result."""
    locations = result.get("locations")
    if not isinstance(locations, list) or not locations:
        return ("unknown", None, None)

    first = locations[0]
    if not isinstance(first, dict):
        return ("unknown", None, None)
    physical = first.get("physicalLocation")
    if not isinstance(physical, dict):
        return ("unknown", None, None)

    artifact = physical.get("artifactLocation")
    uri = "unknown"
    if isinstance(artifact, dict):
        raw_uri = artifact.get("uri")
        if isinstance(raw_uri, str) and raw_uri.strip():
            uri = raw_uri.strip()

    region = physical.get("region")
    if not isinstance(region, dict):
        return (uri, None, None)

    start_line = region.get("startLine")
    end_line = region.get("endLine")
    start = int(start_line) if isinstance(start_line, int) else None
    end = int(end_line) if isinstance(end_line, int) else None
    return (uri, start, end)


def _fingerprint(result: dict[str, Any], fallback_seed: str) -> str:
    """Choose stable fingerprint from SARIF partial fingerprints or content hash."""
    partial = result.get("partialFingerprints")
    if isinstance(partial, dict):
        for key in sorted(partial):
            value = partial.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return hashlib.sha256(fallback_seed.encode("utf-8")).hexdigest()


def _parse_rules(run: dict[str, Any]) -> dict[str, RuleRecord]:
    """Build a rule map keyed by rule id from a SARIF run."""
    rules: dict[str, RuleRecord] = {}
    tool = run.get("tool")
    if not isinstance(tool, dict):
        return rules
    driver = tool.get("driver")
    if not isinstance(driver, dict):
        return rules
    rule_list = driver.get("rules")
    if not isinstance(rule_list, list):
        return rules

    for raw in rule_list:
        if not isinstance(raw, dict):
            continue
        rule_id = raw.get("id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            continue
        name = raw.get("name") if isinstance(raw.get("name"), str) else None
        short_description = None
        short = raw.get("shortDescription")
        if isinstance(short, dict):
            text = short.get("text")
            if isinstance(text, str) and text.strip():
                short_description = text.strip()
        rules[rule_id] = RuleRecord(
            rule_id=rule_id,
            name=name,
            short_description=short_description,
        )
    return rules


def _extract_findings(run: dict[str, Any]) -> list[FindingRecord]:
    """Extract normalized findings from one SARIF run."""
    findings: list[FindingRecord] = []
    results = run.get("results")
    if not isinstance(results, list):
        return findings

    for result in results:
        if not isinstance(result, dict):
            continue
        rule_id_raw = result.get("ruleId")
        rule_id = rule_id_raw if isinstance(rule_id_raw, str) else "unknown"
        level_raw = result.get("level")
        level = level_raw if isinstance(level_raw, str) else "warning"
        message = _message_text(result)
        file_uri, start_line, end_line = _primary_location(result)

        properties = result.get("properties")
        cwe: str | None = None
        security_severity: str | None = None
        precision: str | None = None
        if isinstance(properties, dict):
            cwe_raw = properties.get("cwe")
            if isinstance(cwe_raw, str) and cwe_raw.strip():
                cwe = cwe_raw.strip()
            sev_raw = properties.get("security-severity")
            if isinstance(sev_raw, str) and sev_raw.strip():
                security_severity = sev_raw.strip()
            precision_raw = properties.get("precision")
            if isinstance(precision_raw, str) and precision_raw.strip():
                precision = precision_raw.strip()

        seed = f"{rule_id}|{file_uri}|{start_line}|{end_line}|{message}"
        key = _fingerprint(result, seed)
        findings.append(
            FindingRecord(
                key=key,
                rule_id=rule_id,
                level=level,
                message=message,
                file_uri=file_uri,
                start_line=start_line,
                end_line=end_line,
                cwe=cwe,
                security_severity=security_severity,
                precision=precision,
            )
        )
    return findings


def _run_key(source: str, run_id: str | None, commit_sha: str | None) -> str:
    """Build an idempotent scan-run key."""
    if run_id:
        return f"{source}:run:{run_id}"
    if commit_sha:
        return f"{source}:sha:{commit_sha}"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{source}:manual:{timestamp}"


def sync_codeql_sarif(
    *,
    sarif_path: Path,
    source: str,
    run_id: str | None,
    repo: str | None,
    commit_sha: str | None,
    ref: str | None,
) -> tuple[int, int]:
    """Sync one SARIF payload and return (run_count, finding_count)."""
    payload = _read_json(sarif_path)
    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("SARIF payload has no runs")

    graph = Neo4jGraphStore()
    try:
        synced_runs = 0
        synced_findings = 0
        root_key = _run_key(source, run_id, commit_sha)

        for index, run in enumerate(runs):
            if not isinstance(run, dict):
                continue
            run_key = f"{root_key}:{index}"
            tool_name = "CodeQL"
            tool_version: str | None = None
            tool = run.get("tool")
            if isinstance(tool, dict):
                driver = tool.get("driver")
                if isinstance(driver, dict):
                    driver_name = driver.get("name")
                    if isinstance(driver_name, str) and driver_name.strip():
                        tool_name = driver_name.strip()
                    driver_version = driver.get("semanticVersion")
                    if isinstance(driver_version, str) and driver_version.strip():
                        tool_version = driver_version.strip()

            rule_map = _parse_rules(run)
            findings = _extract_findings(run)

            scan_run = graph.merge_node(
                "CodeScanRun",
                run_key,
                {
                    "source": source,
                    "repo": repo or "unknown",
                    "commit_sha": commit_sha or "unknown",
                    "ref": ref or "unknown",
                    "tool": tool_name,
                    "tool_version": tool_version or "unknown",
                    "sarif_path": str(sarif_path),
                    "finding_count": len(findings),
                    "synced_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            )

            for finding in findings:
                finding_node = graph.merge_node(
                    "CodeQLFinding",
                    finding.key,
                    {
                        "rule_id": finding.rule_id,
                        "level": finding.level,
                        "message": finding.message,
                        "file_uri": finding.file_uri,
                        "start_line": finding.start_line,
                        "end_line": finding.end_line,
                        "cwe": finding.cwe,
                        "security_severity": finding.security_severity,
                        "precision": finding.precision,
                    },
                )
                graph.add_edge(scan_run, finding_node, "SCANNED")

                file_node = graph.merge_node(
                    "SourceFile",
                    finding.file_uri,
                    {"path": finding.file_uri},
                )
                graph.add_edge(finding_node, file_node, "AFFECTS_FILE")

                if finding.rule_id in rule_map:
                    rule = rule_map[finding.rule_id]
                    rule_node = graph.merge_node(
                        "CodeQLRule",
                        rule.rule_id,
                        {
                            "name": rule.name,
                            "short_description": rule.short_description,
                        },
                    )
                    graph.add_edge(finding_node, rule_node, "TRIGGERED_BY")

            synced_runs += 1
            synced_findings += len(findings)

        return (synced_runs, synced_findings)
    finally:
        graph.close()


def _build_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser for the SARIF sync script."""
    parser = argparse.ArgumentParser(
        description=(
            "Sync CodeQL SARIF findings into Neo4j using the kernel graph adapter."
        )
    )
    parser.add_argument(
        "--sarif",
        required=True,
        type=Path,
        help="Path to the CodeQL SARIF file (e.g. codeql-results.sarif).",
    )
    parser.add_argument(
        "--source",
        default="github-actions",
        help="Scan source identifier (default: github-actions).",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional CI run id to make scan keys stable across retries.",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Optional repo slug (owner/name) for traceability.",
    )
    parser.add_argument(
        "--commit-sha",
        default=None,
        help="Optional commit SHA associated with the scan.",
    )
    parser.add_argument(
        "--ref",
        default=None,
        help="Optional Git ref associated with the scan.",
    )
    return parser


def main() -> int:
    """Parse CLI args, sync SARIF into Neo4j, and print a compact summary."""
    parser = _build_parser()
    args = parser.parse_args()

    if not args.sarif.exists():
        parser.error(f"SARIF file does not exist: {args.sarif}")

    synced_runs, synced_findings = sync_codeql_sarif(
        sarif_path=args.sarif,
        source=str(args.source),
        run_id=str(args.run_id) if args.run_id else None,
        repo=str(args.repo) if args.repo else None,
        commit_sha=str(args.commit_sha) if args.commit_sha else None,
        ref=str(args.ref) if args.ref else None,
    )
    sys.stdout.write(
        "CodeQL sync complete: "
        f"runs={synced_runs}, findings={synced_findings}, sarif={args.sarif}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
