"""PostgreSQL SQL for the key-and-edge query (DL-246 D1-D3).

Agent: kernel
Role: keep the anti-join text that finds node keys lacking an edge out of the adapter.
External I/O: none.

Each query selects the key column only - never ``props`` - so a poll that finds no
work downloads no payload. Every value is a bound parameter:
``(label, edge_type, bound, bound)``, where ``bound`` is ``created_at_from`` rendered
as UTC ISO-8601 text or ``None``. The order is ``LIST_NODES_SQL``'s own,
``ORDER BY n.key``, so a poll meets its pending items in the order it always did.
The bound is compared byte-wise (``COLLATE "C"``, Python's ``str`` order): a
linguistic collation may ignore the ``+`` and ``.`` that order same-second stamps.
"""

from __future__ import annotations

KEYS_WITHOUT_OUTGOING_SQL = """
SELECT n.key
FROM nodes n
WHERE n.label = %s
  AND NOT EXISTS (
      SELECT 1
      FROM edges e
      WHERE e.parent_label = n.label
        AND e.parent_key = n.key
        AND e.edge_type = %s
  )
  AND (
      %s::text IS NULL
      OR (
          jsonb_typeof(n.props -> 'created_at') = 'string'
          AND (n.props ->> 'created_at') COLLATE "C" >= %s::text COLLATE "C"
      )
  )
ORDER BY n.key
"""

KEYS_WITHOUT_INCOMING_SQL = """
SELECT n.key
FROM nodes n
WHERE n.label = %s
  AND NOT EXISTS (
      SELECT 1
      FROM edges e
      WHERE e.child_label = n.label
        AND e.child_key = n.key
        AND e.edge_type = %s
  )
  AND (
      %s::text IS NULL
      OR (
          jsonb_typeof(n.props -> 'created_at') = 'string'
          AND (n.props ->> 'created_at') COLLATE "C" >= %s::text COLLATE "C"
      )
  )
ORDER BY n.key
"""
