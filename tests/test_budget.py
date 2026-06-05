"""
S4 — Budget Kernel tests.
"""
import pytest
from capital.budget_kernel import BudgetKernel, BudgetLimits, BudgetState


def limits(**kw):
    d = dict(total_fund=10_000, max_per_action=100,
             max_daily_spend=100, max_weekly_spend=300, max_monthly_spend=1000)
    d.update(kw)
    return BudgetLimits(**d)


def test_within_budget_allowed():
    k = BudgetKernel(limits())
    assert k.check(50, BudgetState()).allow

def test_over_per_action_rejected():
    k = BudgetKernel(limits())
    d = k.check(101, BudgetState())
    assert not d.allow and d.limit_hit == "per_action"

def test_per_action_boundary():
    k = BudgetKernel(limits())
    assert k.check(100, BudgetState()).allow
    assert not k.check(100.01, BudgetState()).allow

def test_daily_limit_rejected():
    k = BudgetKernel(limits())
    d = k.check(60, BudgetState(spent_today=50))   # 110 > 100 daily
    assert not d.allow and d.limit_hit == "daily"

def test_weekly_limit_rejected():
    k = BudgetKernel(limits())
    d = k.check(60, BudgetState(spent_today=0, spent_week=260))  # 320 > 300
    assert not d.allow and d.limit_hit == "weekly"

def test_monthly_limit_rejected():
    k = BudgetKernel(limits())
    d = k.check(60, BudgetState(spent_month=970))  # 1030 > 1000
    assert not d.allow and d.limit_hit == "monthly"

def test_negative_spend_rejected():
    k = BudgetKernel(limits())
    assert not k.check(-10, BudgetState()).allow

def test_bucket_allocation_math():
    k = BudgetKernel(limits())
    assert k.bucket_allocation("core") == pytest.approx(5000)       # 50% of 10k
    assert k.bucket_allocation("trader") == pytest.approx(1500)     # 15%
    assert k.bucket_allocation("emergency") == pytest.approx(1000)  # 10%

def test_unknown_bucket_zero():
    assert BudgetKernel(limits()).bucket_allocation("ghost") == 0.0

def test_default_buckets_sum_to_one():
    assert BudgetKernel(limits()).buckets_sum() == pytest.approx(1.0)
