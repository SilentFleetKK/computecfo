"""
📊 CostAnalyzer — ROI analysis, smart savings, cost prediction,
   model value scoring, and anomaly detection.
"""
import logging
import math
from datetime import datetime, timezone, timedelta
from .tracker import CostTracker
from .models import MODEL_PRICING, get_model_tier, calc_cost

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

    # ─── P0 #4: Model Value Scoring ───

    def get_model_value_scores(self, days: int = 30) -> list[dict]:
        """
        Calculate value-for-money score for each model used.
        Inspired by Graham's intrinsic value — find the "undervalued" models.

        Score = normalized inverse of cost-per-token, benchmarked against peers
        in the same tier. Higher score = better value.
        """
        by_model = self.tracker.get_by_model(days)
        if not by_model:
            return []

        # Build per-model stats
        scored = []
        for m in by_model:
            if m["tokens"] == 0:
                continue
            cost_per_1k = m["cost"] / m["tokens"] * 1000
            tier = get_model_tier(m["model"])

            # Find cheapest alternative in same tier
            tier_peers = [
                (name, p) for name, p in MODEL_PRICING.items()
                if name != "default" and get_model_tier(name) == tier and name != m["model"]
            ]
            cheapest_peer_cost = None
            cheapest_peer_name = None
            if tier_peers:
                cheapest_peer_name, cheapest_peer = min(
                    tier_peers, key=lambda x: (x[1]["input"] + x[1]["output"]) / 2
                )
                cheapest_peer_cost = (cheapest_peer["input"] + cheapest_peer["output"]) / 2 / 1000

            # Value score: 100 if cheapest in tier, lower as cost increases
            pricing = MODEL_PRICING.get(m["model"], MODEL_PRICING["default"])
            model_avg_cost = (pricing["input"] + pricing["output"]) / 2 / 1000
            if cheapest_peer_cost and cheapest_peer_cost > 0:
                ratio = cheapest_peer_cost / model_avg_cost  # <1 means model is more expensive
                value_score = min(100, int(ratio * 100))
            else:
                value_score = 80  # no peers to compare

            recommendation = ""
            if value_score < 40:
                recommendation = (
                    f"Consider switching to '{cheapest_peer_name}' for non-critical tasks. "
                    f"Potential {int((1 - ratio) * 100)}% cost reduction in this tier."
                )
            elif value_score < 70:
                recommendation = f"Acceptable value. '{cheapest_peer_name}' is cheaper if quality allows."

            scored.append({
                "model": m["model"],
                "tier": tier,
                "cost_per_1k_tokens": round(cost_per_1k, 6),
                "total_spent": round(m["cost"], 4),
                "calls": m["calls"],
                "value_score": value_score,
                "grade": "A" if value_score >= 90 else "B" if value_score >= 70 else "C" if value_score >= 50 else "D" if value_score >= 30 else "F",
                "cheapest_alternative": cheapest_peer_name,
                "recommendation": recommendation,
            })

        scored.sort(key=lambda x: x["value_score"], reverse=True)
        return scored

    # ─── P1 #6: Anomaly Detection ───

    def detect_anomalies(self, days: int = 14, z_threshold: float = 2.0) -> list[dict]:
        """
        Detect abnormal spending patterns — the "Mr. Market" alarm.
        Uses Z-score on daily costs + pattern-based heuristics.
        """
        anomalies = []
        trend = self.tracker.get_daily_trend(days)

        if len(trend) < 5:
            return [{"type": "insufficient_data", "message": "Need at least 5 days of data"}]

        costs = [d["cost"] for d in trend]
        mean = sum(costs) / len(costs)
        variance = sum((c - mean) ** 2 for c in costs) / len(costs)
        std = math.sqrt(variance) if variance > 0 else 0.001

        # 1. Daily spending spikes (Z-score)
        for d in trend:
            z = (d["cost"] - mean) / std
            if z > z_threshold:
                anomalies.append({
                    "type": "spending_spike",
                    "severity": "high" if z > 3 else "medium",
                    "date": d["date"],
                    "cost": round(d["cost"], 4),
                    "z_score": round(z, 2),
                    "daily_average": round(mean, 4),
                    "message": f"${d['cost']:.2f} on {d['date']} — {z:.1f}x std dev above mean ${mean:.2f}",
                })

        # 2. Model concentration risk (over-reliance on single model)
        by_model = self.tracker.get_by_model(days)
        total_cost = sum(m["cost"] for m in by_model)
        if total_cost > 0:
            for m in by_model:
                ratio = m["cost"] / total_cost
                if ratio > 0.85 and len(by_model) > 1:
                    anomalies.append({
                        "type": "concentration_risk",
                        "severity": "medium",
                        "model": m["model"],
                        "percent": f"{ratio * 100:.0f}%",
                        "message": (
                            f"'{m['model']}' accounts for {ratio * 100:.0f}% of all spending. "
                            f"Diversify to reduce vendor lock-in risk."
                        ),
                    })

        # 3. Accelerating spend (last 3 days vs first 3 days)
        if len(costs) >= 6:
            recent_avg = sum(costs[-3:]) / 3
            older_avg = sum(costs[:3]) / 3
            if older_avg > 0 and recent_avg > older_avg * 2:
                anomalies.append({
                    "type": "accelerating_spend",
                    "severity": "high",
                    "recent_daily_avg": round(recent_avg, 4),
                    "older_daily_avg": round(older_avg, 4),
                    "acceleration": f"{recent_avg / older_avg:.1f}x",
                    "message": (
                        f"Spending accelerating: recent ${recent_avg:.2f}/day vs earlier ${older_avg:.2f}/day "
                        f"({recent_avg / older_avg:.1f}x increase). Are you being driven by emotion?"
                    ),
                })

        # 4. Premium model creep
        by_model_recent = self.tracker.get_by_model(3)
        by_model_older = self.tracker.get_by_model(days)
        recent_premium = sum(m["cost"] for m in by_model_recent if get_model_tier(m["model"]) == "premium")
        recent_total = sum(m["cost"] for m in by_model_recent) or 0.01
        older_premium = sum(m["cost"] for m in by_model_older if get_model_tier(m["model"]) == "premium")
        older_total = sum(m["cost"] for m in by_model_older) or 0.01
        if recent_premium / recent_total > older_premium / older_total + 0.2:
            anomalies.append({
                "type": "premium_creep",
                "severity": "medium",
                "message": (
                    f"Premium model usage rising: {recent_premium / recent_total * 100:.0f}% recently "
                    f"vs {older_premium / older_total * 100:.0f}% overall. "
                    f"Review if premium quality is truly needed."
                ),
            })

        if not anomalies:
            anomalies.append({"type": "all_clear", "severity": "info", "message": "No anomalies detected. Spending patterns look healthy."})

        return anomalies

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
            "model_value_scores": self.get_model_value_scores(),
            "anomalies": self.detect_anomalies(),
        }
