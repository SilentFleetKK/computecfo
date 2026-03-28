"""
🏦 ComputeCFO — Your AI Financial Officer

Track, analyze, and optimize your LLM API spending.
Budget controls, ROI analysis, cost prediction, and smart savings.
"""

__version__ = "1.0.0"
__author__ = "SilentFleetKK"

from .tracker import CostTracker
from .budget import BudgetManager
from .analyzer import CostAnalyzer
from .models import UsageRecord, MODEL_PRICING

__all__ = [
    "CostTracker",
    "BudgetManager",
    "CostAnalyzer",
    "UsageRecord",
    "MODEL_PRICING",
]
