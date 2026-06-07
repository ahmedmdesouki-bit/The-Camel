"""
L1 — base-rate updater (S11). Auto: update a strategy's hit-rate prior after a trade resolves.

Bayesian-style smoothing: posterior = (prior_rate·prior_n + wins) / (prior_n + wins + losses). Pure.
This is the only fully-automatic tier — it touches a number (base_rate), never a rule or a weight band.
"""
from __future__ import annotations


def update_base_rate(prior_rate: float, prior_n: int, wins: int, losses: int) -> float:
    """Posterior hit-rate after `wins`/`losses` newly-resolved trades. `prior_n` is the prior's weight."""
    prior_rate = max(0.0, min(1.0, prior_rate))
    denom = prior_n + wins + losses
    if denom <= 0:
        return round(prior_rate, 4)
    return round((prior_rate * prior_n + wins) / denom, 4)
