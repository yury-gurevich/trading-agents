"""Orchestration — the dispatcher and distributed-bus app.

Routes messages and triggers runs; makes no trading decisions. Lands in build
phase P4 (see docs/build-plan.md). May depend on kernel and contracts only.
"""
