"""Disposable live-transport lifecycle on a wholly synthetic administration port.

Agent: tooling
Role: prove D6 cleanup and subscription reporting without calling Azure.
External I/O: none.
"""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest
from scripts.debate_lanes_live import PRODUCTION_TOPICS, LiveTransport


class Administration:
    def __init__(self, *, fail_subscription=False, unreadable=False):
        self.fail_subscription = fail_subscription
        self.unreadable = unreadable
        self.changed = False
        self.fail_delete = False
        self.created = []
        self.deleted = []
        self.closed = False

    def create_topic(self, topic):
        assert topic not in PRODUCTION_TOPICS
        self.created.append(topic)

    def create_subscription(self, topic, subscription):
        assert subscription == "agent"
        if self.fail_subscription:
            raise RuntimeError("synthetic subscription creation failure")

    def get_subscription_runtime_properties(self, topic, subscription):
        assert subscription == "agent"
        if self.unreadable and topic in PRODUCTION_TOPICS:
            raise PermissionError("synthetic unreadable fleet subscription")
        return SimpleNamespace(
            active_message_count=int(self.changed and topic in PRODUCTION_TOPICS),
            dead_letter_message_count=0,
        )

    def delete_topic(self, topic):
        if self.fail_delete:
            raise RuntimeError("synthetic deletion failure")
        self.deleted.append(topic)

    def close(self):
        self.closed = True


def install_admin(monkeypatch, admin):
    monkeypatch.setenv("SERVICEBUS_CONNECTION_STRING", "synthetic-administration-only")
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRING", raising=False)
    module = ModuleType("azure.servicebus.management")
    module.ServiceBusAdministrationClient = SimpleNamespace(
        from_connection_string=lambda connection_string: admin
    )
    monkeypatch.setitem(sys.modules, "azure.servicebus.management", module)


def test_partial_creation_deletes_every_created_topic(monkeypatch):
    """DL-279 D6: subscription creation failure still deletes its created topic."""
    admin = Administration(fail_subscription=True)
    install_admin(monkeypatch, admin)
    with pytest.raises(RuntimeError, match="synthetic subscription"):
        LiveTransport()
    assert len(admin.created) == 1
    assert admin.deleted == admin.created
    assert admin.closed is True


@pytest.mark.parametrize("unreadable", [False, True])
def test_cleanup_compares_readable_fleet_counts_and_reports_unreadable(
    monkeypatch, unreadable
):
    """DL-279 D6: unreadable counts are reported without failing the clean rule."""
    admin = Administration(unreadable=unreadable)
    install_admin(monkeypatch, admin)
    transport = LiveTransport()
    assert len(set(transport.topics)) == 3
    assert transport.sb.reply_topic_suffix in transport.reply_topic
    assert transport.sb.receive_max_messages == 1
    assert set(transport.counts()) == set(transport.topics)
    teardown = transport.close()
    assert admin.deleted == admin.created
    assert admin.closed is True
    assert len(teardown) == 3
    assert all(row.endswith(": deleted") for row in teardown)
    assert transport.production_unchanged is True
    if unreadable:
        assert all("unreadable" in row for row in transport.production_before.values())
        assert all("unreadable" in row for row in transport.production_after.values())
    else:
        assert transport.production_before == transport.production_after


def test_changed_fleet_counts_and_failed_deletion_are_visible(monkeypatch):
    """DL-279 D6: fleet changes and failed teardown cannot disappear."""
    admin = Administration()
    install_admin(monkeypatch, admin)
    transport = LiveTransport(10)
    assert transport.sb.receive_max_messages == 10
    admin.changed = True
    admin.fail_delete = True
    teardown = transport.close()
    assert transport.production_unchanged is False
    assert admin.closed is True
    assert len(teardown) == 3
    assert all("NOT deleted" in row for row in teardown)
