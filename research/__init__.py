"""Research Desk (S12.5) — per-vertical analyst framework, evidence-only, dormant by default."""
from research.evidence import EvidenceObject
from research.desk import AnalystDesk, ResearchDesk, write_evidence
from research.desks import ShariaDesk, MacroDesk

__all__ = ["EvidenceObject", "AnalystDesk", "ResearchDesk", "write_evidence", "ShariaDesk", "MacroDesk"]
