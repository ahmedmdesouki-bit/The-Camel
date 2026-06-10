"""
Camel Guardrail Service — the Constitution.

A deterministic gate between Camel's intent and any consequential action.
Camel proposes; this disposes. There is no agent-callable override path:
limits come from founder-owned config, not from the agent.

Deterministic logic; the only I/O is the kill-switch file check (S4), which is
deliberate — the gate itself must see the halt so there is no path around it.
Otherwise no DB and no network, so it stays fully unit-testable. The DB/RLS layer
(see db/schema.sql) is the second wall; this is the first.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict

from ops.kill_switch import is_halted


class ActionType(str, Enum):
    TRADE = "TRADE"            # open/increase a market position
    SPEND = "SPEND"           # entrepreneur spend (hosting, api, etc.)
    DEPLOY = "DEPLOY"         # ship an entrepreneur product
    ADD_WHITELIST = "ADD_WHITELIST"
    WITHDRAW = "WITHDRAW"     # move money out — always forbidden


# Business-activity screen (Sharia §2.1). Lowercased substring match.
HARAM_TERMS = (
    "bank", "conventional finance", "interest", "lending", "loan", "mortgage",
    "alcohol", "beer", "wine", "liquor", "brewery",
    "tobacco", "cigarette", "vape",
    "gambling", "casino", "betting", "lottery",
    "pork", "swine",
    "adult", "porn",
    "weapon", "defense", "defence", "firearm", "ammunition", "military",
)

PROHIBITED_INSTRUMENTS = ("option", "future", "swap", "cfd", "margin",
                          "crypto_derivative", "forward")
PROHIBITED_SIDES = ("short", "sell_short")


@dataclass
class Thesis:
    invalidation: str = ""
    profit_take: str = ""
    time_stop: str = ""

    def complete(self) -> bool:
        return bool(self.invalidation.strip()
                    and self.profit_take.strip()
                    and self.time_stop.strip())


@dataclass
class Instrument:
    symbol: str
    sector: str = "Unknown"
    sharia_status: str = "unknown"   # compliant | non_compliant | unknown
    frozen: bool = False
    on_whitelist: bool = False


@dataclass
class Action:
    type: ActionType
    symbol: Optional[str] = None
    side: str = "buy"                 # buy | sell | short | sell_short
    notional_usd: float = 0.0
    leverage: float = 1.0
    instrument_type: str = "equity"   # equity | etf | option | future | ...
    thesis: Optional[Thesis] = None
    mode: str = "paper"               # paper | live
    approval_id: Optional[str] = None
    business_model: Optional[str] = None   # DEPLOY / SPEND
    approved_by: Optional[str] = None      # ADD_WHITELIST (founder)
    scan_id: Optional[str] = None          # ADD_WHITELIST (logged SHARIA SCAN)
    # illiquidity / slippage gate inputs (S4) — None = unavailable, check skipped
    bid_ask_spread_pct: Optional[float] = None   # (ask-bid)/bid
    avg_daily_volume: Optional[float] = None     # 30-day ADV, shares
    order_shares: Optional[float] = None         # this order's size, shares


@dataclass
class PortfolioState:
    fund_usd: float
    cash_usd: float
    positions: Dict[str, float] = field(default_factory=dict)       # symbol -> mkt value
    sector_values: Dict[str, float] = field(default_factory=dict)   # sector -> mkt value
    whitelist: Dict[str, Instrument] = field(default_factory=dict)  # symbol -> Instrument
    day_pnl_pct: float = 0.0
    week_pnl_pct: float = 0.0
    # rolling velocity stop inputs (S4)
    rolling_5d_pnl_pct: float = 0.0
    rolling_14d_pnl_pct: float = 0.0
    cooldown_active: bool = False          # set by the risk monitor during a 48h freeze
    orders_today: int = 0                  # count of orders already placed today
    entrepreneur_budget_remaining_usd: float = 0.0


@dataclass
class Decision:
    allow: bool
    reason: str
    limit_hit: Optional[str] = None


DEFAULT_LIMITS = {
    "max_position_pct": 0.20,
    "max_sector_pct": 0.40,
    "daily_loss_stop_pct": -0.05,
    "weekly_drawdown_stop_pct": -0.10,
    # rolling velocity stops (S4) — anti-bleeding over a sliding window
    "rolling_5d_stop_pct": -0.08,     # 5-day rolling P&L <= -8% -> reject (48h cooldown)
    "rolling_14d_stop_pct": -0.12,    # 14-day rolling P&L <= -12% -> reject (halt)
    # illiquidity / slippage gate (S4) — skipped gracefully when data absent
    "max_bid_ask_spread_pct": 0.005,  # reject if spread > 0.5%
    "max_adv_participation": 0.01,    # reject if order > 1% of 30-day ADV
    "max_orders_per_day": 10,         # runaway-loop backstop
    "allow_leverage": False,
    "phase": 0,                       # 0 paper, 1 micro-live, 2 auto, 3 scale
    "per_order_envelope_usd": 50.0,   # auto-execute cap (phase >= 2)
    "require_approval_live": True,
    # tiered min cash buffer by fund size
    "cash_tiers": [
        {"max_fund": 1000, "min_cash_pct": 0.0},
        {"max_fund": 10000, "min_cash_pct": 0.10},
        {"max_fund": 1e12, "min_cash_pct": 0.10},
    ],
}


class Constitution:
    def __init__(self, limits: Optional[dict] = None):
        self.L = {**DEFAULT_LIMITS, **(limits or {})}

    @classmethod
    def from_yaml(cls, path: str) -> "Constitution":
        import yaml
        with open(path) as f:
            return cls(yaml.safe_load(f) or {})

    # ---- helpers ----
    def _min_cash_pct(self, fund: float) -> float:
        for tier in self.L["cash_tiers"]:
            if fund <= tier["max_fund"]:
                return tier["min_cash_pct"]
        return self.L["cash_tiers"][-1]["min_cash_pct"]

    @staticmethod
    def _has_haram(text: str) -> bool:
        t = (text or "").lower()
        return any(term in t for term in HARAM_TERMS)

    # ---- main gate ----
    def evaluate(self, a: Action, s: PortfolioState) -> Decision:
        # Kill switch (S4): if halted, NO action proceeds. Checked inside the gate itself
        # so there is no path around it — not merely at the loop entry point.
        if is_halted():
            return Decision(False, "Kill switch active — all actions halted.", "kill_switch")

        try:
            t = ActionType(a.type)
        except ValueError:
            return Decision(False, f"Unknown action type: {a.type}", "unknown_action")

        if t == ActionType.WITHDRAW:
            return Decision(False, "Withdrawals are forbidden by the Constitution.", "no_withdrawals")

        if t == ActionType.ADD_WHITELIST:
            # stripped: a whitespace-only "approval" is no approval (S16 QA — tightens only)
            if not (a.approved_by or "").strip() or not (a.scan_id or "").strip():
                return Decision(False, "Whitelist add needs founder approval + a logged SHARIA SCAN.", "whitelist_unapproved")
            return Decision(True, "Whitelist add approved.")

        if t in (ActionType.DEPLOY, ActionType.SPEND):
            if self._has_haram(a.business_model or ""):
                return Decision(False, "Business model fails the Sharia activity screen.", "haram_business")
            if t == ActionType.SPEND and a.notional_usd > s.entrepreneur_budget_remaining_usd:
                return Decision(False, "Spend exceeds entrepreneur budget.", "budget")
            return Decision(True, "Entrepreneur action within bounds.")

        # ---- TRADE ----
        if t == ActionType.TRADE:
            L = self.L
            # 1. no derivatives / leverage / shorting (Sharia + risk)
            if a.instrument_type.lower() in PROHIBITED_INSTRUMENTS:
                return Decision(False, f"Instrument type '{a.instrument_type}' is prohibited.", "prohibited_instrument")
            if a.side.lower() in PROHIBITED_SIDES:
                return Decision(False, "Short selling is prohibited.", "no_short")
            if not L["allow_leverage"] and a.leverage > 1.0:
                return Decision(False, "Leverage is prohibited.", "no_leverage")

            # 2. must be a name we manage (on the whitelist) — even to sell it
            inst = s.whitelist.get(a.symbol or "")
            if inst is None or not inst.on_whitelist:
                return Decision(False, f"{a.symbol} is not on the compliant whitelist.", "off_whitelist")

            is_sell = a.side.lower() == "sell"

            # 2b. close-only / reduce-only for frozen or non-compliant holdings (S6.5):
            #     a frozen or drifted name may be SOLD to de-risk — never bought or increased.
            if inst.frozen or inst.sharia_status != "compliant":
                if not is_sell:
                    if inst.frozen:
                        return Decision(False, f"{a.symbol} is frozen (compliance drift) — close-only.", "frozen")
                    return Decision(False, f"{a.symbol} is not Sharia-compliant — close-only.", "not_compliant")
                # is_sell → de-risking exit is permitted; fall through to the phantom-sell guard.

            # 2c. phantom-sell guard (S6.5): cannot sell what is not held; cannot oversell.
            #     PortfolioState.positions holds market value per symbol. A precise
            #     share-level check arrives with realistic execution in S12.
            if is_sell:
                held = s.positions.get(a.symbol or "", 0.0)
                if held <= 0:
                    return Decision(False, f"No {a.symbol} position to sell.", "no_holdings")
                if a.notional_usd > held * (1 + 1e-6):
                    return Decision(False, f"Sell exceeds held {a.symbol} value.", "oversell")
                return Decision(True, f"Sell/close {a.symbol} allowed (reduce-only).")

            # ---- buy / increase path (compliant, non-frozen) ----
            # 3. invalidation point required before opening/increasing
            if a.thesis is None or not a.thesis.complete():
                return Decision(False, "No position without a written invalidation/profit-take/time-stop.", "no_invalidation")

            # 4. circuit breakers
            if s.day_pnl_pct <= L["daily_loss_stop_pct"]:
                return Decision(False, "Daily loss stop hit — trading halted.", "daily_loss_stop")
            if s.week_pnl_pct <= L["weekly_drawdown_stop_pct"]:
                return Decision(False, "Weekly drawdown stop hit — trading frozen.", "weekly_drawdown_stop")

            # 4b. rolling velocity stops + cooldown (S4) — anti-bleeding
            if s.cooldown_active:
                return Decision(False, "In post-breach cooldown — trading frozen.", "cooldown")
            if s.rolling_5d_pnl_pct <= L["rolling_5d_stop_pct"]:
                return Decision(False, "5-day rolling drawdown stop hit.", "rolling_5d_stop")
            if s.rolling_14d_pnl_pct <= L["rolling_14d_stop_pct"]:
                return Decision(False, "14-day rolling drawdown stop hit.", "rolling_14d_stop")

            # 4c. orders-per-day cap (S4) — runaway-loop backstop
            if s.orders_today >= L["max_orders_per_day"]:
                return Decision(False, "Max orders per day reached.", "max_orders_per_day")

            # 4d. illiquidity / slippage gate (S4; S6.6 fail-closed in live).
            # In PAPER it still skips gracefully when data is absent. In LIVE, missing the data
            # needed to clear the gate is a BLOCK — an illiquid trade must never pass unchecked.
            liq_data_present = (a.bid_ask_spread_pct is not None
                                and a.avg_daily_volume and a.order_shares is not None)
            if a.mode == "live" and not liq_data_present:
                return Decision(False, "Illiquidity data missing — cannot clear the liquidity gate in live.",
                                "illiquidity_data_missing")
            if (a.bid_ask_spread_pct is not None
                    and a.bid_ask_spread_pct > L["max_bid_ask_spread_pct"]):
                return Decision(False, "Bid-ask spread too wide for safe execution.", "wide_spread")
            if (a.avg_daily_volume and a.order_shares is not None
                    and a.order_shares > L["max_adv_participation"] * a.avg_daily_volume + 1e-9):
                return Decision(False, "Order exceeds ADV participation cap.", "illiquid_size")

            # 5. per-order envelope (auto execution cap)
            env = L["per_order_envelope_usd"]
            over_envelope = env is not None and a.notional_usd > env

            # 6. resulting position concentration
            new_pos = s.positions.get(a.symbol, 0.0) + a.notional_usd
            if s.fund_usd > 0 and new_pos / s.fund_usd > L["max_position_pct"] + 1e-9:
                return Decision(False, f"Position would exceed {L['max_position_pct']:.0%} of fund.", "max_position")

            # 7. resulting sector concentration
            sec = inst.sector
            new_sec = s.sector_values.get(sec, 0.0) + a.notional_usd
            if s.fund_usd > 0 and new_sec / s.fund_usd > L["max_sector_pct"] + 1e-9:
                return Decision(False, f"Sector '{sec}' would exceed {L['max_sector_pct']:.0%}.", "max_sector")

            # 8. cash buffer (tiered)
            buffer = s.fund_usd * self._min_cash_pct(s.fund_usd)
            deployable = s.cash_usd - buffer
            if a.notional_usd > deployable + 1e-9:
                return Decision(False, "Order exceeds deployable cash after buffer.", "cash_buffer")

            # 9. money-movement gate (live)
            if a.mode == "live" and L["require_approval_live"]:
                auto_ok = (L["phase"] >= 2) and not over_envelope
                if not auto_ok and not a.approval_id:
                    return Decision(False, "Live order needs founder approval.", "needs_approval")

            return Decision(True, f"Buy {a.symbol} ${a.notional_usd:.2f} allowed.")

        return Decision(False, "Unhandled action.", "unhandled")
