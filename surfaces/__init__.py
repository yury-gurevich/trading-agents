"""Surfaces — consumers, not agents: dashboard and CLI.

Read the system through read-models and drive it only through the operator's
bounded commands. Lands in build phase P6 (see docs/build-plan.md).
"""

from surfaces.context import SurfaceContext, paper_context, test_context

__all__ = ["SurfaceContext", "paper_context", "test_context"]
