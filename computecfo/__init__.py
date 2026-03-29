"""
🏦 ComputeCFO — Your AI Financial Officer

Track, analyze, and optimize your LLM API spending.
Budget controls, ROI analysis, cost prediction, and smart savings.
"""

__version__ = "1.1.0"
__author__ = "SilentFleetKK"

from .tracker import CostTracker
from .budget import BudgetManager
from .analyzer import CostAnalyzer
from .models import UsageRecord, BudgetConfig, MODEL_PRICING, estimate_tokens
from .decorators import track_cost
from .alerts import AlertManager, AlertConfig, create_budget_callbacks

__all__ = [
    "CostTracker",
    "BudgetManager",
    "CostAnalyzer",
    "UsageRecord",
    "BudgetConfig",
    "MODEL_PRICING",
    "track_cost",
    "AlertManager",
    "AlertConfig",
    "create_budget_callbacks",
    "estimate_tokens",
]
