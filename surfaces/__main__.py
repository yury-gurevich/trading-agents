"""Module entry point for the CLI surface.

Agent: surfaces
Role: delegate python -m surfaces to the CLI runner.
External I/O: stdout and optional runtime context construction.
"""

from surfaces.cli import main

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
