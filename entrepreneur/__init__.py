"""
Entrepreneur Camel (S7) — the engine that proposes, gates, and builds Sharia-compliant products.

Mirrors the Trader arm's discipline: deterministic gates the LLM cannot edit. The agent may
propose theses and generate code; it may NEVER launch, spend, collect data, or publish claims
without passing the Entrepreneur Constitution and a founder approval gate.

This package is pure logic (no network, no real deploy). Stripe / GitHub / customer-data
integration lives behind the approval gates and is wired only when a real product ships.
"""
from entrepreneur.product_gate import ProductThesis, GateResult, evaluate_gate, lead_product_thesis
from entrepreneur.constitution import (
    EntAction, EntActionType, EntDecision, EntrepreneurConstitution,
)
from entrepreneur.build_pipeline import BuildPipeline, Stage, PipelineError

__all__ = [
    "ProductThesis", "GateResult", "evaluate_gate", "lead_product_thesis",
    "EntAction", "EntActionType", "EntDecision", "EntrepreneurConstitution",
    "BuildPipeline", "Stage", "PipelineError",
]
