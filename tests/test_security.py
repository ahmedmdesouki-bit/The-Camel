"""
S4 — security: source allowlist + quorum.
"""
from security.source_allowlist import is_allowed, has_quorum, retrieved_record


def test_allowed_host():
    assert is_allowed("https://capitaltrades.com/politicians")
    assert is_allowed("https://data.alpaca.markets/v2/bars")

def test_subdomain_allowed():
    assert is_allowed("https://api.alpaca.markets/v2")  # subdomain of alpaca.markets

def test_unlisted_host_rejected():
    assert not is_allowed("https://random-blog.example.com/hot-tip")

def test_bare_host_allowed():
    assert is_allowed("sec.gov")

def test_quorum_met_with_two_distinct_allowed():
    assert has_quorum(["https://capitaltrades.com/x", "https://sec.gov/y"])

def test_quorum_not_met_single_source():
    assert not has_quorum(["https://capitaltrades.com/x"])

def test_quorum_ignores_unlisted_and_duplicates():
    # one allowed + one unlisted + duplicate of the allowed = 1 distinct allowed → no quorum
    assert not has_quorum([
        "https://capitaltrades.com/x",
        "https://random.example.com/y",
        "https://capitaltrades.com/z",
    ])

def test_retrieved_record_marks_allowed():
    rec = retrieved_record("https://sec.gov/filing", "abc123")
    assert rec["allowed"] and rec["host"] == "sec.gov" and rec["content_hash"] == "abc123"

def test_retrieved_record_marks_unlisted():
    rec = retrieved_record("https://evil.example.com/x", "deadbeef")
    assert not rec["allowed"]
