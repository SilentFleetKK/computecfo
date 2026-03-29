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
    async def get_summary(project: str = ""):
        return {
            "today": tracker.get_today(project=project),
            "week": tracker.get_this_week(project=project),
            "month": tracker.get_this_month(project=project),
            "projected_monthly": tracker.get_projected_monthly(project=project),
        }

    @router.get("/by-module")
    async def by_module(days: int = 30, project: str = ""):
        return tracker.get_by_module(days, project=project)

    @router.get("/by-model")
    async def by_model(days: int = 30, project: str = ""):
        return tracker.get_by_model(days, project=project)

    @router.get("/by-project")
    async def by_project(days: int = 30):
        return tracker.get_by_project(days)

    @router.get("/daily-trend")
    async def daily_trend(days: int = 30, project: str = ""):
        return tracker.get_daily_trend(days, project=project)

    @router.get("/recent")
    async def recent(limit: int = 20, project: str = ""):
        return tracker.get_recent(limit, project=project)

    @router.get("/budget")
    async def check_budget():
        return budget.check_all()

    @router.get("/estimate")
    async def estimate_cost(model: str, prompt: str = "", tokens: int = 0):
        return budget.estimate_call_cost(model, prompt=prompt, estimated_input_tokens=tokens)

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

    @router.get("/model-values")
    async def model_values(days: int = 30):
        return analyzer.get_model_value_scores(days)

    @router.get("/anomalies")
    async def anomalies(days: int = 14):
        return analyzer.detect_anomalies(days)

    @router.get("/report")
    async def full_report(value_per_output: float = 0):
        return analyzer.generate_report(value_per_output)

    return router
