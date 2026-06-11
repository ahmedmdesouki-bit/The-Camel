"""
S17 — OFAC SDN sanctions screen + its guard on the Sharia universe seed. Injected transport, no live web.
"""
from sharia.sanctions import normalize, parse_sdn, refresh_sanctions, is_sanctioned
from sharia.universe import seed_universe
from sharia.whitelist import load_whitelist


def test_normalize():
    assert normalize("Acme, Inc.") == "ACME INC"
    assert normalize("  ") == ""


def test_parse_sdn_positional_drops_nulls():
    raw = '1,"ACME WEAPONS LLC","entity","UKRAINE"\n2,"-0-","-0-","-0-"\n3,"BAD ACTOR","individual","IRAN"\n'
    assert [r["name"] for r in parse_sdn(raw)] == ["ACME WEAPONS LLC", "BAD ACTOR"]


def test_refresh_and_is_sanctioned(dbs):
    raw = '1,"ACME WEAPONS LLC","entity","PROG"\n2,"BAD ACTOR","individual","PROG"\n'
    assert refresh_sanctions(dbs, transport=lambda u: raw) == 2
    assert is_sanctioned(dbs, "Acme Weapons, LLC")          # normalized match
    assert is_sanctioned(dbs, "bad actor")
    assert not is_sanctioned(dbs, "Innocent Corp")
    assert not is_sanctioned(dbs, "")                       # empty name is never a positive


def test_refresh_is_a_snapshot_not_append(dbs):
    refresh_sanctions(dbs, transport=lambda u: '1,"OLD BADCO","entity","P"\n')
    refresh_sanctions(dbs, transport=lambda u: '1,"NEW BADCO","entity","P"\n')
    assert is_sanctioned(dbs, "New Badco") and not is_sanctioned(dbs, "Old Badco")


def test_seed_universe_refuses_a_sanctioned_name(dbs):
    refresh_sanctions(dbs, transport=lambda u: '1,"EVIL CORP","entity","PROG"\n')
    res = seed_universe(dbs, "Chiko", symbols={"EVL": "etf"}, names={"EVL": "Evil Corp"})
    assert "REFUSED" in res["EVL"]
    assert "EVL" not in load_whitelist(dbs.sharia)          # never entered the tradeable universe


def test_seed_universe_admits_a_clean_name(dbs):
    refresh_sanctions(dbs, transport=lambda u: '1,"EVIL CORP","entity","PROG"\n')
    res = seed_universe(dbs, "Chiko", symbols={"SPUS": "etf"}, names={"SPUS": "SP Funds S&P 500 ETF"})
    assert "added" in res["SPUS"] and "SPUS" in load_whitelist(dbs.sharia)
