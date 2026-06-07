"""Connector base hardening (backlog) — retry/backoff wrapper, with zero real sleep in tests."""
import urllib.error

import pytest

from data.connectors.base import with_retries, _is_retryable


def _flaky(fail_times, exc):
    state = {"n": 0}

    def t(url):
        if state["n"] < fail_times:
            state["n"] += 1
            raise exc
        return "OK"
    return t


def test_retries_then_succeeds_on_transient():
    waits = []
    exc = urllib.error.HTTPError("u", 503, "busy", {}, None)
    t = with_retries(_flaky(2, exc), retries=3, sleeper=waits.append)
    assert t("u") == "OK"
    assert waits == [0.5, 1.0]                  # exponential backoff, two retries, no real sleep


def test_permanent_error_is_not_retried():
    waits = []
    exc = urllib.error.HTTPError("u", 403, "forbidden", {}, None)
    t = with_retries(_flaky(99, exc), retries=3, sleeper=waits.append)
    with pytest.raises(urllib.error.HTTPError):
        t("u")
    assert waits == []                          # 403 is permanent → no backoff, fail fast


def test_gives_up_after_exhausting_retries():
    waits = []
    exc = urllib.error.URLError("reset")
    t = with_retries(_flaky(99, exc), retries=3, sleeper=waits.append)
    with pytest.raises(urllib.error.URLError):
        t("u")
    assert len(waits) == 2                       # tried 3 times → slept twice, then raised


def test_retryable_classification():
    assert _is_retryable(urllib.error.HTTPError("u", 429, "", {}, None))
    assert _is_retryable(urllib.error.URLError("x"))
    assert not _is_retryable(urllib.error.HTTPError("u", 404, "", {}, None))
    assert not _is_retryable(ValueError("bad parse"))
