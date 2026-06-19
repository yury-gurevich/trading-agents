"""List error-level CodeQL findings from the local SARIF.

These are the findings that would fail CI when fail-on: error is set.
Prints nothing and exits 0 when the codebase is clean.
Prints a table and exits 1 when error-level findings exist.

Usage:
    python scripts/codeql_errors.py
    python scripts/codeql_errors.py --sarif path/to/custom.sarif
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SARIF = ROOT / ".codeql-db" / "python-security-and-quality.sarif"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sarif",
        type=Path,
        default=DEFAULT_SARIF,
        help="SARIF file to scan (default: .codeql-db/python-security-and-quality.sarif)",
    )
    args = parser.parse_args()

    if not args.sarif.exists():
        print(f"SARIF not found: {args.sarif}", file=sys.stderr)
        print("Run: powershell -ExecutionPolicy Bypass -File scripts/setup_codeql_local.ps1")
        return 1

    data = json.loads(args.sarif.read_text(encoding="utf-8-sig"))

    errors: list[dict[str, object]] = []
    for run in data.get("runs", []):
        for result in run.get("results", []):
            level = result.get("level", "warning")
            props = result.get("properties") or {}
            sec_sev = props.get("security-severity")
            # error level OR has a CVSS security-severity score
            if level == "error" or sec_sev:
                locs = result.get("locations") or [{}]
                phys = locs[0].get("physicalLocation", {})
                uri = phys.get("artifactLocation", {}).get("uri", "unknown")
                region = phys.get("region", {})
                line = region.get("startLine", "?")
                msg_raw = result.get("message", {})
                msg = (
                    msg_raw.get("text", "")
                    if isinstance(msg_raw, dict)
                    else str(msg_raw)
                )
                errors.append(
                    {
                        "rule": result.get("ruleId", "?"),
                        "level": level,
                        "sec_sev": sec_sev or "-",
                        "file": uri,
                        "line": line,
                        "message": msg[:120],
                    }
                )

    if not errors:
        print("No error-level findings — CI would pass green.")
        return 0

    print(f"\n{'RULE':<40} {'SEV':<5} {'FILE'}:{{'LINE'}}")
    print("-" * 100)
    for e in sorted(errors, key=lambda x: (str(x["sec_sev"]), str(x["rule"]), str(x["file"]))):
        print(
            f"{str(e['rule']):<40} {str(e['sec_sev']):<5}  "
            f"{e['file']}:{e['line']}"
        )
        print(f"  {e['message']}")
    print(f"\n{len(errors)} error-level finding(s) — CI would FAIL.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
