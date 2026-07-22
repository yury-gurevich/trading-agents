"""Route helpers for the controlled Service Bus SAS live check.

Agent: tooling
Role: create/delete canary topics, subscriptions, and SAS rules.
External I/O: Azure CLI; prints no keys or connection strings.
"""

from __future__ import annotations

from scripts.sb_sas_cli import az_cli, base_args

REQUESTER_RULE = "s133-requester"
SERVED_RULE = "s133-served"
WORKER_SUBSCRIPTION = "worker"
PROBE_SUBSCRIPTION = "probe"


def create_canary_routes(
    resource_group: str, namespace_name: str, request_topic: str, reply_topic: str
) -> list[str]:
    """Create disposable request/reply topics and scoped Send/Listen rules."""
    for topic in (request_topic, reply_topic):
        topic_command("create", resource_group, namespace_name, topic)
    subscription(resource_group, namespace_name, request_topic, WORKER_SUBSCRIPTION)
    subscription(resource_group, namespace_name, reply_topic, PROBE_SUBSCRIPTION)
    rule(resource_group, namespace_name, request_topic, REQUESTER_RULE, ("Send",))
    rule(resource_group, namespace_name, request_topic, SERVED_RULE, ("Listen",))
    rule(resource_group, namespace_name, reply_topic, REQUESTER_RULE, ("Listen",))
    rule(resource_group, namespace_name, reply_topic, SERVED_RULE, ("Send",))
    return [request_topic, reply_topic]


def connection_string(
    resource_group: str, namespace_name: str, topic: str, rule_name: str
) -> str:
    """Return one scoped connection string without writing it to stdout."""
    return az_cli(
        [
            "servicebus",
            "topic",
            "authorization-rule",
            "keys",
            "list",
            *base_args(resource_group, namespace_name),
            "--topic-name",
            topic,
            "--name",
            rule_name,
            "--query",
            "primaryConnectionString",
            "-o",
            "tsv",
        ],
        capture=True,
    ).strip()


def topic_command(
    command: str, resource_group: str, namespace_name: str, topic: str
) -> None:
    """Run a Service Bus topic command, ignoring absent canary deletes."""
    az_cli(
        [
            "servicebus",
            "topic",
            command,
            *base_args(resource_group, namespace_name),
            "--name",
            topic,
            "-o",
            "none",
        ],
        check=False,
    )


def subscription(
    resource_group: str, namespace_name: str, topic: str, subscription_name: str
) -> None:
    """Create one canary subscription."""
    az_cli(
        [
            "servicebus",
            "topic",
            "subscription",
            "create",
            *base_args(resource_group, namespace_name),
            "--topic-name",
            topic,
            "--name",
            subscription_name,
            "-o",
            "none",
        ]
    )


def rule(
    resource_group: str,
    namespace_name: str,
    topic: str,
    rule_name: str,
    rights: tuple[str, ...],
) -> None:
    """Create one scoped authorization rule."""
    az_cli(
        [
            "servicebus",
            "topic",
            "authorization-rule",
            "create",
            *base_args(resource_group, namespace_name),
            "--topic-name",
            topic,
            "--name",
            rule_name,
            "--rights",
            *rights,
            "-o",
            "none",
        ]
    )


def delete_rule(
    resource_group: str, namespace_name: str, topic: str, rule_name: str
) -> None:
    """Delete one scoped authorization rule."""
    az_cli(
        [
            "servicebus",
            "topic",
            "authorization-rule",
            "delete",
            *base_args(resource_group, namespace_name),
            "--topic-name",
            topic,
            "--name",
            rule_name,
        ]
    )
