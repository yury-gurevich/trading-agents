"""Service Bus route preparation tests.

Agent: tooling
Role: prove served request routes and deliberator reply routes are declared.
External I/O: none.
"""

from __future__ import annotations

from scripts.servicebus_prepare_routes import prepare_routes


class _Admin:
    def __init__(self) -> None:
        self.topics: list[str] = []
        self.subscriptions: list[tuple[str, str]] = []

    def create_topic(self, topic: str) -> object:
        self.topics.append(topic)
        return object()

    def create_subscription(self, topic: str, subscription: str) -> object:
        self.subscriptions.append((topic, subscription))
        return object()


def test_prepare_routes_creates_deliberator_reply_route() -> None:
    admin = _Admin()

    result = prepare_routes(
        admin,
        subscription_name="agent",
        agent_types=("deliberator-proponent",),
        reply_agent_types=("deliberator-manager",),
    )

    assert result["routes"] == [
        "deliberator-proponent.requests",
        "deliberator-manager.reply",
    ]
    assert ("deliberator-manager.reply", "agent") in admin.subscriptions
