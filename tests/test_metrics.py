"""
Unit tests for the anonymous usage metrics (infrastructure/metrics.py).

Nothing here touches the network: each test gives the client a fake sender
that just records the batches it would have posted.
"""

import json
import os

import pytest

from infrastructure import metrics
from infrastructure.metrics import _Metrics, pid_detail, scrub_reason


@pytest.fixture(autouse=True)
def user_dir(tmp_path, monkeypatch):
    """Point the per-user data dir at a tmp folder (APPDATA on Windows,
    XDG_CONFIG_HOME elsewhere) so no test writes a real metrics.json."""
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    return tmp_path


class FakeSender:
    def __init__(self, fail=False):
        self.batches = []
        self.fail = fail

    def __call__(self, payload, timeout):
        self.batches.append(payload)
        if self.fail:
            raise ConnectionError("offline")


def client(sender=None, enabled=True):
    return _Metrics(sender=sender or FakeSender(), enabled=enabled)


# ----------------------------------------------------------------------
# When it sends at all
# ----------------------------------------------------------------------
def test_a_dev_run_sends_nothing(monkeypatch):
    monkeypatch.delenv(metrics.FORCE_ENV, raising=False)
    monkeypatch.delattr("sys.frozen", raising=False)
    sender = FakeSender()
    m = _Metrics(sender=sender)
    assert not m.enabled()
    m.track("app_open")
    m.flush_on_exit()
    assert sender.batches == []


def test_the_built_app_sends(monkeypatch):
    monkeypatch.delenv(metrics.FORCE_ENV, raising=False)
    monkeypatch.setattr("sys.frozen", True, raising=False)
    assert _Metrics(sender=FakeSender()).enabled()


def test_the_force_switch_sends_from_a_dev_run(monkeypatch):
    monkeypatch.delattr("sys.frozen", raising=False)
    monkeypatch.setenv(metrics.FORCE_ENV, "1")
    assert _Metrics(sender=FakeSender()).enabled()


# ----------------------------------------------------------------------
# What a batch looks like
# ----------------------------------------------------------------------
def test_a_batch_has_the_web_apps_shape_under_the_desktop_site_name():
    sender = FakeSender()
    m = client(sender)
    m.track("quick_chart", action_id="V2_TURBO", detail={"type": "ECU_V2"})
    m.track("app_open")
    m.flush_on_exit()

    [batch] = sender.batches
    assert batch["site"] == "snapshot-desktop"
    assert batch["visitor"] and batch["session"]
    assert batch["events"] == [
        {"event": "quick_chart", "action_id": "V2_TURBO", "detail": {"type": "ECU_V2"}},
        {"event": "app_open"},
    ]


def test_an_unknown_event_is_never_queued():
    sender = FakeSender()
    m = client(sender)
    m.track("keystrokes", detail={"text": "secret"})
    m.flush_on_exit()
    assert sender.batches == []


def test_the_event_list_matches_the_collector():
    """The collector drops what it doesn't know, so the lists must agree.
    Mirror of ALLOWED_EVENTS in rudi-ops/rudi-metrics/app.py."""
    assert metrics.ALLOWED_EVENTS == {
        "app_open", "snapshot_opened", "snapshot_failed", "quick_chart",
        "my_chart", "custom_chart", "my_chart_saved", "chart_to_cart",
        "pdf_exported", "subplots_toggled", "data_table_viewed",
        "parse_timing", "client_error",
    }


# ----------------------------------------------------------------------
# Batching
# ----------------------------------------------------------------------
def test_a_full_queue_sends_straight_away(monkeypatch):
    sent = []
    m = client()
    # Run the background send inline so the test can see it.
    monkeypatch.setattr(m, "_send", lambda events, timeout: sent.append(events))
    for _ in range(metrics.MAX_QUEUE):
        m.track("custom_chart")
    assert len(sent) == 1 and len(sent[0]) == metrics.MAX_QUEUE


def test_a_part_full_queue_waits_for_the_timer():
    m = client()
    m.track("app_open")
    assert m._timer is not None and m._timer.is_alive()
    assert len(m._queue) == 1
    m.flush_on_exit()
    assert m._timer is None and m._queue == []


def test_a_failed_send_is_swallowed_and_not_retried():
    sender = FakeSender(fail=True)
    m = client(sender)
    m.track("app_open")
    m.flush_on_exit()  # must not raise
    m.flush_on_exit()
    assert len(sender.batches) == 1


def test_the_module_level_track_never_raises(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("bug")

    monkeypatch.setattr(metrics._metrics, "track", boom)
    metrics.track("app_open")


# ----------------------------------------------------------------------
# The install id
# ----------------------------------------------------------------------
def test_the_install_id_survives_a_restart():
    first = client().visitor()
    assert client().visitor() == first


def test_a_corrupt_id_file_gets_a_fresh_id():
    from domain.user_paths import user_data_file

    path = user_data_file(metrics.ID_FILE)
    with open(path, "w", encoding="utf-8") as f:
        f.write("{not json")
    fresh = client().visitor()
    assert fresh
    with open(path, encoding="utf-8") as f:
        assert json.load(f) == {"visitor": fresh}
    assert os.path.exists(path + ".bak")


def test_each_launch_is_a_new_session():
    assert client()._session != client()._session


# ----------------------------------------------------------------------
# Keeping file names out
# ----------------------------------------------------------------------
@pytest.mark.parametrize("message", [
    "[Errno 2] No such file or directory: 'C:\\\\Users\\\\tech\\\\Desktop\\\\Acme Excavating T770.xlsx'",
    "Could not read Acme Excavating T770.xlsx: bad header",
    "Acme Excavating T770 is not a snapshot",
])
def test_a_load_error_loses_the_file_name(message):
    path = "C:\\Users\\tech\\Desktop\\Acme Excavating T770.xlsx"
    scrubbed = scrub_reason(message, path)
    assert "Acme" not in scrubbed
    assert "tech" not in scrubbed


def test_a_path_is_removed_even_when_it_isnt_the_files():
    scrubbed = scrub_reason("Permission denied: 'D:\\Shop\\Customers\\job.xlsx'")
    assert "Customers" not in scrubbed and "<path>" in scrubbed


def test_a_pipeline_message_is_kept_and_capped():
    assert scrub_reason("Missing header row", "C:\\x\\snap.xlsx") == "Missing header row"
    assert len(scrub_reason("x" * 500)) == metrics.MAX_REASON


def test_pids_are_capped_like_the_web():
    detail = pid_detail([f"P{i}" for i in range(40)], ["S1"])
    assert len(detail["primary"]) == metrics.MAX_PIDS
    assert detail["secondary"] == ["S1"]
