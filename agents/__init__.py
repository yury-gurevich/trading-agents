"""The trading system. All domain logic lives under here, one agent per package.

Each agent imports only `kernel` (plumbing) and `contracts` (shared vocabulary) —
never another agent. `.importlinter` enforces this.
"""
