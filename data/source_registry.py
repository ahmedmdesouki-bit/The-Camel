"""
Source registry (S8) — every data source declared with its capabilities and constraints.

A connector cannot be decision-grade unless its source is registered here with an explicit
`allowed_for_decisioning` flag, a reliability tier, and whether it needs a cross-check. This is the
catalogue the Opportunity Router / Edge Proof consult before trusting a fact.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    source_name: str
    source_type: str            # macro | fundamentals | news | market | sharia | alt
    base_url: str
    requires_api_key: bool = False
    allowed_for_decisioning: bool = True
    requires_cross_check: bool = False
    rate_limit_per_min: int = 60
    reliability_tier: int = 1    # 1 = official/best, higher = less reliable
    is_paid: bool = False


_REGISTRY: Dict[str, SourceSpec] = {}


def register(spec: SourceSpec) -> SourceSpec:
    _REGISTRY[spec.source_id] = spec
    return spec


def get(source_id: str) -> SourceSpec:
    return _REGISTRY[source_id]


def all_specs() -> List[SourceSpec]:
    return list(_REGISTRY.values())


def is_registered(source_id: str) -> bool:
    return source_id in _REGISTRY


# ---- the first official/free sources (free-first; paid phased in later slices) ----

FRED = register(SourceSpec(
    source_id="fred", source_name="FRED (St. Louis Fed)", source_type="macro",
    base_url="https://api.stlouisfed.org/fred", requires_api_key=True,
    allowed_for_decisioning=True, reliability_tier=1,
))

SEC_EDGAR = register(SourceSpec(
    source_id="sec_edgar", source_name="SEC EDGAR / XBRL", source_type="fundamentals",
    base_url="https://data.sec.gov", requires_api_key=False,
    allowed_for_decisioning=True, reliability_tier=1,
))

TREASURY = register(SourceSpec(
    source_id="treasury", source_name="US Treasury Fiscal Data", source_type="macro",
    base_url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service",
    requires_api_key=False, reliability_tier=1,
))

WORLD_BANK = register(SourceSpec(
    source_id="world_bank", source_name="World Bank Indicators", source_type="macro",
    base_url="https://api.worldbank.org/v2", requires_api_key=False, reliability_tier=1,
))

BLS = register(SourceSpec(
    source_id="bls", source_name="US Bureau of Labor Statistics", source_type="macro",
    base_url="https://api.bls.gov/publicAPI", requires_api_key=False, reliability_tier=1,
))

GDELT = register(SourceSpec(
    source_id="gdelt", source_name="GDELT 2.0 (global news/events)", source_type="news",
    base_url="https://api.gdeltproject.org", requires_api_key=False,
    requires_cross_check=True, reliability_tier=2,   # news → needs source quorum >=2
))
