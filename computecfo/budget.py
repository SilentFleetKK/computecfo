"""
🚨 BudgetManager — Budget controls, alerts, and circuit breaker.
Prevents runaway API costs with multi-level protection.
"""
import logging
from typing import Optional, Callable
from .models import BudgetConfig, calc_cost, get_model_tier, estimate_tokens
from .tracker import CostTracker

log = logging.getLogger("computecfo")


class BudgetManager:
    """Multi-level budget controls with auto-downgrade and circuit breaker."""

    def __init__(self, tracker: CostTracker, config: BudgetConfig = None,
                 on_warn: Callable = None, on_critical: Callable = None,
                 on_circuit_break: Callable = None):
        self.tracker = tracker
        self.config = config or BudgetConfig()
        self.on_warn = on_warn or self._default_warn
        self.on_critical = on_critical or self._default_critical
        self.on_circuit_break = on_circuit_break or self._default_circuit_break
        self._circuit_broken = False

    def check_budget(self, period: str = "daily") -> dict:
        """Check current spending against budget limits."""
        if period == "daily":
            data = self.tracker.get_today()
            limit = self.config.daily_limit
        elif period == "weekly":
            data = self.tracker.get_this_week()
            limit = self.config.weekly_limit
        else:
            data = self.tracker.get_this_month()
            limit = self.config.monthly_limit

        spent = data["cost"]
        ratio = spent / limit if limit > 0 else 0
        remaining = max(0, limit - spent)

        status = "ok"
        if ratio >= self.config.circuit_break_threshold:
            status = "circuit_break"
        elif ratio >= self.config.critical_threshold:
            status = "critical"
        elif ratio >= self.config.warn_threshold:
            status = "warning"

        return {
            "period": period,
            "spent": round(spent, 4),
            "limit": limit,
            "remaining": round(remaining, 4),
            "ratio": round(ratio, 3),
            "percent": f"{ratio * 100:.1f}%",
            "status": status,
            "calls": data["calls"],
        }

    def check_all(self) -> dict:
        """Check all budget periods at once."""
        return {
            "daily": self.check_budget("daily"),
            "weekly": self.check_budget("weekly"),
            "monthly": self.check_budget("monthly"),
            "circuit_broken": self._circuit_broken,
        }

    def pre_call_check(self, model: str, estimated_tokens: int = 1000) -> dict:
        """Check before making an API call. Returns approved model (may be downgraded)."""
        if self._circuit_broken:
            return {
                "approved": False,
                "reason": "Circuit breaker active — budget exceeded 150%",
                "model": model,
            }

        # Check daily budget (most granular)
        daily = self.check_budget("daily")

        if daily["status"] == "circuit_break":
            self._circuit_broken = True
            self.on_circuit_break(daily)
            return {
                "approved": False,
                "reason": f"Daily budget exhausted: ${daily['spent']:.2f} / ${daily['limit']:.2f}",
                "model": model,
            }

        if daily["status"] == "critical":
            self.on_critical(daily)
            # Auto-downgrade to cheaper model
            if self.config.auto_downgrade and model in self.config.downgrade_map:
                cheaper = self.config.downgrade_map[model]
                log.warning(f"Budget critical — downgrading {model} → {cheaper}")
                return {
                    "approved": True,
                    "model": cheaper,
                    "downgraded": True,
                    "original_model": model,
                    "reason": f"Auto-downgraded to save budget ({daily['percent']} used)",
                }

        if daily["status"] == "warning":
            self.on_warn(daily)

        return {
            "approved": True,
            "model": model,
            "downgraded": False,
            "budget_status": daily["status"],
            "remaining": daily["remaining"],
        }

    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker."""
        self._circuit_broken = False
        log.info("Circuit breaker reset")

    def get_savings_report(self) -> dict:
        """Report on cost savings from auto-downgrade and caching."""
        recent = self.tracker.get_recent(100)

        downgraded_count = 0
        cached_count = 0
        estimated_saved = 0.0

        for r in recent:
            if r["cached"]:
                cached_count += 1
                estimated_saved += r["cost_usd"]
            if r["tier"] == "economy" and r.get("metadata", {}).get("was_downgraded"):
                downgraded_count += 1

        return {
            "cached_calls": cached_count,
            "downgraded_calls": downgraded_count,
            "estimated_saved_usd": round(estimated_saved, 4),
            "total_calls_analyzed": len(recent),
        }

    # ─── P1 #12: Pre-call Cost Estimation ───

    def estimate_call_cost(self, model: str, prompt: str = "",
                           estimated_input_tokens: int = 0,
                           estimated_output_ratio: float = 0.5) -> dict:
        """
        Estimate cost before making an API call.

        Args:
            model: Model to use
            prompt: Input prompt text (used to estimate input tokens if estimated_input_tokens=0)
            estimated_input_tokens: Direct token count (overrides prompt-based estimate)
            estimated_output_ratio: Expected output/input token ratio (default 0.5)
        """
        if estimated_input_tokens > 0:
            input_t = estimated_input_tokens
        elif prompt:
            input_t = estimate_tokens(prompt)
        else:
            input_t = 1000  # fallback default

        output_t = int(input_t * estimated_output_ratio)
        cost = calc_cost(model, input_t, output_t)

        # Check against remaining budget
        daily = self.check_budget("daily")
        will_exceed = (daily["spent"] + cost) > daily["limit"]

        # Suggest cheaper alternative if cost is high
        suggestion = None
        if will_exceed and model in self.config.downgrade_map:
            cheaper = self.config.downgrade_map[model]
            cheaper_cost = calc_cost(cheaper, input_t, output_t)
            suggestion = {
                "model": cheaper,
                "estimated_cost": round(cheaper_cost, 6),
                "savings": round(cost - cheaper_cost, 6),
                "will_exceed_budget": (daily["spent"] + cheaper_cost) > daily["limit"],
            }

        return {
            "model": model,
            "estimated_input_tokens": input_t,
            "estimated_output_tokens": output_t,
            "estimated_cost": round(cost, 6),
            "budget_remaining": daily["remaining"],
            "will_exceed_budget": will_exceed,
            "cheaper_alternative": suggestion,
        }

    # ─── Default callbacks ───

    @staticmethod
    def _default_warn(data: dict):
        log.warning(f"⚠️ Budget warning: {data['period']} at {data['percent']} "
                    f"(${data['spent']:.2f} / ${data['limit']:.2f})")

    @staticmethod
    def _default_critical(data: dict):
        log.error(f"🔴 Budget CRITICAL: {data['period']} at {data['percent']} "
                  f"(${data['spent']:.2f} / ${data['limit']:.2f})")

    @staticmethod
    def _default_circuit_break(data: dict):
        log.critical(f"🚨 CIRCUIT BREAK: {data['period']} exceeded 150%! "
                     f"(${data['spent']:.2f} / ${data['limit']:.2f}). API calls blocked.")
