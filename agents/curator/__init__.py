"""Curator agent. See mission.md and contracts/curator.py.

Agent: curator
Role: out-of-band data engineering — curate Neo4j-collected data into training-
      ready datasets. Runs alongside trading; never in the decision path.
External I/O: dataset_store

Runtime (agent.py, domain/, store.py, mcp.py, tests/) lands during implementation.
Imports only `kernel` and `contracts` — never another agent.
"""
