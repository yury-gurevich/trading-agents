"""Tag proof across rerun attempts of one successful image build.

Agent: surfaces
Role: prove every attempt is evidence, searched in order and only as needed.
External I/O: none; GitHub reads and deploy writes use in-memory fakes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from email.message import Message
from urllib.error import HTTPError

import pytest

from kernel import InMemoryGraphStore
from orchestration.deploy_record import record_verified_deploy
from surfaces.dashboard.github_builds import GitHubReadError
from surfaces.dashboard.github_tag_builds import run_log_mentions_tag
from surfaces.tests.github_build_attempts_helpers import (
    BUILD,
    MISSING,
    OTHER_LOG,
    SHA,
    TAG_LOG,
    AttemptGitHub,
)


def test_t1_earlier_attempt_proves_tag_and_records_deploy() -> None:
    """SRF-DEP-04: earlier complete-tag evidence proves and records the build."""
    github = AttemptGitHub({1: TAG_LOG, 2: OTHER_LOG}, count=2)
    assert github.reader.image_builds_for_tag("s259", SHA) == (BUILD,)
    assert github.archives == ["logs", "attempts/1/logs"]

    github.archives.clear()
    graph = InMemoryGraphStore()
    record = record_verified_deploy(
        graph,
        tag="s259",
        git_sha=SHA,
        actor="operator",
        build_reader=github.reader,
        deployed_at=datetime(2026, 10, 11, tzinfo=UTC),
    )
    assert record.props["tag"] == "s259"
    assert record.props["git_sha"] == SHA
    assert graph.list_nodes("DeployRecord") == (record,)
    assert github.archives == ["logs", "attempts/1/logs"]


def test_t3_no_attempt_names_tag_reads_all_newest_first() -> None:
    """SRF-DEP-04: absent tag evidence requires every archive newest first."""
    github = AttemptGitHub({1: OTHER_LOG, 2: OTHER_LOG, 3: OTHER_LOG}, count=3)
    assert github.reader.image_builds_for_tag("s259", SHA) == ()
    assert github.archives == ["logs", "attempts/2/logs", "attempts/1/logs"]


@pytest.mark.parametrize("tag_attempt", [3, 2])
def test_t2_stops_at_first_matching_attempt(tag_attempt: int) -> None:
    """SRF-DEP-04: latest first, never request any archive after a match."""
    github = AttemptGitHub(
        {1: AssertionError("must not read first"), 2: TAG_LOG, 3: OTHER_LOG},
        count=3,
    )
    if tag_attempt == 3:
        github.payloads["logs"] = TAG_LOG
    assert github.reader.image_builds_for_tag("s259", SHA) == (BUILD,)
    expected = ["logs"] if tag_attempt == 3 else ["logs", "attempts/2/logs"]
    assert github.archives == expected


@pytest.mark.parametrize("count", [1, MISSING])
def test_t4_one_or_omitted_attempt_count_reads_latest_once(count: object) -> None:
    """SRF-DEP-04: explicit and omitted one-attempt rows use the legacy path."""
    github = AttemptGitHub({1: OTHER_LOG}, count=count)
    assert github.reader.image_builds_for_tag("s259", SHA) == ()
    assert github.archives == ["logs"]
    github.archives.clear()
    assert not run_log_mentions_tag(github.reader, 7, "s259")
    assert github.archives == ["logs"]


def test_t5_earlier_attempt_requires_the_complete_tag() -> None:
    """SRF-DEP-04: a longer earlier tag cannot prove the requested prefix."""
    github = AttemptGitHub({1: TAG_LOG + "a", 2: OTHER_LOG}, count=2)
    assert github.reader.image_builds_for_tag("s259", SHA) == ()
    assert github.archives == ["logs", "attempts/1/logs"]
    github.archives.clear()
    assert github.reader.image_builds_for_tag("s259a", SHA) == (BUILD,)
    assert github.archives == ["logs", "attempts/1/logs"]


@pytest.mark.parametrize(
    ("archive", "message"),
    [
        (
            HTTPError("https://example.invalid", 404, "missing", Message(), None),
            "GitHub build read failed (404)",
        ),
        (b"not a zip", "GitHub build log response was incomplete"),
    ],
)
def test_t6_unreadable_earlier_archive_is_a_sanitised_error(
    archive: bytes | Exception, message: str
) -> None:
    """SRF-DEP-04 / SRF-SEC-02: unreadable earlier evidence is never absent."""
    github = AttemptGitHub({1: archive, 2: OTHER_LOG}, count=2)
    with pytest.raises(GitHubReadError) as caught:
        github.reader.image_builds_for_tag("s259", SHA)
    assert str(caught.value) == message
    assert "example.invalid" not in str(caught.value)
    assert "api.github.com" not in str(caught.value)
    assert github.archives == ["logs", "attempts/1/logs"]


@pytest.mark.parametrize("count", [0, -1, "2", True, None, 2.0])
def test_t7_invalid_attempt_count_refuses_before_log_reads(count: object) -> None:
    """SRF-DEP-04: only a positive integer attempt count permits a log read."""
    github = AttemptGitHub({1: TAG_LOG, 2: TAG_LOG}, count=count)
    with pytest.raises(
        GitHubReadError, match=r"^GitHub build response was incomplete$"
    ):
        github.reader.image_builds_for_tag("s259", SHA)
    assert github.archives == []


def test_t8_off_main_run_is_rejected_before_any_archive_read() -> None:
    """SRF-DEP-04: earlier tag evidence cannot admit a commit ahead of main."""
    github = AttemptGitHub(
        {1: TAG_LOG, 2: OTHER_LOG}, count=2, branch="release", ahead_by=1
    )
    assert github.reader.image_builds_for_tag("s259", SHA) == ()
    assert github.archives == []
    assert github.urls[-1].endswith(f"/compare/main...{SHA}")
