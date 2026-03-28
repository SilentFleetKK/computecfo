"""
🔌 FastAPI integration — drop-in router for any FastAPI app.

Usage:
    from computecfo.api import create_router
    app.include_router(create_router(tracker), prefix="/api/cost")
"""
from fastapi import APIRouter
from .tracker import CostTracker
from .budget import BudgetManager
from .analyzer import CostAnalyzer
from .models import BudgetConfig


def create_router(tracker: CostTracker = None,
                  budget_config: BudgetConfig = None) -> APIRouter:
    """Create a FastAPI router with all ComputeCFO endpoints."""

    if tracker is None:
        tracker = CostTracker()

    budget = BudgetManager(tracker, budget_config)
    analyzer = CostAnalyzer(tracker)
    router = APIRouter(tags=["computecfo"])

    @router.get("/summary")
    async def get_summary():
        return {
            "today": tracker.get_today(),
            "week": tracker.get_this_week(),
            "month": tracker.get_this_month(),
            "projected_monthly": tracker.get_projected_monthly(),
        }

    @router.get("/by-module")
    async def by_module(days: int = 30):
        return tracker.get_by_module(days)

    @router.get("/by-model")
    async def by_model(days: int = 30):
        return tracker.get_by_model(days)

    @router.get("/daily-trend")
    async def daily_trend(days: int = 30):
        return tracker.get_daily_trend(days)

    @router.get("/recent")
    async def recent(limit: int = 20):
        return tracker.get_recent(limit)

    @router.get("/budget")
    async def check_budget():
        return budget.check_all()

    @router.get("/roi")
    async def roi(value_per_output: float = 0):
        return analyzer.get_roi_report(value_per_output)

    @router.get("/efficiency")
    async def efficiency():
        return analyzer.get_efficiency_score()

    @router.get("/prediction")
    async def prediction():
        return analyzer.predict_monthly_cost()

    @router.get("/savings")
    async def savings():
        return analyzer.get_savings_suggestions()

    @router.get("/report")
    async def full_report(value_per_output: float = 0):
        return analyzer.generate_report(value_per_output)

    return router
