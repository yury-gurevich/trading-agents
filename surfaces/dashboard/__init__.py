"""Operations dashboard surface (DL-47) — read-model API + static frontend.

Agent: surfaces
Role: package marker; exposes the WSGI app factory.
External I/O: none.
"""

from surfaces.dashboard.app import build_app

__all__ = ["build_app"]
