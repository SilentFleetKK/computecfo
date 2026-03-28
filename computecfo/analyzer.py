"""
📊 CostAnalyzer — ROI analysis, smart savings, and cost prediction.
"""
import logging
from datetime import datetime, timezone, timedelta
from .tracker import CostTracker
from .models import MODEL_PRICING, get_model_tier

log = logging.getLogger("computecfo")


class CostAnalyzer:
    """Analyze spending patterns, calculate ROI, and suggest optimizations."""

    def __init__(self, tracker: CostTracker):
        self.tracker = tracker

    def get_roi_report(self, value_per_output: float = 0.0) -> dict:
        """
        Calculate ROI for your AI spending.

        Args:
            value_per_output: estimated value generated per API call (in USD).
                              e.g. if each AI-generated output saves 30 min of work
                              at $50/hr, value_per_output = $25
        """
        month = self.tracker.get_this_month()
        if month["calls"] == 0:
            return {"message": "No data yet. Start using AI and come back!"}

        cost_per_call = month["cost"] / month["calls"] if month["calls"] else 0
        total_value = value_per_output * month["calls"] if value_per_output else 0
        roi = ((total_value - month["cost"]) / month["cost"] * 100) if month["cost"] > 0 and total_value else 0

        return {
            "period": "30 days",
            "total_cost": round(month["cost"], 2),
            "total_calls": month["calls"],
            "cost_per_call": round(cost_per_call, 4),
            "total_tokens": month["total_tokens"],
            "cost_per_1k_tokens": round(month["cost"] / max(month["total_tokens"], 1) * 1000, 4),
            "estimated_value": round(total_value, 2) if value_per_output else "not_configured",
            "roi_percent": round(roi, 1) if value_per_output else "configure value_per_output to calculate",
        }

    def get_savings_suggestions(self) -> list[dict]:
        """Analyze spending and suggest ways to save money."""
        suggestions = []
        by_model = self.tracker.get_by_model(30)
        by_module = self.tracker.get_by_module(30)
        month = self.tracker.get_this_month()

        if not by_model:
            return [{"priority": "info", "suggestion": "Not enough data yet. Keep using AI!"}]

        # 1. Check premium model usage ratio
        premium_cost = sum(m["cost"] for m in by_model if get_model_tier(m["model"]) == "premium")
        total_cost = month["cost"]
        if total_cost > 0 and premium_cost / total_cost > 0.6:
            suggestions.append({
                "priority": "high",
                "category": "model_selection",
                "suggestion": f"Premium models account for {premium_cost/total_cost*100:.0f}% of spending. "
                              f"Consider using standard-tier models for non-critical tasks.",
                "potential_savings": f"${premium_cost * 0.4:.2f}/month",
            })

        # 2. Check for modules with high per-call cost
        for m in by_module:
            if m["calls"] > 5:
                avg_cost = m["cost"] / m["calls"]
                if avg_cost > 0.10:
                    suggestions.append({
                        "priority": "medium",
                        "category": "module_optimization",
                        "suggestion": f"Module '{m['module']}' averages ${avg_cost:.3f}/call. "
                                      f"Consider caching, batching, or model downgrade.",
                        "potential_savings": f"${m['cost'] * 0.3:.2f}/month",
                    })

        # 3. Check daily spending variance
        trend = self.tracker.get_daily_trend(14)
        if len(trend) >= 7:
            costs = [d["cost"] for d in trend]
            avg = sum(costs) / len(costs)
            max_day = max(costs)
            if max_day > avg * 3:
                suggestions.append({
                    "priority": "medium",
                    "category": "spike_detection",
                    "suggestion": f"Spending spike detected: ${max_day:.2f} vs avg ${avg:.2f}. "
                                  f"Investigate high-usage days.",
                })

        # 4. General tips
        if total_cost > 0:
            suggestions.append({
                "priority": "low",
                "category": "general",
                "suggestion": "Enable caching for repeated/similar requests to avoid redundant API calls.",
            })

        return suggestions

    def predict_monthly_cost(self, days_to_analyze: int = 14) -> dict:
        """Predict future monthly cost based on recent spending patterns."""
        trend = self.tracker.get_daily_trend(days_to_analyze)
        if len(trend) < 3:
            return {"prediction": "Insufficient data", "confidence": "low"}

        costs = [d["cost"] for d in trend]
        recent_avg = sum(costs[-7:]) / min(len(costs), 7)  # last 7 days
        older_avg = sum(costs[:7]) / min(len(costs[:7]), 7) if len(costs) > 7 else recent_avg

        # Trend direction
        if recent_avg > older_avg * 1.2:
            direction = "increasing"
            projected = recent_avg * 30 * 1.1  # expect continued growth
        elif recent_avg < older_avg * 0.8:
            direction = "decreasing"
            projected = recent_avg * 30 * 0.9
        else:
            direction = "stable"
            projected = recent_avg * 30

        return {
            "daily_average": round(recent_avg, 4),
            "projected_monthly": round(projected, 2),
            "direction": direction,
            "confidence": "high" if len(trend) >= 14 else "medium" if len(trend) >= 7 else "low",
            "based_on_days": len(trend),
            "trend_data": trend[-7:],  # last 7 days for chart
        }

    def get_efficiency_score(self) -> dict:
        """Score your AI spending efficiency (0-100)."""
        month = self.tracker.get_this_month()
        by_model = self.tracker.get_by_model(30)

        if month["calls"] < 10:
            return {"score": 0, "message": "Need at least 10 calls to calculate efficiency"}

        score = 100
        deductions = []

        # Check 1: Premium overuse (-20 max)
        premium_ratio = sum(m["cost"] for m in by_model if get_model_tier(m["model"]) == "premium") / max(month["cost"], 0.01)
        if premium_ratio > 0.7:
            penalty = int((premium_ratio - 0.5) * 40)
            score -= min(penalty, 20)
            deductions.append(f"Premium model overuse: -{penalty}pts")

        # Check 2: Cost per token efficiency (-15 max)
        cost_per_1k = month["cost"] / max(month["total_tokens"], 1) * 1000
        if cost_per_1k > 0.05:
            penalty = min(int(cost_per_1k * 200), 15)
            score -= penalty
            deductions.append(f"High cost per token: -{penalty}pts")

        # Check 3: Spending trend (-15 max)
        trend = self.tracker.get_daily_trend(14)
        if len(trend) >= 7:
            recent = sum(d["cost"] for d in trend[-3:]) / 3
            older = sum(d["cost"] for d in trend[:3]) / 3
            if recent > older * 1.5:
                score -= 15
                deductions.append("Spending increasing rapidly: -15pts")

        # Check 4: Cache utilization (+10 bonus)
        recent_calls = self.tracker.get_recent(50)
        cached = sum(1 for r in recent_calls if r["cached"])
        if cached > len(recent_calls) * 0.1:
            score = min(score + 10, 100)
            deductions.append(f"Good cache usage: +10pts")

        return {
            "score": max(0, min(score, 100)),
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
            "deductions": deductions,
            "total_cost": round(month["cost"], 2),
            "total_calls": month["calls"],
        }

    def generate_report(self, value_per_output: float = 0) -> dict:
        """Generate a comprehensive financial report."""
        return {
            "summary": self.tracker.get_this_month(),
            "today": self.tracker.get_today(),
            "by_module": self.tracker.get_by_module(),
            "by_model": self.tracker.get_by_model(),
            "roi": self.get_roi_report(value_per_output),
            "efficiency": self.get_efficiency_score(),
            "prediction": self.predict_monthly_cost(),
            "savings_suggestions": self.get_savings_suggestions(),
        }
